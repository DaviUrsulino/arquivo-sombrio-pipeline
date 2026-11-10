"""Série de cotidiano (10/11): a frente de alcance. O que não pode faltar é o dilema com as duas opções —
sem elas na legenda ninguém comenta, e foi exatamente isso que zerou salvos/envios nas séries anteriores."""
from datetime import datetime, timedelta, timezone

import pytest

from src.estudio_instagram import historias_cotidiano as hc

BOM = {"texto_tela": "A CHAVE NAO GIRA", "ganchos": ["Você chega em casa e a chave não gira."],
       "corpo": ["c1", "c2", "c3", "c4", "c5", "c6"], "cta": "Comenta ENTRAR ou FUGIR. A parte 2 sai amanhã.",
       "legenda": "A chave não girou.\nComenta ENTRAR ou FUGIR. A mais votada vira a parte 2.",
       "opcoes": ["ENTRAR", "FUGIR"], "direcao": "D"}


def test_uma_por_dia_e_situacao_sem_repetir():
    agora = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    assert hc.precisa({}, agora)
    feita = {f"{hc.PREFIXO}porta-que-nao-abre": {"quando": (agora - timedelta(hours=5)).isoformat()}}
    assert not hc.precisa(feita, agora)
    assert hc.proxima_situacao(feita)[0] != "porta-que-nao-abre"


def test_nao_confunde_com_as_historias_de_tecnologia():
    """Os dois bancos usam o mesmo arquivo de estado; cada um só conta o seu prefixo."""
    agora = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    so_tech = {"tech:knight-capital-45-minutos": {"quando": (agora - timedelta(hours=1)).isoformat()}}
    assert hc.precisa(so_tech, agora)


@pytest.mark.parametrize("muda, erro_esperado", [
    ({"opcoes": ["ENTRAR"]}, "2 palavras"),
    ({"opcoes": ["ENTRAR", "FICAR NA PORTA"]}, "2 palavras"),
    ({"opcoes": ["entrar", "fugir"]}, "2 palavras"),
    ({"legenda": "A chave não girou. Segue o @ursulino.ia pra ver o final."}, "legenda precisa citar"),
    ({"cta": "Me segue que amanhã tem a parte 2."}, "cta precisa pedir o voto"),
    ({"corpo": ["c1", "c2"]}, "6 a 8 frases"),
])
def test_episodio_sem_dilema_valido_e_recusado(muda, erro_esperado):
    erros = hc.problemas({**BOM, **muda})
    assert any(erro_esperado in e for e in erros), erros


def test_roteiro_bom_vira_episodio_1_pra_produzir():
    h = hc.escrever("porta-que-nao-abre", "situação", 1, llm=lambda *_: {**BOM, "nota": 9})
    assert h["produzir"] and h["episodio"] == 1 and h["opcoes"] == ["ENTRAR", "FUGIR"]
    assert h["estilo"] == hc.ESTILOS[1] and h["roteiro"]["palavra"] == ""
    assert "sem nada de tecnologia" in h["direcao"]


def test_llm_que_nunca_entrega_dilema_nao_vira_video():
    ruim = {**BOM, "opcoes": []}
    with pytest.raises(ValueError):
        hc.escrever("x", "situação", 0, llm=lambda *_: ruim)
