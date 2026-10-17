# Modelo: script / automação em Python

Para projetos pequenos: um script, um robô, uma automação. Copie para a raiz como `CLAUDE.md` e troque
o que está entre `[colchetes]`.

---

# [Nome do projeto]

[Uma frase: o que o script automatiza.]

## Comandos

- Criar ambiente: `python -m venv venv` e `source venv/bin/activate`
- Instalar: `pip install -r requirements.txt`
- Rodar: `python [main.py] [argumentos]`
- Testes: `pytest`
- Estilo: `ruff check .`

## Estrutura

- `[main.py]`: ponto de entrada, só junta as partes
- `[src/]`: a lógica, em funções pequenas com um trabalho cada
- `[tests/]`: testes
- `.env`: segredos (no `.gitignore`, nunca no código)

## Convenções

- Python [3.12]. Tipos nas funções públicas.
- Funções fazem uma coisa. Se passa de ~30 linhas, quebre.
- Tudo que fala com a internet (API, site) fica em um módulo só, para eu poder trocar por um teste falso.
- Mensagens de erro dizem o que aconteceu **e o que eu devo fazer**.

## Cuidado com automação

- Script que apaga, move ou envia coisa tem que ter modo `--simular` que só mostra o que faria.
- Antes de rodar de verdade pela primeira vez, mostre o resultado do `--simular` e espere eu confirmar.
- Operação que não dá para desfazer (apagar, enviar e-mail, publicar) nunca roda sem confirmação.
- Respeite limite de requisições e tempo de espera entre chamadas.

## Antes de dizer que terminou

1. Rode `pytest` e `ruff check .`; mostre o resultado.
2. Rode o script em modo `--simular` e cole a saída.
3. Diga o que não testou.

## O que não fazer

- Não coloque senha, token ou chave no código ou no commit.
- Não instale biblioteca sem me perguntar.
- Não deixe `print` de depuração no código final.
