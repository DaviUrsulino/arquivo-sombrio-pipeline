"""Pauta: o arquivo JSON que descreve um post (Reels + carrossel) e a validação dele.

A validação roda antes de qualquer chamada paga (voz, render). Um erro aqui custa zero;
o mesmo erro descoberto depois da narração custa crédito do ElevenLabs.
"""

import json
import re
from pathlib import Path

from .sincronia import normalizar

CORES = {"laranja", "azul", "verde", "roxo", "vermelho", "amarelo", "branco"}
TIPOS = {
    "robo",
    "numero", "texto", "icone", "etiqueta", "cabecalho", "lista", "fluxo", "cartao", "barra", "comparacao",
    "destaque", "emoji", "card_prompt", "fluxo_icones", "selo", "personagem", "balao", "chips",
    "cartao_repo", "estrelas_gigante", "fluxo_linha",
    "hud", "titulo_pixel", "terminal", "selo_pixel",
    "icone_pixel", "cadeia", "niveis", "comparar", "celular", "banner_repo", "contador", "lista",
    "sala_pixel", "grade_pixel", "preco_pixel",
}
MARCADOR = re.compile(r"\{(estrelas:[\w.-]+/[\w.-]+|total_estrelas)\}")
MAX_CARACTERES_NARRACAO = 1500


def carregar(caminho: Path) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def _palavras(texto: str) -> set[str]:
    return {normalizar(p) for p in texto.split() if normalizar(p)}


def _icones_do_elemento(elemento: dict) -> list[str]:
    icones = [elemento["icone"]] if "icone" in elemento else []
    for lado in ("esquerda", "direita", "esq", "dir"):
        if lado in elemento and "icone" in elemento[lado]:
            icones.append(elemento[lado]["icone"])
    icones += [no["icone"] for no in elemento.get("nos", []) if isinstance(no, dict) and "icone" in no]
    icones += [item["icone"] for item in elemento.get("itens", []) if isinstance(item, dict) and "icone" in item]
    return icones


def _textos(no) -> list[str]:
    if isinstance(no, str):
        return [no]
    if isinstance(no, dict):
        return [t for v in no.values() for t in _textos(v)]
    if isinstance(no, list):
        return [t for v in no for t in _textos(v)]
    return []


def problemas(pauta: dict, icones_disponiveis: set[str]) -> list[str]:
    """Lista tudo que impediria o post de sair certo. Lista vazia = pauta válida."""
    erros = []
    for campo in ("titulo", "palavra_chave", "perfil", "voz", "capa", "itens", "cenas"):
        if campo not in pauta:
            erros.append(f"campo obrigatório ausente: {campo}")
    if erros:
        return erros

    repos = {item["repo"] for item in pauta["itens"]}
    for item in pauta["itens"]:
        if item.get("cor") not in CORES:
            erros.append(f"item {item.get('repo')}: cor inválida {item.get('cor')!r}")

    total = sum(len(c["narracao"]) for c in pauta["cenas"])
    if total > MAX_CARACTERES_NARRACAO:
        erros.append(f"narração com {total} caracteres passa do limite de {MAX_CARACTERES_NARRACAO}")

    for cena in pauta["cenas"]:
        nome = cena.get("id", "?")
        if cena.get("cor") not in CORES:
            erros.append(f"cena {nome}: cor inválida {cena.get('cor')!r}")
        falado = _palavras(cena["narracao"])
        for elemento in cena["elementos"]:
            tipo = elemento.get("tipo")
            if tipo not in TIPOS:
                erros.append(f"cena {nome}: tipo de elemento desconhecido {tipo!r}")
            ancoras = ([elemento["ancora"]] if "ancora" in elemento else []) + elemento.get("ancoras", [])
            if not ancoras:
                erros.append(f"cena {nome}: elemento {tipo} sem âncora")
            for ancora in ancoras:
                if normalizar(ancora) not in falado:
                    erros.append(f"cena {nome}: âncora {ancora!r} não aparece na narração")
            for icone in _icones_do_elemento(elemento):
                if icone not in icones_disponiveis:
                    erros.append(f"cena {nome}: ícone {icone!r} não existe em modelos/assets/icons")
            if "cor" in elemento and elemento["cor"] not in CORES:
                erros.append(f"cena {nome}: cor inválida {elemento['cor']!r}")
            if tipo == "cartao" and elemento.get("repo") and elemento["repo"] not in repos:
                erros.append(f"cena {nome}: cartão aponta para repositório fora da pauta {elemento['repo']!r}")

    for texto in _textos(pauta["capa"]) + _textos(pauta["cenas"]):
        for marcador in MARCADOR.findall(texto):
            if marcador.startswith("estrelas:") and marcador.split(":", 1)[1] not in repos:
                erros.append(f"marcador {{{marcador}}} aponta para repositório fora da pauta")

    if normalizar(pauta["palavra_chave"]) not in _palavras(pauta["cenas"][-1]["narracao"]):
        erros.append("a última cena precisa falar a palavra-chave do 'comenta'")
    return erros


def formatar_estrelas(n: int) -> str:
    """299123 -> '299 mil'; 1250 -> '1,2 mil'; 980 -> '980'."""
    if n >= 10_000:
        return f"{n // 1000} mil"
    if n >= 1000:
        return f"{n / 1000:.1f}".replace(".", ",").replace(",0", "") + " mil"
    return str(n)


def preencher_marcadores(texto: str, estrelas: dict[str, int]) -> str:
    """Troca {estrelas:dono/repo} e {total_estrelas} pelos números reais do GitHub."""
    def trocar(m):
        chave = m.group(1)
        if chave == "total_estrelas":
            return formatar_estrelas(sum(estrelas.values()))
        return formatar_estrelas(estrelas[chave.split(":", 1)[1]])
    return MARCADOR.sub(trocar, texto)


def preencher(no, estrelas: dict[str, int]):
    """Aplica `preencher_marcadores` em todos os textos de uma estrutura JSON."""
    if isinstance(no, str):
        return preencher_marcadores(no, estrelas)
    if isinstance(no, dict):
        return {k: preencher(v, estrelas) for k, v in no.items()}
    if isinstance(no, list):
        return [preencher(v, estrelas) for v in no]
    return no
