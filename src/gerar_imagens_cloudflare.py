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
import time

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


VARIACOES_SUBCENA = [
    "",  # primeira imagem: usa o prompt da cena como está
    ", slightly different camera angle, tighter framing, same moment continuing",
]


def gerar_imagens_do_roteiro(roteiro: dict, canal, pasta_saida: str, imagens_por_cena: int = 2) -> None:
    """Gera e salva as imagens de cada cena do roteiro, encadeando sempre a
    última imagem gerada como referência da próxima (mantém o personagem
    consistente cena a cena E dentro da mesma cena). Com imagens_por_cena=2
    (padrão), salva cenaN_1.jpg/cenaN_2.jpg — o montar_video_local.py já
    sabe cortar entre as duas no meio da fala, o que dá bem mais sensação de
    movimento do que 1 imagem estática segurando a cena inteira (feedback:
    "vídeo muito parado" com poucas fotos e narração longa). Com
    imagens_por_cena=1, salva cenaN.jpg (formato antigo)."""
    os.makedirs(pasta_saida, exist_ok=True)
    personagem = roteiro.get("personagem")
    imagem_anterior = None

    for i, cena in enumerate(roteiro["cenas"], start=1):
        for parte in range(1, imagens_por_cena + 1):
            print(f"Gerando imagem da cena {i} ({parte}/{imagens_por_cena})...")
            prompt_base = cena["prompt_imagem"] + VARIACOES_SUBCENA[(parte - 1) % len(VARIACOES_SUBCENA)]
            prompt = montar_prompt(prompt_base, canal, personagem, imagem_anterior is not None)
            imagem_bytes = gerar_imagem(prompt, imagem_anterior)

            nome = f"cena{i}.jpg" if imagens_por_cena == 1 else f"cena{i}_{parte}.jpg"
            caminho = os.path.join(pasta_saida, nome)
            with open(caminho, "wb") as f:
                f.write(imagem_bytes)
            print(f"  salvo em {caminho}")

            imagem_anterior = imagem_bytes
            time.sleep(2)


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
