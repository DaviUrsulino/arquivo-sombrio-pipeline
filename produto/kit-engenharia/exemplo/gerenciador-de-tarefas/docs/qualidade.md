# Qualidade

Atributos (SQuaRE): adequação funcional (é o que o pedido exige), segurança (aceita entrada externa), manutenibilidade (camadas trocáveis).

| Goal | Question | Metric | Meta | Medido |
|---|---|---|---|---|
| Funcional correto | Quantos critérios RF/RNF têm teste verde? | % de IDs de requisito com teste | 100% dos Must | 100% (RF-01..05, RNF-01,02,04, RN-01,02); RF-06 coberto |
| Teste sensível | Defeitos injetados que a suíte pega? | pegos/injetados | 100% | 13/13 (1 sobrevivente inicial virou teste) |
| Segurança | Itens aplicáveis do checklist atendidos? | itens ok/aplicáveis | 100% | ver relatório |
| Manutenibilidade | Domínio isolado de HTTP/SQL? | imports proibidos em dominio.py | 0 | 0 |

Revisão estática: sem código morto relevante, sem debug, erros não vazam internos (testado).
Dívida aceita: ver docs/decisoes.md (http.server sem TLS/rate limit; cobertura de linha não medida, pois `coverage` não é stdlib).

## Injeção de defeitos com `ferramentas/mutar.py` (2026-10-20)
| Arquivo | Placar | Sobreviventes e decisão |
|---|---|---|
| `src/dominio.py` | 4/4 (após teste de imutabilidade) | `frozen=True`→`False` sobrevivia: faltava teste, escrito. |
| `src/repositorio.py` | 4/4 | — |
| `src/api.py` | 10/12 | `ensure_ascii=False`→`True` (linha 31): equivalente, o JSON decodificado é o mesmo. `token=… or None`→`and` (linha 129, em `main()`): ponto de entrada de configuração, não coberto por teste; dívida aceita. |
