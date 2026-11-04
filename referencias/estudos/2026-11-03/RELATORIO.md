# Estudo de referências e plano de melhorias — @ursulino.ia

Data: 2026-11-03. Pedido do Davi: entender por que os vídeos do perfil parecem "template" e não "identidade",
estudar as referências salvas (visual e conteúdo), pesquisar skills e código aberto que levem ao nível dos
perfis de referência, e montar o plano do que vamos implementar.

---

## 1. Resumo em cinco frases

1. **O motor não é o problema.** O pipeline já renderiza com HyperFrames, o mesmo motor usado pelas melhores
   skills de motion do mercado. O que falta é a camada de **direção** entre o roteiro e o render.
2. **O visual vira template** porque o LLM só preenche texto em um acervo fixo de telas (7 tipos no escritório,
   ordem fixa na vila, ícone + rótulo no pixel2). Nas referências, **a frase escolhe a cena**: cada fala vira uma
   ação física de um personagem, com um objeto específico, dentro de um mundo escolhido pelo tema.
3. **O conteúdo é fraco** porque a fonte da pauta é um README do GitHub, e a regra "use SOMENTE o README" obriga o
   roteiro a descrever a ferramenta. As referências contam um **acontecimento** (alguém fez algo, um experimento,
   uma briga, um resultado), e a ferramenta entra como prova.
4. **O formato que mais rende nas referências e é 100% automatizável** é o "experimento de IAs" do
   @omagodoalgoritmo (58 mil views): colocar várias IAs reais num jogo e narrar o que aconteceu. O pipeline já
   tem vários provedores de LLM em cascata (`src/estudio_instagram/llm.py`), então dá para rodar o experimento de
   verdade (conteúdo real, não inventado).
5. **Qualidade não sai de prompt, sai de portão de qualidade**: storyboard aprovado, quadros parados por cena
   comparados lado a lado com a referência, um crítico com nota por área, e só então o render final.

---

## 2. O que foi estudado

| Item | Quantidade |
|---|---|
| Perfis de referência (de `referencias/referencias.json`) | 17 (1 indisponível: @ismjeff.ia) + 1 novo (@mizak_criativos) |
| Reels baixados do Instagram (yt-dlp, sem login) | 108 de 110 (2 falharam: timeout e exigência de login) |
| Folhas de 24 quadros geradas | 108 (em `folhas/`) |
| Folhas olhadas uma a uma | ~45 (todas as dos perfis de animação com mais views + os reels salvos) |
| Transcrições (faster-whisper large-v3-turbo, local) | 108 (em `transcricoes/`) |
| Repositórios de skills de vídeo lidos | 12 (lista na seção 5) |

Critério de escolha dos reels: 7 mais vistos de cada perfil de animação, 3 dos perfis de roteiro/notícia,
mais os 19 reels salvos pelo Davi. O estudo semanal antigo (`estudo_animacao.py`) usava Apify, que está sem
crédito (HTTP 402); este estudo foi feito pelo navegador + yt-dlp + Whisper local, sem custo.

---

## 3. Diagnóstico visual

### 3.1 Como as referências constroem "identidade"

Todas as boas referências têm **três camadas**, e só a primeira é fixa:

| Camada | O que é | Exemplo (@_aighostlab) |
|---|---|---|
| **Marca** (fixa) | Personagem, tipo de legenda, pílula de título, paleta-base | Mascote cubo laranja, legenda de 1 palavra em chip marrom, título em pílula branca |
| **Mundo** (muda por tema do vídeo) | Gênero/cenário que combina com o assunto | "Canal dark" = filme noir P&B com chapéu de detetive e persiana; "hackear a TV" = apartamento isométrico com relógio acelerado; "prever o futuro" = quarto com bola de cristal e telescópio |
| **Cena** (muda por frase) | Uma ação do personagem + um objeto concreto | "Anima cada palavra" = martelo batendo nas palavras; "corta os erros" = tesoura cortando rolo de filme; "sem editor" = funil + engrenagens cuspindo um Reel |

