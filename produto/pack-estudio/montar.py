#!/usr/bin/env python3
"""Monta um Reels em uma das 8 identidades do Pack Estúdio a partir de um roteiro JSON.

Uso:
    python3 montar.py exemplos/exemplo-ferramenta.json --estilo papel                    # vídeo mudo, tempos estimados
    python3 montar.py meu-roteiro.json --audio minha-narracao.mp3 --estilo 3d            # tempos calculados do áudio
    python3 montar.py meu-roteiro.json --audio narracao.mp3 --estilo tier --renderizar   # já gera o MP4
    python3 montar.py meu-roteiro.json --audio narracao.mp3 --todos --renderizar         # um MP4 por estilo

Estilos: 3d, rabisco, pixelui, tier, telao, papel, vidro, voxel (veja o LEIA-ME).

Sem `--renderizar` ele só prepara a pasta do projeto (saida/<nome>/); para ver no navegador ou renderizar
depois, entre nela e rode `npx hyperframes preview` ou `npx hyperframes render`.

Requisitos: Python 3.9+, Node 22+ e ffmpeg. Só usa a biblioteca padrão do Python.
"""

import argparse
import json
import urllib.request
import re
import shutil
import subprocess
import sys
import unicodedata
import wave
from pathlib import Path

from alinhamento import PalavraNoTempo, aparar, cortes_de_cena

AQUI = Path(__file__).resolve().parent
MODELO = AQUI / "modelo"
VERSAO_HYPERFRAMES = "0.8.154"
TAXA = 24000
ADIANTAMENTO_S = 0.12  # o desenho entra um pouco antes da fala, para estar legível quando a palavra sai
PALAVRAS_POR_LEGENDA = 3

ESTILOS = ["3d", "rabisco", "pixelui", "tier", "telao", "papel", "vidro", "voxel"]
CORES = {"laranja", "azul", "verde", "roxo", "vermelho", "amarelo", "branco", "rosa"}
HUMORES = {"normal", "feliz", "animado", "pensando"}
# os 6 visuais que todas as identidades desenham do seu jeito (o "y" é ignorado pelos moldes do estúdio)
Y_PADRAO = {"titulo_pixel": 300, "icone_pixel": 380, "cadeia": 520, "contador": 340, "lista": 380, "terminal": 420}


class ErroDeRoteiro(Exception):
    pass


def normalizar(palavra: str) -> str:
    sem_acento = unicodedata.normalize("NFD", palavra.lower())
    return "".join(c for c in sem_acento if c.isalnum())


# ---------- validação, com mensagem que explica o que arrumar ----------

def validar(roteiro: dict, icones: set[str]) -> list[str]:
    erros = []
    cenas = roteiro.get("cenas")
    if not isinstance(cenas, list) or not cenas:
        return ['o roteiro precisa de uma lista "cenas" com pelo menos uma cena']
    for i, cena in enumerate(cenas, start=1):
        onde = f"cena {i}"
        if not isinstance(cena, dict) or not str(cena.get("narracao", "")).strip():
            erros.append(f'{onde}: falta o texto em "narracao"')
            continue
        v = cena.get("visual")
        if not isinstance(v, dict) or v.get("tipo") not in Y_PADRAO:
            erros.append(f'{onde}: "visual.tipo" tem que ser um destes: {", ".join(sorted(Y_PADRAO))}')
            continue
        if v.get("cor") and v["cor"] not in CORES:
            erros.append(f'{onde}: cor "{v["cor"]}" não existe. Use: {", ".join(sorted(CORES))}')
        if v.get("icone") and v["icone"] not in icones:
            erros.append(f'{onde}: ícone "{v["icone"]}" não existe (veja a pasta modelo/icons)')
        for no in v.get("nos", []):
            if no.get("icone") not in icones:
                erros.append(f'{onde}: ícone "{no.get("icone")}" não existe (veja a pasta modelo/icons)')
        for lado in ("esq", "dir"):
            if lado in v and v[lado].get("icone") not in icones:
                erros.append(f'{onde}: ícone "{v[lado].get("icone")}" não existe (veja a pasta modelo/icons)')
        if v["tipo"] == "contador" and "valor" not in v and not roteiro.get("repo", {}).get("estrelas"):
            erros.append(f'{onde}: o contador precisa de "valor" ou do bloco "repo" com "estrelas" no topo do roteiro')
        if v["tipo"] == "lista" and not 2 <= len(v.get("itens", [])) <= 4:
            erros.append(f'{onde}: a lista precisa de 2 a 4 "itens"')
        if v["tipo"] == "terminal" and not v.get("comando"):
            erros.append(f'{onde}: o terminal precisa de "comando"')
        if v["tipo"] == "cadeia" and not 2 <= len(v.get("nos", [])) <= 3:
            erros.append(f'{onde}: a cadeia precisa de 2 ou 3 "nos"')
        if len(cena["narracao"].split()) > 30:
            erros.append(f'{onde}: narração com mais de 30 palavras; divida em duas cenas para o visual acompanhar')
    return erros


