import base64
import io
import json
import urllib.error

from src.estudio_instagram.voz import GeminiTTS


def test_passa_pro_proximo_modelo_quando_a_cota_do_dia_acaba():
    pedidos = []

    def abrir(req, timeout=0):
        pedidos.append(req.full_url)
        if "2.5-flash" in req.full_url:
            raise urllib.error.HTTPError(req.full_url, 429, "x", {}, io.BytesIO(b'{"message": "You exceeded your current quota"}'))
        audio = base64.b64encode(b"\x01\x00" * 10).decode()
        return io.BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"inlineData": {"data": audio}}]}}]}).encode())

    tts = GeminiTTS(chave="k", abrir=abrir, esperar=lambda s: None)
    assert tts._pedir_pcm("oi") == b"\x01\x00" * 10
    assert "2.5-flash" in pedidos[0] and "3.8-flash-tts" in pedidos[1] and len(pedidos) == 2
