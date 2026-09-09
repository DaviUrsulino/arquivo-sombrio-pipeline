# 0002 — Modal (GPU serverless) como terceira camada de geração de imagem

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

A cadeia de fallback de imagem (ver ADR-0001) tinha Cloudflare Workers AI → Hugging Face
ZeroGPU → Pollinations. Na prática, Cloudflare esgota sua cota diária (~10.000 Neurons) na
maior parte dos dias antes de cobrir os ~10 vídeos/dia das duas contas, e a cota do Hugging
Face ZeroGPU é minúscula (~3,5 min de GPU/dia, ~6-7 imagens), insuficiente pra cobrir o
excedente sozinha. Isso empurrava boa parte das execuções pro Pollinations — a camada de pior
qualidade, sem suporte real a imagem de referência — derrubando a taxa de vídeos publicáveis
sem revisão manual.

Modal oferece $30/mês de crédito grátis, cobrança por segundo de GPU, sem servidor 24/7 (o
container sobe só quando chamado e desliga sozinho). O Davi já usa Modal em outro projeto
(`~/Trabalho/podcasthub`), então a conta e a familiaridade operacional já existiam.

## Decisão

Adicionar Modal como terceira camada, entre Cloudflare e Hugging Face:

```
Cloudflare Workers AI  →  Modal (FLUX.1-schnell)  →  Hugging Face (FLUX.1 Kontext)  →  Pollinations
```

Posicionada antes do Hugging Face (não depois) porque a cota do Hugging Face é curta demais
pra "desperdiçar" chamando ele primeiro quando Modal, com crédito bem mais folgado, está
disponível.

Implementação: um app Modal (`src/modal_flux_app.py`) hospeda uma classe com FLUX.1-schnell
carregado uma vez (`@modal.enter()`), com um método (`gerar`) que aceita prompt e,
opcionalmente, uma imagem de referência (usa `FluxImg2ImgPipeline` quando há referência,
`FluxPipeline` quando não há) — preservando o mesmo mecanismo de encadeamento de personagem
usado nas outras camadas. O app é deployado uma vez (`modal deploy`) e chamado remotamente do
pipeline via `modal.Cls.from_name(...)`, sem precisar rodar `modal deploy` a cada execução.

Se `MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET` não estiverem configurados, essa camada é pulada
silenciosamente (mesmo padrão de fallback automático usado no podcasthub) — o pipeline nunca
trava por falta do Modal, só perde uma camada da cadeia.

## Consequências

**Positivas:**
- Reduz drasticamente a fração de vídeos que caem no Pollinations (pior qualidade), sem
  aumentar custo real (dentro do crédito grátis mensal).
- FLUX.1-schnell tem melhor aderência a prompt que Pollinations e suporte real a
  img2img, mantendo consistência de personagem.
- Padrão de deploy-uma-vez/chamada-remota já validado em produção no podcasthub.

**Negativas / trade-offs aceitos:**
- Cold start do container na primeira chamada de cada execução (modelo de ~24GB precisa
  carregar na GPU) — mitigado por `scaledown_window=120`, que mantém o container quente por 2
  minutos entre chamadas da mesma execução.
- Consome crédito mensal com card associado à conta — precisa de um limite de gasto ($0)
  configurado no billing da Modal pra evitar cobrança surpresa se o volume crescer além do
  esperado.
- Mais uma credencial pra rotacionar/monitorar.
