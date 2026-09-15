"""Gera as imagens das cenas automaticamente via Cloudflare Workers AI
(FLUX.2 [klein]) — de graça, sem cartão, ~10.000 Neurons/dia.

Usa a imagem da cena anterior como referência (encadeamento), igual o
Nano Banana fazia — isso é o que mantém o personagem consistente entre
cenas. Validado em 2026-09-07: sem isso, cada cena "reinventa" o
personagem (cabelo, roupa etc. mudam). Também reforça "NOT photorealistic"
no prompt porque esse modelo tende a puxar pra foto real quando recebe
imagem de referência, mesmo com o master style lock pedindo 2D animation.

Uso:
    python src/gerar_imagens_cloudflare.py --canal terror --roteiro roteiro_terror.json \
        --saida imagens_aprovadas/terror
"""

import argparse
import base64
import json
import os
import tempfile
import time
import urllib.parse

import requests
from dotenv import load_dotenv

from canais import carregar_canal

load_dotenv()

API_BASE = "https://api.cloudflare.com/client/v4/accounts"
MODELO = "@cf/black-forest-labs/flux-2-klein-4b"


class CotaEsgotadaError(RuntimeError):
    """Cota diária do Cloudflare esgotada — erro permanente pro resto do
    dia, não adianta tentar de novo com retry/backoff."""

REFORCO_2D = (
    "flat cel-shaded 2D cartoon illustration, thick black outlines, "
    "hand-drawn animation style, NOT photorealistic, NOT a photo, NOT 3D render. "
)

# Pedido do Davi 2026-09-10: "ia fraca de geradora de imagem, melhore o
# prompt, ia fraca cerebro monstro" -- o modelo usado (FLUX.2 klein-4b, a
# variante pequena/rápida da Cloudflare) é fraco em detalhe fino comparado a
# modelos grandes tipo o FLUX.1 dev da Replicate. Compensa isso com termos
# de qualidade concretos e específicos no fim do prompt (não genéricos tipo
# "trending on artstation", que modelos recentes já aprenderam a ignorar) --
# reforça nitidez de linha, riqueza de textura e composição, que é onde
# modelo pequeno costuma "borrar"/simplificar demais.
REFORCO_QUALIDADE = (
    "Extremely detailed illustration, crisp clean linework with no blur or smudging, "
    "rich intricate textures on every surface, masterful use of light, shadow and depth, "
    "sharp focus throughout, high production value single comic panel, coherent anatomy "
    "and proportions. "
)


MARCADOR_SEM_PERSONAGEM = "NO_CHARACTER:"


def montar_prompt(prompt_imagem: str, canal, personagem: str | None, tem_referencia: bool) -> str:
    """Bug real encontrado 2026-09-10: cenas puramente de cenário (ex: plano
    geral de uma van vazia, sem o personagem em quadro) saíam sempre com o
    personagem desenhado do mesmo jeito, porque a descrição dele era colada
    incondicionalmente em TODO prompt_imagem/prompt_imagem_2. Roteiros
    manuais que variam entre plano com personagem e plano só de cenário
    (pedido do Davi: "mais cenário") agora podem prefixar o prompt_imagem
    daquela cena/sub-imagem com "NO_CHARACTER:" pra pular a injeção."""
    sem_personagem = prompt_imagem.startswith(MARCADOR_SEM_PERSONAGEM)
    if sem_personagem:
        prompt_imagem = prompt_imagem[len(MARCADOR_SEM_PERSONAGEM):].strip()

    descricao_personagem = f"{personagem}. " if personagem and not sem_personagem else ""
    prefixo_referencia = "Same character as the reference image. " if tem_referencia and not sem_personagem else ""
    return (
        f"{canal.MASTER_STYLE_LOCK}{REFORCO_2D}{REFORCO_QUALIDADE}{prefixo_referencia}"
        f"{descricao_personagem}{prompt_imagem} {canal.RESTRICOES}"
    )


