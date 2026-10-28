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
import re
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

from . import assunto_quente, concorrentes, github_dados, lista, montagem, roteirista, selecao
from .historico import contar_pautas, inedito, registrar

RAIZ = Path(__file__).resolve().parents[2]

# Perfis do nicho mapeados em 2026-10-14/16 (ver docs/estudio-instagram.md) — os que mais
# engajam com conteúdo de Claude Code / IA pra devs no Brasil.
PERFIS_CONCORRENTES = [
    # Perfis brasileiros do nicho (IA, Claude Code, GitHub) que mais engajam: é daqui que sai o tema do dia.
    # Revisado em 2026-10-27: saiu o gurudoprompt (posts sem views públicas).
    "gab.gouvea", "brusantanna.ai", "brunoptrevisan", "tiagolemosx", "yan.gsouza", "99hud", "igao.ia",
    "macelista", "daniel.esantos", "fabianocarvalhojr", "rodrigotadewald", "oguiadaia", "ssupernova.studio",
    "claudedrop",
]
# Referências só de visual/animação: não entram no scraping diário (não ajudam a escolher tema) e ficam
# anotadas aqui pra estudo manual quando for criar estilo novo.
REFERENCIAS_VISUAIS = ["ismjeff.ia", "_aighostlab", "jako.frames", "ckubedasskills", "pixosly", "thiagomendesmed",
                       "nodir.ai_", "evolving.ai", "airesearches"]


# Orçamento do Apify: plano grátis de US$ 5/mês. O instagram-scraper cobra ~US$ 0,0027 por post (medido em
# 2026-10-26: 359 posts = US$ 0,97). Reservando US$ 0,50 pra análises manuais, sobram ~US$ 0,15/dia = ~55 posts.
# Em vez de cortar perfis, faz rodízio: PERFIS_POR_DIA perfis por dia, POSTS_POR_PERFIL posts recentes de cada,
# e em poucos dias todos os perfis de PERFIS_CONCORRENTES são lidos. Uma leitura só por dia (cache em TENDENCIAS).
PERFIS_POR_DIA = 10
POSTS_POR_PERFIL = 5


def perfis_do_dia(dia_ordinal: int, perfis: list[str] = PERFIS_CONCORRENTES, por_dia: int = PERFIS_POR_DIA) -> list[str]:
    """Fatia do rodízio pro dia: dias seguidos pegam fatias seguidas, dando a volta na lista."""
    unicos = list(dict.fromkeys(perfis))
    inicio = (dia_ordinal * por_dia) % len(unicos)
    return [unicos[(inicio + k) % len(unicos)] for k in range(min(por_dia, len(unicos)))]


TENDENCIAS = RAIZ / "pautas" / "tendencias_do_dia.json"


def buscas_do_dia(buscas_padrao: list[str], hoje: str | None = None, arquivo: Path = TENDENCIAS) -> list[str]:
    """Tenta priorizar pelo que está bombando hoje; sem token ou com falha de rede,
    devolve `buscas_padrao` sem mais delongas — nunca propaga o erro pra cima."""
    hoje = hoje or date.today().isoformat()
    if arquivo.exists():
        salvo = json.loads(arquivo.read_text(encoding="utf-8"))
        if salvo.get("dia") == hoje:
            print(f"tendências de hoje já lidas: {salvo.get('temas')}")
            return salvo["buscas"]
    token = os.getenv("APIFY_TOKEN", "").strip()
    if not token:
        print("sem APIFY_TOKEN — usando as buscas padrão, sem olhar tendência de hoje")
        return buscas_padrao
    try:
        perfis = perfis_do_dia(date.fromisoformat(hoje).toordinal())
        posts = concorrentes.coletar(token, perfis, limite_por_perfil=POSTS_POR_PERFIL)
        quentes = concorrentes.temas_em_alta(posts)
        buscas = concorrentes.buscas_do_dia(posts, buscas_padrao)
        print(f"temas em alta hoje: {quentes or '(nenhum claro)'}")
        arquivo.write_text(json.dumps({"dia": hoje, "temas": quentes, "buscas": buscas}, ensure_ascii=False, indent=1), encoding="utf-8")
        return buscas
    except Exception as erro:  # Apify fora do ar, sem crédito, timeout — não é motivo pra falhar o cron.
        print(f"não deu pra puxar tendência hoje ({erro}) — usando as buscas padrão")
        return buscas_padrao


