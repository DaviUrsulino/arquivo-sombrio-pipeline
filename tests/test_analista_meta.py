from src.estudio_instagram import analista


def test_ritmo_da_meta_de_novembro():
    r = analista.ritmo_da_meta(453, "2026-11-10")
    assert r["falta"] == 547 and r["por_dia_necessario"] == 27.4 and r["por_dia_atual"] == 25.0


def test_tipo_do_post_pela_pauta():
    pautas = {"1": {"pauta": "pautas/viral/fila/2026-11-06-1843-historia-x.json"}, "2": {"pauta": "pautas/viral/fila_venda/v.json"}}
    assert analista.tipo_de("1", pautas) == "história" and analista.tipo_de("2", pautas) == "venda"
    assert analista.tipo_de("3", pautas) == "sem registro"
