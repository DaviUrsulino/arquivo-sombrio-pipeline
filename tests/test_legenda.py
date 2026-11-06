"""Legenda com SEO do Instagram e o bug das cenas (cenas_roteiro ignoradas até 2026-11-04)."""

from src.estudio_instagram.pipeline import HASHTAGS, cenas_da_pauta, montar_legenda

PAUTA = {"titulo": "x: roteiro automático", "palavra_chave": "CORTE", "capa": {"subtitulo": "corta vídeo longo em reels com ia"},
         "cenas_roteiro": [{"narracao": "Fizeram um editor de vídeo que corta tudo sozinho."}], "passos": ["Rode npx corte init"]}


def test_gancho_de_cenas_roteiro_vira_a_primeira_linha():
    legenda = montar_legenda(PAUTA, {})
    assert legenda.splitlines()[0] == "Fizeram um editor de vídeo que corta tudo sozinho."
    assert legenda.splitlines()[1].startswith("Me segue e comenta CORTE")  # a palavra aparece antes do "mais"


def test_frase_de_tema_passos_e_no_maximo_5_hashtags_sem_emoji():
    legenda = montar_legenda(PAUTA, {})
    assert "Corta vídeo longo em reels com ia." in legenda and "1. Rode npx corte init" in legenda
    assert legenda.count("#") == len(HASHTAGS) <= 5
    assert all(ord(c) < 0x2600 for c in legenda)


def test_cenas_antigas_continuam_valendo():
    assert cenas_da_pauta({"cenas": [{"narracao": "a"}]}) == [{"narracao": "a"}]
    assert cenas_da_pauta({}) == []