# ---------- âncoras: qual palavra falada dispara cada elemento ----------

def _quantas_ancoras(v: dict) -> tuple[int, bool]:
    t = v["tipo"]
    if t == "cadeia":
        return len(v["nos"]), True
    if t == "lista":
        return len(v["itens"]), True
    if t == "terminal":
        return 2, True
    return 1, False


def _palavras_de_ancora(narracao: str) -> list[str]:
    achadas = []
    for bruta in narracao.split():
        n = normalizar(bruta)
        if len(n) >= 3 and n not in achadas:
            achadas.append(n)
    return achadas or [normalizar(narracao.split()[0])]


def _espalhar(palavras: list[str], quantas: int) -> list[str]:
    if quantas == 1:
        return [palavras[0]]
    passo = max(1, len(palavras) // quantas)
    return [palavras[min(i * passo, len(palavras) - 1)] for i in range(quantas)]


def tempo_da_ancora(ancora: str, palavras: list[PalavraNoTempo]) -> float:
    alvo = normalizar(ancora)
    for p in palavras:
        if normalizar(p.palavra) == alvo:
            return max(0.0, p.t - ADIANTAMENTO_S)
    raise ErroDeRoteiro(f'a âncora "{ancora}" não aparece na narração da cena')


# ---------- tempos ----------

def _peso(palavra: str) -> float:
    return sum(c.isalnum() for c in palavra) + 1.5


def tempos_estimados(textos: list[str]) -> tuple[list[float], list[PalavraNoTempo], float]:
    """Sem áudio: cada cena dura conforme o tamanho do texto (cerca de 2,7 palavras por segundo)."""
    cortes, palavras, cursor = [0.0], [], 0.0
    for texto in textos:
        toks = texto.split()
        duracao = max(2.8, len(toks) / 2.7 + 0.6)
        soma, corrido = sum(_peso(t) for t in toks), 0.0
        for t in toks:
            palavras.append(PalavraNoTempo(round(cursor + 0.2 + (duracao - 0.5) * corrido / soma, 3), t))
            corrido += _peso(t)
        cursor += duracao
        cortes.append(cursor)
    return cortes, palavras, cursor


def ler_audio(caminho: Path) -> bytes:
    resultado = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(caminho), "-f", "s16le", "-ac", "1", "-ar", str(TAXA), "-"],
        capture_output=True,
    )
    if resultado.returncode != 0:
        raise ErroDeRoteiro(f"o ffmpeg não conseguiu ler {caminho}: {resultado.stderr.decode(errors='replace')[:200]}")
    return resultado.stdout


def escrever_wav(caminho: Path, pcm: bytes):
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(pcm)


