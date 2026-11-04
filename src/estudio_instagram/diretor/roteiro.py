"""Roteiro por ACONTECIMENTO (não por README), com 3 ganchos.

Base: estudo de 108 Reels (referencias/estudos/2026-11-03). O que viraliza conta um fato com alguém fazendo algo
("fizeram engenharia reversa...", "coloquei 7 IAs pra governar..."); a ferramenta entra como prova. O mesmo vídeo
com 3 ganchos diferentes fez 32 mil, 122 mil e 941 mil views, então o roteiro sempre sai com 3 ganchos para teste.

A regra anti-invenção continua: só fatos que estão no bloco FATOS (README, dados do GitHub, log do experimento,
número de instalações). O que muda é o ângulo: história e consequência na vida de quem assiste, não descrição.
"""

import re

from ..llm import gerar_json
from .. import segredos

SISTEMA = segredos.texto("roteiro_sistema")  # texto no repositório privado (ver segredos.py)

PROIBIDO_NO_INICIO = re.compile(r"^(conheça|olha só|olha so|você conhece|voce conhece|hoje eu)", re.I)


def problemas(r: dict) -> list[str]:
    erros = []
    g, c = r.get("ganchos"), r.get("corpo")
    if not isinstance(g, list) or len(g) != 3:
        return ["'ganchos' precisa ter exatamente 3 itens"]
    if not isinstance(c, list) or not 4 <= len(c) <= 6:
        return ["'corpo' precisa ter de 4 a 6 frases"]
    for k, f in enumerate(g + c):
        n = len(str(f).split())
        if not 4 <= n <= 15:
            erros.append(f"frase '{f[:40]}' tem {n} palavras (use 5 a 13)")
        if any(ch in str(f) for ch in "#@*/_<>{}"):
            erros.append(f"frase '{f[:40]}' tem símbolo")
    for f in g:
        if PROIBIDO_NO_INICIO.search(str(f).strip()):
            erros.append(f"gancho '{f[:40]}' começa de um jeito proibido")
    if not any(str(f).lower().startswith("isso porque") for f in c):
        erros.append("falta a frase que começa com 'Isso porque'")
    if not any(str(f).lower().startswith("ou seja") for f in c):
        erros.append("falta a frase que começa com 'Ou seja'")
    p = str(r.get("palavra", ""))
    if not re.fullmatch(r"[A-Z]{3,9}", p):
        erros.append("'palavra' precisa ser 3 a 9 letras maiúsculas sem acento")
    return erros


def escrever(fatos: str, llm=gerar_json, tentativas: int = 3, extra: str = "") -> dict:
    pedido = f"FATOS:\n{fatos}\n{extra}"
    for _ in range(tentativas):
        r = llm(SISTEMA, pedido)
        erros = problemas(r)
        if not erros:
            r["cta"] = f"Comenta {r['palavra']} e me segue que eu te mando o link."
            return r
        pedido = f"FATOS:\n{fatos}\n{extra}\n\nSEU ROTEIRO ANTERIOR TEVE PROBLEMAS, CORRIJA:\n- " + "\n- ".join(erros)
    raise RuntimeError("roteiro inválido: " + "; ".join(erros))


def frases(roteiro: dict, gancho: int = 0) -> list[str]:
    return [roteiro["ganchos"][gancho]] + list(roteiro["corpo"]) + [roteiro["cta"]]
