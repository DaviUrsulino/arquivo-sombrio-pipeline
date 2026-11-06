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


def problemas(r: dict, max_corpo: int = 6) -> list[str]:
    erros = []
    g, c = r.get("ganchos"), r.get("corpo")
    if not isinstance(g, list) or len(g) != 3:
        return ["'ganchos' precisa ter exatamente 3 itens"]
    if not isinstance(c, list) or not 4 <= len(c) <= max_corpo:
        return [f"'corpo' precisa ter de 4 a {max_corpo} frases"]
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
    tela = str(r.get("texto_tela", "")).split()
    if not 1 <= len(tela) <= 7:
        erros.append("'texto_tela' precisa ter de 1 a 6 palavras (o gancho escrito na tela)")
    p = str(r.get("palavra", ""))
    if not re.fullmatch(r"[A-Z]{3,9}", p):
        erros.append("'palavra' precisa ser 3 a 9 letras maiúsculas sem acento")
    return erros


LONGO = """VERSÃO LONGA (teste A/B): no perfil, Reels de 45 a 60 s tiveram mediana de 570 views contra 313 dos curtos.
Escreva o corpo com 7 a 9 frases: mais passos concretos e mais detalhes reais dos FATOS (nunca enchimento), mantendo
"Isso porque", "E olha isso" e "Ou seja"."""


def escrever(fatos: str, llm=gerar_json, tentativas: int = 3, extra: str = "", longo: bool = False) -> dict:
    extra = (extra + "\n" + LONGO) if longo else extra
    pedido = f"FATOS:\n{fatos}\n{extra}"
    for _ in range(tentativas):
        r = llm(SISTEMA, pedido)
        erros = problemas(r, max_corpo=9 if longo else 6)
        if not erros:
            # motivo para seguir (conversão de quem chegou pelo Reels): o link vem pelo comentário, o follow pela promessa
            r["cta"] = f"Comenta {r['palavra']} que eu te mando o link. E me segue: todo dia tem uma IA nova aqui."
            return r
        pedido = f"FATOS:\n{fatos}\n{extra}\n\nSEU ROTEIRO ANTERIOR TEVE PROBLEMAS, CORRIJA:\n- " + "\n- ".join(erros)
    raise RuntimeError("roteiro inválido: " + "; ".join(erros))


def prever(r: dict, gancho: int = 0, llm=None, corte: float = 7.5) -> dict:
    """Previsor de viral (Davi, 06/11, como o Virality da Higgsfield), ANTES de gastar o Claude animando: o Gemini dá
    nota ao gancho, clareza, retenção e compartilhamento. Nota abaixo de 7 troca a abertura e o texto da tela pelos
    que ele sugeriu. Falhar aqui nunca derruba a produção: o roteiro segue como estava."""
    try:
        sistema = segredos.texto("viral_nota")
        texto = (f"TEXTO NA TELA: {r.get('texto_tela', '')}\nABERTURA: {r['ganchos'][gancho]}\n"
                 f"CORPO: {' '.join(r['corpo'])}\nFECHAMENTO: {r.get('cta', '')}")
        p = (llm or gerar_json)(sistema, texto)
        nota = float(p.get("nota") or 0)
    except Exception as erro:
        print(f"previsor de viral falhou ({erro}); sigo com o roteiro")
        return r
    r["previsao"] = {k: p.get(k) for k in ("gancho", "clareza", "retencao", "compartilhavel", "seguir", "nota", "problema")}
    novo, tela = (p.get("novo_gancho") or "").strip(), (p.get("novo_texto_tela") or "").strip()
    if nota < corte and novo and len(novo.split()) <= 18:
        r["previsao"]["gancho_antigo"] = r["ganchos"][gancho]
        r["ganchos"][gancho] = novo
        if tela and len(tela.split()) <= 7:
            r["texto_tela"] = tela
    print(f"previsão de viral: {nota:.1f}/10 ({p.get('problema', '')})", flush=True)
    return r


def frases(roteiro: dict, gancho: int = 0) -> list[str]:
    return [roteiro["ganchos"][gancho]] + list(roteiro["corpo"]) + [roteiro["cta"]]
