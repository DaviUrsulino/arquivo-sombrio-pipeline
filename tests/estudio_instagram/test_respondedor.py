import io
import json
import urllib.error
from datetime import datetime, timezone

from src.estudio_instagram.graph_api import InstagramGraph
from src.estudio_instagram.respondedor import palavra_encontrada, responder_novos

CONFIG = {"palavras": {"CLAUDE": "kit do claude", "PLANO": "kit do plano"}}
AGORA = datetime(2026, 10, 17, 18, 0, tzinfo=timezone.utc)


class InstagramFalso:
    def __init__(self, comentarios, falhar_em=None):
        self._comentarios = comentarios
        self.respostas = []
        self.falhar_em = falhar_em

    def comentarios_recentes(self):
        return self._comentarios

    def responder_comentario(self, comment_id, texto):
        if comment_id == self.falhar_em:
            raise urllib.error.HTTPError("u", 400, "ruim", {}, io.BytesIO(b'{"error":"x"}'))
        self.respostas.append((comment_id, texto))
        return {"message_id": "m"}


def _c(id, texto, hora="2026-10-17T15:05:53+0000", usuario="fulano"):
    return {"id": id, "text": texto, "username": usuario, "timestamp": hora}


def test_palavra_ignora_acento_maiuscula_e_pontuacao():
    assert palavra_encontrada("Quero o kit! claude!!", CONFIG["palavras"]) == "CLAUDE"
    assert palavra_encontrada("plano, por favor", CONFIG["palavras"]) == "PLANO"


def test_palavra_nao_casa_pedaco_de_outra_palavra():
    assert palavra_encontrada("claudemir", CONFIG["palavras"]) is None
    assert palavra_encontrada("que legal", CONFIG["palavras"]) is None


def test_responde_comentario_novo_e_marca_como_enviado():
    ig = InstagramFalso([_c("c1", "CLAUDE")])
    enviadas = {}
    feitos = responder_novos(CONFIG, enviadas, ig, AGORA)
    assert ig.respostas == [("c1", "kit do claude")]
    assert "c1" in enviadas and len(feitos) == 1


def test_nao_responde_duas_vezes_o_mesmo_comentario():
    ig = InstagramFalso([_c("c1", "CLAUDE")])
    enviadas = {"c1": {}}
    assert responder_novos(CONFIG, enviadas, ig, AGORA) == []
    assert ig.respostas == []


def test_ignora_comentario_sem_palavra_chave():
    ig = InstagramFalso([_c("c1", "muito bom!")])
    assert responder_novos(CONFIG, {}, ig, AGORA) == []


def test_ignora_comentario_com_mais_de_7_dias():
    ig = InstagramFalso([_c("c1", "CLAUDE", hora="2026-10-01T10:00:00+0000")])
    assert responder_novos(CONFIG, {}, ig, AGORA) == []


def test_simular_nao_envia_nem_marca():
    ig = InstagramFalso([_c("c1", "CLAUDE")])
    enviadas = {}
    feitos = responder_novos(CONFIG, enviadas, ig, AGORA, simular=True)
    assert feitos[0]["simulado"] is True
    assert ig.respostas == [] and enviadas == {}


def test_falha_em_um_comentario_nao_trava_os_outros():
    ig = InstagramFalso([_c("c1", "CLAUDE"), _c("c2", "PLANO")], falhar_em="c1")
    enviadas = {}
    responder_novos(CONFIG, enviadas, ig, AGORA)
    assert ig.respostas == [("c2", "kit do plano")]
    assert "c1" not in enviadas and "c2" in enviadas


class RespostaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_cliente_manda_resposta_privada_com_comment_id():
    pedidos = []

    def abrir(pedido, timeout=None):
        pedidos.append(pedido)
        return RespostaFalsa(b'{"message_id": "mid"}')

    InstagramGraph("tok", "user-9", abrir=abrir).responder_comentario("c1", "oi")
    corpo = json.loads(pedidos[0].data)
    assert pedidos[0].full_url.startswith("https://graph.instagram.com/v22.0/user-9/messages?")
    assert corpo == {"recipient": {"comment_id": "c1"}, "message": {"text": "oi"}}


def test_cliente_lista_comentarios_so_de_midia_com_comentario():
    respostas = [
        {"data": [{"id": "m1", "comments_count": 1}, {"id": "m2", "comments_count": 0}]},
        {"data": [{"id": "c1", "text": "oi", "username": "a", "timestamp": "t"}]},
    ]
    pedidos = []

    def abrir(pedido, timeout=None):
        pedidos.append(pedido.full_url)
        return RespostaFalsa(json.dumps(respostas.pop(0)).encode())

    achados = InstagramGraph("tok", "user-9", abrir=abrir).comentarios_recentes()
    assert [c["id"] for c in achados] == ["c1"] and achados[0]["midia_id"] == "m1"
    assert len(pedidos) == 2
