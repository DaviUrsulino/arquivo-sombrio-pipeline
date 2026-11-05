"""Assunto do momento: o que o Brasil está buscando e lendo AGORA, para virar animação rápida.

Por que existe (Davi, 2026-11-04): o perfil perdeu as ondas do dia ("uma galera fez animação sobre..."). Quem posta
a animação do assunto quente nas primeiras horas pega o alcance; um dia depois ninguém liga mais. Quando o assunto
não tem nada a ver com IA, o vídeo vira venda: a animação é a prova ("esse vídeo eu fiz com IA, quer fazer
igual?").

Fontes grátis, sem login (o X/Twitter não tem acesso grátis e o Apify está sem crédito):
- Google Trends diário do Brasil (RSS): o termo, o volume de busca e as manchetes que explicam o pico;
- Google Notícias, principais do Brasil (RSS);
- Google Notícias por busca, para os assuntos que o Davi marcou como onda longa (VIGIAR, ex.: GTA 6).
Um LLM escolhe o assunto que rende animação para o público do perfil e os FATOS são só as manchetes, com a fonte.

Política fica de fora por padrão (POLITICA=False): o Instagram não recomenda conteúdo político para quem não segue a
conta (configuração padrão desde 2024), e o alcance de não seguidores é exatamente o que o perfil precisa. Além
disso, animação automática sobre político real tem risco de difamação sem revisão humana.
"""

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

from .llm import gerar_json
from . import segredos

RAIZ = Path(__file__).resolve().parents[2]
USADOS = RAIZ / "pautas" / "em_alta_usados.json"
UA = {"User-Agent": "Mozilla/5.0 (estudio-automatico @ursulino.ia)"}
HT = "{https://trends.google.com/trending/rss}"
TRENDS = "https://trends.google.com/trending/rss?geo=BR"
NOTICIAS = "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"
BUSCA = "https://news.google.com/rss/search?q={q}+when:2d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
VIGIAR = ["GTA 6"]  # ondas longas que sempre rendem notícia nova
POLITICA = False
TERMOS_POLITICOS = re.compile(r"\b(bolsonaro|lula|trump|stf|senad\w*|deputad\w*|ministr\w*|president\w*|governo|"
                              r"elei\w*|partido|pec|congresso|câmara|planalto|vereador\w*|prefeit\w*|governador\w*|"
                              r"\bPL\b|\bPT\b|moraes|haddad|tarcísio|eduardo|flávio|michelle)\b", re.I)

ESCOLHA = segredos.texto("em_alta_escolha")  # texto no repositório privado (ver segredos.py)


def _get(url: str, abrir=urllib.request.urlopen) -> str:
    with abrir(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def ler_trends(xml: str) -> list[dict]:
    itens = []
    for item in ElementTree.fromstring(xml).iter("item"):
        trafego = re.sub(r"\D", "", item.findtext(f"{HT}approx_traffic") or "") or "0"
        manchetes = [f"{n.findtext(f'{HT}news_item_title')} ({n.findtext(f'{HT}news_item_source')})"
                     for n in item.iter(f"{HT}news_item")]
        itens.append({"termo": item.findtext("title"), "buscas": int(trafego), "manchetes": manchetes, "fonte": "Google Trends"})
    return itens


def ler_noticias(xml: str, fonte: str, termo: str | None = None) -> list[dict]:
    itens = []
    for item in ElementTree.fromstring(xml).iter("item"):
        titulo = item.findtext("title") or ""
        quando = item.findtext("pubDate")
        itens.append({"termo": termo or titulo, "buscas": 0, "manchetes": [titulo], "fonte": fonte,
                      "quando": parsedate_to_datetime(quando).isoformat() if quando else None})
    return itens


def coletar(abrir=urllib.request.urlopen) -> list[dict]:
    """Junta as fontes; se uma cair, as outras seguem."""
    candidatos = []
    try:
        candidatos += sorted(ler_trends(_get(TRENDS, abrir)), key=lambda i: -i["buscas"])[:20]
    except Exception as erro:
        print(f"Google Trends indisponível: {erro}")
    try:
        candidatos += ler_noticias(_get(NOTICIAS, abrir), "Google Notícias")[:15]
    except Exception as erro:
        print(f"Google Notícias indisponível: {erro}")
    for termo in VIGIAR:
        try:
            noticias = ler_noticias(_get(BUSCA.format(q=urllib.parse.quote_plus(termo)), abrir), "Google Notícias", termo)
            if noticias:
                candidatos.append({"termo": termo, "buscas": 0, "fonte": "Google Notícias",
                                   "manchetes": [m for n in noticias[:6] for m in n["manchetes"]]})
        except Exception as erro:
            print(f"busca '{termo}' indisponível: {erro}")
    return candidatos


def eh_politica(c: dict) -> bool:
    return bool(TERMOS_POLITICOS.search(" ".join([c["termo"], *c["manchetes"]])))


def _usados() -> list[str]:
    return json.loads(USADOS.read_text(encoding="utf-8")) if USADOS.exists() else []


def escolher(candidatos: list[dict], llm=gerar_json, usados: list[str] | None = None) -> dict | None:
    """Devolve {"tema", "angulo", "fatos", "chave"} ou None quando nada do momento rende vídeo."""
    usados = [u.lower() for u in (usados if usados is not None else _usados())]
    validos = [c for c in candidatos if c["manchetes"] and c["termo"].lower() not in usados
               and (POLITICA or not eh_politica(c))]
    if not validos:
        return None
    lista = "\n".join(f"[{k}] {c['termo']} ({c['buscas']}+ buscas)\n" + "\n".join(f"   - {m}" for m in c["manchetes"][:4])
                      for k, c in enumerate(validos))
    regra = "" if POLITICA else "NUNCA escolha política (políticos, governo, eleição, partido)."
    r = llm(ESCOLHA.replace("__POLITICA__", regra), lista)
    try:
        c = validos[int(r.get("id"))]
    except (TypeError, ValueError, IndexError):
        return None
    if float(r.get("nota") or 0) < 8:
        return None
    fatos = (f"ASSUNTO DO MOMENTO no Brasil: {c['termo']} ({c['fonte']}"
             + (f", mais de {c['buscas']} buscas hoje" if c["buscas"] else "") + ").\nManchetes de hoje:\n"
             + "\n".join(f"- {m}" for m in c["manchetes"][:6]))
    return {"tema": r.get("tema") or c["termo"], "angulo": r.get("angulo") or "", "fatos": fatos, "chave": c["termo"]}


def registrar(chave: str):
    usados = _usados()
    USADOS.write_text(json.dumps([*usados, chave][-200:], ensure_ascii=False, indent=1), encoding="utf-8")


def do_momento() -> dict | None:
    return escolher(coletar())


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    print(json.dumps(do_momento(), ensure_ascii=False, indent=1), datetime.now().isoformat(timespec="minutes"))
