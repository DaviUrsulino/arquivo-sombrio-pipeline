"""2026-11-04 (Davi: "só dos novos"): todas as rodadas saem do banco de vídeos novos e a venda tem fila própria."""

import json

from src.estudio_instagram import maestro
from src.estudio_instagram.diretor import produtora


def _pauta(pasta, nome):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / nome).write_text("{}", encoding="utf-8")


def test_todas_as_rodadas_usam_o_banco():
    assert {h for h, _ in maestro.RODADAS} <= set(maestro.FILA_RODADAS)
    assert maestro.SO_VIDEOS_NOVOS


def test_venda_usa_a_fila_de_venda_e_as_outras_rodadas_nao(tmp_path, monkeypatch):
    monkeypatch.setattr(maestro, "RAIZ", tmp_path)
    monkeypatch.setattr(maestro, "FILA", tmp_path / "fila")
    monkeypatch.setattr(maestro, "FILA_VENDA", tmp_path / "fila_venda")
    _pauta(tmp_path / "fila", "a.json")
    _pauta(tmp_path / "fila_venda", "v.json")
    assert maestro.escolher_da_fila("venda", []) == "fila_venda/v.json"
    assert maestro.escolher_da_fila("pixel2", []) == "fila/a.json"
    assert maestro.escolher_da_fila("venda", ["fila_venda/v.json"]) == "fila/a.json"  # sem venda nova, não fura a grade
    assert maestro.escolher_da_fila("lista", ["fila/a.json"]) is None


def test_fatos_de_venda_vem_dos_roteiros_aprovados_sem_hashtag(tmp_path):
    (tmp_path / "v.json").write_text(json.dumps({"cenas_roteiro": [{"narracao": "Oito estilos."}],
                                                 "legenda": "O pack.\n\nComenta ESTUDIO\n\n#ia"}), encoding="utf-8")
    fatos = produtora.fatos_venda(tmp_path)
    assert "- Oito estilos." in fatos and "- O pack." in fatos
    assert "#" not in fatos and "Comenta" not in fatos
