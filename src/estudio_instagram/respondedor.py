"""Bot do "comenta PALAVRA": responde em DM quem comentou a palavra-chave num post.

Roda de tempos em tempos (workflow instagram_respondedor.yml). Lê os comentários recentes pela
Graph API, e para cada comentário novo que contém uma palavra-chave manda a resposta privada
configurada em `pautas/bot_respostas.json`. O que já foi respondido fica em
`pautas/respostas_enviadas.json`, porque a Meta só aceita uma mensagem por comentário.

Uso:
    python -m src.estudio_instagram.respondedor            # responde de verdade
    python -m src.estudio_instagram.respondedor --simular  # só mostra o que responderia
"""

import argparse
import json
import os
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from .graph_api import InstagramGraph
from .sincronia import normalizar

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "pautas" / "bot_respostas.json"
ENVIADAS = RAIZ / "pautas" / "respostas_enviadas.json"
JANELA = timedelta(days=7)  # limite da Meta para a resposta privada


def _hora(texto: str) -> datetime:
    # A API devolve "2026-10-17T15:05:53+0000" (sem dois-pontos no fuso).
    return datetime.strptime(texto, "%Y-%m-%dT%H:%M:%S%z")


def palavra_encontrada(texto: str, palavras: dict[str, str]) -> str | None:
    """Palavra-chave que aparece no comentário (sem acento, sem diferença de maiúscula)."""
    presentes = {normalizar(p) for p in texto.split()}
    for palavra in palavras:
        if normalizar(palavra) in presentes:
            return palavra
    return None


def _avisar_no_comentario(config: dict, ig, comment_id: str, n: int):
    """Resposta pública curta embaixo do comentário. Revezar o texto evita parecer spam.

    Falhar aqui não pode desfazer a DM que já saiu, então só registra o erro.
    """
    avisos = config.get("resposta_publica") or []
    if not avisos:
        return
    try:
        ig.responder_publico(comment_id, avisos[n % len(avisos)])
    except urllib.error.HTTPError as erro:
        print(f"DM enviada, mas a resposta pública em {comment_id} falhou: HTTP {erro.code}")


def responder_novos(config: dict, enviadas: dict, ig, agora: datetime | None = None, simular: bool = False) -> list[dict]:
    """Responde cada comentário novo com palavra-chave. Devolve o que foi (ou seria) respondido.

    Marca o comentário como respondido logo depois de enviar. Se o envio falhar, registra o erro
    e segue: um comentário com problema não pode travar os outros.
    """
    agora = agora or datetime.now(timezone.utc)
    feitos = []
    for comentario in ig.comentarios_recentes():
        if comentario["id"] in enviadas:
            continue
        if agora - _hora(comentario["timestamp"]) > JANELA:
            continue
        palavra = palavra_encontrada(comentario.get("text", ""), config["palavras"])
        if not palavra:
            continue
        texto = config["palavras"][palavra]
        registro = {"comentario_id": comentario["id"], "usuario": comentario.get("username"), "palavra": palavra}
        if simular:
            feitos.append({**registro, "simulado": True})
            continue
        try:
            ig.responder_comentario(comentario["id"], texto)
            enviadas[comentario["id"]] = {**registro, "enviado_em": agora.isoformat(timespec="seconds")}
            feitos.append(registro)
            _avisar_no_comentario(config, ig, comentario["id"], len(enviadas))
        except urllib.error.HTTPError as erro:
            corpo = erro.read().decode(errors="replace")[:300]
            print(f"falhou ao responder {comentario['id']}: HTTP {erro.code} {corpo}")
    return feitos


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--simular", action="store_true")
    args = parser.parse_args()
    load_dotenv(RAIZ / ".env")
    ig = InstagramGraph(os.environ["INSTAGRAM_GRAPH_TOKEN"], os.environ["INSTAGRAM_USER_ID"])
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    enviadas = json.loads(ENVIADAS.read_text(encoding="utf-8")) if ENVIADAS.exists() else {}
    feitos = responder_novos(config, enviadas, ig, simular=args.simular)
    if not args.simular:
        ENVIADAS.write_text(json.dumps(enviadas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(feitos, ensure_ascii=False, indent=2) if feitos else "nenhum comentário novo com palavra-chave")


if __name__ == "__main__":
    main()
