"""2026-11-04 (Davi: "só dos novos"): todas as rodadas saem do banco de vídeos novos e a venda tem fila própria."""

import json

from src.estudio_instagram import maestro
from src.estudio_instagram.diretor import produtora


def _pauta(pasta, nome):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / nome).write_text("{}", encoding="utf-8")


def test_todas_as_rodadas_usam_o_banco():
    assert {h for h, _ in maestro.RODADAS} <= set(maestro.FILA_RODADAS)
    assert maestro.SO_VIDEOS_NOVOS


def test_venda_usa_a_fila_de_venda_e_as_outras_rodadas_nao(tmp_path, monkeypatch):
    monkeypatch.setattr(maestro, "RAIZ", tmp_path)
    monkeypatch.setattr(maestro, "FILA", tmp_path / "fila")
    monkeypatch.setattr(maestro, "FILA_VENDA", tmp_path / "fila_venda")
    _pauta(tmp_path / "fila", "a.json")
    _pauta(tmp_path / "fila_venda", "v.json")
    assert maestro.escolher_da_fila("venda", []) == "fila_venda/v.json"
    assert maestro.escolher_da_fila("pixel2", []) == "fila/a.json"
    assert maestro.escolher_da_fila("venda", ["fila_venda/v.json"]) == "fila/a.json"  # sem venda nova, não fura a grade
    assert maestro.escolher_da_fila("lista", ["fila/a.json"]) is None


def test_fatos_de_venda_vem_dos_roteiros_aprovados_sem_hashtag(tmp_path):
    (tmp_path / "v.json").write_text(json.dumps({"cenas_roteiro": [{"narracao": "Oito estilos."}],
                                                 "legenda": "O pack.\n\nComenta ESTUDIO\n\n#ia"}), encoding="utf-8")
    fatos = produtora.fatos_venda(tmp_path)
    assert "- Oito estilos." in fatos and "- O pack." in fatos
    assert "#" not in fatos and "Comenta" not in fatos


def test_banco_tira_vencido_e_poe_assunto_do_momento_na_frente(tmp_path, monkeypatch):
    from datetime import datetime
    monkeypatch.setattr(maestro, "RAIZ", tmp_path)
    fila = tmp_path / "fila"
    for nome in ("2026-11-01-0300-produtora-velho.json", "2026-11-04-0300-produtora-a.json",
                 "2026-11-04-1100-em-alta-gta.json", "2026-11-03-0300-em-alta-esfriou.json"):
        _pauta(fila, nome)
    agora = datetime(2026, 11, 4, 18, 0, tzinfo=maestro.BRASILIA)
    assert maestro.disponiveis([], fila, agora) == ["fila/2026-11-04-1100-em-alta-gta.json", "fila/2026-11-04-0300-produtora-a.json"]


def test_em_alta_pula_politica_e_usa_so_manchetes():
    from src.estudio_instagram import em_alta
    candidatos = [{"termo": "Flávio Bolsonaro", "buscas": 9000, "manchetes": ["Senador viaja"], "fonte": "x"},
                  {"termo": "GTA 6", "buscas": 0, "manchetes": ["GTA 6 terá mais de 200 GB - Estadão"], "fonte": "x"}]
    vistos = []

    def llm(_sistema, lista):
        vistos.append(lista)
        return {"id": 0, "tema": "GTA 6", "angulo": "e se", "nota": 8}
    r = em_alta.escolher(candidatos, llm=llm, usados=[])
    assert "Bolsonaro" not in vistos[0] and r["chave"] == "GTA 6" and "200 GB" in r["fatos"]
    assert em_alta.escolher(candidatos, llm=lambda *_: {"id": 0, "nota": 4}, usados=[]) is None  # fraco não vira vídeo


def test_estilo_combina_com_o_assunto_e_varia():
    todos = [{"slug": s, "nome": s, "categoria": "x"} for s in ("archive-lighttable", "pixel-rpg", "neon", "dossie")]
    escolhe = lambda *_: {"estilos": ["pixel-rpg", "neon"]}
    assert produtora.estilo_para("GTA 6", {"estilos_usados": []}, todos, llm=escolhe, fracos=set())["slug"] == "pixel-rpg"
    assert produtora.estilo_para("GTA 6", {"estilos_usados": ["pixel-rpg"]}, todos, llm=escolhe, fracos=set())["slug"] == "neon"
    assert produtora.estilo_para("GTA 6", {"estilos_usados": ["neon", "pixel-rpg"]}, todos, llm=escolhe, fracos=set())["slug"] == "pixel-rpg"


