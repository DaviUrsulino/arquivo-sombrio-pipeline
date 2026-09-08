"""Alternativa automatizada ao Nano Banana manual: gera as imagens das cenas
via ImageGPT (api.imagegpt.online), que dá acesso a vários modelos (Flux
Schnell, Nano Banana, etc.) por um único endpoint, com créditos grátis no
cadastro.

AINDA NÃO VALIDADO VISUALMENTE — gere e confira as imagens antes de trocar
de vez o fluxo manual (ver README, seção "O que já foi validado").

Uso:
    python src/gerar_imagens_imagegpt.py --roteiro roteiro_gerado.json \
        --saida ./imagens_aprovadas/ --modelo FLUX-SCHNELL
"""

import argparse
import json
import os

import requests
from dotenv import load_dotenv

from estilo import MASTER_STYLE_LOCK, RESTRICOES

load_dotenv()

API_URL = "https://api.imagegpt.online/generate/text-image"
LARGURA_PADRAO = 720
ALTURA_PADRAO = 1280


def montar_prompt_completo(prompt_imagem: str) -> str:
    return (
        f"{MASTER_STYLE_LOCK}{prompt_imagem} {RESTRICOES} "
        "Vertical 9:16 portrait aspect ratio, full frame, no letterboxing."
    )


def gerar_imagem(
    api_key: str, prompt: str, modelo: str, imagem_referencia_url: str | None
) -> bytes:
    body = {
        "model": modelo,
        "prompt": prompt,
        "width": LARGURA_PADRAO,
        "height": ALTURA_PADRAO,
        "outputType": "url",
        "outputFormat": "jpg",
    }
    if imagem_referencia_url is not None:
        body["image"] = [imagem_referencia_url]
        body["prompt"] = (
            "Use o mesmo personagem da imagem em anexo, mantendo rosto, "
            f"roupa e proporções idênticos. {prompt}"
        )

    resp = requests.post(
        API_URL,
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        json=body,
    )
    resp.raise_for_status()
    dados = resp.json()
    if not dados.get("success"):
        raise RuntimeError(f"ImageGPT retornou erro: {dados}")

    url_imagem = dados["url"]
    print(f"  créditos gastos: {dados.get('creditsDeducted')}")

    img_resp = requests.get(url_imagem)
    img_resp.raise_for_status()
    return img_resp.content, url_imagem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roteiro", default="roteiro_gerado.json")
    parser.add_argument("--saida", default="./imagens_aprovadas/")
    parser.add_argument(
        "--modelo",
        default="FLUX-SCHNELL",
        help="Modelo do ImageGPT (ex: FLUX-SCHNELL, NANO-BANANA)",
    )
    args = parser.parse_args()

    os.makedirs(args.saida, exist_ok=True)

    with open(args.roteiro, encoding="utf-8") as f:
        roteiro = json.load(f)

    api_key = os.environ["IMAGEGPT_API_KEY"]

    url_anterior = None
    for i, cena in enumerate(roteiro["cenas"], start=1):
        print(f"Gerando imagem da cena {i} (modelo={args.modelo})...")
        prompt = montar_prompt_completo(cena["prompt_imagem"])
        imagem_bytes, url_gerada = gerar_imagem(api_key, prompt, args.modelo, url_anterior)

        caminho = os.path.join(args.saida, f"cena{i}.jpg")
        with open(caminho, "wb") as f:
            f.write(imagem_bytes)
        print(f"  salvo em {caminho}")

        url_anterior = url_gerada

    print(
        f"\n{len(roteiro['cenas'])} imagens geradas em {args.saida}. "
        "CONFIRA VISUALMENTE antes de rodar montar_video.py."
    )


if __name__ == "__main__":
    main()
