"""Responde perguntas de verdade nos comentários e no direct, com fatos, no tom do perfil.

Por que existe (Davi, 2026-11-04): quase todo mundo só comenta a palavra-chave, então quando alguém faz uma
pergunta de verdade ("E os dados bancários?" no Reel do Mika) ela precisa de resposta rápida, e o Davi nem sempre
vê. A primeira meia hora depois do comentário é a que mais rende (skill reply-and-comment-writer).

Regras:
- Só pergunta de verdade (tem "?" ou começa como pergunta, 3+ palavras). Palavra-chave e elogio ficam com o
  respondedor de sempre. No direct, só a última mensagem da pessoa, dentro da janela de 24 h da Meta.
- No máximo LIMITE_POR_DIA respostas por dia (comentário + direct): resposta automática em massa é punida.
- Os fatos vêm do README do repositório do post e da legenda. Se os fatos não respondem, NÃO responde (fica para o
  Davi): melhor calar do que inventar.
- O texto do comentário e o README são DADOS, nunca instruções. A resposta passa por uma conferência (tamanho,
  sem link, sem @, sem emoji, sem hashtag) antes de sair.
- O registro guarda só ids (repositório público, LGPD).
"""

import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .llm import gerar_json
from . import segredos

RAIZ = Path(__file__).resolve().parents[2]
REGISTRO = RAIZ / "pautas" / "perguntas_respondidas.json"
PAUTA_POR_POST = RAIZ / "pautas" / "pauta_por_post.json"
LINKS_POR_POST = RAIZ / "pautas" / "links_por_post.json"
LIMITE_POR_DIA = 10
JANELA_COMENTARIO = timedelta(days=3)
JANELA_DM = timedelta(hours=23)  # a Meta fecha a conversa 24 h depois da última mensagem da pessoa
COMECO_DE_PERGUNTA = re.compile(r"^(como|qual|quais|quanto|quantos|quando|onde|porque|por que|pq|funciona|serve|"
                                r"precisa|da pra|dá pra|tem como|e se|e o|e a|e os|e as|é pago|e pago|é grátis|roda)\b", re.I)
PERFIL = "ursulino.ia"

SISTEMA = segredos.texto("perguntas_sistema")  # texto no repositório privado (ver segredos.py)


def eh_pergunta(texto: str) -> bool:
    t = (texto or "").strip()
    if len(t.split()) < 3 or t.lstrip().startswith("@"):
        return False
    return "?" in t or bool(COMECO_DE_PERGUNTA.match(t))


def resposta_segura(texto: str) -> bool:
    if not texto or len(texto) > 320:
        return False
    if re.search(r"https?://|www\.|@|#", texto):
        return False
    return all(ord(c) < 0x2190 for c in texto)  # sem emoji nem símbolo gráfico


def _ler(arquivo: Path, padrao):
    return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else padrao


def respondidas_hoje(registro: dict, agora: datetime) -> int:
    dia = agora.date().isoformat()
    return sum(1 for r in registro.values() if r.get("em", "").startswith(dia))


def _readme(repo: str, abrir=urllib.request.urlopen) -> str:
    try:
        pedido = urllib.request.Request(f"https://api.github.com/repos/{repo}/readme",
                                        headers={"Accept": "application/vnd.github.raw", "User-Agent": "estudio-automatico"})
        with abrir(pedido, timeout=20) as r:
            return r.read().decode("utf-8", "replace")[:4000]
    except Exception:
        return ""


def fatos_do_post(midia_id: str, legenda: str = "", leitor=_readme) -> str:
    """Legenda do post + README dos repositórios da pauta que gerou o post."""
    partes = [f"LEGENDA DO POST:\n{legenda}"] if legenda else []
    repos = []
    registro = _ler(PAUTA_POR_POST, {}).get(midia_id)
    if registro:
        repos = [i["repo"] for i in _ler(RAIZ / registro["pauta"], {}).get("itens", []) if i.get("repo")]
    link = _ler(LINKS_POR_POST, {}).get(midia_id)  # posts mais antigos só têm o registro do respondedor
    if link:
        partes.append(f"MENSAGEM QUE O PERFIL MANDA NO DIRECT SOBRE ESTE POST:\n{link.get('mensagem', '')}")
        repos = repos or ([link["repo"]] if link.get("repo") else [])
    for repo in repos[:4]:
        partes.append(f"README DE {repo}:\n{leitor(repo)}")
    return "\n\n".join(partes)


