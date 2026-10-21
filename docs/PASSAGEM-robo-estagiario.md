# Passagem de sessão: @robo.estagiario (atualizado em 2026-10-20)

Documento para quem abrir uma sessão nova sem ter visto a anterior. Complementa o README (que cobre o canal Arquivo Sombrio)
e `docs/estrategia-crescimento.md` (dados e decisões de crescimento).

## O que é
Conta de Instagram **@robo.estagiario** (notícias de ferramentas de IA para quem programa, em pixel art, Reels + carrossel).
Dono: Davi (estudante de Engenharia de Software, UnB). Meta: ganhar seguidor rápido e vender 3 produtos pela bio.
Estado em 2026-10-20: ~166 seguidores; Reels campeão = Hyperframes (30 mil views, 1.046 salvos).

## O que roda sozinho (GitHub Actions, 24 h)
| Workflow | O que faz |
|---|---|
| `instagram_maestro.yml` | Laço de ~5h40 que dispara as rodadas do dia (`src/estudio_instagram/maestro.py`: 08:00 notícia, 12:00 notícia (ou o próximo do banco), 18:30 venda, 23:30 lista de 5 repositórios; BRT). Reencadeia a si mesmo. |
| `pipeline_instagram.yml` | Gera e publica 1 Reels + 1 carrossel (inputs: `formato`, `repo`, `pauta`, `publicar`). `pauta=` usa uma pauta pronta. |
| `instagram_respondedor.yml` | Bot de comentários e DM. Laço de ~50 min que reencadeia. Filtro de seguidor ligado. |
| `instagram_analista.yml` | Diário: `docs/analise-desempenho.md` e `pautas/desempenho.json` (views, salvos, envios, tempo assistido, por tema/horário/formato). |
| `testes.yml` | pytest. |
Reiniciar maestro ou bot: cancelar os runs em andamento **duas vezes** (cada run cancelado redispara outro) e rodar `gh workflow run <arquivo>`.

## Peças principais (src/estudio_instagram/)
- `maestro.py` rodadas e **banco de vídeos** (`pautas/viral/fila/*.json`, um por dia na rodada de 12:00, ordem do nome; usadas ficam em `pautas/maestro.json`).
- `pipeline.py` / `cenas_pixel.py` / `roteirista.py` (LLM a partir do README do repositório; Gemini, OpenRouter, Mistral em cascata).
- `respondedor.py` + `graph_api.py` bot de comentários. **Filtro de seguidor: tentado e desligado** (`exigir_seguir: false` em `pautas/bot_respostas.json`). Dois bloqueios da plataforma: (1) `is_user_follow_business` devolve erro 230 ("consentimento necessário") mesmo depois de a pessoa responder, porque o app só tem acesso padrão; (2) a 2ª DM (depois da resposta "SIGO") é barrada com 403 / subcódigo 2534022 ("fora do período permitido") e a tag HUMAN_AGENT exige aprovação da Meta. Só a 1ª resposta privada ao comentário funciona. Então o link sai na 1ª DM, com pedido para seguir no texto. O código do filtro continua em `respondedor.py` (`liberar_pendentes`) caso a Meta aprove acesso avançado. 16 pessoas que ficaram sem link receberam resposta pública no comentário. Produtos pagos e gatilhos: ver `pautas/bot_respostas.json`.
- `analista.py` análise de desempenho. `pausa.py` freio de 24 h se o Instagram acusar bloqueio.
- Voz: Gemini TTS "Orus" (reserva Edge). Vídeo: Hyperframes 0.8.154 via npx.

## Regras que NÃO mudam sem decisão do Davi
- **Modo seguro**: 4 rodadas/dia, 2 h entre rodadas, 10 min entre Reels e carrossel, freio de 10 posts/24 h, pausa de 24 h se vier o erro 2207051. A API aceita 100 posts/dia, mas o anti-spam já bloqueou a conta com 10: **não subir volume**.
- Nunca misturar os 2 canais do YouTube (Arquivo Sombrio e Em Alta). Nunca coautoria do Claude em commit/PR.
- Número e comando em roteiro só do README (RN-1). Vídeo de venda: sem promessa de renda.
- Não alterar o "style lock" (`src/estilo.py`) nem as configs de imagem do canal Arquivo Sombrio sem revalidar visualmente.

## Produtos (Kiwify)
Kit Claude Code R$ 17 (`pay.kiwify.com.br/7RZ7Yeh`), Pack Pixel R$ 27 (`jmiKAgE`), **Kit Engenharia com IA R$ 37** (`3Jm8P4j`).
Use sempre o link `pay.kiwify.com.br/...` (o `kiwify.app/...` leva ao perfil). Fontes em `produto/`. O kit de engenharia
(`produto/kit-engenharia/`) tem CLAUDE.md, 6 skills, `ferramentas/mutar.py`, templates e um exemplo testado.

