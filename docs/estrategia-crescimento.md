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
