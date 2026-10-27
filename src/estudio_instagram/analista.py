"""Analisa o desempenho dos Reels da conta e diz o que repetir: horário, tema e retenção.

Lê as métricas de cada Reels pela Graph API (views, alcance, salvos, envios, curtidas, comentários e tempo médio
assistido) e do perfil (alcance e seguidores do dia). Escreve `docs/analise-desempenho.md` (para ler) e
`pautas/desempenho.json` (para o roteirista e a escolha de pauta usarem).

Uso:
    python -m src.estudio_instagram.analista            # consulta a API e grava os dois arquivos
    python -m src.estudio_instagram.analista --commit   # e sobe para o git
"""

import argparse
import json
import os
import statistics
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
RELATORIO = RAIZ / "docs" / "analise-desempenho.md"
DADOS = RAIZ / "pautas" / "desempenho.json"
BRASILIA = timezone(timedelta(hours=-3))
BASE = "https://graph.instagram.com/v22.0"
METRICAS_REELS = ["views", "reach", "saved", "shares", "likes", "comments", "ig_reels_avg_watch_time"]
# Temas por palavra na legenda (sem acento, minúscula). Um Reels pode cair em mais de um tema.
TEMAS = {
    "vídeo com IA": ["vídeo", "video", "renderiza", "animação", "motion", "filme"],
    "assistente (Jarvis)": ["jarvis", "assistente", "voz"],
    "Claude Code": ["claude code", "claude"],
    "agentes e skills": ["agente", "skills", "skill"],
    "segurança e teste": ["segurança", "teste", "seguranca"],
    "venda e kit": ["pack", "kit", "link na bio"],
}
# Experimento "formato curto" (decidido em 2026-10-20): Reels publicados depois desta data usam roteiros de 20-35 s.
# Antes disso os vídeos tinham 45-60 s. O relatório compara os dois grupos.
INICIO_FORMATO_CURTO = datetime(2026, 10, 21, 1, 0, tzinfo=timezone.utc)
MIN_AMOSTRA = 3  # quantos Reels precisa ter num grupo para ele entrar nas recomendações


def _ler(caminho: str, token: str, **consulta) -> dict:
    url = f"{BASE}/{caminho}?{urllib.parse.urlencode({**consulta, 'access_token': token})}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "estudio-automatico/1.0"}), timeout=30) as r:
        return json.load(r)


def coletar(token: str, ig_id: str, quantos: int = 60) -> tuple[list[dict], dict, int | None]:
    """(Reels com métricas, alcance do perfil nos últimos dias, seguidores). Métrica que a API recusa vira ausente."""
    midias = _ler(f"{ig_id}/media", token, fields="id,timestamp,media_product_type,caption", limit=quantos)["data"]
    reels = []
    for m in midias:
        if m.get("media_product_type") != "REELS":
            continue
        valores = {}
        for metrica in METRICAS_REELS:
            try:
                dado = _ler(f"{m['id']}/insights", token, metric=metrica)["data"]
                valores[metrica] = dado[0]["values"][0]["value"]
            except (urllib.error.HTTPError, KeyError, IndexError):
                continue
        reels.append({"id": m["id"], "hora": m["timestamp"], "legenda": m.get("caption") or "", **valores})
    seguidores = None
    try:
        seguidores = _ler("me", token, fields="followers_count").get("followers_count")
    except urllib.error.HTTPError:
        pass
    return reels, {}, seguidores


def _parse(hora: str) -> datetime:
    return datetime.strptime(hora, "%Y-%m-%dT%H:%M:%S%z").astimezone(BRASILIA)


def faixa_horaria(hora: str) -> str:
    h = _parse(hora).hour
    for nome, (ini, fim) in {"madrugada (0-6h)": (0, 6), "manhã (6-10h)": (6, 10), "meio-dia (10-14h)": (10, 14),
                             "tarde (14-18h)": (14, 18), "noite (18-22h)": (18, 22)}.items():
        if ini <= h < fim:
            return nome
    return "tarde da noite (22-24h)"


