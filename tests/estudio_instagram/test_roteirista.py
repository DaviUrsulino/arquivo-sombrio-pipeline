import json
from pathlib import Path

import pytest

from src.estudio_instagram import cenas_pixel, pauta, roteirista
from src.estudio_instagram.github_dados import DadosRepo
from src.estudio_instagram.llm import extrair_json

DADOS = DadosRepo("dono/ferramenta", 12000, "MIT", "Uma ferramenta de teste.", "https://github.com/dono/ferramenta")
README = "Ferramenta de teste. Instale com npx ferramenta init. Requer Node 22. Vem com 21 skills."
ICONES = {"code-xml", "zap", "clapperboard", "check", "terminal", "bot", "sparkles", "shield-check", "github", "star"}


def _resposta(narracao_extra="Funciona no terminal e em agentes.", numero=""):
    cenas = [{"narracao": "Essa ferramenta faz uma coisa bem útil pra quem programa.", "humor": "animado",
              "visual": {"tipo": "titulo_pixel", "linhas": [{"texto": "FERRAMENTA", "cor": "laranja", "tamanho": 120}]}},
             {"narracao": "Ela já tem mais de {estrelas:dono/ferramenta} estrelas no GitHub.", "visual": {"tipo": "contador", "repo": "dono/ferramenta"}},
             {"narracao": "Você escreve a entrada e ela gera a saída final.", "visual": {"tipo": "cadeia", "layout": "horizontal", "nos": [
                 {"icone": "code-xml", "rotulo": "Entrada", "cor": "azul"}, {"icone": "zap", "rotulo": "Ferramenta", "cor": "amarelo"}]}},
             {"narracao": "Dá pra instalar com um comando só no terminal.", "visual": {"tipo": "terminal", "comando": "npx ferramenta init"}},
             {"narracao": narracao_extra + numero, "visual": {"tipo": "icone_pixel", "icone": "check", "cor": "verde", "rotulo": "SIMPLES"}},
             {"narracao": "Ela é feita pra quem quer ganhar tempo no dia a dia.", "visual": {"tipo": "lista", "itens": ["Rápida", "Simples"]}},
             {"narracao": "O README pede Node versão 22 ou mais nova pra rodar.", "visual": {"tipo": "icone_pixel", "icone": "shield-check", "cor": "azul", "rotulo": "NODE 22"}},
             {"narracao": "A licença é MIT, então dá pra usar sem medo.", "visual": {"tipo": "icone_pixel", "icone": "sparkles", "cor": "amarelo", "rotulo": "LICENÇA MIT"}},
             {"narracao": "Resumindo, vale testar quando precisar dessa tarefa.", "visual": {"tipo": "icone_pixel", "icone": "bot", "cor": "roxo", "rotulo": "VALE TESTAR"}}]
    slides = [{"tipo": "capa", "linhas": [{"texto": "FERRAMENTA", "cor": "laranja", "tamanho": 100}], "subtitulo": "conheça"},
              {"tipo": "ponto", "fase": "O QUE É", "progresso": 0.25, "linhas": [{"texto": "O QUE É", "cor": "azul"}], "rotulo": "nota", "texto": "Texto."},
              {"tipo": "comando", "fase": "INSTALAR", "progresso": 0.5, "linhas": [{"texto": "COMO USAR", "cor": "verde"}], "comando": "npx ferramenta init", "texto": "nota", "rotulo": "terminal"},
              {"tipo": "ponto", "fase": "EXEMPLO", "progresso": 0.75, "linhas": [{"texto": "EXEMPLO", "cor": "laranja"}], "rotulo": "nota", "texto": "Texto."},
              {"tipo": "ponto", "fase": "BÔNUS", "progresso": 1.0, "linhas": [{"texto": "LICENÇA", "cor": "amarelo"}], "rotulo": "nota", "texto": "MIT."}]
    return {"subtitulo": "uma ferramenta útil", "destaques": ["ferramenta"], "cenas": cenas, "slides": slides}


def test_roteiro_valido_vira_pauta_que_passa_na_validacao():
    nova = roteirista.gerar_pauta(DADOS, README, "LINK", ICONES, llm=lambda s, u: _resposta())
    final = cenas_pixel.normalizar_pauta(nova)
    assert pauta.problemas(final, ICONES) == []
    assert final["cenas"][-1]["narracao"].startswith("Manda pra um amigo dev, segue o robô estagiário e comenta LINK")
    assert len(nova["slides"]) == 6 and nova["slides"][-1]["tipo"] == "cta"


def test_numero_inventado_volta_pro_modelo_e_ele_corrige():
    respostas = [_resposta(numero=" São 999 usuários."), _resposta()]
    pedidos = []

    def llm(sistema, usuario):
        pedidos.append(usuario)
        return respostas.pop(0)

    roteirista.gerar_pauta(DADOS, README, "LINK", ICONES, llm=llm)
    assert len(pedidos) == 2 and "999" in pedidos[1]


def test_desiste_depois_das_tentativas_com_os_problemas_na_mensagem():
    with pytest.raises(ValueError, match="999"):
        roteirista.gerar_pauta(DADOS, README, "LINK", ICONES, llm=lambda s, u: _resposta(numero=" São 999 usuários."), tentativas=2)