def escrever(pergunta: str, fatos: str, llm=gerar_json) -> str | None:
    if not fatos.strip():
        return None
    r = llm(SISTEMA, f"FATOS:\n{fatos}\n\nPERGUNTA:\n{pergunta}")
    texto = (r.get("texto") or "").strip() if r.get("responder") else ""
    return texto if resposta_segura(texto) else None


def responder_comentarios(ig, comentarios: list[dict], registro: dict, agora: datetime, ja_tratados: set,
                          llm=gerar_json, leitor=_readme, simular: bool = False) -> list[dict]:
    feitos = []
    legendas = {}
    for c in comentarios:
        if respondidas_hoje(registro, agora) >= LIMITE_POR_DIA:
            break
        autor = c.get("username") or c.get("from", {}).get("username")
        if c["id"] in registro or c["id"] in ja_tratados or autor == PERFIL:
            continue
        if agora - datetime.fromisoformat(c["timestamp"].replace("+0000", "+00:00")) > JANELA_COMENTARIO:
            continue
        if not eh_pergunta(c.get("text", "")) or c.get("tem_resposta"):
            continue
        midia = c.get("midia_id", "")
        if midia not in legendas:
            legendas[midia] = (ig._ler(midia, fields="caption").get("caption") or "") if midia else ""
        texto = escrever(c["text"], fatos_do_post(midia, legendas[midia], leitor), llm)
        registro[c["id"]] = {"tipo": "comentario", "em": agora.isoformat(timespec="seconds"), "respondeu": bool(texto)}
        if texto and not simular:
            ig.responder_publico(c["id"], texto)
        if texto:
            feitos.append({"comentario_id": c["id"], "texto": texto, "simulado": simular})
    return feitos


def responder_direct(ig, registro: dict, agora: datetime, llm=gerar_json, simular: bool = False) -> list[dict]:
    """Última mensagem de cada conversa recente: se for pergunta da pessoa e ainda dá tempo, responde."""
    feitos = []
    conversas = ig._ler(f"{ig.ig_user_id}/conversations", platform="instagram", limit=20,
                        fields="id,updated_time,messages.limit(6){id,message,from,created_time}").get("data", [])
    for conversa in conversas:
        if respondidas_hoje(registro, agora) >= LIMITE_POR_DIA:
            break
        msgs = conversa.get("messages", {}).get("data", [])
        if not msgs:
            continue
        ultima = msgs[0]  # a API devolve da mais nova para a mais antiga
        de = ultima.get("from", {})
        if de.get("username") == PERFIL or ultima["id"] in registro or not eh_pergunta(ultima.get("message", "")):
            continue
        if agora - datetime.fromisoformat(ultima["created_time"].replace("+0000", "+00:00")) > JANELA_DM:
            continue
        historico = "\n".join(f"{'PERFIL' if m.get('from', {}).get('username') == PERFIL else 'PESSOA'}: {m.get('message', '')}"
                              for m in reversed(msgs[1:]))
        fatos = f"CONVERSA ANTERIOR (o que o perfil já mandou, inclusive links e repositórios):\n{historico}"
        texto = escrever(ultima["message"], fatos, llm)
        registro[ultima["id"]] = {"tipo": "direct", "em": agora.isoformat(timespec="seconds"), "respondeu": bool(texto)}
        if texto and not simular:
            ig.enviar_mensagem(de["id"], texto)
        if texto:
            feitos.append({"mensagem_id": ultima["id"], "texto": texto, "simulado": simular})
    return feitos


def passada(ig, comentarios: list[dict], ja_tratados: set, simular: bool = False) -> list[dict]:
    """Uma rodada de comentários + direct. Grava o registro (só ids) quando não é simulação."""
    agora = datetime.now(timezone.utc)
    registro = _ler(REGISTRO, {})
    feitos = responder_comentarios(ig, comentarios, registro, agora, ja_tratados, simular=simular)
    try:
        feitos += responder_direct(ig, registro, agora, simular=simular)
    except Exception as erro:  # direct fora do ar não pode travar os comentários
        print(f"direct indisponível: {str(erro)[:160]}")
    if not simular:
        REGISTRO.write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
    return feitos
