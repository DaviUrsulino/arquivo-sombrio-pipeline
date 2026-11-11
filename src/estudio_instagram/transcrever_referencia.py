"""Baixa um Reels de referência e devolve a transcrição + a folha de quadros, para estudar o ROTEIRO.

Davi, 11/11: "eu acho que agora é nos roteiros que a gente tá pecando. A animação se adapta, mas o roteiro não tá
da maneira palatável que a galera gosta de escutar."

Até aqui as referências eram medidas por views e olhadas por fora (capa, estilo, HUD). Faltava ler o que elas
FALAM, frase por frase, com o tempo de cada uma. É o que este módulo faz, sem Apify e sem API paga: yt-dlp baixa,
o ffmpeg tira o áudio e o Whisper local transcreve.

    python -m src.estudio_instagram.transcrever_referencia https://www.instagram.com/p/XXXX/

Precisa de `yt-dlp` e de um ambiente com `faster-whisper` (ver WHISPER_PY).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "referencias" / "transcricoes"
# O Whisper mora num ambiente à parte: é pesado e só serve para estudo, não entra no pipeline de produção.
WHISPER_PY = os.environ.get("WHISPER_PY", "/tmp/wenv/bin/python")
MODELO = os.environ.get("WHISPER_MODELO", "small")


def baixar(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["yt-dlp", "--no-playlist", "-q", "-o", str(destino.with_suffix(".%(ext)s")), url], check=True)
    mp4 = destino.with_suffix(".mp4")
    if not mp4.exists():
        raise SystemExit(f"yt-dlp não trouxe o vídeo de {url}")
    return mp4


def folha_de_quadros(mp4: Path, destino: Path, a_cada_s: int = 8, colunas: int = 5, linhas: int = 3) -> Path:
    """Um quadro a cada N segundos, montados numa imagem só: dá para ver a estrutura do vídeo de relance."""
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf",
                    f"fps=1/{a_cada_s},scale=320:-1,tile={colunas}x{linhas}", "-frames:v", "1", str(destino), "-y"],
                   check=True)
    return destino


def transcrever(mp4: Path) -> list[tuple[float, str]]:
    """[(segundo, frase)] falados no vídeo, pelo Whisper local."""
    wav = mp4.with_suffix(".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vn", "-ar", "16000", "-ac", "1", str(wav), "-y"],
                   check=True)
    codigo = (
        "from faster_whisper import WhisperModel\n"
        f"m = WhisperModel({MODELO!r}, device='cpu', compute_type='int8')\n"
        f"segs, _ = m.transcribe({str(wav)!r}, language='pt', vad_filter=True)\n"
        "for s in segs: print(f'{s.start:.1f}\\t{s.text.strip()}')\n"
    )
    r = subprocess.run([WHISPER_PY, "-c", codigo], capture_output=True, text=True, timeout=1800)
    if r.returncode:
        raise SystemExit(f"Whisper falhou: {r.stderr[-400:]}")
    falas = []
    for linha in r.stdout.splitlines():
        if "\t" in linha:
            t, texto = linha.split("\t", 1)
            falas.append((float(t), texto))
    return falas


def estudar(url: str, nome: str) -> Path:
    pasta = SAIDA / nome
    pasta.mkdir(parents=True, exist_ok=True)
    mp4 = baixar(url, pasta / nome)
    folha_de_quadros(mp4, pasta / "folha.png")
    falas = transcrever(mp4)
    texto = "\n".join(f"[{t:6.1f}] {f}" for t, f in falas)
    (pasta / "fala.txt").write_text(f"{url}\n\n{texto}\n", encoding="utf-8")
    mp4.unlink(missing_ok=True)          # o vídeo é de outra pessoa: fica só o estudo, não a cópia
    mp4.with_suffix(".wav").unlink(missing_ok=True)
    print(texto)
    return pasta


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url")
    p.add_argument("--nome", help="pasta do estudo (padrão: o código do post)")
    a = p.parse_args()
    nome = a.nome or a.url.rstrip("/").split("/")[-1].split("?")[0]
    print(f"estudo em {estudar(a.url, nome)}", file=sys.stderr)


if __name__ == "__main__":
    main()
