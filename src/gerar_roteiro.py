"""Passo 1 do pipeline: gera roteiro + prompts de imagem via API do Claude.

Uso:
    python src/gerar_roteiro.py --tema "escritório abandonado, regras impossíveis"

Saída:
    roteiro_gerado.json (na raiz do projeto) + prompts impressos no terminal,
    prontos pra colar no Leonardo AI.
"""

import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

from canais import carregar_canal

load_dotenv()

# Modelos tentados em ordem — se um estiver sobrecarregado (503), cai pro
# próximo antes de desistir.
MODELOS_FALLBACK = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]


def _chaves_api() -> list[str]:
    """Lê GEMINI_API_KEY (uma) ou GEMINI_API_KEYS (várias, separadas por \
    vírgula) — permite ter uma chave reserva pra quando a principal cair."""
    varias = os.environ.get("GEMINI_API_KEYS")
    if varias:
        return [k.strip() for k in varias.split(",") if k.strip()]
    return [os.environ["GEMINI_API_KEY"]]


def gerar_roteiro(tema: str, canal) -> dict:
    chaves = _chaves_api()
    ultimo_erro = None

    for chave in chaves:
        # timeout explícito: sem isso, uma chamada que trava na rede fica presa
        # indefinidamente (já aconteceu) — crítico num pipeline automatizado
        # que não tem ninguém olhando pra matar o processo manualmente.
        client = genai.Client(api_key=chave, http_options=types.HttpOptions(timeout=45_000))
        for modelo in MODELOS_FALLBACK:
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=f"Tema/premissa da história: {tema}",
                    config=types.GenerateContentConfig(
                        system_instruction=canal.SYSTEM_PROMPT,
                        response_mime_type="application/json",
                    ),
                )
                if modelo != MODELOS_FALLBACK[0]:
                    print(f"(usando modelo de reserva: {modelo})", file=sys.stderr)
                break
            except ServerError as e:
                ultimo_erro = e
                print(f"  {modelo} indisponível (503), tentando próxima opção...", file=sys.stderr)
                time.sleep(2)
                continue
        else:
            continue  # essa chave esgotou os modelos, tenta a próxima chave
        break  # deu certo, não precisa tentar outra chave
    else:
        raise RuntimeError(
            f"Todas as chaves/modelos falharam. Último erro: {ultimo_erro}"
        )

    texto = response.text
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        print("Aviso: resposta não veio em JSON puro, tentando extrair...", file=sys.stderr)
        inicio = texto.find("{")
        fim = texto.rfind("}") + 1
        return json.loads(texto[inicio:fim])


def montar_prompts_completos(roteiro: dict, canal) -> list[str]:
    personagem = roteiro.get("personagem")
    descricao_personagem = f"{personagem}. " if personagem else ""
    prompts = []
    for cena in roteiro["cenas"]:
        prompt_completo = (
            f"{canal.MASTER_STYLE_LOCK}{descricao_personagem}{cena['prompt_imagem']} "
            f"{canal.RESTRICOES} "
            "Vertical 9:16 portrait aspect ratio, full frame, no letterboxing."
        )
        prompts.append(prompt_completo)
    return prompts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--canal", default="terror", help="Nome do canal (ver src/canais/): terror, true_crime"
    )
    parser.add_argument("--tema", required=True, help="Tema/premissa da história")
    parser.add_argument("--saida", default=None, help="Arquivo de saída do roteiro")
    args = parser.parse_args()

    canal = carregar_canal(args.canal)
    saida = args.saida or f"roteiro_{args.canal}.json"

    print(f"Gerando roteiro pro canal '{canal.NOME_CANAL}', tema: {args.tema}\n")
    roteiro = gerar_roteiro(args.tema, canal)

    with open(saida, "w", encoding="utf-8") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)

    print(f"Roteiro salvo em {saida}\n")
    print("=" * 60)
    for chave in ("personagem", "titulo_caso"):
        if chave in roteiro:
            print(f"{chave.upper()}: {roteiro[chave]}")
    print("=" * 60)

    prompts = montar_prompts_completos(roteiro, canal)
    for i, prompt in enumerate(prompts, start=1):
        print(f"\n--- Cena {i}: prompt pra colar no gerador de imagem ---")
        print(prompt)

    print(
        f"\n\nGere as imagens, aprove visualmente, e salve como cena1.jpg, cena2.jpg, ... "
        f"em ./{canal.PASTA_IMAGENS}/. Depois rode: "
        f"python src/montar_video.py --canal {args.canal} --roteiro {saida}"
    )


if __name__ == "__main__":
    main()
