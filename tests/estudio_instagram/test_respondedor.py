import io
import json
import urllib.error
from datetime import datetime, timezone

from src.estudio_instagram.graph_api import InstagramGraph
from src.estudio_instagram.respondedor import _chave, liberar_pendentes, palavra_encontrada, responder_novos

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


def test_avisa_no_comentario_depois_da_dm_e_reveza_o_texto():
    class IgComAviso(InstagramFalso):
        publicos = []

        def responder_publico(self, comment_id, texto):
            self.publicos.append((comment_id, texto))

    ig = IgComAviso([_c("c1", "CLAUDE"), _c("c2", "PLANO")])
    config = {**CONFIG, "resposta_publica": ["a", "b"]}
    responder_novos(config, {}, ig, AGORA)
    assert len(ig.publicos) == 2 and ig.publicos[0][1] != ig.publicos[1][1]


def test_falha_na_resposta_publica_nao_desfaz_a_dm():
    class IgPublicoQuebrado(InstagramFalso):
        def responder_publico(self, comment_id, texto):
            raise urllib.error.HTTPError("u", 400, "ruim", {}, io.BytesIO(b"x"))

    ig = IgPublicoQuebrado([_c("c1", "CLAUDE")])
    enviadas = {}
    responder_novos({**CONFIG, "resposta_publica": ["a"]}, enviadas, ig, AGORA)
    assert ig.respostas == [("c1", "kit do claude")] and "c1" in enviadas


def test_cliente_responde_publico_no_endpoint_de_replies():
    pedidos = []

    def abrir(pedido, timeout=None):
        pedidos.append(pedido)
        return RespostaFalsa(b'{"id": "r1"}')

    InstagramGraph("tok", "user-9", abrir=abrir).responder_publico("c1", "oi")
    assert pedidos[0].full_url == "https://graph.instagram.com/v22.0/c1/replies"
    assert "message=oi" in pedidos[0].data.decode()


def test_responde_com_o_link_do_post_quando_a_palavra_e_do_post():
    ig = InstagramFalso([{**_c("c1", "link"), "midia_id": "m1"}, {**_c("c2", "link"), "midia_id": "outra"}])
    por_post = {"m1": {"palavra": "LINK", "mensagem": "repo do post", "repo": "a/b"}}
    feitos = responder_novos(CONFIG, {}, ig, AGORA, por_post=por_post)
    assert ig.respostas == [("c1", "repo do post")] and len(feitos) == 1


CONFIG_FILTRO = {
    "palavras": {"CLAUDE": "link do kit", "PACK": "link pago do pack"},
    "exigir_seguir": True, "sem_filtro": ["PACK"],
    "mensagem_pedido": "segue e responde SIGO", "mensagem_nao_segue": "ainda não vi o follow",
}


class InstagramComConversa(InstagramFalso):
    def __init__(self, comentarios, conversas=None, segue=True):
        super().__init__(comentarios)
        self._conversas, self._segue = conversas or [], segue
        self.mensagens = []

    def conversas_recentes(self):
        return self._conversas

    def segue_a_conta(self, igsid):
        return self._segue

    def enviar_mensagem(self, igsid, texto):
        self.mensagens.append((igsid, texto))


def _cd(id, texto, quem="u1"):
    return {**_c(id, texto), "from": {"id": quem}}


def test_link_gratis_pede_para_seguir_antes_de_mandar():
    ig, pend = InstagramComConversa([_cd("c1", "CLAUDE")]), {}
    responder_novos(CONFIG_FILTRO, {}, ig, agora=AGORA, pendentes=pend)
    assert ig.respostas == [("c1", "segue e responde SIGO")]
    assert pend[_chave("u1")]["mensagem"] == "link do kit"


def test_link_de_produto_pago_sai_direto_sem_filtro():
    ig, pend = InstagramComConversa([_cd("c1", "PACK")]), {}
    responder_novos(CONFIG_FILTRO, {}, ig, agora=AGORA, pendentes=pend)
    assert ig.respostas == [("c1", "link pago do pack")] and pend == {}


