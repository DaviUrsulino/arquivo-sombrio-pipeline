import copy
from pathlib import Path

import pytest

from src.estudio_instagram import pauta
from src.estudio_instagram.montagem import MODELOS

ICONES = {p.stem for p in (MODELOS / "assets" / "icons").glob("*.svg")}
PAUTA_REAL = pauta.carregar(Path(__file__).parents[2] / "pautas" / "5-repos-claude-code.json")


@pytest.fixture
def valida():
    return copy.deepcopy(PAUTA_REAL)


def test_pauta_do_repositorio_e_valida(valida):
    assert pauta.problemas(valida, ICONES) == []


def test_campo_obrigatorio_ausente(valida):
    del valida["palavra_chave"]
    assert pauta.problemas(valida, ICONES) == ["campo obrigatório ausente: palavra_chave"]


def test_ancora_que_nao_e_falada(valida):
    valida["cenas"][0]["elementos"][0]["ancora"] = "abacaxi"
    assert any("'abacaxi' não aparece" in e for e in pauta.problemas(valida, ICONES))


def test_elemento_sem_ancora(valida):
    del valida["cenas"][0]["elementos"][0]["ancora"]
    assert any("sem âncora" in e for e in pauta.problemas(valida, ICONES))


def test_icone_inexistente(valida):
    valida["cenas"][-1]["elementos"][0]["icone"] = "unicornio"
    assert any("'unicornio' não existe" in e for e in pauta.problemas(valida, ICONES))


def test_cor_fora_da_paleta(valida):
    valida["itens"][0]["cor"] = "rosa"
    assert any("cor inválida 'rosa'" in e for e in pauta.problemas(valida, ICONES))


def test_marcador_de_repositorio_fora_da_pauta(valida):
    valida["capa"]["selo"] = "{estrelas:fulano/projeto}"
    assert any("fora da pauta" in e for e in pauta.problemas(valida, ICONES))


def test_ultima_cena_precisa_falar_a_palavra_chave(valida):
    valida["palavra_chave"] = "SKILL"
    assert "a última cena precisa falar a palavra-chave do 'comenta'" in pauta.problemas(valida, ICONES)


def test_narracao_longa_demais(valida):
    valida["cenas"][0]["narracao"] += " Não" + " blá" * 500
    assert any("passa do limite" in e for e in pauta.problemas(valida, ICONES))


@pytest.mark.parametrize("n, esperado", [
    (0, "0"), (999, "999"), (1000, "1 mil"), (1250, "1,2 mil"), (9999, "10 mil"),
    (10_000, "10 mil"), (298_951, "298 mil"),
])
def test_formatar_estrelas_nos_limites(n, esperado):
    assert pauta.formatar_estrelas(n) == esperado


def test_preencher_troca_marcadores_por_numero_real():
    estrelas = {"a/b": 298_951, "c/d": 63_327}
    texto = {"x": ["★ {estrelas:a/b}", "total {total_estrelas}"], "y": 3}
    assert pauta.preencher(texto, estrelas) == {"x": ["★ 298 mil", "total 362 mil"], "y": 3}
