# Arquitetura

## Classes
```mermaid
classDiagram
    class Tarefa { +int id; +str titulo; +bool concluida; +str criada_em }
    class ServicoTarefas { +criar(titulo) +listar(concluida) +obter(id) +atualizar(id, campos) +apagar(id) }
    class RepositorioTarefas { <<interface>> +adicionar() +listar() +obter() +salvar() +remover() }
    class RepositorioSqlite
    class ErroDominio { <<exception>> }
    class ErroValidacao
    class ErroNaoEncontrado
    ServicoTarefas --> RepositorioTarefas : associação 1..1 (injetado)
    RepositorioSqlite ..|> RepositorioTarefas : realização
    RepositorioTarefas ..> Tarefa : dependência
    ServicoTarefas ..> Tarefa : dependência
    ErroValidacao --|> ErroDominio : generalização
    ErroNaoEncontrado --|> ErroDominio : generalização
```
Sem agregação/composição: Tarefa é entidade única, sem partes.

## Componentes
```mermaid
flowchart LR
    Cliente -- HTTP/JSON --> API[api.py]
    API -- chamada Python --> Servico[dominio.py]
    Servico -- interface --> Repo[repositorio.py]
    Repo -- SQL --> DB[(SQLite)]
```

## Sequência: PATCH /tarefas/3
```mermaid
sequenceDiagram
    Cliente->>API: PATCH /tarefas/3 {"concluida":true}
    API->>API: confere token, tamanho, JSON
    API->>Servico: atualizar(3, campos)
    Servico->>Servico: valida campos
    Servico->>Repo: obter(3) / salvar(t)
    Repo->>DB: SELECT / UPDATE (parametrizado)
    API-->>Cliente: 200 JSON | 400 | 401 | 404
```
Estados e BPMN: N/A (tarefa só alterna concluída/pendente; não é processo de negócio).
