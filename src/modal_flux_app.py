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
    .pip_install(
        "diffusers", "transformers", "torch", "accelerate", "safetensors", "sentencepiece",
        "pillow", "hf_transfer", "bitsandbytes",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": CACHE_DIR})
)

with image.imports():
    import io
    import torch
    from PIL import Image
    from diffusers import FluxImg2ImgPipeline, FluxTransformer2DModel
    from diffusers import BitsAndBytesConfig as DiffusersBnBConfig
    from transformers import T5EncoderModel, BitsAndBytesConfig as TransformersBnBConfig


@app.cls(
    image=image,
    # Modelo original em bf16 exige ~24GB só pro transformer, o que forçava
    # GPU cara (A100) pra caber sem OOM (ver histórico de bugs 2026-09-08).
    # Quantizando o transformer e o encoder T5 em NF4 (4-bit) o footprint
    # cai pra ~8-9GB, mas a codificação/decodificação da imagem pelo VAE
    # (que não é quantizada) sozinha já estourava a T4 (16GB) -- L4 (24GB)
    # é o próximo degrau de preço acima da T4 no catálogo da Modal e ainda
    # bem mais barato que A10G/A100, com folga suficiente pra não precisar
    # de mais gambiarra de memória. Latência um pouco maior que a A100 é
    # aceitável: essa camada é fallback raro (só entra quando o Cloudflare
    # já esgotou a cota grátis do dia) e roda em background no cron.
    gpu="L4",
    scaledown_window=120,
    volumes={CACHE_DIR: volume_cache},
    secrets=[hf_secret],
)
class Flux:
    @modal.enter()
    def carregar_modelo(self):
        token = os.environ["HF_TOKEN"]
        nf4 = dict(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)

        transformer = FluxTransformer2DModel.from_pretrained(
            MODELO, subfolder="transformer",
            quantization_config=DiffusersBnBConfig(**nf4),
            torch_dtype=torch.bfloat16, token=token,
        )
        text_encoder_2 = T5EncoderModel.from_pretrained(
            MODELO, subfolder="text_encoder_2",
            quantization_config=TransformersBnBConfig(**nf4),
            torch_dtype=torch.bfloat16, token=token,
        )
        self.pipe = FluxImg2ImgPipeline.from_pretrained(
            MODELO, transformer=transformer, text_encoder_2=text_encoder_2,
            torch_dtype=torch.bfloat16, token=token,
        ).to("cuda")
        # sem isso, só a decodificação final do VAE (que roda em resolução
        # cheia, sem economia da quantização) já estourava os 16GB da T4
        # sozinha -- tiling/slicing processa a imagem em pedaços menores.
        self.pipe.vae.enable_tiling()
        self.pipe.vae.enable_slicing()

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
            height=altura,
            width=largura,
            strength=strength,
            num_inference_steps=4,
            guidance_scale=0.0,
        ).images[0]

        buffer = io.BytesIO()
        resultado.save(buffer, format="JPEG")
        return buffer.getvalue()
