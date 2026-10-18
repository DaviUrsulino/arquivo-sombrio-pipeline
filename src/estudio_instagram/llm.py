"""Chama um LLM e devolve JSON, tentando provedores gratuitos em cascata.

Ordem: Gemini (várias chaves e modelos) -> OpenRouter (modelos ":free") -> Mistral. É a mesma
ideia do `src/gerar_roteiro.py` do canal Arquivo Sombrio (ADR-0001): se um provedor está fora
do ar ou sem cota, cai no próximo, para o cron não falhar por problema de terceiro.

Só usa a biblioteca padrão (urllib); nada de SDK nem `requests`, para o job do Instagram instalar pouca coisa.
"""

import json
import os
import re
import sys
import time

import urllib.parse
import urllib.request

MODELOS_GEMINI = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]
MODELOS_OPENROUTER_ESTATICOS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free", "google/gemma-4-31b-it:free", "nvidia/nemotron-3-super-120b-a12b:free",
]
MODELOS_MISTRAL = ["mistral-small-latest", "open-mistral-nemo"]


class LLMIndisponivel(RuntimeError):
    pass


def _post_json(url: str, corpo: dict, cabecalhos: dict | None = None, params: dict | None = None, timeout: int = 90) -> dict:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    pedido = urllib.request.Request(
        url, data=json.dumps(corpo).encode(), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "estudio-automatico/1.0", **(cabecalhos or {})},
    )
    with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
        return json.load(resposta)


def extrair_json(texto: str) -> dict:
    """Pega o primeiro objeto JSON do texto (modelos às vezes embrulham em ```json ... ```)."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.S)
    inicio = texto.find("{")
    if inicio < 0:
        raise ValueError("resposta sem objeto JSON")
    fundo, dentro = 0, False
    for i in range(inicio, len(texto)):
        c = texto[i]
        if c == '"' and texto[i - 1] != "\\":
            dentro = not dentro
        elif not dentro:
            fundo += c == "{"
            fundo -= c == "}"
            if fundo == 0:
                return json.loads(texto[inicio:i + 1])
    raise ValueError("JSON truncado")


def _chaves_gemini() -> list[str]:
    varias = os.environ.get("GEMINI_API_KEYS", "")
    chaves = [c.strip() for c in varias.split(",") if c.strip()]
    if not chaves and os.environ.get("GEMINI_API_KEY"):
        chaves = [os.environ["GEMINI_API_KEY"].strip()]
    return chaves


def _gemini(sistema: str, usuario: str, post=_post_json) -> dict:
    ultimo = None
    for chave in _chaves_gemini():
        for modelo in MODELOS_GEMINI:
            try:
                r = post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                    {
                        "systemInstruction": {"parts": [{"text": sistema}]},
                        "contents": [{"role": "user", "parts": [{"text": usuario}]}],
                        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8},
                    },
                    params={"key": chave},
                )
                return extrair_json(r["candidates"][0]["content"]["parts"][0]["text"])
            except Exception as erro:  # 503, cota, JSON ruim: tenta o próximo
                ultimo = erro
                print(f"  gemini {modelo} falhou ({str(erro)[:120]})", file=sys.stderr)
                time.sleep(1)
    raise LLMIndisponivel(f"Gemini falhou: {ultimo}")


def _openai_compativel(url: str, chave: str, modelos: list[str], sistema: str, usuario: str, post=_post_json) -> dict:
    ultimo = None
    for modelo in modelos:
        try:
            r = post(
                url,
                {"model": modelo, "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
                 "response_format": {"type": "json_object"}, "temperature": 0.8},
                cabecalhos={"Authorization": f"Bearer {chave}"},
            )
            return extrair_json(r["choices"][0]["message"]["content"])
        except Exception as erro:
            ultimo = erro
            print(f"  {modelo} falhou ({str(erro)[:120]})", file=sys.stderr)
            time.sleep(1)
    raise LLMIndisponivel(str(ultimo))


def gerar_json(sistema: str, usuario: str) -> dict:
    """Primeiro provedor que responder com JSON válido. Levanta LLMIndisponivel se todos falharem."""
    erros = []
    if _chaves_gemini():
        try:
            return _gemini(sistema, usuario)
        except LLMIndisponivel as erro:
            erros.append(str(erro))
    if os.environ.get("OPENROUTER_API_KEY"):
        try:
            return _openai_compativel("https://openrouter.ai/api/v1/chat/completions", os.environ["OPENROUTER_API_KEY"],
                                      MODELOS_OPENROUTER_ESTATICOS, sistema, usuario)
        except LLMIndisponivel as erro:
            erros.append(f"OpenRouter: {erro}")
    if os.environ.get("MISTRAL_API_KEY"):
        try:
            return _openai_compativel("https://api.mistral.ai/v1/chat/completions", os.environ["MISTRAL_API_KEY"],
                                      MODELOS_MISTRAL, sistema, usuario)
        except LLMIndisponivel as erro:
            erros.append(f"Mistral: {erro}")
    raise LLMIndisponivel("nenhum provedor respondeu: " + " | ".join(erros) if erros else "nenhuma chave de LLM configurada")
