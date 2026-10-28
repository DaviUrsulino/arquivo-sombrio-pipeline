from src.estudio_instagram import assunto_quente as aq

TRENDING = '''<article class="Box-row"><h2 class="h3 lh-condensed"><a href="/dono/agente-x">x</a></h2>
<p class="col-9 color-fg-muted my-1 pr-4">An AI agent that edits videos</p> 1,234 stars today</article>
<article class="Box-row"><h2 class="h3 lh-condensed"><a href="/dono/receitas">y</a></h2>
<p class="col-9 color-fg-muted my-1 pr-4">Cooking recipes</p> 900 stars today</article>'''


def test_trending_le_repo_estrelas_e_descricao():
    r = aq.github_trending(TRENDING)
    assert r["dono/agente-x"] == (1234.0, "An AI agent that edits videos")


def test_combinar_filtra_o_que_nao_e_ia_e_soma_fontes():
    t = aq.github_trending(TRENDING)
    hn = aq.hacker_news({"hits": [{"url": "https://github.com/dono/agente-x", "points": 300, "title": "Show HN"}]})
    itens = aq.combinar([t, hn])
    assert [i["repo"] for i in itens] == ["dono/agente-x"] and itens[0]["fontes"] == 2


def test_cache_do_dia_nao_coleta_de_novo(tmp_path):
    arq, chamadas = tmp_path / "q.json", []
    def coletor():
        chamadas.append(1)
        return [{"repo": "a/b", "nota": 1, "fontes": 1}]
    assert aq.do_dia("2026-10-28", arq, coletor) == ["a/b"]
    assert aq.do_dia("2026-10-28", arq, coletor) == ["a/b"] and len(chamadas) == 1


def test_link_do_github_ignora_paginas_que_nao_sao_repo():
    assert aq.hacker_news({"hits": [{"url": "https://github.com/features/copilot", "points": 9}]}) == {}
