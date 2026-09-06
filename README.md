# Arquivo Sombrio — Pipeline de Conteúdo

Pipeline semi-automatizado pra gerar vídeos de terror (canal dark, estilo "Terror 2D Cartoon")
pro TikTok/YouTube Shorts. Validado manualmente em 2026-09-06 (ver seção "O que já foi validado").

## Contexto (pra quem/o que abrir esse chat sem ter visto a sessão anterior)

Davi (estudante de Engenharia de Software, UnB Gama) passou uma sessão inteira testando
manualmente essa arquitetura antes de partir pro código — isso não é um projeto teórico,
já existe um vídeo publicado no TikTok gerado com esse fluxo ("A Oitava Regra").

## Arquitetura

```
roteiro (Claude API)  →  imagens (Leonardo AI, APROVAÇÃO MANUAL)  →  vídeo final (JSON2Video API)
```

1. **Roteiro + prompts de imagem**: gerados pela API do Claude (`claude-opus-5`). Substitui o
   ChatGPT que os tutoriais de "canal dark" usam manualmente.
2. **Imagens**: geradas no **Leonardo AI**, com aprovação humana antes de seguir. **Isso não é
   opcional nem preguiça — foi uma decisão técnica.** Testamos gerar imagem direto pela API do
   JSON2Video (modelos `flux-pro` e `freepik-classic`) e o personagem simplesmente não aparecia
   ou saía cortado, em ~6 tentativas seguidas com prompts e parâmetros diferentes. Assim que
   trocamos pra Leonardo AI (interface visual, dá pra regenerar até ficar bom), as mesmas
   descrições funcionaram de primeira. **Não tente automatizar a geração de imagem via API sem
   antes validar de novo se isso mudou** — pode ser limitação temporária da ferramenta, mas era
   real na data desse teste.
3. **Montagem do vídeo**: JSON2Video (`api.json2video.com/v2`). Recebe as imagens aprovadas
   (via upload em `/v2/media/file`, fluxo de 2 passos com URL pré-assinada) + roteiro de voz
   (ElevenLabs, embutido no crédito do JSON2Video) + zoom Ken Burns + formato vertical.

## O que já foi validado manualmente (2026-09-06)

- Roteiro de terror curto (5 cenas, ~45s) funciona bem no formato JSON2Video.
- Formato vertical: usar `"resolution": "instagram-story"` (não `"vertical"` — esse não existe).
- Toda imagem precisa de `"resize": "cover"` element, senão sobra barra preta (a imagem gerada
  vem em proporção errada por padrão).
- `"duration": -2` no elemento de imagem = casa com a duração da cena (que por sua vez casa com
  a duração da narração). Sem isso, cena corta ou sobra silêncio.
- Zoom simples (`"zoom": 3`) funciona bem. **Não usar `"pan"`** — desloca o enquadramento e
  descentraliza o personagem.
- Voz `"Clyde"` (ElevenLabs) ficou boa pro clima de terror/suspense.
- Plano grátis do JSON2Video: 600 créditos (~10 min de vídeo), sem cartão. Créditos acabam rápido
  testando — Davi criou conta com e-mail alternativo pra continuar testando de graça.

## Custo estimado

- Roteiro + prompts (Claude API, `claude-opus-5`): ~US$0,01-0,02 por vídeo.
- Geração de imagem (Leonardo AI): grátis até 150 tokens/dia.
- Vídeo final (JSON2Video): dentro do plano grátis pra baixo volume; plano pago mais barato
  (Hobby) ~US$16,95/mês se passar do limite grátis.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# preencher ANTHROPIC_API_KEY e JSON2VIDEO_API_KEY no .env
```

## Uso (fluxo atual, com aprovação manual da imagem)

```bash
# Passo 1: gera roteiro + prompts de imagem pra colar no Leonardo AI
python src/gerar_roteiro.py --tema "escritório abandonado, regras impossíveis"

# Passo 2: você gera as imagens no Leonardo AI, aprova visualmente, baixa os arquivos
# (salva em ./imagens_aprovadas/cena1.jpg, cena2.jpg, ... na ordem das cenas)

# Passo 3: monta o vídeo final
python src/montar_video.py --roteiro roteiro_gerado.json --imagens ./imagens_aprovadas/
```

## Em aberto / próximos passos

- [ ] Testar se dá pra automatizar 100% a geração de imagem (reavaliar Leonardo API própria, ou
      testar de novo se o JSON2Video/flux-pro melhorou).
- [ ] Decidir fonte de tema/nicho por vídeo (banco de ideias gerado, ou manual por enquanto).
- [ ] Pipeline separado do TikTok Shop (avatar + produto via HeyGen) não faz parte deste
      repositório — é um projeto à parte, ainda não iniciado em código.
- [ ] Publicação automática (upload direto pro TikTok) — não implementado, download manual por
      enquanto.
