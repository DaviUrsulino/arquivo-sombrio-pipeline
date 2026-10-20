# Kit Engenharia com IA — software bem feito, mesmo quando a IA escreve o código

Você usa Claude Code (ou outro agente) para construir, e quer que o resultado tenha requisito, teste, arquitetura e
segurança de verdade, sem virar especialista. Este kit transforma o seu Claude em um engenheiro que **decide e entrega
certo**, sem ficar perguntando "quais testes você quer?".

## Em 10 minutos
1. Copie o conteúdo desta pasta para a **raiz do seu projeto** (inclusive a pasta oculta `.claude/`):
   ```bash
   cp -r kit-engenharia/. meu-projeto/
   ```
2. Abra o Claude Code dentro do projeto.
3. Abra `PROMPT-DE-ATIVACAO.md`, copie o bloco, troque a "primeira tarefa" pela sua e envie.

Pronto. A partir daí o Claude lê as regras, segue o método e entrega com prova.

## O que muda na prática
| Sem o kit | Com o kit |
|---|---|
| "Pronto!" sem ter rodado | Só vale o que foi executado, com saída real em `docs/evidencias.md` |
| Testes que sempre passam | Defeitos injetados de propósito; sobreviveu algum, falta teste |
| Pergunta sobre método a cada passo | Decide, registra a suposição e segue (no máximo 3 perguntas, e só de negócio) |
| Sem documentação | Requisitos, decisões (ADR) e arquitetura em `docs/`, no tamanho certo para o projeto |
| Segurança lembrada no fim, ou nunca | Checklist aplicado em todo diff (segredos, autorização, injeção, IA) |

## O que vem no kit
- `CLAUDE.md` — as regras (decida, não pergunte; definição de pronto; o que é proibido; rigor por tamanho de tarefa).
- `.claude/skills/` — o método, uma skill por assunto, que o Claude aciona sozinho:
  `eng-requisitos`, `eng-arquitetura`, `eng-testes`, `eng-qualidade`, `eng-seguranca`, `eng-auditoria`.
- `ferramentas/mutar.py` — injeta defeitos e diz se os seus testes pegam. Funciona em Python, JavaScript e linguagens parecidas.
- `templates/` — requisitos, ADR, plano de testes, checklist de segurança, relatório de entrega, evidências, decisões.
- `exemplo/` — um projeto pequeno entregue com o método, para você ver o resultado.
- `REFERENCIAS.md` — as fontes (livros, artigos, normas, repositórios) por trás de cada regra.

## Os dois modos de uso
- **Projeto novo:** cole o prompt com a ideia. O Claude escreve requisitos curtos, escolhe a arquitetura, faz teste primeiro,
  injeta defeitos, revisa segurança e entrega o relatório.
- **Projeto que já existe:** peça "rode a skill `eng-auditoria`". Você recebe nota de 0 a 3 por dimensão com evidência e as
  correções em ordem de risco, antes de qualquer mudança.

## Limites (leia)
- O kit melhora muito a chance de a IA entregar algo sólido, mas não substitui revisão humana em sistema crítico
  (dinheiro, saúde, dado sensível). Ele reduz risco, não o elimina.
- Não é curso nem consultoria, e não tem suporte individual.
- Exige o agente executar comandos no seu computador (Claude Code ou equivalente) para rodar os testes.
- Material baseado em estudo de Engenharia de Software e em fontes abertas listadas em `REFERENCIAS.md`.
