"""Memória do que já virou post, para o seletor automático nunca repetir pauta (RN-1 de docs/)."""

import json
from pathlib import Path

PADRAO = Path(__file__).resolve().parents[2] / "pautas" / "historico.json"


def carregar(arquivo: Path = PADRAO) -> set[str]:
    if not arquivo.exists():
        return set()
    return set(json.loads(arquivo.read_text(encoding="utf-8")).get("repositorios_usados", []))


def registrar(repos: list[str], arquivo: Path = PADRAO):
    usados = carregar(arquivo)
    usados.update(repos)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps({"repositorios_usados": sorted(usados)}, ensure_ascii=False, indent=2), encoding="utf-8")


def inedito(candidatos: list[str], arquivo: Path = PADRAO) -> list[str]:
    """Mantém a ordem de `candidatos`, tirando o que já foi usado."""
    usados = carregar(arquivo)
    return [r for r in candidatos if r not in usados]
