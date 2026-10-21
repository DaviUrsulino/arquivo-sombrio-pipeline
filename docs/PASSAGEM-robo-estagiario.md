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
| `instagram_maestro.yml` | Laço de ~5h40 que dispara as rodadas do dia (`src/estudio_instagram/maestro.py`: 08:00 notícia, 12:00 notícia (ou o próximo do banco), 18:30 venda, 21:00 lista de 5 repositórios; BRT). Reencadeia a si mesmo. |
| `pipeline_instagram.yml` | Gera e publica 1 Reels + 1 carrossel (inputs: `formato`, `repo`, `pauta`, `publicar`). `pauta=` usa uma pauta pronta. |
| `instagram_respondedor.yml` | Bot de comentários e DM. Laço de ~50 min que reencadeia. Filtro de seguidor ligado. |
| `instagram_analista.yml` | Diário: `docs/analise-desempenho.md` e `pautas/desempenho.json` (views, salvos, envios, tempo assistido, por tema/horário/formato). |
| `testes.yml` | pytest. |
Reiniciar maestro ou bot: cancelar os runs em andamento **duas vezes** (cada run cancelado redispara outro) e rodar `gh workflow run <arquivo>`.

## Peças principais (src/estudio_instagram/)
- `maestro.py` rodadas e **banco de vídeos** (`pautas/viral/fila/*.json`, um por dia na rodada de 12:00, ordem do nome; usadas ficam em `pautas/maestro.json`).
- `pipeline.py` / `cenas_pixel.py` / `roteirista.py` (LLM a partir do README do repositório; Gemini, OpenRouter, Mistral em cascata).
- `respondedor.py` + `graph_api.py` bot. Fluxo do filtro: comentário com palavra → DM pede "segue e responde SIGO" → ao responder, confere `is_user_follow_business` → manda o link. Se a API não souber dizer, depois de 2 tentativas manda o link. Produtos pagos (PACK, ENGENHARIA, TESTES) saem direto. Config em `pautas/bot_respostas.json`.
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
