# Página de venda: Kit Engenharia com IA

Sem promessa de renda ou de resultado garantido. Preço decidido: R$ 37 (pagamento único).

- **Nome:** Kit Engenharia com IA: software bem feito mesmo quando a IA escreve o código
- **Descrição curta:** Faça o Claude Code entregar com requisito, teste, arquitetura e segurança de verdade: regras, 6 skills, script que prova seus testes e exemplo pronto.
- **Arquivo:** `produto/kit-engenharia.zip`

---

## Seu código funciona. Mas você sabe se está bom?

Quando a IA escreve o código, o projeto sobe rápido. E fica a dúvida: tem teste de verdade? Alguém pensou na arquitetura? A senha está protegida? Se a IA disse "pronto", ela rodou o código ou só achou que funcionava?

Um estudo da Veracode (2025) encontrou falha de segurança em 45% das tarefas de código geradas por mais de 100 modelos de IA. Cobertura de teste alta também engana: já se mediu suíte com 100% de cobertura que detectava só 4% dos defeitos injetados.

O **Kit Engenharia com IA** transforma o seu Claude Code em um engenheiro que **decide e entrega certo**, sem ficar perguntando "quais testes você quer?". Eu sou estudante de Engenharia de Software na UnB e juntei o que estudo (requisitos, arquitetura, testes, qualidade) com boas práticas abertas num formato que o agente lê e segue sozinho.

### O que vem no kit

- **`CLAUDE.md` com as regras:** decida em vez de perguntar, definição de pronto, o que é proibido (apagar teste para passar, dizer "pronto" sem rodar) e o rigor certo para cada tamanho de tarefa.
- **6 skills que o Claude aciona sozinho:**
  - **Requisitos:** do pedido vago ao documento testável (níveis, MoSCoW, critérios Dado/Quando/Então).
  - **Arquitetura:** diagramas com o relacionamento certo e decisões registradas (ADR).
  - **Testes:** o que testar, valores-limite, dublês, TDD e prova de que o teste funciona.
  - **Qualidade:** métricas com GQM e revisão do próprio código.
  - **Segurança:** segredos, autorização, injeção, LGPD e os riscos de IA (injeção de prompt, saída do modelo, gasto sem teto).
  - **Auditoria:** nota por dimensão e correções em ordem de risco, para projeto que já existe.
- **`mutar.py`:** injeta defeitos no seu código e diz se os seus testes pegam. Se um defeito sobrevive, falta teste.
- **Templates:** requisitos, ADR, plano de testes, checklist de segurança, relatório de entrega.
- **Um projeto de exemplo** entregue com o método, com testes passando.
- **Referências:** livros, normas e artigos por trás de cada regra.

### Como usar (10 minutos)

1. Copie a pasta do kit para a raiz do seu projeto.
2. Abra o Claude Code e cole o prompt de ativação do arquivo `PROMPT-DE-ATIVACAO.md`.
3. Escreva a sua tarefa em uma ou duas frases. Se o projeto já existe, peça a auditoria primeiro.

### Para quem é

- Quem constrói com IA (vibe coding) e quer mais segurança de que o resultado aguenta.
- Quem está começando e não quer aprender engenharia de software em ordem de livro antes de entregar.
- Quem já programa e quer padronizar como o agente trabalha.

### Para quem não é

- Quem procura curso em vídeo, mentoria ou suporte individual. É um kit de arquivos.
- Quem usa só chat no navegador. O kit precisa de um agente que execute comandos (Claude Code ou equivalente).
- Quem constrói sistema crítico (dinheiro, saúde, dado sensível) e quer dispensar revisão humana. O kit reduz risco, não elimina.

### Investimento

**R$ 37**, pagamento único, acesso imediato. Garantia de 7 dias, conforme o direito de arrependimento em compras online.

### Perguntas frequentes

**Funciona só com Claude Code?** Foi testado com o Claude Code. Os arquivos são Markdown e um script em Python, e a ideia vale para outros agentes, mas as skills automáticas são do Claude Code.

**Preciso saber programar?** Ajuda, mas a ideia é justamente o agente cumprir o método por você. Você precisa conseguir rodar comandos no terminal.

**Em quais linguagens funciona?** O método vale para qualquer uma. O script `mutar.py` funciona bem em Python, JavaScript e linguagens parecidas.

**É igual ao Spec Kit do GitHub?** O Spec Kit é um bom projeto gratuito e aberto, focado em especificação. Este kit é em português, mais enxuto, e junta especificação, teste (com prova de que o teste funciona) e segurança.

**Isso garante software sem bug?** Não. Garante um método que reduz muito a chance de entregar algo frágil, e deixa evidência do que foi verificado.
