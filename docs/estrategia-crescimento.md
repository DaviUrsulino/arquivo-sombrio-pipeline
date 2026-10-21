# Estratégia de crescimento — @robo.estagiario

Atualizado em 2026-10-20. Tudo aqui é hipótese a medir, não promessa de resultado.

## O que já sabemos (dados da própria conta)
- Os posts que mais renderam foram de IA para criar vídeo (Hyperframes, REA). Repositório genérico rende pouco.
- O comentário-gatilho funciona: o bot já respondeu dezenas de comentários.
- A conta chegou ao limite de 10 publicações em 24 h; por segurança o ritmo é 3 rodadas por dia (Reels + carrossel).
- Meme com piada fabricada (fatura do Claude) não agradou o dono da conta. Fora do banco.

## Banco de vídeos (`pautas/viral/fila/`)
- Pautas prontas e revisadas, em ordem de nome. A rodada das 09:00 usa a próxima que ainda não saiu; sem pauta na fila, segue o fluxo normal.
- O que já saiu fica em `pautas/maestro.json` (`fila_usadas`).
- Regra: só entra no banco roteiro cujos números e comandos vêm do README do repositório, sobre tema quente de IA/vídeo/agentes.

## Fecho "siga e comente"
- Vídeo, carrossel, legenda e DM pedem para seguir e comentar a palavra.
- Filtro "só manda para seguidor": a API só libera o campo "segue?" depois que a pessoa responde uma DM (erro 230 antes disso). Caminho possível: primeira DM com botão "Já sigo", depois checar e enviar o link. Só vale a complexidade se o fecho simples não converter. Decidir após 3 dias de dados.

## Experimentos (um de cada vez, 3 dias cada)
1. Gancho nos 2 primeiros segundos com a promessa mais forte do tema.
2. Reels de 20–30 s contra 50 s (a retenção costuma cair no meio).
3. Fecho com e sem "siga e comente".
4. Horário: 09:00 contra 12:00 contra 19:00.
Métricas (GQM): objetivo = seguidores; pergunta = qual formato ganha mais seguidores por Reels; métrica = seguidores novos em 48 h por post, mais salvamentos e compartilhamentos.

## Inteligência de mercado
- Monitor de virais ainda não existe. Opções: Apify (token) ou análise manual pelo Chrome dos perfis de referência (igao.ia, lowcodepedro, brunoptrevisan, oguiadaia).
- Registrar por Reels de referência: tema, gancho, duração, hora, visualizações.

## Identidade
- O robô estagiário é o rosto da conta. Rosto humano do Davi: depois de 1.000 seguidores.
- Bio: promessa em uma linha + link único. Revisar quando houver número de seguidores novo.

## Riscos
- Bloqueio por excesso de ações: manter freio de 10 posts/24 h e pausa de 24 h.
- Áudio de trend pode ter direito autoral; usar a biblioteca de sons do Instagram.
- Não usar scraper não oficial (Instaloader) na conta principal.

## Pesquisa de 2026-10-20: crescer mais rápido (fontes: blogs de marketing e declarações públicas; confiança média)
- **Sinais do Reels, em ordem de peso:** tempo assistido (retenção), envios por DM, salvamentos por alcance, velocidade de engajamento
  nos primeiros 30–60 min e replays. Mosseri disse em público que enviar o Reels por DM é o sinal de maior valor.
  Fontes: https://metricool.com/pt/algoritmo-instagram/ · https://adaptlypost.com/pt/blog/instagram-reels-algorithm
- **Gancho:** o que segura o espectador nos 3 primeiros segundos é a especificidade (número ou ação concreta logo na primeira palavra).
  Uma fonte cita 42% de retenção aos 3 s como limiar para sair do teste de não seguidores (número de blog, não oficial).
- **Seguidor vem de profundidade, não de view:** quem salva, compartilha e visita o perfil. Nosso Reels de 28 mil views teve 973
  salvamentos e 194 envios, mas só cerca de 100 seguidores: o vídeo entregava o link do repositório, não um motivo para seguir.
- **Trial Reels** (Instagram, teste com não seguidores sem aparecer no perfil; métricas em 24 h): https://routenote.com/blog/how-to-test-reels-with-non-followers-on-instagram/
  A API de publicação pode não expor esse recurso; se não expuser, usar manualmente no app.
- **Horários (Brasil, 2026):** picos de 07–09 h, 12–13 h e 18–21 h; terça a quinta rendem mais; fim de manhã é o ponto forte.
  O horário ótimo da conta aparece em Insights, "períodos mais ativos". Fonte: https://metricool.com/pt/melhor-horario-para-postar-instagram/
