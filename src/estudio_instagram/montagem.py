"""Monta as pastas de projeto Hyperframes (Reels e carrossel) a partir da pauta.

Nada aqui chama rede: a voz chega por um `ProvedorDeVoz` e os dados do GitHub chegam
prontos. Isso deixa a montagem inteira testável com dublês.
"""

import json
import re
import shutil
import wave
from pathlib import Path

from .github_dados import DadosRepo
from .pauta import formatar_estrelas, preencher
from .sincronia import PalavraNoTempo, blocos_de_legenda, tempo_da_ancora
from .voz import TAXA_AMOSTRA, ProvedorDeVoz

MODELOS = Path(__file__).parent / "modelos"
PAUSA_ENTRE_CENAS_S = 0.35
# Fundos em pixel art do molde pixel2 (ver CENARIOS em modelos/pixel2.html.tpl). Cada vídeo usa 2 e troca no meio.
CENARIOS_PIXEL = ["biblioteca", "servidores", "cidade", "espaco", "laboratorio"]


def escolher_cenarios(titulo: str) -> list[str]:
    """Par de cenários diferentes, fixo para o mesmo título (determinístico: dá pra testar e reproduzir)."""
    semente = sum(ord(c) for c in titulo)
    primeiro = semente % len(CENARIOS_PIXEL)
    segundo = (primeiro + 1 + semente // len(CENARIOS_PIXEL) % (len(CENARIOS_PIXEL) - 1)) % len(CENARIOS_PIXEL)
    return [CENARIOS_PIXEL[primeiro], CENARIOS_PIXEL[segundo]]
RESPIRO_FINAL_S = 1.0


def _copiar_assets(destino: Path):
    for pasta in ("vendor", "fonts", "icons", "musica", "robo"):
        shutil.copytree(MODELOS / "assets" / pasta, destino / "assets" / pasta, dirs_exist_ok=True)


def _escrever_dados(destino: Path, dados: dict):
    (destino / "assets" / "dados.js").write_text(
        "window.DADOS = " + json.dumps(dados, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8"
    )


def _escrever_projeto(destino: Path, nome: str):
    (destino / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
    }, indent=2), encoding="utf-8")
    (destino / "meta.json").write_text(json.dumps({"id": nome, "name": nome}), encoding="utf-8")


def _miolo_do_icone(nome: str) -> str:
    svg = (MODELOS / "assets" / "icons" / f"{nome}.svg").read_text(encoding="utf-8")
    return re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1).strip()


def _icones_usados(cenas: list[dict]) -> set[str]:
    usados = {"check", "github", "star", "shield-check"}  # "github", "star" e "shield-check": cartão do molde repo
    for cena in cenas:
        for elemento in cena["elementos"]:
            if "icone" in elemento:
                usados.add(elemento["icone"])
            for lado in ("esquerda", "direita"):
                if lado in elemento:
                    usados.add(elemento[lado]["icone"])
            usados.update(item["icone"] for item in elemento.get("itens", []) if isinstance(item, dict) and "icone" in item)
    return usados


