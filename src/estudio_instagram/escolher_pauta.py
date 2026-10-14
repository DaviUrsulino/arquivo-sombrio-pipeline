"""Busca repositórios em alta, descarta o que já virou post e escreve uma pauta nova.

Uso:
    python -m src.estudio_instagram.escolher_pauta --saida pautas/auto-2026-10-14.json
"""

import argparse
import json
from datetime import date
from pathlib import Path

from . import github_dados, selecao
from .historico import registrar

RAIZ = Path(__file__).resolve().parents[2]


def executar(buscas: list[str], quantidade: int, titulo: str | None, palavra_chave: str) -> dict:
    candidatos, vistos = [], set()
    for consulta in buscas:
        for repo in github_dados.buscar_candidatos(consulta):
            if repo.repo not in vistos:
                vistos.add(repo.repo)
                candidatos.append(repo)
    escolhidos = selecao.escolher_repos(candidatos, quantidade=quantidade)
    if len(escolhidos) < quantidade:
        raise SystemExit(
            f"só achei {len(escolhidos)} repositório(s) inédito(s) de {len(candidatos)} candidatos — "
            "aumenta `buscas` ou baixa `quantidade`"
        )
    titulo = titulo or f"{quantidade} repositórios grátis — {date.today().isoformat()}"
    return selecao.montar_pauta(escolhidos, titulo=titulo, palavra_chave=palavra_chave)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--buscas", nargs="+", default=selecao.BUSCAS_PADRAO)
    parser.add_argument("--quantidade", type=int, default=5)
    parser.add_argument("--palavra-chave", default="GITHUB")
    parser.add_argument("--titulo", default=None)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()

    nova_pauta = executar(args.buscas, args.quantidade, args.titulo, args.palavra_chave)
    args.saida.write_text(json.dumps(nova_pauta, ensure_ascii=False, indent=2), encoding="utf-8")
    registrar([item["repo"] for item in nova_pauta["itens"]])
    print(f"pauta escrita em {args.saida}")
    for item in nova_pauta["itens"]:
        print(f"  - {item['repo']}")


if __name__ == "__main__":
    main()
