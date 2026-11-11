"""Curiosidade com número que parece mentira — a frente de maior apelo universal.

Davi, 10/11: "umas curiosidades. O Vaticano é do tamanho de uma quadra da Asa Norte, uns 4 estádios de futebol.
O Isaac Newton ficou dois anos em casa na peste bubônica e inventou o cálculo e a ótica. É umas paradas assim que
a galera gosta de ver."

É o formato das contas de maior alcance que a gente mediu (`segredos/estudos/2026-11-10/`): @voceconstruiu
(mediana 87 mil, nada abaixo de 31 mil), @aprendisemquere (3,5 milhões), @quehistoriabsurda (546 mil),
@thiagonavega.ia (3 milhões). Nenhuma depende de nicho: dependem de um número que a pessoa não acredita.

A regra de fato continua inteira: os números saem da Wikipédia. A diferença é a COMPARAÇÃO DE ESCALA, que é o
que faz o vídeo ser compartilhado ("é do tamanho de 4 estádios") — e que o LLM não pode fazer de cabeça, porque
estimativa inventada vira número errado no ar. Aqui o CÓDIGO faz a conta com a medida real e entrega a frase
pronta; o prompt proíbe o roteirista de calcular qualquer coisa.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from . import series

# (slug, artigo da Wikipédia em inglês, ângulo que o roteirista tem que seguir)
TEMAS = [
    ("tamanho-do-vaticano", "Vatican City",
     "o país inteiro cabe dentro de uma cidade: compare a área dele com coisas que o brasileiro conhece"),
    ("newton-na-quarentena", "Isaac Newton",
     "os dois anos em que a peste fechou a universidade e ele, sozinho em casa, criou o cálculo e a ótica"),
    ("quanto-pesa-a-piramide", "Great Pyramid of Giza",
     "o tanto de pedra que foi empilhado à mão e quanto tempo levou"),
    ("a-mulher-dos-raios", "Marie Curie",
     "o que ela descobriu, e por que os cadernos dela ainda não podem ser tocados sem proteção"),
    ("o-mapa-que-parou-a-peste", "John Snow (physician)",
     "como um mapa simples de uma rua descobriu a causa de uma epidemia inteira"),
    ("a-biblioteca-que-sumiu", "Library of Alexandria",
     "o tamanho do acervo e o quanto do conhecimento antigo se perdeu junto"),
    ("o-relogio-de-10-mil-anos", "Clock of the Long Now",
     "um relógio construído para bater uma vez por ano durante dez mil anos"),
    ("profundidade-do-oceano", "Challenger Deep",
     "o ponto mais fundo do mar comparado com a altura das montanhas e dos prédios"),
]
INTERVALO = timedelta(hours=20)
PREFIXO = "curiosidade:"
NOTA_MINIMA = 7.0

# Referências de escala que qualquer brasileiro visualiza. Valores públicos e estáveis, em metro quadrado.
# (singular, plural, área) — o plural vem escrito porque "campo de futebol" + "s" vira "campo de futebols".
ESCALAS_AREA = [
    ("campo de futebol", "campos de futebol", 7_140),        # 105 x 68 m, medida oficial da FIFA
    ("quarteirão de cidade", "quarteirões de cidade", 10_000),  # 100 x 100 m
    ("Parque Ibirapuera", "Parques Ibirapuera", 1_580_000),
    ("ilha de Fernando de Noronha", "ilhas de Fernando de Noronha", 18_400_000),
]


def _numero(texto: str, padrao: str) -> float | None:
    m = re.search(padrao, texto, re.I)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


# Velocidades de quem atravessa o lugar. Davi, 10/11: "se tu rodar de bicicleta a 12 por hora, você demora 2
# minutos pra dar a volta — tem que ser umas paradas assim pra galera achar massa". É melhor que comparar área:
# "69 campos de futebol" é abstrato, "você atravessa a pé em 8 minutos" a pessoa sente no corpo.
ESCALAS_TEMPO = [("a pé", 5.0), ("de bicicleta", 12.0), ("de carro", 40.0)]


def comparacoes_de_tempo(fatos: str) -> list[str]:
    """Quanto tempo se leva para atravessar e para dar a volta no lugar, a partir da área real.

    Trata a área como um quadrado de lado igual à raiz: é aproximação honesta de ordem de grandeza, então o texto
    diz "mais ou menos". Sem área, nenhuma frase — nunca estimar distância que o artigo não dá."""
    km2 = _numero(fatos, r"([\d,.]+)\s*km2") or _numero(fatos, r"([\d,.]+)\s*square kilomet")
    if not km2:
        return []
    lado = km2 ** 0.5           # km de ponta a ponta, se fosse um quadrado
    volta = lado * 4            # dar a volta no contorno
    frases = []
    for nome, kmh in ESCALAS_TEMPO:
        for rotulo, distancia in (("atravessa", lado), ("dá a volta", volta)):
            minutos = round(distancia / kmh * 60)
            if 1 <= minutos <= 90:
                frases.append(f"{rotulo} {nome} em mais ou menos {minutos} minuto{'s' if minutos > 1 else ''}")
    return frases


def comparacoes_de_area(fatos: str) -> list[str]:
    """Frases de comparação prontas, calculadas com a área real do artigo. Lista vazia quando não há área —
    melhor nenhuma comparação do que uma comparação inventada."""
    km2 = _numero(fatos, r"([\d,.]+)\s*km2") or _numero(fatos, r"([\d,.]+)\s*square kilomet")
    if not km2:
        return []
    m2 = km2 * 1_000_000
    frases = []
    for singular, plural, tamanho in ESCALAS_AREA:
        vezes = round(m2 / tamanho)
        if 2 <= vezes <= 500:  # abaixo de 2 não impressiona, acima de 500 a pessoa não consegue visualizar
            frases.append(f"a área de {km2:g} km2 equivale a {vezes} {plural if vezes > 1 else singular}")
    return frases


def proximo_tema(estado: dict) -> tuple[str, str, str] | None:
    return next((t for t in TEMAS if f"{PREFIXO}{t[0]}" not in estado), None)


def precisa(estado: dict, agora: datetime | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    feitas = [datetime.fromisoformat(v["quando"]) for k, v in estado.items() if k.startswith(PREFIXO)]
    return not feitas or agora - max(feitas) >= INTERVALO


def escrever(slug: str, titulo: str, angulo: str, llm=None, ler=None, corte: float = NOTA_MINIMA) -> dict:
    from . import segredos
    from .historias_tech import fatos as ler_fatos
    from .llm import gerar_json
    import json as _json
    gerar = llm or gerar_json
    base = (ler or ler_fatos)(titulo)
    if len(base) < 1500:
        raise ValueError(f"artigo da Wikipédia curto demais ({len(base)} caracteres)")
    pedido = {"FATOS": base, "ANGULO": angulo,
              # tempo primeiro: "atravessa de bicicleta em 3 minutos" bate mais que "69 campos de futebol"
              "COMPARACOES": comparacoes_de_tempo(base) + comparacoes_de_area(base)}
    r = gerar(segredos.texto("curiosidade"), _json.dumps(pedido, ensure_ascii=False))
    ultima_nota = None
    for _ in range(2):
        if len(r.get("ganchos") or []) != 3:
            pedido["critica_do_editor"] = "preciso de exatamente 3 ganchos diferentes para o mesmo corpo"
        else:
            try:
                texto = (f"TEXTO NA TELA: {r['texto_tela']}\nABERTURA: {r['ganchos'][0]}\n"
                         f"CORPO: {' '.join(r['corpo'])}\nFECHAMENTO: {r['cta']}")
                nota = gerar(segredos.texto("viral_nota"), texto)
            except Exception as erro:
                print(f"previsor da curiosidade falhou ({erro}); sigo com o roteiro")
                break
            ultima_nota = float(nota.get("nota") or 0)
            print(f"curiosidade {slug}: nota {ultima_nota} ({nota.get('problema')})", flush=True)
            if ultima_nota >= corte:
                break
            pedido["critica_do_editor"] = nota.get("problema")
        pedido["roteiro_rejeitado"] = {k: r.get(k) for k in ("texto_tela", "ganchos", "corpo", "cta")}
        r = gerar(segredos.texto("curiosidade"), _json.dumps(pedido, ensure_ascii=False))
    if len(r.get("ganchos") or []) != 3:
        raise ValueError("o roteirista não entregou os 3 ganchos")
    # 10/11: a nota mínima existia mas não barrava nada, e um roteiro nota 5 ("parece uma aula de geografia")
    # ia virar 40 minutos de renderização. Roteiro reprovado não vira vídeo: a frente tenta de novo amanhã.
    if ultima_nota is not None and ultima_nota < corte:
        raise ValueError(f"roteiro reprovado pelo previsor (nota {ultima_nota}, mínimo {corte})")
    return {"slug": slug, "serie": slug, "episodio": 1, "opcoes": None, "produzir": True,
            "formato": "numero",  # o número é o herói: gráfico e comparação, nunca mascote (ver estilo_formato.py)
            "fonte": f"https://en.wikipedia.org/wiki/{titulo.replace(' ', '_')}",
            "direcao": "CURIOSIDADE COM NÚMERO. Sem mascote, sem personagem falando. " + (r.get("direcao") or ""),
            "roteiro": {"texto_tela": r["texto_tela"], "ganchos": r["ganchos"], "corpo": r["corpo"],
                        "cta": r["cta"], "legenda": r["legenda"], "palavra": ""}}


def gerar_se_preciso(agora: datetime | None = None):
    """Escreve a curiosidade do dia se faz 20 h da última. Caminho do roteiro, ou None."""
    import json as _json
    estado = series._ler(series.ESTADO)
    if not precisa(estado, agora):
        return None
    tema = proximo_tema(estado)
    if not tema:
        return None
    slug, titulo, angulo = tema
    try:
        c = escrever(slug, titulo, angulo)
    except Exception as erro:
        print(f"não consegui escrever a curiosidade {slug} ({erro})")
        return None
    destino = series.HISTORIAS / f"{slug}.json"
    destino.write_text(_json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    series.registrar(f"{PREFIXO}{slug}", destino.stem)
    return destino
