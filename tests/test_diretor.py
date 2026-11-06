"""Testes do estúdio com direção (src/estudio_instagram/diretor): regras do roteiro, conserto do storyboard,
efeitos sonoros em sincronia com o motor e catálogo igual dos dois lados (Python e JS). Sem rede."""

import re
from pathlib import Path

import pytest

from src.estudio_instagram.diretor import catalogo, direcao, montar, roteiro

MOTOR = Path(__file__).resolve().parents[1] / "src/estudio_instagram/modelos/assets/vendor/palco-motor.js"


def _roteiro_ok(**extra):
    r = {"ganchos": ["Fizeram um estúdio de games dentro do Claude", "Você perde horas fazendo jogo sozinho",
                     "Mais de quarenta mil pessoas já usam isso"],
         "corpo": ["Isso porque ele cria uma equipe de agentes", "Você descreve o jogo que quer",
                   "E a equipe planeja, programa e testa", "E olha isso, é de graça", "Ou seja, você só tem a ideia"],
         "palavra": "GAME", "texto_tela": "ESTÚDIO DE GAMES NO CLAUDE"}
    r.update(extra)
    return r


# ---------------------------------------------------------------- roteiro
def test_roteiro_valido_nao_tem_problemas():
    assert roteiro.problemas(_roteiro_ok()) == []


def test_gancho_comecando_com_conheca_e_recusado():
    r = _roteiro_ok(ganchos=["Conheça a ferramenta nova do Claude Code", "b c d e f", "g h i j k"])
    assert any("proibido" in e for e in roteiro.problemas(r))


def test_corpo_sem_isso_porque_e_ou_seja_e_recusado():
    r = _roteiro_ok(corpo=["Ele cria agentes pra você", "Você descreve o jogo", "A equipe programa tudo", "É de graça"])
    erros = roteiro.problemas(r)
    assert any("Isso porque" in e for e in erros) and any("Ou seja" in e for e in erros)


def test_escrever_tenta_de_novo_e_adiciona_cta():
    respostas = iter([_roteiro_ok(palavra="game"), _roteiro_ok()])
    r = roteiro.escrever("fatos", llm=lambda s, u: next(respostas))
    assert r["cta"] == "Comenta GAME que eu te mando o link. E me segue: todo dia tem uma IA nova aqui."
    assert roteiro.frases(r, 1)[0] == r["ganchos"][1] and roteiro.frases(r)[-1] == r["cta"]


# ---------------------------------------------------------------- direção
def _frases(n=7):
    base = ["Fizeram um estúdio inteiro", "Isso porque ele cria agentes", "Você descreve o jogo", "A equipe programa",
            "E olha isso, é grátis", "Ou seja, você só pensa", "Comenta GAME e me segue"]
    return base[:n]


def _cena(acao="aponta", objeto="monitor", camera="frente", mundo=None, **extra):
    c = {"titulo": "TÍTULO", "acao": acao, "objeto": objeto, "camera": camera, "emocao": "feliz", "transicao": "chicote", **extra}
    if mundo:
        c["mundo"] = mundo
    return c


def test_consertar_troca_valores_fora_do_catalogo_por_padroes():
    cenas = [_cena(acao="voa", objeto="dragao", camera="drone")] + [_cena(a, o) for a, o in
             [("segura", "celular"), ("digita", "notebook"), ("martela", "caixa"), ("comemora", "moedas"), ("pula", "trofeu"), ("acena", None)]]
    plano, erros = direcao.consertar({"mundo": "marte", "cenas": cenas}, _frases())
    assert plano["mundo"] == "palco"
    c0 = plano["cenas"][0]
    assert c0["acao"] in catalogo.ACOES and c0["camera"] in catalogo.CAMERAS and c0["objeto"] is None
    assert any("voa" in e for e in erros) and any("dragao" in e for e in erros)


def test_variedade_forca_gancho_mundos_cameras_e_hud_crescente():
    cenas = [_cena(a, o, camera="frente") for a, o in
             [("observa", "monitor"), ("segura", "celular"), ("digita", "notebook"), ("martela", "caixa"),
              ("comemora", "moedas"), ("pula", "trofeu"), ("acena", None)]]
    plano, _ = direcao.consertar({"mundo": "oficina", "hud": {"tipo": "contador", "rotulo": "X"}, "cenas": cenas}, _frases())
    cs = plano["cenas"]
    assert cs[0]["camera"] in ("aproxima", "baixo", "orbita") and cs[0]["acao"] in direcao.ACOES_DE_GANCHO
    mundos = {c.get("mundo") or plano["mundo"] for c in cs}
    assert len(mundos) >= 3 and "cor" in mundos
    for a, b in zip(cs, cs[1:-1]):
        assert a["camera"] != b["camera"]
    vals = [c["hud_valor"] for c in cs[:-1]]
    assert all(b > a for a, b in zip(vals, vals[1:]))
    assert cs[-1]["acao"] == "acena" and cs[-1]["objeto"] is None


