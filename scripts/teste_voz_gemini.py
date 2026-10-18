"""Gera a mesma frase em várias vozes masculinas do Gemini TTS, para escolher no ouvido.

Roda no GitHub (a chave GEMINI_API_KEY só existe lá). Saída: arquivos .wav em `vozes_gemini/`.
Usa só a biblioteca padrão.
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

CHAVE = os.environ.get("GEMINI_API_KEY", "").strip()
FRASE = ("Esse repositório do GitHub funciona com Claude Code, Codex, Cursor e Gemini CLI, e usa HTML e MCP. "
         "Já tem mais de sessenta mil estrelas, e é grátis.")
INSTRUCAO = "Fale em português do Brasil, de forma natural e animada, como uma pessoa contando uma descoberta para um amigo: "
VOZES = ["Puck", "Charon", "Fenrir", "Orus", "Iapetus", "Achird", "Zubenelgenubi", "Algenib"]
SAIDA = Path("vozes_gemini")


def requisitar(url: str, corpo: dict | None = None) -> dict:
    pedido = urllib.request.Request(
        url, data=json.dumps(corpo).encode() if corpo else None,
        headers={"Content-Type": "application/json", "x-goog-api-key": CHAVE}, method="POST" if corpo else "GET",
    )
    with urllib.request.urlopen(pedido, timeout=120) as resposta:
        return json.load(resposta)


def modelos_tts() -> list[str]:
    achados = []
    url = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=200"
    for m in requisitar(url).get("models", []):
        nome = m["name"].removeprefix("models/")
        if "tts" in nome and "generateContent" in m.get("supportedGenerationMethods", []):
            achados.append(nome)
    return achados


def sintetizar(modelo: str, voz: str) -> bytes:
    corpo = {
        "contents": [{"parts": [{"text": INSTRUCAO + FRASE}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}},
        },
    }
    resposta = requisitar(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent", corpo)
    return base64.b64decode(resposta["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])


def main():
    if not CHAVE:
        sys.exit("GEMINI_API_KEY não definida")
    SAIDA.mkdir(exist_ok=True)
    modelos = modelos_tts()
    print("modelos TTS disponíveis:", modelos)
    if not modelos:
        sys.exit("nenhum modelo TTS disponível para essa chave")
    modelo = modelos[0]
    feitos = 0
    for voz in VOZES:
        for tentativa in range(3):
            try:
                pcm = sintetizar(modelo, voz)
                with wave.open(str(SAIDA / f"{voz}.wav"), "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(24000)
                    w.writeframes(pcm)
                print(f"ok {voz} ({len(pcm) / 2 / 24000:.1f}s) com {modelo}")
                feitos += 1
                break
            except urllib.error.HTTPError as erro:
                corpo = erro.read().decode(errors="replace")[:200]
                print(f"{voz}: HTTP {erro.code} {corpo}")
                time.sleep(12 if erro.code == 429 else 3)
            except Exception as erro:
                print(f"{voz}: {str(erro)[:150]}")
                time.sleep(3)
        time.sleep(6)
    if not feitos:
        sys.exit("nenhuma voz foi gerada")


if __name__ == "__main__":
    main()
