"""Resposta automática só para pergunta de verdade, com limite diário e texto conferido."""

from datetime import datetime, timezone

from src.estudio_instagram import perguntas

AGORA = datetime(2026, 11, 4, 22, 0, tzinfo=timezone.utc)


def test_so_pergunta_de_verdade():
    assert perguntas.eh_pergunta("E os dados bancários ?")
    assert perguntas.eh_pergunta("como instala isso no windows")
    assert not perguntas.eh_pergunta("ANDROID")
    assert not perguntas.eh_pergunta("muito bom")
    assert not perguntas.eh_pergunta("@fulano olha isso?")


def test_resposta_sem_link_marcacao_emoji_ou_texto_longo():
    assert perguntas.resposta_segura("Roda em Android a partir da versão 11.")
    for ruim in ("veja https://x.com", "fala com @fulano", "boa \U0001F600", "#ia", "a" * 400, ""):
        assert not perguntas.resposta_segura(ruim)


class IgFalso:
    def __init__(self):
        self.publicas = []

    def _ler(self, *_a, **_k):
        return {"caption": "legenda"}

    def responder_publico(self, cid, texto):
        self.publicas.append((cid, texto))


def _comentario(i, texto="Funciona no iPhone?", **extra):
    return {"id": str(i), "text": texto, "timestamp": "2026-11-04T21:00:00+0000", "midia_id": "m", "from": {"username": "x"}, **extra}


def test_respeita_limite_ja_respondido_e_o_proprio_perfil():
    ig = IgFalso()
    registro = {str(k): {"em": "2026-11-04T10:00:00"} for k in range(100, 100 + perguntas.LIMITE_POR_DIA - 1)}
    comentarios = [_comentario(1, tem_resposta=True), _comentario(2, **{"from": {"username": "ursulino.ia"}}),
                   _comentario(3), _comentario(4)]
    feitos = perguntas.responder_comentarios(ig, comentarios, registro, AGORA, set(),
                                             llm=lambda *_: {"responder": True, "texto": "Só Android."}, leitor=lambda r: "")
    assert [f["comentario_id"] for f in feitos] == ["3"]  # 1 já tem resposta, 2 é do perfil, 4 passou do limite
    assert ig.publicas == [("3", "Só Android.")]


def test_quando_o_llm_nao_sabe_nao_responde():
    ig = IgFalso()
    feitos = perguntas.responder_comentarios(ig, [_comentario(5)], {}, AGORA, set(),
                                             llm=lambda *_: {"responder": False}, leitor=lambda r: "")
    assert feitos == [] and ig.publicas == []
