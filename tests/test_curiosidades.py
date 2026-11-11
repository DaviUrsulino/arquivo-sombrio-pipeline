"""Curiosidade com número (Davi, 10/11: Vaticano, Newton).

O ponto delicado é a comparação de escala: é ela que faz o vídeo ser mandado para um amigo, e é exatamente onde
um LLM inventaria número. Por isso a conta é do código, com a medida real do artigo, e o prompt proíbe estimar."""
from datetime import datetime, timedelta, timezone

import pytest

from src.estudio_instagram import curiosidades as cur

VATICANO = "Vatican City ... has an area of 0.49 km2 and a population of about 882."


def test_compara_com_a_area_real_do_artigo():
    frases = cur.comparacoes_de_area(VATICANO)
    assert any("69 campos de futebol" in f for f in frases), frases
    assert all("0.49 km2" in f for f in frases)


def test_plural_escrito_na_mao_nunca_vira_campo_de_futebols():
    for f in cur.comparacoes_de_area(VATICANO):
        assert "futebols" not in f and "ãos" not in f


def test_sem_area_no_artigo_nao_inventa_comparacao():
    assert cur.comparacoes_de_area("Isaac Newton was an English mathematician born in 1643.") == []


def test_comparacao_que_ninguem_visualiza_fica_de_fora():
    """Abaixo de 2 não impressiona; acima de 500 a pessoa não consegue imaginar."""
    assert cur.comparacoes_de_area("area of 0.008 km2") == []          # 1 campo de futebol
    gigante = cur.comparacoes_de_area("area of 8515767 km2")           # Brasil
    assert all("campos de futebol" not in f for f in gigante)


def test_uma_por_dia_e_tema_sem_repetir():
    agora = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    assert cur.precisa({}, agora)
    feita = {f"{cur.PREFIXO}tamanho-do-vaticano": {"quando": (agora - timedelta(hours=4)).isoformat()}}
    assert not cur.precisa(feita, agora)
    assert cur.proximo_tema(feita)[0] != "tamanho-do-vaticano"


def test_roteiro_sai_como_formato_numero_e_com_3_ganchos():
    bom = {"texto_tela": "T", "ganchos": ["g1", "g2", "g3"], "corpo": ["c"] * 6, "cta": "k",
           "legenda": "L", "direcao": "D", "nota": 9}
    c = cur.escrever("x", "X", "ângulo", llm=lambda *_: bom, ler=lambda t: "f" * 2000)
    assert c["formato"] == "numero" and len(c["roteiro"]["ganchos"]) == 3
    assert "Sem mascote" in c["direcao"] and c["produzir"]


def test_sem_os_3_ganchos_nao_vira_video():
    ruim = {"texto_tela": "T", "ganchos": ["só um"], "corpo": ["c"] * 6, "cta": "k", "legenda": "L"}
    with pytest.raises(ValueError):
        cur.escrever("x", "X", "ângulo", llm=lambda *_: ruim, ler=lambda t: "f" * 2000)


def test_roteiro_reprovado_pelo_previsor_nao_vira_video():
    """10/11: a nota mínima existia mas não barrava nada. Um roteiro nota 5 ('parece uma aula de geografia')
    ia virar 40 minutos de renderização."""
    bom = {"texto_tela": "T", "ganchos": ["g1", "g2", "g3"], "corpo": ["c"] * 6, "cta": "k", "legenda": "L"}
    # o previsor devolve sempre 5.0: depois das tentativas, tem que abortar em vez de entregar
    with pytest.raises(ValueError, match="reprovado"):
        cur.escrever("x", "X", "ângulo", llm=lambda s, p: {"nota": 5.0, "problema": "aula"} if "FECHAMENTO" in p else bom,
                     ler=lambda t: "f" * 2000)


def test_roteiro_aprovado_passa_normal():
    bom = {"texto_tela": "T", "ganchos": ["g1", "g2", "g3"], "corpo": ["c"] * 6, "cta": "k", "legenda": "L"}
    c = cur.escrever("x", "X", "ângulo",
                     llm=lambda s, p: {"nota": 8.5, "problema": ""} if "FECHAMENTO" in p else bom,
                     ler=lambda t: "f" * 2000)
    assert c["produzir"] and c["formato"] == "numero"
