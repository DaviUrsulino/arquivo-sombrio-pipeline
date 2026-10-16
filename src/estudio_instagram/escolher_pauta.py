"""Busca repositórios em alta, descarta o que já virou post e escreve uma pauta nova.

Por padrão, antes de buscar no GitHub, olha o que está bombando nos concorrentes hoje
(Apify) e prioriza a busca por esse tema — pra não ficar sempre nos mesmos termos fixos.
Se o Apify falhar ou faltar token, cai sozinho pros termos padrão, sem travar a execução
(RNF: um problema de terceiro não pode derrubar o cron).

Uso:
    python -m src.estudio_instagram.escolher_pauta --saida pautas/auto-2026-10-14.json
    python -m src.estudio_instagram.escolher_pauta --saida pautas/x.json --sem-tendencias
"""

import argparse
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from . import concorrentes, github_dados, selecao
from .historico import contar_pautas, registrar

RAIZ = Path(__file__).resolve().parents[2]

# Perfis do nicho mapeados em 2026-10-14/16 (ver docs/estudio-instagram.md) — os que mais
# engajam com conteúdo de Claude Code / IA pra devs no Brasil.
PERFIS_CONCORRENTES = [
    "fabianocarvalhojr", "brunoptrevisan", "tiagolemosx", "gurudoprompt",
    "rodrigotadewald", "brusantanna.ai", "oguiadaia", "ssupernova.studio",
]


def buscas_do_dia(buscas_padrao: list[str]) -> list[str]:
    """Tenta priorizar pelo que está bombando hoje; sem token ou com falha de rede,
    devolve `buscas_padrao` sem mais delongas — nunca propaga o erro pra cima."""
    token = os.getenv("APIFY_TOKEN", "").strip()
    if not token:
        print("sem APIFY_TOKEN — usando as buscas padrão, sem olhar tendência de hoje")
        return buscas_padrao
    try:
        posts = concorrentes.coletar(token, PERFIS_CONCORRENTES, limite_por_perfil=15)
        quentes = concorrentes.temas_em_alta(posts)
        buscas = concorrentes.buscas_do_dia(posts, buscas_padrao)
        print(f"temas em alta hoje: {quentes or '(nenhum claro)'}")
        return buscas
    except Exception as erro:  # Apify fora do ar, timeout, etc. — não é motivo pra falhar o cron.
        print(f"não deu pra puxar tendência hoje ({erro}) — usando as buscas padrão")
        return buscas_padrao


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
    parser.add_argument("--buscas", nargs="+", default=None, help="padrão: olha tendência de hoje + termos fixos")
    parser.add_argument("--sem-tendencias", action="store_true", help="ignora o Apify, usa só os termos fixos")
    parser.add_argument("--quantidade", type=int, default=5, help="só vale pro formato 'curto'")
    parser.add_argument("--palavra-chave", default="GITHUB")
    parser.add_argument("--titulo", default=None)
    parser.add_argument("--estilo", choices=selecao.ESTILOS, default=None, help="só vale pro formato 'curto'; padrão: alterna sozinho")
    parser.add_argument("--formato", choices=selecao.FORMATOS, default=None, help="padrão: alterna sozinho (2 'curto' pra 1 'aprofundado')")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    load_dotenv(RAIZ / ".env")

    if args.buscas is not None:
        buscas = args.buscas
    elif args.sem_tendencias:
        buscas = selecao.BUSCAS_PADRAO
    else:
        buscas = buscas_do_dia(selecao.BUSCAS_PADRAO)

    nova_pauta = executar(buscas, args.quantidade, args.titulo, args.palavra_chave, args.estilo, args.formato)
    print(f"gancho: {nova_pauta['capa']['linha1']} {nova_pauta['capa']['linha2']}")
    args.saida.write_text(json.dumps(nova_pauta, ensure_ascii=False, indent=2), encoding="utf-8")
    registrar([item["repo"] for item in nova_pauta["itens"]])
    print(f"pauta escrita em {args.saida}")
    for item in nova_pauta["itens"]:
        print(f"  - {item['repo']}")


if __name__ == "__main__":
    main()
