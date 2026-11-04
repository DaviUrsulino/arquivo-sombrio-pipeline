"""Narração frase a frase com tempo por palavra, e mixagem dos efeitos sonoros nos eventos da timeline.

Cada frase é sintetizada separada, as pontas de silêncio são cortadas e as frases são emendadas com uma pausa
curta. Assim o tempo de cada frase (e de cada palavra dentro dela) é conhecido com precisão, e o motor visual
pode trocar de cena exatamente quando a frase começa.

    python -m src.estudio_instagram.diretor.narracao frases.json pasta_saida/
    (frases.json = ["frase 1", "frase 2", ...]; grava voz.wav e falas.json; 3º argumento opcional = nome da voz)
"""

import json
import subprocess
import sys
import wave
from pathlib import Path

from ..voz import TAXA_AMOSTRA, aplicar_pronuncia

RAIZ = Path(__file__).resolve().parents[3]
SFX = Path(__file__).resolve().parents[1] / "modelos" / "assets" / "sfx"
PAUSA_S, INICIO_S, FIM_S = 0.18, 0.25, 1.4


def voz_padrao(nome: str = "Orus"):
    from ..voz import ComReserva, EdgeTTS, GeminiTTS
    return ComReserva(GeminiTTS(nome, RAIZ / "cache_voz"), EdgeTTS())


def narrar_frases(frases: list[str], voz, destino: Path) -> dict:
    """Grava `destino` (wav mono) e devolve {falas: [{texto, t, d, palavras: [{p, t}]}], duracao}."""
    import numpy as np
    textos = [aplicar_pronuncia(f)[0] for f in frases]
    if hasattr(voz, "preparar"):
        voz.preparar(textos)
    falas, trechos, t = [], [], INICIO_S
    for original, texto in zip(frases, textos):
        narr = voz.sintetizar(texto)
        pcm = np.frombuffer(narr.audio_pcm, dtype=np.int16).astype(np.float32) / 32768
        nz = np.flatnonzero(np.abs(pcm) > 0.01)
        corte = max(0, nz[0] - 240) if len(nz) else 0
        pcm = pcm[corte: nz[-1] + 480] if len(nz) else pcm
        d = len(pcm) / TAXA_AMOSTRA
        palavras_orig = original.split()
        tempos = [max(0.0, p.t - corte / TAXA_AMOSTRA) for p in narr.palavras]
        if len(tempos) != len(palavras_orig):  # o alinhador pode juntar/separar palavras: distribui pelo tempo
            tempos = [d * k / max(1, len(palavras_orig)) for k in range(len(palavras_orig))]
        falas.append({"texto": original, "t": round(t, 3), "d": round(d, 3),
                      "palavras": [{"p": p, "t": round(t + min(tt, d), 3)} for p, tt in zip(palavras_orig, tempos)]})
        trechos.append((t, pcm))
        t += d + PAUSA_S
    duracao = t - PAUSA_S + FIM_S
    mix = np.zeros(int(duracao * TAXA_AMOSTRA), dtype=np.float32)
    for ini, pcm in trechos:
        a = int(ini * TAXA_AMOSTRA)
        mix[a:a + len(pcm)] += pcm
    _gravar(destino, mix)
    return {"falas": falas, "duracao": round(duracao, 3)}


def _gravar(destino: Path, mix):
    import numpy as np
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(TAXA_AMOSTRA)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())


def _ler_audio(arquivo: Path):
    import numpy as np
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arquivo), "-f", "f32le", "-ac", "1", "-ar", str(TAXA_AMOSTRA), "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(bruto, dtype=np.float32)


def mixar(voz_wav: Path, eventos: list[dict], destino: Path, trilha: Path | None = None, volume_trilha: float = 0.10):
    """Soma efeitos sonoros (eventos = [{t, som, vol}]) e uma trilha baixinha na voz, com a voz por cima.

    O efeito entra 1 quadro depois do evento visual (a luz chega antes do som). A trilha abaixa sob a voz.
    """
    import numpy as np
    voz = _ler_audio(voz_wav)
    mix = voz.copy()
    cache = {}
    for e in eventos:
        nome = e["som"]
        if nome not in cache:
            arq = SFX / f"{nome}.ogg"
            if not arq.exists():
                continue
            cache[nome] = _ler_audio(arq)
        s = cache[nome] * float(e.get("vol", 0.35))
        a = int((e["t"] + 1 / 30) * TAXA_AMOSTRA)
        if a >= len(mix):
            continue
        b = min(len(mix), a + len(s))
        mix[a:b] += s[: b - a]
    if trilha and Path(trilha).exists():
        tr = _ler_audio(Path(trilha))
        if len(tr):
            tr = np.tile(tr, int(np.ceil(len(mix) / len(tr))))[: len(mix)]
            env = np.abs(voz)
            janela = int(0.25 * TAXA_AMOSTRA)
            env = np.convolve(env, np.ones(janela) / janela, mode="same")
            duck = np.where(env > 0.02, 0.45, 1.0)  # trilha abaixa enquanto tem voz
            mix += tr * volume_trilha * duck
    pico = np.max(np.abs(mix)) or 1
    if pico > 0.95:
        mix *= 0.95 / pico
    _gravar(destino, mix)


def main():
    frases = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    pasta = Path(sys.argv[2])
    pasta.mkdir(parents=True, exist_ok=True)
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    nome_voz = sys.argv[3] if len(sys.argv) > 3 else "Orus"  # vozes Gemini: Orus, Puck, Kore, Charon, Fenrir, Aoede...
    info = narrar_frases(frases, voz_padrao(nome_voz), pasta / "voz.wav")
    (pasta / "falas.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"voz.wav e falas.json em {pasta} ({info['duracao']} s)")


if __name__ == "__main__":
    main()
