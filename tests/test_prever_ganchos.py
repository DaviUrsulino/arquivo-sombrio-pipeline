"""O roteirista sempre escreveu 3 ganchos, mas só o primeiro era avaliado e os outros dois eram descartados.

No estudo de referências, o MESMO vídeo com 3 aberturas diferentes fez 32 mil, 122 mil e 941 mil views
(@gab.gouvea): 29x só pela primeira frase. Avaliar os 3 custa 2 chamadas de texto e nenhuma renderização."""
from src.estudio_instagram.diretor import roteiro


def _roteiro():
    return {"ganchos": ["fraco", "campeão", "mediano"], "corpo": ["c1", "c2"], "cta": "k", "texto_tela": "T"}


def _llm_por_gancho(notas):
    """Devolve a nota conforme o gancho que aparece na ABERTURA do pedido."""
    def llm(_sistema, pedido):
        for texto, nota in notas.items():
            if f"ABERTURA: {texto}" in pedido:
                return {"nota": nota, "problema": ""}
        return {"nota": 0, "problema": ""}
    return llm


def test_o_melhor_dos_tres_ganchos_e_o_que_vai_ao_ar():
    r = roteiro.prever(_roteiro(), llm=_llm_por_gancho({"fraco": 4.0, "campeão": 9.1, "mediano": 6.0}))
    assert r["ganchos"][0] == "campeão", "o vencedor tem que virar o índice 0, que é o que renderiza"
    assert sorted(r["ganchos_alternativos"]) == ["fraco", "mediano"]
    assert r["previsao"]["nota"] == 9.1


def test_ganchos_perdedores_ficam_guardados_pra_repostar():
    r = roteiro.prever(_roteiro(), llm=_llm_por_gancho({"fraco": 8.0, "campeão": 3.0, "mediano": 2.0}))
    assert r["ganchos"][0] == "fraco"
    assert len(r["ganchos_alternativos"]) == 2 and "fraco" not in r["ganchos_alternativos"]


def test_um_gancho_que_falha_nao_custa_os_outros():
    chamadas = {"n": 0}

    def llm(_sistema, pedido):
        chamadas["n"] += 1
        if "ABERTURA: campeão" in pedido:
            raise RuntimeError("503 do provedor")
        return {"nota": 7.0 if "ABERTURA: fraco" in pedido else 5.0, "problema": ""}

    r = roteiro.prever(_roteiro(), llm=llm)
    assert chamadas["n"] == 3
    assert r["ganchos"][0] == "fraco"  # o melhor entre os que responderam


def test_previsor_fora_do_ar_nao_derruba_a_producao():
    def llm(*_):
        raise RuntimeError("sem provedor")
    r = roteiro.prever(_roteiro(), llm=llm)
    assert r["ganchos"][0] == "fraco" and "previsao" not in r  # segue como estava, sem quebrar
