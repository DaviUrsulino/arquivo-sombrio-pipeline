"""Alternativa 100% gratuita ao montar_video.py (JSON2Video): narração via
Kokoro (Apache 2.0, roda local, sem chave), legenda automática via
faster-whisper (roda local, sem GPU) e montagem via ffmpeg (já instalado).

Zero custo por vídeo, mas processamento roda no seu PC (mais lento que a
API paga, e a legenda não tem o destaque de palavra-por-palavra do
JSON2Video — vem em blocos de frase).

Cada cena aceita 1 ou mais imagens (cenaN_1.jpg, cenaN_2.jpg, ...) — se
houver mais de uma, a duração da narração é dividida entre elas, cortando
de uma pra outra no meio da fala (mais dinâmico que uma imagem parada o
tempo todo). Se só existir cenaN.jpg, usa ela sozinha (funciona igual antes).

Uso:
    python src/montar_video_local.py --canal terror --roteiro roteiro_terror.json \
        --imagens imagens_aprovadas/terror --saida video_final.mp4
"""

import argparse
import base64
import io
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import time

import requests
import soundfile as sf
from PIL import Image

from canais import carregar_canal

LARGURA, ALTURA = 1080, 1920

_PIPELINE_KOKORO = None


def _rodar(comando: list[str]):
    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(f"Comando falhou: {' '.join(comando)}\n{resultado.stderr}")


def _duracao_segundos(caminho: str) -> float:
    resultado = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", caminho,
        ],
        capture_output=True, text=True,
    )
    return float(resultado.stdout.strip())


def _contar_frames_reais(caminho: str) -> int:
    """Conta frames de vídeo DECODIFICANDO de verdade (-count_frames), não
    só lendo a duração declarada no container (`format=duration`) -- bug
    real 2026-09-11: um vídeo com xfade encadeado quebrado reportava
    duração normal via `format=duration` mas só tinha metade dos frames de
    vídeo de verdade quando contado. Mais lento (decodifica o arquivo
    inteiro), só usar pra verificação final, não em loop apertado."""
    resultado = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
            "-show_entries", "stream=nb_read_frames",
            "-of", "default=noprint_wrappers=1:nokey=1", caminho,
        ],
        capture_output=True, text=True,
    )
    return int(resultado.stdout.strip())


def _duracao_segundos_stream_audio(caminho: str) -> float:
    """Duração do STREAM de áudio especificamente (não do container/vídeo)
    -- usado pra detectar narração cortada mesmo quando o vídeo bate certo
    (ver montar_video_de_audio_e_imagens)."""
    resultado = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", caminho,
        ],
        capture_output=True, text=True,
    )
    return float(resultado.stdout.strip())


def gerar_narracao(texto: str, voz: str, caminho_saida: str):
    """Kokoro (lang_code='p' = português brasileiro). Carrega o modelo uma
    vez só e reaproveita entre chamadas (fica pesado recarregar por cena)."""
    global _PIPELINE_KOKORO
    from kokoro import KPipeline

    if _PIPELINE_KOKORO is None:
        _PIPELINE_KOKORO = KPipeline(lang_code="p")

    pedacos_audio = []
    for _, _, audio in _PIPELINE_KOKORO(texto, voice=voz):
        pedacos_audio.append(audio)

    import numpy as np
    audio_completo = np.concatenate(pedacos_audio) if len(pedacos_audio) > 1 else pedacos_audio[0]
    sf.write(caminho_saida, audio_completo, 24000)


# Kokoro só tem 3 vozes em pt-BR (pm_alex, pm_santa, pf_dora) — pra dar mais
# variedade percebida sem precisar de um modelo novo, aplica um leve pitch
# shift (preservando a duração) como "variante" de cada voz base. Sorteado
# uma vez por vídeo (não por cena — o mesmo personagem não pode mudar de
# tom no meio do vídeo).
VARIANTES_PITCH = {
    # Extremos (0.84 / 1.19) testados em 2026-09-08 e reprovados no ouvido
    # (feedback real: "não ficou legal") -- mantendo só as variações
    # moderadas, que soam natural.
    "normal": 1.0,
    "levemente_grave": 0.95,
    "grave": 0.90,
    "levemente_aguda": 1.06,
    "aguda": 1.12,
}


def aplicar_variante_pitch(caminho_audio: str, fator: float, taxa_amostragem: int = 24000):
    """Pitch shift preservando a duração (asetrate + atempo inverso). Sem
    efeito se fator == 1.0."""
    if fator == 1.0:
        return
    caminho_tmp = caminho_audio + ".pitch.wav"
    _rodar([
        "ffmpeg", "-y", "-i", caminho_audio,
        "-af", f"asetrate={taxa_amostragem * fator},aresample={taxa_amostragem},atempo={1 / fator}",
        caminho_tmp,
    ])
    os.replace(caminho_tmp, caminho_audio)


def _imagens_da_cena(pasta_imagens: str, indice: int) -> list[str]:
    """Procura cenaN_1.jpg, cenaN_2.jpg, ... Se não achar nenhuma, usa cenaN.jpg."""
    imagens = []
    parte = 1
    while True:
        caminho = os.path.join(pasta_imagens, f"cena{indice}_{parte}.jpg")
        if not os.path.exists(caminho):
            break
        imagens.append(caminho)
        parte += 1

    if imagens:
        return imagens

    caminho_unico = os.path.join(pasta_imagens, f"cena{indice}.jpg")
    if os.path.exists(caminho_unico):
        return [caminho_unico]

    raise FileNotFoundError(
        f"Não encontrei imagem pra cena {indice} (tentei cena{indice}_1.jpg e cena{indice}.jpg)"
    )


