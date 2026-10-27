# Modelo: mínimo para qualquer projeto

Se o seu tipo de projeto não está nos outros modelos, comece por este. São 25 linhas. Copie para a
raiz como `CLAUDE.md`.

---

# [Nome do projeto]

[Uma frase: o que faz e para quem.]

## Comandos

- Instalar: `[comando]`
- Rodar: `[comando]`
- Testar: `[comando]`

## Onde fica o quê

- `[pasta]`: [o que tem]
- `[pasta]`: [o que tem]

## Regras

- [Uma regra de estilo que dá para verificar]
- [Uma regra de estrutura que dá para verificar]

## Antes de dizer que terminou

1. Rode `[comando de teste]` e mostre o resultado.
2. Diga o que mudou e o que não conseguiu verificar.

## Nunca

- Colocar senha, token ou chave no código ou no commit.
- Apagar teste para fazê-lo passar.
- Adicionar dependência sem me perguntar.

---

## Como crescer a partir daqui

Quando o Claude errar a mesma coisa duas vezes, acrescente **uma linha** nas regras dizendo o contrário,
de forma concreta. Quando o arquivo passar de 200 linhas, mova o que só vale para uma parte do projeto
para um arquivo em `.claude/rules/` com escopo de caminho (veja `04-guia-de-comandos.md`).
