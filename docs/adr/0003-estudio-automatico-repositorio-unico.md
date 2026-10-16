# 0003 — Um repositório só ("estúdio automático") para todos os canais

- **Status:** aceito
- **Data:** 2026-10-14

## Contexto

O repositório nasceu como `arquivo-sombrio-pipeline`, um pipeline de vídeo dark para um canal
do YouTube. Hoje ele já opera 2 contas do YouTube, monta vídeos para o TikTok e tem um
publicador do Instagram (`src/publicar_instagram.py`). Surgiu um canal novo, o perfil
**@robo.estagiario** no Instagram: Reels e carrosséis ensinando ferramentas de IA, no estilo
"neon desenhado à mão".

Havia duas opções: criar um repositório novo para o Instagram ou ampliar este. As peças que o
canal novo precisa — agendamento no GitHub Actions, segredos, publicação nas APIs oficiais,
cascata de provedores de LLM — já existem e já rodam em produção aqui.

## Decisão

Manter **um repositório só**, renomeado para `estudio-automatico`. Cada canal continua isolado
na sua configuração, e o código compartilhado fica em módulos comuns.

A reorganização segue o padrão de **estrangulamento** (strangler), não uma reescrita única:

1. O canal novo do Instagram entra num pacote próprio, `src/estudio_instagram/`, já com testes
   e CI. Ele reaproveita `publicar_instagram.py` em vez de duplicar.
2. Os módulos antigos (terror e tendências) só são movidos para pacotes comuns um de cada vez,
   cada movimento protegido por testes de caracterização escritos **antes** da mudança.
3. Nenhuma mudança de comportamento nos canais que já publicam sozinhos entra misturada com
   reorganização de pasta.

## Consequências

- Um lugar só para segredos, agendamento e publicação. Corrigir um bug no publicador corrige
  todos os canais.
- O repositório passa a ter dois motores de render: o atual (Python + ffmpeg) e o Hyperframes
  (Node + Chrome) para o Instagram (ver ADR-0004). O `requirements.txt` não muda para os
  canais antigos; o canal novo traz `package.json` próprio.
- Renomear o repositório no GitHub mantém redirecionamento do link antigo, mas
  `REPO_PADRAO` em `src/publicar_instagram.py` precisa ser atualizado junto.
- Risco: um erro no código comum afeta todos os canais. Mitigação: testes no CI rodando em
  todo push e PR, e o canal novo começa isolado.
