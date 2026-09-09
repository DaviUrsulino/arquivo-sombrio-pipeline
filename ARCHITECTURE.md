# Arquivo Sombrio Pipeline — Arquitetura

> Pipeline que gera e publica vídeos curtos narrados (TikTok/YouTube Shorts) de forma 100%
> automatizada e sem custo fixo, rodando sozinho em cron na nuvem.
>
> **Este documento existe pra ser reaproveitado.** O padrão central daqui — cascata de
> fallbacks gratuitos + execução serverless agendada — não é específico de "vídeo dark", é
> genérico o bastante pra reaplicar em qualquer pipeline de geração de conteúdo (ex: avatar
> automatizado pro Instagram). Ver [`docs/adr/`](docs/adr) pras decisões registradas.
>
> **Status (2026-09-08): em produção**, publicando ~10 vídeos/dia em 2 contas via GitHub
> Actions, sem intervenção manual.

---

## 1. Padrão central: cascata de fallbacks, nunca um provedor único

Toda etapa que depende de um serviço externo tem **2 a 4 provedores em cadeia**, cada um
tentado na ordem só quando o anterior falha ou esgota cota. Isso é o que permite rodar de
graça: provedores free-tier têm cota diária pequena, mas a soma das cotas de vários cobre o
volume necessário — e se um provedor sair do ar, o pipeline não trava.

```
roteiro:  Gemini  →  OpenRouter (modelos :free)  →  Mistral
imagem:   Cloudflare Workers AI  →  Modal (FLUX.1-schnell)  →  Hugging Face (ZeroGPU)  →  Pollinations
```

Regras que tornam isso seguro (não só "tenta de novo até dar certo"):

- **Erro de cota esgotada é diferente de erro passageiro.** Cada camada detecta a mensagem
  específica de "cota diária acabou" (ex: `CotaEsgotadaError` em
  [`gerar_imagens_cloudflare.py`](src/gerar_imagens_cloudflare.py)) e desiste imediatamente
  dessa camada pro resto da execução, em vez de gastar tempo com retry/backoff que não vai
  funcionar mesmo.
- **A última camada da cadeia é sempre a de pior qualidade** (Pollinations, sem chave, sem
  cota) — ela garante que o pipeline nunca quebra por falta de imagem, mas o resultado dela é
  sinalizado (`usou_fallback=True`) pro código de publicação **não postar sozinho** um vídeo
  que passou pela pior camada. Qualidade abaixo do padrão vira "gerado mas não publicado", não
  vira erro fatal nem publicação ruim.
- **Camadas pagas-com-crédito-grátis (Modal) ficam no meio da cadeia, não no fim** — só são
  chamadas quando a camada 100%-grátis-sem-cartão já esgotou, minimizando consumo do crédito
  mensal.

## 2. Padrão central: execução serverless agendada, sem servidor 24/7

Nenhuma parte deste projeto roda num servidor ligado o tempo todo:

| Peça | Onde roda | Por quê |
|---|---|---|
| Orquestração (roteiro → imagem → vídeo → publicação) | **GitHub Actions**, cron (`schedule`) | Grátis pra repositório público/privado dentro da cota, já vem com secrets management e logs |
| Geração de imagem pesada (GPU) | **Modal**, serverless por segundo | $30/mês grátis cobre milhares de gerações; container sobe só na hora de gerar e desliga sozinho (`scaledown_window`) |
| Narração + legenda + montagem de vídeo | **CPU do próprio runner do GitHub Actions** (ffmpeg, Kokoro, faster-whisper) | Modelos leves o bastante pra rodar em CPU comum, evita pagar GPU pra isso |

Isso significa: **o PC do Davi não precisa estar ligado**, o custo por execução é
centavos-a-zero, e escalar o volume (mais vídeos/dia) é só adicionar mais entradas de `cron`
— não precisa de infraestrutura nova.

## 3. Sistema de "canais" — como adicionar um nicho/formato novo sem tocar no pipeline

