# Arquivo Sombrio Pipeline — canais dark automatizados

Pipeline pra gerar e publicar vídeos curtos (TikTok/YouTube Shorts) de forma automatizada,
suportando **múltiplos canais/nichos** no mesmo código. Validado manualmente a partir de
2026-09-06 — já existe vídeo publicado no TikTok gerado com esse fluxo ("A Oitava Regra").

## Contexto (pra quem/o que abrir essa sessão sem ter visto a anterior)

Davi (estudante de Engenharia de Software, UnB Gama) já validou esse pipeline numa sessão
maratona (2026-09-06 → 2026-09-07). Dois canais estão configurados: **Arquivo Sombrio** (terror
ficcional, animação 2D) e **Casos Reais** (true crime, estilo documental). Planeja adicionar
mais contas no futuro, sempre reaproveitando este mesmo código via `src/canais/`.

**Se a sessão de chat foi compactada ou é uma sessão nova**: leia este arquivo inteiro antes de
sugerir qualquer mudança — ele documenta decisões já testadas, não suposições.

## Arquitetura (estado atual)

```
roteiro (Gemini API)  →  imagens (Cloudflare Workers AI, grátis, automatizado)
                       →  narração + legenda (Kokoro + faster-whisper, local, grátis)
                       →  vídeo final (ffmpeg local, OU JSON2Video pago como alternativa)
                       →  publicação (YouTube automatizado; TikTok em auditoria)
```

### 1. Roteiro — `src/gerar_roteiro.py`
- API: **Gemini** (`gemini-3.6-flash`, com fallback automático pra `gemini-3.5-flash` e
  `gemini-flash-latest` se der 503 — a API do Gemini tem instabilidade frequente).
- Suporta múltiplas chaves via `GEMINI_API_KEYS` (separadas por vírgula) — tenta a próxima se
  uma falhar.
- Uso: `python src/gerar_roteiro.py --canal terror --tema "..."`
- Cada canal (`src/canais/terror.py`) define seu próprio
  `SYSTEM_PROMPT`, estilo visual e voz — **não tem hardcode de nicho no script principal**.
- **Regra crítica de consistência de personagem**: o campo `"personagem"` do roteiro é
  injetado *literalmente* (palavra por palavra) em todo prompt de imagem pelo código — o
  campo `prompt_imagem` de cada cena NÃO deve redescrever a aparência física, só ação/
  câmera/ambiente. Sem isso, o personagem muda de aparência a cada cena (testado e comprovado
  em 2026-09-07 — cabelo, barba e até acessórios mudavam entre cenas antes dessa correção).

### 2. Imagens — automatizado e grátis via `src/gerar_imagens_cloudflare.py`
- **Cloudflare Workers AI**, modelo `@cf/black-forest-labs/flux-2-klein-4b`.
- Grátis, sem cartão: ~10.000 Neurons/dia (dá pra gerar bastante imagem por dia).
- **Encadeamento de referência**: cada cena usa a imagem da cena anterior como referência
  (multipart/form-data, campo `image`) — é isso que mantém o personagem consistente. Sem
  imagem de referência, cada cena "reinventa" a aparência.
- **Reforço anti-foto-real obrigatório no prompt**: esse modelo tende a puxar pra
  fotorrealismo quando recebe imagem de referência, mesmo com o master style lock pedindo 2D
  animation — por isso o código sempre adiciona "flat cel-shaded 2D cartoon illustration...
  NOT photorealistic, NOT a photo, NOT 3D render" antes de cada prompt (ver `REFORCO_2D` no
  arquivo).
- Alternativas mantidas no código, mas não recomendadas como padrão:
  - `gerar_imagens.py` — Gemini/Nano Banana, **pago** (~US$0,01-0,04/imagem), mas exige
    faturamento habilitado no Google Cloud (não vem incluso no Gemini Plus, que é assinatura
    de consumidor separada da API).
  - `gerar_imagens_apiframe.py` — mesma ideia via Apiframe (agregador pago).
  - Geração manual no app do Gemini (Nano Banana) — grátis, mas gasta tempo; ainda é a opção
    de melhor qualidade/consistência se o Cloudflare não bastar pra algum canal.