FONTE_PADRAO = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Fundo da tela final (sino + play, gerado via GPT/DALL-E, aprovado
# visualmente em 2026-09-08) — usado pros dois canais (universal, sem
# nada específico de terror ou de tendências). Se o arquivo não existir
# (ex: clone novo do repo sem esse asset), cai pro fundo de cor lisa.
CAMINHO_FUNDO_CTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cta_fundo.jpg")


# Várias frases de CTA em vez de sempre a mesma — reduz a "assinatura"
# repetitiva entre vídeos (pesquisa 2026-09-08: classificador de "AI slop"
# do YouTube pega padrão idêntico repetido, ver README/commit).
FRASES_CTA = [
    ("CURTA E SE INSCREVA", "E ATIVE O SININHO"),
    ("GOSTOU? DEIXA O LIKE", "SE INSCREVE PRO PRÓXIMO"),
    ("SE INSCREVE AQUI", "TEM VÍDEO NOVO TODO DIA"),
    ("CURTIU A HISTÓRIA?", "SE INSCREVE E ATIVA O SININHO"),
]


def gerar_cta_final(caminho_saida: str, duracao: float = 3.0):
    """Tela final animada pedindo like/inscrição/sininho — usa a imagem de
    fundo aprovada (sino+play) se existir, senão cai pra cor lisa. Áudio
    silencioso (proposital, não erro) só pra manter o mesmo formato de
    stream dos outros clipes na hora de concatenar."""
    import random

    fps = 30
    linha1, linha2 = random.choice(FRASES_CTA)
    texto_filtro = (
        f"drawtext=text='{linha1}':fontfile={FONTE_PADRAO}:fontcolor=white:"
        f"fontsize=64:x=(w-text_w)/2:y=h*0.72:borderw=4:bordercolor=black@0.6,"
        f"drawtext=text='{linha2}':fontfile={FONTE_PADRAO}:fontcolor=0xFFD700:"
        f"fontsize=54:x=(w-text_w)/2:y=h*0.80:borderw=4:bordercolor=black@0.6,"
        f"fade=t=in:st=0:d=0.4,fade=t=out:st={max(duracao - 0.4, 0)}:d=0.4"
    )

    if os.path.exists(CAMINHO_FUNDO_CTA):
        # -framerate explícito: sem isso, entrada de imagem estática cai no
        # padrão de 25fps do ffmpeg, diferente dos 30fps das cenas -- isso
        # quebra o xfade na concatenação (timebase incompatível).
        entrada_video = ["-loop", "1", "-framerate", str(fps), "-i", CAMINHO_FUNDO_CTA]
        filtro_video = (
            f"scale=w={LARGURA}:h={ALTURA}:force_original_aspect_ratio=increase,"
            f"crop={LARGURA}:{ALTURA},{texto_filtro}"
        )
    else:
        entrada_video = ["-f", "lavfi", "-i", f"color=c=0x14141f:s={LARGURA}x{ALTURA}:d={duracao}:r={fps}"]
        filtro_video = texto_filtro

    _rodar([
        "ffmpeg", "-y",
        *entrada_video,
        "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono:d={duracao}",
        "-t", str(duracao),
        "-vf", filtro_video,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-shortest",
        caminho_saida,
    ])


PERFIS_AMBIENCIA = {
    "tenso": {"freq": 55, "tremolo_hz": 0.15, "tremolo_depth": 0.6, "volume": 0.05},
    "dramatico": {"freq": 90, "tremolo_hz": 0.25, "tremolo_depth": 0.5, "volume": 0.06},
    "leve": {"freq": 220, "tremolo_hz": 4, "tremolo_depth": 0.4, "volume": 0.04},
    "epico": {"freq": 70, "tremolo_hz": 0.1, "tremolo_depth": 0.55, "volume": 0.06},
}


_PASTA_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Trilhas reais livres de direitos autorais, uma por plataforma (escolhidas
# manualmente pelo Davi, 2026-09-09). Testamos um catálogo de 3 clássicos de
# terror (Bach/Saint-Saëns/Grieg via Kevin MacLeod) no mesmo dia, mas o Davi
# não gostou ("horríveis") -- revertido de volta pra essas duas.
TRILHAS_POR_PLATAFORMA = {
    "tiktok": os.path.join(_PASTA_ASSETS, "trilha_tiktok.mp3"),
    "youtube": os.path.join(_PASTA_ASSETS, "trilha_youtube.mp3"),
}


def gerar_ambiencia(caminho_saida: str, duracao: float, perfil: str = "leve", caminho_trilha: str | None = None):
    """Trilha de fundo: usa `caminho_trilha` (livre de direitos autorais)
    se ele existir, cortada/repetida pra bater a duração do vídeo com
    fade-out no final; senão cai pro drone sintetizado (sine + tremolo)
    como fallback -- nunca falha por falta do arquivo de música."""
    if caminho_trilha and os.path.exists(caminho_trilha):
        fade_inicio = max(duracao - 2, 0)
        _rodar([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", caminho_trilha,
            "-t", str(duracao),
            "-af", f"volume=0.12,afade=t=out:st={fade_inicio}:d=2",
            caminho_saida,
        ])
        return

    p = PERFIS_AMBIENCIA.get(perfil, PERFIS_AMBIENCIA["leve"])
    _rodar([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency={p['freq']}:duration={duracao}",
        "-af", f"tremolo=f={p['tremolo_hz']}:d={p['tremolo_depth']},volume={p['volume']}",
        caminho_saida,
    ])


TIPOS_MOVIMENTO = [
    # zoom repetido de propósito -- feedback 2026-09-09: "gostei demais, só
    # falta mais zoom in/zoom out" -- pesa mais que os pans no sorteio.
    "zoom_in", "zoom_in", "zoom_out", "zoom_out", "zoom_forte",
    "pan_esquerda", "pan_direita", "pan_cima",
]

# Bug real encontrado 2026-09-10: o Kokoro (TTS) mexe no estado do gerador
# global `random` do Python quando gera narração (confirmado com teste
# isolado: os sorteios logo depois de chamar o pipeline do Kokoro ficavam
# visivelmente enviesados) -- como gerar_clipe_cena sorteia o tipo de
# movimento LOGO DEPOIS de gerar a narração da cena, isso fazia
# "personagem_cresce" aparecer bem menos que o peso configurado (2 vídeos
# seguidos com só 1/16 em vez dos ~5-6/16 esperados a 35%). Usa um gerador
# de aleatoriedade PRÓPRIO (random.Random, não o módulo `random` global)
# só pra esse sorteio, imune a qualquer lib que reconfigure o estado global.
_RNG_MOVIMENTO = random.Random()

# Tipos de transição do xfade sorteados por corte entre cenas (ver
# concatenar_com_transicao) -- nomes nativos do ffmpeg, sem precisar de
# filtro customizado. SEM "fade"/"dissolve" de propósito -- pedido do Davi
# 2026-09-10: essas duas MISTURAM (cross-blend) as duas imagens por cima
# uma da outra, exatamente o efeito de "dissolve" que ele rejeitou antes.
# "slide"/"wipe" são diferentes: a imagem nova empurra/varre a antiga pra
# fora do quadro (movimento mecânico), sem sobrepor os dois quadros.
TRANSICOES_XFADE = [
    "slideleft", "slideright", "slideup", "slidedown",
    "wipeleft", "wiperight", "wipeup", "wipedown",
]
# "personagem_cresce" fica de fora da lista principal (sorteado com peso
# menor em gerar_clipe_cena) porque depende de rembg (CPU, mais lento) e
# tem fallback pra zoom_in se a extração falhar -- não deve ser o padrão.


_CLIENTE_REMBG_MODAL = None


def _extrair_personagem_rgba(caminho_imagem: str, caminho_saida_png: str):
    """Remove o fundo da imagem deixando só o personagem opaco num PNG do
    mesmo tamanho da imagem original (RGBA, fundo transparente) -- usado
    pelo movimento "personagem_cresce" pra dar a sensação de personagem
    "recortado tipo figurinha" crescendo sozinho enquanto o fundo fica
    parado (feedback 2026-09-09, referência real de editores desse nicho).

    Roda no Modal (não local) -- ver src/modal_rembg_app.py: rodar isso no
    runner efêmero do GitHub Actions baixava o modelo do rembg (~1GB) do
    zero em toda execução, sem cache nenhum, e isso derrubou o runner real
    ("the runner has received a shutdown signal") duas vezes em produção.
    No Modal o modelo fica num Volume persistente, cache reaproveitado
    entre chamadas (~4s por imagem depois do primeiro cold start)."""
    global _CLIENTE_REMBG_MODAL
    import modal

    if _CLIENTE_REMBG_MODAL is None:
        _CLIENTE_REMBG_MODAL = modal.Cls.from_name("arquivo-sombrio-rembg", "Rembg")()

    with open(caminho_imagem, "rb") as f:
        imagem_bytes = f.read()
    resultado_bytes = _CLIENTE_REMBG_MODAL.remover_fundo.remote(imagem_bytes)
    with open(caminho_saida_png, "wb") as f:
        f.write(resultado_bytes)


def gerar_clipe_imagem_silencioso(
    caminho_imagem: str, duracao: float, caminho_saida: str, tipo_movimento: str = "zoom_in"
):
    """Imagem estática + movimento de câmera (Ken Burns variado) + "tremida"
    sutil (câmera na mão), sem áudio, com a duração pedida.

    `tipo_movimento` (ver TIPOS_MOVIMENTO) varia o tipo de movimento em vez
    de sempre repetir o mesmo zoom centralizado — feedback 2026-09-09:
    referências reais ("Contos Urbanos") alternam arrastar de lado, subir,
    zoom mais forte, não só "tremer parado" — dá mais fluidez.

    A tremida é um jitter senoidal (seno/cosseno em frequências diferentes
    pra não formar um círculo perfeito) somado ao centro do crop a cada
    frame — imita leve instabilidade de câmera na mão. A amplitude é \
pequena (poucos pixels) e cabe folgada dentro da margem de 2x que o crop \
inicial já reserva, então nunca revela borda da imagem."""
    fps = 30
    n_frames = int(duracao * fps)
    jitter_x = "5*sin(on*0.35)"
    jitter_y = "4*cos(on*0.27)"
    t = f"(on/{max(n_frames, 1)})"  # 0.0 -> 1.0 ao longo do clipe

    if tipo_movimento == "personagem_cresce":
        try:
            print("  [personagem_cresce] extraindo personagem (rembg)...")
            with tempfile.TemporaryDirectory() as pasta_tmp_fg:
                caminho_png = os.path.join(pasta_tmp_fg, "personagem.png")
                _extrair_personagem_rgba(caminho_imagem, caminho_png)

                # Bug real encontrado 2026-09-10 (vídeo do palhaço, cena dos
                # dois policiais): rembg não tem como saber QUAL "personagem"
                # recortar numa cena com duas pessoas ou sem um sujeito isolado
                # claro -- às vezes devolve a imagem quase inteira como "frente"
                # (opacidade >70% do quadro), o que faz o overlay virar um
                # "fantasma" da cena inteira duplicada e ampliada por cima do
                # fundo, em vez de só o personagem crescendo. Rejeita a
                # extração nesses casos (ou quando não achou nada, <1%) e cai
                # no fallback de zoom normal, igual já acontece quando o
                # rembg falha de vez.
                with Image.open(caminho_png) as img_rgba:
                    alpha = img_rgba.getchannel("A")
                    histograma = alpha.histogram()  # 256 bins, índice = valor do pixel
                    pixels_opacos = sum(histograma[21:])  # >20 = considera "opaco"
                    fracao_opaca = pixels_opacos / (alpha.width * alpha.height)
                if not (0.01 <= fracao_opaca <= 0.70):
                    raise RuntimeError(
                        f"extração de personagem suspeita (área opaca {fracao_opaca:.0%} do quadro) "
                        "-- provavelmente pegou a cena inteira em vez de só o personagem"
                    )

                # Fundo cresce devagar (8%) e parado; personagem cresce mais
                # rápido E treme mais forte (mesmo jitter senoidal de câmera
                # na mão usado no resto do arquivo) -- feedback 2026-09-09: "o
                # personagem treme mais que o fundo... ele vai aumentando",
                # reforçado em 2026-09-10: "precisa mais, acentuar mais isso"
                # (22% e jitter de 5px ainda liam como sutis demais pro Davi
                # perceber o efeito só assistindo o vídeo final). Sobe o
                # crescimento do personagem pra 40% e dobra a amplitude do
                # tremor dele. Usa zoompan (não scale+crop encadeado) porque
                # o zoompan já é a técnica usada nos outros movimentos do
                # projeto e evita a trepidação por arredondamento que o
                # scale+crop duplo causava a cada frame.
                zoom_por_frame_bg = 1 + (0.08 / max(n_frames, 1))
                expressao_zoom_bg = f"min(zoom+{zoom_por_frame_bg-1},1.08)"
                zoom_por_frame_fg = 1 + (0.40 / max(n_frames, 1))
                expressao_zoom_fg = f"min(zoom+{zoom_por_frame_fg-1},1.40)"
                jitter_x = "10*sin(on*0.35)"
                jitter_y = "8*cos(on*0.27)"
                # Feedback 2026-09-09: "o fundo tremendo também, mas menos
                # que o personagem" -- mesmo jitter senoidal usado no
                # personagem, só que com amplitude bem menor (~40% dele).
                jitter_x_bg = "4*sin(on*0.35)"
                jitter_y_bg = "3*cos(on*0.27)"

                _rodar([
                    "ffmpeg", "-y",
                    "-loop", "1", "-i", caminho_imagem,   # fundo (imagem original)
                    "-loop", "1", "-i", caminho_png,      # personagem recortado (RGBA)
                    "-filter_complex",
                    (
                        f"[0:v]scale=w={LARGURA*2}:h={ALTURA*2}:force_original_aspect_ratio=increase,"
                        f"crop={LARGURA*2}:{ALTURA*2},"
                        f"zoompan=z='{expressao_zoom_bg}':d={n_frames}:"
                        f"x='iw/2-(iw/zoom/2)+{jitter_x_bg}':y='ih/2-(ih/zoom/2)+{jitter_y_bg}':"
                        f"s={LARGURA}x{ALTURA}:fps={fps}[bg];"
                        f"[1:v]format=rgba,"
                        f"scale=w={LARGURA*2}:h={ALTURA*2}:force_original_aspect_ratio=increase,"
                        f"crop={LARGURA*2}:{ALTURA*2},"
                        f"zoompan=z='{expressao_zoom_fg}':d={n_frames}:"
                        f"x='iw/2-(iw/zoom/2)+{jitter_x}':y='ih/2-(ih/zoom/2)+{jitter_y}':"
                        f"s={LARGURA}x{ALTURA}:fps={fps}[fg];"
                        f"[bg][fg]overlay=0:0[v]"
                    ),
                    "-map", "[v]",
                    "-t", str(duracao),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    caminho_saida,
                ])
            return
        except Exception as e:
            # rembg falhando não pode derrubar o vídeo inteiro -- cai pro
            # movimento padrão (mesmo espírito defensivo do resto do
            # pipeline: fallback, nunca crash).
            print(f"  [personagem_cresce] extração de personagem falhou ({e}), usando zoom_in")
            tipo_movimento = "zoom_in"

    if tipo_movimento == "zoom_out":
        zoom_por_frame = 1 + (0.18 / max(n_frames, 1))
        expressao_zoom = f"if(eq(on,0),1.20,max(zoom-{zoom_por_frame-1},1.0))"
        expr_x = f"iw/2-(iw/zoom/2)+{jitter_x}"
        expr_y = f"ih/2-(ih/zoom/2)+{jitter_y}"
    elif tipo_movimento == "zoom_forte":
        zoom_por_frame = 1 + (0.32 / max(n_frames, 1))
        expressao_zoom = f"min(zoom+{zoom_por_frame-1},1.38)"
        expr_x = f"iw/2-(iw/zoom/2)+{jitter_x}"
        expr_y = f"ih/2-(ih/zoom/2)+{jitter_y}"
    elif tipo_movimento == "pan_esquerda":
        zoom_por_frame = 1 + (0.06 / max(n_frames, 1))
        expressao_zoom = f"min(zoom+{zoom_por_frame-1},1.12)"
        expr_x = f"iw/2-(iw/zoom/2)+(0.12*iw/zoom)*(0.5-{t})+{jitter_x}"
        expr_y = f"ih/2-(ih/zoom/2)+{jitter_y}"
    elif tipo_movimento == "pan_direita":
        zoom_por_frame = 1 + (0.06 / max(n_frames, 1))
        expressao_zoom = f"min(zoom+{zoom_por_frame-1},1.12)"
        expr_x = f"iw/2-(iw/zoom/2)+(0.12*iw/zoom)*({t}-0.5)+{jitter_x}"
        expr_y = f"ih/2-(ih/zoom/2)+{jitter_y}"
    elif tipo_movimento == "pan_cima":
        zoom_por_frame = 1 + (0.08 / max(n_frames, 1))
        expressao_zoom = f"min(zoom+{zoom_por_frame-1},1.15)"
        expr_x = f"iw/2-(iw/zoom/2)+{jitter_x}"
        expr_y = f"ih/2-(ih/zoom/2)+(0.10*ih/zoom)*(0.5-{t})+{jitter_y}"
    else:  # zoom_in (padrão)
        zoom_por_frame = 1 + (0.18 / max(n_frames, 1))
        expressao_zoom = f"min(zoom+{zoom_por_frame-1},1.20)"
        expr_x = f"iw/2-(iw/zoom/2)+{jitter_x}"
        expr_y = f"ih/2-(ih/zoom/2)+{jitter_y}"

    _rodar([
        "ffmpeg", "-y",
        "-loop", "1", "-i", caminho_imagem,
        "-filter_complex",
        (
            # cover (não esticar): escala pelo maior lado e corta o excesso
            # centralizado, pra imagem quadrada (ex: FLUX no Cloudflare) ou
            # de qualquer proporção virar 9:16 sem distorcer.
            f"[0:v]scale=w={LARGURA*2}:h={ALTURA*2}:force_original_aspect_ratio=increase,"
            f"crop={LARGURA*2}:{ALTURA*2},"
            f"zoompan=z='{expressao_zoom}':d={n_frames}:"
            f"x='{expr_x}':y='{expr_y}':"
            f"s={LARGURA}x{ALTURA}:fps={fps}[v]"
        ),
        "-map", "[v]",
        "-t", str(duracao),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        caminho_saida,
    ])


def gerar_sfx_whoosh(caminho_saida: str):
    """SFX sintetizado (sem depender de baixar arquivo de terceiro) pra
    marcar o corte entre cenas — som curto de "whoosh" via sweep de ruído
    filtrado. Fica bem mais barato/seguro que integrar uma lib externa de
    efeitos por enquanto."""
    _rodar([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anoisesrc=color=pink:duration=0.35:amplitude=0.6",
        "-af",
        "afade=t=in:d=0.05,afade=t=out:st=0.2:d=0.15,"
        "bandpass=f=1200:width_type=h:w=2000,volume=1.8",
        caminho_saida,
    ])


def gerar_clipe_cena(
    imagens: list[str], caminho_audio: str, duracao: float, caminho_saida: str,
    pasta_tmp: str, caminho_sfx: str | None = None,
):
    """Monta a cena: divide a duração entre as imagens (corte no meio da
    fala se houver mais de uma, sorteando um tipo de movimento de câmera
    diferente por imagem pra reforçar o corte com mais fluidez), depois mux
    a narração por cima do trecho todo."""
    duracao_por_imagem = duracao / len(imagens)
    sub_clipes = []
    for i, caminho_imagem in enumerate(imagens):
        caminho_sub = os.path.join(pasta_tmp, f"{os.path.basename(caminho_saida)}_sub{i}.mp4")
        # "personagem_cresce" reativado 2026-09-09 rodando no Modal (não
        # mais localmente com rembg) -- ver src/modal_rembg_app.py e
        # _extrair_personagem_rgba() acima. Isso resolve o motivo real por
        # trás de duas quedas de runner em produção: o modelo do rembg
        # baixava ~1GB do zero em toda execução no runner efêmero do
        # GitHub Actions, sem cache nenhum. No Modal o cache é persistente
        # (Volume), ~4s por imagem depois do primeiro cold start.
        # Pedido do Davi 2026-09-10: "personagem_cresce" tava sorteado com
        # chance baixa demais (1/9 ~= 11%) e passava despercebido no vídeo
        # inteiro -- sobe pra ~35% de chance por imagem (peso 13 contra peso
        # 3 de cada um dos 8 tipos normais: 13/(8*3+13) = 35%).
        pesos_movimento = [3] * len(TIPOS_MOVIMENTO) + [13]
        tipo_movimento = _RNG_MOVIMENTO.choices(TIPOS_MOVIMENTO + ["personagem_cresce"], weights=pesos_movimento)[0]
        gerar_clipe_imagem_silencioso(caminho_imagem, duracao_por_imagem, caminho_sub, tipo_movimento=tipo_movimento)
        sub_clipes.append(caminho_sub)

    if len(sub_clipes) == 1:
        caminho_video_silencioso = sub_clipes[0]
    else:
        caminho_video_silencioso = os.path.join(pasta_tmp, f"{os.path.basename(caminho_saida)}_silencioso.mp4")
        concatenar_clipes(sub_clipes, caminho_video_silencioso, pasta_tmp)

    # SFX curto em cada corte de imagem dentro da cena (só existe corte se
    # houver mais de uma imagem) — reforça sonoramente a mudança visual.
    pontos_de_corte_ms = [int(round(duracao_por_imagem * i * 1000)) for i in range(1, len(sub_clipes))]

    if caminho_sfx and pontos_de_corte_ms:
        entradas_sfx = []
        rotulos_sfx = []
        for i, atraso_ms in enumerate(pontos_de_corte_ms):
            entradas_sfx += ["-i", caminho_sfx]
            rotulos_sfx.append(f"sfx{i}")
        filtros = [f"[{i+2}:a]adelay={atraso}|{atraso}[{rotulo}]" for i, (atraso, rotulo) in enumerate(zip(pontos_de_corte_ms, rotulos_sfx))]
        entradas_mix = "[1:a]" + "".join(f"[{r}]" for r in rotulos_sfx)
        filtros.append(f"{entradas_mix}amix=inputs={len(rotulos_sfx)+1}:duration=first:dropout_transition=0[aout]")
        _rodar([
            "ffmpeg", "-y",
            "-i", caminho_video_silencioso, "-i", caminho_audio, *entradas_sfx,
            "-filter_complex", ";".join(filtros),
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            caminho_saida,
        ])
    else:
        _rodar([
            "ffmpeg", "-y",
            "-i", caminho_video_silencioso, "-i", caminho_audio,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            caminho_saida,
        ])


def concatenar_clipes(caminhos_clipes: list[str], caminho_saida: str, pasta_tmp: str):
    lista_txt = os.path.join(pasta_tmp, "lista.txt")
    with open(lista_txt, "w", encoding="utf-8") as f:
        for caminho in caminhos_clipes:
            f.write(f"file '{os.path.abspath(caminho)}'\n")
    _rodar([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista_txt,
        "-c", "copy", caminho_saida,
    ])


def concatenar_com_transicao(caminhos_clipes: list[str], caminho_saida: str):
    """Concatena as cenas com transição VARIADA por corte, sorteada entre:
    puxar de um lado/cima/baixo (slide/wipe, duração curta ~0.25s) na
    maioria das vezes, e um corte seco com flash de luz numa fração pequena
    dos cortes (~9%) pra dar impacto sem virar a regra.

    Histórico (2026-09-10, várias idas e voltas com o Davi no mesmo dia):
    1) Tínhamos dissolve de 0.4s sempre -- feedback: "quero mais fluidez".
    2) Troquei pra corte seco puro depois de analisar quadro a quadro (30fps)
       uma referência real que ele trouxe (mesmo roteiro do palhaço, outro
       canal) -- lá é corte seco 100% do tempo, zero blend. Mas o resultado
       ficou "sempre igual" na visão dele.
    3) Adicionei só um flash de luz no corte -- ele achou bom mas queria de
       volta o efeito de "puxar a foto de um lado" que já existia antes
       (slide/wipe), com VÁRIOS tipos alternando pra ser dinâmico, e o
       flash só ocasionalmente, não em todo corte.
    Este é o esquema final: pool com as 8 direções de slide/wipe (peso 1
    cada) + flash (peso 1) -- ~11% flash, ~89% puxão direcional variado.

    Slide/wipe NÃO é a mesma coisa que o dissolve/fade rejeitado no passo
    2 -- é um corte mecânico (a imagem nova empurra/varre a antiga pra fora
    do quadro), sem misturar os dois quadros por cima um do outro como um
    crossfade faz; por isso não conflita com o que foi validado na
    referência sobre "zero mistura".

    Importante sobre ÁUDIO: crossfade de ÁUDIO com FALA (acrossfade) soa
    mal -- duas narrações tocando ao mesmo tempo por uma fração de segundo
    vira chiado/interferência, não transição suave (feedback 2026-09-08).
    Em vez disso, cada junção com slide/wipe recorta uma fatia curta (a
    duração daquele corte) perto do ponto de troca -- metade do fim de uma
    cena, metade do começo da próxima -- sem sobrepor as falas. Corte com
    flash não recorta nada (não há overlap de vídeo nesse tipo)."""
    FLASH = "flash"
    pool_transicoes = TRANSICOES_XFADE + [FLASH]  # 8 direções + 1 flash = ~11% de chance de flash
    # Feedback 2026-09-10: "está demorando, tá tipo carregando... é como se
    # ela tivesse sido jogada" -- 0.25s de slide/wipe lia como um scroll
    # lento, não uma foto "jogada" pra fora do quadro. Encurtar pra 0.12s
    # deixa o xfade rápido o bastante pra ler como um corte com impacto
    # (arremesso), não uma transição suave de carregamento.
    # Bug real encontrado 2026-09-10 (vídeo do Somerton saiu truncado pra
    # 17-41s em vez de ~71s): 0.12s/0.06s não caem num número inteiro de
    # frames a 30fps (3.6 e 1.8 frames) -- o xfade encadeado (offset de um
    # merge depende do acumulado do anterior) space compõe esse erro de
    # arredondamento a cada corte, e pra certas combinações aleatórias de
    # tipo de transição isso estourava o offset além da duração real do
    # clipe seguinte, cortando o resto do vídeo inteiro. Fixado usando
    # duração em frames inteiros (4 e 2 frames a 30fps) em vez de segundos
    # arbitrários.
    duracao_slide = 4 / 30
    duracao_flash = 2 / 30

    duracoes = [_duracao_segundos(c) for c in caminhos_clipes]
    n = len(caminhos_clipes)
    tipos_corte = [_RNG_MOVIMENTO.choice(pool_transicoes) for _ in range(n - 1)]
    duracoes_corte = [duracao_flash if t == FLASH else duracao_slide for t in tipos_corte]

    entradas = []
    for caminho in caminhos_clipes:
        entradas += ["-i", caminho]

    filtros = []
    # setsar=1 em toda entrada -- bug real 2026-09-10: o clipe do
    # personagem_cresce (passa por scale 2x + zoompan + overlay) sai com SAR
    # ligeiramente diferente (7680:7679 por arredondamento) dos clipes
    # normais (1:1), e mesmo só usando xfade (ver abaixo) isso pode gerar
    # inconsistência entre entradas -- normaliza sempre.
    for i in range(n):
        filtros.append(f"[{i}:v]setsar=1[v{i}norm]")

    # Bug real 2026-09-10 (tentativa anterior): usar `concat` pro corte tipo
    # "flash" e `xfade` pros slides/wipes no mesmo grafo quebrava sempre que
    # os dois se encadeavam -- cada filtro produz uma saída com timebase
    # diferente (concat: 1/1000000 fixo; xfade: baseado no frame, variável) e
    # settb=AVTB não resolvia (AVTB É o 1/1000000 que já não batia). Corrigido
    # de vez usando xfade pra TUDO, inclusive o flash: o flash é só um xfade
    # tipo "fade" bem mais curto (0.06s, quase instantâneo) combinado com um
    # pico de brilho na cena que entra -- lê como um "pop" de luz no corte,
    # não como o dissolve/mistura lento que já foi rejeitado antes. Um único
    # tipo de filtro encadeado o tempo todo evita qualquer conflito de
    # timebase entre um corte e o próximo, seja qual for a combinação.
    v_atual = "v0norm"
    duracao_acumulada = duracoes[0]
    for i in range(1, n):
        tipo = tipos_corte[i - 1]
        dur_corte = duracoes_corte[i - 1]
        v_saida = f"v{i}out" if i < n - 1 else "vout"
        offset = max(duracao_acumulada - dur_corte, 0)
        if tipo == FLASH:
            clipe_entrando = f"v{i}norm_flash"
            filtros.append(f"[v{i}norm]eq=brightness=0.9:enable='lte(t,{dur_corte})'[{clipe_entrando}]")
            tipo_xfade = "fade"
        else:
            clipe_entrando = f"v{i}norm"
            tipo_xfade = tipo
        filtros.append(
            f"[{v_atual}][{clipe_entrando}]xfade=transition={tipo_xfade}:duration={dur_corte}:offset={offset}[{v_saida}]"
        )
        duracao_acumulada = duracao_acumulada + duracoes[i] - dur_corte
        v_atual = v_saida

    # Áudio: mesma lógica de sempre, só que a duração recortada em cada
    # junção agora vem de duracoes_corte (0 pra flash, duracao_slide pros
    # outros) em vez de um único valor global.
    rotulos_audio = []
    for i, dur in enumerate(duracoes):
        corte_esquerda = duracoes_corte[i - 1] if i > 0 else 0.0
        corte_direita = duracoes_corte[i] if i < n - 1 else 0.0
        inicio = corte_esquerda / 2
        fim = dur - corte_direita / 2
        rotulo = f"atrim{i}"
        filtros.append(f"[{i}:a]atrim=start={inicio}:end={fim},asetpts=PTS-STARTPTS[{rotulo}]")
        rotulos_audio.append(rotulo)
    entradas_audio = "".join(f"[{r}]" for r in rotulos_audio)
    filtros.append(f"{entradas_audio}concat=n={len(rotulos_audio)}:v=0:a=1[aout]")

    _rodar([
        "ffmpeg", "-y",
        *entradas,
        "-filter_complex", ";".join(filtros),
        "-map", f"[{v_atual}]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        caminho_saida,
    ])


def concatenar_video_silencioso_com_transicao(caminhos_clipes: list[str], caminho_saida: str):
    """Mesmo esquema de transição de `concatenar_com_transicao` (slide/wipe
    variado + flash raro, tudo via xfade), mas SEM a parte de áudio -- usado
    quando os clipes de entrada não têm narração própria (áudio vem de um
    arquivo externo já pronto, ver `montar_video_de_audio_e_imagens`)."""
    FLASH = "flash"
    pool_transicoes = TRANSICOES_XFADE + [FLASH]
    duracao_slide = 4 / 30
    duracao_flash = 2 / 30

    duracoes = [_duracao_segundos(c) for c in caminhos_clipes]
    n = len(caminhos_clipes)
    tipos_corte = [_RNG_MOVIMENTO.choice(pool_transicoes) for _ in range(n - 1)]
    duracoes_corte = [duracao_flash if t == FLASH else duracao_slide for t in tipos_corte]

    entradas = []
    for caminho in caminhos_clipes:
        entradas += ["-i", caminho]

    filtros = []
    for i in range(n):
        filtros.append(f"[{i}:v]setsar=1[v{i}norm]")

    v_atual = "v0norm"
    duracao_acumulada = duracoes[0]
    for i in range(1, n):
        tipo = tipos_corte[i - 1]
        dur_corte = duracoes_corte[i - 1]
        v_saida = f"v{i}out" if i < n - 1 else "vout"
        offset = max(duracao_acumulada - dur_corte, 0)
        if tipo == FLASH:
            clipe_entrando = f"v{i}norm_flash"
            filtros.append(f"[v{i}norm]eq=brightness=0.9:enable='lte(t,{dur_corte})'[{clipe_entrando}]")
            tipo_xfade = "fade"
        else:
            clipe_entrando = f"v{i}norm"
            tipo_xfade = tipo
        filtros.append(
            f"[{v_atual}][{clipe_entrando}]xfade=transition={tipo_xfade}:duration={dur_corte}:offset={offset}[{v_saida}]"
        )
        duracao_acumulada = duracao_acumulada + duracoes[i] - dur_corte
        v_atual = v_saida

    _rodar([
        "ffmpeg", "-y",
        *entradas,
        "-filter_complex", ";".join(filtros),
        "-map", f"[{v_atual}]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        caminho_saida,
    ])


def _transcrever_palavras(caminho_audio: str) -> list[tuple[float, float, str]]:
    """Transcreve o áudio com timestamp por palavra (faster-whisper) --
    extraído do que já era feito dentro de `gerar_legenda_ass` pra poder
    reaproveitar a MESMA transcrição tanto pra gerar a legenda quanto pra
    detectar pausas de fala (ver `_detectar_pausas_da_fala`), sem rodar o
    Whisper duas vezes no mesmo áudio."""
    from faster_whisper import WhisperModel

    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segmentos, _ = modelo.transcribe(caminho_audio, language="pt", word_timestamps=True)

    palavras = []
    for seg in segmentos:
        for palavra in seg.words:
            palavras.append((palavra.start, palavra.end, palavra.word.strip()))
    return palavras


def _detectar_pausas_da_fala(
    palavras: list[tuple[float, float, str]], duracao_minima: float = 0.15,
) -> list[tuple[float, float]]:
    """Detecta pausas de fala a partir dos timestamps de palavra do Whisper
    (gap entre o fim de uma palavra e o início da próxima), retornando
    (ponto MÉDIO da pausa, duração do gap) pra cada uma -- a duração é o que
    permite depois separar "respiro entre frase do mesmo assunto" de "pausa
    grande entre um assunto/foto e outro" (ver `_calcular_cortes_por_pausa`).

    Usa a TRANSCRIÇÃO em vez de detectar silêncio por volume (ffmpeg
    silencedetect) porque o áudio que o irmão do Davi manda SEMPRE já vem
    com a trilha sonora misturada na narração (confirmado pelo Davi
    2026-09-11) -- a música de fundo nunca deixa o volume cair o bastante
    pra parecer silêncio, então detecção por volume não acharia pausa
    nenhuma. O Whisper detecta palavras faladas mesmo com música por baixo,
    então o GAP entre palavras continua um sinal confiável de pausa real."""
    pausas = []
    for (_, fim_atual, _), (inicio_prox, _, _) in zip(palavras, palavras[1:]):
        gap = inicio_prox - fim_atual
        if gap >= duracao_minima:
            pausas.append(((fim_atual + inicio_prox) / 2, gap))
    return pausas


def _calcular_cortes_por_pausa(
    duracao_total: float, n_imagens: int, pausas: list[tuple[float, float]],
) -> list[float]:
    """Wrapper fino sobre `_pontos_de_corte` que retorna DURAÇÕES por
    imagem em vez dos pontos de corte em si -- ver aquela função pro
    critério de corte (maiores pausas de fala, não tempo ideal)."""
    cortes = _pontos_de_corte(duracao_total, n_imagens, pausas)
    return [cortes[i + 1] - cortes[i] for i in range(n_imagens)]


def _pontos_de_corte(duracao_total: float, n_imagens: int, pausas: list[tuple[float, float]]) -> list[float]:
    """Bug real 2026-09-12 (feedback do Manuel, irmão do Davi, DEPOIS do
    primeiro fix por pausa): "quando ele fala do capotamento do ônibus já
    tá numa imagem muito na frente" -- a 1ª versão desse fix ainda ancorava
    cada corte num tempo IDEAL (divisão igual do total pelo nº de fotos) e
    só ajustava pra pausa mais próxima DENTRO de uma tolerância pequena; se
    a narração real não distribui o tempo igualmente entre as fotos (o
    normal -- ele fala mais de um assunto que de outro), o "ideal" desvia
    cada vez mais da fala real conforme o vídeo avança, e a tolerância
    pequena não alcança mais a pausa certa -- daí o atraso ACUMULA e fica
    pior nas fotos finais, exatamente o sintoma relatado.

    Fix de verdade: ignora o tempo ideal. Assume que ele faz uma pausa mais
    longa entre o que fala de uma foto e o que fala da próxima (parágrafo/
    frase nova) do que as pausas curtas dentro da mesma frase -- então pega
    as (n_imagens - 1) MAIORES pausas detectadas (por duração do gap, não
    por proximidade de um tempo ideal) e usa a ordem CRONOLÓGICA delas como
    os cortes de verdade. Isso deixa o corte de imagem seguir o ritmo real
    da fala em vez de um relógio que não tem nada a ver com o conteúdo.

    Se não tiver pausa suficiente pra achar uma por foto (narração corrida
    demais, ex: menos de n_imagens-1 pausas detectáveis), cai de volta pra
    divisão igual só nesse caso -- melhor que travar, mas não é o caminho
    esperado no dia a dia.

    Retorna a lista de PONTOS (n_imagens + 1 valores, incluindo 0.0 e
    duracao_total) -- usado tanto pra calcular duração por imagem quanto
    pra recortar o texto transcrito de cada trecho (ver
    `_textos_por_segmento`, usado no casamento de conteúdo com
    `_casar_imagens_com_segmentos`).

    Bug real 2026-09-12 (feedback do Manuel, RODADA 2, depois do fix por
    pausa E do fix por conteúdo): "tem umas que tá muito rápido" E o
    casamento do "315" voltou a falhar de novo. Raiz dos dois problemas
    era a MESMA: a 1ª versão deste fix pegava as (n-1) maiores pausas por
    duração do gap e, se sobrasse foto com menos de 2s, EMPURRAVA o corte
    pra um ponto arbitrário -- que na prática não é mais uma pausa real,
    e pior: esses mesmos pontos empurrados eram usados pra recortar o
    TEXTO de cada trecho (`_textos_por_segmento`), corrompendo o texto que
    ia pro casamento por conteúdo (o "315" podia ficar cortado ao meio,
    ou grudado no trecho vizinho). Fix de verdade: exige espaçamento
    mínimo já na HORA DE ESCOLHER os cortes (nunca aceita uma pausa muito
    perto de outra já escolhida), em vez de escolher só pelo tamanho do
    gap e consertar a posição depois -- todo ponto final é sempre uma
    pausa real, então o texto de cada trecho nunca fica corrompido."""
    n_cortes_necessarios = n_imagens - 1
    if n_cortes_necessarios <= 0:
        return [0.0, duracao_total]

    duracao_minima = 2.5
    if duracao_minima * n_imagens > duracao_total:
        duracao_minima = duracao_total / n_imagens

    candidatas = sorted(pausas, key=lambda p: p[1], reverse=True)
    aceitas = []
    for ponto, _gap in candidatas:
        if len(aceitas) >= n_cortes_necessarios:
            break
        if ponto < duracao_minima or ponto > duracao_total - duracao_minima:
            continue
        if all(abs(ponto - outro) >= duracao_minima for outro in aceitas):
            aceitas.append(ponto)

    pontos = [0.0] + sorted(aceitas) + [duracao_total]
    faltam = n_cortes_necessarios - len(aceitas)
    if faltam > 0:
        # Bug real 2026-09-12 (RODADA 3): fallback era tudo-ou-nada -- faltando
        # SÓ 1 pausa bem espaçada de 15 necessárias, jogava fora as 14 boas e
        # caía pra divisão igual no vídeo INTEIRO (por isso o fix de ritmo
        # nunca chegava a valer de verdade). Fix: mantém as pausas reais já
        # aceitas e só preenche o que falta dividindo ao meio o(s) MAIOR(ES)
        # intervalo(s) restante(s) -- só o trecho sem pausa real vira divisão
        # igual, o resto continua alinhado com a fala de verdade.
        print(
            f"  AVISO: só {len(aceitas)}/{n_cortes_necessarios} pausa(s) bem espaçada(s) "
            f"(mínimo {duracao_minima:.1f}s entre fotos) -- completando {faltam} corte(s) "
            "por divisão igual só no(s) trecho(s) sem pausa real."
        )
        for _ in range(faltam):
            maior_i = max(range(len(pontos) - 1), key=lambda i: pontos[i + 1] - pontos[i])
            pontos.insert(maior_i + 1, (pontos[maior_i] + pontos[maior_i + 1]) / 2)

    return pontos


def _textos_por_segmento(palavras: list[tuple[float, float, str]], pontos_de_corte: list[float]) -> list[str]:
    """Junta as palavras transcritas que caem dentro de cada janela de
    tempo definida por `pontos_de_corte`, formando o texto falado
    correspondente a cada imagem -- usado pra casar imagem com o CONTEÚDO
    do que está sendo dito (`_casar_imagens_com_segmentos`), não só o tempo."""
    segmentos = []
    for i in range(len(pontos_de_corte) - 1):
        inicio, fim = pontos_de_corte[i], pontos_de_corte[i + 1]
        texto = " ".join(palavra for (ini_p, _fim_p, palavra) in palavras if inicio <= ini_p < fim)
        segmentos.append(texto)
    return segmentos


def _descrever_imagem_cloudflare(caminho_imagem: str) -> str | None:
    """Descreve o conteúdo de uma foto em poucas palavras via modelo de
    visão da Cloudflare Workers AI (mesma conta já usada pra gerar imagem
    em `gerar_imagens_cloudflare.py`) -- usado pra casar cada foto com o
    trecho da narração que fala sobre ela de verdade, em vez de assumir
    que a ordem numérica do arquivo já é a ordem certa. Retorna None se
    a chamada falhar por qualquer motivo (sem chave configurada, rede,
    cota) -- quem chama trata None como "sem info, mantém ordem original"."""
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not account_id or not token:
        return None

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/llava-hf/llava-1.5-7b-hf"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Bug real 2026-09-12: mandar a foto original (2K) como array de bytes
    # no JSON incha o payload (cada byte vira um número JSON, ~3-4x o
    # tamanho) e a Cloudflare rejeita com 413 "Request is too large" pra
    # boa parte das fotos maiores -- foi por isso que 9 de 16 fotos do
    # ônibus vieram sem descrição e o casamento por conteúdo nunca rodou de
    # verdade. Visão não precisa de resolução alta: redimensiona pro máximo
    # de 768px no lado maior antes de mandar.
    with Image.open(caminho_imagem) as img:
        img = img.convert("RGB")
        if max(img.size) > 768:
            escala = 768 / max(img.size)
            img = img.resize((round(img.width * escala), round(img.height * escala)))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        imagem_bytes = buffer.getvalue()

    # Bug real 2026-09-12: rodando 16 fotos em sequência sem pausa, boa
    # parte das chamadas falhava (provável rate limit da Cloudflare) e
    # `_casar_imagens_com_segmentos` desistia SILENCIOSAMENTE do casamento
    # inteiro assim que via qualquer descrição None -- nenhum dos vídeos
    # até agora teve o casamento por conteúdo aplicado de verdade, e a falha
    # não aparecia em lugar nenhum do log. Retry com backoff (mesmo padrão
    # de `gerar_imagem` em gerar_imagens_cloudflare.py) + aviso explícito
    # quando desiste de verdade, pra nunca mais passar em branco.
    ultimo_erro = None
    for tentativa in range(3):
        try:
            # Esse modelo (diferente do modelo de GERAÇÃO de imagem, que
            # aceita multipart com "files=") só aceita a imagem como array
            # de bytes no corpo JSON -- bug real 2026-09-12: multipart
            # devolvia 400 "Unsupported image data".
            resp = requests.post(
                url, headers=headers,
                json={
                    "image": list(imagem_bytes),
                    "prompt": "Descreva em uma frase curta, em português, o que aparece nesta foto.",
                    "max_tokens": 100,
                },
                timeout=60,
            )
            if resp.status_code != 200:
                ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:200]}"
            else:
                dados = resp.json()
                if not dados.get("success"):
                    ultimo_erro = f"resposta sem sucesso: {dados}"
                else:
                    descricao = dados["result"].get("description", "").strip()
                    if descricao:
                        return descricao
                    ultimo_erro = "descrição vazia"
        except Exception as e:
            ultimo_erro = str(e)

        if tentativa < 2:
            time.sleep(2 * (tentativa + 1))

    print(f"  AVISO: falhou ao descrever {os.path.basename(caminho_imagem)} após 3 tentativas ({ultimo_erro})")
    return None


