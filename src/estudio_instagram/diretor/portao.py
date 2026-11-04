"""Portão de qualidade: nada vai para a fila sem passar por aqui.

1. Folha de contato com um quadro no meio de cada cena (o que o olho vê em cada frase).
2. QA automático do MP4: duração, quadro congelado longo, quadro preto, volume da voz.
3. Crítico com visão (Gemini) que olha a nossa folha ao lado de uma folha de referência do estudo e dá nota de
   0 a 10 por área, com correções. Passa com média >= 7 e nenhuma área < 5.

Narração não é prova: o crítico vê os quadros de verdade, não a descrição do vídeo.
"""

import base64
import json
import re
import subprocess
import urllib.request
from pathlib import Path

from ..llm import MODELOS_GEMINI, _chaves_gemini, extrair_json
from .. import segredos

RAIZ = Path(__file__).resolve().parents[3]
REFERENCIAS = RAIZ / "segredos" / "estudos" / "2026-11-03" / "folhas"  # estudo no repositório privado
REF_PADRAO = ["_aighostlab__DfS3jZQpbkb.jpg", "_aighostlab__DfPY4rbJaL-.jpg", "clubedasskills__DfNvOR7CRAh.jpg"]
# o que é próprio de cada formato (o juiz não deve punir isso como falta de variedade)
FORMATOS = {"esquete": "esquete cômica em diálogo entre dois personagens. Cenário fixo e enquadramento parecido são do formato "
                       "(como numa sitcom): julgue variedade pela atuação, expressões, objetos e gags que mudam a cada fala, e o "
                       "gancho pela situação/conflito da 1ª fala."}
AREAS = ["gancho_visual", "personagem_atua", "variedade_de_cena", "legibilidade", "acabamento", "parece_template"]

CRITICO = segredos.texto("critico")  # texto no repositório privado (ver segredos.py)


def _ffprobe_duracao(mp4: Path) -> float:
    s = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True).stdout.strip()
    return float(s or 0)


def _miolo_vazio(mp4: Path, dur: float, amostras: int = 6) -> list[str]:
    """Tempos em que o miolo da tela (onde fica o 3D) é quase uma cor só: sinal de WebGL que não desenhou."""
    import numpy as np
    vazios = []
    for k in range(amostras):
        t = dur * (k + 0.5) / amostras
        bruto = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1",
                                "-vf", "crop=1080:600:0:500,scale=108:60,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
        if bruto and np.frombuffer(bruto, dtype=np.uint8).std() < 4:
            vazios.append(f"{t:.1f}s")
    return vazios if len(vazios) >= amostras // 2 else []


def qa(mp4: Path, duracao_esperada: float) -> dict:
    """Checagens objetivas do arquivo final."""
    dur = _ffprobe_duracao(mp4)
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", str(mp4), "-vf", "freezedetect=n=0.002:d=1.5,blackdetect=d=0.3:pix_th=0.05",
                          "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    congelados = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", log)]
    pretos = re.findall(r"black_start:([\d.]+)", log)
    media = re.search(r"mean_volume: (-?[\d.]+) dB", log)
    vol = float(media.group(1)) if media else -99
    problemas = []
    if abs(dur - duracao_esperada) > 0.6:
        problemas.append(f"duração {dur:.1f}s diferente da esperada {duracao_esperada:.1f}s")
    if congelados:
        problemas.append(f"{len(congelados)} trecho(s) congelado(s) > 1,5 s (maior {max(congelados):.1f}s)")
    if pretos:
        problemas.append(f"quadro preto em {', '.join(pretos[:3])}s")
    if vol < -32:
        problemas.append(f"áudio baixo demais (média {vol} dB)")
    vazios = _miolo_vazio(mp4, dur)
    if vazios:
        problemas.append(f"miolo da tela vazio (3D não desenhou?) em {vazios}")
    return {"duracao": round(dur, 2), "congelados": congelados, "pretos": pretos, "volume_medio_db": vol, "problemas": problemas, "ok": not problemas}


