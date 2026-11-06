import io
import json

import pytest

from src.estudio_instagram.graph_api import INTERVALO_STATUS_S, TENTATIVAS_STATUS, InstagramGraph


class RespostaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class AbridorFalso:
    """Dublê de urlopen: devolve a próxima resposta da fila e registra cada pedido feito."""

    def __init__(self, respostas: list[dict]):
        self.respostas = list(respostas)
        self.pedidos = []

    def __call__(self, pedido, timeout=None):
        self.pedidos.append(pedido)
        return RespostaFalsa(json.dumps(self.respostas.pop(0)).encode())


def test_reels_cria_espera_ficar_pronto_e_publica():
    abrir = AbridorFalso([
        {"id": "creation-1"},
        {"status_code": "IN_PROGRESS"},
        {"status_code": "FINISHED"},
        {"id": "media-1"},
    ])
    esperas = []
    ig = InstagramGraph("token-x", "user-9", abrir=abrir, esperar=esperas.append)

    resultado = ig.publicar_reels("https://cdn/video.mp4", "legenda")

    assert resultado.media_id == "media-1"
    assert esperas == [INTERVALO_STATUS_S]
    caminhos = [p.full_url.split("?")[0] for p in abrir.pedidos]
    assert caminhos == [
        "https://graph.instagram.com/v22.0/user-9/media",
        "https://graph.instagram.com/v22.0/creation-1",
        "https://graph.instagram.com/v22.0/creation-1",
        "https://graph.instagram.com/v22.0/user-9/media_publish",
    ]


def test_reels_manda_video_url_e_legenda_no_corpo():
    abrir = AbridorFalso([{"id": "c1"}, {"status_code": "FINISHED"}, {"id": "m1"}])
    InstagramGraph("token-x", "user-9", abrir=abrir, esperar=lambda s: None).publicar_reels(
        "https://cdn/video.mp4", "legenda aqui"
    )
    corpo = abrir.pedidos[0].data.decode()
    assert "media_type=REELS" in corpo
    assert "video_url=https%3A%2F%2Fcdn%2Fvideo.mp4" in corpo
    assert "caption=legenda+aqui" in corpo
    assert "access_token=token-x" in corpo


def test_reels_estoura_tentativas_se_nunca_terminar():
    respostas = [{"id": "c1"}] + [{"status_code": "IN_PROGRESS"}] * (TENTATIVAS_STATUS + 5)
    abrir = AbridorFalso(respostas)
    ig = InstagramGraph("token", "user", abrir=abrir, esperar=lambda s: None)
    with pytest.raises(RuntimeError, match="não ficou pronta"):
        ig.publicar_reels("https://cdn/v.mp4", "x")


def test_reels_propaga_erro_se_instagram_recusar():
    abrir = AbridorFalso([{"id": "c1"}, {"status_code": "ERROR"}])
    ig = InstagramGraph("token", "user", abrir=abrir, esperar=lambda s: None)
    with pytest.raises(RuntimeError, match="ERROR"):
        ig.publicar_reels("https://cdn/v.mp4", "x")


def test_carrossel_cria_um_filho_por_imagem_e_publica():
    abrir = AbridorFalso([
        {"id": "child-1"}, {"id": "child-2"}, {"id": "child-3"},
        {"id": "parent-1"}, {"status_code": "FINISHED"}, {"id": "media-2"},
    ])
    ig = InstagramGraph("token", "user-9", abrir=abrir, esperar=lambda s: None)

    resultado = ig.publicar_carrossel(
        ["https://cdn/1.png", "https://cdn/2.png", "https://cdn/3.png"], "legenda"
    )

    assert resultado.media_id == "media-2"
    assert "children=child-1%2Cchild-2%2Cchild-3" in abrir.pedidos[3].data.decode()


@pytest.mark.parametrize("n", [0, 1, 11])
def test_carrossel_recusa_fora_do_limite_do_instagram(n):
    ig = InstagramGraph("token", "user", abrir=AbridorFalso([]), esperar=lambda s: None)
    with pytest.raises(ValueError, match="2 a 10"):
        ig.publicar_carrossel([f"https://cdn/{i}.png" for i in range(n)], "legenda")


def test_trial_reel_manda_trial_params_so_quando_pedido():
    import json
    from src.estudio_instagram import graph_api
    enviados = []
    ig = graph_api.InstagramGraph("tok", "123")
    ig._pedir = lambda caminho, corpo: enviados.append((caminho, corpo)) or {"id": "c1"}
    ig._esperar_pronto = lambda _id: None
    ig.publicar_reels("http://v", "leg", teste=True)
    ig.publicar_reels("http://v", "leg")
    assert json.loads(enviados[0][1]["trial_params"]) == {"graduation_strategy": "SS_PERFORMANCE"}
    assert "trial_params" not in enviados[2][1]


def test_reels_com_capa_manda_cover_url():
    abrir = AbridorFalso([{"id": "c1"}, {"status_code": "FINISHED"}, {"id": "m1"}])
    InstagramGraph("t", "u", abrir=abrir, esperar=lambda s: None).publicar_reels("https://cdn/v.mp4", "x", capa_url="https://cdn/c.jpg")
    assert "cover_url=https%3A%2F%2Fcdn%2Fc.jpg" in abrir.pedidos[0].data.decode()


def test_link_vai_num_cartao_com_botao_acessar_agora():
    abrir = AbridorFalso([{"id": "a"}, {"id": "b"}])
    InstagramGraph("t", "u", abrir=abrir).enviar_link("p1", "Oi! Aqui está o kit. Link: https://x.com/kit")
    primeira, cartao = (json.loads(p.data) for p in abrir.pedidos)
    assert primeira["message"] == {"text": "Oi! Aqui está o kit."}
    botao = cartao["message"]["attachment"]["payload"]["elements"][0]["buttons"][0]
    assert botao == {"type": "web_url", "url": "https://x.com/kit", "title": "Acessar agora"}


def test_pedido_de_follow_vai_com_botao_ja_sigo():
    abrir = AbridorFalso([{"id": "a"}])
    InstagramGraph("t", "u", abrir=abrir).responder_comentario("c1", "segue aí", ["Já sigo"])
    assert json.loads(abrir.pedidos[0].data)["message"]["quick_replies"][0]["title"] == "Já sigo"
