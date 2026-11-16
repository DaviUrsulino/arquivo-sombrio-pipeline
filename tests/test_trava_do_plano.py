"""Davi, 15/11: a produtora gasta o mesmo plano Pro que ele usa de dia; só pode rodar de madrugada, até 03:30."""
import pytest
from datetime import datetime, timedelta, timezone

from src.estudio_instagram.diretor import produtora as pr

BR = timezone(timedelta(hours=-3))


@pytest.fixture(autouse=True)
def sem_pausa(monkeypatch):
    monkeypatch.setattr(pr, "PAUSA_ATE", (2026, 1, 1))


def test_pausa_pedida_pelo_davi(monkeypatch):
    monkeypatch.delenv("PRODUTORA_FORCAR", raising=False)
    monkeypatch.setattr(pr, "PAUSA_ATE", (2026, 11, 18))
    assert "pausa" in pr.trava_do_plano(t(2, 30, dia=17), {"producoes": []})
    assert "pausa" in pr.trava_do_plano(t(2, 30, dia=18), {"producoes": []})
    assert pr.trava_do_plano(t(2, 30, dia=19), {"producoes": []}) is None


def t(h, m=0, dia=16):
    return datetime(2026, 11, dia, h, m, tzinfo=BR)


def test_so_roda_na_janela_da_madrugada(monkeypatch):
    monkeypatch.delenv("PRODUTORA_FORCAR", raising=False)
    assert pr.trava_do_plano(t(2, 30), {"producoes": []}) is None
    assert pr.trava_do_plano(t(3, 29), {"producoes": []}) is None
    for hora in (t(1, 59), t(3, 30), t(8, 0), t(12, 0), t(21, 0)):
        assert "fora da janela" in pr.trava_do_plano(hora, {"producoes": []})


def test_maximo_por_noite_e_limite_acusado(monkeypatch):
    monkeypatch.delenv("PRODUTORA_FORCAR", raising=False)
    agora = t(3, 10)
    feitas = [{"quando_utc": (agora - timedelta(minutes=40 * i)).astimezone(timezone.utc).isoformat(), "minutos": 30}
              for i in range(1, 4)]
    assert "máximo" in pr.trava_do_plano(agora, {"producoes": feitas})
    limite = [{"quando_utc": (agora - timedelta(minutes=30)).astimezone(timezone.utc).isoformat(), "limite": True}]
    assert "limite" in pr.trava_do_plano(agora, {"producoes": limite})


def test_orcamento_da_semana(monkeypatch):
    monkeypatch.delenv("PRODUTORA_FORCAR", raising=False)
    agora = t(2, 30)
    velhas = [{"quando_utc": (agora - timedelta(days=d)).astimezone(timezone.utc).isoformat(), "minutos": 100} for d in (1, 2, 3, 4, 5)]
    assert "orçamento" in pr.trava_do_plano(agora, {"producoes": velhas})
    assert pr.trava_do_plano(agora, {"producoes": velhas[:3]}) is None


def test_forcar_so_com_variavel_explicita(monkeypatch):
    monkeypatch.setenv("PRODUTORA_FORCAR", "1")
    assert pr.trava_do_plano(t(14), {"producoes": []}) is None
