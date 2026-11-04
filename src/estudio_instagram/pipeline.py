"""Gera, e opcionalmente publica, o Reels e o carrossel de uma pauta.

Uso:
    python -m src.estudio_instagram.pipeline --pauta pautas/5-repos-claude-code.json
    python -m src.estudio_instagram.pipeline --pauta pautas/5-repos-claude-code.json --publicar

Saída em saida/instagram/<nome-da-pauta>/: reels.mp4, carrossel/slide-NN.png e registro.json.
Publicar exige INSTAGRAM_GRAPH_TOKEN e INSTAGRAM_USER_ID no .env (ver docs/estudio-instagram.md).
"""

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from . import cenas_pixel, github_dados, guia_dm, identidade, story, hospedagem, montagem, pauta, pausa, render
from .graph_api import InstagramGraph
from .roteirista import buscar_readme
from .voz import ComReserva, EdgeTTS, ElevenLabs, GeminiTTS

RAIZ = Path(__file__).resolve().parents[2]
ICONES = {p.stem for p in (montagem.MODELOS / "assets" / "icons").glob("*.svg")}
LIMITE_LEGENDA_INSTAGRAM = 2200
# Modo seguro: não publica se a conta já usou muito da cota de 24 h, e espera entre o Reels e o carrossel.
LIMITE_SEGURO_POSTS_24H = 10
ESPERA_ENTRE_REELS_E_CARROSSEL_S = 600
# Formatos que geram só o Reels (sem carrossel) e o molde visual de cada um.
MOLDES_SO_REELS = {"prompt": "prompt.html.tpl", "diagrama": "diagrama.html.tpl", "palito": "palito.html.tpl",
                   "repo": "repo.html.tpl"}
# Formatos com Reels + carrossel próprio (os slides vêm da pauta, não de repositórios).
MOLDES_COM_SLIDES = {"pixel": "pixel.html.tpl", "pixel2": "pixel2.html.tpl"}
# Moldes "estúdio" (2026-10-26) substituem o pixel2 no Reels: mesmos dados de cena, visual de motion design
# (escuro/laranja, rabisco à mão, neon). Cada pauta cai num deles, fixo pelo título, pra o feed variar.
# `MOLDE_PIXEL2=1` no ambiente volta pro molde antigo.
MOLDES_ESTUDIO = [
    # estudio-3d.html.tpl (@yan.gsouza) reprovado pelo Davi em 2026-11-02: 4 posts, sempre a mesma
    # animaçãozinha 3D genérica (template, não identidade) e um deles saiu sem sincronizar.
    "estudio-rabisco.html.tpl",  # @oguiadaia: desenho à mão em papel
    "estudio-pixelui.html.tpl",  # @99hud: fonte pixel, janelas retrô, personagem
    "estudio-tier.html.tpl",     # @daniel.esantos: ranking S/A/B + print real do repo
    "estudio-telao.html.tpl",    # @jako.frames: tipografia cinética num monitor
    "estudio-papel.html.tpl",    # @nodir.ai_: tipografia 3D extrudada em papel creme
    "estudio-vidro.html.tpl",    # @igao.ia: interface de app em vidro escuro
    "estudio-voxel.html.tpl",    # @macelista: letreiro neon, fita crepe, mascote voxel 3D
    "estudio-cartao.html.tpl",   # @motionia.br: papel rasgado + fita, cartão creme, robô estagiário
    "estudio-glow.html.tpl",     # @mateus.curta.ia: preto, glow vermelho, órbita de ícone, sem personagem
]  # escuro e neon foram reprovados pelo Davi (2026-10-26)

# 2026-10-30: até aqui o rodízio automático do vídeo de UMA ferramenta só escolhia entre as 2
# identidades de identidade.py (escritório, vila) -- os 10 moldes de MOLDES_ESTUDIO só saíam em
# posts com `molde` forçado (venda). Resultado: 2 posts seguidos caíram na mesma identidade
# (BeautifulRust e agent-purge, ambos "vila") e pareceram o mesmo vídeo. Davi reforçou que o Kit
# Engenharia vende 8+ identidades -- o rodízio tem que usar o pool inteiro, não só 2.
IDENTIDADES_IDENT = [f"ident-{n}" for n in identidade.identidades()]


