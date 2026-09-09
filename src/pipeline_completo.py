"""Pipeline automatizado de ponta a ponta: roteiro -> imagens -> vídeo -> publicação.

Usado tanto manualmente quanto pelo GitHub Actions agendado (ver
.github/workflows/pipeline_dark.yml). Trava de segurança embutida: se a
duração final ficar abaixo de 60s ou algum arquivo não sair como esperado,
o pipeline NÃO publica sozinho — só salva tudo em runs/ pra revisão manual.
Sem isso, um roteiro ruim ou uma falha de geração iria direto pro ar sem
ninguém checar.

Uso manual:
    python src/pipeline_completo.py --canal terror
    python src/pipeline_completo.py --canal terror --tema "..." --sem-publicar
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canais import carregar_canal
from canais import tendencias as canal_tendencias
from gerar_imagens_cloudflare import gerar_imagens_do_roteiro
from gerar_roteiro import _chaves_api, gerar_roteiro
from montar_video_local import montar_video

TEMAS_FALLBACK = {
    "terror": [
        "um objeto amaldiçoado herdado de um parente falecido",
        "uma entidade que começa a imitar a voz de alguém conhecido",
        "um perseguidor humano silencioso que aparece todas as noites no mesmo trajeto",
        "um padrão estranho que se repete numa mesma data todo ano",
        "um ritual antigo encontrado escrito num diário de família",
        "um lugar que muda de aparência sempre que ninguém está olhando",
        "um encontro com um estranho que sabe informações que não deveria saber",
        "fotos antigas da família onde uma figura estranha aparece cada vez mais perto",
        # Temas "relato real"/lenda documentada (feedback 2026-09-09: "gostei dos 3, quero
        # roteiros assim") -- baseados em lendas/casos reais amplamente documentados,
        # narrados em primeira pessoa fictícia (nunca afirmando ser a família real do caso).
        "inspirado no caso real e documentado da casa de Amityville (EUA, 1975-1977) -- uma "
        "pessoa se muda pra uma casa isolada com histórico parecido e começa a vivenciar "
        "fenômenos semelhantes aos relatados no caso real",
        "uma lenda antiga sobre um monge ou figura religiosa mal-assombrando uma igreja ou "
        "mosteiro abandonado numa região isolada, com névoa e atmosfera decadente",
        "uma teoria/mistério real sem solução (ex: um desaparecimento histórico documentado "
        "sem explicação) contado como especulação, nunca como fato confirmado",
    ],
    "true_crime": [
        "um caso de desaparecimento nunca solucionado",
        "uma investigação sobre uma fraude que enganou uma cidade inteira",
        "um crime solucionado décadas depois por uma nova evidência",
        "um caso envolvendo um culto investigado pela polícia",
        "um assassinato com um padrão que intrigou investigadores por anos",
    ],
}


ARQUIVO_ESTADO_NARRADOR = os.path.join("runs", "ultimo_narrador.json")
ARQUIVO_ESTADO_SUBCANAL = os.path.join("runs", "ultimo_subcanal.json")

# A conta "Arquivo Sombrio" posta tanto terror ficcional quanto casos reais
# (true crime) — alterna entre os dois em vez de manter contas separadas.
SUBCANAIS_ARQUIVO_SOMBRIO = ["terror", "true_crime"]


def proximo_subcanal_arquivo_sombrio() -> str:
    """Alterna terror/true_crime pra conta 'Arquivo Sombrio' postar os dois
    tipos de conteúdo sem depender de sorteio."""
    estado = {}
    if os.path.exists(ARQUIVO_ESTADO_SUBCANAL):
        with open(ARQUIVO_ESTADO_SUBCANAL, encoding="utf-8") as f:
            estado = json.load(f)

    ultimo = estado.get("arquivo_sombrio", SUBCANAIS_ARQUIVO_SOMBRIO[-1])
    idx_atual = SUBCANAIS_ARQUIVO_SOMBRIO.index(ultimo) if ultimo in SUBCANAIS_ARQUIVO_SOMBRIO else -1
    proximo = SUBCANAIS_ARQUIVO_SOMBRIO[(idx_atual + 1) % len(SUBCANAIS_ARQUIVO_SOMBRIO)]

    estado["arquivo_sombrio"] = proximo
    os.makedirs("runs", exist_ok=True)
    with open(ARQUIVO_ESTADO_SUBCANAL, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

    return proximo


def escolher_tema(canal_nome: str) -> str:
    return random.choice(TEMAS_FALLBACK[canal_nome])


def proximo_genero_narrador(canal_nome: str) -> str:
    """Alterna masculino/feminino entre execuções em vez de deixar 100% ao
    sorteio da IA — sem isso, por coincidência, várias gerações seguidas
    saem com o mesmo narrador (feedback: 'sempre a mesma voz')."""
    estado = {}
    if os.path.exists(ARQUIVO_ESTADO_NARRADOR):
        with open(ARQUIVO_ESTADO_NARRADOR, encoding="utf-8") as f:
            estado = json.load(f)

    ultimo = estado.get(canal_nome, "feminino")
    proximo = "masculino" if ultimo == "feminino" else "feminino"

    estado[canal_nome] = proximo
    os.makedirs("runs", exist_ok=True)
    with open(ARQUIVO_ESTADO_NARRADOR, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

    return proximo


def gerar_titulo(roteiro: dict) -> str:
    primeira_frase = roteiro["cenas"][0]["narracao"].split(".")[0].strip()
    titulo = f"{primeira_frase}... #shorts"
    return titulo[:100]


# Hashtags por canal/formato — YouTube e TikTok usam pra indexar/recomendar
# o vídeo pra quem já assiste esse tipo de conteúdo. Reconhece o prefixo do
# tema (ex: "novela_mascote::...") pros formatos do canal tendencias.
HASHTAGS_POR_CONTEXTO = {
    "terror": ["terror", "creepypasta", "historiadeterror", "assustador", "arquivosombrio", "medo", "shorts"],
    "true_crime": ["casoreal", "truecrime", "investigacao", "misterio", "casosreais", "shorts"],
    "novela_mascote": ["novela", "drama", "comedia", "viral", "shorts", "fyp"],
    "objeto_falante": ["comedia", "humor", "relatable", "engracado", "shorts", "fyp"],
    "historia_pov": ["historia", "pov", "curiosidadeshistoricas", "vocesabia", "shorts"],
    "curiosidade": ["curiosidades", "vocesabia", "fatosreais", "shorts", "aprenda"],
}


def gerar_descricao_unica(roteiro: dict, nome_canal_exibicao: str) -> str | None:
    """Gera uma descrição de YouTube genuinamente específica desta história
    (não um template com hook trocado) — feedback 2026-09-09: a política de
    "conteúdo inautêntico" do YouTube (jul/2026) pune canal onde trocar de
    vídeo pra vídeo revela a mesma estrutura por trás ("substância só \
levemente diferente"), o que inclui descrição template. Retorna None se a \
chamada de IA falhar por qualquer motivo — o chamador cai pro template \
antigo como rede de segurança, nunca trava a publicação por causa disso."""
    from google import genai
    from google.genai import types

    historia = " ".join(c["narracao"] for c in roteiro["cenas"])
    prompt = (
        f'Baseado nesta história: "{historia}"\n\n'
        "Escreva uma descrição de YouTube envolvente e ESPECÍFICA dessa história (2-3 frases, "
        "máximo 220 caracteres), sem entregar o final, sem frase genérica tipo 'baseado em fatos "
        "reais' ou 'você não vai acreditar'. Termine com uma chamada natural pra se inscrever no "
        f'canal "{nome_canal_exibicao}", com uma frase diferente a cada vez (nunca repita uma '
        "fórmula fixa). Responda só com o texto da descrição, sem aspas, sem markdown."
    )
    try:
        client = genai.Client(api_key=_chaves_api()[0], http_options=types.HttpOptions(timeout=20_000))
        resposta = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
        return resposta.text.strip()
    except Exception as e:
        print(f"[gerar_descricao_unica] falhou ({e}), usando descrição-template de fallback")
        return None


def gerar_metadados_publicacao(canal_nome: str, tema: str, roteiro: dict, nome_canal_exibicao: str) -> tuple[str, str, list[str]]:
    """Monta título, descrição e tags — hashtags variam por formato pra
    ajudar o algoritmo a indexar certo (ex: novela de mascote não deve
    levar hashtag de terror, e vice-versa)."""
    contexto = canal_nome
    for prefixo in ("novela_mascote", "objeto_falante", "historia_pov"):
        if tema.startswith(f"{prefixo}::"):
            contexto = prefixo
            break
    else:
        if canal_nome == "tendencias":
            contexto = "curiosidade"

    hashtags = HASHTAGS_POR_CONTEXTO.get(contexto, ["shorts"])
    titulo = gerar_titulo(roteiro)

    # Descrição gerada pela IA em cima da história específica deste vídeo
    # (ver gerar_descricao_unica) — só cai pro template antigo (gancho +
    # CTA fixo) se a chamada de IA falhar por qualquer motivo.
    corpo_descricao = gerar_descricao_unica(roteiro, nome_canal_exibicao)
    if corpo_descricao is None:
        gancho = roteiro["cenas"][0]["narracao"].strip()
        if len(gancho) > 150:
            gancho = gancho[:147].rsplit(" ", 1)[0] + "..."
        frases_cta_descricao = [
            f"{nome_canal_exibicao} traz um vídeo novo por dia — curte e se inscreve pra não perder o próximo.",
            f"Tem mais história dessas no {nome_canal_exibicao} — se inscreve e ativa o sininho.",
            f"Se você chegou até aqui, se inscreve no {nome_canal_exibicao} — sai vídeo novo todo dia.",
            f"{nome_canal_exibicao}: histórias novas toda semana. Deixa o like se quiser mais.",
        ]
        corpo_descricao = f"{gancho}\n\n{random.choice(frases_cta_descricao)}"

    descricao = f"{corpo_descricao}\n\n" + " ".join(f"#{h}" for h in hashtags)
    return titulo, descricao, hashtags


# Cada CONTA (não canal) tem suas próprias credenciais de YouTube/TikTok.
# "arquivo_sombrio" e "tendencias" são nomes de conta; terror/true_crime são
# sub-tipos de conteúdo dentro da conta arquivo_sombrio.
CREDENCIAIS_POR_CONTA = {
    "arquivo_sombrio": {
        "youtube_client_secret": "client_secret.json",
        "youtube_token": "token.json",
        "tiktok_token": "tiktok_token.json",
    },
    "tendencias": {
        "youtube_client_secret": "client_secret.json",  # mesmo app OAuth, conta Google diferente
        "youtube_token": "token_tendencias.json",
        "tiktok_token": "tiktok_token_tendencias.json",
    },
}


def executar(canal_nome: str, tema: str | None, publicar: bool, publicar_tiktok: bool = False) -> dict:
    conta_nome = canal_nome  # antes de resolver terror/true_crime

    # "arquivo_sombrio" é o nome da CONTA, não de um canal técnico — resolve
    # pra terror ou true_crime alternadamente, pra postar os dois tipos de
    # conteúdo na mesma conta.
    if canal_nome == "arquivo_sombrio":
        canal_nome = proximo_subcanal_arquivo_sombrio()

    if canal_nome == "tendencias":
        tema = tema or canal_tendencias.escolher_tema_do_dia()
        canal = canal_tendencias.montar_canal_dinamico(tema)
    else:
        canal = carregar_canal(canal_nome)
        tema = tema or escolher_tema(canal_nome)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_run = os.path.join("runs", f"{canal_nome}_{timestamp}")
    os.makedirs(pasta_run, exist_ok=True)

    # Feedback 2026-09-09: no canal "terror" o narrador deve ser sempre
    # masculino -- a maioria das referências desse estilo de conteúdo
    # (ex: "Contos Urbanos") usa voz masculina. Os outros canais continuam
    # alternando normalmente.
    if canal_nome == "terror":
        genero_desejado = "masculino"
    else:
        genero_desejado = proximo_genero_narrador(canal_nome)
    # Variedade real de duração/ritmo entre vídeos (feedback 2026-09-09,
    # risco de política "conteúdo inautêntico" do YouTube: canal onde todo
    # vídeo tem a mesma duração/profundidade lê como template automatizado).
    # Maioria continua no alvo padrão (bate a meta interna de cada canal,
    # ~200-230 palavras); minoria sai bem mais longa de propósito.
    duracao_variante = random.choices(["padrao", "longa"], weights=[70, 30])[0]
    if duracao_variante == "longa":
        instrucao_duracao = (
            " IMPORTANTE: para este vídeo especificamente, IGNORE a meta de 200-230 palavras "
            "do system prompt -- escreva um roteiro bem mais longo e desenvolvido desta vez, "
            "entre 320 e 420 palavras no total, com mais cenas e mais detalhe na escalada "
            "(mesma estrutura, só mais desenvolvida)."
        )
    else:
        instrucao_duracao = ""

    tema_completo = (
        f"{tema} (o narrador/personagem principal desta história deve ser do gênero "
        f"{genero_desejado}){instrucao_duracao}"
    )

    print(f"[{canal_nome}] tema: {tema} | narrador forçado: {genero_desejado}")

    # Qualquer falha daqui pra frente (roteiro malformado, Cloudflare
    # recusando uma imagem por moderação mesmo após retry, ffmpeg quebrando,
    # etc) vira "reprovado" em vez de derrubar o processo com traceback —
    # sem isso, uma falha de UMA cena travava a run inteira sem marcar
    # nada como reprovado (aconteceu de verdade: moderação da Cloudflare
    # recusou uma cena 3x seguidas e a exceção subiu sem tratamento).
    try:
        roteiro = gerar_roteiro(tema_completo, canal)
        # Garantia em código (não só no prompt) de que o gênero forçado
        # realmente é usado -- a IA às vezes ignora a instrução de texto.
        roteiro["genero_narrador"] = genero_desejado
        with open(os.path.join(pasta_run, "roteiro.json"), "w", encoding="utf-8") as f:
            json.dump(roteiro, f, ensure_ascii=False, indent=2)

        # Checa a contagem de palavras ANTES de gastar cota de imagem — na
        # voz mais rápida do Kokoro (~3 palavras/s), menos de 185 palavras
        # não bate os 60s mínimos de jeito nenhum. Sem essa checagem, o
        # pipeline gastava Neurons do Cloudflare num vídeo que já ia ser
        # reprovado de qualquer forma (aconteceu de verdade em 2026-09-08).
        total_palavras = sum(len(c["narracao"].split()) for c in roteiro["cenas"])
        if total_palavras < 185:
            raise ValueError(
                f"roteiro saiu com só {total_palavras} palavras — não vai bater 60s "
                "nem na voz mais lenta, abortando antes de gastar cota de imagem"
            )

        pasta_imagens = os.path.join(pasta_run, "imagens")
        usou_fallback_imagem = gerar_imagens_do_roteiro(roteiro, canal, pasta_imagens)

        caminho_video = os.path.join(pasta_run, "video.mp4")  # alias == versão YouTube (ver montar_video)
        caminho_video_tiktok = os.path.join(pasta_run, "video_tiktok.mp4")
        duracao = montar_video(roteiro, canal, pasta_imagens, caminho_video)

        video_ok = os.path.exists(caminho_video) and os.path.getsize(caminho_video) > 500_000
        # Vídeo com imagem do fallback Pollinations não publica sozinho --
        # já vimos ele gerar algo completamente diferente do personagem
        # pedido (ex: "geladeira" virou um monstro), precisa de olho humano.
        aprovado = video_ok and duracao >= 60 and not usou_fallback_imagem
        if not video_ok:
            motivo = "arquivo de vídeo não foi gerado corretamente"
        elif duracao < 60:
            motivo = "duração abaixo de 60s"
        elif usou_fallback_imagem:
            motivo = "usou fallback Pollinations (imagem pode não bater com o personagem) — revisar antes de publicar"
        else:
            motivo = None
    except Exception as e:
        aprovado = False
        motivo = f"erro durante geração: {e}"

    if not aprovado:
        print(f"\nREPROVADO AUTOMATICAMENTE ({motivo}) — não vai publicar. Revisar em {pasta_run}/")
        return {"aprovado": False, "motivo": motivo, "pasta": pasta_run}

    titulo, descricao, tags = gerar_metadados_publicacao(canal_nome, tema, roteiro, canal.NOME_CANAL)
    print(f"\nAprovado ({duracao:.1f}s). Título: {titulo}")

    if not publicar:
        print("--sem-publicar ativo — só gerou, não publicou.")
        return {"aprovado": True, "publicado": False, "pasta": pasta_run}

    resultado = {"aprovado": True, "publicado": True, "pasta": pasta_run}
    credenciais = CREDENCIAIS_POR_CONTA.get(conta_nome, CREDENCIAIS_POR_CONTA["arquivo_sombrio"])

    try:
        from publicar_youtube import publicar_short
        video_id = publicar_short(
            caminho_video, titulo, descricao=descricao, tags=tags,
            arquivo_client_secret=credenciais["youtube_client_secret"],
            arquivo_token=credenciais["youtube_token"],
        )
        resultado["youtube"] = f"https://youtube.com/shorts/{video_id}"
        print(f"YouTube: {resultado['youtube']}")
    except Exception as e:
        print(f"AVISO: falhou publicar no YouTube: {e}")
        resultado["youtube_erro"] = str(e)

    if publicar_tiktok:
        try:
            from publicar_tiktok import publicar_video
            # Versão com a trilha escolhida pro TikTok (Musica1), não a
            # mesma cópia que vai pro YouTube (ver TRILHAS_POR_PLATAFORMA
            # em montar_video_local.py).
            publish_id = publicar_video(caminho_video_tiktok, titulo, arquivo_token=credenciais["tiktok_token"])
            resultado["tiktok_publish_id"] = publish_id
            print(f"TikTok publish_id: {publish_id}")
        except Exception as e:
            print(f"AVISO: falhou publicar no TikTok: {e}")
            resultado["tiktok_erro"] = str(e)
    else:
        print("TikTok automático desativado por enquanto (postagem lá é manual) — vídeo pronto em " + caminho_video)

    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canal", default="terror")
    parser.add_argument("--tema", default=None)
    parser.add_argument("--sem-publicar", action="store_true")
    parser.add_argument("--publicar-tiktok", action="store_true", help="Por padrão só publica no YouTube; TikTok fica manual")
    args = parser.parse_args()

    resultado = executar(args.canal, args.tema, publicar=not args.sem_publicar, publicar_tiktok=args.publicar_tiktok)
    print("\n" + json.dumps(resultado, ensure_ascii=False, indent=2))

    # Feedback 2026-09-09: reprovação por motivo esperado (fallback
    # Pollinations, duração curta) é comum quase todo dia quando a cota do
    # Cloudflare esgota -- marcar isso como "falha" (X vermelho) no
    # GitHub Actions criava alarme falso constante. Só um ERRO DE VERDADE
    # (exceção durante geração -- roteiro malformado, ffmpeg quebrando,
    # etc) deve marcar a execução como falha; reprovação por qualidade é
    # esperada e o vídeo continua salvo em runs/ pra revisão manual.
    motivo = resultado.get("motivo") or ""
    if not resultado["aprovado"] and motivo.startswith("erro durante geração"):
        sys.exit(1)


if __name__ == "__main__":
    main()
