"""Escolhe o assunto sozinho: busca repositórios candidatos, descarta o que já virou post, monta a pauta.

Sem LLM — a narração é montada por modelo de frase (template), e cada número vem de um
marcador `{estrelas:dono/repo}` que `pauta.preencher` troca pelo valor real na hora de gerar
o vídeo (RN-1: todo número do post vem de uma fonte coletada).

Dois estilos de gancho, escolhidos medindo engajamento real nos concorrentes (2026-10-14,
Apify): "lista" é o formato campeão no nicho BR (65 mil comentários num post só). "fofoca"
copia a técnica de gancho do @claudedrop ("algo aconteceu e quase ninguém percebeu") — menos
usada aqui, serve pra variar o texto sem repetir a mesma abertura toda vez. Os dois usam a
mesma estrutura de cenas (um card por repositório) e o mesmo visual: só o gancho e a chamada
mudam.
"""

from .github_dados import DadosRepo
from .historico import inedito

BUSCAS_PADRAO = ["claude code skill", "claude-code agent"]
CORES = ["laranja", "azul", "roxo", "verde", "amarelo"]
ICONE_ITEM = "github"
ESTILOS = ("lista", "fofoca")


def _nome_exibicao(repo: str) -> str:
    return repo.split("/", 1)[1]


def _promessa(repo: DadosRepo) -> str:
    descricao = repo.descricao.strip().rstrip(".")
    return descricao[:70] + ("…" if len(descricao) > 70 else "") if descricao else "Mais uma ferramenta grátis pro seu Claude Code."


def _gancho_lista(n: int) -> dict:
    return {
        "narracao": f"{n} repositórios grátis que você precisa conhecer pro Claude Code. "
                    f"Juntos, eles têm {{total_estrelas}} estrelas.",
        "elementos": [
            {"tipo": "cabecalho", "texto": "você precisa conhecer...", "ancora": "repositórios"},
            {"tipo": "numero", "texto": str(n), "ancora": str(n), "y": 640},
            {"tipo": "texto", "texto": "repositórios grátis", "ancora": "grátis", "y": 960, "grande": True},
            {"tipo": "etiqueta", "texto": "★ {total_estrelas} estrelas", "ancora": "estrelas", "y": 1180, "cor": "amarelo"},
        ],
        "capa": {"linha1": "VOCÊ PRECISA", "linha2": "CONHECER ISSO", "subtitulo": f"{n} repositórios grátis pro Claude Code"},
    }


def _gancho_fofoca(n: int) -> dict:
    return {
        "narracao": f"Isso aqui quase ninguém usa no Claude Code, e devia. São {n} repositórios "
                    f"grátis que somam {{total_estrelas}} estrelas, e ninguém te contou.",
        "elementos": [
            {"tipo": "cabecalho", "texto": "quase ninguém sabe disso", "ancora": "ninguém"},
            {"tipo": "numero", "texto": str(n), "ancora": str(n), "y": 640},
            {"tipo": "texto", "texto": "repositórios grátis", "ancora": "repositórios", "y": 960, "grande": True},
            {"tipo": "etiqueta", "texto": "★ {total_estrelas} estrelas", "ancora": "estrelas", "y": 1180, "cor": "amarelo"},
        ],
        "capa": {"linha1": "QUASE NINGUÉM", "linha2": "SABE DISSO", "subtitulo": f"{n} repositórios grátis que ninguém te contou"},
    }


_GANCHOS = {"lista": _gancho_lista, "fofoca": _gancho_fofoca}


def montar_pauta(repos: list[DadosRepo], titulo: str, palavra_chave: str = "GITHUB",
                  voz: dict | None = None, estilo: str = "lista") -> dict:
    """Monta a pauta completa (capa, itens, chamada, cenas) a partir de repositórios reais.

    `estilo`: "lista" (padrão, o campeão de engajamento no nicho) ou "fofoca" (gancho de
    novidade, pra variar o texto de vez em quando sem perder qualidade — ver docstring do
    módulo).
    """
    if not 3 <= len(repos) <= 5:
        raise ValueError(f"escolha de 3 a 5 repositórios, recebeu {len(repos)}")
    if estilo not in _GANCHOS:
        raise ValueError(f"estilo {estilo!r} desconhecido — use um de {ESTILOS}")
    voz = voz or {"id": "iP95p4xoKVk53GoZ742B", "modelo": "eleven_multilingual_v2"}
    n = len(repos)
    gancho = _GANCHOS[estilo](n)

    itens = [{
        "repo": r.repo, "nome": _nome_exibicao(r.repo), "cor": CORES[i % len(CORES)],
        "promessa": _promessa(r), "texto": f"com {{estrelas:{r.repo}}} estrelas no GitHub",
    } for i, r in enumerate(repos)]

    ordinais = ["primeiro", "segundo", "terceiro", "quarto", "quinto"]
    cenas = [{"id": "gancho", "cor": "laranja", "narracao": gancho["narracao"], "elementos": gancho["elementos"]}]
    for i, item in enumerate(itens):
        ordinal = ordinais[i]
        nome_palavra = item["nome"]
        cenas.append({
            "id": f"r{i + 1}", "cor": item["cor"],
            "narracao": f"O {ordinal} é o {nome_palavra}. {item['promessa']}",
            "elementos": [
                {"tipo": "cabecalho", "texto": f"#{i + 1}", "ancora": ordinal},
                {"tipo": "cartao", "numero": item["nome"], "texto": item["texto"], "icone": ICONE_ITEM,
                 "repo": item["repo"], "ancora": nome_palavra, "y": 600, "cor": item["cor"]},
            ],
        })
    cenas.append({
        "id": "cta", "cor": "laranja",
        "narracao": f"Quer o link de todos? Comenta {palavra_chave} aqui embaixo, que eu te mando no direct.",
        "elementos": [
            {"tipo": "icone", "icone": "message-circle", "ancora": "Quer", "y": 520, "tamanho": 240, "cor": "azul"},
            {"tipo": "texto", "texto": f"quer os {n} links?", "ancora": "link", "y": 820, "grande": True},
            {"tipo": "destaque", "texto": f"comenta {palavra_chave}", "ancora": "Comenta", "y": 1040, "cor": "amarelo"},
        ],
    })

    return {
        "titulo": titulo, "palavra_chave": palavra_chave, "perfil": "@robo.estagiario", "voz": voz,
        "capa": {**gancho["capa"], "selo": "★ {total_estrelas} estrelas"},
        "chamada": {"pergunta": f"quer os {n} links?", "promessa": "que eu te mando no direct",
                    "rodape": "e segue pra mais ferramenta grátis de IA"},
        "itens": itens, "cenas": cenas,
    }


def escolher_estilo(indice: int) -> str:
    """Alterna os estilos de forma determinística (ex.: `indice` = nº de pautas já geradas),
    pra variar o gancho sem depender de aleatoriedade (mais fácil de testar e repetir)."""
    return ESTILOS[indice % len(ESTILOS)]


def escolher_repos(candidatos: list[DadosRepo], quantidade: int = 5, arquivo_historico=None) -> list[DadosRepo]:
    """Filtra o que já virou post e devolve os `quantidade` com mais estrelas, nunca repetindo."""
    nomes_ineditos = set(inedito([r.repo for r in candidatos], *([arquivo_historico] if arquivo_historico else [])))
    restantes = sorted((r for r in candidatos if r.repo in nomes_ineditos), key=lambda r: r.estrelas, reverse=True)
    return restantes[:quantidade]
