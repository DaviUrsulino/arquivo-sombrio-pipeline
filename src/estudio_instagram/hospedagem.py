"""Hospeda mídia publicamente numa GitHub Release do próprio repositório, pra servir de
`video_url`/`image_url` pra Instagram Graph API (que não aceita upload de arquivo local,
só URL pública — ver graph_api.py).

Usa uma release fixa (`TAG`) como "pasta pública": o chamador passa um nome único por
arquivo (prefixo da pauta), então nunca colide com o anterior, e o asset fica disponível
na hora via o campo `url` devolvido por `gh release view --json assets`.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

TAG = "midia-publicacao"


def _rodar(args: list[str], executar=subprocess.run) -> str:
    resultado = executar(args, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr)
    return resultado.stdout


def publicar(arquivo: Path, nome: str, executar=subprocess.run) -> str:
    """Sobe `arquivo` como asset `nome` da release e devolve a URL pública de download."""
    with tempfile.TemporaryDirectory() as pasta_tmp:
        renomeado = Path(pasta_tmp) / nome
        shutil.copyfile(arquivo, renomeado)
        _rodar(["gh", "release", "upload", TAG, str(renomeado), "--clobber"], executar)
    saida = _rodar(["gh", "release", "view", TAG, "--json", "assets"], executar)
    assets = json.loads(saida)["assets"]
    casado = next(a for a in assets if a["name"] == nome)
    return casado["url"]
