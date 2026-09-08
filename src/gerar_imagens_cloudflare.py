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

        resp = requests.post(url, headers=headers, data=data, files=files)
        if resp.status_code == 200:
            dados = resp.json()
            if dados.get("success"):
                return base64.b64decode(dados["result"]["image"])
            ultimo_erro = f"Cloudflare retornou erro: {dados}"
        else:
            ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:300]}"

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


def gerar_imagens_do_roteiro(roteiro: dict, canal, pasta_saida: str, imagens_por_cena: int = 2) -> bool:
    """Gera e salva as imagens de cada cena do roteiro, encadeando sempre a
    última imagem gerada como referência da próxima (mantém o personagem
    consistente cena a cena E dentro da mesma cena). Com imagens_por_cena=2
    (padrão), salva cenaN_1.jpg/cenaN_2.jpg — o montar_video_local.py já
    sabe cortar entre as duas no meio da fala, o que dá bem mais sensação de
    movimento do que 1 imagem estática segurando a cena inteira (feedback:
    "vídeo muito parado" com poucas fotos e narração longa). Com
    imagens_por_cena=1, salva cenaN.jpg (formato antigo).

    Retorna True se ALGUMA imagem precisou do fallback Pollinations — o
    chamador usa isso pra decidir se publica sozinho ou não: o Pollinations
    já produziu imagem completamente diferente do personagem pedido (ex:
    "geladeira" virou um monstro ciclope), então vídeo com fallback não
    deve ir ao ar sem revisão humana."""
    os.makedirs(pasta_saida, exist_ok=True)
    personagem = roteiro.get("personagem")
    imagem_anterior = None
    usou_fallback = False
    hf_esgotado = False  # depois do primeiro esgotamento, nem tenta de novo (cota é bem curta)

    for i, cena in enumerate(roteiro["cenas"], start=1):
        for parte in range(1, imagens_por_cena + 1):
            print(f"Gerando imagem da cena {i} ({parte}/{imagens_por_cena})...")
            prompt_base = cena["prompt_imagem"] + VARIACOES_SUBCENA[(parte - 1) % len(VARIACOES_SUBCENA)]
            prompt = montar_prompt(prompt_base, canal, personagem, imagem_anterior is not None)
            try:
                imagem_bytes = gerar_imagem(prompt, imagem_anterior)
            except RuntimeError as e:
                print(f"  Cloudflare falhou ({e})")
                imagem_bytes = None
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

            nome = f"cena{i}.jpg" if imagens_por_cena == 1 else f"cena{i}_{parte}.jpg"
            caminho = os.path.join(pasta_saida, nome)
            with open(caminho, "wb") as f:
                f.write(imagem_bytes)
            print(f"  salvo em {caminho}")

            imagem_anterior = imagem_bytes
            time.sleep(2)

    return usou_fallback


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