def _casar_imagens_com_segmentos(segmentos_texto: list[str], descricoes_imagens: list[str | None]) -> list[int]:
    """Pede pro Gemini casar cada trecho de narração (em ordem cronológica)
    com a foto cujo conteúdo combina melhor, em vez de assumir que a ordem
    numérica das fotos já segue a ordem da fala -- pedido do Davi 2026-09-12
    ("junta com a imagem do contexto certo"). Retorna uma lista de índices
    (0-based) com o mesmo tamanho de `segmentos_texto`: `resultado[i]` é o
    índice da foto que deve aparecer no trecho i.

    Se qualquer coisa der errado (sem GEMINI_API_KEY, resposta inválida,
    fotos sem descrição por falha da Cloudflare) cai pra ORDEM NUMÉRICA
    original -- esse casamento é uma melhoria best-effort, nunca pode
    travar a montagem do vídeo."""
    n = len(segmentos_texto)
    ordem_original = list(range(n))
    faltando = [i for i, d in enumerate(descricoes_imagens) if d is None]
    if faltando:
        print(
            f"  AVISO: {len(faltando)}/{n} foto(s) sem descrição (índices {faltando}) -- "
            "casamento por conteúdo cancelado, mantendo ordem numérica."
        )
        return ordem_original

    # Bug real 2026-09-12 (feedback do Manuel, DEPOIS de já ter pedido pro
    # Gemini "priorizar match exato" via instrução no prompt): mesmo com a
    # instrução explícita, o Gemini ainda errava o par óbvio (narração diz
    # "linha 315", foto mostra literalmente "3155" escrito no ônibus) --
    # instrução em texto livre não é GARANTIA nenhuma de comportamento.
    # Fix de verdade: resolve pares de número EXATO (placa, linha, ano etc)
    # em código, de forma determinística, ANTES de chamar o Gemini -- e
    # depois FORÇA esses pares no resultado final não importa o que o
    # Gemini responda. Isso generaliza pra qualquer vídeo (não só esse
    # ônibus): sempre que a narração citar um número que aparece também
    # numa foto, o casamento correto está garantido, não é mais "sorte da
    # IA seguir a instrução".
    pares_fixos = _pares_por_numero_exato(segmentos_texto, descricoes_imagens)

    chave = os.environ.get("GEMINI_API_KEY") or (os.environ.get("GEMINI_API_KEYS", "").split(",") or [None])[0]
    if not chave:
        print("  AVISO: GEMINI_API_KEY não configurada -- casamento por conteúdo (tema) cancelado.")
        return _aplicar_pares_fixos(ordem_original, pares_fixos)

    try:
        from google import genai
        from google.genai import types

        dica_fixos = ""
        if pares_fixos:
            dica_fixos = (
                "\n\nOs seguintes pares JÁ ESTÃO DECIDIDOS por um número/texto idêntico "
                "entre o trecho e a foto -- NÃO mude esses, só decida os outros: "
                + ", ".join(f"trecho {seg} = foto {img}" for seg, img in pares_fixos.items())
            )
        prompt = (
            "Trechos de narração, em ordem cronológica (0-based):\n"
            + "\n".join(f"{i}: {t}" for i, t in enumerate(segmentos_texto))
            + "\n\nFotos disponíveis, com descrição do conteúdo (0-based):\n"
            + "\n".join(f"{i}: {d}" for i, d in enumerate(descricoes_imagens))
            + dica_fixos
            + "\n\nPra cada trecho de narração, diga qual foto combina melhor com a cena/"
            "tema do que está sendo dito. Cada foto deve ser usada EXATAMENTE uma vez. Se "
            "não tiver certeza pra algum trecho, mantenha o índice da foto igual ao índice "
            "do trecho. "
            'Responda só em JSON: {"ordem": [indice_da_foto_pro_trecho_0, indice_da_foto_pro_trecho_1, ...]}'
        )
        client = genai.Client(api_key=chave.strip(), http_options=types.HttpOptions(timeout=60_000))
        ultimo_erro = None
        for tentativa in range(2):
            try:
                resposta = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                dados = json.loads(resposta.text)
                ordem = dados["ordem"]
                if len(ordem) == n and sorted(ordem) == ordem_original:
                    return _aplicar_pares_fixos(ordem, pares_fixos)
                ultimo_erro = f"resposta inválida: {dados}"
            except Exception as e:
                ultimo_erro = e
                if tentativa == 0:
                    time.sleep(3)
        print(f"  AVISO: casamento por tema via Gemini falhou ({ultimo_erro}), usando só os pares por número exato.")
    except Exception as e:
        print(f"  AVISO: casamento por tema via Gemini falhou ({e}), usando só os pares por número exato.")

    return _aplicar_pares_fixos(ordem_original, pares_fixos)


