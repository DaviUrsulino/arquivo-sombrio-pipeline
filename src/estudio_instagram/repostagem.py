"""Repostagem com outro gancho: o mesmo vídeo, com a primeira frase trocada, quando o 1º gancho foi mal.

Base (estudo de 2026-11-03): o @gab.gouvea postou o MESMO vídeo 3 vezes trocando só a 1ª frase e fez 32 mil,
122 mil e 941 mil views. O gancho sozinho fez 29x de diferença.

Regra: um post com gancho A, publicado há mais de 48 h e há menos de 7 dias, com views abaixo da mediana do perfil,
ganha uma pauta nova igual à original com a 1ª frase trocada pelo 1º gancho alternativo. Essa pauta vai para a fila
do maestro (pautas/viral/fila/), então sai DENTRO da grade, na rodada do banco de vídeos. No máximo uma por dia.
Chamado pelo analista, que já lê as views de cada Reels.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

RAIZ = Path(__file__).resolve().parents[2]
MAPA = RAIZ / "pautas" / "pauta_por_post.json"
REGISTRO = RAIZ / "pautas" / "repostagens.json"
FILA = RAIZ / "pautas" / "viral" / "fila"
MIN_HORAS, MAX_DIAS = 48, 7


def _hora(iso: str) -> datetime:
    return datetime.strptime(iso.replace("+0000", "+00:00"), "%Y-%m-%dT%H:%M:%S%z")


def _linhas_titulo(frase: str) -> list[dict]:
    """O título pixel da cena 1 só pode ter palavras da narração: quebra o gancho em 2-3 linhas de até 14 letras."""
    palavras = re.sub(r"[^\w\sÀ-ÿ]", "", frase).upper().split()
    linhas, atual = [], ""
    for p in palavras:
        if len((atual + " " + p).strip()) > 14:
            linhas.append(atual)
            atual = p
        else:
            atual = (atual + " " + p).strip()
    linhas.append(atual)
    cores = ["branco", "laranja", "amarelo"]
    return [{"texto": l, "cor": cores[i], "tamanho": 120} for i, l in enumerate([l for l in linhas if l][:3])]


def pauta_com_gancho(pauta: dict, gancho: str, letra: str, media_id: str) -> dict:
    nova = json.loads(json.dumps(pauta))
    cenas = nova.get("cenas_roteiro") or []
    if not cenas:
        raise ValueError("pauta sem cenas_roteiro")
    cenas[0]["narracao"] = gancho
    if (cenas[0].get("visual") or {}).get("tipo") == "titulo_pixel":
        cenas[0]["visual"]["linhas"] = _linhas_titulo(gancho)
    nova["gancho"] = letra
    nova["repost_de"] = media_id
    nova["ganchos_alternativos"] = []
    nova["titulo"] = f"{pauta.get('titulo', '')} (gancho {letra})"
    return nova


def escolher(reels: list[dict], mapa: dict, ja_feitos: set[str], agora: datetime) -> list[str]:
    """Ids dos posts que merecem repostagem, do pior para o melhor."""
    vistas = [r.get("views", 0) for r in reels if "views" in r]
    if len(vistas) < 5:
        return []
    corte = median(vistas)
    candidatos = []
    for r in reels:
        info = mapa.get(r["id"])
        if not info or info.get("gancho", "A") != "A" or info.get("repost_de") or r["id"] in ja_feitos:
            continue
        idade = agora - _hora(r["hora"])
        if not (timedelta(hours=MIN_HORAS) <= idade <= timedelta(days=MAX_DIAS)):
            continue
        if r.get("views", 0) < corte:
            candidatos.append((r.get("views", 0), r["id"]))
    return [i for _, i in sorted(candidatos)]


def agendar(reels: list[dict], agora: datetime | None = None, maximo: int = 1) -> list[Path]:
    """Cria até `maximo` pautas de repostagem na fila do maestro. Devolve os arquivos criados."""
    agora = agora or datetime.now(timezone.utc)
    mapa = json.loads(MAPA.read_text(encoding="utf-8")) if MAPA.exists() else {}
    registro = json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.exists() else {}
    criados = []
    for media_id in escolher(reels, mapa, set(registro), agora):
        if len(criados) >= maximo:
            break
        caminho = RAIZ / mapa[media_id]["pauta"]
        if not caminho.exists():
            continue
        pauta = json.loads(caminho.read_text(encoding="utf-8"))
        alternativos = pauta.get("ganchos_alternativos") or []
        if not alternativos:
            continue
        nova = pauta_com_gancho(pauta, alternativos[0], "B", media_id)
        FILA.mkdir(parents=True, exist_ok=True)
        destino = FILA / f"{agora:%Y-%m-%d}-repost-{media_id}.json"
        destino.write_text(json.dumps(nova, ensure_ascii=False, indent=1), encoding="utf-8")
        registro[media_id] = {"pauta": str(destino.relative_to(RAIZ)), "gancho": "B", "em": agora.isoformat(timespec="minutes")}
        criados.append(destino)
    if criados:
        REGISTRO.write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
    return criados
