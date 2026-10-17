# Modelo de CLAUDE.md

Copie este arquivo para a raiz do seu projeto com o nome `CLAUDE.md`, troque tudo que está entre
`[colchetes]` e apague as linhas que não se aplicam. O Claude Code lê esse arquivo no começo de toda
sessão, então ele não precisa que você repita as regras toda vez.

Regra de ouro: **mantenha abaixo de 200 linhas**. A documentação do Claude Code avisa que arquivo
longo gasta contexto e reduz a obediência. Escreva instruções que dá para verificar:

- Ruim: "formate o código direito". Bom: "use indentação de 2 espaços".
- Ruim: "teste suas mudanças". Bom: "rode `npm test` antes de commitar".
- Ruim: "mantenha os arquivos organizados". Bom: "os handlers da API ficam em `src/api/handlers/`".

Atalho: dentro do projeto, rode `/init` e o Claude Code gera um primeiro CLAUDE.md analisando o seu
código. Depois use este modelo para completar o que ele não tem como adivinhar (suas preferências).

---

# [Nome do projeto]

[Uma frase: o que o projeto faz e para quem.]

## Comandos

- Instalar dependências: `[ex.: npm install]`
- Rodar em desenvolvimento: `[ex.: npm run dev]`
- Rodar os testes: `[ex.: npm test]`
- Rodar um teste só: `[ex.: npm test -- caminho/do/arquivo]`
- Checar tipos e estilo: `[ex.: npm run lint]`

## Estrutura

- `[src/]`: [o que mora aqui]
- `[tests/]`: [o que mora aqui]
- `[docs/]`: [o que mora aqui]

## Convenções de código

- Linguagem e versão: [ex.: TypeScript 5, Node 22]
- Estilo: [ex.: indentação de 2 espaços, aspas simples]
- Nomes: [ex.: arquivos em kebab-case, componentes em PascalCase]
- [Uma regra específica do seu projeto que o Claude erra com frequência]

## Antes de dizer que terminou

1. Rode `[comando de testes]` e mostre o resultado.
2. Rode `[comando de lint]` e corrija os avisos que você causou.
3. Diga o que mudou em até 5 linhas e o que ficou sem testar.

## O que não fazer

- Não edite `[pasta gerada ou de terceiros, ex.: dist/ e vendor/]`.
- Não adicione dependência nova sem me perguntar antes.
- Não apague testes para fazê-los passar.
- Nunca coloque senha, token ou chave de API no código ou no commit. Use `[.env]` e confira que ele
  está no `.gitignore`.

## Como eu gosto de trabalhar

- Para mudanças grandes, mostre um plano curto antes de editar.
- Faça commits pequenos, com mensagem no formato `[ex.: feat: ..., fix: ...]`.
- Responda em [português / inglês] e seja direto.

## Contexto que você não consegue adivinhar

- [Decisão de arquitetura e o motivo, ex.: "usamos SQLite porque o app roda offline"]
- [Armadilha conhecida, ex.: "o teste de pagamento só passa com a variável X definida"]
- [Coisa que parece bug mas é de propósito]