def test_maestro_produz_de_madrugada_so_quando_falta_video():
    from datetime import datetime
    noite = datetime(2026, 11, 10, 1, 0, tzinfo=maestro.BRASILIA)
    assert maestro.deve_produzir(noite, {}, banco=1, rodando=False)
    assert not maestro.deve_produzir(noite, {}, banco=3, rodando=False)
    assert not maestro.deve_produzir(noite, {}, banco=0, rodando=True)
    assert not maestro.deve_produzir(noite, {"ultima_producao": "2026-11-10T00:30:00-03:00"}, banco=0, rodando=False)
    assert not maestro.deve_produzir(datetime(2026, 11, 10, 15, 0, tzinfo=maestro.BRASILIA), {}, banco=0, rodando=False)


def test_reforco_ate_a_cota_renovar_e_depois_volta_ao_normal():
    from datetime import datetime
    manha = datetime(2026, 11, 6, 10, 0, tzinfo=maestro.BRASILIA)
    assert maestro.deve_produzir(manha, {}, banco=5, rodando=False)
    assert not maestro.deve_produzir(manha, {}, banco=6, rodando=False)
    depois = datetime(2026, 11, 6, 13, 0, tzinfo=maestro.BRASILIA)
    assert maestro.banco_alvo(depois) == 3 and not maestro.deve_produzir(depois, {}, banco=0, rodando=False)


def test_estado_do_maestro_guarda_a_ultima_producao():
    from datetime import datetime
    _, novo = maestro.decidir(datetime(2026, 11, 6, 1, 0, tzinfo=maestro.BRASILIA),
                              {"dia": "2026-11-05", "feitos": {}, "ultima_producao": "2026-11-06T00:40:00-03:00"})
    assert novo["ultima_producao"] == "2026-11-06T00:40:00-03:00"


def test_legenda_usa_so_a_palavra_final(tmp_path, monkeypatch):
    import json as _json
    pasta = tmp_path / "2026-11-05-0420-gta-6-esquete"
    pasta.mkdir()
    (pasta / "pauta.json").write_text(_json.dumps({"roteiro": {"palavra": "ESTUDIO",
                                                               "legenda": "Dias de duas horas. Comenta GAME e me segue."}}))
    monkeypatch.setattr(produtora, "FILA", tmp_path / "fila")
    from src.estudio_instagram import hospedagem
    monkeypatch.setattr(hospedagem, "publicar", lambda *a, **k: "https://x/v.mp4")
    destino = produtora.para_fila({"pasta": str(pasta), "repo": "em-alta/gta-6", "estilo": "esquete", "em_alta": True})
    legenda = _json.loads(destino.read_text())["legenda"]
    assert "GAME" not in legenda and legenda.count("ESTUDIO") == 1


def test_no_maximo_um_assunto_do_momento_por_dia(monkeypatch):
    # 06/11: o repo do assunto do momento é a string fixa "em-alta" (sem slug — ver main()), e o campo
    # que diz se foi assunto do momento é `em_alta`, não um prefixo em `repo`. Testar com "em-alta/gta-6"
    # passava isolado mas nunca batia com o dado real gravado, e saíram 2 em-alta na mesma madrugada (06/11).
    from datetime import datetime
    agora = datetime(2026, 11, 5, 9, 0)
    feitos = {"producoes": [{"repo": "em-alta", "em_alta": True, "ok": True, "quando": "2026-11-05T01:00"}]}
    monkeypatch.setattr(produtora, "_estado", lambda: feitos)
    assert not produtora.cabe_em_alta(agora)
    monkeypatch.setattr(produtora, "_estado", lambda: {"producoes": [{"repo": "x/y", "em_alta": False, "ok": True, "quando": "2026-11-05T01:00"}]})
    assert produtora.cabe_em_alta(agora)


def test_estilo_que_flopou_sai_da_escolha():
    desempenho = {"geral": {"views_medianas": 1200},
                  "por_estilo": {"produtora-dossie": {"views_medianas": 130}, "produtora-esquete": {"views_medianas": 1266},
                                 "vila": {"views_medianas": 100}}}
    assert produtora.estilos_fracos(desempenho) == {"dossie"}
    todos = [{"slug": s, "nome": s, "categoria": "x"} for s in ("dossie", "esquete")]
    escolhe = lambda *_: {"estilos": ["dossie", "esquete"]}
    assert produtora.estilo_para("caso", {}, todos, llm=escolhe, fracos={"dossie"})["slug"] == "esquete"
    # se só sobrar estilo fraco, ainda produz (não trava a madrugada)
    so_dossie = lambda *_: {"estilos": ["dossie"]}
    assert produtora.estilo_para("caso", {}, todos, llm=so_dossie, fracos={"dossie"})["slug"] == "dossie"
