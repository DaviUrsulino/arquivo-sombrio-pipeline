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


def test_banco_tira_vencido_e_poe_assunto_do_momento_na_frente(tmp_path, monkeypatch):
    from datetime import datetime
    monkeypatch.setattr(maestro, "RAIZ", tmp_path)
    fila = tmp_path / "fila"
    for nome in ("2026-11-01-0300-produtora-velho.json", "2026-11-04-0300-produtora-a.json",
                 "2026-11-04-1100-em-alta-gta.json", "2026-11-03-0300-em-alta-esfriou.json"):
        _pauta(fila, nome)
    agora = datetime(2026, 11, 4, 18, 0, tzinfo=maestro.BRASILIA)
    assert maestro.disponiveis([], fila, agora) == ["fila/2026-11-04-1100-em-alta-gta.json", "fila/2026-11-04-0300-produtora-a.json"]


def test_em_alta_pula_politica_e_usa_so_manchetes():
    from src.estudio_instagram import em_alta
    candidatos = [{"termo": "Flávio Bolsonaro", "buscas": 9000, "manchetes": ["Senador viaja"], "fonte": "x"},
                  {"termo": "GTA 6", "buscas": 0, "manchetes": ["GTA 6 terá mais de 200 GB - Estadão"], "fonte": "x"}]
    vistos = []

    def llm(_sistema, lista):
        vistos.append(lista)
        return {"id": 0, "tema": "GTA 6", "angulo": "e se", "nota": 8}
    r = em_alta.escolher(candidatos, llm=llm, usados=[])
    assert "Bolsonaro" not in vistos[0] and r["chave"] == "GTA 6" and "200 GB" in r["fatos"]
    assert em_alta.escolher(candidatos, llm=lambda *_: {"id": 0, "nota": 4}, usados=[]) is None  # fraco não vira vídeo
