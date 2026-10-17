# Modelo: site / front-end

Copie para a raiz do projeto como `CLAUDE.md`. Troque o que está entre `[colchetes]` e apague o que
não se aplica. Mantenha abaixo de 200 linhas.

---

# [Nome do site]

[Uma frase: o que o site faz e para quem.]

## Comandos

- Instalar: `[npm install]`
- Rodar em desenvolvimento: `[npm run dev]` (abre em `[http://localhost:3000]`)
- Build de produção: `[npm run build]`
- Testes: `[npm test]`
- Lint e tipos: `[npm run lint]` e `[npx tsc --noEmit]`

## Estrutura

- `[src/app/]` ou `[src/pages/]`: rotas e páginas
- `[src/components/]`: componentes reutilizáveis (um por arquivo)
- `[src/lib/]`: funções utilitárias e acesso a dados
- `[public/]`: imagens e arquivos estáticos

## Convenções

- Linguagem: [TypeScript, sem `any`]
- Componentes: [função, PascalCase, props tipadas]
- Estilo: [Tailwind / CSS Modules]. Não crie CSS global novo sem me perguntar.
- Textos da interface em [português do Brasil].
- Acessibilidade: todo `img` com `alt`, todo botão com texto ou `aria-label`, foco visível.

## Antes de dizer que terminou

1. Rode `[npm run lint]` e `[npm run build]`; mostre se passou.
2. Se mexeu em interface, abra no navegador e descreva o que viu (ou rode o teste de interface).
3. Diga o que mudou em até 5 linhas e o que não conseguiu verificar.

## O que não fazer

- Não adicione biblioteca nova sem me perguntar (peso do site e manutenção).
- Não coloque chave de API ou token no código do navegador. Segredo só em variável de ambiente do
  servidor, e `.env` no `.gitignore`.
- Não apague nem "pule" teste para passar.
- Não use `dangerouslySetInnerHTML` ou equivalente com texto vindo de usuário.

## Contexto que você não adivinha

- [Decisão de design: ex. "paleta e fontes estão em `tailwind.config`; não invente cor nova"]
- [Armadilha: ex. "a rota /checkout só funciona com a variável X"]
