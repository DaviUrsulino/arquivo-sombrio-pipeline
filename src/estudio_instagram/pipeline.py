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
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from . import cenas_pixel, github_dados, guia_dm, hospedagem, montagem, pauta, pausa, render
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
    "estudio-3d.html.tpl",       # @yan.gsouza: cenas 3D cinematográficas
    "estudio-rabisco.html.tpl",  # @oguiadaia: desenho à mão em papel
    "estudio-pixelui.html.tpl",  # @99hud: fonte pixel, janelas retrô, personagem
    "estudio-tier.html.tpl",     # @daniel.esantos: ranking S/A/B + print real do repo
    "estudio-telao.html.tpl",    # @jako.frames: tipografia cinética num monitor
    "estudio-papel.html.tpl",    # @nodir.ai_: tipografia 3D extrudada em papel creme
    "estudio-vidro.html.tpl",    # @igao.ia: interface de app em vidro escuro
    "estudio-voxel.html.tpl",    # @macelista: letreiro neon, fita crepe, mascote voxel 3D
]  # escuro e neon foram reprovados pelo Davi (2026-10-26)


def molde_estudio(titulo: str) -> str:
    return MOLDES_ESTUDIO[sum(ord(c) for c in titulo) % len(MOLDES_ESTUDIO)]


# Carrossel desligado (2026-10-26): cada post saía duplicado (Reels + carrossel com a mesma legenda), o que
# dividia o alcance e cansava quem segue. Volta a ligar só com `PUBLICAR_CARROSSEL=1` no ambiente.
MIN_SEGUIDORES_TRIAL = 1000  # Trial Reels só liberam a partir daqui
PUBLICAR_CARROSSEL = os.getenv("PUBLICAR_CARROSSEL") == "1"


def montar_legenda(dados_pauta: dict, repos: dict) -> str:
    """Legenda curta + chamada + hashtags. Pauta com `legenda` própria (vídeo de venda) usa o texto dela."""
    if dados_pauta.get("legenda"):
        return dados_pauta["legenda"][:LIMITE_LEGENDA_INSTAGRAM]
    hashtags = " ".join(f"#{t.replace('/', '').replace('-', '')}" for t in ["claude", "claudecode", "github", "ia"])
    passos = dados_pauta.get("passos") or []
    bloco_passos = ""
    if passos:
        bloco_passos = "Salva este vídeo pra usar com calma:\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(passos, 1)) + "\n\n"
    # 1ª linha da legenda = o gancho falado (problema/benefício pra quem assiste), que é o que segura o "ver mais";
    # a descrição da ferramenta sozinha ("Componentes de vídeo para...") foi o padrão dos posts que menos renderam.
    cenas = dados_pauta.get("cenas") or []
    gancho = (cenas[0].get("narracao") or "").strip() if cenas else ""
    primeira = gancho or dados_pauta['capa']['subtitulo'].capitalize()
    texto = (
        f"{primeira}\n\n"
        f"{bloco_passos}"
        f"Comenta {dados_pauta['palavra_chave']} que eu te mando o link no direct.\n"
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
    atual[media_id] = molde.removeprefix("estudio-").removesuffix(".html.tpl")
    arquivo.write_text(json.dumps(atual, ensure_ascii=False, indent=1), encoding="utf-8")


def executar(caminho_pauta: Path, pasta_saida: Path, *, publicar: bool = False) -> dict:
    if publicar and pausa.ativa():
        raise SystemExit(f"pausa de segurança ativa ({pausa.motivo()}): não publico agora")
    dados_pauta = pauta.carregar(caminho_pauta)
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
    if formato == "pixel2" and os.getenv("MOLDE_PIXEL2") != "1":
        # a pauta pode fixar o estilo (ex.: vídeo de venda sempre no estilo mais vistoso)
        modelo_reels = dados_pauta.get("molde") or molde_estudio(dados_pauta.get("titulo", ""))
    duracao = montagem.montar_reels(dados_pauta, repos, voz, trabalho / "reels", modelo=modelo_reels)
    if modelo_reels.startswith("estudio-") and repos:
        # o molde tier mostra o print real do repositório; os outros ignoram o arquivo
        try:
            github_dados.baixar_cartao(next(iter(repos)), trabalho / "reels" / "assets" / "cartao.png")
        except Exception as erro:  # sem print o molde mostra um quadro vazio, não vale travar o post
            print(f"não baixei o cartão do repositório ({erro})")
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
            reels_publicado = ig.publicar_reels(url_video, legenda, teste=teste)
            registro["trial_reel"] = teste
            registro["publicado"] = True
            registro["legenda"] = legenda
            registro["reels"]["media_id"] = reels_publicado.media_id
            _registrar_links(dados_pauta, repos, registro) if repos else None  # o Reels já saiu: o bot já pode responder
            _registrar_estilo(reels_publicado.media_id, modelo_reels)

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
