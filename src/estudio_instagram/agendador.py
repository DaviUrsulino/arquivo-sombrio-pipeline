"""Publica Reels já prontos na hora marcada.

A lista fica em `pautas/agendadas.json`. Cada item guarda a URL pública do vídeo (já hospedado
na release do repositório, ver hospedagem.py), a legenda e o horário em UTC. Um workflow roda de
tempos em tempos, chama `executar_vencidos` e publica o que já passou da hora e ainda não saiu.
O vídeo publicado é exatamente o que o Davi aprovou: nada é gerado de novo aqui.

Uso:
    python -m src.estudio_instagram.agendador
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .graph_api import InstagramGraph

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO = RAIZ / "pautas" / "agendadas.json"


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _hora(texto: str) -> datetime:
    hora = datetime.fromisoformat(texto)
    return hora if hora.tzinfo else hora.replace(tzinfo=timezone.utc)


def executar_vencidos(arquivo: Path, ig: InstagramGraph, agora: datetime | None = None) -> list[dict]:
    """Publica cada item vencido e ainda não publicado. Devolve os itens publicados agora.

    Grava o arquivo depois de cada publicação: se a seguinte falhar, a anterior não é repetida.
    """
    agora = agora or _agora_utc()
    itens = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    publicados = []
    for item in itens:
        if item.get("publicado") or _hora(item["postar_apos"]) > agora:
            continue
        resultado = ig.publicar_reels(item["video_url"], item["legenda"])
        item["publicado"] = True
        item["media_id"] = resultado.media_id
        item["publicado_em"] = agora.isoformat(timespec="seconds")
        Path(arquivo).write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")
        publicados.append(item)
    return publicados


def main():
    load_dotenv(RAIZ / ".env")
    ig = InstagramGraph(os.environ["INSTAGRAM_GRAPH_TOKEN"], os.environ["INSTAGRAM_USER_ID"])
    publicados = executar_vencidos(ARQUIVO, ig)
    print(json.dumps(publicados, ensure_ascii=False, indent=2) if publicados else "nada vencido")


if __name__ == "__main__":
    main()
