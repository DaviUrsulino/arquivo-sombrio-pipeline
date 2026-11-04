"""Repostagem com outro gancho: escolhe só post com gancho A, entre 48 h e 7 dias, abaixo da mediana, uma vez."""

import json
from datetime import datetime, timezone

from src.estudio_instagram import repostagem

AGORA = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


def _r(id_, hora, views):
    return {"id": id_, "hora": hora, "views": views}


REELS = [_r("velho", "2026-10-20T12:00:00+0000", 10), _r("novo", "2026-11-09T12:00:00+0000", 10),
         _r("ruim", "2026-11-07T12:00:00+0000", 15), _r("bom", "2026-11-07T13:00:00+0000", 5000),
         _r("b", "2026-11-06T12:00:00+0000", 20), _r("x1", "2026-11-05T12:00:00+0000", 900), _r("x2", "2026-11-05T13:00:00+0000", 800), _r("x3", "2026-11-05T14:00:00+0000", 700)]
MAPA = {i: {"pauta": f"pautas/{i}.json", "gancho": "A"} for i in ("velho", "novo", "ruim", "bom", "x1", "x2", "x3")}
MAPA["b"] = {"pauta": "pautas/b.json", "gancho": "B"}


def test_escolhe_so_gancho_a_na_janela_e_abaixo_da_mediana():
    assert repostagem.escolher(REELS, MAPA, set(), AGORA) == ["ruim"]


def test_nao_repete_post_ja_repostado():
    assert repostagem.escolher(REELS, MAPA, {"ruim"}, AGORA) == []


def test_pauta_com_gancho_troca_frase_e_titulo_e_marca_origem():
    pauta = {"titulo": "x: roteiro", "ganchos_alternativos": ["Fizeram engenharia reversa na sua placa de vídeo"],
             "cenas_roteiro": [{"narracao": "gancho velho", "visual": {"tipo": "titulo_pixel", "linhas": []}}, {"narracao": "2"}]}
    nova = repostagem.pauta_com_gancho(pauta, pauta["ganchos_alternativos"][0], "B", "123")
    assert nova["cenas_roteiro"][0]["narracao"].startswith("Fizeram")
    linhas = [l["texto"] for l in nova["cenas_roteiro"][0]["visual"]["linhas"]]
    assert all(len(l) <= 14 for l in linhas) and " ".join(linhas).startswith("FIZERAM")
    assert nova["gancho"] == "B" and nova["repost_de"] == "123" and nova["ganchos_alternativos"] == []
    assert pauta["cenas_roteiro"][0]["narracao"] == "gancho velho"  # original intacta


def test_agendar_grava_na_fila_e_registra(tmp_path, monkeypatch):
    (tmp_path / "pautas").mkdir()
    (tmp_path / "pautas" / "ruim.json").write_text(json.dumps({"titulo": "t", "ganchos_alternativos": ["Um dev sozinho fez isso aqui"],
                                                              "cenas_roteiro": [{"narracao": "a"}]}))
    (tmp_path / "mapa.json").write_text(json.dumps(MAPA))
    monkeypatch.setattr(repostagem, "RAIZ", tmp_path)
    monkeypatch.setattr(repostagem, "MAPA", tmp_path / "mapa.json")
    monkeypatch.setattr(repostagem, "REGISTRO", tmp_path / "reg.json")
    monkeypatch.setattr(repostagem, "FILA", tmp_path / "fila")
    criados = repostagem.agendar(REELS, AGORA)
    assert len(criados) == 1 and json.loads(criados[0].read_text())["repost_de"] == "ruim"
    assert repostagem.agendar(REELS, AGORA) == []  # registrado: não agenda de novo
