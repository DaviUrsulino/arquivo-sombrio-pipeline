# Modo seguro do Instagram (desde 2026-10-19)

**Por quê:** ao rodar 5 rodadas por dia (10 posts), a Graph API devolveu `action is blocked` /
`Application request limit reached` (código 4, subcódigo 2207051). A Meta não publica o limite exato de
publicações automáticas, então a regra é ficar bem abaixo do que chamou atenção.

## O que está ligado

| Proteção | Valor | Onde |
|---|---|---|
| Rodadas por dia (cada uma = 1 Reels + 1 carrossel) | 3 (09:00, 14:00, 19:00 de Brasília), ou seja, 6 posts por dia | `maestro.py` |
| Intervalo mínimo entre rodadas | 2 horas | `maestro.py` |
| Espera entre o Reels e o carrossel | 10 minutos | `pipeline.py` |
| Rodada atrasada demais (mais de 2 h) | é pulada, não acumula | `maestro.py` |
| Cota de 24 h da conta | não publica se já usou 10 (limite oficial: 100) | `pipeline.py` |
| **Freio automático** | se o Instagram acusar bloqueio, pausa tudo por 24 h (`pautas/pausa.json`) | `pausa.py` |

## Como saber se pausou

`pautas/pausa.json` existe com `ate` no futuro, e o log da rodada diz "PAUSA DE SEGURANÇA". O maestro e o
pipeline deixam de publicar até a hora marcada. Para liberar antes, apague o arquivo (só depois de entender o motivo).

## O que isso NÃO garante

Nenhuma proteção impede a Meta de limitar a conta. Conteúdo repetido, muitos links e comentários idênticos
também pesam. O bot de comentários responde só a quem comenta uma palavra-chave, que é o uso permitido de resposta privada.
