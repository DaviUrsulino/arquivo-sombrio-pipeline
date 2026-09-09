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

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from canais import carregar_canal

load_dotenv()

# Modelos tentados em ordem — se um estiver sobrecarregado (503), cai pro
# próximo antes de desistir.
MODELOS_FALLBACK = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]

# Modelos gratuitos do OpenRouter, usados só se o Gemini falhar (todas as
# chaves/modelos) — free tier de 50 req/dia sem custo nenhum, validado em
# 2026-09-08 depois de o Gemini cair 503 nos 3 modelos ao mesmo tempo. A
# lista de modelos ":free" do OpenRouter muda com frequência (modelo que
# existia na pesquisa já tinha sumido dias depois) — por isso busca a lista
# atual em tempo real em vez de confiar num nome fixo que pode não existir
# mais. Essa lista aqui é só o fallback final se a busca falhar.
MODELOS_OPENROUTER_FALLBACK_ESTATICO = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]


def _modelos_openrouter_disponiveis(chave: str) -> list[str]:
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {chave}"},
            timeout=15,
        )
        resp.raise_for_status()
        modelos = [m["id"] for m in resp.json()["data"] if m["id"].endswith(":free")]
        if modelos:
            return modelos[:5]
    except Exception:
        pass
    return MODELOS_OPENROUTER_FALLBACK_ESTATICO


def _gerar_roteiro_openrouter(tema: str, canal) -> dict:
    chave = os.environ.get("OPENROUTER_API_KEY")
    if not chave:
        raise RuntimeError("Gemini falhou e OPENROUTER_API_KEY não está configurada — sem fallback disponível.")

    ultimo_erro = None
    for modelo in _modelos_openrouter_disponiveis(chave):
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
                json={
                    "model": modelo,
                    "messages": [
                        {"role": "system", "content": canal.SYSTEM_PROMPT},
                        {"role": "user", "content": f"Tema/premissa da história: {tema}"},
                    ],
                    "response_format": {"type": "json_object"},
                },
                timeout=45,
            )
            resp.raise_for_status()
            dados = resp.json()
            texto = dados["choices"][0]["message"]["content"]
            print(f"(Gemini indisponível — usando fallback OpenRouter: {modelo})", file=sys.stderr)
            return texto
        except Exception as e:
            ultimo_erro = e
            print(f"  OpenRouter {modelo} falhou ({e}), tentando próxima opção...", file=sys.stderr)
            time.sleep(2)

    raise RuntimeError(f"Gemini e todos os modelos do OpenRouter falharam. Último erro: {ultimo_erro}")


# Modelos do Mistral (La Plateforme) — free tier com cota de tokens/mês bem
# maior que o OpenRouter (~1 bilhão de tokens/mês vs 50 req/dia), usado como
# terceira camada pra não sobrecarregar a cota do OpenRouter sozinha.
MODELOS_MISTRAL_FALLBACK = ["mistral-small-latest", "open-mistral-nemo"]


def _gerar_roteiro_mistral(tema: str, canal) -> dict:
    chave = os.environ.get("MISTRAL_API_KEY")
    if not chave:
        raise RuntimeError("Gemini e OpenRouter falharam e MISTRAL_API_KEY não está configurada.")

    ultimo_erro = None
    for modelo in MODELOS_MISTRAL_FALLBACK:
        try:
            resp = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
                json={
                    "model": modelo,
                    "messages": [
                        {"role": "system", "content": canal.SYSTEM_PROMPT},
                        {"role": "user", "content": f"Tema/premissa da história: {tema}"},
                    ],
                    "response_format": {"type": "json_object"},
                },
                timeout=45,
            )
            resp.raise_for_status()
            texto = resp.json()["choices"][0]["message"]["content"]
            print(f"(Gemini e OpenRouter indisponíveis — usando fallback Mistral: {modelo})", file=sys.stderr)
            return texto
        except Exception as e:
            ultimo_erro = e
            print(f"  Mistral {modelo} falhou ({e}), tentando próxima opção...", file=sys.stderr)
            time.sleep(2)

    raise RuntimeError(f"Gemini, OpenRouter e Mistral falharam. Último erro: {ultimo_erro}")


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
            except ClientError as e:
                # Bug real encontrado 2026-09-09: 429 (cota diária esgotada)
                # não era pego aqui, então nunca caía pro fallback
                # OpenRouter/Mistral -- quebrava a execução do cron inteira
                # assim que a cota do Gemini estourasse (mais provável de
                # acontecer em produção do que um 503 passageiro).
                ultimo_erro = e
                print(f"  {modelo} indisponível ({e.code if hasattr(e, 'code') else e}), tentando próxima opção...", file=sys.stderr)
                time.sleep(2)
                continue
        else:
            continue  # essa chave esgotou os modelos, tenta a próxima chave
        break  # deu certo, não precisa tentar outra chave
    else:
        print(
            f"Gemini indisponível em todas as chaves/modelos (último erro: {ultimo_erro}) — "
            "tentando fallback OpenRouter...",
            file=sys.stderr,
        )
        try:
            texto = _gerar_roteiro_openrouter(tema, canal)
        except Exception as e_or:
            print(f"OpenRouter também falhou ({e_or}) — tentando fallback Mistral...", file=sys.stderr)
            texto = _gerar_roteiro_mistral(tema, canal)
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            inicio = texto.find("{")
            fim = texto.rfind("}") + 1
            return json.loads(texto[inicio:fim])

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
        "--canal", default="terror", help="Nome do canal (ver src/canais/): terror"
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