def temas_de(legenda: str) -> list[str]:
    texto = legenda.lower()
    achados = [tema for tema, palavras in TEMAS.items() if any(p in texto for p in palavras)]
    return achados or ["outros"]


def taxa(parte, total) -> float:
    return round(100 * (parte or 0) / total, 2) if total else 0.0


def resumo(reels: list[dict]) -> dict:
    views = [r.get("views", 0) for r in reels]
    return {
        "n": len(reels),
        "views_medianas": int(statistics.median(views)) if views else 0,
        "views_media": int(statistics.mean(views)) if views else 0,
        "salvos_por_100_alcance": taxa(sum(r.get("saved", 0) for r in reels), sum(r.get("reach", 0) for r in reels)),
        "envios_por_100_alcance": taxa(sum(r.get("shares", 0) for r in reels), sum(r.get("reach", 0) for r in reels)),
        "tempo_medio_s": round(statistics.mean([r.get("ig_reels_avg_watch_time", 0) / 1000 for r in reels]), 1) if reels else 0,
    }


def agrupar(reels: list[dict], chave) -> dict[str, dict]:
    grupos = defaultdict(list)
    for r in reels:
        for nome in (chave(r) if isinstance(chave(r), list) else [chave(r)]):
            grupos[nome].append(r)
    return {nome: resumo(itens) for nome, itens in grupos.items()}


def formato_de(hora: str) -> str:
    return "curto (20-35 s)" if datetime.strptime(hora, "%Y-%m-%dT%H:%M:%S%z") >= INICIO_FORMATO_CURTO else "longo (45-60 s)"


ESTILOS = Path(__file__).resolve().parents[2] / "pautas" / "estilo_por_post.json"


def estilo_de(media_id: str, mapa: dict) -> str:
    """Identidade visual do post (gravada pelo pipeline ao publicar); posts de antes de 2026-10-27 são 'pixel antigo'."""
    return mapa.get(media_id, "pixel antigo / manual")


def analisar(reels: list[dict], estilos: dict | None = None) -> dict:
    estilos = estilos if estilos is not None else (json.loads(ESTILOS.read_text(encoding="utf-8")) if ESTILOS.exists() else {})
    por_hora = agrupar(reels, lambda r: faixa_horaria(r["hora"]))
    por_tema = agrupar(reels, lambda r: temas_de(r["legenda"]))
    ordenados = sorted(reels, key=lambda r: r.get("views", 0), reverse=True)
    elegiveis = lambda grupos: {k: v for k, v in grupos.items() if v["n"] >= MIN_AMOSTRA}
    melhor_hora = max(elegiveis(por_hora).items(), key=lambda kv: kv[1]["views_medianas"], default=None)
    melhor_tema = max(elegiveis(por_tema).items(), key=lambda kv: kv[1]["views_medianas"], default=None)
    return {
        "geral": resumo(reels), "por_estilo": agrupar(reels, lambda r: estilo_de(r["id"], estilos)), "por_formato": agrupar(reels, lambda r: formato_de(r["hora"])), "por_faixa_horaria": por_hora, "por_tema": por_tema,
        "melhor_faixa": melhor_hora[0] if melhor_hora else None, "melhor_tema": melhor_tema[0] if melhor_tema else None,
        "top": [{"id": r["id"], "views": r.get("views", 0), "salvos": r.get("saved", 0), "envios": r.get("shares", 0),
                 "tempo_s": round(r.get("ig_reels_avg_watch_time", 0) / 1000, 1), "titulo": r["legenda"].split("\n")[0][:70], "hora": _parse(r["hora"]).strftime("%d/%m %H:%M")} for r in ordenados[:8]],
    }


