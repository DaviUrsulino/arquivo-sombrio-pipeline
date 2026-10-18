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
    assert final["cenas"][-1]["narracao"].startswith("Comenta LINK")
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
