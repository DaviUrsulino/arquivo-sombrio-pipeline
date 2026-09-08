"""Passo único (por conta) pra obter o refresh_token inicial do TikTok via
OAuth. Depois de rodar isso uma vez, publicar_tiktok.py renova o token
sozinho — não precisa repetir esse processo, exceto pra logar numa conta
TikTok NOVA (ex: a conta da "Em Alta").

Usa o MESMO app do TikTok (TIKTOK_CLIENT_KEY/SECRET no .env) que já existe —
não precisa criar um app novo, só autorizar com a conta TikTok certa.

Uso:
    python src/obter_token_tiktok.py --saida tiktok_token_tendencias.json \
        --redirect-uri "https://SEU-CALLBACK-JA-CADASTRADO-NO-APP"

O --redirect-uri tem que ser EXATAMENTE igual ao que está cadastrado no
TikTok Developer Portal (developers.tiktok.com > seu app > Login Kit >
Redirect URI) — copie de lá, não invente um novo.
"""

import argparse
import json
import os
import urllib.parse

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://open.tiktokapis.com/v2"
SCOPES = "user.info.basic,video.publish,video.upload"


def montar_url_autorizacao(redirect_uri: str) -> str:
    params = {
        "client_key": os.environ["TIKTOK_CLIENT_KEY"],
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": redirect_uri,
        "state": "obter_token_inicial",
    }
    return f"https://www.tiktok.com/v2/auth/authorize/?{urllib.parse.urlencode(params)}"


def trocar_code_por_token(code: str, redirect_uri: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": os.environ["TIKTOK_CLIENT_KEY"],
            "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", required=True, help="ex: tiktok_token_tendencias.json")
    parser.add_argument("--redirect-uri", required=True, help="callback já cadastrado no app do TikTok")
    args = parser.parse_args()

    print("1. Abra esta URL no navegador, LOGADO NA CONTA TIKTOK CORRETA pra esse canal:\n")
    print(montar_url_autorizacao(args.redirect_uri))
    print(
        "\n2. Autorize o app. O navegador vai te redirecionar pra uma URL com "
        "'?code=...' — copie a URL INTEIRA da barra de endereço e cole abaixo:"
    )
    url_final = input("> ").strip()

    query = urllib.parse.urlparse(url_final).query
    parametros = urllib.parse.parse_qs(query)
    if "code" not in parametros:
        raise SystemExit("Não achei '?code=' na URL colada — confere se copiou a URL certa.")
    code = parametros["code"][0]

    dados = trocar_code_por_token(code, args.redirect_uri)
    resultado = {"refresh_token": dados["refresh_token"], "open_id": dados["open_id"]}

    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2)

    print(f"\nToken salvo em {args.saida}. Agora cadastra o CONTEÚDO desse arquivo como secret no GitHub.")


if __name__ == "__main__":
    main()
