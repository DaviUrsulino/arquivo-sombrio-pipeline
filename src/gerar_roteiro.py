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

from anthropic import Anthropic
from dotenv import load_dotenv

from estilo import MASTER_STYLE_LOCK, RESTRICOES

load_dotenv()

SYSTEM_PROMPT = f"""Você escreve roteiros curtos de terror (estilo creepypasta) para um canal \
dark de TikTok/YouTube Shorts chamado "Arquivo Sombrio". Regras:

- Sempre 5 cenas, cada uma com ~8-10 segundos de narração falada (não escreva a duração, \
apenas o texto).
- Narrador único, em primeira pessoa, tom calmo e contido (nunca gritando) — o medo vem da \
atmosfera, não do choque.
- Zero gore, zero violência gráfica — adequado pra qualquer plataforma.
- Escalada de tensão: começo calmo, meio com desconforto crescente, final com revelação \
perturbadora (gancho, sem resolver tudo).
- Personagem principal: sempre o mesmo ao longo das 5 cenas, descreva ele UMA vez com detalhe \
suficiente (idade, porte físico, roupa, cabelo) pra reaproveitar a descrição em todas as cenas.
- Cada cena precisa favorecer um enquadramento ESTÁTICO e de UM personagem só (sentado, \
olhando, segurando objeto) — evite cenas de ação/movimento ou com dois personagens interagindo, \
porque isso já causou falha de geração de imagem em teste anterior (ver README do projeto).

Sua resposta deve ser APENAS um JSON válido, sem texto antes ou depois, no formato:
{{
  "personagem": "descrição completa e reutilizável do personagem principal",
  "cenas": [
    {{"narracao": "texto que o narrador fala nesta cena", "prompt_imagem": "descrição da cena \
para gerar imagem, incluindo a descrição do personagem repetida"}},
    ...
  ]
}}

O campo "prompt_imagem" de cada cena deve, quando combinado com o master style lock \
(fornecido separadamente pelo código, não repita aqui), formar um prompt completo pronto pra \
colar num gerador de imagem. Não inclua o master style lock nem as restrições no seu \
"prompt_imagem" — isso é adicionado depois pelo código."""


def gerar_roteiro(tema: str) -> dict:
    client = Anthropic()
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Tema/premissa da história: {tema}"},
        ],
    )
    texto = "".join(block.text for block in response.content if block.type == "text")
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        print("Aviso: resposta não veio em JSON puro, tentando extrair...", file=sys.stderr)
        inicio = texto.find("{")
        fim = texto.rfind("}") + 1
        return json.loads(texto[inicio:fim])


def montar_prompts_completos(roteiro: dict) -> list[str]:
    prompts = []
    for cena in roteiro["cenas"]:
        prompt_completo = (
            f"{MASTER_STYLE_LOCK}{cena['prompt_imagem']} {RESTRICOES}"
        )
        prompts.append(prompt_completo)
    return prompts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tema", required=True, help="Tema/premissa da história de terror")
    parser.add_argument(
        "--saida", default="roteiro_gerado.json", help="Arquivo de saída do roteiro"
    )
    args = parser.parse_args()

    print(f"Gerando roteiro pro tema: {args.tema}\n")
    roteiro = gerar_roteiro(args.tema)

    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)

    print(f"Roteiro salvo em {args.saida}\n")
    print("=" * 60)
    print("PERSONAGEM:")
    print(roteiro["personagem"])
    print("=" * 60)

    prompts = montar_prompts_completos(roteiro)
    for i, prompt in enumerate(prompts, start=1):
        print(f"\n--- Cena {i}: prompt pra colar no Leonardo AI ---")
        print(prompt)

    print(
        "\n\nGere as imagens no Leonardo AI (formato vertical/portrait), aprove visualmente, "
        "e salve como cena1.jpg, cena2.jpg, ... numa pasta (ex: ./imagens_aprovadas/). "
        "Depois rode: python src/montar_video.py"
    )


if __name__ == "__main__":
    main()
