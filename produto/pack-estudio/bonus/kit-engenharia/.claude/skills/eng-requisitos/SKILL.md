---
name: eng-requisitos
description: Transforma um pedido vago em requisitos claros, priorizados e testáveis, sem interrogar o usuário. Use ao começar qualquer funcionalidade ou projeto novo, antes de escrever código.
---

# Requisitos sem interrogatório

Objetivo: sair de "quero um app de X" para um documento curto que dê para testar. Você infere, o usuário corrige.

## Passo 1 — Entenda o problema, não só a solução
Antes de listar requisitos, escreva em 3 linhas: **quem** tem a dor, **qual** é a dor, **como resolvem hoje**
(planilha, mensagem, de cabeça). Se o usuário não disse, infira o cenário mais comum e marque `[SUPOSIÇÃO]`.
O que as pessoas pedem costuma ser desejo ou frustração; o requisito real está na necessidade por trás.

## Passo 2 — Escreva nos três níveis (não misture)
- **Negócio** (por quê): a meta. Ex.: "reduzir o tempo para registrar um pedido".
- **Usuário** (o quê): o que a pessoa precisa conseguir. Ex.: "o atendente registra um pedido em menos de 1 min".
- **Produto** (como, comportamental): o que o sistema faz e vai para teste. Ex.: "RF-03: ao enviar o formulário com campos válidos, o sistema grava o pedido e mostra o número".

Classifique cada item como **RF** (funcional), **RNF** (desempenho, segurança, usabilidade, restrição) ou
**RN** (regra de negócio que não pode ser violada). Dê ID estável (RF-01, RNF-01, RN-01).

## Passo 3 — Priorize com MoSCoW
- **Must**: sem isso não sai. **Should**: importante, a v1 sobrevive sem. **Could**: bônus.
- **Won't (agora)**: registre o que ficou de fora, para ninguém confundir com "nunca".
Regra de bolso: se tudo é Must, nada foi priorizado. Mantenha Must em no máximo 60% dos itens.

## Passo 4 — Critério de aceitação testável
Cada RF Must ganha ao menos um critério no formato **Dado / Quando / Então**, com valores concretos.
Inclua o caso limite e o caso inválido. Esses critérios viram os testes (ver `eng-testes`).

## Passo 5 — Verificação (o texto está bom?)
Cada requisito deve ser: **atômico** (uma coisa só), **testável** (existe um jeito objetivo de provar),
**sem ambiguidade** (nada de "rápido", "fácil", "bonito" sem número), **consistente** (não contradiz outro)
e **rastreável** (tem ID e vira teste). Reescreva o que falhar.

## Passo 6 — Validação (é isso que a pessoa precisa?)
Devolva ao usuário um resumo de 5 linhas: "Entendi que X sofre com Y e precisa de Z; vou entregar A, B, C; deixei D de fora."
Não espere resposta para continuar: siga com as suposições e deixe o resumo visível. Se o usuário corrigir, ajuste.

## Saída
Preencha `templates/requisitos.md` e salve em `docs/requisitos.md`. Registre suposições em `docs/decisoes.md`.

## Erros comuns que você deve evitar
- Requisito que é solução disfarçada ("usar MongoDB") quando a necessidade era "guardar pedidos".
- RNF vazio ("o sistema deve ser seguro"). Diga o quê: "senha com hash, sessão expira em 30 min".
- Esquecer o usuário que não é o principal (administrador, suporte).
