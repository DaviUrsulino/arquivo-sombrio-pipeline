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
import hashlib
import json
import os
import subprocess
import time
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from .graph_api import InstagramGraph
from .sincronia import normalizar

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "pautas" / "bot_respostas.json"
ENVIADAS = RAIZ / "pautas" / "respostas_enviadas.json"
# Cada post de repositório registra aqui a palavra e a mensagem dele (chave = id da mídia no Instagram).
LINKS_POR_POST = RAIZ / "pautas" / "links_por_post.json"
# Quem pediu um link grátis e ainda precisa seguir a conta: chave = hash do id da pessoa (nada que a identifique no repositório público).
PENDENTES = RAIZ / "pautas" / "pendentes_seguir.json"
# Se a API não sabe dizer se a pessoa segue (erro 230: o app só tem acesso padrão, sem revisão da Meta), vale a palavra dela: manda o link.
# Em post de repositório, quem comenta uma destas palavras também recebe o link do repositório do post.
SINONIMOS_DO_POST = ("REPO", "REPOSITORIO", "LINK", "QUERO", "EU QUERO")
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


def _chave(igsid: str) -> str:
    return hashlib.sha256(igsid.encode()).hexdigest()[:16]


def _exige_seguir(config: dict, palavra: str, comentario: dict) -> bool:
    """Só filtra link grátis (repositório, kit). Link de produto pago sai direto. Sem id da pessoa, não dá para conferir."""
    if not config.get("exigir_seguir"):
        return False
    if palavra in config.get("sem_filtro", []):
        return False
    return bool((comentario.get("from") or {}).get("id"))


def liberar_pendentes(config: dict, pendentes: dict, ig, agora: datetime | None = None, simular: bool = False) -> list[dict]:
    """Para cada pessoa que respondeu na DM: se segue a conta, manda o link; se não, pede de novo.

    Só reage a mensagem nova da pessoa (guarda a hora da última já tratada) para não repetir o aviso.
    """
    agora = agora or datetime.now(timezone.utc)
    feitos = []
    for chave in [k for k, v in pendentes.items() if agora - _hora(v["desde"]) > JANELA]:
        del pendentes[chave]  # passou da validade da resposta; a pessoa pode comentar de novo
    if not pendentes:
        return feitos
    for conversa in ig.conversas_recentes():
        chave = _chave(conversa["usuario_id"])
        pendente = pendentes.get(chave)
        if not pendente:
            continue
        dela = [m for m in conversa["mensagens"] if m["de"] == conversa["usuario_id"] and m["hora"]]
        if not dela:
            continue
        ultima = max(dela, key=lambda m: _hora(m["hora"]))
        nova = _hora(ultima["hora"]) > _hora(pendente.get("tratada_ate", pendente["desde"]))
        # Pendente antigo que já levou o aviso "não consegui confirmar" (versão anterior): libera agora, dentro da janela de 24 h.
        legado = pendente.get("erros", 0) >= 1 and agora - _hora(ultima["hora"]) < timedelta(hours=23)
        if not nova and not legado:
            continue
        segue = ig.segue_a_conta(conversa["usuario_id"]) if nova else None
        verificado = segue is not None
        if segue is None:
            segue = True
        registro = {"palavra": pendente["palavra"], "segue": segue, "verificado": verificado}
        if simular:
            feitos.append({**registro, "simulado": True})
            continue
        try:
            if segue:
                ig.enviar_mensagem(conversa["usuario_id"], pendente["mensagem"])
                del pendentes[chave]
            else:
                ig.enviar_mensagem(conversa["usuario_id"], config["mensagem_nao_segue"])
                pendente["tratada_ate"] = ultima["hora"]
            feitos.append(registro)
        except urllib.error.HTTPError as erro:
            print(f"falhou ao responder na DM: HTTP {erro.code} {erro.read().decode(errors='replace')[:200]}")
    return feitos


def _mensagem_para(comentario: dict, config: dict, por_post: dict) -> tuple[str, str] | None:
    """(palavra, mensagem) para este comentário: primeiro as palavras globais, depois a do post."""
    texto = comentario.get("text", "")
    palavra = palavra_encontrada(texto, config["palavras"])
    if palavra:
        return palavra, config["palavras"][palavra]
    do_post = por_post.get(comentario.get("midia_id", ""))
    if do_post and palavra_encontrada(texto, {p: "" for p in (do_post["palavra"], *SINONIMOS_DO_POST)}):
        return do_post["palavra"], do_post["mensagem"]
    return None


