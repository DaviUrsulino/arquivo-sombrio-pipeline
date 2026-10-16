# 0005 — Publicação direta pela Instagram Graph API (substitui Publora)

- **Status:** aceito
- **Data:** 2026-10-16
- **Supera:** a parte de publicação do ADR-0004 (Publora)

## Contexto

O ADR-0004 escolheu a Publora porque, na época, o fluxo oficial de verificação de telefone
no painel de desenvolvedor da Meta estava quebrado — sem conseguir passar por ele, não dava
pra gerar um token oficial da Instagram Graph API. A Publora contornava isso por já ter o
app da Meta aprovado, trocando o OAuth por um login simples.

Isso deixava o pipeline dependente de um terceiro pago pra uma operação central (publicar),
e divergia do RF-07 original (`docs/estudio-instagram.md`), que já pedia Graph API direta.

Em 2026-10-16, o cadastro oficial do app (`robo-estagiario-automacao`, "API do Instagram com
login do Instagram") foi concluído pelo painel dedicado da Meta — o problema era usar a UI
errada (Graph API Explorer / Facebook Login), não o telefone. Com o app aprovado e o token de
acesso de longa duração gerado e validado (`GET /me` devolveu `robo.estagiario`,
`account_type: MEDIA_CREATOR`), a Publora deixou de ser necessária.

## Decisão

- **Publicação:** `src/estudio_instagram/graph_api.py`, cliente `InstagramGraph` que fala
  direto com `graph.instagram.com/v22.0`. Reels: cria container (`media_type=REELS`), espera
  `status_code=FINISHED`, publica (`media_publish`). Carrossel: um container por imagem,
  container pai com `children`, espera, publica.
- **Hospedagem de mídia:** `src/estudio_instagram/hospedagem.py`. A Graph API só aceita
  `video_url`/`image_url` público (não aceita upload de arquivo local, diferente da
  Publora). Usamos uma GitHub Release fixa (`midia-publicacao`) do próprio repositório como
  CDN: cada arquivo sobe com nome único (prefixo da pauta) via `gh release upload --clobber`,
  e o Instagram baixa de lá na hora de criar o container.
- Variáveis de ambiente: `INSTAGRAM_GRAPH_TOKEN` (token de acesso de longa duração) e
  `INSTAGRAM_USER_ID` (ID numérico da conta, não o `@usuario`). Substituem
  `PUBLORA_API_KEY`/`INSTAGRAM_PLATFORM_ID`.
- `src/estudio_instagram/publicacao.py` (cliente Publora) foi removido — sem mais nenhum
  chamador no pipeline.

## Consequências

- **100% autonomia**: nenhuma dependência de terceiro pago pra publicar. Custo operacional
  do Instagram cai a zero (fora o que já existia: ElevenLabs).
- O token de acesso de longa duração expira em ~60 dias e precisa ser renovado manualmente
  pelo painel da Meta (`Casos de uso > Personalizar > Configuração da API com login do
  Instagram > Gerar token`) — não existe hoje renovação automática. Isso é um risco conhecido,
  não um RNF resolvido; se incomodar, dá pra automatizar depois com o endpoint de refresh de
  token de longa duração.
- A GitHub Release usada como CDN é pública (o repositório é público) — qualquer um com o link
  consegue baixar o vídeo/imagem enquanto ela estiver lá. Isso é aceitável porque o conteúdo já
  está indo pro Instagram publicamente de qualquer forma; nenhum dado sensível passa por essa
  release.
- O `gh` CLI precisa estar autenticado no ambiente que roda o pipeline (local: já está;
  GitHub Actions: `GITHUB_TOKEN` automático do job, com `permissions: contents: write`, já
  usado para o commit de histórico).
