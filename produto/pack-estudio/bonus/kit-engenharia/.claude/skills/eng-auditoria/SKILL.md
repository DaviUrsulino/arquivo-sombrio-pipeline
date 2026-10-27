---
name: eng-auditoria
description: Audita um projeto que já existe (inclusive feito 100% com IA) e entrega um relatório com nota por dimensão e as correções mais importantes em ordem. Use quando o usuário disser "audita", "confere meu projeto" ou ao começar em um repositório desconhecido.
---

# Auditoria de projeto existente

Não mude nada antes de entender. Primeiro diagnostique, depois corrija em ordem de risco.

## Passo 1 — Reconhecimento (rápido, só leitura)
Descubra: linguagem e frameworks, como rodar, como testar, estrutura de pastas, tamanho, histórico recente do git,
se há CI, README e `.env.example`. Rode os testes existentes e o linter e anote o resultado real.

## Passo 2 — Nota de 0 a 3 por dimensão (com evidência)
0 = ausente ou perigoso · 1 = frágil · 2 = aceitável · 3 = sólido.
| Dimensão | O que olhar |
|---|---|
| Requisitos | Existe descrição do que o sistema deve fazer, com critérios testáveis? |
| Arquitetura | Estrutura coerente? Regra de negócio separada de tela e banco? Decisões registradas? |
| Testes | Há testes? Passam? Cobrem valores-limite e erros? **Injete 3 defeitos e veja se algum teste falha.** |
| Qualidade | Código legível, sem duplicação grande, funções curtas, linter limpo? |
| Segurança | Segredos, autorização, injeção, entrada validada, dependências (ver `eng-seguranca`). |
| Operação | Roda de forma reproduzível? Há CI, log útil, tratamento de falha, backup? |
| Documentação | README permite subir o projeto do zero em 10 minutos? |
Cada nota exige uma linha de evidência (arquivo, comando, saída). Sem evidência, não dê nota.

## Passo 3 — Lista de correções ordenada
Ordene por **risco × esforço**: primeiro o que expõe dado ou quebra o negócio (segredo vazado, rota sem autorização,
sem teste no fluxo principal), depois o que atrapalha a manutenção. No máximo 10 itens, cada um com: problema,
por que importa, correção proposta, esforço (P/M/G).

## Passo 4 — Corrija em fatias
Para cada item, em ordem: teste que falha → correção → suíte verde → commit pequeno. Pare e reporte ao fim dos
itens CRÍTICOS e ALTOS. Não reescreva o projeto: melhore sem quebrar o que funciona.

## Saída
`docs/auditoria.md` com: resumo em 5 linhas, tabela de notas com evidência, lista das correções, o que foi corrigido e o que ficou.
Seja honesto: se o projeto está bom, diga que está bom.
