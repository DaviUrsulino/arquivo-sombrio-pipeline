import copy
import json
import wave
from pathlib import Path

import pytest

from src.estudio_instagram import montagem, pauta
from src.estudio_instagram.github_dados import DadosRepo
from src.estudio_instagram.sincronia import PalavraNoTempo
from src.estudio_instagram.voz import TAXA_AMOSTRA, Narracao

PAUTA = pauta.carregar(Path(__file__).parents[2] / "pautas" / "5-repos-claude-code.json")
REPOS = {item["repo"]: DadosRepo(item["repo"], 100_000 + i, "MIT", "", f"https://github.com/{item['repo']}")
         for i, item in enumerate(PAUTA["itens"])}


class VozFalsa:
    """Dublê de ProvedorDeVoz: cada palavra dura 0,5 s, sem rede e sem crédito gasto."""

    def __init__(self):
        self.textos = []

    def sintetizar(self, texto):
        self.textos.append(texto)
        palavras = [PalavraNoTempo(i * 0.5, p) for i, p in enumerate(texto.split())]
        return Narracao(b"\x00\x00" * int(TAXA_AMOSTRA * 0.5 * len(palavras)), palavras)


def _dados_js(pasta: Path) -> dict:
    texto = (pasta / "assets" / "dados.js").read_text(encoding="utf-8")
    return json.loads(texto.removeprefix("window.DADOS = ").rstrip().rstrip(";"))


def test_reels_monta_cenas_em_sequencia_com_audio_do_tamanho_certo(tmp_path):
    voz = VozFalsa()
    duracao = montagem.montar_reels(copy.deepcopy(PAUTA), REPOS, voz, tmp_path)

    assert voz.textos == [c["narracao"] for c in PAUTA["cenas"]]
    dados = _dados_js(tmp_path)
    inicios = [c["inicio"] for c in dados["cenas"]]
    assert inicios == sorted(inicios) and inicios[0] == 0.0
    assert dados["duracao"] == pytest.approx(duracao)
    with wave.open(str(tmp_path / "assets" / "narracao.wav")) as w:
        assert w.getnframes() / w.getframerate() == pytest.approx(duracao, abs=0.01)
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert html.count('class="cena clip"') == len(PAUTA["cenas"])
    assert "{{" not in html


def test_reels_preenche_estrelas_reais_e_tempos_dentro_da_cena(tmp_path):
    montagem.montar_reels(copy.deepcopy(PAUTA), REPOS, VozFalsa(), tmp_path)
    dados = _dados_js(tmp_path)
    cartoes = [e for c in dados["cenas"] for e in c["elementos"] if e["tipo"] == "cartao"]
    assert cartoes[0]["texto"] == "★ 100 mil estrelas"
    for cena in dados["cenas"]:
        for e in cena["elementos"]:
            for t in [e.get("t")] + e.get("ts", []):
                if t is not None:
                    assert cena["inicio"] - 0.2 <= t <= cena["inicio"] + cena["duracao"]


def test_carrossel_tem_capa_itens_e_chamada(tmp_path):
    cartoes = {}
    for r in REPOS:
        arquivo = tmp_path / "cartoes" / f"{r.replace('/', '_')}.png"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_bytes(b"PNG")
        cartoes[r] = arquivo

    n = montagem.montar_carrossel(PAUTA, REPOS, cartoes, tmp_path / "carrossel")

    assert n == len(PAUTA["itens"]) + 2
    dados = _dados_js(tmp_path / "carrossel")
    assert [i["n"] for i in dados["itens"]] == ["01", "02", "03", "04", "05"]
    assert dados["capa"]["selo"] == "★ 500 mil estrelas"
    assert all((tmp_path / "carrossel" / i["cartao"]).exists() for i in dados["itens"])
    html = (tmp_path / "carrossel" / "index.html").read_text(encoding="utf-8")
    assert html.count('class="slide clip"') == n


def test_montar_legenda_tem_palavra_chave_e_hashtags():
    from src.estudio_instagram.pipeline import montar_legenda
    legenda = montar_legenda(PAUTA, REPOS)
    assert PAUTA["palavra_chave"] in legenda
    assert "#claudecode" in legenda
    assert len(legenda) <= 2200
