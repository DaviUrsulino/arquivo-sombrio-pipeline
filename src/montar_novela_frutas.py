"""Montagem do formato "novela de frutas" (2026-09-13): personagens
animados gerados manualmente no Google Flow (cada clipe já vem com o
diálogo do personagem embutido no áudio -- ao contrário do pivô do
ônibus, aqui NÃO tem narração externa pra sincronizar, então não precisa
de roteiro marcado [FOTO N] nem de Whisper pra decidir corte).

Este pipeline só cuida da EDIÇÃO final: concatenar as cenas prontas (na
ordem que quem gerou decidiu -- nunca reordena, mesmo princípio do pivô,
ver montar_video_local.py), legendar o diálogo e mixar uma trilha de
fundo baixinha por trás das falas.

A geração das cenas em si (roteiro/personagens no ChatGPT, imagem+vídeo
no Google Flow, tudo manual por enquanto -- ver decisão 2026-09-12 de
não automatizar via RPA sem antes avaliar risco de ban de conta) fica
FORA deste arquivo de propósito.

Uso:
    python src/montar_novela_frutas.py --cenas pasta_com_cena1.mp4_cena2.mp4... --saida video_final.mp4
"""

import argparse
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from montar_video_local import (  # noqa: E402
    ALTURA,
    LARGURA,
    _contar_frames_reais,
    _duracao_segundos,
    _rodar,
    _transcrever_palavras,
    concatenar_com_transicao,
    extrair_audio,
    gerar_ambiencia,
    gerar_legenda_ass,
    queimar_legenda,
)

# Trilha própria da novela de frutas -- NÃO reaproveita TRILHAS_POR_PLATAFORMA
# do resto do projeto (aquelas são do canal de terror). Bug real 2026-09-13:
# a 1ª versão deste arquivo importava TRILHAS_POR_PLATAFORMA por hábito e
# usava ela aqui, tocando a música do terror por engano na novela de frutas.
_PASTA_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
CAMINHO_TRILHA_FRUTINHA = os.path.join(_PASTA_ASSETS, "trilha_frutinha.mp3")


def _listar_cenas_em_ordem(pasta_cenas: str) -> list[str]:
    """Acha os .mp4 de cena na pasta e ordena pelo número no nome do
    arquivo (cena1.mp4, cena2.mp4...) -- a ORDEM nunca é decidida por
    conteúdo, é sempre a numérica de quem gerou as cenas (mesmo
    princípio do pivô do ônibus: este pipeline decide só a edição, nunca
    a ordem)."""
    arquivos = [f for f in os.listdir(pasta_cenas) if f.lower().endswith(".mp4")]
    if not arquivos:
        raise RuntimeError(f"Nenhum .mp4 de cena encontrado em {pasta_cenas}")

    def _numero(nome: str) -> int:
        m = re.search(r"\d+", nome)
        if not m:
            raise RuntimeError(f"Arquivo de cena sem número no nome: {nome} (esperado tipo cena1.mp4)")
        return int(m.group())

    arquivos.sort(key=_numero)
    return [os.path.join(pasta_cenas, f) for f in arquivos]


def _normalizar_clipe_video(caminho_entrada: str, caminho_saida: str):
    """Reencoda um clipe pronto (vindo do Google Flow) pro formato padrão
    do projeto (1080x1920, 30fps, h264) -- o xfade encadeado usado em
    `concatenar_com_transicao` exige que todos os inputs tenham a mesma
    resolução/fps, e o Flow pode exportar clipes com pequenas diferenças
    entre si."""
    _rodar([
        "ffmpeg", "-y", "-i", caminho_entrada,
        "-vf", f"scale=w={LARGURA}:h={ALTURA}:force_original_aspect_ratio=increase,crop={LARGURA}:{ALTURA},fps=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000",
        caminho_saida,
    ])


def montar_video_de_cenas_prontas(pasta_cenas: str, caminho_saida: str) -> float:
    """Monta o vídeo final a partir das cenas já prontas (imagem+vídeo
    gerados no Flow, diálogo do personagem já embutido). Concatena com a
    mesma transição variada do resto do projeto (slide/wipe + flash
    raro), queima legenda transcrita do diálogo final (Whisper local) e
    mixa uma trilha de fundo baixinha por baixo das falas (volume mais
    baixo que o pivô -- lá é só narração isolada, aqui tem diálogo dos
    personagens que não pode ficar abafado).

    Retorna a duração total do vídeo."""
    cenas = _listar_cenas_em_ordem(pasta_cenas)
    print(f"{len(cenas)} cena(s) encontrada(s), na ordem: {[os.path.basename(c) for c in cenas]}")

    with tempfile.TemporaryDirectory() as pasta_tmp:
        print("Normalizando resolução/fps das cenas...")
        clipes_normalizados = []
        for i, caminho_cena in enumerate(cenas):
            caminho_norm = os.path.join(pasta_tmp, f"norm{i}.mp4")
            _normalizar_clipe_video(caminho_cena, caminho_norm)
            clipes_normalizados.append(caminho_norm)

        print("Concatenando cenas (com transição fluida entre elas)...")
        caminho_bruto = os.path.join(pasta_tmp, "bruto.mp4")
        concatenar_com_transicao(clipes_normalizados, caminho_bruto)
        duracao_total = _duracao_segundos(caminho_bruto)

        print("Transcrevendo diálogo final pra gerar legenda (Whisper local)...")
        caminho_audio = os.path.join(pasta_tmp, "audio.wav")
        extrair_audio(caminho_bruto, caminho_audio)
        palavras = _transcrever_palavras(caminho_audio)
        caminho_ass = os.path.join(pasta_tmp, "legenda.ass")
        gerar_legenda_ass(caminho_audio, caminho_ass, LARGURA, ALTURA, palavras=palavras)

        print("Queimando legenda...")
        caminho_com_legenda = os.path.join(pasta_tmp, "com_legenda.mp4")
        queimar_legenda(caminho_bruto, caminho_ass, caminho_com_legenda)

        print("Adicionando trilha de fundo baixinha (Medley de Igaratá, padrão desse nicho)...")
        caminho_trilha_wav = os.path.join(pasta_tmp, "trilha.wav")
        gerar_ambiencia(caminho_trilha_wav, duracao_total, "leve", CAMINHO_TRILHA_FRUTINHA)

        _rodar([
            "ffmpeg", "-y",
            "-i", caminho_com_legenda, "-i", caminho_trilha_wav,
            "-filter_complex",
            "[0:a]volume=1.0[a0];[a0][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac",
            "-movflags", "+faststart",
            caminho_saida,
        ])

    frames_reais = _contar_frames_reais(caminho_saida)
    duracao_real = frames_reais / 30
    if duracao_real < duracao_total * 0.8:
        raise RuntimeError(
            f"Vídeo saiu truncado: {duracao_real:.1f}s reais de vídeo ({frames_reais} frames) "
            f"pra {duracao_total:.1f}s esperado -- não usar esse arquivo, precisa remontar."
        )

    print(f"\nVídeo salvo em: {caminho_saida} ({duracao_real:.1f}s, verificado)")
    return duracao_total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cenas", required=True, help="pasta com cena1.mp4, cena2.mp4... (baixados do Flow)")
    parser.add_argument("--saida", required=True, help="caminho do vídeo final")
    args = parser.parse_args()
    montar_video_de_cenas_prontas(args.cenas, args.saida)


if __name__ == "__main__":
    main()