def responder_novos(config: dict, enviadas: dict, ig, agora: datetime | None = None, simular: bool = False,
                    por_post: dict | None = None, pendentes: dict | None = None) -> list[dict]:
    """Responde cada comentário novo com palavra-chave. Devolve o que foi (ou seria) respondido.

    Marca o comentário como respondido logo depois de enviar. Se o envio falhar, registra o erro
    e segue: um comentário com problema não pode travar os outros.
    """
    agora = agora or datetime.now(timezone.utc)
    feitos = []
    if pendentes is None:
        pendentes = {}
    for comentario in ig.comentarios_recentes():
        if comentario["id"] in enviadas:
            continue
        if agora - _hora(comentario["timestamp"]) > JANELA:
            continue
        achado = _mensagem_para(comentario, config, por_post or {})
        if not achado:
            continue
        palavra, texto = achado
        gate = _exige_seguir(config, palavra, comentario)
        # Só o id do comentário e a palavra: o arquivo vai pro repositório público (LGPD, RN-3), então
        # nada que identifique a pessoa (nome de usuário, texto do comentário).
        registro = {"comentario_id": comentario["id"], "palavra": palavra}
        if simular:
            feitos.append({**registro, "simulado": True})
            continue
        try:
            if gate:
                # Passo 1: pede para seguir e responder. O link só sai depois de conferir que a pessoa segue.
                pendentes[_chave(comentario["from"]["id"])] = {
                    "palavra": palavra, "mensagem": texto, "desde": agora.isoformat(timespec="seconds")}
                ig.responder_comentario(comentario["id"], config["mensagem_pedido"])
            else:
                ig.responder_comentario(comentario["id"], texto)
            enviadas[comentario["id"]] = {**registro, "enviado_em": agora.isoformat(timespec="seconds")}
            feitos.append(registro)
            _avisar_no_comentario(config, ig, comentario["id"], len(enviadas))
        except urllib.error.HTTPError as erro:
            if gate:
                pendentes.pop(_chave(comentario["from"]["id"]), None)  # o pedido não saiu: não deixa pendente órfão
            corpo = erro.read().decode(errors="replace")[:300]
            print(f"falhou ao responder {comentario['id']}: HTTP {erro.code} {corpo}")
    return feitos


def _ler_json(arquivo: Path, padrao):
    return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else padrao


def _guardar_no_git():
    """Commita e sobe o registro de quem já foi respondido. Falha aqui não derruba o laço."""
    try:
        subprocess.run(["git", "add", str(ENVIADAS), str(PENDENTES)], cwd=RAIZ, check=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=RAIZ).returncode == 0:
            return
        subprocess.run(["git", "commit", "-m", "chore: registra respostas enviadas pelo bot [skip ci]"], cwd=RAIZ, check=True)
        subprocess.run(["git", "pull", "--rebase", "-q"], cwd=RAIZ, check=True)
        subprocess.run(["git", "push", "-q"], cwd=RAIZ, check=True)
    except subprocess.CalledProcessError as erro:
        print(f"não consegui gravar no git ({erro}); sigo, o próximo ciclo tenta de novo")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--simular", action="store_true")
    parser.add_argument("--minutos", type=float, default=0, help="fica em laço por tantos minutos (0 = uma passada só)")
    parser.add_argument("--intervalo", type=int, default=120, help="segundos entre passadas no laço")
    parser.add_argument("--commit", action="store_true", help="grava o registro no git depois de cada passada com resposta")
    args = parser.parse_args()
    load_dotenv(RAIZ / ".env")
    ig = InstagramGraph(os.environ["INSTAGRAM_GRAPH_TOKEN"], os.environ["INSTAGRAM_USER_ID"])
    config = _ler_json(CONFIG, {})
    fim = time.monotonic() + args.minutos * 60
    while True:
        # Recarrega a cada passada: o registro e os links por post mudam enquanto o laço roda.
        enviadas = _ler_json(ENVIADAS, {})
        por_post = _ler_json(LINKS_POR_POST, {})
        pendentes = _ler_json(PENDENTES, {})
        try:
            feitos = responder_novos(config, enviadas, ig, simular=args.simular, por_post=por_post, pendentes=pendentes)
            feitos += liberar_pendentes(config, pendentes, ig, simular=args.simular)
        except Exception as erro:  # API fora do ar, rede: não pode matar o laço inteiro
            print(f"passada falhou ({str(erro)[:200]}); tento de novo")
            feitos = []
        if feitos and not args.simular:
            ENVIADAS.write_text(json.dumps(enviadas, ensure_ascii=False, indent=2), encoding="utf-8")
            PENDENTES.write_text(json.dumps(pendentes, ensure_ascii=False, indent=2), encoding="utf-8")
            if args.commit:
                _guardar_no_git()
        print(json.dumps(feitos, ensure_ascii=False) if feitos else "nenhum comentário novo com palavra-chave", flush=True)
        if time.monotonic() + args.intervalo >= fim:
            break
        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