O @omagodoalgoritmo leva isso ao extremo: a marca é só a fonte pixel e o "Comenta EDITA"; o **mundo vem de um
jogo famoso** que combina com o experimento (mapa de guerra, ilha de sobrevivência, Among Us, battle royale).

### 3.2 O que nossos vídeos fazem hoje

Olhando as folhas dos nossos próprios reels salvos (`salvo__DertWseDbXz`, `salvo__De8OMwtBhLP`):

- Fundo de estante pixel **sempre igual**.
- Robozinho **parado** embaixo, do mesmo tamanho, em todos os quadros. Ele não age.
- Centro da tela sempre "ícone + rótulo" ou "título em 3 linhas".
- A legenda repete a narração.

É exatamente a sensação de template que o Davi descreveu.

### 3.3 Padrões visuais medidos nas referências

| Padrão | Onde aparece | Nosso estado |
|---|---|---|
| Corte ou mudança visual a cada 1–3 s | todos os perfis de animação | 4–5 s por cena (regra do roteirista) |
| Personagem **age** (pega objeto, reage, troca de chapéu, se assusta) | aighostlab, clubedasskills, motionia, macelista, mizak | robô parado |
| **Estado persistente na tela** (contador que sobe, barra de etapas, "ANO 3/10", "DIA 7/10", "JURADOS 2/3", "VÍDEOS x18") | aighostlab, omago, motionia, clube, macelista, mateus | ausente |
| Mundo escolhido pelo tema | aighostlab, omago, clube | mundo fixo por identidade |
| Fundo que troca de cor chapada nas frases abstratas | aighostlab, lowstack, jako, yan.gsouza | não |
| Transição com objeto (explode em voxels, wipe com personagem, borrão de movimento) | aighostlab, mizak | corte seco / fade |
| Prova real na tela (print de tweet, página do GitHub, número de estrelas/instalações) | gab.gouvea (941 mil), mateus, macelista, clube | só contador de estrelas |
| Legenda de 1 palavra em chip, sempre no mesmo lugar | aighostlab, clube, macelista, omago | legenda de frase |
| Fechamento com a caixa de comentário digitando a palavra + botão seguir | quase todos | texto "comenta" |

### 3.4 Destaques por perfil (melhor reel visto)

| Perfil | Views | Estilo | O que copiar (a gramática, nunca o conteúdo) |
|---|---|---|---|
| @omagodoalgoritmo `DfLZXoHjqzi` | 58,1 mil | mapa 3D low-poly + chat das IAs | Experimento com placar ("ANO x/10"), mensagens das IAs em balão, exércitos se movendo |
| @mateus.curta.ia `DfNu8hoCvDX` | 46,9 mil | preto/vermelho, raposa pixel no canto | Capítulos "01/07", número gigante por capítulo (+43%, +50%) |
| @motionia.br `DfAP6GNMZ8M` / `DfC4zT2MMQi` | 28,6 / 23,7 mil | 2D chapado, humano + mascote | Esquete em diálogo; metáfora (banca de jurados, carimbo REPROVADO) |
| @_aighostlab `DfM7ZaIJDUH` | não visível sem login (o vídeo diz "meio milhão de views em 1 semana" no perfil) | 3D brinquedo, palco | Três camadas (marca / mundo / cena), contador mecânico, máquina-metáfora |
| @jako.frames `De3j7xpoPJj` | 90 mil | chibi 3D + cards de UI | Número gigante ("1,000s"), progresso "01/11" |
| @macelista `DezJbfEqg7b` | 16,9 mil | voxel, ranking em pódio | Top 5 com "#5" gigante entre itens, cada item é um personagem com fantasia |
| @clubedasskills `DfM_KHMIXm4` | 12,3 mil | 3D low-poly, programa de auditório | Cada item do ranking tem cenário próprio (biblioteca, planta baixa, loja) |
| @lowstack.app `DfIQhqEza1L` | 18,3 mil | vetor 2D "Apple" | Um objeto-herói em todas as cenas (a air fryer), cenário muda por frase |
| @gab.gouvea `DfAy1NHseqU` | 941 mil | preto/dourado, ícones | História de um dev ("engenharia reversa na placa da Nvidia"), prova com prints reais |
| @yan.gsouza (salvo `Dep_9l2tzZH`) | — | rosa/preto ilustrado | Vilão e herói ("clonaram a ElevenLabs… um dev sozinho") |
| @pixosly | 8–11 milhões | pixel art emocional, sem voz | Loop de emoção identificável (fora do nicho, mas mostra o poder do "relatable") |
| @thiagomendesmed `DUJ6tr2EZmC` | 1,8 milhão | objetos falantes | Personificação com humor ("eu sou o pão do seu hospital") |

