"""Gera a trilha original do molde pixel (arpejo chiptune em lá menor, 90 s, sem direito autoral de terceiros).

Uso: python ferramentas_gerar_trilha.py  -> src/estudio_instagram/modelos/assets/musica/trilha-pixel.mp3
Só stdlib + ffmpeg. Música sintetizada aqui: não vem de nenhum arquivo ou banco de música.
"""
import math
import struct
import subprocess
import wave
from pathlib import Path

TAXA = 22050
DURACAO = 90
SAIDA = Path("src/estudio_instagram/modelos/assets/musica")
BPM = 112
PASSO = 60 / BPM / 2  # colcheia
ACORDES = [  # (baixo, [arpejo])
    (110.0, [220.0, 261.63, 329.63]),   # Am
    (87.31, [174.61, 220.0, 261.63]),   # F
    (130.81, [261.63, 329.63, 392.0]),  # C
    (98.0, [196.0, 246.94, 293.66]),    # G
]
PADRAO = [0, 1, 2, 1, 2, 1, 0, 1]


def triangulo(fase: float) -> float:
    return 2 * abs(2 * (fase % 1) - 1) - 1


def principal():
    amostras = []
    total = TAXA * DURACAO
    passos_por_acorde = 8
    for i in range(total):
        t = i / TAXA
        passo = int(t / PASSO)
        acorde = ACORDES[(passo // passos_por_acorde) % len(ACORDES)]
        nota = acorde[1][PADRAO[passo % len(PADRAO)]]
        dentro = (t - passo * PASSO) / PASSO
        env = math.exp(-3.2 * dentro)  # pluck curto
        arpejo = 0.55 * env * triangulo(nota * t)
        baixo_dentro = (t % (PASSO * passos_por_acorde)) / (PASSO * passos_por_acorde)
        baixo = 0.35 * (1 - 0.4 * baixo_dentro) * triangulo(acorde[0] * t)
        amostras.append(max(-1.0, min(1.0, arpejo + baixo)))
    SAIDA.mkdir(parents=True, exist_ok=True)
    wav = SAIDA / "trilha-pixel.wav"
    with wave.open(str(wav), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(TAXA)
        f.writeframes(b"".join(struct.pack("<h", int(a * 12000)) for a in amostras))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-af", "afade=t=in:d=1,afade=t=out:st=88:d=2",
                    "-b:a", "96k", str(SAIDA / "trilha-pixel.mp3")], check=True)
    wav.unlink()


if __name__ == "__main__":
    principal()