def _pares_por_numero_exato(segmentos_texto: list[str], descricoes_imagens: list[str]) -> dict[int, int]:
    """Casa trecho<->foto de forma DETERMINÍSTICA (sem depender de LLM
    seguir instrução) quando os dois citam o MESMO número de 2+ dígitos
    (linha de ônibus, placa, ano, nº de prédio etc) -- ex: trecho diz "linha
    315", foto descrita como "ônibus com a numeração 3155" (315 é
    substring de 3155). Só usa o par quando é uma correspondência ÚNICA
    (só um trecho e só uma foto compartilham aquele número) -- ambiguidade
    fica pro Gemini decidir por tema, não força um palpite errado."""
    def numeros(texto: str) -> set[str]:
        return set(re.findall(r"\d{2,}", texto))

    numeros_por_segmento = [numeros(t) for t in segmentos_texto]
    numeros_por_imagem = [numeros(d) for d in descricoes_imagens]

    pares = {}
    fotos_usadas = set()
    for i, nums_seg in enumerate(numeros_por_segmento):
        if not nums_seg:
            continue
        candidatos = [
            j for j, nums_img in enumerate(numeros_por_imagem)
            if nums_img and any(a in b or b in a for a in nums_seg for b in nums_img)
        ]
        if len(candidatos) == 1 and candidatos[0] not in fotos_usadas:
            pares[i] = candidatos[0]
            fotos_usadas.add(candidatos[0])
    return pares


