"""Assunto quente do dia: repositórios de IA que estão bombando AGORA, de fontes grátis (sem Apify).

O que estoura no nicho é "saiu ontem e todo mundo tá falando". Junta três termômetros públicos:
- GitHub Trending (diário): estrelas ganhas hoje;
- Hacker News (primeira página das últimas 48 h): links pro GitHub, com os pontos;
- busca oficial do GitHub: repositórios de IA criados nos últimos 7 dias, pelos que mais ganharam estrela.
(Reddit ficou de fora: bloqueia acesso automatizado.)
Cada fonte vira uma nota normalizada (0 a 1); repositório citado em mais de uma fonte soma. Só entra o que tem
cara de IA (palavras-chave na descrição/título). Lido uma vez por dia (cache em pautas/quentes_do_dia.json);
se uma fonte cair, as outras seguem; se todas caírem, devolve lista vazia e o pipeline usa a busca normal.
"""

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CACHE = RAIZ / "pautas" / "quentes_do_dia.json"
UA = {"User-Agent": "estudio-automatico (perfil @ursulino.ia)"}
IA = re.compile(r"\b(ai|llms?|gpt|claude|agents?|agentic|mcp|openai|gemini|anthropic|diffusion|copilot|rag|ollama|"
                r"whisper|tts|chatbot|skills?|text-to-\w+|codex|cursor|deepseek|qwen|mistral|transformers?)\b", re.I)
REPO_URL = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
IGNORAR_DONOS = {"features", "orgs", "topics", "sponsors", "marketplace", "settings", "apps", "collections"}


def _get(url: str, abrir=urllib.request.urlopen) -> str:
    with abrir(urllib.request.Request(url, headers=UA), timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def _repo(dono: str, nome: str) -> str | None:
    nome = re.sub(r"(\.git|[).,#?].*)$", "", nome)
    if dono.lower() in IGNORAR_DONOS or not nome:
        return None
    return f"{dono}/{nome}"


def github_trending(html: str) -> dict[str, tuple[float, str]]:
    """{repo: (estrelas hoje, descrição)} a partir do HTML de github.com/trending."""
    saida = {}
    for bloco in html.split('<article class="Box-row')[1:]:
        m = re.search(r'<h2[^>]*>\s*<a[^>]*href="/([^/"]+)/([^/"]+)"', bloco)
        if not m:
            continue
        hoje = re.search(r"([\d,]+)\s+stars\s+today", bloco)
        desc = re.search(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', bloco, re.S)
        repo = _repo(m.group(1), m.group(2))
        if repo:
            saida[repo] = (float(hoje.group(1).replace(",", "")) if hoje else 0.0,
                           re.sub(r"<[^>]+>|\s+", " ", desc.group(1)).strip() if desc else "")
    return saida


def hacker_news(dados: dict) -> dict[str, tuple[float, str]]:
    saida = {}
    for h in dados.get("hits", []):
        m = REPO_URL.search(h.get("url") or "")
        repo = m and _repo(*m.groups())
        if repo:
            pts, tit = saida.get(repo, (0, ""))
            saida[repo] = (pts + (h.get("points") or 0), tit or h.get("title") or "")
    return saida


def novos_do_github(itens: list[dict]) -> dict[str, tuple[float, str]]:
    """Resposta da busca do GitHub: estrelas totais de repositório recém-criado (todas ganhas na semana)."""
    return {i["full_name"]: (float(i["stargazers_count"]), i.get("description") or "") for i in itens}


def combinar(fontes: list[dict[str, tuple[float, str]]], filtrar_ia: bool = True) -> list[dict]:
    """Nota de cada fonte normalizada pelo maior valor dela; soma entre fontes; ordena da mais quente."""
    nota, texto, citado = {}, {}, {}
    for fonte in fontes:
        topo = max((v for v, _ in fonte.values()), default=0) or 1
        for repo, (valor, desc) in fonte.items():
            nota[repo] = nota.get(repo, 0) + valor / topo
            texto[repo] = f"{texto.get(repo, '')} {desc} {repo.replace('-', ' ').replace('_', ' ')}"
            citado[repo] = citado.get(repo, 0) + 1
    itens = [{"repo": r, "nota": round(n, 3), "fontes": citado[r]} for r, n in nota.items()
             if not filtrar_ia or IA.search(texto[r])]
    return sorted(itens, key=lambda x: (x["nota"], x["fontes"]), reverse=True)


def coletar(abrir=urllib.request.urlopen, agora: float | None = None) -> list[dict]:
    fontes = []
    try:
        fontes.append(github_trending(_get("https://github.com/trending?since=daily", abrir)))
    except Exception as erro:
        print(f"  GitHub Trending fora ({str(erro)[:80]})")
    try:
        desde = int((agora or time.time()) - 48 * 3600)
        fontes.append(hacker_news(json.loads(_get(
            f"https://hn.algolia.com/api/v1/search?tags=story&query=github.com&numericFilters=created_at_i>{desde},points>40&hitsPerPage=100", abrir))))
    except Exception as erro:
        print(f"  Hacker News fora ({str(erro)[:80]})")
    try:
        from datetime import timedelta
        from .github_dados import _cabecalhos
        desde = (date.today() - timedelta(days=7)).isoformat()
        consulta = urllib.parse.quote(f"created:>{desde} stars:>80")  # o filtro de IA vem depois, na descrição
        req = urllib.request.Request(f"https://api.github.com/search/repositories?q={consulta}&sort=stars&order=desc&per_page=30",
                                     headers=_cabecalhos())
        with abrir(req, timeout=25) as r:
            fontes.append(novos_do_github(json.load(r)["items"]))
    except Exception as erro:
        print(f"  busca do GitHub fora ({str(erro)[:80]})")
    print(f"  fontes lidas: {[len(f) for f in fontes]}")
    return combinar(fontes)


def do_dia(hoje: str | None = None, arquivo: Path = CACHE, coletor=coletar) -> list[str]:
    """Repositórios quentes de hoje, do mais quente pro menos (cache diário)."""
    hoje = hoje or date.today().isoformat()
    if arquivo.exists():
        salvo = json.loads(arquivo.read_text(encoding="utf-8"))
        if salvo.get("dia") == hoje:
            return [i["repo"] for i in salvo["itens"]]
    itens = coletor()
    arquivo.write_text(json.dumps({"dia": hoje, "itens": itens[:40]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"assuntos quentes hoje: {[i['repo'] for i in itens[:8]]}")
    return [i["repo"] for i in itens]


if __name__ == "__main__":
    for i in coletar()[:20]:
        print(i)