def legenda(palavras: list[PalavraNoTempo], fim: float) -> list[dict]:
    blocos = []
    for i in range(0, len(palavras), PALAVRAS_POR_LEGENDA):
        grupo = palavras[i:i + PALAVRAS_POR_LEGENDA]
        seguinte = palavras[i + PALAVRAS_POR_LEGENDA].t if i + PALAVRAS_POR_LEGENDA < len(palavras) else fim
        blocos.append({"t": grupo[0].t, "fim": seguinte, "texto": " ".join(p.palavra for p in grupo)})
    return blocos


# ---------- montagem ----------

def montar(roteiro: dict, destino: Path, audio: Path | None, estilo: str = "papel") -> float:
    icones = {p.stem for p in (MODELO / "assets" / "icons").glob("*.svg")}
    erros = validar(roteiro, icones)
    if erros:
        raise ErroDeRoteiro("Arrume isto no roteiro:\n- " + "\n- ".join(erros))

    cenas_in = roteiro["cenas"]
    textos = [c["narracao"].strip() for c in cenas_in]
    if audio:
        pcm, _ = aparar(ler_audio(audio))
        cortes, palavras = cortes_de_cena(textos, pcm)
        total = round(len(pcm) / 2 / TAXA + 0.6, 3)
    else:
        cortes, palavras, total = tempos_estimados(textos)
        total = round(total + 0.6, 3)
        pcm = bytes(int(TAXA * total) * 2)

    cenas, i = [], 0
    for k, (cena, texto) in enumerate(zip(cenas_in, textos), start=1):
        n = len(texto.split())
        da_cena = palavras[i:i + n]
        i += n
        v = dict(cena["visual"])
        quantas, lista = _quantas_ancoras(v)
        v.setdefault("y", Y_PADRAO[v["tipo"]])
        if lista:
            v["ancoras"] = v.get("ancoras") or _espalhar(_palavras_de_ancora(texto), quantas)
            v["ts"] = [round(tempo_da_ancora(a, da_cena), 3) for a in v["ancoras"]]
        else:
            ancora = v.get("ancora") or _palavras_de_ancora(texto)[0]
            v["t"] = round(tempo_da_ancora(ancora, da_cena), 3)
        inicio, fim = cortes[k - 1], cortes[k]
        humor = cena.get("humor", "normal")
        cenas.append({"id": str(k), "inicio": round(inicio, 3), "duracao": round(fim - inicio + (0.6 if k == len(cenas_in) else 0), 3),
                      "humor": humor if humor in HUMORES else "normal", "elementos": [v]})

    # o repositório do vídeo (nome e estrelas) alimenta o contador, o cabeçalho e o print do molde tier
    bloco = roteiro.get("repo") or {}
    nome_repo = bloco.get("nome", "")
    estrelas = bloco.get("estrelas") or next((c["elementos"][0].get("valor") for c in cenas if c["elementos"][0]["tipo"] == "contador"), 0)
    for c in cenas:
        if c["elementos"][0]["tipo"] == "contador":
            c["elementos"][0]["repo"] = nome_repo
    repos = {nome_repo: {"repo": nome_repo, "estrelas": int(estrelas or 0), "descricao": bloco.get("descricao", ""),
                         "url": f"https://github.com/{nome_repo}" if nome_repo else ""}}

    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(MODELO / "assets", destino / "assets")
    garantir_gsap(destino)
    escrever_wav(destino / "assets" / "narracao.wav", pcm)
    if estilo == "tier" and "/" in nome_repo:
        baixar_cartao(nome_repo, destino / "assets" / "cartao.png")

    miolos = {}
    for arquivo in (MODELO / "assets" / "icons").glob("*.svg"):
        achado = re.search(r"<svg[^>]*>(.*)</svg>", arquivo.read_text(encoding="utf-8"), re.S)
        miolos[arquivo.stem] = achado.group(1).strip()
    dados = {
        "duracao": total, "cenas": cenas, "legenda": legenda(palavras, total), "icones": miolos,
        "destaques": [d.lower() for d in roteiro.get("destaques", [])], "repos": repos,
    }
    (destino / "assets" / "dados.js").write_text("window.DADOS = " + json.dumps(dados, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    secoes = "\n".join(
        f'      <section id="cena-{c["id"]}" class="cena clip" data-start="{c["inicio"]}" data-duration="{c["duracao"]}" '
        f'data-track-index="1"><div class="palco"></div></section>' for c in cenas
    )
    html = (MODELO / f"estudio-{estilo}.html.tpl").read_text(encoding="utf-8")
    (destino / "index.html").write_text(html.replace("{{DURACAO}}", str(total)).replace("{{CENAS}}", secoes), encoding="utf-8")
    (destino / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
    }, indent=2), encoding="utf-8")
    (destino / "meta.json").write_text(json.dumps({"id": destino.name, "name": destino.name}), encoding="utf-8")
    return total


