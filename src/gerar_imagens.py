"""Alternativa ao passo manual do Leonardo AI: gera as imagens das cenas via
Gemini (Nano Banana / gemini-3.1-flash-image), usando a imagem da cena
anterior como referência pra manter o personagem consistente.

AINDA NÃO VALIDADO VISUALMENTE (ver README, seção "O que já foi validado") —
gere e confira as imagens antes de considerar esse fluxo pronto pra
substituir o Leonardo AI de vez.

Uso:
    python src/gerar_imagens.py --roteiro roteiro_gerado.json --saida ./imagens_aprovadas/
"""

import argparse
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from estilo import MASTER_STYLE_LOCK, RESTRICOES

load_dotenv()

MODELO_IMAGEM = "gemini-3.1-flash-image"


def montar_prompt_completo(prompt_imagem: str) -> str:
    return f"{MASTER_STYLE_LOCK}{prompt_imagem} {RESTRICOES}"


def gerar_imagem(client, prompt: str, imagem_referencia: bytes | None) -> bytes:
    conteudo = [prompt]
    if imagem_referencia is not None:
        conteudo.insert(
            0,
            types.Part.from_bytes(data=imagem_referencia, mime_type="image/jpeg"),
        )
        conteudo[1] = (
            "Use o mesmo personagem da imagem em anexo, mantendo rosto, "
            "roupa e proporções idênticos. Só muda a pose/ação/expressão "
            f"descrita a seguir: {prompt}"
        )

    response = client.models.generate_content(model=MODELO_IMAGEM, contents=conteudo)

    for parte in response.candidates[0].content.parts:
        if parte.inline_data is not None:
            return parte.inline_data.data

    raise RuntimeError("Gemini não retornou imagem nessa resposta.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roteiro", default="roteiro_gerado.json")
    parser.add_argument("--saida", default="./imagens_aprovadas/")
    args = parser.parse_args()

    os.makedirs(args.saida, exist_ok=True)

    with open(args.roteiro, encoding="utf-8") as f:
        roteiro = json.load(f)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    imagem_anterior = None
    for i, cena in enumerate(roteiro["cenas"], start=1):
        print(f"Gerando imagem da cena {i}...")
        prompt = montar_prompt_completo(cena["prompt_imagem"])
        imagem_bytes = gerar_imagem(client, prompt, imagem_anterior)

        caminho = os.path.join(args.saida, f"cena{i}.jpg")
        with open(caminho, "wb") as f:
            f.write(imagem_bytes)
        print(f"  salvo em {caminho}")

        imagem_anterior = imagem_bytes

    print(
        f"\n{len(roteiro['cenas'])} imagens geradas em {args.saida}. "
        "CONFIRA VISUALMENTE antes de rodar montar_video.py — isso ainda "
        "não foi validado (ver README)."
    )


if __name__ == "__main__":
    main()
