# 0002 — http.server da stdlib, monólito em 3 camadas

- **Status:** aceito
- **Data:** 2026-10-20

## Contexto
Restrição: só biblioteca padrão. Precisa de regra de negócio testável sem rede.

## Decisão
Monólito modular: `dominio` (Tarefa, validação, ServicoTarefas) <- `repositorio` (SQLite) e `api` (HTTP). O domínio não importa HTTP nem sqlite. A API só traduz HTTP <-> serviço; `ThreadingHTTPServer` ligado a 127.0.0.1.

## Consequências
+ Regra de negócio testada em unidade; API testada de ponta a ponta em porta efêmera.
- `http.server` é rudimentar (sem TLS, rate limit, timeouts finos): não expor na rede (dívida registrada).