def _tabela(grupos: dict[str, dict]) -> str:
    linhas = ["| Grupo | Reels | Views (mediana) | Salvos/100 alcance | Envios/100 alcance | Tempo médio (s) |", "|---|---|---|---|---|---|"]
    for nome, g in sorted(grupos.items(), key=lambda kv: -kv[1]["views_medianas"]):
        aviso = "" if g["n"] >= MIN_AMOSTRA else " (amostra pequena)"
        linhas.append(f"| {nome}{aviso} | {g['n']} | {g['views_medianas']} | {g['salvos_por_100_alcance']} | {g['envios_por_100_alcance']} | {g['tempo_medio_s']} |")
    return "\n".join(linhas)


def relatorio(analise: dict, seguidores: int | None, gerado_em: str) -> str:
    g = analise["geral"]
    top = "\n".join(f"{i}. {t['views']} views, {t['salvos']} salvos, {t['envios']} envios, {t['tempo_s']} s assistidos em média ({t['hora']}): {t['titulo']}" for i, t in enumerate(analise["top"], 1))
    return f"""# Análise de desempenho dos Reels

Gerado em {gerado_em} (horário de Brasília). Seguidores agora: {seguidores}. Reels analisados: {g['n']}.
Mediana de views: {g['views_medianas']} · média: {g['views_media']} (a média é puxada para cima por poucos vídeos que estouram).

## Melhores posts
{top}

## Por estilo visual (as 8 identidades)
{_tabela(analise['por_estilo'])}
Depois de uns 4 Reels por estilo, os que ficarem na lanterna saem do rodízio (MOLDES_ESTUDIO em pipeline.py).

## Experimento: formato curto contra longo
{_tabela(analise['por_formato'])}
O formato curto vale a aposta se o tempo médio assistido e os salvos/envios por 100 de alcance subirem. Com poucos Reels
no grupo curto, a comparação ainda não é confiável (compare de novo quando houver 8 ou mais).

## Por tema
{_tabela(analise['por_tema'])}

## Por horário de publicação
{_tabela(analise['por_faixa_horaria'])}

## Leitura
- Melhor tema (grupo com pelo menos {MIN_AMOSTRA} Reels): **{analise['melhor_tema']}**.
- Melhor faixa de horário: **{analise['melhor_faixa']}**.
- Amostra pequena: um vídeo que estoura distorce o grupo inteiro. Use como pista, não como regra, e confirme com mais posts.
- **Retenção:** em média as pessoas assistem {g['tempo_medio_s']} s de cada Reels. Se os vídeos têm 30 a 60 s, a maioria sai nos primeiros segundos: o gancho decide tudo e vídeo mais curto tende a reter mais.
- Salvos e envios por 100 de alcance medem se o vídeo vale guardar e mandar para um amigo, que é o que o algoritmo premia.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    load_dotenv(RAIZ / ".env")
    reels, _, seguidores = coletar(os.environ["INSTAGRAM_GRAPH_TOKEN"], os.environ["INSTAGRAM_USER_ID"])
    analise = analisar(reels)
    agora = datetime.now(BRASILIA).strftime("%Y-%m-%d %H:%M")
    RELATORIO.write_text(relatorio(analise, seguidores, agora), encoding="utf-8")
    DADOS.write_text(json.dumps({"gerado_em": agora, "seguidores": seguidores, **analise}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RELATORIO.read_text(encoding="utf-8"))
    if args.commit:
        try:
            subprocess.run(["git", "add", str(RELATORIO), str(DADOS)], cwd=RAIZ, check=True)
            if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=RAIZ).returncode != 0:
                subprocess.run(["git", "commit", "-m", "chore: análise de desempenho dos Reels [skip ci]"], cwd=RAIZ, check=True)
                subprocess.run(["git", "pull", "--rebase", "-q"], cwd=RAIZ, check=True)
                subprocess.run(["git", "push", "-q"], cwd=RAIZ, check=True)
        except subprocess.CalledProcessError as erro:
            print(f"não consegui gravar no git ({erro})")


if __name__ == "__main__":
    main()
