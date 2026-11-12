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
    """10/11: a janela passou a começar às 2h (a sessão do Claude do Davi renova nesse horário)."""
    from datetime import datetime
    noite = datetime(2026, 11, 10, 3, 0, tzinfo=maestro.BRASILIA)
    alvo = maestro.banco_alvo(noite)
    assert maestro.deve_produzir(noite, {}, banco=1, rodando=False)
    assert not maestro.deve_produzir(noite, {}, banco=alvo, rodando=False)
    assert not maestro.deve_produzir(noite, {}, banco=0, rodando=True)
    assert not maestro.deve_produzir(noite, {"ultima_producao": "2026-11-10T02:30:00-03:00"}, banco=0, rodando=False)
    assert not maestro.deve_produzir(datetime(2026, 11, 10, 15, 0, tzinfo=maestro.BRASILIA), {}, banco=0, rodando=False)
    # antes das 2h não produz: a cota ainda é da sessão velha
    assert not maestro.deve_produzir(datetime(2026, 11, 10, 1, 0, tzinfo=maestro.BRASILIA), {}, banco=0, rodando=False)


def test_reforco_ate_a_cota_renovar_e_depois_volta_ao_normal():
    from datetime import datetime
    manha = datetime(2026, 11, 11, 10, 0, tzinfo=maestro.BRASILIA)   # dentro do reforço
    reforcado = maestro.banco_alvo(manha)
    assert maestro.deve_produzir(manha, {}, banco=reforcado - 1, rodando=False)
    assert not maestro.deve_produzir(manha, {}, banco=reforcado, rodando=False)
    depois = maestro.REFORCO_ATE.replace(hour=13)                     # reforço acabou
    assert maestro.banco_alvo(depois) == maestro.BANCO_ALVO
    assert not maestro.deve_produzir(depois, {}, banco=0, rodando=False)


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


def test_legenda_com_duas_chamadas_vira_uma_so(tmp_path, monkeypatch):
    # 06/11: o LLM escreveu "Comente MAQUINA..." (verbo diferente de "Comenta") numa linha e deixou uma segunda
    # linha de CTA solta; o regex antigo só pegava "comenta" e o reforço de palavra colava uma 3ª linha -- saiu
    # legenda real com 2 chamadas de ação diferentes ("Comente MAQUINA" + "Comenta ESTUDIO").
    import json as _json
    pasta = tmp_path / "2026-11-06-1137-pack-estudio-dark-keynote"
    pasta.mkdir()
    (pasta / "pauta.json").write_text(_json.dumps({"roteiro": {"palavra": "ESTUDIO",
        "legenda": "Tenha seu sistema de vídeos sem mensalidade.\nComente MAQUINA para receber o link no direct."}}))
    monkeypatch.setattr(produtora, "FILA_VENDA", tmp_path / "fila_venda")
    from src.estudio_instagram import hospedagem
    monkeypatch.setattr(hospedagem, "publicar", lambda *a, **k: "https://x/v.mp4")
    destino = produtora.para_fila({"pasta": str(pasta), "repo": "venda/pack-estudio", "estilo": "dark-keynote", "venda": True})
    legenda = _json.loads(destino.read_text())["legenda"]
    assert "MAQUINA" not in legenda
    assert legenda.lower().count("comenta") == 1


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


def test_nunca_dois_videos_de_venda_seguidos(tmp_path, monkeypatch):
    fila, venda = tmp_path / "pautas/viral/fila", tmp_path / "pautas/viral/fila_venda"
    fila.mkdir(parents=True), venda.mkdir(parents=True)
    for n in ("2099-01-01-0000-em-alta-x.json", "2099-01-01-0001-produtora-a.json"):
        (fila / n).write_text("{}")
    (venda / "2099-01-01-0002-produtora-v.json").write_text("{}")
    monkeypatch.setattr(maestro, "RAIZ", tmp_path)
    monkeypatch.setattr(maestro, "FILA", fila)
    monkeypatch.setattr(maestro, "FILA_VENDA", venda)
    monkeypatch.setattr(maestro, "disponiveis", lambda usadas, pasta=None, agora=None: [
        c for c in ["pautas/viral/fila/2099-01-01-0000-em-alta-x.json", "pautas/viral/fila/2099-01-01-0001-produtora-a.json"]
        if c not in usadas] if pasta in (None, fila) else [c for c in ["pautas/viral/fila_venda/2099-01-01-0002-produtora-v.json"] if c not in usadas])
    em_alta = "pautas/viral/fila/2099-01-01-0000-em-alta-x.json"
    # depois de um em-alta, a rodada comum pega o vídeo comum
    assert maestro.escolher_da_fila("lista", [em_alta]) == "pautas/viral/fila/2099-01-01-0001-produtora-a.json"
    # na rodada antes da venda do dia, nada de em-alta
    assert maestro.escolher_da_fila("pixel2", [], antes_da_venda=True) == "pautas/viral/fila/2099-01-01-0001-produtora-a.json"