def test_pedir_para_comentar_na_narracao_e_barrado():
    erros = roteirista._problemas_roteiro(_resposta(narracao_extra="Comenta aqui se gostou."), DADOS, README, ICONES)
    assert any("comentar" in e for e in erros)


def test_normalizador_cria_ancoras_que_existem_na_narracao():
    cena = {"narracao": "Você escreve a entrada e ela gera a saída final.", "visual": {"tipo": "cadeia", "layout": "horizontal", "nos": [
        {"icone": "code-xml", "rotulo": "A", "cor": "azul"}, {"icone": "zap", "rotulo": "B", "cor": "amarelo"}]}}
    saida = cenas_pixel.normalizar_cena(cena, 1)
    assert len(saida["elementos"][0]["ancoras"]) == 2


def test_visual_desconhecido_e_rejeitado():
    with pytest.raises(ValueError):
        cenas_pixel.normalizar_cena({"narracao": "Uma frase qualquer aqui.", "visual": {"tipo": "foguete"}}, 1)


def test_extrair_json_aceita_cerca_de_markdown():
    assert extrair_json('```json\n{"a": {"b": 1}}\n```') == {"a": {"b": 1}}


def test_modelo_pode_recusar_ferramenta_de_risco_e_nao_tenta_de_novo():
    chamadas = []

    def llm(sistema, usuario):
        chamadas.append(1)
        return {"recusar": True, "motivo": "faz rodízio de contas para burlar cota"}

    with pytest.raises(roteirista.Recusado, match="rodízio"):
        roteirista.gerar_pauta(DADOS, README, "LINK", ICONES, llm=llm)
    assert len(chamadas) == 1


def test_foco_so_vale_enquanto_tem_restantes(tmp_path):
    import json as _json

    from src.estudio_instagram.escolher_pauta import gastar_foco, ler_foco

    arq = tmp_path / "foco.json"
    arq.write_text(_json.dumps({"restantes": 2, "buscas": ["ai video"]}))
    assert ler_foco(arq)["buscas"] == ["ai video"]
    gastar_foco(arq); gastar_foco(arq); gastar_foco(arq)
    assert _json.loads(arq.read_text())["restantes"] == 0 and ler_foco(arq) is None
    assert ler_foco(tmp_path / "nao_existe.json") is None


def test_venda_gira_um_roteiro_por_dia_e_nao_repete_dois_dias_seguidos(tmp_path):
    import json as _json
    from datetime import date

    from src.estudio_instagram.escolher_pauta import pauta_de_venda

    for i in range(3):
        (tmp_path / f"v{i}.json").write_text(_json.dumps({"titulo": f"v{i}"}))
    dias = [date(2026, 10, 18 + k) for k in range(4)]
    titulos = [pauta_de_venda(tmp_path, d)["titulo"] for d in dias]
    assert all(a != b for a, b in zip(titulos, titulos[1:])) and set(titulos) == {"v0", "v1", "v2"}
    assert pauta_de_venda(tmp_path / "nao_existe") is None


def test_fecho_proprio_nao_acrescenta_o_comenta_e_o_fecho_padrao_chama_para_a_bio():
    base = {"palavra_chave": "BIO", "cenas_roteiro": [{"narracao": "Quer fazer igual? O link está na bio.",
            "visual": {"tipo": "titulo_pixel", "linhas": [{"texto": "A", "cor": "branco"}]}}]}
    so_a_do_roteiro = cenas_pixel.normalizar_pauta({**base, "fecho_proprio": True})
    assert len(so_a_do_roteiro["cenas"]) == 1
    padrao = cenas_pixel.normalizar_pauta({**base, "palavra_chave": "LINK"})
    ultima = padrao["cenas"][-1]
    assert "link está na bio" in ultima["narracao"].lower() and ultima["elementos"][-1]["texto"] == "FAÇA IGUAL: LINK NA BIO"


def test_passos_vao_para_a_pauta_e_para_a_legenda():
    resposta = {**_resposta(), "passos": ["Rode npx ferramenta init", "Requer Node 22"]}
    nova = roteirista.gerar_pauta(DADOS, README, "LINK", ICONES, llm=lambda s, u: resposta)
    assert nova["passos"] == ["Rode npx ferramenta init", "Requer Node 22"]
    from src.estudio_instagram.pipeline import montar_legenda
    legenda = montar_legenda(nova, {})
    assert "Salva este vídeo" in legenda and "1. Rode npx ferramenta init" in legenda and "2. Requer Node 22" in legenda


def test_passo_com_numero_fora_do_readme_e_barrado():
    erros = roteirista._problemas_roteiro({**_resposta(), "passos": ["Dá 300% mais velocidade"]}, DADOS, README, ICONES)
    assert any("300" in e for e in erros)


def test_mais_de_4_passos_e_barrado():
    erros = roteirista._problemas_roteiro({**_resposta(), "passos": ["a", "b", "c", "d", "e"]}, DADOS, README, ICONES)
    assert any("passos" in e for e in erros)