def test_sem_id_da_pessoa_manda_o_link_como_antes():
    ig, pend = InstagramComConversa([_c("c1", "CLAUDE")]), {}
    responder_novos(CONFIG_FILTRO, {}, ig, agora=AGORA, pendentes=pend)
    assert ig.respostas == [("c1", "link do kit")]


def _pendente(**extra):
    return {_chave("u1"): {"palavra": "CLAUDE", "mensagem": "link do kit", "desde": "2026-10-17T15:00:00+00:00", **extra}}


def _resposta_da_pessoa(hora="2026-10-17T16:00:00+0000"):
    return [{"usuario_id": "u1", "mensagens": [{"de": "u1", "texto": "SIGO", "hora": hora}]}]


def test_quem_segue_e_responde_recebe_o_link_e_sai_da_lista():
    ig, pend = InstagramComConversa([], _resposta_da_pessoa(), segue=True), _pendente()
    feitos = liberar_pendentes(CONFIG_FILTRO, pend, ig, agora=AGORA)
    assert ig.mensagens == [("u1", "link do kit")] and pend == {} and feitos[0]["segue"] is True


def test_quem_nao_segue_recebe_aviso_uma_vez_so_por_mensagem():
    ig, pend = InstagramComConversa([], _resposta_da_pessoa(), segue=False), _pendente()
    liberar_pendentes(CONFIG_FILTRO, pend, ig, agora=AGORA)
    liberar_pendentes(CONFIG_FILTRO, pend, ig, agora=AGORA)  # mesma mensagem da pessoa: não repete o aviso
    assert ig.mensagens == [("u1", "ainda não vi o follow")] and _chave("u1") in pend


def test_sem_resposta_da_pessoa_nada_acontece():
    conversa = [{"usuario_id": "u1", "mensagens": [{"de": "eu", "texto": "segue", "hora": "2026-10-17T15:01:00+0000"}]}]
    ig, pend = InstagramComConversa([], conversa), _pendente()
    assert liberar_pendentes(CONFIG_FILTRO, pend, ig, agora=AGORA) == [] and ig.mensagens == []


def test_se_a_api_nao_sabe_dizer_vale_a_palavra_da_pessoa_e_manda_o_link():
    ig, pend = InstagramComConversa([], _resposta_da_pessoa("2026-10-17T16:00:00+0000"), segue=None), _pendente()
    feitos = liberar_pendentes(CONFIG_FILTRO, pend, ig, agora=AGORA)
    assert ig.mensagens == [("u1", "link do kit")] and pend == {} and feitos[0]["verificado"] is False


def test_pendente_legado_que_ja_levou_o_aviso_e_liberado_dentro_da_janela_de_24h():
    ig = InstagramComConversa([], _resposta_da_pessoa("2026-10-17T16:00:00+0000"), segue=None)
    pend = _pendente(erros=1, tratada_ate="2026-10-17T16:00:00+0000")
    liberar_pendentes(CONFIG_FILTRO, pend, ig, agora=AGORA)
    assert ig.mensagens == [("u1", "link do kit")] and pend == {}


def test_pendente_legado_fora_da_janela_de_24h_nao_recebe_mensagem():
    ig = InstagramComConversa([], _resposta_da_pessoa("2026-10-15T16:00:00+0000"), segue=None)
    pend = _pendente(erros=1, tratada_ate="2026-10-15T16:00:00+0000")
    liberar_pendentes(CONFIG_FILTRO, pend, ig, agora=AGORA)
    assert ig.mensagens == [] and _chave("u1") in pend


def test_pendente_velho_demais_e_descartado():
    ig, pend = InstagramComConversa([], _resposta_da_pessoa()), _pendente(desde="2026-10-01T15:00:00+00:00")
    liberar_pendentes(CONFIG_FILTRO, pend, ig, agora=AGORA)
    assert pend == {} and ig.mensagens == []
