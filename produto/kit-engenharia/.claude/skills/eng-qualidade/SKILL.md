---
name: eng-qualidade
description: Define o que significa "qualidade" para este projeto com métricas que respondem perguntas reais (GQM), e faz verificação estática antes de encerrar. Use ao fechar uma entrega, ao refatorar, ou quando alguém pergunta "isso está bom?".
---

# Qualidade medida, não opinada

Qualidade de **processo** é como o software é feito; de **produto** é o que foi entregue. Os dois se influenciam.
Não meça por medir: derive a métrica do objetivo.

## Passo 1 — Escolha 3 atributos que importam (de 8, SQuaRE / ISO 25010)
Adequação funcional, eficiência de desempenho, compatibilidade, usabilidade, confiabilidade, segurança,
manutenibilidade, portabilidade. Não otimize todos. Nomeie três e escreva por que, em `docs/qualidade.md`.
Ex.: app de pagamento → segurança, confiabilidade, adequação funcional. Ferramenta pessoal → usabilidade, manutenibilidade.

## Passo 2 — GQM (Goal → Question → Metric)
Para cada atributo escolhido:
- **Goal** (objetivo): "reduzir o tempo de resposta da busca".
- **Question** (pergunta que diz se atingiu): "qual o tempo médio de resposta hoje?".
- **Metric** (dado concreto): "latência p95 em ms, medida em 100 requisições".
Registre a meta numérica e meça de verdade. Sem número, não é métrica.

## Métricas práticas por atributo (escolha as que respondem suas perguntas)
- Funcional: % de critérios de aceitação com teste passando.
- Manutenibilidade: complexidade ciclomática por função (alerta acima de 10), duplicação, tamanho de arquivo, cobertura.
- Confiabilidade: taxa de erro, comportamento sob falha injetada.
- Desempenho: latência p95, memória, tempo de build.
- Segurança: itens do checklist OWASP atendidos, dependências com vulnerabilidade conhecida.

## Quando não há ferramenta
Se o projeto não tem analisador, não instale um só para isso. Use métrica manual honesta: contagem de requisitos Must com teste
passando, placar do `ferramentas/mutar.py`, tamanho das maiores funções (`wc -l`), número de dependências. Marque como
"não medido" o que não deu para medir, em vez de inventar.

## Passo 3 — Verificação estática (antes de encerrar, sempre)
Leia o próprio diff como se fosse de outra pessoa. Checklist:
- Nomes dizem o que a coisa faz? Funções fazem uma coisa só?
- Há código morto, comentário mentiroso, `TODO` esquecido, `console.log` de depuração?
- Erro é tratado ou engolido? Mensagem de erro vaza detalhe interno?
- Há duplicação que merece função? Há abstração sem uso (excesso de engenharia)?
- Cada requisito tocado tem teste? Cada ADR ainda vale?
Rode também o linter e o analisador de tipos do projeto e corrija o que apontarem.

## Passo 4 — Custo da qualidade
Defeito em produção custa muito mais que defeito achado no teste. Se estiver em dúvida entre "mais um teste agora" e
"consertar depois", escolha o teste. Registre dívida técnica que decidiu aceitar, com motivo, em `docs/decisoes.md`.

## Saída
`docs/qualidade.md`: 3 atributos, tabela GQM com meta e valor medido, achados da revisão estática e dívida aceita.
