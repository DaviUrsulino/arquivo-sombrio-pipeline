# Kit Claude Code

Do perfil [@ursulino.ia](https://www.instagram.com/ursulino.ia/). Versão 1.0, outubro de 2026.

Este kit existe para resolver uma coisa: **o Claude Code começa toda sessão sem lembrar do seu
projeto**. Se você não escreve as regras em lugar nenhum, repete tudo toda vez e recebe código fora do
seu padrão. Aqui você tem as regras prontas e os prompts para pedir direito.

## O que tem aqui

| Pasta/arquivo | Quando usar |
|---|---|
| `01-modelos-claude-md/` | No começo de qualquer projeto: escolha o modelo do seu tipo de projeto |
| `02-prompts.md` | No dia a dia: 20 prompts prontos, por etapa (planejar, implementar, revisar...) |
| `03-checklists.md` | Para começar um projeto e antes de aceitar código |
| `04-guia-de-comandos.md` | Para consultar comandos e atalhos do Claude Code |

## Em 15 minutos

1. **(2 min)** Abra o terminal na pasta do projeto e rode `claude`.
2. **(2 min)** Rode `/init`. O Claude Code lê o seu projeto e cria um primeiro `CLAUDE.md`.
3. **(5 min)** Abra o modelo do seu tipo de projeto em `01-modelos-claude-md/` e passe para o seu
   `CLAUDE.md` o que o `/init` não adivinhou: comandos que você usa, o que não pode fazer, suas
   preferências.
4. **(3 min)** Rode `/doctor prompt-audit` para o Claude procurar regras desatualizadas ou
   contraditórias nos seus arquivos de instrução (requer Claude Code v2.1.283 ou mais novo).
5. **(3 min)** Na próxima tarefa, use o prompt 1 de `02-prompts.md` (planejar antes de editar).

## As 3 regras que mais mudam o resultado

1. **Regras concretas, curtas e verificáveis.** "Rode `npm test` antes de commitar" funciona.
   "Teste direito" não. Mantenha o `CLAUDE.md` abaixo de 200 linhas.
2. **Plano antes de código** em tarefa que mexe em mais de um arquivo.
3. **Peça a prova.** Todo "terminei" tem que vir com o comando rodado e o resultado.

## Aviso

O Claude Code muda com frequência. Tudo que está aqui foi conferido na documentação oficial em
outubro de 2026 (<https://code.claude.com/docs>). Se algo não bater com a sua versão, a documentação
manda. Este kit não tem vínculo com a Anthropic. Prompts ajudam, mas não garantem resultado: você
continua sendo quem revisa o que o Claude escreve.
