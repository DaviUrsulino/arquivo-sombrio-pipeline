"""Passo 2 do pipeline: monta o vídeo final via API do JSON2Video, usando as
imagens já aprovadas manualmente no Leonardo AI + a narração do roteiro gerado.

Uso:
    python src/montar_video.py --roteiro roteiro_gerado.json --imagens ./imagens_aprovadas/

Configurações validadas manualmente em 2026-09-06 (ver README) — não mudar sem
testar de novo visualmente:
    - resolution: instagram-story (formato vertical correto, "vertical" sozinho não existe)
    - resize: cover em toda imagem (senão sobra barra preta)
    - duration: -2 (casa com a duração da narração da cena)
    - zoom: ok. NÃO usar "pan" (descentraliza o personagem).
    - voice: "Clyde" (ElevenLabs) — tom bom pra terror/suspense.
"""

import argparse
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.json2video.com/v2"
VOZ_PADRAO = "Clyde"


def _headers():
    return {"x-api-key": os.environ["JSON2VIDEO_API_KEY"]}


def upload_imagem(caminho_arquivo: str, nome_remoto: str) -> str:
    """Sobe uma imagem local pro JSON2Video (fluxo de 2 passos) e retorna a URL pública."""
    tamanho = os.path.getsize(caminho_arquivo)
    resp = requests.post(
        f"{API_BASE}/media/file",
        headers={**_headers(), "Content-Type": "application/json"},
        json={
            "name": nome_remoto,
            "contentType": "image/jpeg",
            "size": tamanho,
            "folder": "arquivo-sombrio",
        },
    )
    resp.raise_for_status()
    dados = resp.json()
    upload_url = dados["uploadUrl"]
    file_url = dados["fileUrl"]

    with open(caminho_arquivo, "rb") as f:
        put_resp = requests.put(
            upload_url, headers={"Content-Type": "image/jpeg"}, data=f
        )
    put_resp.raise_for_status()
    return file_url


def montar_json_filme(roteiro: dict, urls_imagens: list[str]) -> dict:
    cenas = []
    for cena, url_imagem in zip(roteiro["cenas"], urls_imagens):
        cenas.append(
            {
                "elements": [
                    {
                        "type": "image",
                        "src": url_imagem,
                        "duration": -2,
                        "zoom": 3,
                        "resize": "cover",
                    },
                    {
                        "type": "voice",
                        "model": "elevenlabs",
                        "voice": VOZ_PADRAO,
                        "text": cena["narracao"],
                    },
                ]
            }
        )
    return {"resolution": "instagram-story", "scenes": cenas}


def gerar_video(movie_json: dict) -> str:
    resp = requests.post(
        f"{API_BASE}/movies",
        headers={**_headers(), "Content-Type": "application/json"},
        json=movie_json,
    )
    resp.raise_for_status()
    return resp.json()["project"]


def aguardar_e_baixar(project_id: str, saida: str, timeout_s: int = 300):
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        resp = requests.get(
            f"{API_BASE}/movies", params={"project": project_id}, headers=_headers()
        )
        resp.raise_for_status()
        movie = resp.json()["movie"]
        status = movie["status"]
        print(f"status: {status}")

        if status == "done":
            video_resp = requests.get(movie["url"])
            video_resp.raise_for_status()
            with open(saida, "wb") as f:
                f.write(video_resp.content)
            print(f"\nVídeo salvo em: {saida}")
            return
        if status == "error":
            raise RuntimeError(f"JSON2Video retornou erro: {movie.get('message')}")

        time.sleep(10)

    raise TimeoutError("Vídeo não terminou de renderizar dentro do tempo limite.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roteiro", default="roteiro_gerado.json")
    parser.add_argument("--imagens", default="./imagens_aprovadas/")
    parser.add_argument("--saida", default="video_final.mp4")
    args = parser.parse_args()

    with open(args.roteiro, encoding="utf-8") as f:
        roteiro = json.load(f)

    n_cenas = len(roteiro["cenas"])
    urls_imagens = []
    for i in range(1, n_cenas + 1):
        caminho = os.path.join(args.imagens, f"cena{i}.jpg")
        if not os.path.exists(caminho):
            raise FileNotFoundError(
                f"Não encontrei {caminho} — gera e aprova a imagem dessa cena no Leonardo "
                "AI antes de rodar esse passo."
            )
        print(f"Subindo cena {i}...")
        url = upload_imagem(caminho, f"cena{i}.jpg")
        urls_imagens.append(url)

    print("\nMontando vídeo...")
    movie_json = montar_json_filme(roteiro, urls_imagens)
    project_id = gerar_video(movie_json)
    print(f"Projeto criado: {project_id}. Aguardando renderização...")
    aguardar_e_baixar(project_id, args.saida)


if __name__ == "__main__":
    main()
