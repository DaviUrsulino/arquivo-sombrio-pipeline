import pytest

from src.estudio_instagram import identidade
from src.estudio_instagram.github_dados import DadosRepo

REPO = DadosRepo("microsoft/markitdown", 192000, "MIT", "Converte arquivos", "https://github.com/microsoft/markitdown")


def _cena(tipo, **extra):
    return {"fala": "A sua IA não lê planilha direito hoje.", "tipo": tipo, "titulo_a": "A SUA IA", "titulo_b": "NÃO LÊ", **extra}


def test_plano_valido_ganha_cena_final_de_comentario():
    resp = {"cenas": [_cena(t) for t in ["time", "folha", "celular", "conversor", "grade", "chat", "cracha"]]}
    plano = identidade.planejar("escritorio", REPO, "", "gancho", "TEXTO", llm=lambda s, u: resp)
    assert plano["cenas"][-1]["tipo"] == "comenta" and "TEXTO" in plano["cenas"][-1]["fala"]
    assert plano["repo"]["estrelas"] == 192000


def test_campos_aninhados_sao_achatados():
    resp = {"cenas": [_cena("chat", chat={"pergunta": "p", "resposta": "r"})] * 6}
    assert identidade.problemas("escritorio", resp) == []
    assert resp["cenas"][0]["pergunta"] == "p"


def test_tipo_fora_do_acervo_e_recusado_e_pede_correcao():
    chamadas = []
    def llm(s, u):
        chamadas.append(u)
        return {"cenas": [_cena("inventado")] * 6}
    with pytest.raises(RuntimeError):
        identidade.planejar("escritorio", REPO, "", "g", "TEXTO", llm=llm)
    assert len(chamadas) == 3 and "CORRIJA" in chamadas[-1]


def test_vila_exige_predio_contador_objeto():
    resp = {"cenas": [_cena(t) for t in ["aerea", "entrega", "passos", "resultado", "plateia", "placa", "notebook"]]}
    assert "faltam predio/contador/objeto" in identidade.problemas("vila", resp)
