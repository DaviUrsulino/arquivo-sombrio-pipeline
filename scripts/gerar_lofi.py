"""Gera uma trilha lo-fi original (sem direito autoral de terceiros) do tamanho exato de um loop de vídeo.

Piano elétrico em acordes de sétima (Fmaj7, Em7, Dm7, Cmaj7), baixo, bumbo e caixa abafados, chiado de
vinil e filtro passa-baixa. Os 4 acordes cabem certinho na duração pedida, então a música também emenda
sem pulo quando o Reels recomeça.

    python3 scripts/gerar_lofi.py 7.458 saida.wav
"""

import sys
import wave

import numpy as np

TAXA = 44100
ACORDES = [  # notas em Hz: baixo + acorde
    (87.31, [174.61, 220.00, 261.63, 329.63]),   # Fmaj7
    (82.41, [164.81, 196.00, 246.94, 293.66]),   # Em7
    (73.42, [146.83, 174.61, 220.00, 261.63]),   # Dm7
    (65.41, [130.81, 164.81, 196.00, 246.94]),   # Cmaj7
]


def epiano(freq, n, t):
    env = np.exp(-t * 1.6)
    onda = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 4) + 0.12 * np.sin(2 * np.pi * freq * 3 * t) * np.exp(-t * 7)
    vibrato = 1 + 0.004 * np.sin(2 * np.pi * 5 * t)
    return onda * env * vibrato


def gerar(duracao: float) -> np.ndarray:
    n = int(TAXA * duracao)
    mix = np.zeros(n)
    por_acorde = n // 4
    rng = np.random.default_rng(7)
    for k, (baixo, notas) in enumerate(ACORDES):
        ini = k * por_acorde
        t = np.arange(n - ini) / TAXA
        for j, f in enumerate(notas):  # acorde levemente "arrastado", como dedo humano
            atraso = int(TAXA * 0.025 * j)
            tt = t[: max(0, len(t) - atraso)]
            mix[ini + atraso: ini + atraso + len(tt)] += 0.18 * epiano(f, len(tt), tt) * (tt < duracao / 4 + 0.6)
        tb = t[:por_acorde]
        mix[ini: ini + por_acorde] += 0.28 * np.sin(2 * np.pi * baixo * tb) * np.exp(-tb * 0.8)
    batida = duracao / 8  # 2 tempos por acorde
    for b in range(8):
        i = int(b * batida * TAXA)
        tk = np.arange(int(0.25 * TAXA)) / TAXA
        if b % 2 == 0:  # bumbo abafado
            kick = 0.55 * np.sin(2 * np.pi * (55 + 60 * np.exp(-tk * 30)) * tk) * np.exp(-tk * 12)
        else:  # caixa: ruído curto filtrado
            kick = 0.12 * rng.standard_normal(len(tk)) * np.exp(-tk * 25)
        fim = min(n, i + len(tk))
        mix[i:fim] += kick[: fim - i]
    mix += 0.012 * rng.standard_normal(n) * (rng.random(n) > 0.9993) * 8  # estalos de vinil
    mix += 0.004 * rng.standard_normal(n)  # chiado
    # passa-baixa simples (média móvel) pra soar "lo-fi"
    janela = 9
    mix = np.convolve(mix, np.ones(janela) / janela, mode="same")
    # emenda: os últimos 30 ms se fundem no começo
    m = int(0.03 * TAXA)
    mix[:m] = mix[:m] * np.linspace(0, 1, m) + mix[-m:] * np.linspace(1, 0, m)
    return mix / max(1e-9, np.abs(mix).max()) * 0.7


def main():
    duracao, saida = float(sys.argv[1]), sys.argv[2]
    pcm = (gerar(duracao) * 32767).astype(np.int16)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(pcm.tobytes())
    print(f"trilha de {duracao:.2f} s em {saida}")


if __name__ == "__main__":
    main()
