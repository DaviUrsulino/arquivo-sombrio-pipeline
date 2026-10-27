# Modelo: projeto de dados / IA

Para análise de dados, notebooks, treino ou uso de modelos. Copie para a raiz como `CLAUDE.md` e troque
o que está entre `[colchetes]`.

---

# [Nome do projeto]

[Uma frase: qual pergunta os dados respondem ou qual tarefa o modelo faz.]

## Comandos

- Ambiente: `[python -m venv venv]` / `[conda env create -f environment.yml]`
- Instalar: `[pip install -r requirements.txt]`
- Rodar o pipeline: `[python -m src.pipeline]`
- Testes: `[pytest]`

## Estrutura

- `[data/raw/]`: dados originais. **Somente leitura, nunca altere.**
- `[data/processed/]`: dados tratados (gerados pelo código)
- `[notebooks/]`: exploração. O que vira rotina vai para `[src/]`
- `[src/]`: código reutilizável
- `[reports/]`: gráficos e resultados

## Regras de ouro

- Nunca altere `data/raw/`. Todo tratamento é código que lê o bruto e escreve em `processed/`.
- Todo resultado tem que ser reproduzível: fixe a semente aleatória (`seed = [42]`) e registre versões.
- Separe treino e teste **antes** de qualquer tratamento que aprenda com os dados (evita vazamento).
- Não invente número. Se uma estatística aparece no texto, ela vem de uma célula ou script que eu consigo rodar.
- Diga o tamanho da amostra e o que não dá para concluir.

## Dados sensíveis

- Dado pessoal (nome, CPF, e-mail, telefone) não vai para o repositório nem para prompt de modelo externo.
- Anonimize antes de compartilhar qualquer amostra.
- Arquivos grandes ou privados ficam no `.gitignore`.

## Antes de dizer que terminou

1. Rode o pipeline do zero (sem cache) e confirme que o resultado é o mesmo.
2. Mostre as métricas com o tamanho da amostra.
3. Liste o que o resultado **não** permite concluir.

## O que não fazer

- Não comite dados brutos nem credenciais de banco.
- Não "ajuste" o conjunto de teste para melhorar a métrica.
- Não instale pacote pesado sem me perguntar.