def gerar_imagem(prompt: str, imagem_referencia: bytes | None, tentativas: int = 3) -> bytes:
    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    token = os.environ["CLOUDFLARE_API_TOKEN"]
    url = f"{API_BASE}/{account_id}/ai/run/{MODELO}"
    headers = {"Authorization": f"Bearer {token}"}

    ultimo_erro = None
    for tentativa in range(1, tentativas + 1):
        data = {"prompt": prompt}
        files = {"image": ("ref.jpg", imagem_referencia, "image/jpeg")} if imagem_referencia else None

        try:
            resp = requests.post(url, headers=headers, data=data, files=files, timeout=90)
            if resp.status_code == 200:
                dados = resp.json()
                if dados.get("success"):
                    return base64.b64decode(dados["result"]["image"])
                ultimo_erro = f"Cloudflare retornou erro: {dados}"
            else:
                ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.exceptions.RequestException as e:
            # rede instável/reset -- não derruba a run inteira (bug real
            # 2026-09-10: ConnectionResetError sem try/except aqui travava
            # todo o script em vez de cair pro próximo fallback).
            ultimo_erro = f"erro de rede: {e}"

        # Cota diária esgotada (code 4006) não é erro passageiro -- tentar
        # de novo com backoff é só desperdiçar tempo, desiste na hora.
        if "daily free allocation" in ultimo_erro or '"code":4006' in ultimo_erro:
            raise CotaEsgotadaError(f"Cota diária esgotada: {ultimo_erro}")

        print(f"  tentativa {tentativa} falhou ({ultimo_erro[:120]}), esperando...")
        time.sleep(3 * tentativa)

    raise RuntimeError(f"Falhou após {tentativas} tentativas: {ultimo_erro}")


_CLIENTE_HF = None


def gerar_imagem_huggingface(prompt: str, imagem_referencia: bytes | None) -> bytes:
    """Segundo fallback (antes do Pollinations): FLUX.1 Kontext via Hugging
    Face Space, gratuito com conta (token em HUGGINGFACE_TOKEN) — cota bem
    curta (~3,5 min de GPU/dia, ~6-7 imagens), mas qualidade e aderência ao
    prompt bem melhores que o Pollinations, com suporte real a imagem de
    referência (mantém personagem consistente, validado em 2026-09-08).
    Como a cota é curta, só cobre uma fração das cenas de um vídeo — o
    chamador cai pro Pollinations quando essa também esgotar."""
    global _CLIENTE_HF
    from gradio_client import Client, handle_file

    if _CLIENTE_HF is None:
        token = os.environ.get("HUGGINGFACE_TOKEN")
        _CLIENTE_HF = Client("black-forest-labs/FLUX.1-Kontext-Dev", token=token) if token else Client("black-forest-labs/FLUX.1-Kontext-Dev")

    with tempfile.TemporaryDirectory() as pasta_tmp:
        if imagem_referencia:
            caminho_ref = os.path.join(pasta_tmp, "ref.jpg")
            with open(caminho_ref, "wb") as f:
                f.write(imagem_referencia)
        else:
            # o modelo exige uma imagem de entrada -- sem referência ainda
            # (primeira cena), usa um fundo neutro em branco como ponto de
            # partida, deixando o prompt (com a descrição do personagem)
            # fazer o trabalho sozinho.
            from PIL import Image
            caminho_ref = os.path.join(pasta_tmp, "ref.jpg")
            Image.new("RGB", (768, 1344), (128, 128, 128)).save(caminho_ref)

        resultado = _CLIENTE_HF.predict(
            input_image=handle_file(caminho_ref),
            prompt=prompt,
            seed=0,
            randomize_seed=True,
            guidance_scale=2.5,
            steps=28,
            api_name="/infer",
        )
        caminho_resultado = resultado[0]
        with open(caminho_resultado, "rb") as f:
            imagem_bytes = f.read()

        # normaliza pra JPEG (o resultado vem em .webp) pra manter
        # consistência com o resto do pipeline
        from PIL import Image
        caminho_jpg = os.path.join(pasta_tmp, "saida.jpg")
        Image.open(caminho_resultado).convert("RGB").save(caminho_jpg, "JPEG")
        with open(caminho_jpg, "rb") as f:
            return f.read()





# NÃO usar Modal aqui -- o app/crédito do Modal (mesmo o "arquivo-sombrio-
# flux") é compartilhado com o projeto podcasthub, decisão explícita do
# Davi 2026-09-15 de não gastar esse crédito neste pipeline. Removido de
# novo depois de uma tentativa (commit anterior) que ligou isso por engano.


