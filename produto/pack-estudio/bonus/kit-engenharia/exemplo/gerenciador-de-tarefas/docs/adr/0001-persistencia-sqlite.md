# 0001 — Persistência em SQLite

- **Status:** aceito
- **Data:** 2026-10-20

## Contexto
Precisa persistir entre execuções, sem instalar nada. Alternativas: lista em memória (perde dados), arquivo JSON (corrida de escrita, reescrita total), SQLite (stdlib).

## Decisão
SQLite via `sqlite3`, atrás da interface `RepositorioTarefas`; `:memory:` nos testes; SQL sempre parametrizado.
Uma conexão por repositório com `check_same_thread=False` protegida por `threading.Lock` (servidor com threads).

## Consequências
+ Atômico, sem dependência, testável com banco real em memória.
- Uma conexão serializada limita concorrência (irrelevante para uso pessoal). Trocar de banco = nova implementação da interface.
