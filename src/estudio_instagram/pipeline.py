"""Gera, e opcionalmente publica, o Reels e o carrossel de uma pauta.

Uso:
    python -m src.estudio_instagram.pipeline --pauta pautas/5-repos-claude-code.json
    python -m src.estudio_instagram.pipeline --pauta pautas/5-repos-claude-code.json --publicar

Saída em saida/instagram/<nome-da-pauta>/: reels.mp4, carrossel/slide-NN.png e registro.json.
Publicar exige PUBLORA_API_KEY e INSTAGRAM_PLATFORM_ID no .env (ver docs/estudio-instagram.md).
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from . import github_dados, montagem, pauta, render
from .publicacao import Publora
from .voz import ElevenLabs

RAIZ = Path(__file__).resolve().parents[2]
ICONES = {p.stem for p in (montagem.MODELOS / "assets" / "icons").glob("*.svg")}
LIMITE_LEGENDA_INSTAGRAM = 2200


def montar_legenda(dados_pauta: dict, repos: dict) -> str:
    """Legenda curta + chamada + hashtags, com link das fontes no primeiro comentário fica pro Publora."""
    hashtags = " ".join(f"#{t.replace('/', '').replace('-', '')}" for t in ["claude", "claudecode", "github", "ia"])
    texto = (
        f"{dados_pauta['capa']['subtitulo'].capitalize()} 🤖\n\n"
        f"{dados_pauta['chamada']['pergunta'].capitalize()} "
        f"Comenta {dados_pauta['palavra_chave']} que eu te mando no direct.\n\n{hashtags}"
    )
    return texto[:LIMITE_LEGENDA_INSTAGRAM]


def executar(caminho_pauta: Path, pasta_saida: Path, *, publicar: bool = False) -> dict:
    dados_pauta = pauta.carregar(caminho_pauta)
    erros = pauta.problemas(dados_pauta, ICONES)
    if erros:
        raise SystemExit("pauta inválida:\n- " + "\n- ".join(erros))

    trabalho = pasta_saida / "trabalho"
    repos = {item["repo"]: github_dados.buscar(item["repo"]) for item in dados_pauta["itens"]}
    cartoes = {r: github_dados.baixar_cartao(r, trabalho / "cartoes" / f"{r.replace('/', '_')}.png") for r in repos}

    voz = ElevenLabs(dados_pauta["voz"]["id"], dados_pauta["voz"]["modelo"], RAIZ / ".cache" / "voz")
    duracao = montagem.montar_reels(dados_pauta, repos, voz, trabalho / "reels")
    n_slides = montagem.montar_carrossel(dados_pauta, repos, cartoes, trabalho / "carrossel")

    video = render.renderizar_reels(trabalho / "reels", pasta_saida / "reels.mp4")
    slides = render.renderizar_carrossel(trabalho / "carrossel", n_slides, pasta_saida / "carrossel")

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
        publora = Publora(os.environ["PUBLORA_API_KEY"], os.environ["INSTAGRAM_PLATFORM_ID"])
        reels_publicado = publora.publicar_reels(video, legenda, agora=True)
        carrossel_publicado = publora.publicar_carrossel(slides, legenda, agora=True)
        registro["publicado"] = True
        registro["legenda"] = legenda
        registro["reels"]["post_group_id"] = reels_publicado.post_group_id
        registro["carrossel_post_group_id"] = carrossel_publicado.post_group_id

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
