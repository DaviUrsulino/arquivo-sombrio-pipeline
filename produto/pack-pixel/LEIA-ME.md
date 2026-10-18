# Pack Pixel: Reels em pixel art com Hyperframes

Um template de vídeo vertical (1080x1920) em pixel art: cenário de biblioteca com tochas, um robô que anda
e reage, **uma cena visual por frase** e legenda em caixa com palavras em destaque. Você escreve o roteiro
em JSON (ou pede para o Claude Code escrever), e o `montar.py` gera o projeto e o MP4.

Do perfil [@robo.estagiario](https://www.instagram.com/robo.estagiario/). Versão 1.0.

## O que você recebe

| Arquivo/pasta | Para quê |
|---|---|
| `montar.py` | Script que transforma o roteiro em projeto Hyperframes (e em MP4, se quiser) |
| `modelo/` | O template visual (HTML), a fonte e 31 ícones |
| `exemplos/exemplo-todos-os-visuais.json` | Roteiro de 10 cenas que usa **todos os 9 tipos de visual**. Copie e troque os textos |
| `exemplos/exemplo-dica.json` | Roteiro curto de 4 cenas, o mais simples possível |
| `referencia-visuais.md` | Cada visual, com o JSON de exemplo e os limites de texto |
| `prompts/gerar-roteiro-com-claude.md` | Prompt pronto para o Claude escrever o roteiro de qualquer assunto |
| `LICENCAS.md` | O que é de quem (fonte, ícones, bibliotecas) |

## O que precisa estar instalado

- **Python 3.9 ou mais novo** (só usa a biblioteca padrão)
- **Node 22 ou mais novo** (o Hyperframes roda nele)
- **ffmpeg** (lê o áudio e gera o vídeo)

## Primeiro vídeo em 5 minutos (sem áudio)

```bash
python3 montar.py exemplos/exemplo-dica.json --renderizar
```

Na primeira vez ele baixa o GSAP (biblioteca de animação) do npm e o Hyperframes pelo `npx`. O vídeo sai em
`saida/exemplo-dica.mp4`. Sem áudio, o vídeo sai **mudo**, com tempos estimados pelo tamanho do texto.

## Com a sua narração (recomendado)

1. Escreva o roteiro (`meu-roteiro.json`): cada cena tem uma `narracao` (uma frase) e um `visual`.
2. Grave **uma narração só**, lendo as frases na ordem, em qualquer voz: a sua, ou de qualquer serviço de voz
   que você use. Formato: mp3, wav ou m4a.
3. Rode:

```bash
python3 montar.py meu-roteiro.json --audio minha-narracao.mp3 --renderizar
```

O script descobre sozinho onde cada frase começa (olhando as pausas do áudio) e sincroniza legenda e visuais.
Dica: faça uma **pausa curta entre as frases** quando gravar; é nela que ele corta as cenas.

## Com o Claude Code

Abra o Claude Code nesta pasta e use o prompt de `prompts/gerar-roteiro-com-claude.md`. Ele escreve o JSON,
você grava a narração e roda o `montar.py`.

## O vídeo ficou estranho?

| Sintoma | O que fazer |
|---|---|
| "Arrume isto no roteiro: ..." | O script diz o que está errado (ícone que não existe, cor inválida, etc.) |
| Cena troca na hora errada | Grave com uma pausa mais clara entre as frases, ou divida a frase em duas cenas |
| Texto cortado na tela | Veja os limites de letras em `referencia-visuais.md` |
| `npx` ou `ffmpeg` não encontrado | Instale Node 22+ e ffmpeg e abra um terminal novo |
| Quero só ver, sem renderizar | `cd saida/<nome> && npx hyperframes preview` |

## Limites e avisos

- É um template, não um curso e não tem suporte individual.
- O Hyperframes é de terceiros (licença Apache 2.0) e muda com o tempo: o script fixa a versão `0.8.154`.
- Os tempos calculados do áudio são uma estimativa (erram uns décimos de segundo dentro de uma frase).
- Este pack não tem vínculo com a HeyGen nem com a Anthropic.