def todas_as_identidades() -> list[str]:
    return IDENTIDADES_IDENT + MOLDES_ESTUDIO


ARQUIVO_ULTIMA_IDENTIDADE = RAIZ / "pautas" / "ultima_identidade.json"


def identidade_do(titulo: str) -> str:
    """Identidade/molde do vídeo de uma ferramenta, em rodízio pelo título, por TODO o acervo.

    Nunca repete a identidade do post anterior: a soma de char codes colide fácil (dois títulos
    quaisquer terminando em "roteiro automático" caem no mesmo bucket com frequência), e foi
    exatamente isso que fez dois posts seguidos saírem na mesma identidade em 2026-10-30.
    """
    escolhas = todas_as_identidades()
    indice = sum(ord(c) for c in titulo) % len(escolhas)
    anterior = None
    if ARQUIVO_ULTIMA_IDENTIDADE.exists():
        anterior = json.loads(ARQUIVO_ULTIMA_IDENTIDADE.read_text(encoding="utf-8")).get("molde")
    if escolhas[indice] == anterior:
        indice = (indice + 1) % len(escolhas)
    escolhido = escolhas[indice]
    ARQUIVO_ULTIMA_IDENTIDADE.write_text(json.dumps({"molde": escolhido}), encoding="utf-8")
    return escolhido


def molde_estudio(titulo: str) -> str:
    return MOLDES_ESTUDIO[sum(ord(c) for c in titulo) % len(MOLDES_ESTUDIO)]


# Carrossel desligado (2026-10-26): cada post saía duplicado (Reels + carrossel com a mesma legenda), o que
# dividia o alcance e cansava quem segue. Volta a ligar só com `PUBLICAR_CARROSSEL=1` no ambiente.
MIN_SEGUIDORES_TRIAL = 1000  # Trial Reels só liberam a partir daqui
PUBLICAR_CARROSSEL = os.getenv("PUBLICAR_CARROSSEL") == "1"


HASHTAGS = ["ia", "inteligenciaartificial", "claudecode", "automacao"]  # 3 a 5: o Instagram limita e trata como tema


def cenas_da_pauta(dados_pauta: dict) -> list[dict]:
    """A pauta automática guarda as cenas em `cenas_roteiro`; as pautas manuais antigas, em `cenas`.

    Bug corrigido em 2026-11-04: legenda e identidades só olhavam `cenas`, então nos vídeos automáticos a 1ª linha
    da legenda (e o gancho das identidades) caíam na descrição do repositório em vez do gancho escrito.
    """
    return dados_pauta.get("cenas") or dados_pauta.get("cenas_roteiro") or []