Cada canal/formato é um módulo Python isolado em [`src/canais/`](src/canais) que expõe a
mesma interface: `NOME_CANAL`, `SYSTEM_PROMPT`, `MASTER_STYLE_LOCK`, `RESTRICOES`,
`VOZES_LOCAIS`, `PASTA_IMAGENS`, `AMBIENCIA`. O resto do pipeline (`gerar_roteiro.py`,
`gerar_imagens_cloudflare.py`, `montar_video_local.py`) nunca referencia um nicho específico —
só chama `carregar_canal(nome)` e usa os atributos.

Isso é o que permite ter hoje 2 contas/5 formatos (Arquivo Sombrio: terror + true crime; Em
Alta: curiosidade + novela de mascote + objeto falante + POV histórico) sem nenhum `if canal ==
"terror"` espalhado pelo código — cada canal novo é só um arquivo novo em `src/canais/` + uma
linha em `src/canais/__init__.py`. Reaproveitável 1:1 pra "personalidades" diferentes de um
avatar, por exemplo.

## 4. Consistência de personagem entre imagens geradas separadamente

Problema central de qualquer pipeline que gera N imagens independentes pra contar uma história:
sem cuidado extra, o "personagem" muda de aparência a cada imagem. Duas técnicas usadas juntas:

1. **Descrição física fixa, injetada em código, nunca gerada pelo LLM por cena.** O roteiro
   define o personagem UMA vez (`"personagem": "..."`); o código concatena essa string
   literalmente em todo prompt de imagem. O LLM nunca é livre pra redescrever aparência cena a
   cena — pequena variação de texto já faz o gerador desenhar gente diferente.
2. **Encadeamento de imagem de referência (img2img).** Cada imagem nova usa a imagem anterior
   como referência visual (Cloudflare, Modal e Hugging Face suportam isso; Pollinations não —
   por isso é a pior camada da cadeia). Isso resolve o que a descrição em texto sozinha não
   resolve: sombreado, proporção, estilo de traço.

## 5. Stack

| Camada | Escolha | Por quê |
|---|---|---|
| Roteiro | Gemini → OpenRouter (`:free`) → Mistral | 3 contas gratuitas independentes, nenhuma cobra cartão |
| Imagem | Cloudflare Workers AI → Modal (FLUX.1-schnell) → Hugging Face (FLUX.1 Kontext) → Pollinations | Ordenado do mais barato/rápido pro mais genérico; ver ADR-0001 |
| Narração (TTS) | Kokoro (Apache 2.0, CPU) | Único TTS grátis com licença comercial liberada testado até agora; Coqui XTTS foi descartado por licença CPML (não-comercial) |
| Legenda | faster-whisper (`small`, CPU) | Transcreve a própria narração pra gerar timestamp de legenda, sem depender do provedor de TTS entregar isso |
| Montagem de vídeo | ffmpeg (xfade + concat + drawtext) | Zero dependência externa, roda em qualquer runner Linux |
| Orquestração/agendamento | GitHub Actions (`schedule` cron) | Grátis, já integrado ao repositório, secrets nativos |
| GPU sob demanda | Modal | $30/mês grátis, cobrança por segundo, sem servidor 24/7 — ver ADR-0001 |
| Publicação | YouTube Data API v3, TikTok Content Posting API, Instagram Graph API | APIs oficiais das próprias plataformas, sem scraping |

## 6. O que fica fora do escopo deste documento

Detalhes de validação manual específicos de cada API (parâmetros exatos testados, bugs
encontrados e corrigidos, formato de prompt de cada canal) ficam no [`README.md`](README.md) —
esse é o "log de decisões técnicas testadas" do projeto, atualizado a cada mudança relevante.
Este documento (`ARCHITECTURE.md`) é o resumo estável pra quem chega no projeto pela primeira
vez ou quer reaproveitar o padrão em outro lugar.

Ver também [`docs/adr/`](docs/adr) pras decisões arquiteturais individuais, no formato usado em
`~/Trabalho/podcasthub`.
