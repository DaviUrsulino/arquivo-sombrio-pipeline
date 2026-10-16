from src.estudio_instagram.concorrentes import PostConcorrente, buscas_do_dia, classificar_tema, temas_em_alta


def _post(legenda, comentarios=0):
    return PostConcorrente("alguem", "Video", "https://x", comentarios, 0, legenda)


def test_classificar_tema_reconhece_palavra_chave():
    assert classificar_tema("5 repositórios grátis pro Claude Code") == "repositorio"
    assert classificar_tema("Como economizar token no Claude") == "limite"
    assert classificar_tema("Foto da praia de férias") is None


def test_temas_em_alta_ignora_tema_com_so_um_post():
    posts = [_post("skill nova", comentarios=9999)]
    assert temas_em_alta(posts) == []


def test_temas_em_alta_ordena_pelo_comentario_somado():
    posts = [
        _post("skill 1", comentarios=10), _post("skill 2", comentarios=10),
        _post("repositório 1", comentarios=100), _post("repositório 2", comentarios=100),
    ]
    assert temas_em_alta(posts) == ["repositorio", "skill"]


def test_buscas_do_dia_prioriza_tema_quente_e_mantem_padrao_no_fim():
    posts = [_post("economize token", comentarios=50) for _ in range(3)]
    padrao = ["busca fixa 1", "busca fixa 2"]
    resultado = buscas_do_dia(posts, padrao, quantidade_temas=1)
    assert resultado[:2] == ["claude code token usage", "llm proxy rate limit"]
    assert set(padrao) <= set(resultado)


def test_buscas_do_dia_sem_tema_quente_devolve_so_o_padrao():
    assert buscas_do_dia([], ["a", "b"]) == ["a", "b"]
