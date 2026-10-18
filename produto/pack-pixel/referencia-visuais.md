# Referência dos visuais

Cada cena do roteiro tem `narracao` (uma frase), `humor` (opcional) e **um** `visual`. Use um visual diferente
do anterior para o vídeo ter ritmo. Cores: `laranja`, `azul`, `verde`, `roxo`, `vermelho`, `amarelo`, `branco`, `rosa`.
Ícones: os nomes dos arquivos da pasta `modelo/icons` (sem `.svg`).

`humor` (reação do robô): `normal`, `feliz`, `animado`, `pensando`.

Estrutura do roteiro:

```json
{
  "titulo": "nome interno",
  "destaques": ["palavras", "da narração", "que ficam amarelas na legenda"],
  "cenas": [
    {"humor": "feliz", "narracao": "Uma frase falada.", "visual": {"tipo": "icone_pixel", "icone": "check", "cor": "verde", "rotulo": "TEXTO"}}
  ]
}
```

## Os 9 visuais

**`titulo_pixel`**: título grande, letra por letra. Ótimo para a cena 1 e a última.
```json
{"tipo": "titulo_pixel", "linhas": [{"texto": "A IA CRIA", "cor": "branco", "tamanho": 120}, {"texto": "VÍDEO", "cor": "laranja", "tamanho": 150}]}
```
2 a 3 linhas, MAIÚSCULAS, até 14 letras por linha, tamanho entre 100 e 170.

**`icone_pixel`**: um ícone grande em pixel art com um rótulo embaixo.
```json
{"tipo": "icone_pixel", "icone": "check", "cor": "verde", "rotulo": "SAI IGUAL TODA VEZ"}
```
Rótulo de até 22 letras, MAIÚSCULAS.

**`cadeia`**: 2 ou 3 caixas ligadas por setas pontilhadas (A, B, C).
```json
{"tipo": "cadeia", "layout": "horizontal", "nos": [{"icone": "code-xml", "rotulo": "HTML", "cor": "azul"}, {"icone": "zap", "rotulo": "Motor", "cor": "amarelo"}, {"icone": "clapperboard", "rotulo": "Vídeo", "cor": "verde"}]}
```
`layout`: `horizontal` ou `vertical`. Rótulo de até 14 letras.

**`comparar`**: dois cartões lado a lado, com barras de 0 a 8.
```json
{"tipo": "comparar", "esq": {"titulo": "RÁPIDO", "icone": "zap", "cor": "amarelo", "linhas": [{"rotulo": "velocidade", "valor": 8}]}, "dir": {"titulo": "AVANÇADO", "icone": "brain", "cor": "roxo", "linhas": [{"rotulo": "controle", "valor": 8}]}}
```

**`niveis`**: 2 ou 3 colunas que crescem, com estrelas.
```json
{"tipo": "niveis", "itens": [{"rotulo": "BÁSICO", "altura": 1, "cor": "verde"}, {"rotulo": "MÉDIO", "altura": 2, "cor": "azul"}, {"rotulo": "AVANÇADO", "altura": 3, "cor": "amarelo"}]}
```
`altura`: 1 a 3.

**`lista`**: itens que entram um a um, com marca de feito.
```json
{"tipo": "lista", "itens": ["Claude Code", "Codex", "Cursor"]}
```
2 a 4 itens, até 22 letras.

**`terminal`**: janela de terminal com o comando sendo digitado e um texto explicando.
```json
{"tipo": "terminal", "rotulo": "terminal", "comando": "git init", "texto": "cria o repositório na pasta atual"}
```
O `texto` é opcional. Comandos longos quebram de linha sozinhos.

**`contador`**: um número grande que sobe até o valor.
```json
{"tipo": "contador", "valor": 65000, "rotulo": "ESTRELAS NO GITHUB"}
```
`formato` (opcional): sem ele, números grandes viram "65 mil"; `"formato": "ano"` mostra o número puro (2005);
`"formato": "cheio"` mostra com separador de milhar (1.250.000).

**`banner_repo`**: faixa no topo com um endereço.
```json
{"tipo": "banner_repo", "rotulo": "repositório gratuito", "url": "github.com/dono/repo"}
```

## Âncoras (avançado)

Por padrão, o script escolhe sozinho quais palavras da narração disparam cada elemento. Para escolher você mesmo,
acrescente `"ancora": "palavra"` (visual único) ou `"ancoras": ["palavra1", "palavra2"]` (cadeia, lista, niveis,
comparar, terminal). A palavra tem que aparecer na narração da cena.
