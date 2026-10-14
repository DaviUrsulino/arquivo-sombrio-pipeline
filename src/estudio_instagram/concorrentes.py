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
