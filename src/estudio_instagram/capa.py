"""Capa dos Reels (Davi, 05/11, olhando o @clubedasskills: "todos têm capa, bonitão").

Fundo de cor chapada, título gigante em cima, três quadros do próprio vídeo no meio e a pílula da marca embaixo.
Tudo cabe no recorte 3:4 que o grid do perfil mostra (y 240..1680 numa capa 1080x1920). Feito com Pillow, sem
navegador nem LLM: roda no CI da produtora em segundos e não gasta token.
"""
from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTES = Path(__file__).resolve().parents[2] / "assets" / "fontes"
L, A = 1080, 1920
TOPO_GRID, BASE_GRID = 240, 1680
CORES = ["#ff5a36", "#2f4bff", "#11a05a", "#7b2ff7", "#e2276f", "#0b8f8a"]
DESTAQUE = "#ffd23f"
ESCURO = "#0b0e12"


def _titulo(tamanho: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTES / "BricolageGrotesque.ttf"), tamanho)
    f.set_variation_by_axes([96, 800, 75])  # tamanho óptico, peso, largura (condensada)
    return f


def _mono(tamanho: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTES / "MartianMono.ttf"), tamanho)
    f.set_variation_by_axes([100, 600])
    return f


def cor_para(texto: str) -> str:
    """Mesma pauta, mesma cor; pautas diferentes espalham as cores no grid."""
    return CORES[int(hashlib.md5(texto.encode()).hexdigest(), 16) % len(CORES)]


def quebrar(texto: str, fonte: ImageFont.FreeTypeFont, largura: int) -> list[str]:
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = f"{atual} {palavra}".strip()
        if fonte.getlength(teste) <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    return linhas + ([atual] if atual else [])


def caber(texto: str, largura: int = 960, max_linhas: int = 3) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Maior fonte em que o título cabe em até 3 linhas sem quebrar palavra."""
    for tamanho in range(190, 70, -6):
        f = _titulo(tamanho)
        linhas = quebrar(texto, f, largura)
        if len(linhas) <= max_linhas and all(f.getlength(x) <= largura for x in linhas):
            return f, linhas
    f = _titulo(70)
    return f, quebrar(texto, f, largura)[:max_linhas]


def quadros(video: Path, pontos=(0.22, 0.5, 0.78)) -> list[Image.Image]:
    """Três quadros do vídeo (começo, meio, fim), sem a fala de abertura nem o CTA."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                               capture_output=True, text=True, check=True).stdout.strip())
    imgs = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, p in enumerate(pontos):
            saida = Path(tmp) / f"q{i}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur * p:.2f}", "-i", str(video), "-frames:v", "1",
                            "-q:v", "2", str(saida)], check=True)
            imgs.append(Image.open(saida).convert("RGB"))
    return imgs


