# Prompt: o Claude escreve o roteiro por você

Copie o bloco abaixo, troque o que está entre `[colchetes]` e cole no Claude (ou no Claude Code, nesta pasta).
Ele devolve um JSON pronto para o `montar.py`. Para o Claude Code, acrescente no fim:
"Salve o resultado em `meu-roteiro.json`."

```
Escreva o roteiro de um Reels de 40 a 55 segundos sobre: [ASSUNTO].
Público: [QUEM VAI ASSISTIR]. Tom: informativo, direto e curioso, como quem conta uma descoberta para um amigo.

REGRAS DE FATO:
- Use SOMENTE o material que eu colar abaixo. Nada de número, comparação ou capacidade que não esteja nele.
- Se o material não diz, não diga. Comando de instalação ou de uso: copie exatamente do material.
- Não prometa resultado nem faça afirmação que eu não consiga conferir.

MATERIAL (cole aqui o README, a página ou as anotações):
"""
[COLE AQUI]
"""

NARRAÇÃO (é lida em voz alta):
- Português do Brasil, frases curtas de 8 a 14 palavras, uma ideia por frase, sem emoji nem hashtag.
- Escreva siglas e comandos do jeito que se fala, sem símbolos como / @ # *.
- Números pequenos por extenso ("vinte e uma").

ESTRUTURA: de 9 a 11 cenas. Cada cena = UMA frase falada + UM visual, diferente do visual da cena anterior.
A cena 1 é um gancho (visual titulo_pixel) com curiosidade honesta. A última é uma chamada para salvar, seguir
ou comentar uma palavra (visual titulo_pixel).

VISUAIS permitidos (campo "visual", com "tipo" e os campos de cada um):
titulo_pixel, icone_pixel, cadeia, comparar, niveis, lista, terminal, contador, banner_repo.
Cores: laranja, azul, verde, roxo, vermelho, amarelo, branco, rosa.
Ícones: use só nomes da pasta modelo/icons (por exemplo: check, zap, bot, terminal, sparkles, brain, bug,
shield-check, rocket, clock, star, github, code-xml, clapperboard, flame, search).
Os campos e os limites de texto de cada visual estão em referencia-visuais.md: leia esse arquivo antes.

SAÍDA: um único JSON, sem texto fora dele, neste formato:
{"titulo": "...", "destaques": ["até 8 palavras da narração que ficam amarelas"],
 "cenas": [{"humor": "feliz", "narracao": "...", "visual": {...}}]}
"humor" pode ser normal, feliz, animado ou pensando.
```

## Depois

1. Confira o roteiro com os olhos: o fato está no material que você colou?
2. Grave a narração lendo as frases na ordem, com uma pausa curta entre elas.
3. `python3 montar.py meu-roteiro.json --audio narracao.mp3 --renderizar`
