# Checklists

Imprima ou deixe aberto. Marcou tudo, pode seguir.

## 1. Começar um projeto novo com Claude Code (10 minutos)

- [ ] O projeto está em uma pasta com controle de versão (`git init`) e com `.gitignore`.
- [ ] `.env` e qualquer arquivo com segredo estão no `.gitignore` **antes** do primeiro commit.
- [ ] Rodei `claude` na pasta do projeto e depois `/init`.
- [ ] Abri o `CLAUDE.md` e completei com o modelo do meu tipo de projeto.
- [ ] Os comandos de instalar, rodar e testar estão no `CLAUDE.md` e **eu os executei** para ver se funcionam.
- [ ] Tem uma seção "o que não fazer" (segredos, dependência nova, apagar teste).
- [ ] O arquivo tem menos de 200 linhas.
- [ ] Rodei `/doctor prompt-audit` e li o relatório.
- [ ] A primeira tarefa grande eu fiz com `/plan`.

## 2. Antes de aceitar o código que o Claude escreveu

- [ ] Eu li o diff inteiro (não só o resumo).
- [ ] O Claude **rodou** os testes e eu vi o resultado, não só a afirmação.
- [ ] Mudou só o que eu pedi? Algum arquivo que eu não esperava foi tocado?
- [ ] Apareceu dependência nova? Eu aprovei?
- [ ] Tem segredo, chave ou senha no código ou nos logs?
- [ ] Toda entrada de usuário é validada antes de ser usada?
- [ ] Algum teste foi apagado, pulado ou enfraquecido para passar?
- [ ] Eu entendo o que o código faz. Se não, pedi o prompt 12 (explicar).
- [ ] Commit pequeno, com mensagem que diz o porquê.

## 3. Antes de publicar ou entregar

- [ ] Todos os testes passam numa execução limpa (sem cache).
- [ ] O projeto instala e roda seguindo só o README, em uma pasta nova.
- [ ] Nenhum `print`/`console.log` de depuração sobrou.
- [ ] Variáveis de ambiente necessárias estão documentadas (sem os valores).
- [ ] Revisei o código com o prompt 9 (revisão cética) e o prompt 11 se há entrada de dados.
- [ ] Sei o que fazer se der errado (como voltar para a versão anterior).

## 4. O Claude começou a errar sempre a mesma coisa

- [ ] Está no `CLAUDE.md`? Se não, acrescente **uma linha** dizendo o contrário, de forma concreta.
- [ ] A regra contradiz outra do arquivo? Rode `/doctor prompt-audit`.
- [ ] A conversa está muito longa? Use `/compact` ou comece outra com `/clear`.
- [ ] O pedido tinha objetivo, contexto, limite e prova? Se faltou algum, refaça o pedido.
