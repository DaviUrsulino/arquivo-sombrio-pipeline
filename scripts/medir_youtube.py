"""Mede os Shorts dos dois canais do YouTube (views, likes, comentários) e agrupa por molde do ciclo de teste.

Davi, 11/11: ciclo de 3 a 5 dias com vários moldes de animação; na segunda a gente olha o que rendeu. Este script é
o "olhar": lê a lista de uploads de cada conta pela YouTube Data API (os tokens já existem na raiz), cruza com as
pautas de pautas/youtube/fila/ (que guardam o molde e a URL publicada) e grava pautas/youtube/desempenho.json.

    python scripts/medir_youtube.py            # os dois canais
    python scripts/medir_youtube.py --conta tendencias

Custo de cota: ~3 unidades por chamada de lista + 1 por lote de 50 vídeos; desprezível perto dos 1.600 de um upload.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from pipeline_completo import CREDENCIAIS_POR_CONTA  # noqa: E402
from publicar_youtube import autenticar  # noqa: E402

FILA = RAIZ / "pautas" / "youtube" / "fila"
SAIDA = RAIZ / "pautas" / "youtube" / "desempenho.json"


def videos_da_conta(conta: str, maximo: int = 100) -> list[dict]:
    from googleapiclient.discovery import build
    cred = CREDENCIAIS_POR_CONTA[conta]
    yt = build("youtube", "v3", credentials=autenticar(cred["youtube_client_secret"], cred["youtube_token"]))
    canal = yt.channels().list(part="contentDetails,statistics", mine=True).execute()["items"][0]
    uploads = canal["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while len(ids) < maximo:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        token = r.get("nextPageToken")
        if not token:
            break
    saida = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,statistics", id=",".join(ids[i:i + 50])).execute()
        for v in r["items"]:
            st = v.get("statistics", {})
            saida.append({"id": v["id"], "titulo": v["snippet"]["title"], "publicado": v["snippet"]["publishedAt"],
                          "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
                          "comentarios": int(st.get("commentCount", 0))})
    return saida, {"inscritos": int(canal["statistics"].get("subscriberCount", 0)),
                   "videos": int(canal["statistics"].get("videoCount", 0))}


def moldes_publicados() -> dict[str, dict]:
    """id do vídeo no YouTube -> {molde, estilo, slug} a partir das pautas da fila."""
    mapa = {}
    for arq in sorted(FILA.glob("*.json")) if FILA.exists() else []:
        p = json.loads(arq.read_text(encoding="utf-8"))
        for conta, pub in (p.get("publicado") or {}).items():
            vid = (pub.get("url") or "").rsplit("/", 1)[-1]
            if vid:
                mapa[vid] = {"molde": p.get("molde", ""), "estilo": p.get("estilo", ""), "slug": p.get("slug", ""), "conta": conta}
    return mapa


def resumo(videos: list[dict], mapa: dict) -> dict:
    por_molde: dict[str, list[int]] = {}
    for v in videos:
        chave = mapa.get(v["id"], {}).get("molde") or "foto (antigo)"
        por_molde.setdefault(chave, []).append(v["views"])
    return {m: {"n": len(vs), "mediana": statistics.median(vs), "maior": max(vs)} for m, vs in por_molde.items()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--conta", choices=list(CREDENCIAIS_POR_CONTA), default=None)
    p.add_argument("--alerta-horas", type=float, default=0,
                   help="sai com erro se alguma conta ficou mais que N horas sem publicar (o workflow diário usa 26)")
    a = p.parse_args()
    contas = [a.conta] if a.conta else list(CREDENCIAIS_POR_CONTA)
    mapa = moldes_publicados()
    relatorio = {"medido_em": datetime.now(timezone.utc).isoformat(timespec="minutes"), "contas": {}}
    for conta in contas:
        videos, canal = videos_da_conta(conta)
        relatorio["contas"][conta] = {"canal": canal, "por_molde": resumo(videos, mapa),
                                      "videos": [{**v, **mapa.get(v["id"], {})} for v in videos]}
        print(f"== {conta}: {canal['inscritos']} inscritos, {len(videos)} vídeos lidos")
        for molde, r in sorted(relatorio["contas"][conta]["por_molde"].items(), key=lambda kv: -kv[1]["mediana"]):
            print(f"  {molde:22} n={r['n']:3}  mediana={r['mediana']:>8.0f}  maior={r['maior']:>8}")
    silenciosas = []
    if a.alerta_horas:
        limite = datetime.now(timezone.utc).timestamp() - a.alerta_horas * 3600
        for conta, dados in relatorio["contas"].items():
            ultimo = max((datetime.fromisoformat(v["publicado"].replace("Z", "+00:00")).timestamp() for v in dados["videos"]), default=0)
            if ultimo < limite:
                silenciosas.append(conta)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado em {SAIDA.relative_to(RAIZ)}")
    if silenciosas:
        print(f"ALERTA: sem publicar há mais de {a.alerta_horas:.0f} h: {', '.join(silenciosas)}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
