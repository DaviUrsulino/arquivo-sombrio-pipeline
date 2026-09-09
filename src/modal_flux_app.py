"""App Modal com FLUX.1-schnell — terceira camada de geração de imagem
(entre Cloudflare e Hugging Face na cadeia de fallback), usando o crédito
gratuito mensal do Modal ($30/mês, cobre milhares de imagens já que cada
geração custa frações de centavo de GPU).

Setup (uma vez só, feito pelo Davi):
    pip install modal
    modal setup                    # abre o navegador pra logar/criar conta
    modal deploy src/modal_flux_app.py

Depois de deployado, o app fica hospedado no Modal e é chamado remotamente
por gerar_imagens_cloudflare.py via `modal.Cls.from_name(...)` — não precisa
rodar `modal deploy` de novo a cada execução do pipeline, só se este
arquivo mudar.

Suporta encadeamento de referência (img2img) igual Cloudflare/Hugging
Face — é isso que mantém o personagem consistente entre cenas, requisito
já validado como crítico neste projeto (ver README, "Regra crítica de
consistência de personagem"). Sem imagem de referência (primeira cena),
cai pra txt2img.
"""

import os

import modal

app = modal.App("arquivo-sombrio-flux")

MODELO = "black-forest-labs/FLUX.1-schnell"
CACHE_DIR = "/cache"

# FLUX.1-schnell é um repo "gated" no Hugging Face -- precisa de um token de
# uma conta que já aceitou a licença do modelo (ver instrução no fim deste
# arquivo). Secret criado uma vez via `modal secret create huggingface-secret
# HF_TOKEN=...` e referenciado por nome -- NÃO usar Secret.from_dict() lendo
# os.environ aqui: esse trecho é reavaliado dentro do próprio container
# (que não tem o .env) toda vez que o Modal reimporta o módulo pra hidratar
# a classe, o que zerava o token silenciosamente (bug real, encontrado
# 2026-09-08: dava GatedRepoError mesmo com o token certo no .env local).
hf_secret = modal.Secret.from_name("huggingface-secret")

# Volume persistente pro cache do Hugging Face -- sem isso, cada cold start
# (cada execução nova do cron) baixaria os ~24GB do modelo de novo, levando
# minutos. Com o Volume, o download só acontece de verdade na primeira
# chamada depois do deploy; todas as próximas reaproveitam o cache.
volume_cache = modal.Volume.from_name("arquivo-sombrio-flux-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("diffusers", "transformers", "torch", "accelerate", "safetensors", "sentencepiece", "pillow", "hf_transfer")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": CACHE_DIR})
)

with image.imports():
    import io
    import torch
    from PIL import Image
    from diffusers import FluxImg2ImgPipeline


@app.cls(
    image=image,
    # A10G (22GB) não fecha nem pra UM FluxPipeline em bf16 (o transformer
    # sozinho já é ~24GB) -- tentar offload pra CPU deu CUDA OOM na prática.
    # Carregar txt2img E img2img como pipelines separadas (mesmo via
    # `from_pipe`, que deveria só compartilhar componentes) também deu OOM
    # até numa A100 de 40GB -- parece duplicar peso na prática nesta versão
    # do diffusers (2026-09-08). Solução: só UM pipeline (img2img) pros dois
    # casos -- sem imagem de referência, usa um placeholder cinza neutro
    # (mesmo truque já usado em gerar_imagem_huggingface) com strength≈1.0,
    # que equivale na prática a gerar do zero.
    gpu="A100",
    scaledown_window=120,
    volumes={CACHE_DIR: volume_cache},
    secrets=[hf_secret],
)
class Flux:
    @modal.enter()
    def carregar_modelo(self):
        self.pipe = FluxImg2ImgPipeline.from_pretrained(
            MODELO, torch_dtype=torch.bfloat16, token=os.environ["HF_TOKEN"]
        ).to("cuda")

    @modal.method()
    def gerar(
        self,
        prompt: str,
        imagem_referencia: bytes | None = None,
        largura: int = 768,
        altura: int = 1344,
    ) -> bytes:
        if imagem_referencia:
            ref = Image.open(io.BytesIO(imagem_referencia)).convert("RGB").resize((largura, altura))
            strength = 0.75  # preserva traços do personagem, ainda muda o suficiente pra cena nova
        else:
            ref = Image.new("RGB", (largura, altura), (128, 128, 128))
            strength = 1.0  # sem referência real -- denoise quase total, equivale a txt2img

        resultado = self.pipe(
            prompt=prompt,
            image=ref,
            strength=strength,
            num_inference_steps=4,
            guidance_scale=0.0,
        ).images[0]

        buffer = io.BytesIO()
        resultado.save(buffer, format="JPEG")
        return buffer.getvalue()