def _celular(img: Image.Image, larg: int, giro: float) -> Image.Image:
    """Quadro 9:16 com canto arredondado, borda clara e sombra, girado."""
    alt = larg * 16 // 9
    tela = img.resize((larg, alt), Image.LANCZOS)
    borda = 10
    peca = Image.new("RGBA", (larg + 2 * borda, alt + 2 * borda), (0, 0, 0, 0))
    ImageDraw.Draw(peca).rounded_rectangle([0, 0, *peca.size], radius=46, fill="#f4e9d6")
    mascara = Image.new("L", (larg, alt), 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, larg, alt], radius=36, fill=255)
    peca.paste(tela, (borda, borda), mascara)
    margem = 60
    sombra = Image.new("RGBA", (peca.width + 2 * margem, peca.height + 2 * margem), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([margem, margem + 24, margem + peca.width, margem + peca.height + 24],
                                             radius=46, fill=(0, 0, 0, 120))
    sombra = sombra.filter(ImageFilter.GaussianBlur(26))
    sombra.alpha_composite(peca, (margem, margem))
    return sombra.rotate(giro, resample=Image.BICUBIC, expand=True)


def _robo(d: ImageDraw.ImageDraw, x: int, y: int, s: float) -> None:
    """O logo do perfil (assets/logo.svg da página de venda) desenhado em escala s (64 px -> 64*s)."""
    r = lambda a, b, c, e, raio, cor: d.rounded_rectangle([x + a * s, y + b * s, x + (a + c) * s, y + (b + e) * s], radius=raio * s, fill=cor)
    r(31, 2, 2.6, 10, 1.3, "#b9ab98")
    d.ellipse([x + 28.1 * s, y + 0.3 * s, x + 36.5 * s, y + 8.7 * s], fill="#ff3b30")
    r(6, 12, 52, 42, 12, "#f4e9d6")
    r(2, 27, 5, 12, 2.5, "#ff6a48")
    r(57, 27, 5, 12, 2.5, "#ff6a48")
    r(12, 18, 40, 29, 7, ESCURO)
    r(21, 24, 6.5, 11, 3.25, "#5ef2c2")
    r(36.5, 24, 6.5, 11, 3.25, "#5ef2c2")
    d.arc([x + 27 * s, y + 35 * s, x + 37 * s, y + 42 * s], 20, 160, fill="#5ef2c2", width=max(2, int(2.4 * s)))


def montar(titulo: str, imgs: list[Image.Image], cor: str | None = None) -> Image.Image:
    cor = cor or cor_para(titulo)
    capa = Image.new("RGBA", (L, A), cor)
    # luz suave no centro, pra cor chapada não ficar morta
    luz = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    ImageDraw.Draw(luz).ellipse([-200, 500, L + 200, 1700], fill=(255, 255, 255, 46))
    capa.alpha_composite(luz.filter(ImageFilter.GaussianBlur(160)))
    d = ImageDraw.Draw(capa)

    texto = titulo.upper().strip().rstrip(".")
    fonte, linhas = caber(texto)
    passo = int(fonte.size * 0.9)
    y = TOPO_GRID + 40
    for i, linha in enumerate(linhas):
        tinta = DESTAQUE if i == len(linhas) - 1 and len(linhas) > 1 else "#ffffff"
        d.text((L // 2, y), linha, font=fonte, fill=tinta, anchor="ma")
        y += passo
    topo_quadros = y + 30

    # três quadros: os dois de trás menores e girados, o do meio na frente
    base = BASE_GRID - 150
    alt_meio = base - topo_quadros
    larg_meio = max(260, min(470, alt_meio * 9 // 16 - 20))
    lados = [(imgs[0], int(larg_meio * 0.78), 7, -1), (imgs[2], int(larg_meio * 0.78), -7, 1)]
    for img, larg, giro, lado in lados:
        p = _celular(img, larg, giro)
        cx = L // 2 + lado * int(larg_meio * 0.78)
        capa.alpha_composite(p, (cx - p.width // 2, topo_quadros + (alt_meio - p.height) // 2 + 30))
    p = _celular(imgs[1], larg_meio, -2)
    capa.alpha_composite(p, (L // 2 - p.width // 2, topo_quadros + (alt_meio - p.height) // 2))

    # pílula da marca
    d = ImageDraw.Draw(capa)
    marca, perfil = "Máquina de Reels", "@ursulino.ia"
    fm = _mono(30)
    larg_p = 64 + 16 + int(fm.getlength(marca)) + 50 + int(fm.getlength(perfil)) + 70
    x0, y0 = (L - larg_p) // 2, BASE_GRID - 120
    d.rounded_rectangle([x0, y0, x0 + larg_p, y0 + 88], radius=44, fill=ESCURO)
    _robo(d, x0 + 30, y0 + 13, 0.97)
    xt = x0 + 30 + 64 + 18
    d.text((xt, y0 + 44), marca, font=fm, fill="#f4e9d6", anchor="lm")
    xs = xt + fm.getlength(marca) + 25
    d.line([xs, y0 + 26, xs, y0 + 62], fill="#4a4f59", width=2)
    d.text((xs + 25, y0 + 44), perfil, font=fm, fill="#5ef2c2", anchor="lm")
    return capa.convert("RGB")


def gerar(video: Path, titulo: str, saida: Path, cor: str | None = None) -> Path:
    montar(titulo, quadros(video), cor).save(saida, "JPEG", quality=90)
    return saida


if __name__ == "__main__":
    import sys
    print(gerar(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])))
