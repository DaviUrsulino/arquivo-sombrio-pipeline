"""Aponta os posts que não decolaram, para o Davi decidir se apaga.

Davi, 11/11: "se não passou de 300 views em 12 horas, eu apagaria -- já dá pra ver que o conteúdo ficou lixo".

Aqui o robô só APONTA; quem apaga é ele, no app. Dois motivos para não automatizar:
- apagar post é irreversível, e um vídeo às vezes pega alcance tardio (o melhor da conta levou dias);
- a conta é dele, e apagar errado custa mais caro do que deixar um post fraco no feed.

    python -m src.estudio_instagram.fracos            # lista o que está abaixo da linha
    python -m src.estudio_instagram.fracos --horas 24 --minimo 500
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone

MINIMO_VIEWS = 300   # linha que o Davi usa de olho
HORAS = 12           # tempo que o post tem para provar que anda


def _reels(token: str, ig_id: str, quantos: int = 30) -> list[dict]:
    from . import analista
    dados = analista._ler(f"{ig_id}/media", token, fields="id,timestamp,caption,permalink", limit=quantos)
    return [m for m in dados.get("data", [])]


def fracos(token: str, ig_id: str, agora: datetime | None = None,
           minimo: int = MINIMO_VIEWS, horas: int = HORAS) -> list[dict]:
    """Posts com mais de `horas` no ar e menos de `minimo` views, do pior para o melhor."""
    from . import analista
    agora = agora or datetime.now(timezone.utc)
    achados = []
    for m in _reels(token, ig_id):
        publicado = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
        idade = agora - publicado
        if idade < timedelta(hours=horas):
            continue  # ainda é cedo para julgar
        try:
            views = analista._ler(f"{m['id']}/insights", token, metric="views")["data"][0]["values"][0]["value"]
        except Exception:
            continue
        if views < minimo:
            achados.append({"id": m["id"], "views": views, "horas": round(idade.total_seconds() / 3600),
                            "legenda": (m.get("caption") or "").split("\n")[0][:70], "link": m.get("permalink", "")})
    return sorted(achados, key=lambda x: x["views"])


def main():
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--minimo", type=int, default=MINIMO_VIEWS)
    p.add_argument("--horas", type=int, default=HORAS)
    a = p.parse_args()
    lista = fracos(os.environ["INSTAGRAM_GRAPH_TOKEN"], os.environ["INSTAGRAM_USER_ID"],
                   minimo=a.minimo, horas=a.horas)
    if not lista:
        print(f"nenhum post abaixo de {a.minimo} views depois de {a.horas} h no ar")
        return
    print(f"{len(lista)} post(s) abaixo de {a.minimo} views depois de {a.horas} h — o Davi decide se apaga:\n")
    for f in lista:
        print(f"  {f['views']:>5} views em {f['horas']:>3} h  {f['legenda']}")
        print(f"        {f['link']}")


if __name__ == "__main__":
    main()
