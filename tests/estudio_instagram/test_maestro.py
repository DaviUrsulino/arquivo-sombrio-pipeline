from datetime import datetime

from src.estudio_instagram.maestro import BRASILIA, decidir


def _t(hhmm, dia="2026-10-19"):
    return datetime.fromisoformat(f"{dia}T{hhmm}:00").replace(tzinfo=BRASILIA)


def test_dispara_a_rodada_quando_chega_a_hora():
    formato, estado = decidir(_t("07:31"), {})
    assert formato == "pixel2" and "07:30" in estado["feitos"]


def test_nao_dispara_antes_da_hora_nem_repete():
    assert decidir(_t("07:00"), {})[0] is None
    _, estado = decidir(_t("07:31"), {})
    assert decidir(_t("07:35"), estado)[0] is None


def test_rodada_de_venda_e_a_das_19h():
    estado = {"dia": "2026-10-19", "feitos": {"07:30": "x", "11:30": "x", "15:30": "x"}}
    assert decidir(_t("19:05"), estado)[0] == "venda"


def test_acordar_muito_depois_da_hora_perde_a_rodada_em_vez_de_empilhar():
    formato, estado = decidir(_t("14:00"), {})
    assert formato is None
    assert estado["feitos"] == {"07:30": "perdida", "11:30": "perdida"}


def test_nunca_dispara_duas_rodadas_em_menos_de_20_minutos():
    estado = {"dia": "2026-10-19", "feitos": {"07:30": "x", "11:30": "x", "15:30": "x"}, "ultimo_disparo": _t("19:00").isoformat()}
    assert decidir(_t("19:10"), estado)[0] is None  # a de 19:00 já saiu há 10 min; nada novo mesmo


def test_dia_novo_zera_o_estado():
    velho = {"dia": "2026-10-18", "feitos": {"07:30": "x", "22:00": "x"}}
    formato, estado = decidir(_t("07:40", "2026-10-19"), velho)
    assert formato == "pixel2" and estado["dia"] == "2026-10-19" and list(estado["feitos"]) == ["07:30"]