def montar_reels(
    pauta: dict, repos: dict[str, DadosRepo], voz: ProvedorDeVoz, destino: Path, modelo: str = "reels.html.tpl"
) -> float:
    """Gera narração, tempos e index.html do Reels. Devolve a duração em segundos.

    `modelo` escolhe o "molde" visual (arquivo em modelos/*.html.tpl) — a orquestração
    (voz, sincronia, legendas) é a mesma pra qualquer molde; só o HTML/CSS/JS muda.
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    _copiar_assets(destino)
    _escrever_projeto(destino, "reels")
    estrelas = {r: d.estrelas for r, d in repos.items()}
    cenas = preencher(pauta["cenas"], estrelas)

    if hasattr(voz, "preparar"):
        voz.preparar([cena["narracao"] for cena in cenas])

    pcm_total = bytearray()
    silencio = bytes(int(TAXA_AMOSTRA * PAUSA_ENTRE_CENAS_S) * 2)
    cursor = 0.0
    legenda: list[dict] = []
    for cena in cenas:
        narracao = voz.sintetizar(cena["narracao"])
        for elemento in cena["elementos"]:
            if "ancora" in elemento:
                elemento["t"] = tempo_da_ancora(elemento["ancora"], narracao.palavras, cursor)
            if "ancoras" in elemento:
                elemento["ts"] = [tempo_da_ancora(a, narracao.palavras, cursor) for a in elemento["ancoras"]]
        # Legenda por cena, não pelo texto inteiro: um bloco nunca pode juntar o fim de uma fala
        # com o começo da próxima (ex.: "de propósito. É" grudando duas cenas diferentes).
        palavras_cena = [PalavraNoTempo(round(cursor + p.t, 3), p.palavra) for p in narracao.palavras]
        legenda += blocos_de_legenda(palavras_cena, round(cursor + narracao.duracao(), 3))
        cena["inicio"] = round(cursor, 3)
        cena["duracao"] = round(narracao.duracao() + PAUSA_ENTRE_CENAS_S, 3)
        pcm_total += narracao.audio_pcm + silencio
        cursor += narracao.duracao() + PAUSA_ENTRE_CENAS_S

    pcm_total += bytes(int(TAXA_AMOSTRA * RESPIRO_FINAL_S) * 2)
    total = round(len(pcm_total) / 2 / TAXA_AMOSTRA, 3)
    cenas[-1]["duracao"] = round(total - cenas[-1]["inicio"], 3)

    with wave.open(str(destino / "assets" / "narracao.wav"), "wb") as saida:
        saida.setnchannels(1)
        saida.setsampwidth(2)
        saida.setframerate(TAXA_AMOSTRA)
        saida.writeframes(bytes(pcm_total))

    _escrever_dados(destino, {
        "duracao": total,
        "cenas": cenas,
        "legenda": legenda,
        "destaques": pauta.get("destaques", []),
        "cenarios": pauta.get("cenarios") or escolher_cenarios(pauta.get("titulo", "")),
        "repos": {r: {"repo": d.repo, "estrelas": d.estrelas, "licenca": d.licenca, "descricao": d.descricao, "url": d.url}
                  for r, d in repos.items()},
        "icones": {nome: _miolo_do_icone(nome) for nome in sorted(
            {p.stem for p in (MODELOS / "assets" / "icons").glob("*.svg")} if modelo.startswith(("pixel2", "estudio")) else _icones_usados(cenas)
        )},
    })
    secoes = "\n".join(
        f'      <section id="cena-{c["id"]}" class="cena clip" data-start="{c["inicio"]}" '
        f'data-duration="{c["duracao"]}" data-track-index="1"><div class="palco"></div></section>'
        for c in cenas
    )
    html = (MODELOS / modelo).read_text(encoding="utf-8")
    (destino / "index.html").write_text(html.replace("{{DURACAO}}", str(total)).replace("{{CENAS}}", secoes), encoding="utf-8")
    return total


def montar_carrossel(pauta: dict, repos: dict[str, DadosRepo], cartoes: dict[str, Path], destino: Path) -> int:
    """Gera o index.html do carrossel (1 slide por segundo). Devolve o número de slides."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    _copiar_assets(destino)
    _escrever_projeto(destino, "carrossel")
    estrelas = {r: d.estrelas for r, d in repos.items()}

    itens = []
    for i, item in enumerate(pauta["itens"], start=1):
        dados = repos[item["repo"]]
        cartao = Path("assets") / "cartoes" / Path(cartoes[item["repo"]]).name
        (destino / cartao).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(cartoes[item["repo"]], destino / cartao)
        itens.append({
            "n": f"{i:02d}", "nome": item["nome"], "cor": item["cor"],
            "promessa": item["promessa"], "texto": item["texto"],
            "estrelas": formatar_estrelas(dados.estrelas), "licenca": dados.licenca,
            "cartao": cartao.as_posix(),
        })

    total_slides = len(itens) + 2
    _escrever_dados(destino, {
        "perfil": pauta["perfil"],
        "palavra_chave": pauta["palavra_chave"],
        "capa": preencher(pauta["capa"], estrelas),
        "chamada": pauta["chamada"],
        "itens": itens,
    })
    slides = "\n".join(
        f'      <section id="s{i}" class="slide clip" data-start="{i - 1}" data-duration="1" data-track-index="0"></section>'
        for i in range(1, total_slides + 1)
    )
    modelo = (MODELOS / "carrossel.html.tpl").read_text(encoding="utf-8")
    (destino / "index.html").write_text(modelo.replace("{{DURACAO}}", str(total_slides)).replace("{{SLIDES}}", slides), encoding="utf-8")
    return total_slides


def montar_carrossel_pixel(pauta: dict, destino: Path) -> int:
    """Carrossel do molde pixel: um slide por segundo, o conteúdo vem de `pauta["slides"]`.

    Não depende de repositório do GitHub: serve para dica, lista, passo a passo.
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    _copiar_assets(destino)
    _escrever_projeto(destino, "carrossel")
    slides_pauta = pauta["slides"]
    _escrever_dados(destino, {
        "perfil": pauta["perfil"],
        "slides": slides_pauta,
        "icones": {},
    })
    secoes = "\n".join(
        f'      <section id="s{i}" class="slide clip" data-start="{i - 1}" data-duration="1" data-track-index="0"></section>'
        for i in range(1, len(slides_pauta) + 1)
    )
    modelo = (MODELOS / "pixel-carrossel.html.tpl").read_text(encoding="utf-8")
    (destino / "index.html").write_text(
        modelo.replace("{{DURACAO}}", str(len(slides_pauta))).replace("{{SLIDES}}", secoes), encoding="utf-8"
    )
    return len(slides_pauta)