def test_numero_de_cenas_errado_pede_nova_tentativa():
    _, erros = direcao.consertar({"cenas": [_cena()]}, _frases())
    assert erros and "exatamente 7" in erros[0]


# ---------------------------------------------------------------- som em sincronia com o motor
def test_eventos_de_martelo_e_carimbo_seguem_os_tempos_do_motor():
    falas = [{"t": 0.25}, {"t": 4.0}, {"t": 8.0}]
    cenas = [_cena("martela", "caixa"), _cena("carimba", "carimbo", transicao="voxel"), _cena("acena", None)]
    ev = montar.eventos_sfx(cenas, falas, "OI")
    baques = [e["t"] for e in ev if e["som"] == "baque"]
    assert baques == pytest.approx([0.68, 1.28, 1.88])  # 0,35 + 0,6k + 0,33 (palco-motor.js, ação martela)
    assert any(e["som"] == "impact" and e["t"] == pytest.approx(3.88 + 0.58) for e in ev)
    js = MOTOR.read_text(encoding="utf-8")
    assert "(lt - 0.35) / 0.6" in js and "seg(lt, 0.45, 0.6)" in js  # se mudar lá, mude em montar.eventos_sfx


def test_catalogo_python_e_motor_js_tem_os_mesmos_objetos_mundos_e_acoes():
    js = MOTOR.read_text(encoding="utf-8")
    bloco_obj = js[js.index("const OBJ = {"): js.index("// ação de ferramenta")]
    obj_js = set(re.findall(r"^    (\w+)\(", bloco_obj, re.M))
    assert set(catalogo.OBJETOS) <= obj_js, set(catalogo.OBJETOS) - obj_js
    bloco_mundo = js[js.index("const CONSTRUTOR = {"): js.index("const usados")]
    mundos_js = set(re.findall(r"^    (\w+)\(g\)", bloco_mundo, re.M))
    assert set(catalogo.MUNDOS) <= mundos_js, set(catalogo.MUNDOS) - mundos_js
    for acao in catalogo.ACOES:
        assert f'case "{acao}"' in js, acao
    for cam in catalogo.CAMERAS:
        assert f"{cam}: (k)" in js, cam


def test_versao_longa_aceita_corpo_maior_e_curta_nao():
    corpo = ["Isso porque ele cria agentes", "Você descreve o jogo", "A equipe planeja tudo", "Depois ela programa o jogo",
             "Em seguida ela testa", "E olha isso, é de graça", "Ou seja, você só tem a ideia"]
    assert roteiro.problemas(_roteiro_ok(corpo=corpo), max_corpo=9) == []
    assert roteiro.problemas(_roteiro_ok(corpo=corpo))
    assert roteiro.problemas(_roteiro_ok(texto_tela=""))  # sem gancho escrito na tela não passa


def test_previsor_troca_gancho_fraco_e_mantem_o_bom():
    from src.estudio_instagram.diretor import roteiro as rt
    base = lambda: {"ganchos": ["Este repositório usa embeddings vetoriais"], "corpo": ["a"], "cta": "c", "texto_tela": "REPO NOVO"}
    fraco = lambda *_: {"nota": 4, "problema": "técnico", "novo_gancho": "Essa IA faz seu trabalho de uma semana em 5 minutos",
                        "novo_texto_tela": "UMA SEMANA EM 5 MIN"}
    r = rt.prever(base(), llm=fraco)
    assert r["ganchos"][0].startswith("Essa IA") and r["texto_tela"] == "UMA SEMANA EM 5 MIN" and r["previsao"]["nota"] == 4
    bom = lambda *_: {"nota": 8.5, "novo_gancho": "outro"}
    assert rt.prever(base(), llm=bom)["ganchos"][0].startswith("Este repositório")
    def quebra(*_):
        raise RuntimeError("sem cota")
    assert rt.prever(base(), llm=quebra)["ganchos"][0].startswith("Este repositório")