def gerar_imagem_falai(prompt: str, imagem_referencia: bytes | None, tentativas: int = 3) -> bytes:
    """Quarto fallback (entre Modal e Hugging Face): FLUX.1 rodando na
    fal.ai, pago mas muito barato (~$0,006/imagem em 9:16, $0,003/megapixel)
    -- ver pesquisa 2026-09-09. Entra antes do Hugging Face porque não tem
    cota curta (paga por uso, sem limite diário como o Cloudflare/HF), só
    depende de ter crédito e a env var FAL_KEY configurada. Se a chave não
    estiver configurada, o chamador pula esse fallback direto (ver
    `falai_indisponivel` em `gerar_imagens_do_roteiro`)."""
    chave = os.environ["FAL_KEY"]
    headers = {"Authorization": f"Key {chave}", "Content-Type": "application/json"}

    if imagem_referencia:
        # img2img com a cena anterior como referência -- mesmo encadeamento
        # de personagem que Cloudflare/Modal/HF já fazem.
        data_uri = "data:image/jpeg;base64," + base64.b64encode(imagem_referencia).decode()
        url = "https://fal.run/fal-ai/flux/dev/image-to-image"
        body = {"prompt": prompt, "image_url": data_uri, "strength": 0.75}
    else:
        url = "https://fal.run/fal-ai/flux/schnell"
        body = {"prompt": prompt, "image_size": {"width": 768, "height": 1344}}

    ultimo_erro = None
    for tentativa in range(1, tentativas + 1):
        resp = requests.post(url, headers=headers, json=body, timeout=90)
        if resp.status_code == 200:
            dados = resp.json()
            imagem_url = dados["images"][0]["url"]
            resp_img = requests.get(imagem_url, timeout=60)
            resp_img.raise_for_status()
            return resp_img.content
        ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:300]}"
        # sem crédito não adianta tentar de novo
        if resp.status_code in (401, 403) or "credit" in ultimo_erro.lower():
            raise RuntimeError(f"fal.ai sem crédito/autorização: {ultimo_erro}")
        print(f"  [fal.ai] tentativa {tentativa} falhou ({ultimo_erro[:120]}), esperando...")
        time.sleep(3 * tentativa)

    raise RuntimeError(f"fal.ai falhou após {tentativas} tentativas: {ultimo_erro}")


def gerar_imagem_pollinations(prompt: str, tentativas: int = 5) -> bytes:
    """Fallback pra quando a cota do Cloudflare estoura (10.000 Neurons/dia
    já esgotados) — Pollinations.ai não precisa de chave/cadastro, mas a
    API deles só aceita imagem de referência via URL pública, não bytes
    locais. Sem chaining de referência aqui: a consistência do personagem
    fica só por conta da descrição em texto (ainda incluída no prompt),
    mais fraca que o encadeamento do Cloudflare — aceitável pra emergência,
    não pra rota principal (ver README/pesquisa de 2026-09-08)."""
    ultimo_erro = None
    for tentativa in range(1, tentativas + 1):
        try:
            url = (
                f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
                # model=flux explícito: o modelo padrão deles ("sana") ficou
                # constantemente congestionado/rate-limited em teste real
                # (2026-09-08), flux respondeu de forma estável.
                f"?width=768&height=1344&nologo=true&safe=true&model=flux"
            )
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
                return resp.content
            ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            ultimo_erro = str(e)

        print(f"  [Pollinations] tentativa {tentativa} falhou ({ultimo_erro[:120]}), esperando...")
        # o rate limit deles é por minuto (community model compartilhado
        # entre todos os usuários) -- espera mais generosa que o Cloudflare
        # dá mais chance de já ter liberado na próxima tentativa.
        time.sleep(8 * tentativa)

    raise RuntimeError(f"Pollinations falhou após {tentativas} tentativas: {ultimo_erro}")


VARIACOES_SUBCENA = [
    "",  # primeira imagem: usa o prompt da cena como está
    ", slightly different camera angle, tighter framing, same moment continuing",
]


