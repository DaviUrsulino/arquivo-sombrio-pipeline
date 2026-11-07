"""Séries "você decide" (Davi, 06/11): o episódio sai terminando em "Comenta A ou B"; umas 12 horas depois o robô conta
os votos nos comentários, escreve o próximo episódio com a escolha que ganhou e a produtora anima com o MESMO
personagem e o MESMO estilo. História real com parte 2 (sem voto) usa os fatos da continuação guardados no episódio.

Cada episódio é um JSON em pautas/historias/ (o mesmo formato que `produtora --historia` lê). O estado de quais
episódios já ganharam continuação fica em pautas/series.json.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HISTORIAS = RAIZ / "pautas" / "historias"
ESTADO = RAIZ / "pautas" / "series.json"
POSTS = RAIZ / "pautas" / "pauta_por_post.json"
ESPERA_VOTOS = timedelta(hours=12)  # 22:30 -> pronto pra rodada das 22:30 do dia seguinte ("a parte 2 sai amanhã")
MAX_EPISODIOS = 6  # depois disso a série fecha (ou o Davi decide continuar)


def _ler(arquivo: Path) -> dict:
    try:
        return json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _normal(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().upper()


def slug_do_post(info: dict) -> str | None:
    """pautas/viral/fila/2026-11-06-1843-historia-preso-no-shopping-cartoon-3d-short.json -> preso-no-shopping."""
    nome = Path(info.get("pauta", "")).stem
    if "-historia-" not in nome:
        return None
    resto = nome.split("-historia-", 1)[1]
    for arq in sorted(HISTORIAS.glob("*.json"), key=lambda a: -len(a.stem)):
        if resto.startswith(arq.stem + "-") or resto == arq.stem:
            return arq.stem
    return None


def pendente(agora: datetime | None = None, posts: dict | None = None, estado: dict | None = None) -> dict | None:
    """O episódio no ar há mais de ESPERA_VOTOS que pede continuação e ainda não ganhou. None se não houver."""
    agora = agora or datetime.now(timezone.utc)
    posts = _ler(POSTS) if posts is None else posts
    estado = _ler(ESTADO) if estado is None else estado
    for media_id, info in sorted(posts.items(), key=lambda kv: kv[1].get("publicado_em", "")):
        slug = slug_do_post(info)
        if not slug or slug in estado:
            continue
        ep = _ler(HISTORIAS / f"{slug}.json")
        if not (ep.get("opcoes") or ep.get("fatos_continuacao")) or ep.get("episodio", 1) >= MAX_EPISODIOS:
            continue
        quando = datetime.fromisoformat(info.get("publicado_em", "2000-01-01T00:00:00+00:00"))
        if agora - quando >= ESPERA_VOTOS:
            return {"slug": slug, "media_id": media_id, "episodio": ep}
    return None


def contar_votos(comentarios: list[dict], media_id: str, opcoes: list[str]) -> dict[str, int]:
    votos = {o: 0 for o in opcoes}
    for c in comentarios:
        if c.get("midia_id") != media_id:
            continue
        texto = _normal(c.get("text", ""))
        achadas = [o for o in opcoes if re.search(rf"\b{re.escape(_normal(o))}\b", texto)]
        if len(achadas) == 1:  # comentário que cita as duas não conta
            votos[achadas[0]] += 1
    return votos


def vencedora(votos: dict[str, int]) -> str:
    """Mais votada; empate (ou zero voto) fica com a primeira opção, que é a que o roteiro deixa mais tensa."""
    return max(votos, key=lambda o: (votos[o], -list(votos).index(o)))


def escrever_proximo(p: dict, votos: dict[str, int] | None, llm=None) -> Path:
    """Escreve pautas/historias/<serie>-ep<N>.json com o próximo episódio (mesmo personagem, estilo e direção)."""
    from . import segredos
    from .llm import gerar_json
    ep = p["episodio"]
    n = ep.get("episodio", 1) + 1
    serie = ep.get("serie", p["slug"])
    escolha = vencedora(votos) if votos else None
    pedido = {"episodio_anterior": ep["roteiro"], "numero_do_novo_episodio": n, "opcoes_anteriores": ep.get("opcoes"),
              "votos": votos, "escolha_vencedora": escolha, "fatos_da_continuacao": ep.get("fatos_continuacao"),
              "ultimo_episodio": n >= MAX_EPISODIOS}
    gerar = llm or gerar_json
    r = gerar(segredos.texto("serie_episodio"), json.dumps(pedido, ensure_ascii=False))
    # Davi (07/11): "faz melhor ainda". O previsor critica; abaixo de 7,5 o roteirista reescreve com a crítica (até 2x).
    for _ in range(2):
        try:
            texto = (f"TEXTO NA TELA: {r['texto_tela']}\nABERTURA: {r['ganchos'][0]}\nCORPO: {' '.join(r['corpo'])}\n"
                     f"FECHAMENTO: {r['cta']}")
            nota = gerar(segredos.texto("viral_nota"), texto)
        except Exception as erro:
            print(f"previsor do episódio falhou ({erro}); sigo com o roteiro")
            break
        print(f"episódio {n}: nota {nota.get('nota')} ({nota.get('problema')})", flush=True)
        if float(nota.get("nota") or 0) >= 7.5:
            break
        pedido["critica_do_editor"] = nota.get("problema")
        pedido["roteiro_rejeitado"] = {k: r.get(k) for k in ("texto_tela", "ganchos", "corpo", "cta")}
        r = gerar(segredos.texto("serie_episodio"), json.dumps(pedido, ensure_ascii=False))
    novo = {k: ep[k] for k in ("estilo", "direcao") if k in ep}
    novo.update({"slug": f"{serie}-ep{n}", "serie": serie, "episodio": n,
                 "roteiro": {k: r[k] for k in ("texto_tela", "ganchos", "corpo", "cta", "legenda")},
                 "opcoes": r.get("opcoes") or None, "fatos_continuacao": r.get("fatos_continuacao") or None,
                 "escolha_anterior": escolha, "votos_anteriores": votos,
                 "produzir": True, "prioridade": True})  # se a produção falhar (ex.: limite do Claude), tenta de novo
    novo["roteiro"]["palavra"] = ""
    destino = HISTORIAS / f"{novo['slug']}.json"
    destino.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino


def registrar(slug: str, resultado: str):
    estado = _ler(ESTADO)
    estado[slug] = {"quando": datetime.now(timezone.utc).isoformat(timespec="minutes"), "resultado": resultado}
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")


def preparar_proximo(ig=None) -> Path | None:
    """Usado pela produtora no --auto: se tem episódio esperando continuação, conta votos e escreve o próximo."""
    p = pendente()
    if not p:
        return None
    votos = None
    if p["episodio"].get("opcoes"):
        try:
            if ig is None:
                import os
                from .graph_api import InstagramGraph
                ig = InstagramGraph(os.environ["INSTAGRAM_GRAPH_TOKEN"], os.environ["INSTAGRAM_USER_ID"])
            votos = contar_votos(ig.comentarios_recentes(20), p["media_id"], p["episodio"]["opcoes"])
        except Exception as erro:  # sem voto contado a série segue com a primeira opção, nunca para
            print(f"não consegui contar os votos ({erro}); sigo com a primeira opção")
            votos = {o: 0 for o in p["episodio"]["opcoes"]}
    destino = escrever_proximo(p, votos)
    registrar(p["slug"], destino.stem)
    print(f"série {p['slug']}: votos {votos}; próximo episódio em {destino.relative_to(RAIZ)}", flush=True)
    return destino


def historia_para_produzir(estado: dict | None = None) -> Path | None:
    """Roteiro novo marcado com "produzir": true que ainda não virou vídeo (06/11: lote de 5 escritos à mão; o GitHub
    produz um por rodada, com o PC do Davi desligado). Episódio de série pendente tem prioridade (ver pendente)."""
    estado = _ler(ESTADO) if estado is None else estado
    # episódio de série (prometido "amanhã") antes dos roteiros novos
    for arq in sorted(HISTORIAS.glob("*.json"), key=lambda a: (not _ler(a).get("prioridade"), a.name)):
        h = _ler(arq)
        if h.get("produzir") and f"produzido:{arq.stem}" not in estado:
            return arq
    return None


def marcar_produzida(slug: str):
    registrar(f"produzido:{slug}", "ok")