def _candidatos(buscas: list[str], **filtro) -> list:
    candidatos, vistos = [], set()
    for consulta in buscas:
        for repo in github_dados.buscar_candidatos(consulta, **filtro):
            if repo.repo not in vistos:
                vistos.add(repo.repo)
                candidatos.append(repo)
    return candidatos


FOCO = RAIZ / "pautas" / "foco.json"


def ler_foco(arquivo: Path = FOCO) -> dict | None:
    """Foco temporário de tema (pautas/foco.json). None quando não há foco ou ele já acabou."""
    if not arquivo.exists():
        return None
    foco = json.loads(arquivo.read_text(encoding="utf-8"))
    return foco if foco.get("restantes", 0) > 0 and foco.get("buscas") else None


def gastar_foco(arquivo: Path = FOCO):
    foco = json.loads(arquivo.read_text(encoding="utf-8"))
    foco["restantes"] = max(0, foco.get("restantes", 0) - 1)
    arquivo.write_text(json.dumps(foco, ensure_ascii=False, indent=2), encoding="utf-8")


def quentes_ineditos(limite: int = 6, minimo_estrelas: int = 100, fonte=assunto_quente.do_dia) -> list:
    """Repositórios que estão bombando hoje (GitHub Trending, Hacker News, GitHub novos) e ainda não viraram post,
    do mais quente pro menos. Qualquer falha devolve [] e o pipeline segue com a busca normal."""
    try:
        nomes = inedito(fonte())[: limite * 2]
    except Exception as erro:
        print(f"assunto quente indisponível ({str(erro)[:120]})")
        return []
    dados = []
    for nome in nomes:
        try:
            d = github_dados.buscar(nome)
        except Exception:
            continue
        # repositório só em chinês/japonês/coreano não serve pro público brasileiro (README ilegível pra ele)
        if d.estrelas >= minimo_estrelas and not re.search(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]", d.descricao):
            dados.append(d)
        if len(dados) == limite:
            break
    return dados


def pauta_pixel2(buscas: list[str], palavra_chave: str, dias_novidade: int = 120, llm=None,
                 minimo_estrelas: int = 300, repo: str | None = None) -> dict | None:
    """Notícia de ferramenta: um repositório novo e inédito, roteiro escrito pelo LLM a partir do README.

    Devolve None se não achar candidato ou o LLM não passar na validação; quem chama cai no formato
    antigo, para o cron nunca ficar sem post.
    """
    desde = (date.today() - timedelta(days=dias_novidade)).isoformat()
    icones = {p.stem for p in (montagem.MODELOS / "assets" / "icons").glob("*.svg")}
    if repo:  # repositório pedido de propósito: vale mesmo que já tenha virado post
        escolhidos = [github_dados.buscar(repo)]
    else:
        # o que está bombando hoje vem primeiro (é o que estoura); depois a busca por tema de sempre
        candidatos = _candidatos(buscas, minimo_estrelas=minimo_estrelas, criado_apos=desde) or _candidatos(buscas)
        escolhidos = quentes_ineditos(limite=3) + selecao.escolher_repos(candidatos, quantidade=5)
    for dados in escolhidos:
        try:
            readme = roteirista.buscar_readme(dados.repo)
            if len(readme) < 400:
                continue
            kwargs = {"llm": llm} if llm else {}
            return roteirista.gerar_pauta(dados, readme, palavra_chave, icones, **kwargs)
        except Exception as erro:  # LLM fora, README estranho: tenta o próximo candidato
            print(f"roteiro de {dados.repo} falhou ({str(erro)[:200]}); tentando o próximo")
    return None


