import json

import pytest

from src.estudio_instagram import pauta, selecao
from src.estudio_instagram.github_dados import DadosRepo
from src.estudio_instagram.historico import carregar, registrar
from src.estudio_instagram.montagem import MODELOS

ICONES = {p.stem for p in (MODELOS / "assets" / "icons").glob("*.svg")}


def _repo(n, estrelas=1000):
    return DadosRepo(f"dono/projeto{n}", estrelas, "MIT", f"Faz a coisa número {n} muito bem.", "https://github.com/x")


@pytest.mark.parametrize("quantidade", [3, 4, 5])
def test_pauta_gerada_sempre_passa_na_validacao(quantidade):
    repos = [_repo(i) for i in range(quantidade)]
    p = selecao.montar_pauta(repos, titulo="teste")
    assert pauta.problemas(p, ICONES) == []


@pytest.mark.parametrize("n", [0, 1, 2, 6])
def test_pauta_recusa_quantidade_fora_de_3_a_5(n):
    with pytest.raises(ValueError, match="3 a 5"):
        selecao.montar_pauta([_repo(i) for i in range(n)], titulo="teste")


def test_pauta_usa_a_palavra_chave_pedida():
    p = selecao.montar_pauta([_repo(0), _repo(1), _repo(2)], titulo="t", palavra_chave="SKILL")
    assert p["palavra_chave"] == "SKILL"
    assert "SKILL" in p["cenas"][-1]["narracao"]


def test_pauta_preenchida_mostra_estrelas_reais():
    repos = [_repo(0, estrelas=123_456), _repo(1, estrelas=1), _repo(2, estrelas=1)]
    p = selecao.montar_pauta(repos, titulo="t")
    estrelas = {r.repo: r.estrelas for r in repos}
    preenchida = pauta.preencher(p, estrelas)
    assert preenchida["itens"][0]["texto"] == "com 123 mil estrelas no GitHub"
    assert "123 mil" in preenchida["cenas"][0]["elementos"][3]["texto"]


def test_escolher_repos_ignora_quem_ja_virou_post(tmp_path):
    arquivo = tmp_path / "historico.json"
    registrar(["dono/projeto0"], arquivo)
    candidatos = [_repo(0, 500), _repo(1, 300), _repo(2, 900)]

    escolhidos = selecao.escolher_repos(candidatos, quantidade=2, arquivo_historico=arquivo)

    assert [r.repo for r in escolhidos] == ["dono/projeto2", "dono/projeto1"]


def test_historico_registra_e_persiste(tmp_path):
    arquivo = tmp_path / "historico.json"
    assert carregar(arquivo) == set()
    registrar(["a/b"], arquivo)
    registrar(["c/d"], arquivo)
    assert carregar(arquivo) == {"a/b", "c/d"}
