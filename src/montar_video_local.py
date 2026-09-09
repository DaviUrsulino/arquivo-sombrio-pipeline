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
import json
import os
import random
import shutil
import subprocess
import tempfile

import soundfile as sf

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

# Trilhas reais livres de direitos autorais, uma por plataforma (Davi
# escolheu manualmente, 2026-09-09) -- vídeo idêntico em tudo, só a
# mixagem final de áudio muda entre as duas versões geradas.
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

# Tipos de transição do xfade sorteados por corte entre cenas (ver
# concatenar_com_transicao) -- nomes nativos do ffmpeg, sem precisar de
# filtro customizado. Mistura arrastar de lado/cima com dissolve, pra não
# ficar só "arrastando" toda hora nem só "esmaecendo" toda hora.
TRANSICOES_XFADE = [
    "fade", "dissolve",
    "slideleft", "slideright", "slideup", "slidedown",
    "wipeleft", "wiperight", "wipeup",
]
# "personagem_cresce" fica de fora da lista principal (sorteado com peso
# menor em gerar_clipe_cena) porque depende de rembg (CPU, mais lento) e
# tem fallback pra zoom_in se a extração falhar -- não deve ser o padrão.


def _extrair_personagem_rgba(caminho_imagem: str, caminho_saida_png: str):
    """Remove o fundo da imagem (rembg, CPU, sem GPU/Modal) deixando só o
    personagem opaco num PNG do mesmo tamanho da imagem original (RGBA,
    fundo transparente) -- usado pelo movimento "personagem_cresce" pra dar
    a sensação de personagem "recortado tipo figurinha" crescendo sozinho
    enquanto o fundo fica parado (feedback 2026-09-09, referência real de
    editores desse nicho)."""
    from rembg import remove
    from PIL import Image

    imagem = Image.open(caminho_imagem).convert("RGB")
    resultado = remove(imagem)
    resultado.save(caminho_saida_png)


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
            with tempfile.TemporaryDirectory() as pasta_tmp_fg:
                caminho_png = os.path.join(pasta_tmp_fg, "personagem.png")
                _extrair_personagem_rgba(caminho_imagem, caminho_png)
                _rodar([
                    "ffmpeg", "-y",
                    "-loop", "1", "-i", caminho_imagem,   # fundo (imagem original, parado)
                    "-loop", "1", "-i", caminho_png,      # personagem recortado (RGBA)
                    "-filter_complex",
                    (
                        f"[0:v]scale=w={LARGURA}:h={ALTURA}:force_original_aspect_ratio=increase,"
                        f"crop={LARGURA}:{ALTURA}[bg];"
                        f"[1:v]format=rgba,"
                        f"scale=w={LARGURA}:h={ALTURA}:force_original_aspect_ratio=increase:eval=frame,"
                        f"crop={LARGURA}:{ALTURA},"
                        # cresce ~22% ao longo do clipe, a partir do centro
                        f"scale=w='iw*(1+0.22*t/{duracao})':h='ih*(1+0.22*t/{duracao})':eval=frame[fg];"
                        f"[bg][fg]overlay=(W-w)/2:(H-h)/2:eval=frame[v]"
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
        # "personagem_cresce" (rembg) DESATIVADO DE NOVO 2026-09-09 -- deu
        # OOM local (código 137) E depois estourou o disco do runner do
        # GitHub Actions (rembg/onnxruntime puxaram pacotes CUDA gigantes
        # sem necessidade, "No space left on device", quebrando o cron
        # inteiro). Precisa de uma abordagem mais leve (torch CPU-only
        # explícito, ou outra lib sem essa pegada) antes de tentar de novo.
        tipo_movimento = random.choice(TIPOS_MOVIMENTO)
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


def concatenar_com_transicao(
    caminhos_clipes: list[str], caminho_saida: str, duracao_transicao: float = 0.4,
):
    """Concatena as cenas com dissolve suave no VÍDEO (xfade), mas com corte
    seco no ÁUDIO perto de cada junção (sem crossfade de áudio).

    Importante: crossfade de ÁUDIO com FALA (acrossfade) soa mal — é duas
    narrações diferentes tocando ao mesmo tempo por uma fração de segundo,
    o que o ouvido percebe como chiado/interferência, não como transição
    suave (feedback real de usuário, 2026-09-08). Em vez disso, cada
    junção recorta uma fatia curta (duracao_transicao) perto do corte —
    metade do fim de uma cena, metade do começo da próxima — e concatena
    sem sobrepor. Isso remove o mesmo tanto de tempo que o xfade de vídeo
    remove (mantém vídeo e áudio com a mesma duração final), só que sem
    misturar as duas falas."""
    duracoes = [_duracao_segundos(c) for c in caminhos_clipes]
    metade = duracao_transicao / 2

    entradas = []
    for caminho in caminhos_clipes:
        entradas += ["-i", caminho]

    filtros = []

    # Vídeo: transição encadeada, tipo sorteado por corte (arrasta lado,
    # sobe, dissolve) em vez de sempre o mesmo "fade" -- feedback
    # 2026-09-09: transição sempre igual não tinha a "fluidez" que
    # referências reais do nicho usam entre um corte e outro.
    v_atual = "0:v"
    duracao_acumulada = duracoes[0]
    for i in range(1, len(caminhos_clipes)):
        offset = max(duracao_acumulada - duracao_transicao, 0)
        v_saida = f"v{i}" if i < len(caminhos_clipes) - 1 else "vout"
        tipo_transicao = random.choice(TRANSICOES_XFADE)
        filtros.append(
            f"[{v_atual}][{i}:v]xfade=transition={tipo_transicao}:duration={duracao_transicao}:offset={offset}[{v_saida}]"
        )
        v_atual = v_saida
        duracao_acumulada = duracao_acumulada + duracoes[i] - duracao_transicao

    # Áudio: apara uma fatia curta perto de cada junção (sem misturar) e
    # concatena — remove o mesmo total de tempo que o vídeo, mantendo os
    # dois sincronizados, sem sobrepor duas falas.
    rotulos_audio = []
    for i, dur in enumerate(duracoes):
        inicio = metade if i > 0 else 0
        fim = dur - metade if i < len(duracoes) - 1 else dur
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


def extrair_audio(caminho_video: str, caminho_saida: str):
    _rodar(["ffmpeg", "-y", "-i", caminho_video, "-vn", "-acodec", "pcm_s16le", caminho_saida])




def _formatar_tempo_ass(segundos: float) -> str:
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = segundos % 60
    cs = int((s - int(s)) * 100)
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def gerar_legenda_ass(caminho_audio: str, caminho_saida_ass: str, largura: int, altura: int):
    from faster_whisper import WhisperModel

    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segmentos, _ = modelo.transcribe(caminho_audio, language="pt", word_timestamps=True)

    palavras = []
    for seg in segmentos:
        for palavra in seg.words:
            palavras.append((palavra.start, palavra.end, palavra.word.strip()))

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
    """Queima a legenda E aplica aberração cromática sutil e constante no
    vídeo inteiro -- padrão observado no canal de referência "Contos
    Urbanos" (@vulto_137): o efeito aparece em TODO frame, não só em
    momentos de choque, então é filtro de vídeo (ffmpeg puro, sem custo de
    imagem/GPU), não instrução de prompt pro gerador de imagem.
    `rgbashift` roda ANTES de queimar a legenda, pra o texto continuar
    nítido (só a imagem por baixo ganha a franja de cor)."""
    caminho_ass_escapado = caminho_ass.replace(":", "\\:")
    _rodar([
        "ffmpeg", "-y", "-i", caminho_video,
        "-vf", f"rgbashift=rh=-3:bh=3,ass={caminho_ass_escapado}",
        "-c:a", "copy", caminho_saida,
    ])


def montar_video(roteiro: dict, canal, pasta_imagens: str, saida: str, sem_legenda: bool = False) -> float:
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
        clipes.append(caminho_cta)

        print("Concatenando cenas (com transição fluida entre elas)...")
        caminho_bruto = os.path.join(pasta_tmp, "bruto.mp4")
        concatenar_com_transicao(clipes, caminho_bruto)

        caminho_com_legenda = os.path.join(pasta_tmp, "com_legenda.mp4")
        if sem_legenda:
            caminho_com_legenda = caminho_bruto
        else:
            print("Transcrevendo áudio pra gerar legenda (faster-whisper, pode demorar um pouco)...")
            caminho_audio_full = os.path.join(pasta_tmp, "audio_full.wav")
            extrair_audio(caminho_bruto, caminho_audio_full)
            caminho_ass = os.path.join(pasta_tmp, "legenda.ass")
            gerar_legenda_ass(caminho_audio_full, caminho_ass, LARGURA, ALTURA)

            print("Queimando legenda no vídeo...")
            queimar_legenda(caminho_bruto, caminho_ass, caminho_com_legenda)

        perfil_ambiencia = getattr(canal, "AMBIENCIA", "leve")
        duracao_total_video = _duracao_segundos(caminho_com_legenda)

        # Gera UMA versão do vídeo por plataforma (TikTok/YouTube), cada
        # uma com sua própria trilha real -- tudo até aqui (imagens,
        # narração, legenda, cortes) já rodou uma vez só, então isso não
        # dobra o custo/tempo pesado, só repete a etapa barata de mixar
        # áudio no final (feedback 2026-09-09).
        base, ext = os.path.splitext(saida)
        caminhos_finais = {}
        for plataforma, caminho_trilha in TRILHAS_POR_PLATAFORMA.items():
            print(f"Adicionando trilha real ({plataforma}, {perfil_ambiencia})...")
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
                "-c:v", "copy", "-c:a", "aac",
                caminho_saida_plataforma,
            ])
            caminhos_finais[plataforma] = caminho_saida_plataforma

        # Mantém o caminho `saida` original como alias da versão do YouTube
        # (compatibilidade com quem só espera um arquivo, ex: CLI antiga).
        shutil.copyfile(caminhos_finais["youtube"], saida)

    print(f"\nVídeo YouTube salvo em: {caminhos_finais['youtube']}")
    print(f"Vídeo TikTok salvo em: {caminhos_finais['tiktok']} (custo: R$0,00)")
    return duracao_total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canal", default="terror")
    parser.add_argument("--roteiro", required=True)
    parser.add_argument("--imagens", default=None)
    parser.add_argument("--saida", default="video_final.mp4")
    parser.add_argument("--sem-legenda", action="store_true")
    args = parser.parse_args()

    canal = carregar_canal(args.canal)
    pasta_imagens = args.imagens or canal.PASTA_IMAGENS

    with open(args.roteiro, encoding="utf-8") as f:
        roteiro = json.load(f)

    montar_video(roteiro, canal, pasta_imagens, args.saida, sem_legenda=args.sem_legenda)


if __name__ == "__main__":
    main()
