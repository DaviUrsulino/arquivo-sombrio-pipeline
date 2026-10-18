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
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from . import cenas_pixel, github_dados, hospedagem, montagem, pauta, render
from .graph_api import InstagramGraph
from .voz import ComReserva, EdgeTTS, ElevenLabs, GeminiTTS

RAIZ = Path(__file__).resolve().parents[2]
ICONES = {p.stem for p in (montagem.MODELOS / "assets" / "icons").glob("*.svg")}
LIMITE_LEGENDA_INSTAGRAM = 2200
# Formatos que geram só o Reels (sem carrossel) e o molde visual de cada um.
MOLDES_SO_REELS = {"prompt": "prompt.html.tpl", "diagrama": "diagrama.html.tpl", "palito": "palito.html.tpl",
                   "repo": "repo.html.tpl"}
# Formatos com Reels + carrossel próprio (os slides vêm da pauta, não de repositórios).
MOLDES_COM_SLIDES = {"pixel": "pixel.html.tpl", "pixel2": "pixel2.html.tpl"}


def montar_legenda(dados_pauta: dict, repos: dict) -> str:
    """Legenda curta + chamada + hashtags, com link das fontes no primeiro comentário fica pro Publora."""
    hashtags = " ".join(f"#{t.replace('/', '').replace('-', '')}" for t in ["claude", "claudecode", "github", "ia"])
    texto = (
        f"{dados_pauta['capa']['subtitulo'].capitalize()} 🤖\n\n"
        f"{dados_pauta['chamada']['pergunta'].capitalize()} "
        f"Comenta {dados_pauta['palavra_chave']} que eu te mando no direct.\n\n{hashtags}"
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
    primeiro = next(iter(repos.values()))
    mensagem = (f"Oi! Aqui está o repositório {primeiro.repo.split('/', 1)[1]}: {primeiro.url}\n"
                f"Se curtir, segue o @robo.estagiario pra mais ferramentas de IA 🤖")
    arquivo = RAIZ / "pautas" / "links_por_post.json"
    atual = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    for media_id in (registro["reels"].get("media_id"), registro.get("carrossel_media_id")):
        if media_id:
            atual[media_id] = {"palavra": dados_pauta["palavra_chave"], "mensagem": mensagem, "repo": primeiro.repo}
    arquivo.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")


def executar(caminho_pauta: Path, pasta_saida: Path, *, publicar: bool = False) -> dict:
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
    duracao = montagem.montar_reels(dados_pauta, repos, voz, trabalho / "reels", modelo=modelo_reels)
    video = render.renderizar_reels(trabalho / "reels", pasta_saida / "reels.mp4")

    if formato in MOLDES_COM_SLIDES:
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
        reels_publicado = ig.publicar_reels(url_video, legenda)
        registro["publicado"] = True
        registro["legenda"] = legenda
        registro["reels"]["media_id"] = reels_publicado.media_id

        if not eh_prompt:
            urls_slides = [
                hospedagem.publicar(s, f"{nome_base}-slide-{i:02d}.png") for i, s in enumerate(slides, start=1)
            ]
            carrossel_publicado = ig.publicar_carrossel(urls_slides, legenda)
            registro["carrossel_media_id"] = carrossel_publicado.media_id

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
