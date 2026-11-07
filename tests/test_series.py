from datetime import datetime, timedelta, timezone

from src.estudio_instagram import series


def test_conta_votos_ignora_acento_caixa_e_comentario_com_as_duas():
    coments = [{"midia_id": "m", "text": "Escada!!"}, {"midia_id": "m", "text": "vai de elevador"},
               {"midia_id": "m", "text": "ESCADA"}, {"midia_id": "m", "text": "escada ou elevador?"},
               {"midia_id": "outro", "text": "elevador"}]
    votos = series.contar_votos(coments, "m", ["ESCADA", "ELEVADOR"])
    assert votos == {"ESCADA": 2, "ELEVADOR": 1}
    assert series.vencedora(votos) == "ESCADA"
    assert series.vencedora({"VIDEO": 0, "SITE": 0}) == "VIDEO"
    assert series.contar_votos([{"midia_id": "m", "text": "vídeo"}], "m", ["VIDEO", "SITE"]) == {"VIDEO": 1, "SITE": 0}


def test_pendente_so_depois_de_12h_e_so_uma_vez():
    posts = {"m1": {"pauta": "pautas/viral/fila/2026-11-06-1843-historia-preso-no-shopping-cartoon-3d-short.json",
                    "publicado_em": "2026-11-07T01:30:00+00:00"}}
    cedo = datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc)
    assert series.pendente(cedo, posts, {}) is None
    tarde = cedo + timedelta(hours=5)
    p = series.pendente(tarde, posts, {})
    assert p["slug"] == "preso-no-shopping" and p["media_id"] == "m1"
    assert series.pendente(tarde, posts, {"preso-no-shopping": {}}) is None


def test_historia_real_sem_continuacao_nao_pede_parte_2():
    posts = {"m": {"pauta": "pautas/viral/fila/2026-11-06-1843-historia-phineas-gage-engraving.json",
                   "publicado_em": "2026-11-01T00:00:00+00:00"}}
    assert series.pendente(datetime(2026, 11, 7, tzinfo=timezone.utc), posts, {}) is None


def test_escreve_episodio_seguinte_com_mesmo_estilo(tmp_path, monkeypatch):
    monkeypatch.setattr(series, "HISTORIAS", tmp_path)
    ep = {"slug": "x", "serie": "x", "episodio": 1, "estilo": "cel-anime-80s", "direcao": "D", "opcoes": ["A", "B"],
          "roteiro": {"ganchos": ["g"], "corpo": ["c"], "cta": "k", "texto_tela": "T", "legenda": "L"}}
    llm = lambda *_: {"texto_tela": "T2", "ganchos": ["Vocês escolheram B."], "corpo": ["c2"], "cta": "k2",
                      "legenda": "Parte 2.", "opcoes": ["C", "D"], "fatos_continuacao": ""}
    destino = series.escrever_proximo({"slug": "x", "episodio": ep}, {"A": 1, "B": 3}, llm=llm)
    import json
    novo = json.loads(destino.read_text())
    assert destino.name == "x-ep2.json" and novo["estilo"] == "cel-anime-80s" and novo["direcao"] == "D"
    assert novo["escolha_anterior"] == "B" and novo["opcoes"] == ["C", "D"] and novo["roteiro"]["palavra"] == ""


def test_historia_marcada_pra_produzir_sai_uma_vez(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(series, "HISTORIAS", tmp_path)
    (tmp_path / "a.json").write_text(json.dumps({"produzir": True}))
    (tmp_path / "b.json").write_text(json.dumps({}))
    assert series.historia_para_produzir({}).name == "a.json"
    assert series.historia_para_produzir({"produzido:a": {}}) is None