- **Testado e descartado**: Together.ai (pede depósito), Gemini API direta (cota 0 no free
  tier), ImageGPT e Apiframe (créditos grátis reais muito menores que o anunciado), Pollinations
  (grátis mas não obedece ao estilo), Hugging Face Inference (só ~10 imagens grátis/mês). O
  Cloudflare foi o único que entregou grátis + volume real + qualidade aceitável.

### 3. Narração + legenda — 100% local e grátis via `src/montar_video_local.py`
- **Kokoro** (licença Apache 2.0, uso comercial liberado) pra narração — roda no CPU, sem GPU.
  Vozes em `VOZES_LOCAIS` de cada canal (`pm_santa`/`pf_dora` hoje), escolhida conforme o
  campo `"genero_narrador"` que o próprio roteiro define (varia entre execuções).
  - **Atenção de licença**: **NÃO usar Coqui XTTS v2** pra isso — a licença (CPML) é só
    não-comercial, incompatível com um canal monetizado.
- **faster-whisper** (`small`, CPU) transcreve a narração gerada e cria legenda estilo CapCut
  (blocos de poucas palavras, fonte grande, embaixo da tela) — arquivo `.ass` com
  `PlayResX`/`PlayResY` corretos (sem isso a legenda fica desalinhada).
- Suporta **múltiplas imagens por cena** (`cenaN_1.jpg`, `cenaN_2.jpg`, ...) — divide a duração
  da narração entre elas, cortando no meio da fala. Cai pra `cenaN.jpg` único se não houver
  variantes. Usado pra deixar o vídeo mais dinâmico sem exigir imagem por cena inteira.
- Imagem quadrada (caso do Cloudflare) é cortada (`crop`, não esticada) pro formato 9:16 —
  ver `gerar_clipe_imagem_silencioso`.
- Hardware do Davi (Ryzen 7 5700U, sem GPU dedicada) **não roda geração de imagem/vídeo local
  com qualidade viável** — já testado e confirmado; não vale reabrir essa investigação.

### 4. Montagem paga (alternativa) — `src/montar_video.py`
- JSON2Video (`api.json2video.com/v2`), configurações validadas em 2026-09-06 (ver seção
  histórica abaixo). Ainda funciona, mas o pipeline local (item 3) é o padrão agora por ser
  grátis.
- JSON2Video tem um elemento nativo `"subtitles"` com legenda automática + destaque de palavra
  falada — não implementado ainda, mas é uma melhoria fácil se voltar a usar essa rota (ver
  `docs` do JSON2Video, elemento `subtitles`, nível do filme/movie, não por cena).

### 5. Publicação
- **YouTube**: automatizado de verdade via `src/publicar_youtube.py` (YouTube Data API v3,
  grátis, ~100 uploads/dia). OAuth com `client_secret.json` (Google Cloud Console, projeto
  "Default Gemini Project"). **Atenção**: uma conta Google pode ter vários canais/marcas — o
  OAuth loga no canal errado se não for explícito qual autorizar (já aconteceu, vídeo teve que
  ser apagado manualmente). Sempre confirmar com `channels().list(mine=True)` depois de logar.
- **TikTok**: app **"Arquivo Sombrio Pipeline"** cadastrado no TikTok for Developers, submetido
  pra auditoria de produção em 2026-09-07 (aguardando aprovação, normalmente 1-2 semanas). Até
  aprovar, a Content Posting API só posta em modo `SELF_ONLY` E exige a conta estar configurada
  como privada (`unaudited_client_can_only_post_to_private_accounts`) — não dá pra postar
  público via API antes disso. Script pronto em `src/publicar_tiktok.py`, só trocar
  `PRIVACY_LEVEL_PADRAO` pra `PUBLIC_TO_EVERYONE` quando aprovado. Token OAuth salvo em
  `tiktok_token.json` (refresh token, válido ~1 ano).
  - Callback OAuth hospedado como Artifact (Claude.ai) — TikTok exige HTTPS público real, não
    aceita `localhost`.
  - Domínio próprio pra Privacy Policy/Termos/site: `https://daviursulino.github.io/
    arquivo-sombrio-site/` (repo público separado `DaviUrsulino/arquivo-sombrio-site`, GitHub
    Pages) — Artifacts do Claude.ai **não servem** pra isso porque a auditoria exige verificação
    de propriedade de domínio (arquivo de verificação em URL específica), que não é possível
    num domínio que não é seu.

## Sistema de canais — `src/canais/`

