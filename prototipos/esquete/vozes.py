"""Gera as vozes do esquete low-poly (Edge TTS) com a pronúncia brasileira dos termos de tecnologia.

Lê roteiro.json ([quem, texto] por fala), fala cada linha com a voz do personagem, emenda tudo em
assets/voz.wav e escreve assets/falas.js (tempos das falas + envelope da boca a 30 fps).

    python3 prototipos/esquete/vozes.py PASTA_DO_ESQUETE
"""

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.estudio_instagram.voz import aplicar_pronuncia  # noqa: E402

VOZES = {"dev": ("pt-BR-AntonioNeural", "+4%"), "robo": ("pt-BR-ThalitaMultilingualNeural", "+6%")}
TAXA, FPS, INICIO, PAUSA, FIM = 48000, 30, 0.4, 0.25, 1.2


def falar(texto: str, quem: str, saida: Path) -> np.ndarray:
    voz, ritmo = VOZES[quem]
    falado, _ = aplicar_pronuncia(texto)
    mp3 = saida.with_suffix(".mp3")
    subprocess.run(["edge-tts", "--voice", voz, f"--rate={ritmo}", "--text", falado, "--write-media", str(mp3)],
                   check=True, capture_output=True)
    # corta o silêncio do começo e do fim pra fala emendar no tempo certo
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    "-ar", str(TAXA), "-ac", "1", str(saida)], check=True)
    with wave.open(str(saida)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def main():
    pasta = Path(sys.argv[1])
    roteiro = json.loads((pasta / "roteiro.json").read_text(encoding="utf-8"))
    falas, trechos, t = [], [], INICIO
    for i, (quem, texto) in enumerate(roteiro):
        audio = falar(texto, quem, pasta / f"l{i}.wav")
        falas.append({"quem": quem, "texto": texto, "t": round(t, 3), "d": round(len(audio) / TAXA, 3)})
        trechos.append((t, audio))
        t += len(audio) / TAXA + PAUSA
    duracao = t - PAUSA + FIM
    mix = np.zeros(int(duracao * TAXA), dtype=np.float32)
    for ini, audio in trechos:
        a = int(ini * TAXA)
        mix[a:a + len(audio)] += audio
    with wave.open(str(pasta / "assets" / "voz.wav"), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(TAXA)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    passo = TAXA // FPS
    rms = [float(np.sqrt(np.mean(mix[i:i + passo] ** 2))) for i in range(0, len(mix), passo)]
    topo = max(rms) or 1
    boca = [round(min(1.0, r / topo * 1.6), 3) for r in rms]
    dados = {"falas": falas, "duracao": round(duracao, 3), "boca": boca, "fps": FPS}
    (pasta / "assets" / "falas.js").write_text("window.ESQ=" + json.dumps(dados, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(falas)} falas, {duracao:.2f} s")


if __name__ == "__main__":
    main()
