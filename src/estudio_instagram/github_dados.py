"""Dados reais dos repositórios da pauta (RN-1: todo número do post vem de uma fonte)."""

import json
import os
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


def baixar_cartao(repo: str, destino: Path, abrir=urllib.request.urlopen) -> Path:
    """Baixa o cartão de prévia do repositório (a imagem que o GitHub mostra ao compartilhar o link)."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with abrir(urllib.request.Request(CARTAO.format(repo=repo), headers={"User-Agent": "estudio-automatico"}), timeout=30) as resposta:
        destino.write_bytes(resposta.read())
    return destino
