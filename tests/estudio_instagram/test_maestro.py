from datetime import datetime

from src.estudio_instagram.maestro import BRASILIA, RODADAS, decidir
from src.estudio_instagram import maestro


def _t(hhmm, dia="2026-10-19"):
    return datetime.fromisoformat(f"{dia}T{hhmm}:00").replace(tzinfo=BRASILIA)


def test_modo_seguro_sao_so_tres_rodadas_com_a_de_venda_no_horario_nobre():
    assert [h for h, _ in RODADAS] == ["09:00", "14:00", "19:00"] and RODADAS[-1][1] == "venda"


def test_dispara_a_rodada_quando_chega_a_hora():
    formato, estado = decidir(_t("09:01"), {})
    assert formato == "pixel2" and "09:00" in estado["feitos"]


def test_nao_dispara_antes_da_hora_nem_repete():
    assert decidir(_t("08:30"), {})[0] is None
    _, estado = decidir(_t("09:01"), {})
    assert decidir(_t("09:05"), estado)[0] is None


def test_rodada_de_venda_e_a_das_19h():
    estado = {"dia": "2026-10-19", "feitos": {"09:00": "x", "14:00": "x"}}
    assert decidir(_t("19:05"), estado)[0] == "venda"


def test_acordar_muito_depois_da_hora_perde_a_rodada_em_vez_de_empilhar():
    formato, estado = decidir(_t("17:00"), {})
    assert formato is None
    assert estado["feitos"] == {"09:00": "perdida", "14:00": "perdida"}


def test_nunca_dispara_duas_rodadas_em_menos_de_2_horas():
    estado = {"dia": "2026-10-19", "feitos": {"09:00": "x"}, "ultimo_disparo": _t("13:30").isoformat()}
    assert decidir(_t("14:05"), estado)[0] is None  # a anterior saiu há 35 min


def test_dia_novo_zera_o_estado():
    velho = {"dia": "2026-10-18", "feitos": {"09:00": "x", "19:00": "x"}}
    formato, estado = decidir(_t("09:10", "2026-10-19"), velho)
    assert formato == "pixel2" and estado["dia"] == "2026-10-19" and list(estado["feitos"]) == ["09:00"]


def test_proxima_da_fila_pula_as_ja_usadas(tmp_path, monkeypatch):
    monkeypatch.setattr(maestro, "RAIZ", tmp_path)
    fila = tmp_path / "pautas" / "viral" / "fila"
    fila.mkdir(parents=True)
    (fila / "01-a.json").write_text("{}")
    (fila / "02-b.json").write_text("{}")
    assert maestro.proxima_da_fila([], fila) == "pautas/viral/fila/01-a.json"
    assert maestro.proxima_da_fila(["pautas/viral/fila/01-a.json"], fila) == "pautas/viral/fila/02-b.json"
    assert maestro.proxima_da_fila(["pautas/viral/fila/01-a.json", "pautas/viral/fila/02-b.json"], fila) is None


def test_decidir_guarda_a_fila_usada_ao_virar_o_dia():
    ontem = {"dia": "2026-10-19", "feitos": {"09:00": "x"}, "fila_usadas": ["a.json"]}
    _, novo = maestro.decidir(datetime(2026, 10, 20, 9, 5, tzinfo=maestro.BRASILIA), ontem)
    assert novo["fila_usadas"] == ["a.json"]
