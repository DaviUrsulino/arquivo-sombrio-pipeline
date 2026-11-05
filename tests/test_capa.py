from PIL import Image

from src.estudio_instagram import capa


def test_titulo_cabe_em_tres_linhas_e_capa_tem_tamanho_de_reel():
    fonte, linhas = capa.caber("RALPH FIENNES PERDEU O 007 POR UM ERRO BOBO")
    assert 1 <= len(linhas) <= 3 and all(fonte.getlength(x) <= 960 for x in linhas)
    quadros = [Image.new("RGB", (1080, 1920), c) for c in ("red", "green", "blue")]
    assert capa.montar("titulo de teste", quadros).size == (1080, 1920)


def test_mesma_pauta_mesma_cor():
    assert capa.cor_para("GTA 6") == capa.cor_para("GTA 6") in capa.CORES
