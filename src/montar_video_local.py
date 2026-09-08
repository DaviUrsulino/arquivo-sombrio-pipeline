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
    "normal": 1.0,
    "grave": 0.90,
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


def gerar_cta_final(caminho_saida: str, duracao: float = 3.0):
    """Tela final animada pedindo like/inscrição/sininho — usa a imagem de
    fundo aprovada (sino+play) se existir, senão cai pra cor lisa. Áudio
    silencioso (proposital, não erro) só pra manter o mesmo formato de
    stream dos outros clipes na hora de concatenar."""
    fps = 30
    texto_filtro = (
        f"drawtext=text='CURTA E SE INSCREVA':fontfile={FONTE_PADRAO}:fontcolor=white:"
        f"fontsize=64:x=(w-text_w)/2:y=h*0.72:borderw=4:bordercolor=black@0.6,"
        f"drawtext=text='E ATIVE O SININHO':fontfile={FONTE_PADRAO}:fontcolor=0xFFD700:"
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


def gerar_ambiencia(caminho_saida: str, duracao: float, perfil: str = "leve"):
    """Cama de som ambiente sintetizada (drone + tremolo) — NÃO é trilha
    musical de verdade (composição autoral estaria sujeita a direito
    autoral se baixada de terceiro), é atmosfera de fundo bem baixa, só
    pra dar textura sonora por trás da narração. Perfil varia por
    formato/canal (ver AMBIENCIA em cada canais/*.py)."""
    p = PERFIS_AMBIENCIA.get(perfil, PERFIS_AMBIENCIA["leve"])
    _rodar([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency={p['freq']}:duration={duracao}",
        "-af", f"tremolo=f={p['tremolo_hz']}:d={p['tremolo_depth']},volume={p['volume']}",
        caminho_saida,
    ])


def gerar_clipe_imagem_silencioso(
    caminho_imagem: str, duracao: float, caminho_saida: str, zoom_out: bool = False
):
    """Imagem estática + Ken Burns, sem áudio, com a duração pedida.

    zoom_out=True inverte a direção (começa mais perto, afasta) — alternar
    entre zoom-in e zoom-out a cada troca de imagem dá mais sensação de
    movimento/corte do que repetir sempre o mesmo zoom-in (feedback: vídeo
    "parado demais" pra viralizar)."""
    fps = 30
    zoom_por_frame = 1 + (0.12 / max(duracao * fps, 1))
    if zoom_out:
        expressao_zoom = f"if(eq(on,0),1.15,max(zoom-{zoom_por_frame-1},1.0))"
    else:
        expressao_zoom = f"min(zoom+{zoom_por_frame-1},1.15)"
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
            f"zoompan=z='{expressao_zoom}':d={int(duracao*fps)}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={LARGURA}x{ALTURA}:fps={fps}[v]"
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
    fala se houver mais de uma, alternando zoom-in/zoom-out pra reforçar o
    corte), depois mux a narração por cima do trecho todo, com um whoosh
    curto em cada troca de imagem."""
    duracao_por_imagem = duracao / len(imagens)
    sub_clipes = []
    for i, caminho_imagem in enumerate(imagens):
        caminho_sub = os.path.join(pasta_tmp, f"{os.path.basename(caminho_saida)}_sub{i}.mp4")
        gerar_clipe_imagem_silencioso(caminho_imagem, duracao_por_imagem, caminho_sub, zoom_out=(i % 2 == 1))
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
    """Concatena as cenas com crossfade (video) + crossfade de áudio entre
    elas, em vez do corte seco do concat demuxer — dá sensação de "cenas
    conectadas" em vez de cortes duros. Precisa reencodar (não dá pra usar
    -c copy com xfade), então é mais lento que concatenar_clipes, mas só é
    usado uma vez por vídeo (na junção final das cenas, não nas trocas de
    imagem dentro da cena, que continuam com corte+whoosh)."""
    duracoes = [_duracao_segundos(c) for c in caminhos_clipes]

    entradas = []
    for caminho in caminhos_clipes:
        entradas += ["-i", caminho]

    filtros = []
    v_atual = "0:v"
    a_atual = "0:a"
    duracao_acumulada = duracoes[0]

    for i in range(1, len(caminhos_clipes)):
        offset = max(duracao_acumulada - duracao_transicao, 0)
        v_saida = f"v{i}" if i < len(caminhos_clipes) - 1 else "vout"
        a_saida = f"a{i}" if i < len(caminhos_clipes) - 1 else "aout"
        filtros.append(
            f"[{v_atual}][{i}:v]xfade=transition=fade:duration={duracao_transicao}:offset={offset}[{v_saida}]"
        )
        filtros.append(f"[{a_atual}][{i}:a]acrossfade=d={duracao_transicao}[{a_saida}]")
        v_atual, a_atual = v_saida, a_saida
        duracao_acumulada = duracao_acumulada + duracoes[i] - duracao_transicao

    _rodar([
        "ffmpeg", "-y",
        *entradas,
        "-filter_complex", ";".join(filtros),
        "-map", f"[{v_atual}]", "-map", f"[{a_atual}]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        caminho_saida,
    ])


def extrair_audio(caminho_video: str, caminho_saida: str):
    _rodar(["ffmpeg", "-y", "-i", caminho_video, "-vn", "-acodec", "pcm_s16le", caminho_saida])


PALAVRAS_POR_BLOCO = 4  # estilo CapCut: poucas palavras por vez, não frase inteira


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
Style: Legenda,Arial Black,78,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,5,0,2,60,60,340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # Destaque palavra-por-palavra (estilo CapCut): pra cada palavra falada,
    # gera uma linha mostrando o bloco inteiro com só aquela palavra colorida
    # — legenda estática em bloco tinha retenção pior segundo a pesquisa.
    COR_DESTAQUE = "&H0000D7FF&"  # amarelo/dourado (BGR)
    COR_NORMAL = "&H00FFFFFF&"  # branco

    linhas = []
    for i in range(0, len(palavras), PALAVRAS_POR_BLOCO):
        bloco = palavras[i:i + PALAVRAS_POR_BLOCO]
        for idx_ativo, (inicio, fim, _) in enumerate(bloco):
            partes = []
            for idx, (_, _, palavra) in enumerate(bloco):
                token = palavra.strip().upper()
                if idx == idx_ativo:
                    token = f"{{\\c{COR_DESTAQUE}}}{token}{{\\c{COR_NORMAL}}}"
                partes.append(token)
            texto = " ".join(partes)
            linhas.append(
                f"Dialogue: 0,{_formatar_tempo_ass(inicio)},{_formatar_tempo_ass(fim)},"
                f"Legenda,,0,0,0,,{texto}"
            )

    with open(caminho_saida_ass, "w", encoding="utf-8") as f:
        f.write(cabecalho)
        f.write("\n".join(linhas))


def queimar_legenda(caminho_video: str, caminho_ass: str, caminho_saida: str):
    caminho_ass_escapado = caminho_ass.replace(":", "\\:")
    _rodar([
        "ffmpeg", "-y", "-i", caminho_video,
        "-vf", f"ass={caminho_ass_escapado}",
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
        caminho_sfx = os.path.join(pasta_tmp, "whoosh.wav")
        gerar_sfx_whoosh(caminho_sfx)

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
        print(f"Adicionando ambientação sonora ({perfil_ambiencia})...")
        duracao_total_video = _duracao_segundos(caminho_com_legenda)
        caminho_ambiencia = os.path.join(pasta_tmp, "ambiencia.wav")
        gerar_ambiencia(caminho_ambiencia, duracao_total_video, perfil_ambiencia)
        _rodar([
            "ffmpeg", "-y",
            "-i", caminho_com_legenda, "-i", caminho_ambiencia,
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac",
            saida,
        ])

    print(f"\nVídeo salvo em: {saida} (custo: R$0,00)")
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
