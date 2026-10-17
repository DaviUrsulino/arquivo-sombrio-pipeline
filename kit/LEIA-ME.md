# Kit do iniciante em Claude Code

Do perfil [@robo.estagiario](https://www.instagram.com/robo.estagiario/). Três arquivos, grátis:

1. [`modelo-CLAUDE.md`](modelo-CLAUDE.md): modelo do arquivo de regras que o Claude Code lê em toda
   sessão, para ele parar de esquecer o seu projeto.
2. [`prompt-planejamento.md`](prompt-planejamento.md): o prompt para o Claude planejar antes de editar
   (plan mode), com o checklist para revisar o plano.
3. [`guia-de-comandos.md`](guia-de-comandos.md): os comandos e atalhos do Claude Code conferidos na
   documentação oficial (`/rewind`, `/context`, `/resume`, `/compact`, `/clear`, `Shift+Tab` e mais).

## Ordem sugerida

1. Abra o terminal na pasta do projeto e rode `claude`.
2. Rode `/init` para gerar um primeiro CLAUDE.md automaticamente.
3. Complete com o `modelo-CLAUDE.md` (comandos, convenções, o que não fazer).
4. Na próxima tarefa grande, use o `prompt-planejamento.md`.

## Fonte

Os fatos sobre o Claude Code (sessão começa sem memória, CLAUDE.md carregado em toda sessão, `/init`,
limite de 200 linhas recomendado, `/plan` e `Shift+Tab`) vêm da documentação oficial:
<https://code.claude.com/docs/en/memory> e <https://code.claude.com/docs/en/permission-modes>.
O Claude Code muda rápido, então se algum comando não bater com a sua versão, confira a documentação.

Licença: use, copie e adapte à vontade.
