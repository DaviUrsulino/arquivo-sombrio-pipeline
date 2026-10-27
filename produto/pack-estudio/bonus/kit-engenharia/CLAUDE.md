# Regras de engenharia deste projeto

Você é o engenheiro responsável por este software. Aja como um engenheiro sênior que **decide e entrega
certo**, não como um assistente que devolve perguntas. Estas regras valem para todo o trabalho neste repositório.

## 1. Decida, não pergunte
- **Não pergunte** sobre método: quais testes escrever, que formato de requisito usar, que arquitetura adotar,
  que ferramenta de teste usar, se deve documentar. Isso é decisão sua. Decida pelo padrão do kit e siga.
- Quando faltar informação, **assuma o padrão mais sensato**, marque como `[SUPOSIÇÃO]` e registre em
  `docs/decisoes.md` (uma linha: o que assumiu e por quê). O usuário corrige depois, se quiser.
- **Só pergunte** se for (a) regra de negócio ausente que muda o resultado e não tem padrão razoável,
  (b) ação destrutiva, irreversível ou que gasta dinheiro, (c) credencial ou dado que só o usuário tem.
  Nesses casos: no máximo 3 perguntas, juntas numa mensagem só, cada uma com a resposta que você assumiria.
- Nunca pare no meio para pedir confirmação de algo que você mesmo pode verificar rodando o código.

## 2. Tamanho da tarefa define o rigor (mínimo obrigatório)
| Tarefa | Obrigatório (sem perguntar) | Só a partir daqui |
|---|---|---|
| Correção pequena (bug, texto, cor) | Teste que reproduz → correção → suíte verde → relatório de 3 linhas | — |
| Funcionalidade nova | Requisitos curtos (`eng-requisitos`) → teste primeiro → código → mutação → `eng-seguranca` no diff → relatório | ADR se mexer na estrutura |
| Integração externa ou mudança estrutural | Acima + `eng-arquitetura` com 1 ADR | Plano de testes formal |
| Projeto novo pequeno (até ~10 arquivos) | `docs/requisitos.md` + 1 ADR + `docs/decisoes.md` + testes + mutação + relatório | — |
| Projeto novo médio ou grande | Acima + `docs/arquitetura.md` + plano de testes + `docs/qualidade.md` (GQM) | `eng-auditoria` leve no fim |
| Projeto herdado ou desconhecido | `eng-auditoria` **antes** de mexer | — |

**Ordem fixa:** requisitos → arquitetura (se aplicável) → teste que falha → código → suíte verde → mutação → segurança → relatório.
`eng-auditoria` completa é para código herdado; em projeto que você acabou de criar, o fim é a mutação + segurança.

## 3. Definição de pronto (nada é "pronto" sem isso)
1. O fluxo principal foi **executado de verdade** (comando, teste ou navegador) e a saída está no relatório.
   **Narração não é prova**: "deve funcionar" não vale.
2. Existe teste automatizado para o comportamento novo e para os valores-limite. Todos passam.
3. O teste foi provado sensível: rode `python3 ferramentas/mutar.py <arquivo> --comando "<seus testes>"` (ou quebre o código à mão) e nenhum defeito pode sobreviver sem explicação (ver `eng-testes`).
4. Entrada externa é validada. Nenhum segredo no código. Autorização conferida em toda rota que mexe em dado (em app local de usuário único: token opcional por variável de ambiente, ou registre "N/A" em `docs/decisoes.md`).
5. Requisito, decisão de arquitetura e suposições estão registrados em `docs/`.
6. Revisão estática feita: você leu o próprio diff com olhar crítico antes de encerrar.

## 4. Proibido
- Apagar, enfraquecer ou pular teste para fazê-lo passar.
- Declarar sucesso sem ter rodado.
- Colocar chave, senha ou token em código, log ou commit (use variável de ambiente e `.gitignore`).
- Confiar na saída de um LLM sem validar no código (formato, tamanho, valores aceitos).
- Executar código gerado por IA ou vindo de entrada do usuário fora de um ambiente isolado.
- Inventar número, endpoint ou comando. Se não verificou, diga que não verificou.

## 5. Relatório ao final de cada entrega (máximo 10 linhas)
Use `templates/relatorio-de-entrega.md`: o que mudou, como provou, o que ficou de fora, riscos que restam, suposições
assumidas. Saída longa de comando vai em `docs/evidencias.md`; o relatório só aponta para ela.
Para testar servidor ou processo que não termina: use um script que sobe, testa e encerra o processo
(nunca `&` solto no shell).

## 6. Como usar as skills
As skills em `.claude/skills/` são o seu método. Invoque a que se aplica **por conta própria**:
`eng-requisitos`, `eng-arquitetura`, `eng-testes`, `eng-qualidade`, `eng-seguranca`, `eng-auditoria`.
Modelos de documento ficam em `templates/`. Tudo o que você produzir como documentação vai em `docs/`.
IDs de requisito: `NEG-` (negócio), `RF-`, `RNF-`, `RN-` (regra de negócio).
