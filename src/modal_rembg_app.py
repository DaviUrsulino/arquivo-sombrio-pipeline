"""App Modal pra remoção de fundo (rembg) -- usado pelo movimento
"personagem_cresce" em montar_video_local.py (personagem recortado
"tipo figurinha" crescendo sozinho sobre o fundo).

Motivo de existir (2026-09-09): rodando isso localmente no runner efêmero
do GitHub Actions, o modelo do rembg (~1GB) era baixado do zero em TODA
execução -- sem cache nenhum entre runs, isso derrubou o runner real
(GitHub matou o job com "the runner has received a shutdown signal") duas
vezes em produção, incluindo um vídeo do Em Alta. No Modal já temos o
padrão de Volume persistente (ver modal_flux_app.py) -- o download do
modelo só acontece de verdade na primeira chamada depois do deploy, todas
as próximas reaproveitam o cache.

Setup (uma vez só):
    modal deploy src/modal_rembg_app.py
"""

import modal

app = modal.App("arquivo-sombrio-rembg")

CACHE_DIR = "/cache"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("rembg[cpu]", "pillow")
    .env({"U2NET_HOME": CACHE_DIR})
)

# Persistente entre execuções -- sem isso, cada cold start baixaria o
# modelo do rembg de novo (era exatamente o que derrubava o runner do
# GitHub Actions, ver motivo acima).
volume_cache = modal.Volume.from_name("arquivo-sombrio-rembg-cache", create_if_missing=True)

with image.imports():
    import io
    from PIL import Image
    from rembg import new_session, remove


@app.cls(
    image=image,
    cpu=2.0,
    scaledown_window=120,
    volumes={CACHE_DIR: volume_cache},
)
class Rembg:
    @modal.enter()
    def carregar_modelo(self):
        self.session = new_session("u2net")

    @modal.method()
    def remover_fundo(self, imagem_bytes: bytes) -> bytes:
        imagem = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
        resultado = remove(imagem, session=self.session)
        buffer = io.BytesIO()
        resultado.save(buffer, format="PNG")
        return buffer.getvalue()
