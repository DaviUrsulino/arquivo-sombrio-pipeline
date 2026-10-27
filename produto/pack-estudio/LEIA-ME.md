# Pack Estúdio — 8 identidades de Reels feitas com código

Os mesmos vídeos que saem no perfil, gerados a partir de um roteiro em JSON e da sua narração.
Uma frase vira uma cena, a legenda sai sincronizada palavra por palavra e você escolhe entre 8 estilos.

## Os 8 estilos

| `--estilo` | Visual |
|---|---|
| `3d` | Cenas 3D cinematográficas: monitor com onda de voz, túnel de estrelas, blocos de luz no espaço, câmera sempre em movimento |
| `rabisco` | Papel, traço tremido de desenho à mão, cards colados com quique |
| `pixelui` | Fonte pixel, janelas retrô com sombra dura, diagrama hub, carimbos, Robô Estagiário reagindo |
| `tier` | Ranking S/A/B no escuro + cenas creme com o print real do repositório circulado à mão |
| `telao` | Sala escura, dois monitores com tipografia cinética em cor chapada e luz vazando |
| `papel` | Papel creme, tipografia 3D extrudada voando, anéis com régua, letras recortadas |
| `vidro` | Preto com cards de interface em vidro, chips, linha do tempo e itálico serifado |
| `voxel` | Letreiro de lâmpadas com neon, fita crepe, monitor retrô e o Robô Estagiário em 3D |

## Instalar (uma vez)

Precisa de **Python 3.9+**, **Node 22+** e **ffmpeg**. Nada de pip install: só a biblioteca padrão.

## Fazer um vídeo

```bash
# 1. ver o exemplo pronto em todos os estilos (sem áudio, tempos estimados)
python3 montar.py exemplos/exemplo-ferramenta.json --todos

# 2. abrir um deles no navegador
cd saida/exemplo-ferramenta-papel && npx hyperframes preview

# 3. o seu vídeo: roteiro + narração gravada -> MP4
python3 montar.py meu-roteiro.json --audio narracao.mp3 --estilo 3d --renderizar
```

- O roteiro você escreve com o prompt de `prompts/gerar-roteiro-com-claude.md`.
- A narração pode ser gravada no celular ou gerada por voz de IA. O `montar.py` acha sozinho onde cada frase
  começa no áudio e sincroniza cena e legenda.
- O MP4 sai em 1080x1920, pronto para Reels, TikTok e Shorts.
- Quer música? Coloque por cima no editor que você já usa (CapCut, por exemplo); o pack não traz trilha.

## Bônus incluídos

- `bonus/kit-claude-code/`: 5 modelos de CLAUDE.md, 20 prompts, checklists e guia de comandos.
- `bonus/kit-engenharia/`: skills de requisitos, arquitetura, testes e segurança para o Claude Code, com projeto de exemplo testado.

## Mudar cores, fontes ou o mascote

Cada estilo é um arquivo em `modelo/estudio-<estilo>.html.tpl`: as cores ficam no topo do `<style>` e no
objeto `TEMA`. Peça ao Claude Code: "muda a cor de destaque do estilo papel para verde" e ele edita.
O robô fica em `modelo/assets/robo/` (11 reações em SVG).
