"""Testes do script do pack de venda (produto/pack-pixel/montar.py). Não rodam npm nem renderizam."""

import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "produto" / "pack-pixel"


def _montar():
    import sys
    sys.path.insert(0, str(RAIZ))
    spec = importlib.util.spec_from_file_location("montar_pack", RAIZ / "montar.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


ICONES = {p.stem for p in (RAIZ / "modelo" / "icons").glob("*.svg")}


def test_exemplos_do_pack_sao_validos():
    m = _montar()
    for arquivo in (RAIZ / "exemplos").glob("*.json"):
        assert m.validar(json.loads(arquivo.read_text(encoding="utf-8")), ICONES) == [], arquivo.name


def test_validacao_explica_o_que_arrumar():
    m = _montar()
    erros = m.validar({"cenas": [
        {"narracao": "Oi.", "visual": {"tipo": "foguete"}},
        {"narracao": "Oi de novo.", "visual": {"tipo": "icone_pixel", "icone": "nao-existe", "cor": "marrom"}},
        {"narracao": "", "visual": {"tipo": "lista", "itens": ["a"]}},
    ]}, ICONES)
    texto = " | ".join(erros)
    assert "cena 1" in texto and "visual.tipo" in texto
    assert "nao-existe" in texto and "marrom" in texto and "cena 3" in texto


def test_tempos_estimados_crescem_com_o_tamanho_do_texto():
    m = _montar()
    cortes, palavras, total = m.tempos_estimados(["Curta.", "Uma frase bem mais comprida para ocupar muito mais tempo na tela do vídeo."])
    assert cortes[2] - cortes[1] > cortes[1] - cortes[0] and total == cortes[-1]
    assert all(a.t <= b.t for a, b in zip(palavras, palavras[1:]))
