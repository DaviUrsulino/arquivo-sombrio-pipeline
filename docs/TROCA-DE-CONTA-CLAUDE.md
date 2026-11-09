# Troca de conta do Claude

Davi, 08/11/2026: a conta atual do Claude é um teste de 7 dias. Quando ele trocar de conta, a produtora do GitHub
para de fazer vídeo até o token novo ser colocado. Os posts, o direct e o maestro continuam, porque não usam o Claude.

## O que fazer na conta nova (5 minutos)

1. Entra no Claude Code com a conta nova (`claude` no terminal e faz o login).
2. Gera o token de longa duração. Ele aparece uma vez só; copia:

   ```bash
   claude setup-token
   ```

3. Troca o segredo no GitHub. O comando pede pra colar o token e não mostra na tela:

   ```bash
   gh secret set CLAUDE_CODE_OAUTH_TOKEN -R DaviUrsulino/arquivo-sombrio-pipeline
   ```

4. Testa disparando a produtora uma vez:

   ```bash
   gh workflow run produtora.yml -R DaviUrsulino/arquivo-sombrio-pipeline --ref master
   ```

   Se o vídeo sair (ou se ela disser que o banco está cheio), está funcionando.

## O que NÃO muda

- As memórias do Claude ficam neste PC (`~/.claude/projects/...`), então a conta nova continua sabendo de tudo.
- Os outros segredos do GitHub (Gemini, Instagram, ElevenLabs, Gradium) não dependem da conta do Claude.
- O repositório privado de segredos (`./segredos`) e a chave de deploy dele continuam iguais.

## Limite de uso

O plano da conta nova define quantos vídeos por dia a produtora consegue fazer. Com 4 posts por dia, o plano Pro
pode apertar. Se a cota acabar, a produtora falha com "You've hit your limit" e o maestro tenta de novo depois.