Cada canal é um módulo Python com: `NOME_CANAL`, `SYSTEM_PROMPT`, `MASTER_STYLE_LOCK`,
`RESTRICOES`, `VOZES_LOCAIS` (dict género→voz Kokoro), `PASTA_IMAGENS`. Registrar um canal novo
em `src/canais/__init__.py` (dict `CANAIS`). Todo o resto do pipeline (`gerar_roteiro.py`,
`gerar_imagens_cloudflare.py`, `montar_video_local.py`) já funciona pra qualquer canal
registrado via `--canal <nome>`, sem precisar tocar em mais nada.

- **`terror`** (Arquivo Sombrio, único canal técnico da conta desde 2026-09-09 — não alterna
  mais com `true_crime`, removido): moldura de "relato real"/lenda documentada ou teoria da
  conspiração (âncora de realidade no gancho, escalada de 2-3 eventos, fecho ambíguo), narrador
  sempre masculino, personagem fixo descrito uma vez e reaproveitado, premissa variando entre
  execuções (perseguição, culto, entidade, objeto amaldiçoado, etc. — evitar sempre "preso em
  ambiente fechado", ficou repetitivo).

Estilo de escrita: frases curtas e objetivas (máx. 12-15 palavras), pequenos suspenses entre
cenas, nunca resolver a curiosidade até o final, sempre acima de 60s de narração (requisito do
TikTok Creator Rewards Program).

## O que já foi validado manualmente (2026-09-06, JSON2Video)

- Formato vertical: usar `"resolution": "instagram-story"` (não `"vertical"` — esse não existe).
- Toda imagem precisa de `"resize": "cover"` element, senão sobra barra preta.
- `"duration": -2` no elemento de imagem = casa com a duração da narração da cena.
- Zoom simples (`"zoom": 3"`) funciona bem. **Não usar `"pan"`** — descentraliza o personagem.
- Voz `"Clyde"` (ElevenLabs) ficou boa pro clima de terror/suspense (canal terror).

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# preencher: GEMINI_API_KEY (ou GEMINI_API_KEYS separadas por vírgula),
# CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN (permissão "Workers AI" → Read),
# TIKTOK_CLIENT_KEY/SECRET, JSON2VIDEO_API_KEY (só se for usar a rota paga)
```

Pra YouTube: baixar `client_secret.json` do Google Cloud Console (projeto "Default Gemini
Project" → Credenciais → OAuth Client ID → Desktop app) e colocar na raiz do projeto.

## Uso (fluxo atual, 100% automatizado e grátis)

```bash
# Passo 1: roteiro
python src/gerar_roteiro.py --canal terror --tema "..."

# Passo 2: imagens (automatizado, Cloudflare, grátis)
python src/gerar_imagens_cloudflare.py --canal terror --roteiro roteiro_terror.json

# Passo 3: vídeo (narração + legenda + montagem, 100% local, grátis)
python src/montar_video_local.py --canal terror --roteiro roteiro_terror.json

# Passo 4: publicar
python src/publicar_youtube.py --video video_final.mp4 --titulo "..." --descricao "..."
# TikTok: aguardando aprovação da auditoria, publicar manual por enquanto
```

## Custo estimado (pipeline grátis, padrão atual)

- Roteiro (Gemini API): ~US$0,01-0,02/vídeo.
- Imagens (Cloudflare Workers AI): **R$0,00**.
- Narração + legenda + montagem (Kokoro + faster-whisper + ffmpeg, local): **R$0,00**.
- YouTube: **R$0,00** (API grátis).
- **Total por vídeo: só o roteiro, centavos de dólar.**

## Em aberto / próximos passos

- [ ] Aprovação da auditoria TikTok (submetido 2026-09-07) — trocar `PRIVACY_LEVEL_PADRAO`
      quando aprovar.
- [ ] Reativar "personagem cresce" (movimento de câmera) com torch CPU-only explícito no
      requirements.txt (causou estouro de disco no runner antes, ver montar_video_local.py).
- [ ] TikTok Shop (afiliado/dropshipping) — projeto separado, decidido não misturar com os
      canais dark. Ainda não iniciado, material de referência recebido do Davi mas não
      analisado a fundo.
- [ ] Considerar 2ª/3ª conta (nicho ainda a decidir) reaproveitando `src/canais/`.
- [ ] Legenda com destaque palavra-por-palavra (JSON2Video nativo tem; pipeline local não,
      vem em blocos de poucas palavras).
