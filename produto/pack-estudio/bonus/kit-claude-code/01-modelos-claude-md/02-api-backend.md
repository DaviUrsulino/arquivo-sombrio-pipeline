# Modelo: API / back-end

Copie para a raiz do projeto como `CLAUDE.md`. Troque o que está entre `[colchetes]`. Mantenha abaixo
de 200 linhas.

---

# [Nome da API]

[Uma frase: o que a API faz e quem consome.]

## Comandos

- Instalar: `[pip install -r requirements.txt]` ou `[npm install]`
- Rodar local: `[uvicorn app.main:app --reload]` ou `[npm run dev]`
- Testes: `[pytest]` ou `[npm test]`; um teste só: `[pytest tests/test_x.py -k nome]`
- Migrações: `[alembic upgrade head]` / criar nova: `[alembic revision --autogenerate -m "..."]`
- Lint e tipos: `[ruff check .]` e `[mypy .]`

## Estrutura

- `[app/routes/]`: endpoints (finos: só validam e chamam o serviço)
- `[app/services/]`: regra de negócio
- `[app/models/]`: tabelas e schemas
- `[tests/]`: testes, espelhando a estrutura de `app/`

## Convenções

- Toda entrada externa é validada com [Pydantic / zod] antes de ser usada.
- Endpoints devolvem erro com código HTTP correto e corpo `{"erro": "mensagem"}`.
- Regra de negócio fica em `services/`, nunca dentro da rota.
- Nome de função e variável em [inglês], mensagens ao usuário em [português].

## Banco de dados

- Nunca edite uma migração que já foi aplicada; crie uma nova.
- Toda migração nova precisa funcionar também para reverter (`downgrade`).
- Consultas com dado do usuário usam parâmetros, nunca concatenação de texto (injeção de SQL).

## Segurança

- Autenticação em toda rota, exceto as listadas em `[app/routes/publicas.py]`.
- Segredos só em variável de ambiente; `.env` no `.gitignore`; nunca em log.
- Não registre senha, token ou dado pessoal em log.

## Antes de dizer que terminou

1. Rode `[pytest]` e mostre o resultado. Para mudança de comportamento, escreva o teste antes.
2. Rode `[ruff check .]`.
3. Diga o que mudou, o que quebra se alguém usar a API antiga, e o que ficou sem teste.

## O que não fazer

- Não mude o formato de resposta de um endpoint existente sem me avisar (quebra quem consome).
- Não apague teste para passar. Não use `try/except` vazio para esconder erro.
- Não adicione dependência nova sem me perguntar.
