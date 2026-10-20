from datetime import datetime

from src.estudio_instagram.maestro import BRASILIA, RODADAS, decidir
from src.estudio_instagram import maestro


def _t(hhmm, dia="2026-10-19"):
    return datetime.fromisoformat(f"{dia}T{hhmm}:00").replace(tzinfo=BRASILIA)


def _mais(hhmm, minutos):
    h, m = map(int, hhmm.split(":"))
    total = h * 60 + m + minutos
    return f"{total // 60:02d}:{total % 60:02d}"


def test_quatro_rodadas_nos_horarios_de_ouro_com_a_de_venda_no_horario_nobre():
    horas = [h for h, _ in RODADAS]
    assert horas == sorted(horas) and len(horas) == 4
    assert [f for h, f in RODADAS if f == "venda"] == ["venda"]
    gaps = [int(b[:2]) * 60 + int(b[3:]) - int(a[:2]) * 60 - int(a[3:]) for a, b in zip(horas, horas[1:])]
    assert min(gaps) >= maestro.INTERVALO_MIN_MIN  # nunca duas rodadas em menos de 2 h


def test_dispara_a_rodada_quando_chega_a_hora():
    hora, formato_esperado = RODADAS[0]
    formato, estado = decidir(_t(_mais(hora, 1)), {})
    assert formato == formato_esperado and hora in estado["feitos"]


def test_nao_dispara_antes_da_hora_nem_repete():
    hora = RODADAS[0][0]
    assert decidir(_t(_mais(hora, -30)), {})[0] is None
    _, estado = decidir(_t(_mais(hora, 1)), {})
    assert decidir(_t(_mais(hora, 5)), estado)[0] is None


def test_rodada_de_venda_dispara_no_horario_dela():
    hora_venda = next(h for h, f in RODADAS if f == "venda")
    anteriores = {h: "x" for h, _ in RODADAS if h < hora_venda}
    estado = {"dia": "2026-10-19", "feitos": anteriores}
    assert decidir(_t(_mais(hora_venda, 5)), estado)[0] == "venda"


def test_acordar_muito_depois_da_hora_perde_a_rodada_em_vez_de_empilhar():
    hora = RODADAS[1][0]
    agora = _mais(hora, int(maestro.TOLERANCIA_ATRASO.total_seconds() // 60) + 30)
    formato, estado = decidir(_t(agora), {})
    assert formato is None
    assert estado["feitos"][RODADAS[0][0]] == "perdida" and estado["feitos"][hora] == "perdida"


def test_nunca_dispara_duas_rodadas_em_menos_de_2_horas():
    hora = RODADAS[1][0]
    estado = {"dia": "2026-10-19", "feitos": {RODADAS[0][0]: "x"}, "ultimo_disparo": _t(_mais(hora, -30)).isoformat()}
    assert decidir(_t(_mais(hora, 5)), estado)[0] is None  # a anterior saiu há 35 min


def test_dia_novo_zera_o_estado():
    velho = {"dia": "2026-10-18", "feitos": {h: "x" for h, _ in RODADAS}}
    hora = RODADAS[0][0]
    formato, estado = decidir(_t(_mais(hora, 10), "2026-10-19"), velho)
    assert formato == RODADAS[0][1] and estado["dia"] == "2026-10-19" and list(estado["feitos"]) == [hora]


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
