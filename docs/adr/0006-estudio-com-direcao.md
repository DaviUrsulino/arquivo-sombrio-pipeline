# 0006 — Estúdio com direção: a frase escolhe a cena, e nada sai sem portão de qualidade

- **Status:** aceito (desligado na grade até o Davi aprovar os vídeos de teste: `ESTUDIO_DIRETOR=1`)
- **Data:** 2026-11-03

## Contexto

O Davi sentia que as "identidades" do @ursulino.ia eram moldes: todo vídeo tinha a mesma animação. Um estudo de
108 Reels de 17 perfis de referência (`referencias/estudos/2026-11-03/RELATORIO.md`) mostrou o porquê:

- No pipeline, o LLM só **preenchia texto** em um acervo fixo de telas (7 tipos no escritório, ordem fixa na vila,
  ícone + rótulo no pixel2), e o robô ficava parado.
- Nas referências, a identidade tem 3 camadas: **marca** fixa (mascote, legenda, pílula de título), **mundo**
  escolhido pelo tema do vídeo e **cena** escolhida pela frase, com o personagem **agindo** com um objeto concreto.
- O conteúdo era fraco porque a pauta vinha de um README ("use SOMENTE o README" obriga a descrever a ferramenta).
  As referências contam um **acontecimento**; o mesmo vídeo com 3 ganchos diferentes fez 32 mil, 122 mil e
  941 mil views.
- As skills abertas que chegam nesse nível (motion-video-director, video-director, claude-animated-shorts,
  lemo-opuscar) concordam: "o prompt é 10%, o harness é 90%". Qualidade vem de roteiro → storyboard →
  quadros → crítica → correção, não de um prompt melhor.

## Decisão

Novo pacote `src/estudio_instagram/diretor/`, ao lado do pipeline atual (padrão estrangulamento, ADR 0003):

| Módulo | Papel |
|---|---|
| `roteiro.py` | Roteiro por acontecimento com a fórmula medida (fato → "isso porque" → passos → "e olha isso" → "ou seja" → comenta) e **3 ganchos** por pauta |
| `direcao.py` | Diretor (LLM) escreve o storyboard frase a frase, só com o que existe no `catalogo.py`; o conserto garante gancho forte, 3 mundos, câmeras variadas e HUD crescente |
| `catalogo.py` | Fonte única do que o motor desenha (mundos, ações, objetos, câmeras, emoções, chapéus); o teste garante que Python e JS têm o mesmo catálogo |
| `assets/vendor/palco-motor.js` | Motor three.js: robô de vinil com rosto de tela (emoções, piscada, boca sincronizada com a voz), 11 mundos, 31 objetos, 15 ações, 8 planos de câmera, transições (chicote, voxel), HUD, legenda em chip, fechamento com caixa de comentário; modo experimento (várias IAs numa ilha) |
| `narracao.py` | Voz frase a frase com tempo por palavra; mixagem de efeitos sonoros CC0 nos eventos da timeline e trilha com ducking |
| `montar.py` | Monta a pasta HyperFrames; os tempos dos efeitos espelham as regras do motor |
| `portao.py` | QA do MP4 (duração, congelado, preto, volume, miolo vazio) + crítico com visão comparando com uma folha de referência; aprova com média ≥ 7 e nenhuma área < 5 |
| `fazer.py` | Ponta a ponta, com uma rodada automática de correção usando as notas do crítico |
| `experimento.py` | Formato "Experimento de IAs" REAL: 4 modelos de verdade jogam "A Ilha"; o log é a única fonte do roteiro |
| `ranking.py` | Formato ranking com prova: número real de instalações do skills.sh |

No pipeline, o vídeo de uma ferramenta usa o estúdio novo quando `ESTUDIO_DIRETOR=1`. A palavra do comentário
continua sendo a da pauta (o respondedor de Direct depende dela). Se o vídeo for reprovado no portão ou der erro,
o pipeline cai no caminho antigo: a grade nunca fura por causa do estúdio novo.

## Consequências

- Cada frase vira uma cena diferente, com mundo, objeto, ação e câmera; o "molde" deixa de existir no nível da cena.
- Custo: o render 3D por software leva ~7 min por vídeo de 30 s (o `--browser-gpu` do HyperFrames não cria
  contexto WebGL nos workers nesta máquina; o motor tolera página sem WebGL para não bloquear a verificação, e o
  portão detecta "miolo vazio" se o 3D não desenhar). Com a rodada de correção, até ~20 min por vídeo.
- O crítico depende do Gemini com visão; se ele estiver fora, o portão não aprova (fica do lado seguro).
- O formato experimento usa o `claude` CLI local para os jogadores Claude; no GitHub Actions só os modelos do
  Gemini estariam disponíveis.
- Os vídeos de teste ficam em `videos_teste/` (MP4 ignorados pelo git).
