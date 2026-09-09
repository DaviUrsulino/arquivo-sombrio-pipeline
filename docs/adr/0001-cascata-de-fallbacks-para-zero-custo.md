# 0001 — Cascata de fallbacks gratuitos em vez de um provedor único pago

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

O objetivo do pipeline é rodar com custo zero ou quase zero por vídeo, sem cartão de crédito
onde for possível. Todo provedor gratuito real (Gemini, Cloudflare Workers AI, Hugging Face
ZeroGPU) tem cota diária baixa o suficiente pra não cobrir sozinho o volume de vídeos/dia
desejado, e volume esperado só cresce com o tempo. Usar só um provedor pago desde o início
(ex: OpenAI + Leonardo AI) resolveria a cota, mas comprometeria o objetivo de custo zero e
criaria dependência de um único ponto de falha.

## Decisão

Cada etapa que depende de serviço externo (geração de roteiro, geração de imagem) usa uma
cadeia ordenada de 2 a 4 provedores, tentados em sequência só quando o anterior falhar ou
esgotar cota:

- Roteiro: Gemini → OpenRouter (modelos `:free`, buscados dinamicamente) → Mistral.
- Imagem: Cloudflare Workers AI → Modal (FLUX.1-schnell) → Hugging Face (FLUX.1 Kontext) →
  Pollinations.

Erros de "cota diária esgotada" são detectados por assinatura de mensagem e tratados como
permanentes pro resto da execução (não tenta de novo com backoff) — isso evita desperdiçar
minutos de execução do GitHub Actions tentando um provedor que já se sabe que vai falhar até o
reset diário.

A última camada de cada cadeia é sempre a de menor qualidade/confiabilidade
(Pollinations para imagem), e seu uso é sinalizado explicitamente pro código de publicação, que
trata isso como "gerar mas não publicar sem revisão humana" em vez de publicar automaticamente
um resultado abaixo do padrão.

## Consequências

**Positivas:**
- Custo por vídeo permanece perto de zero mesmo com volume crescente, sem depender de um único
  provedor pago.
- Uma mudança de política/preço/instabilidade de qualquer provedor não derruba o pipeline
  inteiro — só reduz a chance daquela camada específica ser usada.
- Adicionar volume (mais vídeos/dia) é sustentável: o excedente de cota de uma camada cai pra
  próxima automaticamente.

**Negativas / trade-offs aceitos:**
- Mais código de orquestração e mais casos de erro pra tratar do que integrar um único
  provedor.
- Qualidade do resultado final não é constante — varia conforme qual camada da cadeia atendeu
  aquela execução (mitigado pela regra de "fallback de pior qualidade não publica sozinho").
- Requer monitorar múltiplas contas/credenciais em vez de uma só.
