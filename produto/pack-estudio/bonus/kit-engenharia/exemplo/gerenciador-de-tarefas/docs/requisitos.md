# Requisitos — Gerenciador de tarefas

## 1. Problema
- **Quem:** uma pessoa que organiza o próprio dia [SUPOSIÇÃO].
- **Dor:** tarefas espalhadas em memória/mensagens; quer lista única acessível por script/outros programas via HTTP.
- **Hoje:** de cabeça ou bloco de notas [SUPOSIÇÃO].

## 2. Negócio
- NEG-01: ter uma lista de tarefas confiável e consultável por programa.

## 3. Usuário
- RU-01: criar, ver, marcar como concluída, editar título e apagar tarefas.

## 4. Produto
| ID | Tipo | Descrição | Prio | Critério (Dado/Quando/Então) |
|---|---|---|---|---|
| RF-01 | RF | Criar tarefa (POST /tarefas) | M | Dado título "Comprar pão" quando POST então 201 com id, concluida=false. Título de 200 chars aceito; 201 chars, vazio, só espaços ou não-string -> 400 |
| RF-02 | RF | Listar (GET /tarefas), filtro opcional `?concluida=true|false` | M | Dado 2 tarefas (1 concluída) quando GET ?concluida=true então só 1. Valor inválido -> 400 |
| RF-03 | RF | Obter por id (GET /tarefas/{id}) | M | Id existente -> 200; inexistente -> 404; id não numérico -> 404 |
| RF-04 | RF | Atualizar parcialmente (PATCH): titulo e/ou concluida | M | Dado tarefa quando PATCH {"concluida":true} então 200 e persistido; corpo vazio ou campo desconhecido -> 400; inexistente -> 404 |
| RF-05 | RF | Apagar (DELETE) | M | Existente -> 204 e depois 404; inexistente -> 404 |
| RF-06 | RF | Falha sem vazar interno | S | Erro inesperado -> 500 com mensagem genérica |
| RNF-01 | RNF | Segurança: token opcional; toda rota exige se definido | M | Com token definido: sem header/errado -> 401; certo -> 200 |
| RNF-02 | RNF | Entrada: JSON objeto, Content-Length obrigatório e <= 4096 | M | 4097 bytes -> 413; JSON inválido ou não-objeto -> 400 |
| RNF-03 | RNF | Zero dependências externas (Python 3.12) | M | Só imports stdlib |
| RNF-04 | RNF | SQL parametrizado | M | Título `'; DROP TABLE tarefas;--` armazenado literalmente |
| RN-01 | RN | Título é aparado (strip) e nunca vazio | M | " a " vira "a" |
| RN-02 | RN | `concluida` só aceita booleano real (não "true", não 1) | M | PATCH {"concluida":"sim"} -> 400 |

## 5. Won't (agora)
Multiusuário/login, prazo, prioridade, tags, paginação, HTTPS, UI web.

## 6. Suposições
Ver docs/decisoes.md.

## 7. Verificação
Revisado: atômicos, testáveis, com número onde havia adjetivo.

## 8. Validação
Entendi que você quer uma lista de tarefas pessoal acessível por HTTP; entrego CRUD + filtro por concluída,
SQLite local, token opcional; deixei de fora multiusuário, prazo, paginação e interface web.
