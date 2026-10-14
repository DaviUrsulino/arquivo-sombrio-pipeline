"""Chama o CLI do Hyperframes para gerar o MP4 do Reels e os PNG do carrossel."""

import re
import shutil
import subprocess
from pathlib import Path

VERSAO_HYPERFRAMES = "0.8.154"


def _hyperframes(*args: str, pasta: Path) -> str:
    resultado = subprocess.run(
        ["npx", "--yes", f"hyperframes@{VERSAO_HYPERFRAMES}", *args],
        cwd=pasta, capture_output=True, text=True, check=False,
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"hyperframes {args[0]} falhou:\n{resultado.stdout[-2000:]}\n{resultado.stderr[-2000:]}")
    return resultado.stdout


def renderizar_reels(pasta: Path, saida: Path) -> Path:
    saida = Path(saida).resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)
    _hyperframes("render", "--quality", "high", "--output", str(saida), pasta=Path(pasta))
    return saida


def renderizar_carrossel(pasta: Path, n_slides: int, destino: Path) -> list[Path]:
    """Tira um snapshot no meio de cada segundo (um slide por segundo) e copia os PNG."""
    momentos = ",".join(f"{i + 0.5}" for i in range(n_slides))
    saida = _hyperframes("snapshot", "--at", momentos, pasta=Path(pasta))
    achado = re.search(r"(\S*snapshots/[\w-]+)/contact-sheet", saida)
    if not achado:
        raise RuntimeError("não achei a pasta de snapshots na saída do hyperframes")
    pasta_snap = Path(achado.group(1))
    if not pasta_snap.is_absolute():
        pasta_snap = Path(pasta) / pasta_snap
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    quadros = sorted(pasta_snap.glob("frame-*.png"))[:n_slides]
    slides = []
    for i, quadro in enumerate(quadros, start=1):
        alvo = destino / f"slide-{i:02d}.png"
        shutil.copy(quadro, alvo)
        slides.append(alvo)
    return slides
