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


def montar_prompt(prompt_imagem: str, canal, personagem: str | None, tem_referencia: bool) -> str:
    descricao_personagem = f"{personagem}. " if personagem else ""
    prefixo_referencia = "Same character as the reference image. " if tem_referencia else ""
    return (
        f"{canal.MASTER_STYLE_LOCK}{REFORCO_2D}{prefixo_referencia}"
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


_CLIENTE_MODAL = None


def gerar_imagem_modal(prompt: str, imagem_referencia: bytes | None) -> bytes:
    """Terceiro fallback (entre Cloudflare e Hugging Face): FLUX.1-schnell
    rodando na Modal (GPU serverless, $30/mês grátis) — ver
    src/modal_flux_app.py. Suporta encadeamento de referência (img2img),
    então mantém a consistência de personagem igual o Cloudflare. Entra
    antes do Hugging Face na cadeia porque a cota do HF (ZeroGPU) é
    minúscula (~3,5 min/dia) e a da Modal é bem mais folgada."""
    global _CLIENTE_MODAL
    import modal

    if _CLIENTE_MODAL is None:
        _CLIENTE_MODAL = modal.Cls.from_name("arquivo-sombrio-flux", "Flux")()

    return _CLIENTE_MODAL.gerar.remote(prompt, imagem_referencia)


def gerar_imagem_replicate(prompt: str, imagem_referencia: bytes | None, tentativas: int = 3) -> bytes:
    """Fallback pago (Replicate, FLUX.1 [dev]) -- validado manualmente em
    2026-09-10 como o de MELHOR fidelidade entre todos os fallbacks pagos
    (ver testes com o roteiro do palhaço-fantasma). Entra ANTES do fal.ai
    na cadeia por isso. Custo ~$0,025/imagem -- não é grátis, então só usa
    quando Cloudflare/Modal (grátis) já falharam. Requer REPLICATE_API_TOKEN
    no .env/secrets.

    Achado importante na mesma sessão: a causa real da baixa fidelidade de
    figurino em TODOS os provedores (não só aqui) era o prompt de imagem
    estar em português -- FLUX (e modelos afins) são treinados majoritariamente
    em inglês e ignoram/erram detalhes de roupa/objeto descritos em
    português, mesmo termos comuns. Corrigido na fonte (ver canais/terror.py
    e canais/tendencias.py, campo "prompt_imagem"/"personagem" agora exigidos
    em inglês) -- isso melhora a qualidade em QUALQUER fallback, não só este."""
    token = os.environ["REPLICATE_API_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Prefer": "wait"}

    body = {"input": {"prompt": prompt, "aspect_ratio": "9:16", "output_format": "jpg"}}
    if imagem_referencia:
        body["input"]["image"] = "data:image/jpeg;base64," + base64.b64encode(imagem_referencia).decode()

    ultimo_erro = None
    for tentativa in range(1, tentativas + 1):
        status_code = None
        try:
            resp = requests.post(
                "https://api.replicate.com/v1/models/black-forest-labs/flux-dev/predictions",
                headers=headers, json=body, timeout=90,
            )
            status_code = resp.status_code
            if status_code in (200, 201):
                dados = resp.json()
                if dados.get("status") == "succeeded" and dados.get("output"):
                    resp_img = requests.get(dados["output"][0], timeout=60)
                    resp_img.raise_for_status()
                    return resp_img.content
                ultimo_erro = f"status {dados.get('status')}: {dados.get('error')}"
            else:
                ultimo_erro = f"HTTP {status_code}: {resp.text[:300]}"
        except requests.exceptions.RequestException as e:
            # rede instável/reset -- não é erro definitivo, entra no
            # retry normal em vez de derrubar a run inteira (bug real
            # 2026-09-10: isso não tratado fazia o script inteiro
            # travar em vez de cair pro próximo fallback).
            ultimo_erro = f"erro de rede: {e}"

        if status_code in (401, 402, 403) or "credit" in ultimo_erro.lower() or "spend limit" in ultimo_erro.lower():
            raise RuntimeError(f"Replicate sem crédito/autorização: {ultimo_erro}")
        print(f"  [Replicate] tentativa {tentativa} falhou ({ultimo_erro[:120]}), esperando...")
        # rate limit padrão da Replicate é 6 predictions/min -- espera de
        # pelo menos 12s garante não estourar de novo na próxima tentativa
        espera = 15 if status_code == 429 else 3 * tentativa
        time.sleep(espera)

    raise RuntimeError(f"Replicate falhou após {tentativas} tentativas: {ultimo_erro}")


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
    roteiro: dict, canal, pasta_saida: str, imagens_por_cena: int = 2
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
    imagem_anterior = None
    usou_fallback = False
    # Bug real encontrado 2026-09-09: a mensagem de reprovação dizia sempre
    # "usou fallback Pollinations", mesmo quando quem gerou a imagem foi o
    # Modal -- confundia o diagnóstico (o vídeo ruim daquele dia tinha vindo
    # 100% do Modal, não do Pollinations, e o log não deixava isso claro).
    fonte_fallback = None
    hf_esgotado = False  # depois do primeiro esgotamento, nem tenta de novo (cota é bem curta)
    cloudflare_esgotado = False  # idem -- cota diária, não adianta insistir na mesma run
    modal_indisponivel = not (os.environ.get("MODAL_TOKEN_ID") and os.environ.get("MODAL_TOKEN_SECRET"))
    falai_indisponivel = not os.environ.get("FAL_KEY")
    falai_sem_credito = False  # sem crédito não é passageiro, não insiste na mesma run
    replicate_indisponivel = not os.environ.get("REPLICATE_API_TOKEN")
    replicate_sem_credito = False

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
            prompt = montar_prompt(prompt_base, canal, personagem, imagem_anterior is not None)
            imagem_bytes = None
            if not cloudflare_esgotado:
                try:
                    imagem_bytes = gerar_imagem(prompt, imagem_anterior)
                except CotaEsgotadaError as e:
                    print(f"  Cloudflare esgotado ({e}) — não tenta mais nessa run")
                    cloudflare_esgotado = True
                except RuntimeError as e:
                    print(f"  Cloudflare falhou ({e})")

            if imagem_bytes is None and not modal_indisponivel:
                try:
                    print("  tentando fallback Modal (FLUX.1-schnell)...")
                    imagem_bytes = gerar_imagem_modal(prompt, imagem_anterior)
                    # Bug real encontrado 2026-09-09: Modal só foi validado
                    # pro estilo dark/terror -- pra formatos bem diferentes
                    # (ex: novela de mascote, objeto falante) a qualidade e
                    # aderência ao estilo não têm garantia nenhuma. Vídeo
                    # inteiro caiu no Modal e foi aprovado/publicado sozinho
                    # sem essa trava, saindo "horrível" segundo o Davi.
                    usou_fallback = True
                    fonte_fallback = "Modal (FLUX.1-schnell)"
                except Exception as e_modal:
                    print(f"  Modal falhou ({e_modal})")

            if imagem_bytes is None and not replicate_indisponivel and not replicate_sem_credito:
                try:
                    print("  tentando fallback Replicate (FLUX.1 dev)...")
                    imagem_bytes = gerar_imagem_replicate(prompt, imagem_anterior)
                    usou_fallback = True
                    fonte_fallback = "Replicate (FLUX.1 dev)"
                except Exception as e_replicate:
                    print(f"  Replicate falhou ({e_replicate})")
                    if "crédito" in str(e_replicate) or "autorização" in str(e_replicate):
                        replicate_sem_credito = True

            if imagem_bytes is None and not falai_indisponivel and not falai_sem_credito:
                try:
                    print("  tentando fallback fal.ai (FLUX.1)...")
                    imagem_bytes = gerar_imagem_falai(prompt, imagem_anterior)
                    usou_fallback = True
                    fonte_fallback = "fal.ai (FLUX.1)"
                except Exception as e_falai:
                    print(f"  fal.ai falhou ({e_falai})")
                    if "crédito" in str(e_falai) or "autorização" in str(e_falai):
                        falai_sem_credito = True

            if imagem_bytes is None:
                if not hf_esgotado:
                    try:
                        print("  tentando fallback Hugging Face (FLUX.1 Kontext)...")
                        imagem_bytes = gerar_imagem_huggingface(prompt, imagem_anterior)
                    except Exception as e_hf:
                        print(f"  Hugging Face falhou/esgotou ({e_hf}) — não tenta mais nessa run")
                        hf_esgotado = True
                if imagem_bytes is None:
                    print("  caindo pro fallback Pollinations...")
                    imagem_bytes = gerar_imagem_pollinations(prompt)
                    usou_fallback = True
                    fonte_fallback = "Pollinations"

            nome = f"cena{i}.jpg" if imagens_por_cena == 1 else f"cena{i}_{parte}.jpg"
            caminho = os.path.join(pasta_saida, nome)
            with open(caminho, "wb") as f:
                f.write(imagem_bytes)
            print(f"  salvo em {caminho}")

            imagem_anterior = imagem_bytes
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

    gerar_imagens_do_roteiro(roteiro, canal, pasta_saida, imagens_por_cena=args.imagens_por_cena)

    print(
        f"\n{len(roteiro['cenas'])} imagens geradas em {pasta_saida} — custo: R$0,00. "
        "Confira visualmente antes de montar o vídeo."
    )


if __name__ == "__main__":
    main()
