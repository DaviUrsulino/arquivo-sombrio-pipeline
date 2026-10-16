"""Dados reais dos repositórios da pauta (RN-1: todo número do post vem de uma fonte)."""

import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

API = "https://api.github.com/repos/{repo}"
CARTAO = "https://opengraph.githubassets.com/1/{repo}"


@dataclass(frozen=True)
class DadosRepo:
    repo: str
    estrelas: int
    licenca: str
    descricao: str
    url: str


def _cabecalhos() -> dict:
    cabecalhos = {"Accept": "application/vnd.github+json", "User-Agent": "estudio-automatico"}
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        cabecalhos["Authorization"] = f"Bearer {token}"
    return cabecalhos


def buscar(repo: str, abrir=urllib.request.urlopen) -> DadosRepo:
    with abrir(urllib.request.Request(API.format(repo=repo), headers=_cabecalhos()), timeout=30) as resposta:
        d = json.load(resposta)
    licenca = (d.get("license") or {}).get("spdx_id") or "sem licença"
    if licenca == "NOASSERTION":
        licenca = "licença própria"
    return DadosRepo(d["full_name"], d["stargazers_count"], licenca, d.get("description") or "", d["html_url"])


def buscar_candidatos(consulta: str, minimo_estrelas: int = 50, limite: int = 15, abrir=urllib.request.urlopen) -> list[DadosRepo]:
    """Repositórios que combinam com a busca, ordenados por estrela (mais relevante primeiro)."""
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
        "q": f"{consulta} stars:>={minimo_estrelas} license:mit,apache-2.0,bsd-3-clause",
        "sort": "stars", "order": "desc", "per_page": limite,
    })
    with abrir(urllib.request.Request(url, headers=_cabecalhos()), timeout=30) as resposta:
        itens = json.load(resposta)["items"]
    return [DadosRepo(i["full_name"], i["stargazers_count"], (i.get("license") or {}).get("spdx_id", "licença própria"),
                       i.get("description") or "", i["html_url"]) for i in itens]


def baixar_cartao(repo: str, destino: Path, abrir=urllib.request.urlopen, tentativas: int = 4, dormir=time.sleep) -> Path:
    """Baixa o cartão de prévia do repositório (a imagem que o GitHub mostra ao compartilhar o link).

    O gerador de imagem do GitHub (opengraph.githubassets.com) tem limite de requisição por
    IP sem chave — passa de 2 ou 3 por segundo e devolve 429. Tenta de novo com espera
    crescente em vez de falhar a execução inteira por um cartão só.
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    pedido = urllib.request.Request(CARTAO.format(repo=repo), headers={"User-Agent": "estudio-automatico"})
    for tentativa in range(tentativas):
        try:
            with abrir(pedido, timeout=30) as resposta:
                destino.write_bytes(resposta.read())
            return destino
        except urllib.error.HTTPError as erro:
            if erro.code != 429 or tentativa == tentativas - 1:
                raise
            dormir(2 ** tentativa)
