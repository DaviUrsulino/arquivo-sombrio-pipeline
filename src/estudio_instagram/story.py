"""Story automático do Robô Estagiário: avisa quem já segue que saiu vídeo novo.

Pega os primeiros segundos do Reels recém-publicado (o gancho), põe uma faixa "VÍDEO NOVO NO PERFIL" em cima e
o @ embaixo, e publica como Story. Quem vê o Story e não viu o Reels vai até o perfil: é o que transforma
visualização em seguidor fiel. Falha aqui nunca derruba o post (quem chama ignora o erro).
"""

import subprocess
from pathlib import Path

FONTE = Path(__file__).resolve().parent / "modelos" / "assets" / "fonts" / "ArchivoBlack.ttf"
DURACAO_S = 9
FAIXA = "VIDEO NOVO NO PERFIL"  # drawtext com acento depende da fonte; a Archivo Black tem, mas evita o risco


def preparar(reels: Path, saida: Path, duracao: float = DURACAO_S) -> Path:
    fonte = str(FONTE).replace(":", r"\:")
    filtro = (
        "scale=1080:1920,format=yuv420p,"
        "drawbox=x=0:y=40:w=iw:h=150:color=0xE8314F@0.95:t=fill,"
        f"drawtext=fontfile='{fonte}':text='{FAIXA}':fontsize=66:fontcolor=white:x=(w-text_w)/2:y=40+(150-text_h)/2,"
        "drawbox=x=0:y=1790:w=iw:h=110:color=black@0.7:t=fill,"
        f"drawtext=fontfile='{fonte}':text='@ursulino.ia':fontsize=56:fontcolor=white:x=(w-text_w)/2:y=1790+(110-text_h)/2,"
        f"fade=t=out:st={duracao - 0.5}:d=0.5"
    )
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(reels), "-t", str(duracao), "-vf", filtro,
                    "-af", f"afade=t=out:st={duracao - 0.5}:d=0.5", "-c:v", "libx264", "-b:v", "5M", "-r", "30",
                    "-c:a", "aac", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(saida)], check=True)
    return saida
