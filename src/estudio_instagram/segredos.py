"""Textos que valem dinheiro (prompts, briefing do agente) moram num repositório PRIVADO, não neste público.

Por que (Davi, 2026-11-04): este repositório é público para o GitHub Actions sair de graça, então qualquer um podia
copiar a fórmula de roteiro, o briefing do agente e o estudo das referências, que são a base do produto à venda.
O repositório privado DaviUrsulino/arquivo-sombrio-segredos fica em ./segredos (no PC, um clone; no Actions, um
checkout com chave de implantação só de leitura). O código público só sabe o NOME de cada texto.
"""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA = Path(os.environ.get("SEGREDOS_DIR", RAIZ / "segredos"))


def texto(nome: str) -> str:
    arquivo = PASTA / "prompts" / f"{nome}.txt"
    if arquivo.exists():
        return arquivo.read_text(encoding="utf-8")
    if os.environ.get("PYTEST_CURRENT_TEST"):  # testes do CI público rodam sem o repositório privado
        return f"[segredo {nome}] __FALAS__ __POLITICA__ __ANGULO__"
    raise RuntimeError(f"falta o texto privado '{nome}' em {PASTA}/prompts (clone o repositório arquivo-sombrio-segredos em ./segredos)")
