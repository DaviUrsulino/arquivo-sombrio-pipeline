import json

import pytest

from src.estudio_instagram import cenas_pixel, lista, pauta
from src.estudio_instagram.github_dados import DadosRepo
from src.estudio_instagram.roteirista import Recusado

ICONES = {"code-xml", "zap", "clapperboard", "check", "terminal", "bot", "sparkles", "shield-check", "github", "star"}
DADOS = [DadosRepo(f"dono/ferr{i}", 1000 * i, "MIT", f"Ferramenta {i} de teste.", f"https://github.com/dono/ferr{i}") for i in range(1, 6)]
READMES = {d.repo: f"Ferramenta {d.repo}. Instale com npx ferr. Requer Node 22. Vem com 21 skills." for d in DADOS}


def _resposta(**mudar):
    base = {
        "tema": "criar vídeo com IA", "gancho": ["5 REPOS PARA", "CRIAR VÍDEO"], "subtitulo": "cinco ferramentas grátis",
        "itens": [{"repo": d.repo, "rotulo": f"FERRAMENTA {i}", "falado": f"ferramenta {i}",
                   "frase": "Cria vídeo direto do terminal com agentes.", "icone": "zap"} for i, d in enumerate(DADOS, 1)],
        "excluir": [],
    }
    return {**base, **mudar}


def test_lista_valida_vira_pauta_pixel2_que_passa_na_validacao():
    nova = lista.gerar_pauta(DADOS, READMES, "LINK", ICONES, llm=lambda s, u: _resposta())
    assert nova["formato"] == "pixel2" and len(nova["itens"]) == 5 and len(nova["cenas_roteiro"]) == 6
    final = cenas_pixel.normalizar_pauta(nova)
    assert pauta.problemas(final, ICONES) == []
    assert final["cenas"][0]["narracao"].startswith("Cinco repositórios grátis para criar vídeo com IA")
    assert "Número um: ferramenta 1." in final["cenas"][1]["narracao"]
    assert final["cenas"][-1]["narracao"].startswith("Manda pra um amigo dev")


def test_legenda_lista_os_itens_e_pede_para_salvar():
    nova = lista.gerar_pauta(DADOS, READMES, "LINK", ICONES, llm=lambda s, u: _resposta())
    assert "Salva este vídeo" in nova["legenda"] and "1. Ferramenta 1:" in nova["legenda"] and "LINK" in nova["legenda"]


def test_numero_fora_do_readme_e_barrado():
    itens = _resposta()["itens"]
    itens[0]["frase"] = "Gera vídeo 300% mais rápido que o resto."
    erros = lista.problemas(_resposta(itens=itens), DADOS, READMES, ICONES)
    assert any("300" in e for e in erros)


def test_repo_que_nao_foi_recebido_e_barrado():
    itens = _resposta()["itens"]
    itens[0]["repo"] = "outro/inventado"
    assert any("não está entre os recebidos" in e for e in lista.problemas(_resposta(itens=itens), DADOS, READMES, ICONES))


def test_gancho_com_linha_grande_demais_e_barrado():
    erros = lista.problemas(_resposta(gancho=["CINCO REPOSITORIOS", "X"]), DADOS, READMES, ICONES)
    assert any("gancho" in e for e in erros)


def test_excluir_um_repo_ainda_gera_lista_com_4():
    itens = _resposta()["itens"][:4]
    nova = lista.gerar_pauta(DADOS, READMES, "LINK", ICONES, llm=lambda s, u: _resposta(itens=itens, excluir=[DADOS[4].repo]))
    assert len(nova["itens"]) == 4 and nova["cenas_roteiro"][0]["narracao"].startswith("Quatro")


def test_recusa_do_modelo_levanta_recusado():
    with pytest.raises(Recusado):
        lista.gerar_pauta(DADOS, READMES, "LINK", ICONES, llm=lambda s, u: {"recusar": True, "motivo": "x"})


def test_desiste_depois_de_3_tentativas_com_problemas():
    with pytest.raises(ValueError, match="lista não passou"):
        lista.gerar_pauta(DADOS, READMES, "LINK", ICONES, llm=lambda s, u: _resposta(gancho=["a", "b"]))


def test_dm_da_lista_leva_o_link_de_todos_os_repositorios(tmp_path, monkeypatch):
    from src.estudio_instagram import pipeline
    monkeypatch.setattr(pipeline, "RAIZ", tmp_path)
    (tmp_path / "pautas").mkdir()
    repos = {d.repo: d for d in DADOS}
    pipeline._registrar_links({"palavra_chave": "LINK"}, repos, {"reels": {"media_id": "m1"}, "carrossel_media_id": "m2"})
    salvo = json.loads((tmp_path / "pautas" / "links_por_post.json").read_text(encoding="utf-8"))
    mensagem = salvo["m1"]["mensagem"]
    assert all(d.url in mensagem for d in DADOS) and "1. ferr1:" in mensagem and salvo["m2"]["palavra"] == "LINK"


def test_frase_em_minuscula_do_modelo_sai_com_inicial_maiuscula():
    itens = _resposta()["itens"]
    itens[0]["frase"] = "cria vídeo direto do terminal."
    nova = lista.gerar_pauta(DADOS, READMES, "LINK", ICONES, llm=lambda s, u: _resposta(itens=itens))
    assert "Número um: ferramenta 1. Cria vídeo direto do terminal." in nova["cenas_roteiro"][1]["narracao"]
    assert "1. Ferramenta 1: Cria vídeo direto do terminal." in nova["legenda"]