def _aplicar_pares_fixos(ordem: list[int], pares_fixos: dict[int, int]) -> list[int]:
    """Força os pares determinísticos (`_pares_por_numero_exato`) no
    resultado final, trocando de lugar o que for preciso pra manter uma
    permutação válida -- garante o match exato não importa o que o Gemini
    (ou a ordem numérica de fallback) tenha decidido."""
    ordem = list(ordem)
    for segmento, foto in pares_fixos.items():
        if ordem[segmento] == foto:
            continue
        posicao_atual = ordem.index(foto)
        ordem[posicao_atual], ordem[segmento] = ordem[segmento], ordem[posicao_atual]
    return ordem


def montar_video_de_audio_e_imagens(
    caminho_audio: str, imagens: list[str], caminho_saida: str, plataforma: str = "tiktok",
) -> float:
    """Monta o vídeo final a partir de uma narração JÁ PRONTA (mp3/wav já
    com trilha embutida, gerado fora daqui) + uma lista de imagens numeradas
    já aprovadas -- caminho pro fluxo novo (2026-09-10) onde o roteiro/
    imagem/voz vêm de outro workflow (feito pelo irmão do Davi, formato
    fixo: fotos enumeradas 1, 2, 3... + um único áudio narrando com trilha
    já misturada) e esse pipeline só cuida da EDIÇÃO.

    A troca de imagem NÃO usa divisão igual de tempo (duração total / nº de
    fotos) -- feedback real do irmão do Davi 2026-09-11/12 ("a imagem não
    acompanha o áudio, fala uma coisa e mostra outra" / "quando fala do
    capotamento já tá numa imagem muito na frente"): se a narração não fala
    o mesmo tempo sobre cada foto, divisão igual desalinha e o erro vai
    acumulando (pior nas fotos finais). Em vez disso, transcreve o áudio
    (Whisper, único jeito confiável de achar pausa de fala aqui porque o
    áudio já vem com trilha embutida -- detecção de silêncio por volume não
    funcionaria) e usa as (nº de fotos - 1) MAIORES pausas de fala, em ordem
    cronológica, como os cortes de imagem -- sem ancorar num tempo ideal
    (ver `_detectar_pausas_da_fala`/`_pontos_de_corte`).

    Além do RITMO do corte, também casa o CONTEÚDO: descreve cada foto via
    visão computacional (Cloudflare Workers AI) e pede pro Gemini casar cada
    trecho de narração com a foto que combina melhor (pedido do Davi
    2026-09-12: "junta com a imagem do contexto certo", não só assumir que a
    ordem numérica do arquivo já é a ordem da fala) -- ver
    `_descrever_imagem_cloudflare`/`_casar_imagens_com_segmentos`. Se a
    visão ou o casamento falharem por qualquer motivo, cai pra ordem
    numérica original (nunca trava a montagem por causa disso).

    Aplica o mesmo Ken Burns variado + tremida + personagem_cresce de sempre
    (`gerar_clipe_imagem_silencioso`), concatena com a mesma transição
    variada (slide/wipe + flash raro), queima legenda transcrita do áudio
    (reaproveitando a MESMA transcrição, sem rodar o Whisper 2x) e mixa a
    ambientação/trilha por cima -- tudo reaproveitado do fluxo normal, só
    sem gerar roteiro/narração/imagem aqui dentro.

    Retorna a duração total do vídeo (= duração do áudio de entrada)."""
    import random as _random_stdlib

    duracao_total = _duracao_segundos(caminho_audio)

    print("Transcrevendo áudio pra sincronizar corte de imagem com a fala...")
    palavras = _transcrever_palavras(caminho_audio)
    pausas = _detectar_pausas_da_fala(palavras)
    pontos_de_corte = _pontos_de_corte(duracao_total, len(imagens), pausas)
    duracoes_por_imagem = [pontos_de_corte[i + 1] - pontos_de_corte[i] for i in range(len(imagens))]

    print("Descrevendo fotos pra casar com o trecho certo da narração...")
    descricoes_imagens = [_descrever_imagem_cloudflare(img) for img in imagens]
    segmentos_texto = _textos_por_segmento(palavras, pontos_de_corte)
    ordem_por_conteudo = _casar_imagens_com_segmentos(segmentos_texto, descricoes_imagens)
    if ordem_por_conteudo != list(range(len(imagens))):
        print(f"  ordem ajustada pelo conteúdo: {ordem_por_conteudo}")
    imagens = [imagens[i] for i in ordem_por_conteudo]

    with tempfile.TemporaryDirectory() as pasta_tmp:
        pesos_movimento = [3] * len(TIPOS_MOVIMENTO) + [13]
        clipes = []
        for i, (imagem, duracao_imagem) in enumerate(zip(imagens, duracoes_por_imagem)):
            tipo_movimento = _RNG_MOVIMENTO.choices(
                TIPOS_MOVIMENTO + ["personagem_cresce"], weights=pesos_movimento
            )[0]
            caminho_clipe = os.path.join(pasta_tmp, f"clipe{i}.mp4")
            gerar_clipe_imagem_silencioso(imagem, duracao_imagem, caminho_clipe, tipo_movimento)
            clipes.append(caminho_clipe)

        print("Concatenando imagens (com transição fluida entre elas)...")
        caminho_bruto = os.path.join(pasta_tmp, "bruto.mp4")
        concatenar_video_silencioso_com_transicao(clipes, caminho_bruto)

        print("Juntando com a narração...")
        # Bug real 2026-09-11 (Davi: "a narração tem dois e cinco e o vídeo
        # dois e três"): as transições cortam alguns frames a cada corte
        # (ver concatenar_video_silencioso_com_transicao), então o vídeo
        # monttado sempre sai um pouco MAIS CURTO que o áudio original.
        # "-shortest" cortava o que sobrava do ÁUDIO pra bater com o vídeo
        # -- ou seja, cortava a narração de verdade, não só o enquadramento.
        # Fix: em vez de encurtar o áudio, estica o vídeo segurando o
        # último frame (congelado) até bater a duração exata do áudio --
        # nunca perde uma palavra da narração.
        # Bug real 2026-09-11 (2ª vez, corte de ~0.6s mesmo com o fix acima):
        # `format=duration` do ffprobe em MP3 é só uma ESTIMATIVA (cabeçalho
        # VBR impreciso) -- o áudio de verdade, decodificado, pode ser mais
        # longo que essa estimativa. Com a margem exata calculada, o vídeo
        # ainda saía um pouco mais curto que o áudio real, e o "-shortest"
        # voltava a cortar esse restinho de narração. Fix: soma uma margem
        # de segurança (2s) no padding -- garante que o vídeo sempre fica
        # MAIS longo que o áudio de verdade, e o "-shortest" corta o excesso
        # de VÍDEO (silêncio congelado sobrando), nunca a narração.
        MARGEM_SEGURANCA = 2.0
        duracao_video_bruto = _duracao_segundos(caminho_bruto)
        diferenca = duracao_total - duracao_video_bruto + MARGEM_SEGURANCA
        filtro_video = f"[0:v]tpad=stop_mode=clone:stop_duration={diferenca:.3f}[v]"
        caminho_com_audio = os.path.join(pasta_tmp, "com_audio.mp4")
        _rodar([
            "ffmpeg", "-y", "-i", caminho_bruto, "-i", caminho_audio,
            "-filter_complex", filtro_video,
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest",
            caminho_com_audio,
        ])

        print("Gerando legenda (reaproveitando a transcrição feita pro sincronismo)...")
        caminho_ass = os.path.join(pasta_tmp, "legenda.ass")
        gerar_legenda_ass(caminho_audio, caminho_ass, LARGURA, ALTURA, palavras=palavras)

        print("Queimando legenda no vídeo...")
        caminho_com_legenda = os.path.join(pasta_tmp, "com_legenda.mp4")
        queimar_legenda(caminho_com_audio, caminho_ass, caminho_com_legenda)

        caminho_trilha = TRILHAS_POR_PLATAFORMA.get(plataforma)
        print(f"Adicionando ambientação ({plataforma})...")
        caminho_ambiencia = os.path.join(pasta_tmp, "ambiencia.wav")
        gerar_ambiencia(caminho_ambiencia, duracao_total, "tenso", caminho_trilha)

        # Bug real 2026-09-11 (2ª causa raiz do corte de ~0.6s no final da
        # narração, achado depurando o pivô passo a passo): misturar áudio
        # (filter_complex) E reencodar vídeo (libx264) NA MESMA chamada do
        # ffmpeg perde ~0.6s de áudio -- confirmado isolando cada etapa:
        # o mesmo filtro de áudio sozinho (sem vídeo) dá a duração certa,
        # e com "-c:v copy" (sem reencodar) também dá certo; só quebra
        # quando os dois acontecem juntos na mesma chamada (bug/instabili-
        # dade do libx264 processando junto com o filtergraph de áudio).
        # O reencode de vídeo daqui tinha sido adicionado 2026-09-10 achando
        # que corrigia o truncamento do xfade (não corrigia -- a causa real
        # daquele era arredondamento de frame no offset do xfade, já
        # corrigido em concatenar_com_transicao). Sem motivo real pra
        # reencodar aqui, então volta pra "-c:v copy" -- mais rápido E sem
        # o bug de áudio.
        _rodar([
            "ffmpeg", "-y",
            "-i", caminho_com_legenda, "-i", caminho_ambiencia,
            "-filter_complex",
            "[0:a]volume=1.8[a0];[a0][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]",
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
            f"pra {duracao_total:.1f}s de áudio esperado. Bug conhecido no xfade encadeado -- "
            "não usar esse arquivo, precisa remontar."
        )
    # Trava extra 2026-09-11: o bug real desta vez não era no VÍDEO (frame
    # count batia certinho), era a NARRAÇÃO sendo cortada no fim por causa
    # do "-shortest" -- contagem de frame de vídeo sozinha não pega isso,
    # tem que conferir a duração do stream de ÁUDIO do arquivo final contra
    # o áudio de entrada de verdade. Fluxo automático (pivô via Drive) não
    # pode publicar nada com narração cortada sem ninguém perceber.
    duracao_audio_final = _duracao_segundos_stream_audio(caminho_saida)
    duracao_audio_fonte = _duracao_segundos(caminho_audio)
    if duracao_audio_final < duracao_audio_fonte - 0.5:
        raise RuntimeError(
            f"Narração saiu cortada: áudio final tem {duracao_audio_final:.1f}s, "
            f"a narração original tem {duracao_audio_fonte:.1f}s -- não usar esse arquivo, "
            "precisa remontar."
        )
    print(f"\nVídeo salvo em: {caminho_saida} ({duracao_real:.1f}s de vídeo, {duracao_audio_final:.1f}s de áudio, verificado)")
    return duracao_total


def extrair_audio(caminho_video: str, caminho_saida: str):
    _rodar(["ffmpeg", "-y", "-i", caminho_video, "-vn", "-acodec", "pcm_s16le", caminho_saida])




def _formatar_tempo_ass(segundos: float) -> str:
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = segundos % 60
    cs = int((s - int(s)) * 100)
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def gerar_legenda_ass(
    caminho_audio: str, caminho_saida_ass: str, largura: int, altura: int,
    palavras: list[tuple[float, float, str]] | None = None,
):
    """`palavras` opcional -- se quem chamou já transcreveu o áudio pra
    outro fim (ex: sincronismo de imagem no fluxo pivô, ver
    `_transcrever_palavras`), passa aqui pra não rodar o Whisper de novo no
    mesmo áudio."""
    if palavras is None:
        palavras = _transcrever_palavras(caminho_audio)

    cabecalho = f"""[Script Info]
PlayResX: {largura}
PlayResY: {altura}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Legenda,Arial Black,84,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,6,0,2,60,60,800,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # Uma palavra por vez, centro-baixo da tela (~58% da altura, MarginV
    # medido de baixo pra cima) -- padrão observado no canal de referência
    # "Contos Urbanos" (@vulto_137, ver gravação de tela 2026-09-08):
    # palavra única, grande, branca com contorno preto grosso, sem bloco de
    # frase nem destaque de cor (isso era o padrão CapCut anterior).
    linhas = []
    for inicio, fim, palavra in palavras:
        texto = palavra.strip().upper()
        linhas.append(
            f"Dialogue: 0,{_formatar_tempo_ass(inicio)},{_formatar_tempo_ass(fim)},"
            f"Legenda,,0,0,0,,{texto}"
        )

    with open(caminho_saida_ass, "w", encoding="utf-8") as f:
        f.write(cabecalho)
        f.write("\n".join(linhas))


def queimar_legenda(caminho_video: str, caminho_ass: str, caminho_saida: str):
    """Queima a legenda E aplica os efeitos visuais constantes de "analog
    horror" no vídeo inteiro -- padrão observado no canal de referência
    "Contos Urbanos" (@vulto_137): aberração cromática (rgbashift) + agora
    também um leve visual de fita VHS (scanline sutil, cor levemente lavada
    com flicker, chromashift extra discreto) -- testado com o Davi em
    2026-09-09 ("ficou top") numa versão leve, sem o ruído/blur pesado da
    primeira tentativa (que multiplicava o tamanho do arquivo por 9x).
    Tudo roda ANTES de queimar a legenda, pra o texto continuar nítido (só
    a imagem por baixo recebe os efeitos)."""
    caminho_ass_escapado = caminho_ass.replace(":", "\\:")
    filtro_vhs = (
        "rgbashift=rh=-3:bh=3,"
        "chromashift=crh=-1:cbh=1,"
        "eq=contrast=1.05:saturation=0.85:brightness='0.01+0.008*sin(2*PI*t*6)':gamma_g=1.03:eval=frame,"
        "drawgrid=w=iw:h=6:t=1:color=black@0.06,"
        "vignette=PI/6"
    )
    _rodar([
        "ffmpeg", "-y", "-i", caminho_video,
        "-vf", f"{filtro_vhs},ass={caminho_ass_escapado}",
        "-c:a", "copy", caminho_saida,
    ])


def montar_video(
    roteiro: dict, canal, pasta_imagens: str, saida: str, sem_legenda: bool = False,
    plataformas: list[str] | None = None,
) -> float:
    """Monta o vídeo final a partir do roteiro + imagens aprovadas. Retorna a
    duração total narrada (segundos) — o chamador (CLI ou pipeline
    automatizado) decide o que fazer se ficar abaixo dos 60s exigidos."""
    import random

    genero_narrador = roteiro.get("genero_narrador", "masculino")
    voz = canal.VOZES_LOCAIS.get(genero_narrador, next(iter(canal.VOZES_LOCAIS.values())))
    nome_variante = random.choice(list(VARIANTES_PITCH.keys()))
    fator_pitch = VARIANTES_PITCH[nome_variante]
    print(f"Narrador: {genero_narrador} (voz Kokoro: {voz}, variante: {nome_variante})\n")

    with tempfile.TemporaryDirectory() as pasta_tmp:
        # SFX de whoosh removido (feedback 2026-09-08: soava como chiado/
        # estática nos cortes de imagem dentro da cena, "ficou horrível").
        caminho_sfx = None

        clipes = []
        duracao_total = 0.0
        for i, cena in enumerate(roteiro["cenas"], start=1):
            imagens = _imagens_da_cena(pasta_imagens, i)

            print(f"Cena {i}: gerando narração ({len(imagens)} imagem(ns))...")
            caminho_audio = os.path.join(pasta_tmp, f"audio{i}.wav")
            gerar_narracao(cena["narracao"], voz, caminho_audio)
            aplicar_variante_pitch(caminho_audio, fator_pitch)
            duracao = _duracao_segundos(caminho_audio)
            duracao_total += duracao

            print(f"Cena {i}: montando clipe ({duracao:.1f}s)...")
            caminho_clipe = os.path.join(pasta_tmp, f"clipe{i}.mp4")
            gerar_clipe_cena(imagens, caminho_audio, duracao, caminho_clipe, pasta_tmp, caminho_sfx=caminho_sfx)
            clipes.append(caminho_clipe)

        if duracao_total < 60:
            print(
                f"\nAVISO: narração total ficou em {duracao_total:.1f}s — abaixo dos 60s exigidos "
                "pra monetização no TikTok. O roteiro precisa de cenas mais longas.\n"
            )

        print("Montando tela final (curta e se inscreva)...")
        caminho_cta = os.path.join(pasta_tmp, "cta_final.mp4")
        gerar_cta_final(caminho_cta)

        # A tela final de "curta e se inscreva/ativa o sininho" é conceito
        # de YouTube -- TikTok não tem sino de notificação, incluir isso lá
        # soa estranho/fora de contexto (feedback 2026-09-10). Por isso
        # concatena e legenda DUAS vezes (uma por plataforma) em vez de uma
        # vez só reaproveitada -- mais caro que o esquema antigo (que só
        # repetia a mixagem de áudio barata no final), mas é o preço de ter
        # o CTA só onde faz sentido.
        plataformas_ativas = plataformas or ["youtube", "tiktok"]
        clipes_por_plataforma = {
            "youtube": clipes + [caminho_cta],
            "tiktok": clipes,
        }
        clipes_por_plataforma = {p: c for p, c in clipes_por_plataforma.items() if p in plataformas_ativas}

        caminhos_com_legenda = {}
        for plataforma, lista_clipes in clipes_por_plataforma.items():
            print(f"Concatenando cenas ({plataforma}, com transição fluida entre elas)...")
            caminho_bruto = os.path.join(pasta_tmp, f"bruto_{plataforma}.mp4")
            concatenar_com_transicao(lista_clipes, caminho_bruto)

            caminho_com_legenda = os.path.join(pasta_tmp, f"com_legenda_{plataforma}.mp4")
            if sem_legenda:
                caminho_com_legenda = caminho_bruto
            else:
                print(f"Transcrevendo áudio ({plataforma}) pra gerar legenda (faster-whisper, pode demorar um pouco)...")
                caminho_audio_full = os.path.join(pasta_tmp, f"audio_full_{plataforma}.wav")
                extrair_audio(caminho_bruto, caminho_audio_full)
                caminho_ass = os.path.join(pasta_tmp, f"legenda_{plataforma}.ass")
                gerar_legenda_ass(caminho_audio_full, caminho_ass, LARGURA, ALTURA)

                print(f"Queimando legenda no vídeo ({plataforma})...")
                queimar_legenda(caminho_bruto, caminho_ass, caminho_com_legenda)

            caminhos_com_legenda[plataforma] = caminho_com_legenda

        perfil_ambiencia = getattr(canal, "AMBIENCIA", "leve")

        # Decisão 2026-09-09: trilha real só no canal "Arquivo Sombrio"
        # (terror) -- "Em Alta" (tendencias) continua com a ambientação
        # sintetizada, canal.USAR_TRILHA_REAL controla isso por canal.
        usar_trilha_real = getattr(canal, "USAR_TRILHA_REAL", True)

        base, ext = os.path.splitext(saida)
        caminhos_finais = {}
        for plataforma, caminho_trilha in TRILHAS_POR_PLATAFORMA.items():
            if plataforma not in plataformas_ativas:
                continue
            if not usar_trilha_real:
                caminho_trilha = None
            caminho_com_legenda = caminhos_com_legenda[plataforma]
            duracao_total_video = _duracao_segundos(caminho_com_legenda)
            print(f"Adicionando ambientação ({plataforma}, {perfil_ambiencia})...")
            caminho_ambiencia = os.path.join(pasta_tmp, f"ambiencia_{plataforma}.wav")
            gerar_ambiencia(caminho_ambiencia, duracao_total_video, perfil_ambiencia, caminho_trilha)
            caminho_saida_plataforma = f"{base}_{plataforma}{ext}"
            _rodar([
                "ffmpeg", "-y",
                "-i", caminho_com_legenda, "-i", caminho_ambiencia,
                # amix normaliza (divide o volume) por padrão -- sem normalize=0
                # e sem reforçar a narração antes, o narrador saía pela metade
                # do volume só por causa da mixagem (feedback 2026-09-08:
                # "narrador muito baixo").
                "-filter_complex",
                "[0:a]volume=1.8[a0];[a0][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]",
                "-map", "0:v", "-map", "[aout]",
                # -c:v copy: a causa real do truncamento do Somerton
                # (2026-09-10) era arredondamento de frame no offset do
                # xfade encadeado, já corrigido em concatenar_com_transicao
                # -- reencodar vídeo aqui não corrigia aquilo (confirmado
                # testando). E reencodar vídeo (libx264) JUNTO com o filtro
                # de mixagem de áudio nessa mesma chamada causa um bug
                # DIFERENTE, achado 2026-09-11 depurando o fluxo do pivô:
                # perde uns 0.6s do fim do ÁUDIO (confirmado isolando cada
                # etapa -- só acontece quando os dois rodam juntos). Sem
                # motivo real pra reencodar vídeo aqui, "-c:v copy" evita os
                # dois problemas.
                "-c:v", "copy", "-c:a", "aac",
                # +faststart move o moov atom pro início do arquivo -- TikTok/
                # YouTube conseguem começar a tocar sem baixar o mp4 inteiro
                # primeiro (aprovado 2026-09-09, nível 1 item 2).
                "-movflags", "+faststart",
                caminho_saida_plataforma,
            ])
            caminhos_finais[plataforma] = caminho_saida_plataforma

        # Mantém o caminho `saida` original como alias da versão do YouTube
        # (compatibilidade com quem só espera um arquivo, ex: CLI antiga).
        if "youtube" in caminhos_finais:
            shutil.copyfile(caminhos_finais["youtube"], saida)

    # Trava de segurança 2026-09-11: o vídeo do Somerton Man saiu publicado
    # duas vezes com metade do conteúdo cortado (bug real no xfade
    # encadeado, ainda não 100% raiz-causado) sem NENHUM erro/aviso -- o
    # arquivo saía, ffprobe reportava duração normal no nível do container,
    # mas os frames de vídeo de verdade acabavam bem antes do áudio. Confere
    # aqui com CONTAGEM DE FRAMES real (não só metadata, que mentiu nos dois
    # casos) se o vídeo final bate com o esperado antes de deixar
    # `pipeline_completo.py` aprovar e publicar sozinho.
    for plataforma, caminho in caminhos_finais.items():
        fps_saida = 30
        frames_reais = _contar_frames_reais(caminho)
        duracao_real = frames_reais / fps_saida
        # Tolerância de 20% pra cobrir os cortes normais das transições
        # (cada corte tira uns 4 frames) e o CTA extra no youtube.
        if duracao_real < duracao_total * 0.8:
            raise RuntimeError(
                f"Vídeo {plataforma} saiu truncado: {duracao_real:.1f}s reais de vídeo "
                f"({frames_reais} frames) pra {duracao_total:.1f}s de narração esperada. "
                "Bug conhecido no xfade encadeado (ver concatenar_com_transicao) -- "
                "não publica isso, precisa remontar."
            )
        print(f"\nVídeo {plataforma} salvo em: {caminho} ({duracao_real:.1f}s reais, verificado)")
    return duracao_total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canal", default="terror")
    parser.add_argument("--roteiro", default=None)
    parser.add_argument("--imagens", default=None)
    parser.add_argument("--saida", default="video_final.mp4")
    parser.add_argument("--sem-legenda", action="store_true")
    # Fluxo novo (2026-09-10): áudio + imagens já prontos de outro workflow,
    # esse script só cuida da edição (transição, tremida, legenda, trilha).
    parser.add_argument("--audio", default=None, help="narração já pronta (mp3/wav) -- ativa o modo 'só edição'")
    parser.add_argument("--plataforma", default="tiktok", choices=["tiktok", "youtube"])
    args = parser.parse_args()

    if args.audio:
        pasta_imagens = args.imagens
        if not pasta_imagens:
            raise SystemExit("--imagens é obrigatório junto com --audio (pasta com as fotos, em ordem)")
        # Bug real encontrado 2026-09-10 durante o teste com o Davi: sorted()
        # comum ordena "img10.jpeg" ANTES de "img2.jpeg" (ordem alfabética
        # de string, não numérica) -- com 20 fotos (img1..img20) isso
        # embaralhava a ordem certinha a partir da décima foto. Ordena pela
        # sequência de dígitos no nome do arquivo (numérica de verdade).
        def _chave_ordenacao(nome_arquivo: str):
            numeros = re.findall(r"\d+", nome_arquivo)
            return (int(numeros[0]), nome_arquivo) if numeros else (float("inf"), nome_arquivo)

        nomes = sorted(
            (f for f in os.listdir(pasta_imagens) if f.lower().endswith((".jpg", ".jpeg", ".png"))),
            key=_chave_ordenacao,
        )
        if not nomes:
            raise SystemExit(f"nenhuma imagem encontrada em {pasta_imagens}")
        imagens = [os.path.join(pasta_imagens, n) for n in nomes]
        print(f"{len(imagens)} imagens encontradas, ordem: {nomes}")
        montar_video_de_audio_e_imagens(args.audio, imagens, args.saida, plataforma=args.plataforma)
        return

    if not args.roteiro:
        raise SystemExit("--roteiro é obrigatório (ou use --audio pro modo 'só edição')")

    canal = carregar_canal(args.canal)
    pasta_imagens = args.imagens or canal.PASTA_IMAGENS

    with open(args.roteiro, encoding="utf-8") as f:
        roteiro = json.load(f)

    montar_video(roteiro, canal, pasta_imagens, args.saida, sem_legenda=args.sem_legenda)


if __name__ == "__main__":
    main()
