"""Memória do que já virou post, para o seletor automático nunca repetir pauta (RN-1 de docs/)."""

import json
from pathlib import Path

PADRAO = Path(__file__).resolve().parents[2] / "pautas" / "historico.json"


def _ler(arquivo: Path) -> dict:
    if not arquivo.exists():
        return {"repositorios_usados": [], "pautas_geradas": 0}
    return json.loads(arquivo.read_text(encoding="utf-8"))


def carregar(arquivo: Path = PADRAO) -> set[str]:
    return set(_ler(arquivo).get("repositorios_usados", []))


def contar_pautas(arquivo: Path = PADRAO) -> int:
    """Quantas pautas já foram geradas — usado por `selecao.escolher_estilo` pra alternar o gancho."""
    return _ler(arquivo).get("pautas_geradas", 0)


def registrar(repos: list[str], arquivo: Path = PADRAO):
    dados = _ler(arquivo)
    usados = set(dados.get("repositorios_usados", []))
    usados.update(repos)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps({
        "repositorios_usados": sorted(usados), "pautas_geradas": dados.get("pautas_geradas", 0) + 1,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def inedito(candidatos: list[str], arquivo: Path = PADRAO) -> list[str]:
    """Mantém a ordem de `candidatos`, tirando o que já foi usado."""
    usados = carregar(arquivo)
    return [r for r in candidatos if r not in usados]