---

## 4. Diagnóstico de conteúdo (transcrições)

### 4.1 Nossos roteiros

Exemplos reais das últimas pautas (`pautas/auto-2026-11-0*.json`):

- "O Floorplan desenha um mapa interativo de todo o seu projeto."
- "O projeto oficial da DeepSeek automatiza tarefas direto no GitHub."
- "Agentes de inteligência artificial investigam cada evento de segurança."

Mesmo com o gancho bom, a partir da 2ª frase o vídeo vira **leitura do README**. Números do perfil
(`pautas/desempenho.json`, 35 Reels): mediana de **313 views**, **6,9 s** assistidos em média.
O único que estourou (54,7 mil) foi "Esse repositório faz a IA criar vídeo escrevendo HTML" — um tema de
**desejo do público** (fazer vídeo), não de nicho técnico.

Causas no código:
- `src/estudio_instagram/roteirista.py` manda usar **SOMENTE** o README e "descrever o que a ferramenta faz".
  Isso protege contra invenção (bom), mas impede história.
- `src/estudio_instagram/assunto_quente.py` escolhe pelo GitHub Trending / HN. O que bomba lá é técnico demais
  para o público amplo (já registrado: "às vezes pega repo técnico demais, nem o Davi entende").

### 4.2 Formatos que funcionam nas referências

| Formato | Exemplo e views | Estrutura |
|---|---|---|
| **Experimento de IAs** | omago: "Coloquei 7 IAs pra governar a América do Sul por 10 anos" (58,1 mil), ilha (9,9 mil), Among Us (6,5 mil), Brasil (6 mil) | Regras do jogo em 1 frase → rodadas com traição/aliança → reviravolta → placar final → "comenta" |
| **Acontecimento com pessoa** | aighostlab: "Estão hackeando a própria TV com o Claude Code…"; "Um cara montou um canal dark que fatura 250 mil"; gab.gouvea: placa da Nvidia (941 mil) | Fato chocante → "isso porque" → 2–3 passos → "e olha isso" (bônus) → "ou seja" (antes/depois) → comenta |
| **Benefício de vida real** | mateus: "Agora o Claude te ajuda a viajar gastando menos e pegando milhas" (46,9 mil) | Desejo comum (viajar, economizar, TV sem propaganda) → como → prova → comenta |
| **Esquete em diálogo** | motionia: Davi vs Claude, "Zero bugs" + banca de jurados (23,7 mil), "Você assistiu o vídeo inteiro?" (28,6 mil) | Abre no meio da briga → cada fala apresenta 1 ferramenta → punchline → comenta |
| **Ranking com prova** | macelista "5 skills mais instaladas" (16,9 mil), clube Top 5 (12,3 mil) | "#5 … #1" com métrica real (instalações) → cada item com 1 benefício |
| **Meta / resultado próprio** | aighostlab "Acabei de criar uma skill que me fez bater meio milhão de views" | Resultado → como → "esse vídeo foi feito com isso" → comenta |
| **Contrário / pergunta errada** | mizak: "Qual é o prompt? Pergunta errada." | Quebra a expectativa → revela o que importa (skill, não prompt) |