## Novidades de 2026-10-20/21
- **Formato lista** (`--formato lista`, `lista.py`): 5 repositórios num Reels de ~35-40 s + carrossel; DM com os 5 links. Roda às 21:00 (cai no pixel2 se não sair).
- **Legenda salvável**: roteiros trazem "passos" do README e a legenda abre com "Salva este vídeo pra usar com calma".
- **Trilha original** (`gerar_trilha.py`, arpejo chiptune sintetizado, sem direito autoral) 14 dB abaixo da voz em `pixel2.html.tpl`. Para desligar, tirar a linha `<audio id="trilha" ...>`.
- **Banco** (`pautas/viral/fila/`): tudo regenerado no formato curto (5-6 cenas). Ordem de saída às 12:00: habblaud, xerj... (ver `ls`).
- **Referências lidas pelo Chrome** (andrevale.dev, lowcodepedro, igao.ia): ver `docs/estrategia-crescimento.md`.

## Aposta em curso: formato curto
Descoberta (analista): as pessoas assistem 5–11 s de cada Reels. Desde 2026-10-21 os roteiros saem com 20–35 s (5–6 cenas, frases completas).
O analista compara curto × longo em `docs/analise-desempenho.md`. Decidir quando houver 8+ Reels curtos: tempo assistido e salvos/envios subiram?

## Pendências que só o Davi pode fazer
1. Chave Pix na Kiwify (Financeiro > Dados bancários). Compra teste dos 3 produtos. Módulo vazio "Organizando o Conteúdo" nas áreas de membros.
2. **Testar o filtro de seguidor** com a conta pessoal: comentar uma palavra, responder SIGO sem seguir (deve vir o aviso), seguir e responder de novo (deve vir o link). Se a API não retornar `is_user_follow_business` depois da resposta, ajustar `liberar_pendentes`.
3. Bio e links do perfil (a API não lê os links extras).
4. Trial Reels só pelo app (a API pode não expor).

## Ideias ainda não feitas
- Monitor de virais de outros perfis (a API oficial não lê perfil alheio nem hashtag; precisa de Apify ou do Chrome com extensão).
- Highlight com o Reels de 30 mil; série "IA que cria vídeo" e formato tutorial "instale em 4 passos, salve este vídeo".
- Trilha sonora de fundo baixa (arquivo `assets/musica3_curioso.mp3` existe, não integrado).
- Pivô Drive: `invalid_grant` pendente (não relacionado ao Instagram).

## Armadilhas já vividas
- Cron do GitHub atrasa horas: por isso o maestro e o bot são laços que reencadeiam.
- Push durante um run perde o bookkeeping: os workflows têm laço de 5 tentativas `pull --rebase && push`.
- `.pyc` em cache dava falso "sobreviveu" no `mutar.py` (corrigido com `PYTHONDONTWRITEBYTECODE`).
- Marcador `{estrelas:...}` como primeira palavra quebrava as âncoras (corrigido).
- Pipe com `| tail` esconde o código de saída: conferir testes pelo `exit code`.

## Se o Claude e o PC forem desligados: o que continua e até quando
Tudo roda na nuvem (GitHub Actions, repositório público = minutos grátis). Sem o PC e sem o Claude, continuam: 4 rodadas por dia, bot de comentários e DM, análise diária e o banco de vídeos (1 por dia ao meio-dia, 10 vídeos na fila = ~10 dias; depois disso as rodadas seguem com repositório novo escolhido sozinho).
Limites reais, por ordem de prazo:
1. **Token do Instagram (`INSTAGRAM_GRAPH_TOKEN`)**: token de longa duração, vale ~60 dias a partir de quando foi gerado (colado em 17–18/10 → renovar até ~10/12/2026). Quando vence, tudo de Instagram para (post e bot). Renovar: `curl "https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=<TOKEN>"` devolve um token novo (precisa ter 24 h+), e depois atualizar o segredo: `gh secret set INSTAGRAM_GRAPH_TOKEN`.
2. **Cota grátis das APIs de IA** (Gemini voz e roteiro, OpenRouter, Mistral): se acabar, a voz cai no Edge TTS e o roteiro tenta o próximo provedor; se todos falharem, a rodada falha e tenta de novo na seguinte (sem postar lixo).
3. **Bloqueio do Instagram (erro 2207051)**: liga a pausa de 24 h sozinha e volta sozinho.
4. **GitHub**: desliga workflows agendados depois de 60 dias sem atividade no repositório; os commits de bookkeeping do próprio robô contam como atividade.
5. **Corrente do maestro/bot**: cada execução dispara a próxima; se morrer, o cron de hora em hora religa (no máximo 1 h parado).
Sem o Claude **não** acontece: ajuste de estratégia, abastecer o banco depois dos 10 vídeos com roteiro curado, trocar bio/fixar post, conferir a análise. Dá para abrir um Claude novo e mandar ler este arquivo.
