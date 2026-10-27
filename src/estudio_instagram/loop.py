"""Loops de 8-10 s no estilo do @pixosly (gerados pelo Davi no Google Flow) postados um por noite.

O Davi solta o MP4 cru do Flow em `loops/fila/` (e, se quiser, um .txt com o mesmo nome contendo a legenda).
Este módulo pega o mais antigo, emenda o fim no começo (loop sem pulo), mistura uma trilha lo-fi original por
cima do som do Flow, sobe em 1080x1920 no formato que o Instagram aceita e publica. Depois move pra
`loops/postados/`. Sem emoji na legenda (pedido do Davi).

    python -m src.estudio_instagram.loop --publicar
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from . import hospedagem, pausa
from .graph_api import InstagramGraph

RAIZ = Path(__file__).resolve().parents[2]
FILA = RAIZ / "loops" / "fila"
POSTADOS = RAIZ / "loops" / "postados"
TRANSICAO_S = 0.6
LEGENDA_PADRAO = "madrugada de deploy\n\n#pixelart #lofi #programacao #anime"


def proximo(pasta: Path = FILA) -> Path | None:
    videos = sorted(pasta.glob("*.mp4")) if pasta.exists() else []
    return videos[0] if videos else None


def legenda_de(video: Path) -> str:
    txt = video.with_suffix(".txt")
    return txt.read_text(encoding="utf-8").strip() if txt.exists() else LEGENDA_PADRAO


def _duracao(video: Path) -> float:
    saida = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True, check=True)
    return float(saida.stdout.strip())


def _tem_audio(video: Path) -> bool:
    saida = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True)
    return bool(saida.stdout.strip())


def preparar(entrada: Path, saida: Path) -> Path:
    """Loop sem pulo + trilha lo-fi + 1080x1920 H.264 30 fps (o que o Instagram aceita sem recusar)."""
    d = _duracao(entrada)
    final = d - TRANSICAO_S
    trilha = saida.with_suffix(".wav")
    subprocess.run([sys.executable, str(RAIZ / "scripts" / "gerar_lofi.py"), f"{final:.3f}", str(trilha)], check=True)
    video = (f"[0:v]split[v1][v2];[v1]trim={TRANSICAO_S}:{d},setpts=PTS-STARTPTS[corpo];"
             f"[v2]trim=0:{TRANSICAO_S},setpts=PTS-STARTPTS[ini];"
             f"[corpo][ini]xfade=transition=fade:duration={TRANSICAO_S}:offset={final - TRANSICAO_S:.3f},"
             f"scale=1080:1920:flags=lanczos,fps=30,format=yuv420p[v]")
    if _tem_audio(entrada):
        audio = (f";[0:a]atrim={TRANSICAO_S}:{d},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={final - 0.4:.3f}:d=0.4,"
                 f"volume=0.35[amb];[1:a]volume=0.9[mus];[mus][amb]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.9[a]")
    else:
        audio = ";[1:a]volume=0.9[a]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(entrada), "-i", str(trilha), "-filter_complex", video + audio,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-profile:v", "high", "-b:v", "6M", "-maxrate", "8M",
                    "-bufsize", "12M", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k", "-movflags", "+faststart",
                    str(saida)], check=True)
    return saida


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--publicar", action="store_true")
    args = parser.parse_args()
    load_dotenv(RAIZ / ".env")
    video = proximo()
    if not video:
        print("fila de loops vazia")
        return
    (RAIZ / "saida" / "loops").mkdir(parents=True, exist_ok=True)
    pronto = preparar(video, RAIZ / "saida" / "loops" / f"{video.stem}-pronto.mp4")
    print(f"loop pronto: {pronto}")
    if not args.publicar:
        return
    if pausa.ativa():
        raise SystemExit(f"pausa de segurança ativa ({pausa.motivo()})")
    ig = InstagramGraph(os.environ["INSTAGRAM_GRAPH_TOKEN"], os.environ["INSTAGRAM_USER_ID"])
    url = hospedagem.publicar(pronto, f"loop-{video.stem}.mp4")
    post = ig.publicar_reels(url, legenda_de(video))
    print(f"publicado: {post.media_id}")
    POSTADOS.mkdir(parents=True, exist_ok=True)
    for arq in (video, video.with_suffix(".txt")):
        if arq.exists():
            shutil.move(str(arq), POSTADOS / arq.name)


if __name__ == "__main__":
    main()
