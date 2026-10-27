---
name: eng-arquitetura
description: Define a estrutura do sistema com diagramas e decisões registradas (ADR) antes de codar. Use ao iniciar projeto, ao integrar serviço externo, ao mudar a estrutura de classes ou módulos, ou quando o código "funciona mas está bagunçado".
---

# Arquitetura e desenho, sem enfeite

Código que funciona com a estrutura errada vira dívida. Desenhe o mínimo certo e registre o porquê.

## Passo 1 — Modelo estático (diagrama de classes ou de entidades)
Liste entidades, atributos e operações. O ponto que mais erra é o **tipo de relacionamento**. Não use
"associação" para tudo. Escolha de propósito, do mais fraco ao mais forte:
1. **Dependência**: uso pontual, sem vínculo permanente. Ex.: um serviço usa um formatador.
2. **Associação**: ligação estrutural, com cardinalidade (1..1, 1..*, *..*). Ex.: Cliente faz Pedido.
   - Relação `*..*` que guarda dado próprio vira **classe associativa** (nota do aluno na disciplina: o dado é da matrícula).
   - Associação com a própria classe precisa de **papéis** (supervisor / supervisionado).
3. **Agregação** ("tem"): a parte existe sem o todo. Empresa tem Funcionário.
4. **Composição** ("é composto de"): a parte não existe sem o todo. Pedido contém ItensDoPedido; apagou o pedido, apagou os itens.
5. **Generalização** ("é um"): herança. Só use quando a frase "X é um Y" vale em **todo** caso. Na dúvida, prefira composição.
6. **Realização**: implementa uma interface.
Desenhe em Mermaid dentro de `docs/arquitetura.md`.

## Passo 2 — Componentes (se há mais de uma peça)
Se existem frontend/backend, fila, banco ou API externa, desenhe quem **oferece** e quem **requer** cada interface.
Cada seta precisa de um nome de protocolo (HTTP, SQL, evento).

## Passo 3 — Modelo dinâmico, só onde o fluxo é complexo
- **Sequência**: qualquer fluxo com mais de 2–3 passos entre usuário, sistema e serviço externo (login, pagamento, upload).
- **Estados**: quando uma entidade muda de status (pedido: criado → pago → enviado → entregue; liste as transições proibidas).
- **BPMN**: só se o problema é um processo de negócio com papéis diferentes, não um CRUD.

## Passo 4 — Escolha do estilo e registro da decisão (ADR)
Escolha o estilo pelo problema, não por moda. Monólito modular costuma bastar para um MVP; microserviço só com
motivo escrito. Para **toda** decisão que seria cara de desfazer (banco, framework, provedor externo, forma de
autenticar, estrutura de pastas), crie um ADR em `docs/adr/NNNN-titulo.md` com `templates/adr.md`:
**contexto → decisão → consequências** (inclua o lado ruim).

## Decisões padrão (use quando o contexto bater, citando o motivo no ADR)
- MVP com IA pesada: API paga por uso antes de GPU própria.
- Provedor externo instável ou com cota: cascata de 2 a 4 alternativas, tentadas em ordem.
- Saída de LLM com limites de formato: valide no código, nunca confie no prompt.
- Cobrança e crédito: operação idempotente (repetir a chamada não cobra duas vezes).
- Integração externa frágil: tenha um caminho manual simples de contingência.
- Dashboard da primeira versão: comece no canal que já existe e migre quando doer.

## Passo 5 — Regras de estrutura que o código deve respeitar
- Regra de negócio fica em uma camada própria, longe de controller e de tela.
- Acesso a banco e a serviço externo fica atrás de uma interface (permite trocar e testar com dublê).
- Dependência aponta para dentro: tela e banco conhecem o domínio; o domínio não conhece tela nem banco.
- Nenhum módulo importa outro "por conveniência" criando ciclo.

## Se o sistema já existe (engenharia reversa)
Recupere o projeto a partir do código, em ordem: estrutura de pastas → entidades e relações → fluxos principais
(sequência) → decisões implícitas (vire ADR com status "aceito, retroativo"). Mantenedores gastam boa parte do tempo só
entendendo o software; documentar isso agora corta esse custo.

## Saída
`docs/arquitetura.md` (diagramas Mermaid + texto curto) e ADRs em `docs/adr/`.
