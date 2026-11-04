# Estado do Instagram @ursulino.ia (atualizado em 03/11/2026)

Documento de passagem: qualquer sessão nova do Claude deve ler isto antes de mexer no Instagram.

## O que funciona (dados)
- Lista de 4 repositórios no visual pixel ORIGINAL, postada por volta das 23:30: 1.000 a 1.200 views, 7 a 9 s assistidos, cerca de 20 salvos.
- A mesma lista ao meio-dia e no estilo "tier": 111 views. Não pôr lista em estilo de estúdio.
- Vídeo de uma ferramenta só: nunca passou de ~380 views, com 3 a 4 s assistidos, em nenhum estilo.
- Melhor gancho: problema ou risco pra quem assiste ("Seu espaço pode ser roubado...", 1.269 views). Descrever a ferramenta não funciona.

## Grade (src/estudio_instagram/maestro.py)
- 12:00: vídeo de uma ferramenta numa identidade (escritório ou vila 3D, em rodízio); venda na terça e sexta.
- 20:00: loop, só se houver vídeo em loops/fila/.
- 22:30: lista, todo dia.

## Peças
- Identidades automáticas: src/estudio_instagram/identidade.py e modelos/identidades/ (acervo de cenas escolhido pelo LLM).
- Protótipos ainda manuais: prototipos/pixel, holofote, esquete.
- Direct: guia_dm.py manda um mini-guia (o que faz, 3 passos e o link).
- Assunto quente (assunto_quente.py): GitHub Trending + Hacker News + repos novos do GitHub, sem Apify (o Reddit bloqueia robô). Os repositórios quentes e inéditos entram primeiro: até 3 candidatos no vídeo de ferramenta e até 2 itens na lista.
- Referências do Davi: referencias/referencias.json. Estudo semanal automático em referencias/estudos/.
- Produto: Pack Estúdio, R$ 47 na Kiwify (https://pay.kiwify.com.br/lfbxkKI).

## Estúdio com direção (novo em 2026-11-03, ainda DESLIGADO na grade)
- Estudo de 108 Reels: referencias/estudos/2026-11-03/RELATORIO.md. Plano de crescimento: docs/plano-crescimento-2026-11.md.
- Código: src/estudio_instagram/diretor/ (ADR 0006). A frase escolhe a cena; robô de vinil atua; 3 ganchos por pauta;
  portão de qualidade (QA + crítico com visão) antes de publicar.
- Formatos: vídeo de ferramenta (`python -m src.estudio_instagram.diretor.fazer --repo dono/nome --saida ...`),
  experimento real de IAs (`... diretor.experimento`), ranking com instalações reais (`... diretor.ranking`).
- Na grade só com `ESTUDIO_DIRETOR=1`; se reprovar no portão, o pipeline usa o caminho antigo.
- Vídeos de teste em videos_teste/ (não postar sem o Davi aprovar).
- Render 3D por software: ~7 min por vídeo (GPU do HyperFrames não cria WebGL nesta máquina).

## Regras do Davi
- Sem emoji em legenda.
- Não postar fora da grade sem ele pedir.
- Toda referência nova vai no registro.
- Cada vídeo com cenas próprias; identidade não é molde.
- Nunca pôr linha de coautoria em commit.

## Próximos passos combinados
1. Não mudar nada até 31/10. Depois, ver se as listas das 22:30 voltaram a passar de mil.
2. Se passarem, colocar uma 2ª lista por dia, com o tema puxado das tendências.
3. Davi gravar ganchos de 5 a 10 s com o rosto; o resto do vídeo continua animado.
4. Ligar no automático as identidades pixel e holofote.
5. Produto futuro "Instagram no automático com IA", só depois de o perfil ter prova de crescimento.
