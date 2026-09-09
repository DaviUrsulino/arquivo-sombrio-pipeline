"""Publica automaticamente no Instagram Reels via Instagram Graph API (Meta).

Setup necessário (uma vez só, feito pelo Davi):
    1. Converter a conta do Instagram pra Profissional (Criador ou Empresa).
    2. Vincular essa conta a uma Página do Facebook.
    3. Criar um app em developers.facebook.com com o produto "Instagram Graph API".
    4. Rodar src/obter_token_instagram.py pra gerar instagram_token.json.

A API do Instagram exige que o vídeo esteja numa URL PÚBLICA (ela busca o
arquivo, não aceita upload direto) — esse script hospeda o vídeo
temporariamente como asset de uma Release do próprio repositório GitHub e
apaga a release depois de publicar.

Uso:
    python src/publicar_instagram.py --video video_final.mp4 --legenda "Texto #hashtag"
"""

import argparse
import json
import os
import subprocess
import time
import uuid

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://graph.facebook.com/v21.0"
ARQUIVO_TOKEN = "instagram_token.json"
REPO_PADRAO = "DaviUrsulino/arquivo-sombrio-pipeline"


def _carregar_token(arquivo_token: str) -> dict:
    with open(arquivo_token, encoding="utf-8") as f:
        return json.load(f)


def hospedar_video_temporario(caminho_video: str, repo: str) -> tuple[str, str]:
    """Sobe o vídeo como asset de uma Release do GitHub pra ter uma URL
    pública temporária. Retorna (url, tag) — a tag é usada depois pra
    apagar a release."""
    tag = f"video-temp-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            "gh", "release", "create", tag, caminho_video,
            "-R", repo, "--title", tag, "--notes", "Vídeo temporário pra publicação automática (apagado depois).",
        ],
        check=True,
    )
    nome_arquivo = os.path.basename(caminho_video)
    url = f"https://github.com/{repo}/releases/download/{tag}/{nome_arquivo}"
    return url, tag


def apagar_release_temporaria(tag: str, repo: str):
    subprocess.run(["gh", "release", "delete", tag, "-R", repo, "--yes", "--cleanup-tag"], check=False)


def _aguardar_processamento(creation_id: str, access_token: str, timeout_s: int = 300):
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        resp = requests.get(
            f"{API_BASE}/{creation_id}",
            params={"fields": "status_code", "access_token": access_token},
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")
        print(f"  status: {status}")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError("Instagram reportou erro processando o vídeo.")
        time.sleep(5)
    raise TimeoutError("Processamento do vídeo no Instagram não terminou a tempo.")


def publicar_reel(caminho_video: str, legenda: str, repo: str = REPO_PADRAO, arquivo_token: str = ARQUIVO_TOKEN) -> str:
    dados_token = _carregar_token(arquivo_token)
    access_token = dados_token["access_token"]
    ig_user_id = dados_token["ig_user_id"]

    print("Hospedando vídeo temporariamente (GitHub Release)...")
    video_url, tag = hospedar_video_temporario(caminho_video, repo)

    try:
        print("Criando container de mídia no Instagram...")
        resp = requests.post(
            f"{API_BASE}/{ig_user_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": legenda,
                "access_token": access_token,
            },
        )
        resp.raise_for_status()
        creation_id = resp.json()["id"]

        print("Aguardando o Instagram processar o vídeo...")
        _aguardar_processamento(creation_id, access_token)

        print("Publicando...")
        resp = requests.post(
            f"{API_BASE}/{ig_user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": access_token},
        )
        resp.raise_for_status()
        return resp.json()["id"]
    finally:
        print("Removendo o vídeo temporário do GitHub Releases...")
        apagar_release_temporaria(tag, repo)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="video_final.mp4")
    parser.add_argument("--legenda", required=True)
    parser.add_argument("--repo", default=REPO_PADRAO)
    args = parser.parse_args()

    media_id = publicar_reel(args.video, args.legenda, args.repo)
    print(f"\nPublicado! media_id: {media_id}")


if __name__ == "__main__":
    main()