def folha_de_cenas(mp4: Path, tempos: list[float], destino: Path, largura: int = 270) -> Path:
    """Um quadro por tempo, lado a lado (grade de até 4 colunas)."""
    tmp = destino.parent / "_quadros"
    tmp.mkdir(exist_ok=True)
    arqs = []
    for k, t in enumerate(tempos):
        a = tmp / f"q{k:02d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf", f"scale={largura}:-1", str(a)], check=True)
        arqs.append(a)
    cols = min(4, len(arqs))
    linhas = (len(arqs) + cols - 1) // cols
    entradas = sum([["-i", str(a)] for a in arqs], [])
    filtro = "".join(f"[{k}:v]" for k in range(len(arqs))) + f"xstack=inputs={len(arqs)}:layout=" + "|".join(
        f"{(k % cols) * largura}_{(k // cols) * int(largura * 16 / 9)}" for k in range(len(arqs))) + ":fill=black"
    if len(arqs) == 1:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(arqs[0]), str(destino)], check=True)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", filtro, "-frames:v", "1", str(destino)], check=True)
    for a in arqs:
        a.unlink()
    tmp.rmdir()
    return destino


def _imagem(path: Path) -> dict:
    return {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(Path(path).read_bytes()).decode()}}


def criticar(folha: Path, falas: list[str], referencia: Path | None = None, formato: str | None = None) -> dict:
    """Crítico com visão. Sem referência por padrão: comparar com uma folha fixa (3D do @_aighostlab) enviesava o juiz
    a favor desse estilo. Calibração de 2026-11-04: os 3 vídeos que o Davi aprovou (esquete, pixel, dossiê) levavam
    3 a 4,8, abaixo do palco 3D (5,0) que ele achou mediano."""
    texto = CRITICO.replace("__FALAS__", "\n".join(f"{i + 1}. {f}" for i, f in enumerate(falas)))
    if formato in FORMATOS:
        texto += "\n\nFORMATO DESTE VÍDEO: " + FORMATOS[formato]
    partes = [{"text": texto}, _imagem(folha)] + ([_imagem(referencia)] if referencia else [])
    ultimo = None
    for chave in _chaves_gemini():
        for modelo in MODELOS_GEMINI:
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={chave}",
                    data=json.dumps({"contents": [{"role": "user", "parts": partes}],
                                     "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}).encode(),
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    resp = json.load(r)
                return extrair_json(resp["candidates"][0]["content"]["parts"][0]["text"])
            except Exception as erro:
                ultimo = erro
    return {"erro": f"crítico indisponível: {ultimo}"}


def julgar(critica: dict, qa_res: dict) -> dict:
    notas = critica.get("notas") or {}
    valores = [float(notas[a]) for a in AREAS if isinstance(notas.get(a), (int, float))]
    media = round(sum(valores) / len(valores), 2) if valores else None
    aprovado = qa_res["ok"] and media is not None and media >= 7 and min(valores) >= 5
    # 3 níveis (calibração de 2026-11-04 contra o olho do Davi): verde vai pra fila; amarelo vai com aviso para ele
    # revisar; vermelho (falha técnica ou nota < 5) não vai. O juiz é conselheiro: a palavra final é do Davi.
    nivel = "vermelho" if not qa_res["ok"] or media is None or media < 5 else ("verde" if aprovado else "amarelo")
    return {"media": media, "aprovado": aprovado, "nivel": nivel, "qa": qa_res, "critica": critica}


def avaliar(mp4: Path, info_voz: dict, pasta: Path) -> dict:
    falas = info_voz["falas"]
    ini = [0.0 if i == 0 else f["t"] - 0.12 for i, f in enumerate(falas)]
    fins = ini[1:] + [info_voz["duracao"]]
    meios = [a + (b - a) * (0.65 if i == 0 else 0.55) for i, (a, b) in enumerate(zip(ini, fins))]
    folha = folha_de_cenas(mp4, meios, pasta / "folha_cenas.jpg")
    q = qa(mp4, info_voz["duracao"])
    critica = criticar(folha, [f["texto"] for f in falas])
    res = julgar(critica, q)
    (pasta / "portao.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res
