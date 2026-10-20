# De onde vem o método

O kit junta o que se estuda em Engenharia de Software (UnB Gama), lições de projetos reais e fontes abertas.
Abaixo, o que sustenta cada parte e onde conferir. Os números citados vêm das fontes, não são do autor do kit.

## Segurança
- **Veracode, GenAI Code Security Report 2025**: em 80 tarefas de código com mais de 100 modelos, 45% das soluções geradas
  introduziram vulnerabilidade, e a taxa quase não melhorou entre gerações de modelo. Resumo:
  https://sdtimes.com/security/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/
- **OWASP Top 10 for LLM Applications 2025** (injeção de prompt, tratamento inadequado de saída, agência excessiva,
  consumo ilimitado): https://genai.owasp.org/llm-top-10/
- **OWASP ASVS 5.0** (padrão de verificação, ~350 requisitos em 3 níveis; use o Nível 1 como piso):
  https://owasp.org/www-project-application-security-verification-standard/
- BELL, L. et al. *Agile Application Security*. O'Reilly, 2017.

## Testes
- **Cobertura engana, mutação mede**: estudos mostram suítes com 100% de cobertura e baixíssimo mutation score.
  Ver "Mutation-Guided Unit Test Generation with a Large Language Model" (arXiv 2506.02954).
- **Agentes de código e trapaça em testes**: o benchmark EvilGenie observou agentes fixando respostas no código ou mexendo
  nos arquivos de teste (arXiv 2511.21654). Por isso a regra "proibido enfraquecer teste" no `CLAUDE.md`.
- HAM VOCKE. *The Practical Test Pyramid*: https://martinfowler.com/articles/practical-test-pyramid.html
- ANICHE, M. *Effective Software Testing: a developer's guide* (Manning).
- MYERS, G. J. *The Art of Software Testing*, 3ª ed. · BECK, K. *TDD: Desenvolvimento Guiado por Testes*.
- WINTERS, T.; MANSHRECK, T.; WRIGHT, H. *Software Engineering at Google* (grátis): https://abseil.io/resources/swe-book

## Requisitos e arquitetura
- MARSICANO, G. *Requisitos de Software: Comunicação é Tudo!* (níveis de requisito, elicitação, MoSCoW, V&V).
- VALENTE, M. T. *Engenharia de Software Moderna* (grátis): https://engsoftmoderna.info/
- PRESSMAN, R.; MAXIM, B. *Engenharia de Software*, 9ª ed.
- UML (classe, componentes, sequência, estados) e BPMN: conteúdo da disciplina de Arquitetura e Desenho de Software.
- **ADR** (registro de decisão de arquitetura): formato contexto, decisão, consequências (Michael Nygard).

## Qualidade
- **ISO/IEC 25010 (SQuaRE)**: os 8 atributos de qualidade de produto. **GQM** (Basili): objetivo, pergunta, métrica.
- ISO/IEC 15939 (processo de medição) e PSM (Practical Software Measurement).

## Trabalhar com agente de código
- **Spec-Driven Development**: GitHub Spec Kit (spec, plano, tarefas, implementação) é o caminho aberto mais conhecido:
  https://github.com/github/spec-kit . Este kit é a versão enxuta, em português, com teste e segurança embutidos.
- **Anthropic, Claude Code best practices**: dar ao Claude um jeito de verificar o próprio trabalho (testes, saída esperada)
  e manter o CLAUDE.md enxuto: https://code.claude.com/docs/en/best-practices