def test_pauta_fixada_do_dia_nao_perde_a_vez_pro_banco(tmp_path, monkeypatch):
    """11/11: a estreia do cotidiano estava fixada em PAUTAS_DO_DIA para as 22:30 e saiu o vídeo do xAI.
    Como hoje TODAS as rodadas usam o banco, o escolher_da_fila sobrescrevia a pauta fixada."""
    from datetime import datetime
    monkeypatch.setitem(maestro.PAUTAS_DO_DIA, "2026-11-20", {"22:30": "pautas/viral/fixada.json"})
    agora = datetime(2026, 11, 20, 22, 31, tzinfo=maestro.BRASILIA)
    formato, _ = maestro.decidir(agora, {"dia": "2026-11-20", "feitos": {h: "ok" for h, _ in maestro.RODADAS
                                                                        if h != "22:30"}})
    assert formato == "pauta:pautas/viral/fixada.json"
    # e o main só consulta o banco quando a rodada NÃO tem pauta fixada
    assert formato.startswith("pauta:")


def test_fechamento_segue_o_que_os_virais_fazem():
    """11/11: transcrevi 6 Reels com 11 milhões de views somados. O de 3 milhões (@thiagonavega) não pede NADA,
    e o de 3,5 milhões (@aprendisemquere) segmenta ('já sabia? comenta X / aprendeu agora? comenta Y')."""
    tipos = [produtora.fechamento(n, "ESTUDIO")[0] for n in range(len(produtora.FECHAMENTOS))]
    assert "nenhum" in tipos, "um em cada quatro fecha sem pedir nada, como o de 3 milhões"
    assert "segmentado" in tipos, "o de 3,5 milhões divide quem assiste em dois grupos"
    assert len(set(tipos)) >= 5, "o fechamento tem que variar, senão cansa"


def test_fechamento_vazio_nao_vira_cena_muda():
    from src.estudio_instagram.diretor import roteiro
    tipo, frase = next((t, f) for t, f in (produtora.fechamento(n, "X")
                                           for n in range(len(produtora.FECHAMENTOS))) if t == "nenhum")
    assert frase == ""
    rot = {"ganchos": ["g"], "corpo": ["c1", "c2"], "cta": frase}
    assert roteiro.frases(rot) == ["g", "c1", "c2"], "sem pedido, o vídeo acaba na última frase do corpo"


def test_segmentado_da_uma_palavra_pra_cada_lado():
    frase = dict(produtora.FECHAMENTOS)["segmentado"].format(p="ESTUDIO")
    assert frase.lower().count("comenta") == 2, "um pedido para cada grupo"
    assert "ESTUDIO" in frase


def test_rodada_da_tarde_so_pega_o_que_foi_posto_de_lado(tmp_path, monkeypatch):
    """Davi, 11/11: 'apagar é muito forte, bota esses pra tarde'. A tarde é a pior faixa do perfil (15h fez 173
    views), então é onde o vídeo reprovado sai sem queimar a rodada da madrugada ou do meio-dia."""
    descarte = tmp_path / "descarte"
    _pauta(descarte, "2026-11-11-0816-fraco.json")
    comum = tmp_path / "fila"
    _pauta(comum, "2026-11-11-0306-bom.json")
    monkeypatch.setattr(maestro, "RAIZ", tmp_path)
    monkeypatch.setattr(maestro, "FILA_DESCARTE", descarte)
    monkeypatch.setattr(maestro, "FILA", comum)
    assert dict(maestro.RODADAS)["15:00"] == "descarte"
    escolhido = maestro.escolher_da_fila("descarte", [])
    assert escolhido and "fraco" in escolhido, "a tarde puxa do descarte"
    normal = maestro.escolher_da_fila("pixel2", [])
    assert normal and "bom" in normal, "as outras rodadas nunca pegam do descarte"