def baixar_cartao(repo: str, destino: Path):
    """Print de prévia do repositório (o cartão que o GitHub mostra ao compartilhar o link), usado no estilo tier."""
    try:
        pedido = urllib.request.Request(f"https://opengraph.githubassets.com/1/{repo}", headers={"User-Agent": "pack-estudio"})
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            destino.write_bytes(resposta.read())
    except OSError as erro:
        print(f"aviso: não baixei o print do repositório ({erro}); o quadro fica vazio")


def garantir_gsap(destino: Path):
    """O GSAP (biblioteca de animação) não vem junto no pack: ele é baixado do npm na primeira vez."""
    gsap = AQUI / "node_modules" / "gsap" / "dist" / "gsap.min.js"
    if not gsap.exists():
        print("baixando o GSAP do npm (só na primeira vez)...")
        if not (AQUI / "package.json").exists():
            (AQUI / "package.json").write_text('{"name": "pack-estudio", "private": true}\n', encoding="utf-8")
        subprocess.run(["npm", "install", "--no-audit", "--no-fund", "gsap"], cwd=AQUI, check=True)
    (destino / "assets" / "vendor").mkdir(parents=True, exist_ok=True)
    shutil.copy(gsap, destino / "assets" / "vendor" / "gsap.min.js")


def renderizar(destino: Path, saida: Path):
    saida = saida.resolve()
    subprocess.run(["npx", "--yes", f"hyperframes@{VERSAO_HYPERFRAMES}", "render", "--quality", "high", "--output", str(saida)],
                   cwd=destino, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roteiro", type=Path, help="arquivo .json com o roteiro (veja exemplos/)")
    parser.add_argument("--audio", type=Path, default=None, help="narração (mp3, wav, m4a...) com o roteiro falado em ordem")
    parser.add_argument("--saida", type=Path, default=None, help="pasta do projeto (padrão: saida/<nome do roteiro>)")
    parser.add_argument("--renderizar", action="store_true", help="depois de montar, gera o MP4")
    parser.add_argument("--estilo", choices=ESTILOS, default="papel", help="identidade visual (padrão: papel)")
    parser.add_argument("--todos", action="store_true", help="monta (e renderiza, com --renderizar) um vídeo em cada estilo")
    args = parser.parse_args()
    try:
        roteiro = json.loads(args.roteiro.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        sys.exit(f"não consegui ler {args.roteiro}: {erro}")
    estilos = ESTILOS if args.todos else [args.estilo]
    for estilo in estilos:
        destino = (args.saida or AQUI / "saida" / args.roteiro.stem)
        if args.todos:
            destino = destino.parent / f"{destino.name}-{estilo}"
        try:
            total = montar(json.loads(json.dumps(roteiro)), destino, args.audio, estilo)
        except ErroDeRoteiro as erro:
            sys.exit(str(erro))
        print(f"[{estilo}] projeto montado em {destino} ({total:.1f} s, {len(roteiro['cenas'])} cenas)")
        if args.renderizar:
            mp4 = destino.parent / f"{destino.name}.mp4"
            renderizar(destino, mp4)
            print(f"[{estilo}] vídeo pronto: {mp4}")
        else:
            print(f"para ver: cd {destino} && npx hyperframes preview   |   para gerar o MP4: npx hyperframes render")


if __name__ == "__main__":
    main()