### 4.3 Fórmula de frase do @_aighostlab (repetida em todos os 7 vídeos)

> **[Fato chocante ou resultado]** → **"Isso porque"** [mecanismo] → [2–3 passos concretos] →
> **"E olha isso,"** [bônus que surpreende] → **"Ou seja,"** [antes e depois na vida de quem assiste] →
> **"Comenta X e me segue que eu te mando."**

Duração 20–30 s, 6 a 8 frases curtas. É praticamente o tamanho do nosso formato curto, mas com arco.

### 4.4 Ganchos que abrem os vídeos mais vistos

- "Coloquei / Larguei **N IAs** [num lugar] …" (omago, 4 vídeos)
- "O Claude **acabou de** [ganhar / matar / acabar com] …" (aighost, kaio, mateus)
- "Estão [fazendo algo inesperado] com o Claude Code …" (aighost)
- "Um cara / um dev sozinho [fez algo grande] …" (aighost, yan.gsouza, gab.gouvea)
- "[Coisa famosa] e quase ninguém usa ainda" (kaio)
- Diálogo no meio da cena: "Terminei. Zero bugs." (motionia)
- "Pergunta errada." (mizak)

Em comum: **ninguém abre com o nome da ferramenta**, e em quase todos o sujeito da frase é **uma pessoa ou uma IA
fazendo algo**, não "a ferramenta faz".

### 4.5 O mesmo vídeo com 3 ganchos: de 32 mil a 941 mil

O @gab.gouvea postou **o mesmo corpo de vídeo três vezes**, trocando só a primeira frase:

| Gancho | Views |
|---|---|
| "**Fizeram engenharia reversa** na placa da NVIDIA e acharam quase o dobro de potência escondida." | **941 mil** |
| "A NVIDIA travou metade da força da sua placa de vídeo. E alguém acabou de achar a chave." | 122 mil |
| "A sua placa de vídeo roda pela metade. De propósito. E agora dá pra destravar de graça." | 32,2 mil |

