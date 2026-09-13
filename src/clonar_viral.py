"""Primeira parte do fluxo de "clonar vídeo viral" (ver conversa 2026-09-12
com o Davi): baixar um vídeo de referência do TikTok e transcrever a
narração dele localmente (yt-dlp + Whisper, os dois já usados/instalados
neste projeto) -- zero custo e zero risco de conta banida.

As próximas etapas do fluxo completo (reescrever o roteiro, gerar as
imagens e a narração) dependem de automatizar Claude.ai, Google Flow e
ElevenLabs via RPA -- ficam de fora deste arquivo de propósito, porque
automatizar a INTERFACE dessas contas (em vez da API oficial) arrisca
banimento e precisa da extensão Claude in Chrome pra mapear os seletores
reais antes de codar (decisão 2026-09-12, ainda pendente).

Uso:
    python src/clonar_viral.py --url https://www.tiktok.com/@fulano/video/123
"""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from montar_video_local import _transcrever_palavras  # noqa: E402


def baixar_audio_tiktok(url: str, caminho_saida_audio: str):
    """Baixa só o áudio do vídeo do TikTok (yt-dlp, sem login/API/conta
    nenhuma -- por isso não carrega o mesmo risco de ban das próximas
    etapas do fluxo). `caminho_saida_audio` deve terminar em .mp3."""
    raiz, _ext = os.path.splitext(caminho_saida_audio)
    resultado = subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "mp3", "-o", f"{raiz}.%(ext)s", url],
        capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"yt-dlp falhou baixando {url}:\n{resultado.stderr}")


def transcrever_video_referencia(url: str, pasta_saida: str) -> str:
    """Baixa o áudio do vídeo de referência e transcreve localmente
    (Whisper, mesma função usada pra sincronizar o pivô) -- retorna o
    caminho do .txt com a transcrição corrida, pronta pra colar no
    Claude/ChatGPT reescrever (etapa seguinte, ainda manual até a
    automação RPA de Claude/Flow/ElevenLabs estar pronta)."""
    os.makedirs(pasta_saida, exist_ok=True)
    caminho_audio = os.path.join(pasta_saida, "audio_referencia.mp3")
    print(f"Baixando áudio de {url}...")
    baixar_audio_tiktok(url, caminho_audio)

    print("Transcrevendo (Whisper local)...")
    palavras = _transcrever_palavras(caminho_audio)
    texto = " ".join(p for _, _, p in palavras)

    caminho_txt = os.path.join(pasta_saida, "transcricao_referencia.txt")
    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.write(texto)

    print(f"Transcrição salva em {caminho_txt}")
    return caminho_txt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="link do vídeo do TikTok de referência")
    parser.add_argument("--saida", default="clonagem_tmp", help="pasta onde salvar áudio + transcrição")
    args = parser.parse_args()
    transcrever_video_referencia(args.url, args.saida)


if __name__ == "__main__":
    main()
