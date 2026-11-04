"""Monta a pasta HyperFrames de um vídeo do palco: modelo + roteiro (storyboard) + falas + áudio mixado.

Os tempos dos efeitos sonoros seguem as MESMAS regras do motor (assets/vendor/palco-motor.js): se mudar o tempo
de uma ação lá (ex.: o martelo bate em lt = 0,35 + 0,6k + 0,33), mude aqui também.
"""

import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from . import catalogo
from .narracao import mixar

RAIZ = Path(__file__).resolve().parents[3]
MODELOS = Path(__file__).resolve().parents[1] / "modelos"
ASSETS = MODELOS / "assets"


def inicios(falas: list[dict]) -> list[float]:
    return [0.0 if i == 0 else f["t"] - 0.12 for i, f in enumerate(falas)]


def eventos_sfx(cenas: list[dict], falas: list[dict], palavra: str) -> list[dict]:
    ini = inicios(falas)
    ev = []
    for i, c in enumerate(cenas):
        t0 = ini[i]
        if i > 0:
            if c.get("transicao") == "chicote":
                ev.append({"t": t0, "som": "whoosh", "vol": 0.45})
            elif c.get("transicao") == "voxel":
                ev.append({"t": t0, "som": "woosh2", "vol": 0.35})
                ev.append({"t": t0 + 0.05, "som": "pop", "vol": 0.35})
            else:
                ev.append({"t": t0, "som": "click", "vol": 0.25})
        if c.get("objeto"):
            ev.append({"t": t0 + 0.12, "som": "pop", "vol": 0.4})
        acao, obj = c.get("acao"), c.get("objeto")
        if acao == "martela":
            ev += [{"t": t0 + 0.35 + 0.6 * k + 0.33, "som": "baque", "vol": 0.5} for k in range(3)]
        if acao == "carimba":
            ev.append({"t": t0 + 0.58, "som": "impact", "vol": 0.55})
        if acao == "comemora":
            ev.append({"t": t0 + 0.15, "som": "ding", "vol": 0.4})
        if acao == "assusta":
            ev.append({"t": t0 + 0.05, "som": "baque", "vol": 0.3})
        if obj == "contador":
            ev += [{"t": t0 + 0.25 + 0.2 * k, "som": "tick", "vol": 0.25} for k in range(7)]
        if obj in ("cadeado", "presente"):
            ev.append({"t": t0 + 0.7, "som": "ding", "vol": 0.35})
        if obj == "lampada":
            ev.append({"t": t0 + 0.6, "som": "ding", "vol": 0.35})
        if obj == "foguete":
            ev.append({"t": t0 + 0.6, "som": "riser", "vol": 0.3})
        if c.get("hud_valor") is not None and i > 0:
            ev.append({"t": t0 + 0.15, "som": "tick", "vol": 0.3})
    fc = falas[-1]["t"]
    ev += [{"t": fc + 0.25 + 0.08 * k, "som": "click", "vol": 0.18} for k in range(len(palavra))]
    ev += [{"t": fc + 1.62, "som": "click", "vol": 0.35}, {"t": fc + 1.72, "som": "ding", "vol": 0.35}]
    return ev


def envelope_boca(wav: Path, fps: int = 30) -> list[float]:
    import numpy as np
    with wave.open(str(wav)) as w:
        taxa = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    passo = taxa // fps
    rms = [float(np.sqrt(np.mean(pcm[i:i + passo] ** 2))) for i in range(0, len(pcm), passo)]
    topo = max(rms) or 1
    return [round(min(1.0, v / topo * 1.6), 3) for v in rms]


def montar(plano: dict, info_voz: dict, voz_wav: Path, pasta: Path, modelo: str = "palco", trilha: bool = True) -> float:
    """Cria `pasta` pronta para `hyperframes render`. Devolve a duração."""
    if pasta.exists():
        shutil.rmtree(pasta)
    shutil.copytree(MODELOS / "identidades" / modelo, pasta)
    a = pasta / "assets"
    a.mkdir(exist_ok=True)
    for arq in ("three.min.js", "gsap.min.js", "palco-motor.js"):
        shutil.copy(ASSETS / "vendor" / arq, a / arq)
    for fonte in ("ArchivoBlack.ttf", "Montserrat.ttf", "Silkscreen-Bold.ttf"):
        shutil.copy(ASSETS / "fonts" / fonte, a / fonte)
    catalogo.gravar_js(a / "catalogo.js")
    duracao = info_voz["duracao"]
    shutil.copy(voz_wav, a / "voz.wav")
    esq = {"falas": info_voz["falas"], "duracao": duracao, "boca": envelope_boca(voz_wav), "fps": 30}
    (a / "falas.js").write_text("window.ESQ=" + json.dumps(esq, ensure_ascii=False) + ";", encoding="utf-8")
    (a / "roteiro.js").write_text("window.ROT=" + json.dumps(plano, ensure_ascii=False) + ";", encoding="utf-8")
    trilha_wav = None
    if trilha:
        trilha_wav = a / "trilha.wav"
        subprocess.run([sys.executable, str(RAIZ / "scripts" / "gerar_lofi.py"), f"{duracao:.2f}", str(trilha_wav)],
                       check=True, capture_output=True)
    eventos = eventos_sfx(plano["cenas"], info_voz["falas"], plano.get("palavra", "LINK"))
    mixar(a / "voz.wav", eventos, a / "audio.wav", trilha_wav, volume_trilha=0.16)
    html = (pasta / "index.html").read_text(encoding="utf-8").replace("__DURACAO__", f"{duracao:.2f}")
    (pasta / "index.html").write_text(html, encoding="utf-8")
    (pasta / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1), encoding="utf-8")
    return duracao
