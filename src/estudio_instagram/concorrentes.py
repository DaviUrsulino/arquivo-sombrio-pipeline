"""Caça pauta: varre os posts públicos dos concorrentes (Apify) e devolve o que mais engaja.

RF-01/RF-02 de docs/estudio-instagram.md. Só lê dado público, com limite de itens (LGPD).
"""

import json
import urllib.request
from dataclasses import dataclass

ATOR_PERFIS = "apify~instagram-scraper"


@dataclass(frozen=True)
class PostConcorrente:
    perfil: str
    tipo: str
    url: str
    comentarios: int
    curtidas: int
    legenda: str


def _pedir(token: str, entrada: dict, abrir=urllib.request.urlopen) -> list[dict]:
    pedido = urllib.request.Request(
        f"https://api.apify.com/v2/acts/{ATOR_PERFIS}/run-sync-get-dataset-items?timeout=280",
        data=json.dumps(entrada).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "estudio-automatico/1.0"},
    )
    with abrir(pedido, timeout=300) as resposta:
        return json.load(resposta)


def coletar(token: str, perfis: list[str], limite_por_perfil: int = 25, abrir=urllib.request.urlopen) -> list[PostConcorrente]:
    """Puxa os últimos posts dos perfis e devolve ordenado por comentários (maior primeiro)."""
    entrada = {
        "directUrls": [f"https://www.instagram.com/{p}/" for p in perfis],
        "resultsType": "posts", "resultsLimit": limite_por_perfil, "addParentData": False,
    }
    posts = [
        PostConcorrente(i.get("ownerUsername", "?"), i.get("type", "?"), i["url"],
                         i.get("commentsCount") or 0, i.get("likesCount") or 0, (i.get("caption") or "").strip())
        for i in _pedir(token, entrada, abrir) if i.get("url")
    ]
    return sorted(posts, key=lambda p: p.comentarios, reverse=True)


PALAVRAS_CHAVE_TEMA = {
    # "clonar app pago" / "acabou pro X": tema dos vídeos de 170-450 mil views do gab.gouvea e do brunoptrevisan.
    "alternativa": ["clonar", "clone", "acabou pro", "alternativa", "de graça", "gratuito", "pago"],
    "repositorio": ["repositório", "repositórios", "github", "repo", "biblioteca", "open source"],
    "skill": ["skill", "skills", "plugin", "plugins"],
    "site": ["site", "landing page", "construir site", "app"],
    "video": ["motion", "vídeo", "edição", "reels", "hyperframes"],
    "limite": ["limite", "token", "racionado", "economizar"],
}


def classificar_tema(legenda: str) -> str | None:
    """Identifica qual tema de PALAVRAS_CHAVE_TEMA a legenda cobre, se algum."""
    texto = legenda.lower()
    for tema, palavras in PALAVRAS_CHAVE_TEMA.items():
        if any(p in texto for p in palavras):
            return tema
    return None


# Cada tema vira uma busca diferente no GitHub — é a ponte entre "o que tá bombando
# no Instagram hoje" e "quais repositórios buscar", sem precisar de LLM.
BUSCA_GITHUB_POR_TEMA = {
    "alternativa": ["open source alternative", "self-hosted alternative ai"],
    "repositorio": ["claude code skill", "claude-code agent"],
    "skill": ["claude code skill", "claude code plugin"],
    "site": ["claude code website builder", "ai website generator open source"],
    "video": ["claude code motion graphics", "ai video automation open source"],
    "limite": ["claude code token usage", "llm proxy rate limit"],
}


def temas_em_alta(posts: list[PostConcorrente], minimo: int = 2) -> list[str]:
    """Soma o engajamento por tema e devolve do mais quente pro mais frio.

    `minimo`: um tema só conta se tiver pelo menos esse número de posts classificados —
    um post isolado com muito comentário não deve virar tendência sozinho.
    """
    comentarios_por_tema: dict[str, int] = {}
    contagem_por_tema: dict[str, int] = {}
    for post in posts:
        tema = classificar_tema(post.legenda)
        if tema is None:
            continue
        comentarios_por_tema[tema] = comentarios_por_tema.get(tema, 0) + post.comentarios
        contagem_por_tema[tema] = contagem_por_tema.get(tema, 0) + 1
    quentes = [t for t, n in contagem_por_tema.items() if n >= minimo]
    return sorted(quentes, key=lambda t: comentarios_por_tema[t], reverse=True)


def buscas_do_dia(posts: list[PostConcorrente], buscas_padrao: list[str], quantidade_temas: int = 2) -> list[str]:
    """Monta a lista de busca do dia: os temas mais quentes primeiro, `buscas_padrao` no
    final como rede de segurança (garante candidato mesmo se nada bateu com os temas)."""
    buscas = []
    for tema in temas_em_alta(posts)[:quantidade_temas]:
        buscas += BUSCA_GITHUB_POR_TEMA.get(tema, [])
    for busca in buscas_padrao:
        if busca not in buscas:
            buscas.append(busca)
    return buscas
