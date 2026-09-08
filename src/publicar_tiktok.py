"""Publica o vídeo final automaticamente no TikTok, via Content Posting API
(Direct Post), usando o refresh token salvo em tiktok_token.json.

IMPORTANTE — enquanto o app não passa pela auditoria de produção da TikTok,
todo post sai como SELF_ONLY (só quem publicou vê). Depois da auditoria
aprovada, troca PRIVACY_LEVEL_PADRAO pra "PUBLIC_TO_EVERYONE".

Uso:
    python src/publicar_tiktok.py --video video_final.mp4 --titulo "Título"
"""

import argparse
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://open.tiktokapis.com/v2"
ARQUIVO_TOKEN = "tiktok_token.json"
PRIVACY_LEVEL_PADRAO = "SELF_ONLY"  # trocar pra PUBLIC_TO_EVERYONE após auditoria


def _carregar_token(arquivo_token: str) -> dict:
    with open(arquivo_token, encoding="utf-8") as f:
        return json.load(f)


def _salvar_token(dados: dict, arquivo_token: str):
    with open(arquivo_token, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2)


def obter_access_token(arquivo_token: str = ARQUIVO_TOKEN) -> str:
    token = _carregar_token(arquivo_token)
    resp = requests.post(
        f"{API_BASE}/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": os.environ["TIKTOK_CLIENT_KEY"],
            "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
            "grant_type": "refresh_token",
            "refresh_token": token["refresh_token"],
        },
    )
    resp.raise_for_status()
    dados = resp.json()

    token["refresh_token"] = dados["refresh_token"]
    _salvar_token(token, arquivo_token)

    return dados["access_token"]


def publicar_video(caminho_video: str, titulo: str, arquivo_token: str = ARQUIVO_TOKEN) -> str:
    """arquivo_token permite publicar em contas diferentes (ex: "Arquivo
    Sombrio" vs "Em Alta") sem misturar credenciais."""
    access_token = obter_access_token(arquivo_token)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    tamanho = os.path.getsize(caminho_video)
    corpo_init = {
        "post_info": {
            "title": titulo,
            "privacy_level": PRIVACY_LEVEL_PADRAO,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": tamanho,
            "chunk_size": tamanho,
            "total_chunk_count": 1,
        },
    }

    resp = requests.post(
        f"{API_BASE}/post/publish/video/init/", headers=headers, json=corpo_init
    )
    resp.raise_for_status()
    dados = resp.json()
    if dados.get("error", {}).get("code") != "ok":
        raise RuntimeError(f"TikTok retornou erro: {dados}")

    publish_id = dados["data"]["publish_id"]
    upload_url = dados["data"]["upload_url"]

    with open(caminho_video, "rb") as f:
        video_bytes = f.read()

    put_resp = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{tamanho - 1}/{tamanho}",
        },
        data=video_bytes,
    )
    put_resp.raise_for_status()

    print(f"Upload enviado. publish_id: {publish_id}. Aguardando processamento...")
    aguardar_status(access_token, publish_id)
    return publish_id


def aguardar_status(access_token: str, publish_id: str, timeout_s: int = 180):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        resp = requests.post(
            f"{API_BASE}/post/publish/status/fetch/",
            headers=headers,
            json={"publish_id": publish_id},
        )
        resp.raise_for_status()
        status = resp.json()["data"]["status"]
        print(f"status: {status}")

        if status == "PUBLISH_COMPLETE":
            print("\nPublicado com sucesso (SELF_ONLY até a auditoria ser aprovada).")
            return
        if status == "FAILED":
            raise RuntimeError("TikTok reportou falha na publicação.")

        time.sleep(5)

    raise TimeoutError("Publicação não concluiu dentro do tempo limite.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="video_final.mp4")
    parser.add_argument("--titulo", required=True)
    args = parser.parse_args()

    publicar_video(args.video, args.titulo)


if __name__ == "__main__":
    main()
