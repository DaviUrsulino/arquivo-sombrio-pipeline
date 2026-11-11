"""Estilo tem que casar com o FORMATO do vídeo, não só com o assunto (Davi, 10/11: 'usa os estilos a favor').

O caso que motivou: documentário no padrão do @marcondes.ai não tem personagem nenhum — é objeto-herói por cena.
Deixar o rodízio escolher um mascote cartoon ali quebra o vídeo mesmo com o assunto certo."""
from src.estudio_instagram import estilo_formato
from src.estudio_instagram.diretor import produtora


def _catalogo(*slugs):
    return [{"slug": s, "nome": s, "categoria": "x"} for s in slugs]


def test_documentario_nao_pega_mascote_cartoon():
    todos = _catalogo("hand-drawn-cartoon", "satellite-briefing", "rubber-hose", "teardown")
    slugs = [e["slug"] for e in estilo_formato.filtrar(todos, "documentario")]
    assert slugs == ["satellite-briefing", "teardown"]


def test_historia_pega_personagem_que_atua():
    todos = _catalogo("satellite-briefing", "cartoon-3d-short", "dataviz", "hand-drawn-cartoon")
    slugs = [e["slug"] for e in estilo_formato.filtrar(todos, "historia_personagem")]
    assert slugs == ["hand-drawn-cartoon", "cartoon-3d-short"]


def test_utilidade_mostra_a_tela():
    todos = _catalogo("living-screencast", "rubber-hose", "telestrator")
    slugs = [e["slug"] for e in estilo_formato.filtrar(todos, "utilidade")]
    assert slugs == ["living-screencast", "telestrator"]


def test_sem_formato_ou_sem_candidato_nao_trava_a_producao():
    todos = _catalogo("rubber-hose", "ukiyoe")
    assert estilo_formato.filtrar(todos, None) == todos
    assert estilo_formato.filtrar(todos, "documentario") == todos  # nenhum do mapa existe: usa o catálogo inteiro
    assert estilo_formato.filtrar(todos, "formato-que-nao-existe") == todos


def test_todo_formato_tem_motivo_escrito():
    for formato in estilo_formato.FORMATOS:
        assert len(estilo_formato.motivo(formato)) > 40
        assert estilo_formato.recomendados(formato)


def test_estilo_para_so_oferece_ao_llm_o_que_cabe_no_formato():
    """O LLM continua escolhendo, mas a lista que chega nele já veio filtrada pelo formato."""
    todos = _catalogo("hand-drawn-cartoon", "satellite-briefing", "teardown")
    vistos = {}

    def llm(_sistema, pedido):
        vistos["pedido"] = pedido
        return {"estilos": ["teardown"]}

    escolhido = produtora.estilo_para("tecnologia", {}, todos, llm=llm, fracos=set(), formato="documentario")
    assert escolhido["slug"] == "teardown"
    assert "hand-drawn-cartoon" not in vistos["pedido"]


def test_placar_do_topo_muda_com_o_formato():
    """O Reels de 1,9 milhão do @escolhas.app mantém o placar na tela o vídeo inteiro; o nosso briefing tem que
    pedir um placar que faça sentido pro formato, não um contador genérico."""
    from pathlib import Path
    estilo = {"slug": "pixel-rpg", "nome": "RPG"}
    historia = produtora.briefing(["f1"], estilo, Path("/tmp/x"), "P", formato="historia_personagem")
    numero = produtora.briefing(["f1"], estilo, Path("/tmp/x"), "P", formato="numero")
    generico = produtora.briefing(["f1"], estilo, Path("/tmp/x"), "P")
    assert "PLACAR FIXO NO TOPO" in historia
    assert "TENSÃO" in historia and "A CONTA" not in historia
    assert "A CONTA" in numero
    assert produtora.PLACAR_GENERICO in generico
