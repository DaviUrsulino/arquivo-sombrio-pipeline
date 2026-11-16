"""Libera um vídeo da revisão para a fila do maestro: python scripts/liberar.py <trecho do nome> [--descartar]
Só rode depois de assistir (folha de contato + roteiro). Vídeo ruim: --descartar."""
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REV, FILA, LIXO = (RAIZ / "pautas/viral" / n for n in ("revisao", "fila", "fila_descartada"))

if __name__ == "__main__":
    achados = [f for f in sorted(REV.glob("*.json")) if sys.argv[1] in f.name]
    if len(achados) != 1:
        sys.exit(f"{len(achados)} arquivos casam com {sys.argv[1]!r}: {[f.name for f in achados]}")
    destino = LIXO if "--descartar" in sys.argv else FILA
    destino.mkdir(parents=True, exist_ok=True)
    shutil.move(achados[0], destino / achados[0].name)
    print(f"{achados[0].name} -> {destino.relative_to(RAIZ)}")