O gancho sozinho fez **29 vezes** de diferença. O vencedor tem alguém fazendo algo ousado ("fizeram engenharia
reversa") e um resultado concreto. O @exosmkt repete o padrão: "Um cara fez engenharia reversa no Opus Clip…"
(218 mil). Conclusão para o pipeline: gerar **3 ganchos por pauta** e testar (ver S5).

---

## 5. Ferramentas encontradas (skills e código aberto)

Lidas no código, não só pelo README. Nenhuma foi instalada ainda, exceto o find-skills.

### 5.1 Direção e qualidade (o "software bem construído")

| Repositório | O que traz de útil para nós |
|---|---|
| [MuhammadaliMS/motion-video-director](https://github.com/MuhammadaliMS/motion-video-director) | 20 regras de direção (um herói por plano, molas em vez de linear, "explique um processo agindo sobre um objeto", "mostre, não nomeie"), portões em 6 etapas, kit three.js de estúdio (`lib/studio3d.js`), biblioteca de 273 técnicas com sorteio para fugir do padrão |
| [win4r/video-director](https://github.com/win4r/video-director) | "O prompt é 10%, o harness é 90%". `timeline.json` como fonte única de tempo, `qa_video.py`, crítico de contexto limpo com lista de correções, "fix card" por problema |
| [mromidev/claude-animated-shorts](https://github.com/mromidev/claude-animated-shorts) | Método de **medir a referência em números** (luz, cor, câmera, contorno), folhas lado a lado, verificador com nota 0–10 por área até subir. Personagens 2D em mundo 3D com three.js |
| [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) ("bizarro", como o Davi disse) | **66 estilos de filme em código**, cada um com `STYLE.md` + filme-demo. Vários servem de "mundo": `game-show`, `pixel-rpg`, `brick-toy`, `lowpoly-island`, `isometric-picture-book`, `newsreel`, `spy-titles`, `teardown`, `microgame`, `memphis-diorama`, `blueprint`, `caption-news`. Tem `DIRECTOR.md` com as falhas mais comuns. Custo: 30–60 min de agente por filme |
| [PHANTOMTONYT/motion-design-skills](https://github.com/PHANTOMTONYT/motion-design-skills) — `3d-toy-character` | É o estilo do @_aighostlab (mascote de vinil, luz de estúdio, sombra de contato) em HyperFrames + three.js. Regras: antecipação → movimento → overshoot → assentar; personagem nunca congelado |
| [JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) | Personagem com **31 emoções**, vistas, chapéus, guia de animação de personagem, render com folhas de contato. Base para dar "atuação" ao nosso mascote |
| [feitangyuan/onetake](https://github.com/feitangyuan/onetake) | Filme em um plano contínuo (cada momento nasce do anterior), com nota de continuidade nas transições |
| [hypit-ai/hypit](https://github.com/hypit-ai/hypit) | Clona um vídeo de referência "1 para 1" como workflow editável, ancorado em palavras. **Atenção**: usa provedores pagos (Seedance 2, GPT Image 2, MiniMax). Avaliar custo antes |
| [zhuyansen/awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills) | Catálogo de 413 repositórios com nota de segurança |

Skills oficiais do HyperFrames que ainda **não** estão instaladas aqui e são do mesmo autor das que já usamos:
`heygen-com/hyperframes@hyperframes-animation` (1 milhão de instalações) e
`heygen-com/hyperframes@hyperframes-creative` (917 mil).

### 5.2 Conteúdo e Instagram (achadas com o find-skills)

| Skill | Instalações | Uso |
|---|---|---|
| `coreyhaines31/marketingskills@content-strategy` | 170 mil | estratégia de conteúdo |
| `coreyhaines31/marketingskills@social-content` | 67 mil | posts e legendas |
| `social-media-skills/skills@instagram-growth` | 1,1 mil | crescimento no Instagram |
| `social-media-skills/skills@instagram-reels-publishing` | 868 | publicação de Reels |
| `gonzalochale/skills@viral-tiktok-hooks` | 366 | ganchos |

Pela regra do próprio find-skills, as de menos de 1 mil instalações precisam ser lidas antes de instalar.

### 5.3 Instalado nesta sessão

- `find-skills` (vercel-labs, 2,4 milhões de instalações), global: `~/.agents/skills/find-skills`, com link no
  Claude Code. Serve para buscar skill nova sempre que surgir uma necessidade.

---

## 6. Plano de melhorias

Priorização MoSCoW. Cada item diz **onde** mexe no código.

### Must have (sem isso o salto de qualidade não acontece)

**M1. Camada de Direção entre roteiro e render.**
Hoje: roteiro → LLM escolhe tipo de tela → HTML fixo.
Depois: roteiro → **diretor** escreve, para cada frase, `{mundo, ação do personagem, objeto, câmera, texto na tela,
estado do HUD}` → montagem combina **peças** (não telas prontas).
- Novo módulo `src/estudio_instagram/direcao.py` (storyboard em JSON validado, como `identidade.problemas()` já faz).
- Acervo vira **peças combináveis**: `modelos/pecas/` (objetos: martelo, tesoura, funil+engrenagens, contador
  mecânico, cadeira de diretor, lupa, carimbo, celular, jornal, mapa…), `modelos/mundos/` (palco, oficina, noir,
  apartamento isométrico, mapa, ilha, auditório) e `modelos/poses/` do mascote.
- Regra dura do diretor: **nenhuma cena sem ação do personagem**, e nenhuma cena igual à anterior.

**M2. Personagem que atua.**
Mascote com biblioteca de emoções, poses e chapéus (modelo: ClaudeAnimationBase, 31 emoções; regras do
`3d-toy-character`: antecipação, overshoot, respiração e piscada, nunca congelado). Ele carrega o objeto de uma
cena para a outra (continuidade), em vez de ficar parado embaixo.

**M3. Portão de qualidade antes de publicar.**
Inspirado em `video-director` e `claude-animated-shorts`:
1. Storyboard aprovado (no automático: validado por regras).
2. 1 quadro parado por cena (`hyperframes snapshot`, já usado em `render.renderizar_carrossel`).
3. **Folha lado a lado** com quadros das referências deste estudo.
4. Crítico de visão (LLM multimodal) dá nota por área (composição, ação do personagem, legibilidade, variedade,
   fidelidade ao mundo) e lista correções. Nota mínima para seguir.
5. QA automático do MP4: quadro preto, quadro congelado por mais de 12 quadros, duração, áudio.
Sem passar, o vídeo não entra na fila do maestro.

**M4. Pauta por acontecimento, não por README.**
- `roteirista.py`: trocar "descreva o que a ferramenta faz" pela fórmula da seção 4.3 e pelos ganchos da 4.4.
  Manter a regra anti-invenção, mas permitir fatos de **fontes verificadas** além do README (notícia, post do
  autor, número de instalações), registrados num `FATOS` com a fonte, como o `video-director` faz.
- `assunto_quente.py`: além de GitHub Trending/HN, priorizar o que é **desejo do público amplo** (vídeo, dinheiro,
  economizar tempo, Instagram, viagem, celular) e penalizar nicho técnico (segurança, infraestrutura).

### Should have (importante, o V1 sobrevive sem)

**S1. Formato "Experimento de IAs" (automático e real).**
O pipeline roda de verdade um jogo com várias IAs (usando os provedores que `llm.py` já tem: Gemini, modelos do
OpenRouter, Mistral), grava o log (mensagens, votos, placar) e o vídeo narra o que aconteceu. Mundo escolhido pelo
jogo (mapa, ilha, nave). É conteúdo **real**, sem meme fabricado, e foi o formato com mais views do nicho.

**S2. Lista das 22:30 com ranking de prova.**
Usar o número de **instalações** do skills.sh (o `npx skills find` já devolve) como métrica do ranking:
"as 5 skills mais instaladas da semana pra [tema de desejo]". Cada item com personagem/fantasia e cenário próprio
(padrão clubedasskills/macelista), "#N" gigante entre os itens.

**S3. HUD de estado persistente.**
Contador que sobe, barra de etapas, "x/5", placar. Barato de fazer e aparece em quase todo vídeo de referência.

**S5. Três ganchos por pauta.**
O roteirista gera 3 ganchos com o mesmo corpo (seção 4.5). O primeiro vai na grade; os outros dois ficam na fila
para repostar o mesmo vídeo em outro dia/horário se o primeiro ficar abaixo da mediana. O `analista.py` passa a
registrar qual gancho rendeu mais, e esse histórico alimenta o roteirista.

**S4. Estudo semanal sem Apify.**
Reescrever `estudo_animacao.py` com o método deste estudo: navegador (lista de reels e views) → yt-dlp → folha de
24 quadros → Whisper local → relatório. Custo zero.

### Could have (bônus)

- **C1.** Formato "Esquete" (Davi vs Claude em diálogo), que já existe em `prototipos/esquete`, com a metáfora
  como cenário (banca de jurados, oficina).
- **C2.** Usar os estilos do Lemo-Opuscar como **cardápio de mundos** (ler os `STYLE.md` e portar 4–6 para
  HyperFrames), em vez de criar mundo do zero.
- **C3.** Efeitos sonoros presos aos eventos da timeline (whoosh no corte, pop no objeto, tique no contador).
- **C4.** Transições com objeto (explodir em voxels, wipe com o personagem).

### Won't have agora (registrado para não esquecer)

- Vídeo gerado por modelo de vídeo (Seedance, Veo, Runway, Higgsfield). As referências provam que dá para chegar
  lá só com código, e é mais barato e repetível.
- Hypit como motor principal (depende de provedores pagos). Pode servir para estudar referências mais tarde.
- Automatizar stories (regra do Davi: stories são manuais).

### Instagram: horário, chamada e legenda

Dados do próprio perfil (`pautas/desempenho.json`, gerado em 2026-11-02, 35 Reels; amostra pequena, então são
indícios, não certezas):

| Faixa | Reels | Views medianas | Tempo médio |
|---|---|---|---|
| manhã (6–10h) | 4 | 920 | 8,4 s |
| meio-dia (10–14h) | 8 | **169** | 5,8 s |
| tarde (14–18h) | 5 | 163 | 7,5 s |
| noite (18–22h) | 8 | 275 | 5,9 s |
| tarde da noite (22–24h) | 8 | **1.176** | 7,3 s |

- O horário das 12:00 da grade é o pior medido. Sugestão: **testar o vídeo de ferramenta às 8h** por duas
  semanas, mantendo a lista às 22:30, e comparar.
- Chamada final usada por praticamente todas as referências: **"Comenta PALAVRA e me segue que eu te mando"**,
  com a caixa de comentário digitando a palavra na tela. O "me segue" converte o envio do link em seguidor
  (o @lowstack ainda avisa: "verifica se está me seguindo, senão não consigo te enviar").
- Legenda: as referências repetem a promessa em uma linha e a palavra do comentário logo no início. Sem emoji
  (regra do Davi). As skills de conteúdo da seção 5.2 podem revisar legenda e plano semanal.

---

## 7. Ordem de execução sugerida

1. **Prova de conceito manual de 1 vídeo** (sem mexer no pipeline): pegar uma pauta real, escrever o storyboard
   com direção (M1), montar 1 mundo + mascote que atua (M2) e passar pelo portão (M3). Davi compara com o
   @_aighostlab lado a lado. Critério de pronto: Davi olha e diz que não parece template.
2. Só depois, automatizar: `direcao.py` + acervo de peças + portão no pipeline.
3. Trocar o roteirista (M4) — pode ser feito em paralelo, porque é texto.
4. Experimento de IAs (S1) como formato novo na grade.
5. Lista 22:30 com ranking de instalações (S2).

Cada passo é validado olhando o resultado antes de seguir (regra do `CLAUDE.md` deste repositório).

---

## 8. Decisões que precisam do Davi

1. **Mascote:** manter o robô atual e dar atuação a ele, ou criar um mascote novo de marca (como o cubo do
   @_aighostlab)?
2. **Estética-base da marca:** pixel (o que mais rendeu no perfil até agora) ou 3D brinquedo (o das
   referências mais fortes)? O mundo muda por vídeo, mas a marca precisa de uma base.
3. **Experimento de IAs:** pode usar os nomes reais das IAs (Claude, GPT, Gemini…) como personagens, como o
   @omagodoalgoritmo faz?
4. **Skills para instalar:** `hyperframes-animation` e `hyperframes-creative` (oficiais), `lemo-opuscar` (plugin),
   `3d-toy-character` e as de conteúdo da seção 5.2. Quais o Davi autoriza?

---

## 9. Arquivos deste estudo

- `RELATORIO.md` — este arquivo.
- `folhas/` — 108 folhas de 24 quadros (nome: `perfil__codigo.jpg`; `salvo__` = reel salvo pelo Davi).
- `transcricoes/` — transcrição de cada reel com tempo por trecho.
- `reels.json` — perfil, código e views de cada reel estudado.
- Os MP4 (835 MB) ficaram fora do repositório, na pasta temporária da sessão. Podem ser baixados de novo com
  `yt-dlp https://www.instagram.com/reel/<codigo>/`.
