from src.estudio_instagram import guia_dm
from src.estudio_instagram.github_dados import DadosRepo
from src.estudio_instagram.llm import LLMIndisponivel

REPO = DadosRepo("microsoft/markitdown", 192000, "MIT", "Converte arquivos em Markdown", "https://github.com/microsoft/markitdown")


def test_guia_completo_com_passos_e_link():
    resp = {"resolve": "Transforma PDF e Excel em texto que a IA entende.",
            "passos": ["pip install markitdown", "markitdown arquivo.pdf > arquivo.md", "Cole o .md no ChatGPT"],
            "dica": "converta uma planilha e peça um resumo."}
    msg = guia_dm.gerar(REPO, "readme", llm=lambda s, u: resp)
    assert "1. pip install markitdown" in msg and REPO.url in msg and len(msg) <= guia_dm.LIMITE


def test_cai_no_link_simples_quando_llm_falha():
    def falha(s, u):
        raise LLMIndisponivel("x")
    assert guia_dm.gerar(REPO, "", llm=falha) == guia_dm.simples(REPO)


def test_cai_no_link_simples_com_resposta_incompleta():
    assert guia_dm.gerar(REPO, "", llm=lambda s, u: {"resolve": "x"}) == guia_dm.simples(REPO)


def test_mensagem_longa_demais_vira_simples():
    resp = {"resolve": "a" * 900, "passos": ["b", "c", "d"], "dica": "e"}
    assert guia_dm.gerar(REPO, "", llm=lambda s, u: resp) == guia_dm.simples(REPO)
