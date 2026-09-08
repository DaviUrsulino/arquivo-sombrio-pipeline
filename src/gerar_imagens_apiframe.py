"""Alternativa automatizada ao Nano Banana manual: gera as imagens das cenas
via Apiframe (api.apiframe.ai), que dá acesso a vários modelos (Nano Banana,
Flux, Midjourney, etc.) por um endpoint assíncrono único (job + polling).

AINDA NÃO VALIDADO VISUALMENTE — gere e confira as imagens antes de trocar
de vez o fluxo manual (ver README, seção "O que já foi validado").

Uso:
    python src/gerar_imagens_apiframe.py --roteiro roteiro_gerado.json \
        --saida ./imagens_aprovadas/ --modelo nano-banana-2-lite
"""

import argparse
import json
import os
import time

import requests
from dotenv import load_dotenv

from estilo import MASTER_STYLE_LOCK, RESTRICOES

load_dotenv()

API_BASE = "https://api.apiframe.ai/v2"


def montar_prompt_completo(prompt_imagem: str) -> str:
    return (
        f"{MASTER_STYLE_LOCK}{prompt_imagem} {RESTRICOES} "
        "Vertical 9:16 portrait aspect ratio, full frame, no letterboxing."
    )


def _headers(api_key: str) -> dict:
    return {"X-API-Key": api_key, "Content-Type": "application/json"}


def gerar_imagem(
    api_key: str, prompt: str, modelo: str, imagem_referencia_url: str | None
) -> str:
    body = {"model": modelo, "prompt": prompt}
    if imagem_referencia_url is not None:
        body["prompt"] = (
            "Use o mesmo personagem da imagem em anexo, mantendo rosto, "
            f"roupa e proporções idênticos. {prompt}"
        )
        body["image_input"] = [imagem_referencia_url]

    resp = requests.post(
        f"{API_BASE}/images/generate", headers=_headers(api_key), json=body
    )
    resp.raise_for_status()
    job_id = resp.json()["jobId"]

    while True:
        time.sleep(3)
        status_resp = requests.get(
            f"{API_BASE}/jobs/{job_id}", headers=_headers(api_key)
        )
        status_resp.raise_for_status()
        job = status_resp.json()

        if job["status"] == "COMPLETED":
            return job["result"][0]
        if job["status"] == "FAILED":
            raise RuntimeError(f"Apiframe retornou erro: {job}")
        print(f"  status: {job['status']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roteiro", default="roteiro_gerado.json")
    parser.add_argument("--saida", default="./imagens_aprovadas/")
    parser.add_argument(
        "--modelo",
        default="nano-banana-2-lite",
        help="Modelo do Apiframe (ex: nano-banana-2-lite, flux-schnell)",
    )
    args = parser.parse_args()

    os.makedirs(args.saida, exist_ok=True)

    with open(args.roteiro, encoding="utf-8") as f:
        roteiro = json.load(f)

    api_key = os.environ["APIFRAME_API_KEY"]

    url_anterior = None
    for i, cena in enumerate(roteiro["cenas"], start=1):
        print(f"Gerando imagem da cena {i} (modelo={args.modelo})...")
        prompt = montar_prompt_completo(cena["prompt_imagem"])
        url_gerada = gerar_imagem(api_key, prompt, args.modelo, url_anterior)

        caminho = os.path.join(args.saida, f"cena{i}.jpg")
        img_resp = requests.get(url_gerada)
        img_resp.raise_for_status()
        with open(caminho, "wb") as f:
            f.write(img_resp.content)
        print(f"  salvo em {caminho}")

        url_anterior = url_gerada

    print(
        f"\n{len(roteiro['cenas'])} imagens geradas em {args.saida}. "
        "CONFIRA VISUALMENTE antes de rodar montar_video.py."
    )


if __name__ == "__main__":
    main()
