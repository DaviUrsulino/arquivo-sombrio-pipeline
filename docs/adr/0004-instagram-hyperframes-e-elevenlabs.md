# 0004 — Instagram: render com Hyperframes e narração com ElevenLabs

- **Status:** aceito
- **Data:** 2026-10-14

## Contexto

O canal @robo.estagiario segue o formato dos perfis de IA que mais geram comentário no
Instagram brasileiro (levantamento feito com Apify em 2026-10-14, 271 posts de 14 perfis):
gancho forte, lista de ferramentas reais com prova (estrelas no GitHub, print), e "comenta
PALAVRA que eu te mando". O visual escolhido é neon desenhado à mão, com cada elemento
entrando no momento em que a narração fala dele.

Três exigências:

1. **Animação sincronizada com a fala**, sempre igual (determinística). Imagem gerada por IA
   não serve: muda de vídeo para vídeo e não sincroniza.
2. **Carrossel e Reels saindo do mesmo roteiro**, sem retrabalho.
3. **Voz boa em pt-BR, automática.** O Davi não grava narração.

## Decisão

- **Render: Hyperframes** (HTML + GSAP gravado quadro a quadro, licença Apache-2.0). O mesmo
  motor gera o MP4 do Reels e os PNG do carrossel (snapshot de cada slide). Desenho "à mão"
  com rough.js e ícones Lucide, tudo empacotado localmente (sem rede durante o render).
- **Narração: ElevenLabs**, voz "Chris" (`iP95p4xoKVk53GoZ742B`), modelo
  `eleven_multilingual_v2`, endpoint `with-timestamps`. Ele devolve o tempo de cada
  caractere, e o código junta isso em tempo por palavra para sincronizar animação e legenda.
  Respostas ficam em cache por hash do texto, então renderizar de novo não gasta crédito.

### Alternativas testadas e descartadas

| Opção | Por que saiu |
|---|---|
| Edge TTS (Microsoft, grátis) | Voz robótica; reprovada pelo Davi. Endpoint não oficial. |
| Chatterbox (clone da voz do Davi, local, MIT) | Qualidade abaixo do esperado; precisa de ~4 GB de RAM e derrubou o PC por falta de memória (OOM) duas vezes. |
| Kokoro (já usado nos canais dark) | Vozes pt-BR limitadas para o tom de "creator". |
| Gemini TTS | Modelos em preview e cota grátis instável para produção. |
| Voz da biblioteca do ElevenLabs (`EuTuDpe9l2OzoZgvu4T6`) | A API recusa no plano grátis (`paid_plan_required`). Volta a ser opção se o plano Starter for assinado. |
| Voz de pessoa famosa | Fere direito de personalidade; risco de derrubada do perfil e de processo. Fora de questão. |

## Consequências

- Custo: o plano grátis do ElevenLabs dá 10 mil caracteres por mês (~10 Reels de 60 s). Acima
  disso, o Starter (US$ 5/mês, ~30 Reels) e uso comercial liberado.
- O render precisa de Node 22+ e Chrome. No GitHub Actions isso precisa ser validado antes de
  ligar o cron do Instagram; localmente o render de 50 s leva ~2,5 min.
- Como o render roda Chrome, ele deve rodar com limite de memória quando for local
  (`systemd-run --user -p MemoryMax=4G`), para não derrubar o resto do PC.
