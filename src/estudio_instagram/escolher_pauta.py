"""Busca repositórios em alta, descarta o que já virou post e escreve uma pauta nova.

Uso:
    python -m src.estudio_instagram.escolher_pauta --saida pautas/auto-2026-10-14.json
"""

import argparse
import json
from datetime import date
from pathlib import Path

from . import github_dados, selecao
from .historico import contar_pautas, registrar

RAIZ = Path(__file__).resolve().parents[2]


def executar(buscas: list[str], quantidade: int, titulo: str | None, palavra_chave: str,
             estilo: str | None = None, formato: str | None = None) -> dict:
    candidatos, vistos = [], set()
    for consulta in buscas:
        for repo in github_dados.buscar_candidatos(consulta):
            if repo.repo not in vistos:
                vistos.add(repo.repo)
                candidatos.append(repo)

    indice = contar_pautas()
    formato = formato or selecao.escolher_formato(indice)
    quantidade_real = 1 if formato == "aprofundado" else quantidade
    escolhidos = selecao.escolher_repos(candidatos, quantidade=quantidade_real)
    if len(escolhidos) < quantidade_real:
        raise SystemExit(
            f"só achei {len(escolhidos)} repositório(s) inédito(s) de {len(candidatos)} candidatos — "
            "aumenta `buscas` ou baixa `quantidade`"
        )

    if formato == "aprofundado":
        titulo = titulo or f"{selecao.nome_exibicao(escolhidos[0].repo)} — {date.today().isoformat()}"
        return selecao.montar_pauta_aprofundada(escolhidos[0], titulo=titulo, palavra_chave=palavra_chave)

    titulo = titulo or f"{quantidade_real} repositórios grátis — {date.today().isoformat()}"
    estilo = estilo or selecao.escolher_estilo(indice)
    return selecao.montar_pauta(escolhidos, titulo=titulo, palavra_chave=palavra_chave, estilo=estilo)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--buscas", nargs="+", default=selecao.BUSCAS_PADRAO)
    parser.add_argument("--quantidade", type=int, default=5, help="só vale pro formato 'curto'")
    parser.add_argument("--palavra-chave", default="GITHUB")
    parser.add_argument("--titulo", default=None)
    parser.add_argument("--estilo", choices=selecao.ESTILOS, default=None, help="só vale pro formato 'curto'; padrão: alterna sozinho")
    parser.add_argument("--formato", choices=selecao.FORMATOS, default=None, help="padrão: alterna sozinho (2 'curto' pra 1 'aprofundado')")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()

    nova_pauta = executar(args.buscas, args.quantidade, args.titulo, args.palavra_chave, args.estilo, args.formato)
    print(f"gancho: {nova_pauta['capa']['linha1']} {nova_pauta['capa']['linha2']}")
    args.saida.write_text(json.dumps(nova_pauta, ensure_ascii=False, indent=2), encoding="utf-8")
    registrar([item["repo"] for item in nova_pauta["itens"]])
    print(f"pauta escrita em {args.saida}")
    for item in nova_pauta["itens"]:
        print(f"  - {item['repo']}")


if __name__ == "__main__":
    main()
