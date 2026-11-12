# Instruções pro Claude Code neste repositório

Leia `README.md` inteiro antes de mexer em qualquer coisa — ele documenta decisões técnicas
já validadas manualmente numa sessão de teste real (não são suposições, são resultado de
~10 iterações testando o que funciona e o que não funciona nas APIs usadas aqui).

Pontos que **não devem ser alterados sem revalidar visualmente primeiro** (gerar e olhar o
resultado antes de assumir que uma mudança é melhoria):
- O texto do master style lock em `src/estilo.py`.
- As configurações de imagem em `src/montar_video.py` (`resize: cover`, `duration: -2`,
  ausência de `pan`, `resolution: instagram-story`).
- A decisão de manter a geração de imagem manual (Leonardo AI) em vez de automática — foi
  testado e falhou repetidamente via API direta (ver README, seção "O que já foi validado").

Este é um projeto pessoal do Davi (estudante de Engenharia de Software, UnB Gama), separado do
segundo cérebro dele em Obsidian — não misturar contexto dos dois.

Instagram (@ursulino.ia): ler `docs/INSTAGRAM-ESTADO.md` antes de mexer no pipeline do Instagram.

**Antes de escrever roteiro, escolher formato de vídeo ou mexer na grade de horários, leia
`segredos/FORMATOS.md`.** É o catálogo do que já foi MEDIDO (views de 20 contas de referência, 6 transcrições
com 11 milhões de views somados, horários do nosso perfil e os formatos que já morreram aqui). Davi, 11/11:
"às vezes tu alucina, fala que esqueceu — e esquecer vai ter que fazer tudo de novo". Esse arquivo existe para
isso não acontecer: não redescubra na unha o que já está medido lá, e atualize-o quando medir algo novo.
