"""Passo único: converte um token de curta duração do Graph API Explorer
num token de longa duração (~60 dias, renovável) e descobre o ID da conta
comercial do Instagram — salva tudo em instagram_token.json.

Antes de rodar isso:
    1. Vai em developers.facebook.com/tools/explorer
    2. Seleciona o SEU app (o que você criou com o produto Instagram Graph API)
    3. Em "User or Page", garante que está com o usuário certo
    4. Em "Permissions", adiciona: instagram_basic, instagram_content_publish,
       pages_show_list, pages_read_engagement
    5. Clica "Generate Access Token", autoriza, e copia o token gerado
       (é de curta duração, ~1h — por isso esse script já resolve tudo na hora)

Uso:
    python src/obter_token_instagram.py --token-curto "EAAxxxx..."
"""

import argparse
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://graph.facebook.com/v21.0"


def trocar_por_token_longo(token_curto: str, app_id: str, app_secret: str) -> str:
    resp = requests.get(
        f"{API_BASE}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": token_curto,
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def descobrir_ig_user_id(access_token: str) -> str:
    resp = requests.get(f"{API_BASE}/me/accounts", params={"access_token": access_token})
    resp.raise_for_status()
    paginas = resp.json().get("data", [])
    if not paginas:
        raise RuntimeError(
            "Nenhuma Página do Facebook encontrada pra essa conta — confere se a conta do "
            "Instagram já está vinculada a uma Página do Facebook."
        )

    pagina_id = paginas[0]["id"]
    print(f"Página do Facebook encontrada: {paginas[0]['name']} ({pagina_id})")

    resp = requests.get(
        f"{API_BASE}/{pagina_id}",
        params={"fields": "instagram_business_account", "access_token": access_token},
    )
    resp.raise_for_status()
    dados = resp.json()
    ig_account = dados.get("instagram_business_account")
    if not ig_account:
        raise RuntimeError(
            "Essa Página do Facebook não tem conta do Instagram vinculada — confere o passo "
            "de vincular a conta profissional do Instagram à Página."
        )
    return ig_account["id"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token-curto", required=True, help="Token gerado no Graph API Explorer")
    parser.add_argument("--saida", default="instagram_token.json")
    args = parser.parse_args()

    app_id = os.environ["FACEBOOK_APP_ID"]
    app_secret = os.environ["FACEBOOK_APP_SECRET"]

    print("Trocando por token de longa duração...")
    token_longo = trocar_por_token_longo(args.token_curto, app_id, app_secret)

    print("Descobrindo o ID da conta comercial do Instagram...")
    ig_user_id = descobrir_ig_user_id(token_longo)

    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump({"access_token": token_longo, "ig_user_id": ig_user_id}, f, indent=2)

    print(f"\nSalvo em {args.saida}. Esse token dura ~60 dias — depois disso precisa gerar de novo.")


if __name__ == "__main__":
    main()
