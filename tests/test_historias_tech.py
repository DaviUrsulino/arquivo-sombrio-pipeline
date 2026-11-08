from datetime import datetime, timedelta, timezone

import pytest

from src.estudio_instagram import historias_tech as ht


def test_uma_por_dia_e_tema_sem_repetir():
    agora = datetime(2026, 11, 8, 12, tzinfo=timezone.utc)
    assert ht.precisa({}, agora)
    feita = {"tech:knight-capital-45-minutos": {"quando": (agora - timedelta(hours=5)).isoformat()}}
    assert not ht.precisa(feita, agora)
    assert ht.proximo_tema(feita)[0] != "knight-capital-45-minutos"


def test_sem_fatos_nao_escreve():
    with pytest.raises(ValueError):
        ht.escrever("x", "X", 0, llm=lambda *_: {}, ler=lambda t: "curto")


def test_roteiro_vira_historia_pra_produzir():
    r = {"texto_tela": "T", "ganchos": ["g"], "corpo": ["c"], "cta": "k", "legenda": "L", "direcao": "D", "nota": 9}
    h = ht.escrever("x", "X", 1, llm=lambda *_: r, ler=lambda t: "f" * 2000)
    assert h["produzir"] and h["opcoes"] is None and h["estilo"] == ht.ESTILOS[1] and h["roteiro"]["palavra"] == ""
