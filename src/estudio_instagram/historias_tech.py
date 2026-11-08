"""Uma história real da tecnologia por dia (Davi, 08/11: "o que você achar melhor pra ganhar seguidor").

Nos números de 06 a 08/11, histórias reais de tecnologia seguraram 14 a 20 s de quem assistiu (o dobro dos vídeos
de ferramenta); o foguete que explodiu por um bug teve o maior tempo assistido da conta. Aqui a máquina pega o próximo
caso bem documentado da lista, lê o artigo da Wikipédia (inglês, mais completo) e escreve o roteiro SÓ com o que está
lá; o previsor critica e o roteirista reescreve abaixo de 7,5. O roteiro vai pra pautas/historias/ com "produzir",
e a produtora anima na rodada seguinte, como as outras histórias.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from . import series

# Casos famosos e bem documentados, sem morte nem tragédia. (slug, artigo da Wikipédia em inglês)
TEMAS = [
    ("knight-capital-45-minutos", "Knight Capital Group"),
    ("mars-climate-orbiter", "Mars Climate Orbiter"),
    ("wannacry-dominio-de-10-dolares", "WannaCry ransomware attack"),
    ("left-pad-11-linhas", "npm left-pad incident"),
    ("pentium-errou-a-conta", "Pentium FDIV bug"),
    ("facebook-sumiu-da-internet", "2021 Facebook outage"),
    ("crowdstrike-tela-azul-do-mundo", "2024 CrowdStrike-related IT outages"),
    ("verme-de-morris", "Morris worm"),
    ("virus-iloveyou", "ILOVEYOU"),
    ("bug-do-milenio", "Year 2000 problem"),
    ("heartbleed", "Heartbleed"),
]
ESTILOS = ["hand-drawn-cartoon", "cartoon-3d-short", "scifi-toon", "midcentury-toon", "cel-anime-80s", "engraving"]
INTERVALO = timedelta(hours=20)  # no máximo uma por dia


def fatos(titulo: str, abrir=urllib.request.urlopen) -> str:
    url = ("https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&redirects=1&format=json&titles="
           + urllib.parse.quote(titulo))
    pedido = urllib.request.Request(url, headers={"User-Agent": "estudio-automatico/1.0 (ursulino.ia)"})
    with abrir(pedido, timeout=30) as resposta:
        paginas = json.load(resposta)["query"]["pages"]
    texto = next(iter(paginas.values())).get("extract", "")
    texto = re.split(r"\n== (See also|References|External links|Notes) ==", texto)[0]
    return texto[:9000]


def proximo_tema(estado: dict) -> tuple[str, str] | None:
    return next(((s, t) for s, t in TEMAS if f"tech:{s}" not in estado), None)


def precisa(estado: dict, agora: datetime | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    feitas = [datetime.fromisoformat(v["quando"]) for k, v in estado.items() if k.startswith("tech:")]
    return not feitas or agora - max(feitas) >= INTERVALO


def escrever(slug: str, titulo: str, n: int, llm=None, ler=fatos) -> dict:
    from . import segredos
    from .llm import gerar_json
    gerar = llm or gerar_json
    base = ler(titulo)
    if len(base) < 1500:  # artigo vazio ou curto demais: sem fato, sem roteiro (nunca inventar)
        raise ValueError(f"artigo da Wikipédia curto demais ({len(base)} caracteres)")
    pedido = {"FATOS": base}
    r = gerar(segredos.texto("historia_tech"), json.dumps(pedido, ensure_ascii=False))
    for _ in range(2):
        try:
            texto = (f"TEXTO NA TELA: {r['texto_tela']}\nABERTURA: {r['ganchos'][0]}\nCORPO: {' '.join(r['corpo'])}\n"
                     f"FECHAMENTO: {r['cta']}")
            nota = gerar(segredos.texto("viral_nota"), texto)
        except Exception as erro:
            print(f"previsor da história falhou ({erro}); sigo com o roteiro")
            break
        print(f"história {slug}: nota {nota.get('nota')} ({nota.get('problema')})", flush=True)
        if float(nota.get("nota") or 0) >= 7.5:
            break
        pedido.update({"critica_do_editor": nota.get("problema"),
                       "roteiro_rejeitado": {k: r.get(k) for k in ("texto_tela", "ganchos", "corpo", "cta")}})
        r = gerar(segredos.texto("historia_tech"), json.dumps(pedido, ensure_ascii=False))
    return {"slug": slug, "serie": slug, "episodio": 1, "opcoes": None, "produzir": True,
            "estilo": ESTILOS[n % len(ESTILOS)], "fonte": f"https://en.wikipedia.org/wiki/{titulo.replace(' ', '_')}",
            "direcao": "HISTÓRIA REAL DA TECNOLOGIA. " + r.get("direcao", ""),
            "roteiro": {"texto_tela": r["texto_tela"], "ganchos": r["ganchos"][:1], "corpo": r["corpo"], "cta": r["cta"],
                        "legenda": r["legenda"], "palavra": ""}}


def gerar_se_preciso(agora: datetime | None = None):
    """Escreve a história do dia se faz 20 h ou mais da última. Devolve o caminho do roteiro ou None."""
    estado = series._ler(series.ESTADO)
    if not precisa(estado, agora):
        return None
    tema = proximo_tema(estado)
    if not tema:
        return None
    slug, titulo = tema
    n = sum(1 for k in estado if k.startswith("tech:"))
    try:
        h = escrever(slug, titulo, n)
    except Exception as erro:
        print(f"não consegui escrever a história {slug} ({erro})")
        return None
    destino = series.HISTORIAS / f"{slug}.json"
    destino.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
    series.registrar(f"tech:{slug}", destino.stem)
    return destino
