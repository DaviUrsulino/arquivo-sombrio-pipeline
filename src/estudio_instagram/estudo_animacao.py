"""Estudo semanal de animação: o que os perfis de referência estão postando e o que está dando view.

Lê referencias/referencias.json, puxa os Reels recentes de cada perfil pelo Apify, escolhe os que mais renderam
(views relativas à média do próprio perfil), baixa e monta uma folha quadro a quadro de cada um. Salva tudo em
referencias/estudos/AAAA-MM-DD/ com um relatorio.md (gancho, duração, views, link e a folha), pra virar
identidade nova numa sessão de trabalho. Custo: ~US$ 0,0027 por post (16 perfis x 4 posts = ~US$ 0,17/semana).

    python -m src.estudio_instagram.estudo_animacao
"""

import json
import os
import subprocess
import urllib.request
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
REFS = RAIZ / "referencias" / "referencias.json"
POSTS_POR_PERFIL = 4
ESCOLHIDOS = 10
ATOR = "https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items"


def buscar(perfis: list[str], token: str, abrir=urllib.request.urlopen) -> list[dict]:
    corpo = json.dumps({"directUrls": [f"https://www.instagram.com/{p}/" for p in perfis], "resultsType": "posts",
                        "resultsLimit": POSTS_POR_PERFIL}).encode()
    req = urllib.request.Request(f"{ATOR}?token={token}&timeout=280", data=corpo, headers={"Content-Type": "application/json"})
    with abrir(req, timeout=320) as r:
        return json.load(r)


def views(p: dict) -> int:
    return p.get("videoPlayCount") or p.get("videoViewCount") or 0


def escolher(posts: list[dict], n: int = ESCOLHIDOS) -> list[dict]:
    """Reels com mais views em relação à média do próprio perfil (perfil pequeno com hit também entra)."""
    reels = [p for p in posts if p.get("type") == "Video" and p.get("videoUrl")]
    media = {}
    for p in reels:
        media.setdefault(p.get("ownerUsername"), []).append(views(p))
    for p in reels:
        vs = media[p.get("ownerUsername")]
        p["_forca"] = views(p) / max(1, sum(vs) / len(vs))
    return sorted(reels, key=lambda p: (p["_forca"], views(p)), reverse=True)[:n]


def folha(video: Path, saida: Path):
    """18 quadros espalhados pelo vídeo numa grade 6x3."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                               capture_output=True, text=True).stdout.strip() or 30)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vf", f"fps=18/{dur:.2f},scale=216:-1,tile=6x3",
                    "-frames:v", "1", str(saida)], check=True)


def main():
    load_dotenv(RAIZ / ".env")
    refs = json.loads(REFS.read_text(encoding="utf-8"))
    pasta = RAIZ / "referencias" / "estudos" / date.today().isoformat()
    pasta.mkdir(parents=True, exist_ok=True)
    posts = buscar([p["perfil"] for p in refs["perfis"]], os.environ["APIFY_TOKEN"])
    linhas = [f"# Estudo de animação, {date.today().isoformat()}", "",
              f"{len(posts)} posts lidos de {len(refs['perfis'])} perfis. Abaixo, os Reels que mais renderam pro tamanho do perfil.", ""]
    for p in escolher(posts):
        cod = p["shortCode"]
        mp4 = pasta / f"{cod}.mp4"
        try:
            urllib.request.urlretrieve(p["videoUrl"], mp4)
            folha(mp4, pasta / f"{cod}.jpg")
        except Exception as erro:
            print(f"  {cod}: {erro}")
            continue
        finally:
            mp4.unlink(missing_ok=True)  # guarda só a folha; o vídeo pesa e pode ser baixado de novo
        gancho = (p.get("caption") or "").split("\n")[0][:140]
        linhas += [f"## @{p.get('ownerUsername')} · {views(p)} views · {p['_forca']:.1f}x a média do perfil · {p.get('videoDuration', 0):.0f}s",
                   f"https://www.instagram.com/reel/{cod}/", "", f"> {gancho}", "", f"![{cod}]({cod}.jpg)", ""]
    (pasta / "relatorio.md").write_text("\n".join(linhas), encoding="utf-8")
    print(f"estudo salvo em {pasta}")


if __name__ == "__main__":
    main()