def pauta_lista(buscas: list[str], palavra_chave: str, dias_novidade: int = 120, llm=None, minimo_estrelas: int = 200) -> dict | None:
    """Lista de 5 repositórios inéditos com README de verdade. None se não houver 5 ou se o LLM não passar na validação."""
    desde = (date.today() - timedelta(days=dias_novidade)).isoformat()
    icones = {p.stem for p in (montagem.MODELOS / "assets" / "icons").glob("*.svg")}
    candidatos = _candidatos(buscas, minimo_estrelas=minimo_estrelas, criado_apos=desde) or _candidatos(buscas)
    readmes, escolhidos = {}, []
    quentes = quentes_ineditos(limite=2)  # até 2 dos 4-5 itens da lista são assunto do dia
    ja = {d.repo for d in quentes}
    for dados in quentes + [d for d in selecao.escolher_repos(candidatos, quantidade=12) if d.repo not in ja]:
        try:
            readme = roteirista.buscar_readme(dados.repo)
        except Exception:
            continue
        if len(readme) < 400:
            continue
        readmes[dados.repo] = readme
        escolhidos.append(dados)
        if len(escolhidos) == lista.QUANTIDADE:
            break
    if len(escolhidos) < 3:
        return None
    try:
        kwargs = {"llm": llm} if llm else {}
        return lista.gerar_pauta(escolhidos, readmes, palavra_chave, icones, **kwargs)
    except Exception as erro:
        print(f"lista falhou ({str(erro)[:200]})")
        return None


VENDAS = RAIZ / "pautas" / "vendas"


def pauta_de_venda(pasta: Path = VENDAS, hoje: date | None = None) -> dict | None:
    """Vídeo de venda do dia: os roteiros em `pautas/vendas/` giram, um por dia, sem repetir dois dias seguidos."""
    roteiros = sorted(pasta.glob("*.json")) if pasta.exists() else []
    if not roteiros:
        return None
    escolhido = roteiros[(hoje or date.today()).toordinal() % len(roteiros)]
    return json.loads(escolhido.read_text(encoding="utf-8"))


def executar(buscas: list[str], quantidade: int, titulo: str | None, palavra_chave: str,
             estilo: str | None = None, formato: str | None = None, repo: str | None = None) -> dict:
    if formato == "venda":
        venda = pauta_de_venda()
        if venda:
            return venda
        print("sem roteiro de venda; seguindo com notícia de ferramenta")
        formato = "pixel2"
    if formato == "lista":
        nova = pauta_lista(buscas, palavra_chave)
        if nova:
            return nova
        print("lista não saiu; caindo no pixel2")
        formato = "pixel2"
    if formato == "pixel2":
        foco = None if repo else ler_foco()
        nova = (pauta_pixel2(foco["buscas"], palavra_chave, minimo_estrelas=foco.get("minimo_estrelas", 200)) if foco else None) \
            or pauta_pixel2(buscas, palavra_chave, repo=repo)
        if nova:
            if foco:
                gastar_foco()
            return nova
        print("pixel2 não saiu; caindo no formato antigo")
        formato = None
    candidatos = _candidatos(buscas)

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
    parser.add_argument("--palavra-chave", default=None, help="padrão: LINK no pixel2, GITHUB nos outros")
    parser.add_argument("--titulo", default=None)
    parser.add_argument("--estilo", choices=selecao.ESTILOS, default=None, help="só vale pro formato 'curto'; padrão: alterna sozinho")
    parser.add_argument("--formato", choices=selecao.FORMATOS + ("pixel2", "venda", "lista"), default=None, help="padrão: alterna sozinho (2 'curto' pra 1 'aprofundado')")
    parser.add_argument("--repo", default=None, help="força o repositório (dono/nome) no formato pixel2")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    load_dotenv(RAIZ / ".env")

    if args.buscas is not None:
        buscas = args.buscas
    elif args.sem_tendencias:
        buscas = selecao.BUSCAS_PADRAO
    else:
        buscas = buscas_do_dia(selecao.BUSCAS_PADRAO)

    palavra = args.palavra_chave or ("LINK" if args.formato == "pixel2" else "GITHUB")
    nova_pauta = executar(buscas, args.quantidade, args.titulo, palavra, args.estilo, args.formato, args.repo)
    print(f"gancho: {nova_pauta['capa'].get('linha1', nova_pauta['titulo'])} {nova_pauta['capa'].get('linha2', '')}")
    args.saida.write_text(json.dumps(nova_pauta, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.formato != "venda":  # vídeo de venda não gasta repositório nem o foco de tema
        registrar([item["repo"] for item in nova_pauta["itens"]])
    print(f"pauta escrita em {args.saida}")
    for item in nova_pauta["itens"]:
        print(f"  - {item['repo']}")


if __name__ == "__main__":
    main()