def montar_legenda(dados_pauta: dict, repos: dict) -> str:
    """Legenda pensada para a busca do Instagram (skill instagram-seo) e para o algoritmo (envios e salvos).

    1ª linha = o gancho falado (é o que aparece antes do "mais"); logo depois a palavra para comentar; uma frase com a
    palavra-chave do tema (o que alguém buscaria); passos para salvar; 1 a cada 3 posts pede para enviar a alguém;
    3 a 5 hashtags de tema. Sem emoji (regra do Davi). Pauta com `legenda` própria (venda) usa o texto dela.
    """
    if dados_pauta.get("legenda"):
        return dados_pauta["legenda"][:LIMITE_LEGENDA_INSTAGRAM]
    cenas = cenas_da_pauta(dados_pauta)
    gancho = (cenas[0].get("narracao") or "").strip() if cenas else ""
    subtitulo = (dados_pauta.get("capa") or {}).get("subtitulo", "").strip()
    primeira = gancho or subtitulo.capitalize()
    palavra = dados_pauta["palavra_chave"]
    passos = dados_pauta.get("passos") or []
    bloco_passos = ("Salva este vídeo pra usar com calma:\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(passos, 1)) + "\n\n") if passos else ""
    tema = f"{subtitulo[:1].upper()}{subtitulo[1:]}.\n\n" if subtitulo and subtitulo.lower() != primeira.lower() else ""
    envio = "Manda pra um amigo que vai querer usar isso.\n" if sum(map(ord, dados_pauta.get("titulo", ""))) % 3 == 0 else ""
    hashtags = " ".join(f"#{t}" for t in HASHTAGS)
    texto = (
        f"{primeira}\n"
        f"Comenta {palavra} que eu te mando o link no direct.\n\n"
        f"{tema}"
        f"{bloco_passos}"
        f"{envio}"
        f"Segue o @ursulino.ia pra não perder a próxima ferramenta de IA.\n\n{hashtags}"
    )
    return texto[:LIMITE_LEGENDA_INSTAGRAM]


def criar_voz(dados_pauta: dict):
    """Voz do vídeo. Padrão: Gemini "Orus" (a que o Davi escolheu), com a voz do Edge de reserva.

    `VOZ=elevenlabs` no ambiente volta para o ElevenLabs (cota do plano grátis acabou em 2026-10-18).
    """
    cache = RAIZ / ".cache" / "voz"
    if os.getenv("VOZ", "").lower() == "elevenlabs" or not os.getenv("GEMINI_API_KEY"):
        principal = ElevenLabs(dados_pauta["voz"]["id"], dados_pauta["voz"]["modelo"], cache)
    else:
        principal = GeminiTTS("Orus", cache)
    return ComReserva(principal, EdgeTTS())


def _registrar_links(dados_pauta: dict, repos: dict, registro: dict):
    """Guarda, para cada mídia publicada, a palavra e a mensagem que o bot de comentários deve mandar."""
    lista = list(repos.values())
    if len(lista) == 1:  # vídeo de uma ferramenta: o direct leva um mini-guia, não só o link
        primeiro = lista[0]
        try:
            readme = buscar_readme(primeiro.repo)
        except Exception:
            readme = ""
        mensagem = guia_dm.gerar(primeiro, readme)
    else:  # formato lista: um link por repositório, na ordem do vídeo
        linhas = "\n".join(f"{i}. {d.repo.split('/', 1)[1]}: {d.url}" for i, d in enumerate(lista, 1))
        mensagem = f"Oi! Aqui estão os repositórios do vídeo:\n{linhas}\nSe curtir, segue o @ursulino.ia pra mais ferramentas de IA."
    primeiro = lista[0]
    arquivo = RAIZ / "pautas" / "links_por_post.json"
    atual = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    for media_id in (registro["reels"].get("media_id"), registro.get("carrossel_media_id")):
        if media_id:
            atual[media_id] = {"palavra": dados_pauta["palavra_chave"], "mensagem": mensagem, "repo": primeiro.repo}
    arquivo.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")


def _registrar_estilo(media_id: str, molde: str):
    """Guarda qual identidade visual saiu em cada post, pro analista comparar os estilos."""
    arquivo = RAIZ / "pautas" / "estilo_por_post.json"
    atual = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    atual[media_id] = molde.removeprefix("estudio-").removeprefix("ident-").removesuffix(".html.tpl")
    arquivo.write_text(json.dumps(atual, ensure_ascii=False, indent=1), encoding="utf-8")


def _registrar_pauta(media_id: str, caminho_pauta: Path, dados_pauta: dict, molde: str, formato: str):
    """Liga o post à pauta que o gerou (gancho A/B, formato, estilo): base da repostagem e da comparação de ganchos."""
    arquivo = RAIZ / "pautas" / "pauta_por_post.json"
    atual = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    try:
        rel = str(Path(caminho_pauta).resolve().relative_to(RAIZ))
    except ValueError:
        rel = str(caminho_pauta)
    atual[media_id] = {"pauta": rel, "gancho": dados_pauta.get("gancho", "A"), "formato": formato,
                       "estilo": molde.removeprefix("estudio-").removeprefix("ident-").removesuffix(".html.tpl"),
                       "repost_de": dados_pauta.get("repost_de"), "publicado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    arquivo.write_text(json.dumps(atual, ensure_ascii=False, indent=1), encoding="utf-8")


def _publicar(publicar: bool, video: Path, dados_pauta: dict, repos: dict, registro: dict, caminho_pauta: Path,
              pasta_saida: Path, modelo_reels: str, formato: str, slides: list):
    """Publica o Reels (e o carrossel, se houver) e registra links, estilo e pauta do post. Usado pelo caminho normal
    e pelo de vídeo pronto (produtora), para os dois respeitarem a mesma cota, pausa de segurança e registros."""
    if publicar:
        legenda = montar_legenda(dados_pauta, repos)
        nome_base = pasta_saida.name
        url_video = hospedagem.publicar(video, f"{nome_base}-reels.mp4")
        ig = InstagramGraph(os.environ["INSTAGRAM_GRAPH_TOKEN"], os.environ["INSTAGRAM_USER_ID"])
        try:
            usados = ig.publicados_nas_ultimas_24h()
        except Exception:  # consultar a cota não pode impedir o post; só informa quando consegue
            usados = 0
        if usados >= LIMITE_SEGURO_POSTS_24H:
            raise SystemExit(f"a conta já usou {usados} publicações nas últimas 24 h (limite seguro: {LIMITE_SEGURO_POSTS_24H}); não publico")
        try:
            # Trial Reel (só pra quem não segue) no vídeo experimental da noite, quando a conta já tem acesso (1.000+):
            # testa estilos e ganchos sem cansar os seguidores; o Instagram promove sozinho o que performar.
            try:
                experimental = formato == "pixel2" and len(dados_pauta.get("itens", [])) == 1 and dados_pauta.get("palavra_chave") != "ESTUDIO"
                teste = experimental and ig.seguidores() >= MIN_SEGUIDORES_TRIAL
            except Exception:
                teste = False
            reels_publicado = ig.publicar_reels(url_video, legenda, teste=teste, colaboradores=dados_pauta.get("colaboradores"))
            registro["trial_reel"] = teste
            registro["publicado"] = True
            registro["legenda"] = legenda
            registro["reels"]["media_id"] = reels_publicado.media_id
            _registrar_links(dados_pauta, repos, registro) if repos else None  # o Reels já saiu: o bot já pode responder
            _registrar_estilo(reels_publicado.media_id, modelo_reels)
            _registrar_pauta(reels_publicado.media_id, caminho_pauta, dados_pauta, modelo_reels, formato)
            # Story desligado em 28/10: o Davi achou sem sentido (trecho do Reels repostado). Volta com STORIES=1
            # quando tiver um formato de Story próprio.
            if os.getenv("STORIES") == "1":
                try:  # Story avisando quem segue; se falhar, o Reels já saiu e segue a vida
                    arq_story = story.preparar(video, pasta_saida / "story.mp4")
                    url_story = hospedagem.publicar(arq_story, f"{nome_base}-story.mp4")
                    registro["story_media_id"] = ig.publicar_story(url_story).media_id
                except Exception as erro:
                    print(f"story não saiu ({str(erro)[:160]})")

            if slides:
                time.sleep(ESPERA_ENTRE_REELS_E_CARROSSEL_S)
                urls_slides = [
                    hospedagem.publicar(s, f"{nome_base}-slide-{i:02d}.png") for i, s in enumerate(slides, start=1)
                ]
                carrossel_publicado = ig.publicar_carrossel(urls_slides, legenda)
                registro["carrossel_media_id"] = carrossel_publicado.media_id
        except RuntimeError as erro:
            if pausa.e_bloqueio(str(erro)):
                pausa.ativar(str(erro))
                print("O Instagram acusou excesso de atividade: PAUSA DE SEGURANÇA de 24 h ligada (pautas/pausa.json).")
            raise

    if publicar and repos and registro["publicado"]:
        _registrar_links(dados_pauta, repos, registro)


def _executar_pronto(caminho_pauta: Path, dados_pauta: dict, pasta_saida: Path, publicar: bool) -> dict:
    """Pauta de VÍDEO PRONTO (feito pela produtora no GitHub Actions): baixa o MP4 já hospedado e só publica.

    A produtora sobe o vídeo para a release de mídia e põe a pauta na fila do maestro; aqui não se renderiza nada.
    """
    pasta_saida.mkdir(parents=True, exist_ok=True)
    video = pasta_saida / "reels.mp4"
    subprocess.run(["curl", "-sSLf", "-o", str(video), dados_pauta["video_pronto_url"]], check=True)
    repos = {item["repo"]: github_dados.buscar(item["repo"]) for item in dados_pauta.get("itens", [])}
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True).stdout.strip()
    registro = {"pauta": str(caminho_pauta), "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "fontes": [d.url for d in repos.values()], "estrelas": {r: d.estrelas for r, d in repos.items()},
                "reels": {"arquivo": str(video), "duracao_s": float(dur or 0)}, "carrossel": [], "publicado": False}
    _publicar(publicar, video, dados_pauta, repos, registro, caminho_pauta, pasta_saida,
              f"produtora-{dados_pauta.get('estilo', 'estilo')}", "pronto", [])
    (pasta_saida / "registro.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    return registro


def executar(caminho_pauta: Path, pasta_saida: Path, *, publicar: bool = False) -> dict:
    if publicar and pausa.ativa():
        raise SystemExit(f"pausa de segurança ativa ({pausa.motivo()}): não publico agora")
    dados_pauta = pauta.carregar(caminho_pauta)
    if dados_pauta.get("video_pronto_url"):
        return _executar_pronto(caminho_pauta, dados_pauta, pasta_saida, publicar)
    if dados_pauta.get("formato") == "pixel2":
        dados_pauta = cenas_pixel.normalizar_pauta(dados_pauta)
    erros = pauta.problemas(dados_pauta, ICONES)
    if erros:
        raise SystemExit("pauta inválida:\n- " + "\n- ".join(erros))

    # "prompt": molde sem lista de repositórios (ver modelos/prompt.html.tpl) — só Reels,
    # sem carrossel (o carrossel existe pra mostrar N itens, aqui só tem o prompt em si).
    formato = dados_pauta.get("formato")
    eh_prompt = formato in MOLDES_SO_REELS

    trabalho = pasta_saida / "trabalho"
    repos = {item["repo"]: github_dados.buscar(item["repo"]) for item in dados_pauta["itens"]}
    # Cartão só serve ao carrossel; o molde "prompt" não tem carrossel, então nem baixa.
    cartoes = {} if (eh_prompt or formato in MOLDES_COM_SLIDES) else {
        r: github_dados.baixar_cartao(r, trabalho / "cartoes" / f"{r.replace('/', '_')}.png") for r in repos
    }

    voz = criar_voz(dados_pauta)
    modelo_reels = MOLDES_SO_REELS.get(formato) or MOLDES_COM_SLIDES.get(formato) or "reels.html.tpl"
    # lista (vários repositórios) fica no visual pixel original: as 2 listas de 1.000+ views saíram nele, e a de
    # 28/10 no estilo "tier" fez 111. Os estilos de estúdio valem só pro vídeo de uma ferramenta e pra venda.
    if formato == "pixel2" and os.getenv("MOLDE_PIXEL2") != "1" and (len(repos) == 1 or dados_pauta.get("molde")):
        # a pauta pode fixar o estilo (ex.: vídeo de venda sempre no estilo mais vistoso)
        modelo_reels = dados_pauta.get("molde") or molde_estudio(dados_pauta.get("titulo", ""))
    if formato == "pixel2" and len(repos) == 1 and not dados_pauta.get("molde") and os.getenv("MOLDE_PIXEL2") != "1":
        # vídeo de uma ferramenta: rodízio por TODO o acervo de identidades (ident- com cenas próprias
        # do assunto, ou um molde estúdio comum) -- nunca só entre as 2 de identidade.py (2026-10-30).
        modelo_reels = identidade_do(dados_pauta.get("titulo", ""))
    video = None
    if (formato == "pixel2" and len(repos) == 1 and not dados_pauta.get("molde") and os.getenv("ESTUDIO_DIRETOR") == "1"):
        # estúdio com direção (src/estudio_instagram/diretor): roteiro por acontecimento + storyboard por frase +
        # portão de qualidade. Desligado por padrão; se o vídeo não passar no portão, cai no caminho antigo.
        from .diretor import fazer as diretor_fazer
        dados = next(iter(repos.values()))
        try:
            pasta_dir = trabalho / "diretor"
            res = diretor_fazer.produzir(diretor_fazer.fatos_do_repo(dados.repo), pasta_dir, palavra=dados_pauta["palavra_chave"])
            if res["aprovado"]:
                video = pasta_saida / "reels.mp4"
                pasta_saida.mkdir(parents=True, exist_ok=True)
                shutil.copy(pasta_dir / "final.mp4", video)
                duracao = res["qa"]["duracao"]
                modelo_reels = "diretor-palco"
            else:
                print(f"estúdio com direção reprovado no portão (média {res['media']}); usando o caminho antigo")
        except Exception as erro:
            print(f"estúdio com direção falhou ({erro}); usando o caminho antigo")
    if video is not None:
        pass
    elif modelo_reels.startswith("ident-"):
        dados = next(iter(repos.values()))
        cenas_pauta = cenas_da_pauta(dados_pauta) or [{}]
        plano = identidade.planejar(modelo_reels.removeprefix("ident-"), dados, buscar_readme(dados.repo),
                                    cenas_pauta[0].get("narracao") or dados.descricao, dados_pauta["palavra_chave"])
        duracao = identidade.montar(modelo_reels.removeprefix("ident-"), plano, voz, trabalho / "reels")
    else:
        duracao = montagem.montar_reels(dados_pauta, repos, voz, trabalho / "reels", modelo=modelo_reels)
    if video is None and modelo_reels.startswith("estudio-") and repos:
        # o molde tier mostra o print real do repositório; os outros ignoram o arquivo
        try:
            github_dados.baixar_cartao(next(iter(repos)), trabalho / "reels" / "assets" / "cartao.png")
        except Exception as erro:  # sem print o molde mostra um quadro vazio, não vale travar o post
            print(f"não baixei o cartão do repositório ({erro})")
    if video is None:
        video = render.renderizar_reels(trabalho / "reels", pasta_saida / "reels.mp4")

    if not PUBLICAR_CARROSSEL:
        slides = []
    elif formato in MOLDES_COM_SLIDES:
        n_slides = montagem.montar_carrossel_pixel(dados_pauta, trabalho / "carrossel")
        slides = render.renderizar_carrossel(trabalho / "carrossel", n_slides, pasta_saida / "carrossel")
    elif not eh_prompt:
        n_slides = montagem.montar_carrossel(dados_pauta, repos, cartoes, trabalho / "carrossel")
        slides = render.renderizar_carrossel(trabalho / "carrossel", n_slides, pasta_saida / "carrossel")
    else:
        slides = []

    registro = {
        "pauta": str(caminho_pauta),
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fontes": [d.url for d in repos.values()],
        "estrelas": {r: d.estrelas for r, d in repos.items()},
        "reels": {"arquivo": str(video), "duracao_s": duracao},
        "carrossel": [str(s) for s in slides],
        "publicado": False,
    }

    _publicar(publicar, video, dados_pauta, repos, registro, caminho_pauta, pasta_saida, modelo_reels, formato, slides)

    (pasta_saida / "registro.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    return registro


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pauta", type=Path, required=True)
    parser.add_argument("--saida", type=Path, default=None)
    parser.add_argument("--publicar", action="store_true", help="publica de verdade no Instagram via Publora")
    args = parser.parse_args()
    load_dotenv(RAIZ / ".env")
    saida = args.saida or RAIZ / "saida" / "instagram" / args.pauta.stem
    registro = executar(args.pauta, saida, publicar=args.publicar)
    print(json.dumps(registro, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
