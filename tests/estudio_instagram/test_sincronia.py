import pytest

from src.estudio_instagram.sincronia import (
    ADIANTAMENTO_S,
    PalavraNoTempo,
    blocos_de_legenda,
    normalizar,
    palavras_do_alinhamento,
    tempo_da_ancora,
)


def test_normalizar_tira_acento_pontuacao_e_caixa():
    assert normalizar("Código,") == "codigo"
    assert normalizar("GITHUB!") == "github"
    assert normalizar("...") == ""


def test_alinhamento_vira_tempo_da_primeira_letra_de_cada_palavra():
    caracteres = list("oi  mundo")
    inicios = [0.0, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7]
    assert palavras_do_alinhamento(caracteres, inicios) == [PalavraNoTempo(0.0, "oi"), PalavraNoTempo(0.3, "mundo")]


def test_alinhamento_vazio_ou_so_espaco():
    assert palavras_do_alinhamento([], []) == []
    assert palavras_do_alinhamento([" ", " "], [0.0, 0.1]) == []


PALAVRAS = [PalavraNoTempo(0.05, "Comenta"), PalavraNoTempo(0.6, "GITHUB"), PalavraNoTempo(1.2, "github.")]


def test_ancora_usa_primeira_ocorrencia_com_deslocamento_da_cena():
    assert tempo_da_ancora("github", PALAVRAS, deslocamento=10) == pytest.approx(10 + 0.6 - ADIANTAMENTO_S)


def test_ancora_nunca_fica_negativa():
    assert tempo_da_ancora("comenta", PALAVRAS) == 0.0


def test_ancora_ausente_e_erro_explicito():
    with pytest.raises(ValueError, match="não aparece"):
        tempo_da_ancora("instagram", PALAVRAS)


def test_legenda_agrupa_e_cada_bloco_vai_ate_o_proximo():
    palavras = [PalavraNoTempo(float(i), f"p{i}") for i in range(5)]
    blocos = blocos_de_legenda(palavras, fim=9.0, tamanho=2)
    # a palavra que sobraria sozinha ("p4") gruda no bloco anterior em vez de piscar solta na tela
    assert [b["texto"] for b in blocos] == ["p0 p1", "p2 p3 p4"]
    assert [(b["t"], b["fim"]) for b in blocos] == [(0.0, 2.0), (2.0, 9.0)]
