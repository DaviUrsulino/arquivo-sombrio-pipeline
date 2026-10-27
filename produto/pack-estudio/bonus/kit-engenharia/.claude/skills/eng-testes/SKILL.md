---
name: eng-testes
description: Projeta, escreve e PROVA testes automatizados sem perguntar ao usuário quais testes fazer. Use ao implementar qualquer funcionalidade, corrigir bug, ou quando disserem que "os testes passam" mas ninguém confia neles.
---

# Testes que provam alguma coisa

Teste que nunca falha não prova nada. Você decide quais testes escrever e prova que eles funcionam.

## Passo 1 — Escolha o nível (pirâmide)
Muitos de **unidade** (rápidos, isolados), alguns de **integração** (módulos juntos, banco real de teste),
poucos de **sistema/aceitação** (fluxo completo, no navegador se houver interface). Cada critério de aceitação
de `docs/requisitos.md` vira pelo menos um teste.

## Passo 2 — Projete os casos (não chute valores)
**Caixa-preta** (pela especificação):
- **Partição de equivalência**: agrupe entradas que devem se comportar igual e teste um valor de cada grupo.
- **Valor-limite**: teste exatamente na borda e um passo de cada lado (17, 18 e 19 para "maior de idade").
  A maioria dos bugs de regra mora na borda.
- **Tabela de decisão**: quando várias condições combinam, liste as combinações e o resultado de cada.
- Sempre inclua: entrada vazia, nula, tipo errado, valor negativo, texto gigante, caractere especial.
**Caixa-branca** (pelo código): garanta que cada desvio (`if`, `else`, `catch`, laço) é executado por algum teste.
Cobertura de linha é sinal, não garantia: 100% pode ainda esconder erro.

## Passo 3 — Escreva bem (FIRST e AAA)
**F**ast, **I**ndependent, **R**epeatable, **S**elf-validating, **T**imely. Estrutura **Arrange, Act, Assert**.
Um teste verifica um comportamento e o nome diz qual (`rejeita_idade_negativa`). Nada de teste que depende da ordem,
do relógio ou da internet.

## Passo 4 — Dublês para o que é lento ou imprevisível
Use *stub* (resposta fixa), *spy* (registra chamada), *mock* (verifica interação) e *fake* (versão simples, como banco em memória)
para API externa, e-mail, pagamento, relógio e aleatório. Não faça mock do que você está testando.

## Passo 5 — TDD quando a regra é clara
Red (teste falha pelo motivo certo) → Green (código mínimo) → Refactor (com teste verde). Para bug: primeiro o teste
que reproduz, depois a correção.

## Passo 6 — PROVE que os testes funcionam (injeção de defeitos)
Obrigatório antes de dizer "pronto". Cobertura de linha engana: já se viu suíte com 100% de cobertura e só 4% de
defeitos detectados. O que mede qualidade de teste é quantos defeitos injetados ele pega (mutation score).
1. Rode a suíte: tudo verde. Guarde a saída real em `docs/evidencias.md`.
2. Rode `python3 ferramentas/mutar.py <arquivo-do-código> --comando "<comando dos testes>"`. Ele troca operadores
   (`>=` por `>`, `+` por `-`, `and` por `or`, `True` por `False`…) um por vez, roda a suíte e diz PEGOU ou SOBREVIVEU,
   e sempre restaura o arquivo. Em linguagem que o script não cobre, faça à mão (e restaure com `git checkout`).
3. **Todo SOBREVIVEU exige ação**: escreva o teste que o pega, ou registre por que o defeito é equivalente (não muda o
   comportamento). Rode de novo até o placar fechar.
4. Registre no relatório o placar final (ex.: 14/14) e um exemplo de defeito que revelou teste faltando.
Rode o script nos arquivos de regra de negócio (domínio, validação, cálculo), não em código de cola.

## Passo 7 — Testes não funcionais proporcionais ao risco
- **Segurança**: autorização (usuário A não lê dado do usuário B), injeção, limite de tentativas. Ver `eng-seguranca`.
- **Desempenho**: só se houver requisito; meça p95 de latência com carga realista, não adivinhe.
- **Confiabilidade**: o que acontece quando o banco cai, a API externa demora ou devolve lixo.

## Passo 8 — Interface web: prova no navegador
Execute o fluxo principal num navegador de verdade (Playwright), tire screenshot do estado final e transforme o fluxo em
teste de ponta a ponta no CI. "A tela deve funcionar" não é evidência.

## Plano de testes
Para projeto ou módulo relevante, preencha `templates/plano-de-testes.md`: objetivo, escopo (dentro e fora), técnicas,
ambiente, critério de aprovação, tabela de casos (ID, entrada, esperado, obtido, status), resultado da execução e
a análise crítica com a injeção de defeitos.

## Proibido
Apagar teste para passar, usar `skip` sem motivo escrito, assert que sempre é verdadeiro, teste sem assert, copiar o
resultado do código para o "esperado" sem conferir contra o requisito.
