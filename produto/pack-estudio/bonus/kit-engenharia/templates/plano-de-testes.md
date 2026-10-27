# Plano de testes — <módulo ou projeto>

**Data:** AAAA-MM-DD

## 1. Objetivo
O que estes testes garantem.

## 2. Escopo
**Dentro:** …
**Fora:** …

## 3. Estratégia e técnicas
- Nível(is): unidade | integração | sistema | aceitação
- Caixa-preta: partição de equivalência, valor-limite, tabela de decisão
- Caixa-branca: desvios cobertos (liste os `if`/`catch` relevantes)
- Dublês usados e por quê

## 4. Ferramentas e ambiente
Framework, versão, como executar, sistema operacional.

## 5. Critério de aprovação
O caso passa quando resultado obtido = esperado. O plano passa com 0 falhas.

## 6. Casos de teste
| ID | Requisito | Entrada | Esperado | Obtido | Observação (técnica) | Status |
|---|---|---|---|---|---|---|
| CT-01 | RF-01 | | | | valor-limite | |

## 7. Execução e resultados
Saída real da execução (cole o resumo: N testes, 0 falhas).

## 8. Análise crítica — injeção de defeitos
| Defeito injetado | Onde | Teste que falhou | Interpretação |
|---|---|---|---|
| `>=` trocado por `>` | | CT-0X | O valor-limite pegou o erro |
Conclusão: a suíte é sensível a erros de lógica? O que ainda não está coberto?
