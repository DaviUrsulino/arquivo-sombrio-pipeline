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


def test_pronuncia_troca_termo_por_uma_palavra_e_guarda_o_original():
    from src.estudio_instagram.voz import aplicar_pronuncia

    falado, originais = aplicar_pronuncia("Isso roda no GitHub, com Claude Code.")
    assert falado == "Isso roda no Guitrab, com Clód Cóude."
    assert originais == ["Isso", "roda", "no", "GitHub,", "com", "Claude", "Code."]
    assert len(falado.split()) == len(originais)


def _pcm_com_fala_e_pausas():
    """1 s de silêncio, 1 s de 'fala', 0,3 s de pausa, 1 s de 'fala', 1 s de silêncio (24 kHz, 16 bits)."""
    import math
    import struct

    def tom(seg):
        return b"".join(struct.pack("<h", int(8000 * math.sin(i / 8))) for i in range(int(24000 * seg)))

    def silencio(seg):
        return bytes(int(24000 * seg) * 2)

    return silencio(1.0) + tom(1.0) + silencio(0.3) + tom(1.0) + silencio(1.0)


def test_alinhamento_acha_a_fala_e_a_pausa_da_virgula():
    from src.estudio_instagram.alinhamento import alinhar, aparar

    pcm, tirado = aparar(_pcm_com_fala_e_pausas())
    assert 0.9 < tirado < 1.0 and len(pcm) / 2 / 24000 < 3.5  # cortou o silêncio das pontas
    palavras = alinhar("um dois três, quatro cinco seis", pcm)
    assert [p.palavra for p in palavras] == "um dois três, quatro cinco seis".split()
    assert all(a.t <= b.t for a, b in zip(palavras, palavras[1:]))
    assert palavras[3].t > 1.3  # "quatro" vem depois da pausa, na segunda metade


def test_gemini_tts_tenta_de_novo_quando_a_api_pede_calma():
    import base64
    import io
    import json as _json
    import urllib.error

    from src.estudio_instagram.voz import GeminiTTS

    pcm = _pcm_com_fala_e_pausas()
    resposta = _json.dumps({"candidates": [{"content": {"parts": [{"inlineData": {"data": base64.b64encode(pcm).decode()}}]}}]}).encode()
    chamadas, esperas = [], []

    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def abrir(pedido, timeout=None):
        chamadas.append(1)
        if len(chamadas) == 1:
            raise urllib.error.HTTPError("u", 429, "calma", {}, io.BytesIO(b"{}"))
        return Resp(resposta)

    voz = GeminiTTS("Orus", chave="x", abrir=abrir, esperar=esperas.append)
    narracao = voz.sintetizar("um dois três, quatro cinco seis")
    assert len(chamadas) == 2 and esperas == [12] and len(narracao.palavras) == 6


def test_gemini_tts_desiste_com_erro_claro_se_nao_for_limite():
    import io
    import urllib.error

    import pytest as _pytest

    from src.estudio_instagram.voz import GeminiTTS

    def abrir(pedido, timeout=None):
        raise urllib.error.HTTPError("u", 400, "ruim", {}, io.BytesIO(b'{"error":"chave"}'))

    with _pytest.raises(RuntimeError, match="Gemini TTS recusou"):
        GeminiTTS("Orus", chave="x", abrir=abrir, esperar=lambda s: None).sintetizar("oi")


def test_gemini_tts_tenta_de_novo_em_falha_de_rede_crua():
    import base64
    import io
    import json as _json
    import urllib.error

    from src.estudio_instagram.voz import GeminiTTS

    pcm = _pcm_com_fala_e_pausas()
    resposta = _json.dumps({"candidates": [{"content": {"parts": [{"inlineData": {"data": base64.b64encode(pcm).decode()}}]}}]}).encode()
    chamadas, esperas = [], []

    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def abrir(pedido, timeout=None):
        chamadas.append(1)
        if len(chamadas) == 1:
            raise urllib.error.URLError("falha de dns")
        return Resp(resposta)

    voz = GeminiTTS("Orus", chave="x", abrir=abrir, esperar=esperas.append)
    narracao = voz.sintetizar("um dois três, quatro cinco seis")
    assert len(chamadas) == 2 and esperas == [12] and len(narracao.palavras) == 6


def test_com_reserva_cai_pra_reserva_mesmo_quando_o_erro_nao_e_runtime_error():
    from src.estudio_instagram.voz import ComReserva, Narracao

    class FalhaDeRede:
        def sintetizar_varios(self, textos):
            raise ConnectionError("timeout")

    class Reserva:
        def sintetizar(self, t): return Narracao(b"reserva", [])

    voz = ComReserva(FalhaDeRede(), Reserva())
    voz.preparar(["a", "b"])
    assert voz.usando_reserva and voz.sintetizar("a").audio_pcm == b"reserva"


def test_cortar_em_cenas_divide_a_narracao_unica_na_pausa_entre_frases():
    from src.estudio_instagram.alinhamento import aparar, cortar_em_cenas

    pcm, _ = aparar(_pcm_com_fala_e_pausas())
    cenas = cortar_em_cenas(["um dois três.", "quatro cinco seis."], pcm)
    assert len(cenas) == 2
    (a1, p1), (a2, p2) = cenas
    assert [p.palavra for p in p1] == ["um", "dois", "três."] and [p.palavra for p in p2] == ["quatro", "cinco", "seis."]
    assert abs(len(a1) / 2 / 24000 - 1.15) < 0.25 and abs(len(a2) / 2 / 24000 - 1.15) < 0.35  # ~1 s de fala cada
    assert p2[0].t < 0.2  # a segunda cena começa colada na fatia dela


def test_com_reserva_usa_pedido_unico_quando_o_provedor_sabe():
    from src.estudio_instagram.voz import ComReserva, Narracao

    class EmLote:
        chamadas = 0
        def sintetizar_varios(self, textos):
            EmLote.chamadas += 1
            return {t: Narracao(b"x", []) for t in textos}
        def sintetizar(self, t): raise AssertionError("não devia chamar uma a uma")

    voz = ComReserva(EmLote(), EmLote())
    voz.preparar(["a", "b", "c"])
    assert EmLote.chamadas == 1 and voz.sintetizar("b").audio_pcm == b"x"
