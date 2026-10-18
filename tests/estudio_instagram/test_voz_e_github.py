import base64
import io
import json

import pytest

from src.estudio_instagram import github_dados, voz
from src.estudio_instagram.sincronia import PalavraNoTempo


class RespostaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class AbridorFalso:
    """Dublê de urllib.request.urlopen: registra os pedidos e devolve uma resposta pronta."""

    def __init__(self, corpo: bytes):
        self.corpo = corpo
        self.pedidos = []

    def __call__(self, pedido, timeout=None):
        self.pedidos.append(pedido)
        return RespostaFalsa(self.corpo)


RESPOSTA_ELEVENLABS = json.dumps({
    "audio_base64": base64.b64encode(b"mp3-falso").decode(),
    "alignment": {"characters": list("oi tu"), "character_start_times_seconds": [0.0, 0.1, 0.2, 0.3, 0.4]},
}).encode()


@pytest.fixture(autouse=True)
def sem_ffmpeg(monkeypatch):
    monkeypatch.setattr(voz, "mp3_para_pcm", lambda mp3: b"\x00\x00" * voz.TAXA_AMOSTRA)


def test_elevenlabs_pede_uma_vez_e_depois_usa_cache(tmp_path):
    abrir = AbridorFalso(RESPOSTA_ELEVENLABS)
    provedor = voz.ElevenLabs("VOZ1", "modelo-x", tmp_path, chave="segredo", abrir=abrir)

    primeira = provedor.sintetizar("oi tu")
    segunda = provedor.sintetizar("oi tu")

    assert len(abrir.pedidos) == 1
    assert primeira.palavras == segunda.palavras == [PalavraNoTempo(0.0, "oi"), PalavraNoTempo(0.3, "tu")]
    assert primeira.duracao() == pytest.approx(1.0)


def test_elevenlabs_manda_voz_modelo_e_chave_certos(tmp_path):
    abrir = AbridorFalso(RESPOSTA_ELEVENLABS)
    voz.ElevenLabs("VOZ1", "modelo-x", tmp_path, chave="segredo", abrir=abrir).sintetizar("oi tu")
    pedido = abrir.pedidos[0]
    assert pedido.full_url.endswith("/text-to-speech/VOZ1/with-timestamps")
    assert pedido.get_header("Xi-api-key") == "segredo"
    assert json.loads(pedido.data) == {"text": "oi tu", "model_id": "modelo-x", "language_code": "pt"}


def test_elevenlabs_sem_chave_falha_antes_de_chamar_a_api(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    abrir = AbridorFalso(RESPOSTA_ELEVENLABS)
    with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY"):
        voz.ElevenLabs("VOZ1", "m", tmp_path, abrir=abrir).sintetizar("oi")
    assert abrir.pedidos == []


@pytest.mark.parametrize("licenca, esperado", [
    ({"spdx_id": "MIT"}, "MIT"),
    ({"spdx_id": "NOASSERTION"}, "licença própria"),
    (None, "sem licença"),
])
def test_github_buscar_traduz_licenca(licenca, esperado):
    corpo = json.dumps({"full_name": "a/b", "stargazers_count": 42, "license": licenca,
                        "description": None, "html_url": "https://github.com/a/b"}).encode()
    dados = github_dados.buscar("a/b", abrir=AbridorFalso(corpo))
    assert (dados.repo, dados.estrelas, dados.licenca, dados.descricao) == ("a/b", 42, esperado, "")


def test_github_baixar_cartao_grava_imagem(tmp_path):
    destino = github_dados.baixar_cartao("a/b", tmp_path / "x" / "a_b.png", abrir=AbridorFalso(b"PNG"))
    assert destino.read_bytes() == b"PNG"


def test_com_reserva_usa_a_principal_quando_funciona():
    from src.estudio_instagram.voz import ComReserva, Narracao

    class Fixa:
        def __init__(self, nome): self.nome, self.chamadas = nome, []
        def sintetizar(self, t):
            self.chamadas.append(t); return Narracao(self.nome.encode(), [])

    p, r = Fixa("p"), Fixa("r")
    voz = ComReserva(p, r); voz.preparar(["a", "b"])
    assert voz.sintetizar("a").audio_pcm == b"p" and r.chamadas == []


def test_com_reserva_troca_o_video_inteiro_se_a_cota_acaba_no_meio():
    from src.estudio_instagram.voz import ComReserva, Narracao

    class AcabaNaSegunda:
        n = 0
        def sintetizar(self, t):
            self.n += 1
            if self.n == 2: raise RuntimeError("quota_exceeded")
            return Narracao(b"principal", [])

    class Reserva:
        def sintetizar(self, t): return Narracao(b"reserva", [])

    voz = ComReserva(AcabaNaSegunda(), Reserva()); voz.preparar(["a", "b", "c"])
    assert [voz.sintetizar(t).audio_pcm for t in "abc"] == [b"reserva"] * 3
