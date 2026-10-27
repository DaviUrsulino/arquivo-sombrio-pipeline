# Prompt: o Claude escreve o roteiro por você

Copie o bloco abaixo, troque o que está entre `[colchetes]` e cole no Claude (ou no Claude Code, nesta pasta).
Ele devolve um JSON pronto para o `montar.py`. No Claude Code, acrescente no fim: "Salve em `meu-roteiro.json`."

```
Escreva o roteiro de um Reels de 30 a 50 segundos sobre: [ASSUNTO].
Público: [QUEM VAI ASSISTIR]. Tom: direto e curioso, como quem conta uma descoberta para um amigo.

REGRAS DE FATO:
- Use SOMENTE o material que eu colar abaixo. Nada de número, comparação ou capacidade que não esteja nele.
- Comando de instalação ou de uso: copie exatamente do material.
- Não prometa resultado nem faça afirmação que eu não consiga conferir.

MATERIAL (README, página ou anotações):
"""
[COLE AQUI]
"""

GANCHO (cena 1, o mais importante): resultado concreto + curiosidade, entendível por quem nem programa.
Exemplos que funcionam: "Acabou pro [ferramenta paga famosa]?", "O repositório que está bombando no GitHub
faz [resultado]", "Fizeram [coisa famosa] com IA". Nunca comece com "Conheça" nem com o nome do projeto.

NARRAÇÃO (lida em voz alta): português do Brasil, frases de 8 a 14 palavras, uma ideia por frase, sem emoji,
siglas e comandos do jeito que se fala, números pequenos por extenso.

ESTRUTURA: 6 a 8 cenas. Cada cena = UMA frase + UM visual, diferente do visual da cena anterior.
Cena 1: titulo_pixel (o gancho, 2 linhas curtas em MAIÚSCULAS que repetem palavras ditas).
Meio: mostre o que faz (cadeia), o que vem junto (lista), a prova (contador), como usar (terminal),
o detalhe que surpreende (icone_pixel).
Última cena: titulo_pixel com as linhas "COMENTA" e a PALAVRA que a pessoa comenta; a narração pede
para comentar essa palavra.

VISUAIS (campo "visual"):
- titulo_pixel: {"tipo":"titulo_pixel","linhas":[{"texto":"A IA CRIA","cor":"branco"},{"texto":"VÍDEO","cor":"laranja"}]}
- contador: {"tipo":"contador"}  (usa as estrelas do bloco "repo"; ou {"tipo":"contador","valor":12000})
- cadeia: {"tipo":"cadeia","nos":[{"icone":"message-circle","rotulo":"VOZ","cor":"azul"},{"icone":"brain","rotulo":"MODELO","cor":"amarelo"}]}  (2 ou 3 nós)
- lista: {"tipo":"lista","itens":["Memória local","Busca web","MCP tools"]}  (2 a 4 itens curtos)
- terminal: {"tipo":"terminal","comando":"npx exemplo init","texto":"o que esse comando faz"}
- icone_pixel: {"tipo":"icone_pixel","icone":"check","cor":"verde","rotulo":"RODA OFFLINE"}
Cores: laranja, azul, verde, roxo, vermelho, amarelo, branco, rosa.
Ícones: só nomes da pasta modelo/assets/icons (check, zap, bot, terminal, sparkles, brain, bug, shield-check,
rocket, clock, star, github, code-xml, clapperboard, flame, search, message-circle, users, palette...).

SAÍDA: um único JSON, sem texto fora dele:
{"repo": {"nome": "dono/repositorio", "estrelas": 0, "descricao": "..."},
 "destaques": ["até 8 palavras da narração que ganham destaque na legenda"],
 "cenas": [{"humor": "feliz", "narracao": "...", "visual": {...}}]}
"humor" (reação do robô nos estilos com mascote): normal, feliz, animado ou pensando.
Se não for sobre um repositório, apague o bloco "repo" e use "valor" no contador.
```

## Depois

1. Confira com os olhos: cada fato está no material que você colou?
2. Grave a narração lendo as frases na ordem (celular serve), ou gere com uma voz de IA.
3. `python3 montar.py meu-roteiro.json --audio narracao.mp3 --todos --renderizar` gera os 8 estilos e você escolhe.
