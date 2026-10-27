# Decisões e suposições

| Data | Tipo | O que | Por quê |
|---|---|---|---|
| 2026-10-20 | SUPOSIÇÃO | Usuário único, uso local; API escuta só em 127.0.0.1 | Pedido não cita multiusuário |
| 2026-10-20 | SUPOSIÇÃO | Tarefa = título (1..200) + concluída (bool) + criada_em; sem prazo/prioridade/tags | Menor modelo que resolve a dor |
| 2026-10-20 | DECISÃO | Token opcional via env `TAREFAS_TOKEN` (Bearer); se definido, toda rota exige | Autorização conferida em toda rota (CLAUDE.md 3.4) sem exigir login num app local |
| 2026-10-20 | DECISÃO | Persistência em SQLite (stdlib), arquivo via env `TAREFAS_DB` (padrão `tarefas.db`) | Sem dependência; ver ADR-0001 |
| 2026-10-20 | DECISÃO | Só stdlib `http.server` | Restrição do pedido; ver ADR-0002 |
| 2026-10-20 | SUPOSIÇÃO | Corpo máx. 4096 bytes; lista sem paginação | Uso pessoal, volume baixo |
| 2026-10-20 | DÍVIDA | `http.server` não tem limite de requisições, TLS nem timeout de leitura robusto | Aceitável em 127.0.0.1; trocar se expor na rede |
| 2026-10-20 | DÍVIDA | `pip-audit` N/A (zero dependências) | Só stdlib |

| 2026-10-20 | DECISÃO | Teste de imutabilidade da Tarefa | `ferramentas/mutar.py` mostrou que trocar `frozen=True` por `False` não quebrava nenhum teste |