def gerar_imagens_do_roteiro(
    roteiro: dict, canal, pasta_saida: str, imagens_por_cena: int = 2,
    contagem_saida: dict | None = None,
) -> tuple[bool, str | None]:
    """Gera e salva as imagens de cada cena do roteiro, encadeando sempre a
    última imagem gerada como referência da próxima (mantém o personagem
    consistente cena a cena E dentro da mesma cena). Com imagens_por_cena=2
    (padrão), salva cenaN_1.jpg/cenaN_2.jpg — o montar_video_local.py já
    sabe cortar entre as duas no meio da fala, o que dá bem mais sensação de
    movimento do que 1 imagem estática segurando a cena inteira (feedback:
    "vídeo muito parado" com poucas fotos e narração longa). Com
    imagens_por_cena=1, salva cenaN.jpg (formato antigo).

    Retorna (usou_fallback, fonte_fallback): usou_fallback é True se ALGUMA
    imagem precisou de Modal ou Pollinations (o chamador usa isso pra decidir
    se publica sozinho ou não), fonte_fallback identifica QUAL foi usado por
    último ("Modal (FLUX.1-schnell)" ou "Pollinations") pra a mensagem de
    revisão não mentir sobre a causa (bug real 2026-09-09: dizia sempre
    "Pollinations" mesmo quando era o Modal)."""
    os.makedirs(pasta_saida, exist_ok=True)
    personagem = roteiro.get("personagem")
    usou_fallback = False
    contagem_fontes: dict[str, int] = {}
    # Bug real encontrado 2026-09-09: a mensagem de reprovação dizia sempre
    # "usou fallback Pollinations", mesmo quando quem gerou a imagem foi o
    # Modal -- confundia o diagnóstico (o vídeo ruim daquele dia tinha vindo
    # 100% do Modal, não do Pollinations, e o log não deixava isso claro).
    fonte_fallback = None
    hf_esgotado = False  # depois do primeiro esgotamento, nem tenta de novo (cota é bem curta)
    cloudflare_esgotado = False  # idem -- cota diária, não adianta insistir na mesma run
    falai_indisponivel = not os.environ.get("FAL_KEY")
    falai_sem_credito = False  # sem crédito não é passageiro, não insiste na mesma run

    ultima_imagem_personagem = None  # encadeia referência só entre fotos COM personagem

    for i, cena in enumerate(roteiro["cenas"], start=1):
        for parte in range(1, imagens_por_cena + 1):
            print(f"Gerando imagem da cena {i} ({parte}/{imagens_por_cena})...")
            # prompt_imagem_2 (se o roteiro trouxer) descreve um momento
            # ESPECÍFICO diferente da narração, em vez de só variar o
            # ângulo da mesma pose — imagem mais ligada ao que é dito
            # naquele trecho (pesquisa 2026-09-08: densidade de informação
            # nova por corte ajuda retenção, não só variedade visual vazia).
            if parte == 1:
                prompt_base = cena["prompt_imagem"]
            else:
                prompt_base = cena.get("prompt_imagem_2") or (
                    cena["prompt_imagem"] + VARIACOES_SUBCENA[(parte - 1) % len(VARIACOES_SUBCENA)]
                )
            sem_personagem = prompt_base.startswith(MARCADOR_SEM_PERSONAGEM)
            # Bug real encontrado 2026-09-10 (feedback do Davi repetido três
            # vezes: "tá faltando cenário, tudo fica parecido" / "ficou um
            # lixo todas iguais"): mesmo com o prompt de texto pedindo só
            # cenário/objeto, o img2img mandava a ÚLTIMA imagem gerada como
            # referência visual -- o modelo ancora na composição em pixels
            # da referência, não só no texto. Dois casos precisam de
            # NENHUMA referência:
            # 1) cena marcada NO_CHARACTER -- não deve herdar composição de
            #    uma cena anterior que tinha o personagem;
            # 2) roteiro SEM personagem nenhum (ex: "Em Alta" formato
            #    documentário/curiosidade, tipo Chernobyl) -- não existe
            #    identidade nenhuma pra manter consistente, então encadear
            #    imagem só faz cada cena puxar a composição da anterior
            #    (sala de controle -> explosão -> bombeiros ficam todos
            #    parecidos por causa da referência, não do prompt).
            # Só encadeia entre si fotos que TÊM personagem definido no
            # roteiro E não estão marcadas NO_CHARACTER.
            imagem_referencia = None if (sem_personagem or not personagem) else ultima_imagem_personagem
            prompt = montar_prompt(prompt_base, canal, personagem, imagem_referencia is not None)
            imagem_bytes = None
            fonte_desta_imagem = "Cloudflare"
            if not cloudflare_esgotado:
                try:
                    imagem_bytes = gerar_imagem(prompt, imagem_referencia)
                except CotaEsgotadaError as e:
                    print(f"  Cloudflare esgotado ({e}) — não tenta mais nessa run")
                    cloudflare_esgotado = True
                except RuntimeError as e:
                    print(f"  Cloudflare falhou ({e})")

            if imagem_bytes is None and not falai_indisponivel and not falai_sem_credito:
                try:
                    print("  tentando fallback fal.ai (FLUX.1)...")
                    imagem_bytes = gerar_imagem_falai(prompt, imagem_referencia)
                    usou_fallback = True
                    fonte_fallback = "fal.ai (FLUX.1)"
                    fonte_desta_imagem = fonte_fallback
                except Exception as e_falai:
                    print(f"  fal.ai falhou ({e_falai})")
                    if "crédito" in str(e_falai) or "autorização" in str(e_falai):
                        falai_sem_credito = True

            if imagem_bytes is None:
                if not hf_esgotado:
                    try:
                        print("  tentando fallback Hugging Face (FLUX.1 Kontext)...")
                        imagem_bytes = gerar_imagem_huggingface(prompt, imagem_referencia)
                        usou_fallback = True
                        fonte_fallback = "Hugging Face (FLUX.1 Kontext)"
                        fonte_desta_imagem = fonte_fallback
                    except Exception as e_hf:
                        print(f"  Hugging Face falhou/esgotou ({e_hf}) — não tenta mais nessa run")
                        hf_esgotado = True
                if imagem_bytes is None:
                    print("  caindo pro fallback Pollinations...")
                    imagem_bytes = gerar_imagem_pollinations(prompt)
                    usou_fallback = True
                    fonte_fallback = "Pollinations"
                    fonte_desta_imagem = fonte_fallback

            nome = f"cena{i}.jpg" if imagens_por_cena == 1 else f"cena{i}_{parte}.jpg"
            caminho = os.path.join(pasta_saida, nome)
            with open(caminho, "wb") as f:
                f.write(imagem_bytes)
            print(f"  salvo em {caminho}")

            if contagem_saida is not None:
                contagem_saida[fonte_desta_imagem] = contagem_saida.get(fonte_desta_imagem, 0) + 1

            if not sem_personagem:
                ultima_imagem_personagem = imagem_bytes
            time.sleep(2)

    return usou_fallback, fonte_fallback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canal", default="terror")
    parser.add_argument("--roteiro", required=True)
    parser.add_argument("--saida", default=None)
    parser.add_argument("--imagens-por-cena", type=int, default=2)
    args = parser.parse_args()

    canal = carregar_canal(args.canal)
    pasta_saida = args.saida or canal.PASTA_IMAGENS

    with open(args.roteiro, encoding="utf-8") as f:
        roteiro = json.load(f)

    contagem: dict[str, int] = {}
    gerar_imagens_do_roteiro(
        roteiro, canal, pasta_saida, imagens_por_cena=args.imagens_por_cena, contagem_saida=contagem,
    )

    # Bug real encontrado 2026-09-10: essa mensagem sempre dizia "custo:
    # R$0,00" e contava só len(cenas) em vez do total de imagens (cenas x
    # imagens_por_cena). Removido o fallback Replicate 2026-09-15 (o Davi
    # não quer mais pagar por imagem avulsa) -- SEM substituto pago no lugar
    # dele (Modal também está fora, é crédito compartilhado com o
    # podcasthub, não pode ser gasto aqui). fal.ai continua sendo o único
    # fallback com custo direto por imagem, se a chave estiver configurada.
    CUSTO_USD_POR_IMAGEM = {"fal.ai (FLUX.1)": 0.006}
    total_imagens = sum(contagem.values())
    custo_total = sum(CUSTO_USD_POR_IMAGEM.get(fonte, 0.0) * n for fonte, n in contagem.items())
    resumo_fontes = ", ".join(f"{n}x {fonte}" for fonte, n in contagem.items())
    print(
        f"\n{total_imagens} imagens geradas em {pasta_saida} ({resumo_fontes}) — "
        f"custo estimado: US$ {custo_total:.2f}. Confira visualmente antes de montar o vídeo."
    )


if __name__ == "__main__":
    main()