- **Limite de publicação:** a API aceita até 100 posts por 24 h (carrossel conta como 1), mas a detecção de spam (erro 2207051) é
  separada e foi o que bloqueou a conta com 10 posts no dia. Fonte: https://developers.facebook.com/docs/instagram-platform/content-publishing

### Decisões tomadas a partir disso
1. Fecho do vídeo: "manda pra um amigo dev, segue o robô estagiário e comenta X" (envio por DM e seguir antes do link).
2. Gancho do roteirista: promessa específica nas primeiras palavras, sem "Conheça" e sem começar pelo nome do projeto.
3. Rodadas nos horários de ouro: 08:00, 12:00, 18:30 e 21:00 (8 posts por dia), freio de 10 posts por 24 h mantido. O vídeo mais forte do banco sai às 12:00.
4. Série "IA que cria vídeo" (o tema que estourou) e formato tutorial "instale em 4 passos, salve este vídeo" entram no banco.

## Monetização no Instagram (Brasil, 2026)
- **Programa de bônus por views (Reels Play):** descontinuado em 2023; não é caminho.
- **Presentes em Reels:** a partir de 500 seguidores. **Assinaturas e selos:** a partir de 10 mil seguidores, conta profissional, 18+.
- **Parcerias pagas e afiliados:** dependem de audiência qualificada; o nicho (devs e quem constrói com IA) paga bem por ferramenta.
- **Produto próprio** (o que já fazemos): Kit Claude Code (R$ 17), Pack Pixel (R$ 27) e Kit Engenharia com IA (R$ 37). É a
  receita mais rápida com pouca audiência, porque não depende do programa do Instagram.
- Fonte: https://metricool.com/pt/como-monetizar-instagram/ · https://lojaintegrada.com.br/hub/ativar-monetizacao-instagram/

## Perfis de referência lidos pelo Chrome (2026-10-20, só leitura)
Dados do perfil e das legendas dos posts campeões de cada conta.

| Conta | Seguidores | Views típicas | Campeões | O que repete nos campeões |
|---|---|---|---|---|
| andrevale.dev | 1.013 | 400 a 3 mil | 53,6 mil · 42,1 mil · 23,6 mil | Projeto visual novo (escritório em pixel art com agentes), tutorial em 4 passos, "Salva este vídeo", palavra-chave nos comentários |
| lowcodepedro | 9.251 | 2 a 6 mil | 436 mil · 111 mil · 38 mil | "A maioria usa X do jeito cansativo..." + repositório grátis + "Comenta LINKEDIN e me segue pra receber a mensagem" |
| igao.ia | 141 mil | 4 a 8 mil | 248 mil · 81 mil · 67 mil | Título com seta ("5 plugins para turbinar o Claude Code ↓"), lista com nome de cada item, "Comenta SKILL e me segue" |

Leituras:
- **A cauda é pesada em todas as contas**: mesmo com 141 mil seguidores a mediana é ~5 mil e poucos posts passam de 80 mil. Viral é loteria com
  muitas tentativas; vale subir a qualidade do gancho e testar vários temas, não repetir um.
- **Conta pequena também estoura**: andrevale.dev com 1 mil seguidores teve 53 mil views. O que decidiu foi o tema (novidade visual) e o formato (passo a passo salvável).
- **Formatos que repetem**: lista de N ferramentas com nome de cada uma, tutorial em N passos, contraste "a maioria faz X do jeito cansativo", e fecho "Comenta PALAVRA e me segue".
- **Legenda longa e salvável**: os campeões trazem o passo a passo ou a lista dentro da legenda ("Salva este vídeo...").
- **Tema da semana** nessas contas: skills de Instagram/LinkedIn dentro do Claude (achar Reels virais e virar roteiro), plugins e MCPs para Claude Code,
  escritório de agentes em pixel art (Habblaud, repositório `marmottajr/habblaud`, 754 estrelas).

### Decisões tiradas daí (implementadas em 2026-10-20)
1. Legenda salvável: os roteiros trazem "passos" de 3 a 4 itens do README e a legenda começa com "Salva este vídeo pra usar com calma".
2. Formato **lista** (`--formato lista`, `src/estudio_instagram/lista.py`): 5 repositórios reais num Reels curto + carrossel, com DM de todos os links.
3. Vídeo sobre o Habblaud (pixel art é a nossa marca) entra no banco como prioridade.
4. Bio sugerida (a API não edita a bio; o Davi cola): "1 ferramenta de IA grátis por dia 🤖 | Garimpo o GitHub pra você | Estudante de Eng. de Software (UnB) | Kits abaixo".
