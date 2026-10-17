# Referências para o @robo.estagiario (2026-10-17)

Coletado no Instagram logado (Claude in Chrome), a partir da lista de perfis do Davi. Números são
views da aba Reels no dia da coleta. Amostra pequena: serve para decidir direção, não para provar causa.

## Referências de ESTILO (vídeo sem aparecer)

### oguiadaia (5,4 mil seguidores, 14 posts)
- Personagem de palito com rosto em fundo claro, identidade da marca (logo Claude) no topo, texto curto
  embaixo (ex.: "pare").
- Um Reel com 1,1 milhão de views, outros com 117 mil e 84 mil, mas a maioria entre 1,6 mil e 25 mil.
  O resultado vem de poucos acertos, não de consistência.
- Gancho do Reel de 1,1 mi (legenda): "Não use o Claude Code a menos que você tenha esses cinco
  plugins instalados". É uma proibição com lista prometida.
- Cuidado: nos comentários desse Reel há aviso de plugin com minerador de moeda e crítica de
  segurança. Não copiar recomendação de ferramenta sem checar o repositório.

### brunoptrevisan (19,8 mil seguidores, 53 posts)
- Fundo escuro com fonte manuscrita, ícones de apps/logos ligados por setas, selo "PARTE 2" em
  moldura dourada. É a estética mais parecida com a do robô (escuro + laranja/dourado).
- Views entre 1,8 mil e 446 mil (396 mil, 342 mil, 118 mil nos melhores).
- O de 396 mil ("COMO CLONAR APPS COM IA") tem 33,8 mil curtidas e 727 comentários. Comentário
  fixado do autor: "roteiro, voz e edição feita por IA". Há quem comente que o vídeo "também foi
  feito 100% por IA", e isso virou assunto de engajamento.
- Formato de série: "Parte 2", "Parte 3". Comentários pedem a próxima parte.

### dicas.de.ia (55 seguidores)
- Objetos do dia a dia com rosto, estilo 3D, falando. Pouco alcance, só referência visual.

## Referências de CONTEÚDO (quem aparece)

| Perfil | Seguidores | Views típicas | Melhor |
|---|---|---|---|
| gabrieltomaz.ia | 31,1 mil | 5 mil a 250 mil | 987 mil |
| 99hud | 81,3 mil | 2 mil a 67 mil | 67 mil |
| rafa.grandi | 334 mil | 11 mil a 172 mil | 1,1 mi |
| fabianocarvalhojr | 258 mil | 1,8 mil a 62 mil | 62 mil |
| lowcodepedro | 8,4 mil | 800 a 87 mil | 384 mil |
| gabrielventurads | 10,8 mil | 2 mil a 39 mil | 39 mil |
| sougucarvalho | 7 mil | 800 a 5,5 mil | 5,5 mil |
| inteligenciaartificialbrasill | 18 mil | 2 mil a 7 mil | 7 mil |

- `gabrieltomaz.ia`: fala para câmera com gravação de tela no topo, legenda de 1 palavra por vez
  com a palavra-chave destacada e CTA em tela: `comenta "APP"` / "sua DM" (palavra para comentar).
- `amvrosiokt`: o perfil com esse nome não existe (a página diz "não está disponível"). Confirmar o @.
- `gabrielventurads` informa na bio "Meus vídeos são editados por IA".

## Padrões que se repetem

1. Variação enorme de views no mesmo perfil (10x a 100x). Os picos têm gancho de proibição, lista
   prometida ou novidade, e o resto é morno. Vale gerar mais variações de gancho do que polir uma.
2. CTA com palavra para comentar (a "palavra no final" que o Davi citou), e série em partes.
3. Texto grande desde o primeiro quadro; legenda curta que muda no ritmo da fala.
4. Os vídeos sem rosto que funcionam têm personagem ou diagrama animado, não cartão estático.

## Contraste com o robô hoje

Carrossel e Reels são cartões estáticos de texto em fundo escuro. Não tem personagem, diagrama
animado, CTA de palavra para comentar nem série em partes. O estilo `brunoptrevisan` (diagrama com
setas e selo de parte) é o mais fácil de adaptar, porque a paleta já é parecida.

## Pesquisa de ferramentas (TikTok/YouTube)

Busca na web retornou só páginas de ferramentas pagas (Revid, Invideo, Short AI e semelhantes), sem
exemplo de canal. Não usei como fonte. O pipeline já tem HyperFrames para animação, então o
caminho provável é construir o estilo dentro dele, não assinar ferramenta.

## Próximos passos sugeridos

1. Escolher uma direção de estilo com o Davi: diagrama animado (estilo brunoptrevisan) ou personagem
   de palito (estilo oguiadaia).
2. Novo molde de Reels com: gancho de proibição/lista no primeiro quadro, ícones ligados por setas,
   legenda por palavra, CTA "comenta X", e selo "Parte N" quando for série.
3. Testar um Reels por vez, olhando o resultado antes de aceitar.

## lowcodepedro (8,4 mil seguidores) — referência de qualidade, adicionada em 2026-10-17

- Formato dividido na tela: metade de cima é gráfico animado, metade de baixo é a pessoa falando,
  com legenda que destaca uma palavra por vez (verde).
- O gráfico de cima é um **cartão de repositório do GitHub** (nome, linguagem, estrelas) flutuando
  em perspectiva, ou ícones de apps com marca de "feito", ou um cartão "ITEM LENDÁRIO / LV 1 / XP"
  em estilo de jogo para apresentar um repositório.
- O mesmo repositório (`morluto/rea`, 269 mil estrelas, "engenharia reversa de qualquer app") virou
  três Reels em dias seguidos, cada um com palavra de comentar diferente: 386 mil, 87 mil e 81 mil
  views. Cada um reuniu de 70 a 330 comentários só com a palavra-chave (ENGENHARIA, CLONE).
- Legenda do post: abre com "Esse repositório do GitHub pode mudar a forma como você...", explica em
  3 frases, fecha com `Comenta "PALAVRA" que eu te mando o link`.

Leitura: o formato que mais rendeu é "um repositório do GitHub + cartão do repositório + palavra para
comentar". O robô já coleta dados do GitHub (estrelas, licença, cartão), então o ingrediente está
no código. Falta um molde de Reels com o cartão do repositório em destaque e reaproveitar o mesmo
repositório com ganchos e palavras diferentes.
