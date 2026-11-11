"""Assunto gigante + a ferramenta que serve a quem curte aquele assunto.

A fórmula veio do Reels que o Davi mandou em 2026-11-10 pedindo "faz igual" (@_aighostlab, DfiRG6Dpn5T):
**558 mil views, 35 mil curtidas e 8.211 comentários em um dia, com 53 segundos.** A legenda inteira é uma linha:

    "Comenta CORTES e recebe o sistema que faz os cortes do GTA 6 por você"

Three coisas que a gente não fazia:
1. O gancho é o assunto que o país inteiro está falando (GTA 6), não a ferramenta.
2. A ferramenta entregue resolve uma dor de quem JÁ curte aquele assunto (quem joga quer postar clipe), em vez de
   vender a nossa máquina genérica -- que é o que o nosso "em-alta" fazia e rendeu mediana de 195 views.
3. A legenda é UMA linha, que é só o pedido do comentário. Sem 4 linhas de resumo e sem hashtag empilhada.

Aqui o assunto não é o do dia (isso é o `em_alta.py`): é um público grande e permanente -- jogo, futebol, música,
prova, viagem. O par assunto-ferramenta é curado à mão porque é exatamente onde a escolha errada mata o vídeo.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import series

# (slug, assunto gigante, repositório, palavra do comentário, o que a ferramenta faz PARA quem curte o assunto)
PARES = [
    # 10/11: a 2ª prova do ENEM 2026 é dia 15/11. Janela de 5 dias com milhões de estudantes no desespero —
    # assunto gigante com data marcada vem antes de qualquer outro (ver em_alta.py para o assunto do dia).
    ("resumo-pra-prova", "a reta final do ENEM, com a segunda prova no domingo e matéria demais pra revisar",
     "Mintplex-Labs/anything-llm", "RESUMO", "lê a apostila inteira e responde a sua dúvida em português"),
    ("cortes-de-gameplay", "GTA 6 e os clipes de jogo que todo mundo posta", "Vincentwei1021/video-shotcraft",
     "CLIPE", "corta sozinho os melhores momentos de uma gravação longa de gameplay"),
    ("legenda-de-corte", "os cortes de podcast que tomaram conta do feed", "m1guelpf/auto-subtitle",
     "LEGENDA", "põe legenda queimada em qualquer corte, do jeito que o pessoal posta"),
    ("capa-de-musica", "a capa que todo mundo posta quando sai a retrospectiva do ano", "danielgatis/rembg",
     "CAPA", "recorta a sua foto e monta a arte sem pagar aplicativo"),
    ("roteiro-de-viagem", "a viagem que todo mundo planeja no grupo e nunca sai do papel", "open-webui/open-webui",
     "VIAGEM", "monta o roteiro dia a dia com o que você quer ver e quanto pode gastar"),
    ("foto-de-familia", "aquela foto antiga de família que ficou borrada", "TencentARC/GFPGAN",
     "FOTO", "recupera foto velha, riscada ou tremida em alguns segundos"),
]
INTERVALO = timedelta(hours=20)
PREFIXO = "assunto-ferramenta:"


def proximo(estado: dict) -> tuple[str, str, str, str, str] | None:
    return next((p for p in PARES if f"{PREFIXO}{p[0]}" not in estado), None)


def precisa(estado: dict, agora: datetime | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    feitas = [datetime.fromisoformat(v["quando"]) for k, v in estado.items() if k.startswith(PREFIXO)]
    return not feitas or agora - max(feitas) >= INTERVALO


def extra(assunto: str, promessa: str, palavra: str) -> str:
    from . import segredos
    return (segredos.texto("extra_assunto_ferramenta")
            .replace("__ASSUNTO__", assunto).replace("__PROMESSA__", promessa).replace("__PALAVRA__", palavra))


def legenda(promessa: str, palavra: str) -> str:
    """Uma linha, que é só o pedido do comentário — como a do Reels de 558 mil. O resto do texto está no vídeo."""
    return f"Comenta {palavra} e recebe o sistema que {promessa} 🎮".replace(" 🎮", "")


def registrar(slug: str):
    series.registrar(f"{PREFIXO}{slug}", slug)
