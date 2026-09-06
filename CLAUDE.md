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
