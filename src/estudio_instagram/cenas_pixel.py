"""Converte o roteiro "por frase" do molde pixel2 no formato de cenas do pipeline.

O roteiro (escrito à mão ou por LLM) só diz, para cada frase falada, qual visual aparece. Aqui
a gente completa o que é mecânico: a posição vertical padrão de cada visual e as âncoras (a
palavra falada que dispara cada elemento), sorteando palavras que existem na própria narração.
Assim quem escreve o roteiro não precisa saber de tempo nem de coordenada, e a validação de
`pauta.problemas` continua valendo.
"""

import re

from .sincronia import normalizar

# Quantas âncoras (palavras que disparam algo na tela) cada visual precisa.
def _quantas_ancoras(visual: dict) -> tuple[int, bool]:
    """Devolve (quantidade, lista). `lista=False` significa uma âncora só, no campo `ancora`."""
    tipo = visual["tipo"]
    if tipo == "cadeia":
        return len(visual["nos"]), True
    if tipo == "niveis":
        return len(visual["itens"]), True
    if tipo == "lista":
        return len(visual["itens"]), True
    if tipo == "comparar":
        return 2, True
    if tipo == "celular":
        return 2, True
    if tipo == "terminal":
        return 2, True
    return 1, False


# Posição vertical padrão (o robô anda em y=1320, a legenda fica em y=1590).
Y_PADRAO = {
    "titulo_pixel": 300, "icone_pixel": 380, "cadeia": 520, "niveis": 460, "comparar": 320,
    "celular": 200, "banner_repo": 300, "contador": 340, "lista": 380, "terminal": 420, "selo_pixel": 900,
}
HUMORES = {"normal", "feliz", "animado", "pensando"}
TIPOS_VISUAIS = set(Y_PADRAO)


def _palavras_da_narracao(narracao: str) -> list[str]:
    """Palavras que viram âncora: sem pontuação, com pelo menos 3 letras (evita 'o', 'de', 'e')."""
    achadas = []
    for bruta in narracao.split():
        n = normalizar(bruta)
        if len(n) >= 3 and n not in achadas:
            achadas.append(n)
    return achadas


def _espalhar(palavras: list[str], quantas: int) -> list[str]:
    """Escolhe `quantas` palavras bem espalhadas pela frase, a primeira bem no começo."""
    if not palavras:
        raise ValueError("narração sem palavra utilizável como âncora")
    if quantas == 1:
        return [palavras[0]]
    passo = max(1, len(palavras) // quantas)
    escolhidas = [palavras[min(i * passo, len(palavras) - 1)] for i in range(quantas)]
    return escolhidas


def normalizar_cena(cena: dict, indice: int) -> dict:
    visual = dict(cena["visual"])
    if visual.get("tipo") not in TIPOS_VISUAIS:
        raise ValueError(f"cena {indice}: visual desconhecido {visual.get('tipo')!r}")
    palavras = _palavras_da_narracao(cena["narracao"])
    quantas, lista = _quantas_ancoras(visual)
    escolhidas = _espalhar(palavras, quantas)
    visual.setdefault("y", Y_PADRAO[visual["tipo"]])
    if "ancora" not in visual and "ancoras" not in visual:
        if lista:
            visual["ancoras"] = escolhidas
        else:
            visual["ancora"] = escolhidas[0]
    if not lista and "t" not in visual:
        visual["t"] = 0.1
    humor = cena.get("humor", "normal")
    return {
        "id": str(indice),
        "cor": cena.get("cor", "laranja"),
        "narracao": cena["narracao"],
        "humor": humor if humor in HUMORES else "normal",
        "elementos": [visual],
    }


def cena_final(palavra_chave: str) -> dict:
    """Última cena, sempre igual: o 'comenta PALAVRA' que o bot responde."""
    return {
        "narracao": f"Segue o robô estagiário e comenta {palavra_chave} que eu te mando o link do repositório. E quer aprender a fazer vídeos assim? O link está na bio.",
        "humor": "animado",
        "visual": {
            "tipo": "titulo_pixel", "y": 330,
            "linhas": [{"texto": "SIGA E COMENTE", "cor": "branco", "tamanho": 84},
                       {"texto": palavra_chave, "cor": "verde", "tamanho": 150}],
        },
    }


def normalizar_pauta(pauta: dict) -> dict:
    """Pauta no formato `pixel2` (cenas com `visual`) -> pauta no formato que o pipeline monta."""
    palavra = pauta["palavra_chave"]
    # `fecho_proprio`: o roteiro já traz a chamada final (ex.: vídeo de venda com "link na bio"),
    # então não acrescenta o "comenta PALAVRA".
    cenas = list(pauta["cenas_roteiro"]) + ([] if pauta.get("fecho_proprio") else [cena_final(palavra)])
    saida = dict(pauta)
    saida["cenas"] = [normalizar_cena(c, i) for i, c in enumerate(cenas, start=1)]
    if not pauta.get("fecho_proprio"):
        # A cena final também ganha o selo, depois da primeira (não precisa de âncora própria no roteiro).
        saida["cenas"][-1]["elementos"].append({
            "tipo": "selo_pixel", "texto": "FAÇA IGUAL: LINK NA BIO", "y": 840,
            "ancora": "bio",
        })
    saida.setdefault("destaques", [])
    return saida
