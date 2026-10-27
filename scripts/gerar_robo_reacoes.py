"""Gera o pack de reações do Robô Estagiário (mascote do @robo.estagiario) em SVG.

Mesma identidade do robô pixel do molde pixel2 (laranja, contorno marrom-escuro, antena amarela), redesenhada
em vetor para os moldes "estúdio": cabeça com visor escuro onde os olhos ciano mudam de expressão, crachá de
estagiário no peito e braços que mudam de pose. Saída: src/estudio_instagram/modelos/assets/robo/<reacao>.svg

    python scripts/gerar_robo_reacoes.py
"""

from pathlib import Path

DESTINO = Path(__file__).resolve().parents[1] / "src" / "estudio_instagram" / "modelos" / "assets" / "robo"
LARANJA, LARANJA_ESC, CONTORNO, VISOR, OLHO, AMARELO = "#ff8a2a", "#d9661a", "#2a1608", "#1b1d2b", "#5ff3ff", "#ffd84a"
T = 'stroke="#2a1608" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"'

# olhos (dentro do visor, centro em x=150/250, y=205)
OLHOS = {
    "normal": f'<rect x="125" y="180" width="46" height="56" rx="20" fill="{OLHO}"/><rect x="229" y="180" width="46" height="56" rx="20" fill="{OLHO}"/>',
    "feliz": f'<path d="M126 218 Q148 180 170 218" fill="none" stroke="{OLHO}" stroke-width="14" stroke-linecap="round"/><path d="M230 218 Q252 180 274 218" fill="none" stroke="{OLHO}" stroke-width="14" stroke-linecap="round"/>',
    "arregalado": f'<circle cx="148" cy="206" r="34" fill="{OLHO}"/><circle cx="252" cy="206" r="34" fill="{OLHO}"/><circle cx="148" cy="206" r="12" fill="{VISOR}"/><circle cx="252" cy="206" r="12" fill="{VISOR}"/>',
    "estrela": "".join(f'<path transform="translate({x} 206)" d="M0 -34 L9 -10 L34 -10 L14 6 L22 32 L0 16 L-22 32 L-14 6 L-34 -10 L-9 -10 Z" fill="{AMARELO}"/>' for x in (148, 252)),
    "pensando": f'<rect x="125" y="200" width="46" height="18" rx="9" fill="{OLHO}"/><rect x="229" y="180" width="46" height="40" rx="18" fill="{OLHO}"/>',
    "piscando": f'<rect x="125" y="180" width="46" height="56" rx="20" fill="{OLHO}"/><path d="M228 212 Q252 196 276 212" fill="none" stroke="{OLHO}" stroke-width="14" stroke-linecap="round"/>',
    "confuso": f'<rect x="125" y="190" width="46" height="40" rx="18" fill="{OLHO}"/><circle cx="252" cy="206" r="28" fill="{OLHO}"/><path d="M226 168 L280 178" stroke="{OLHO}" stroke-width="10" stroke-linecap="round"/>',
    "x": f'<path d="M128 186 L168 226 M168 186 L128 226 M232 186 L272 226 M272 186 L232 226" stroke="{OLHO}" stroke-width="14" stroke-linecap="round"/>',
}
# boca (no visor, abaixo dos olhos)
BOCAS = {
    "fechada": f'<path d="M180 262 Q200 270 220 262" fill="none" stroke="{OLHO}" stroke-width="8" stroke-linecap="round"/>',
    "sorriso": f'<path d="M170 254 Q200 286 230 254" fill="none" stroke="{OLHO}" stroke-width="9" stroke-linecap="round"/>',
    "aberta": f'<path d="M172 252 Q200 296 228 252 Z" fill="{OLHO}"/>',
    "meia": f'<rect x="180" y="254" width="40" height="16" rx="8" fill="{OLHO}"/>',
    "o": f'<ellipse cx="200" cy="266" rx="16" ry="20" fill="{OLHO}"/>',
    "torta": f'<path d="M176 268 L196 258 L210 266 L226 256" fill="none" stroke="{OLHO}" stroke-width="8" stroke-linecap="round"/>',
    "grito": f'<path d="M166 250 Q200 310 234 250 Z" fill="{OLHO}"/>',
}
# braços: (esquerdo, direito) como caminhos a partir dos ombros (x=110 e x=290, y=360)
def braco(pontos: str) -> str:
    return f'<path d="{pontos}" fill="none" stroke="{CONTORNO}" stroke-width="34" stroke-linecap="round" stroke-linejoin="round"/><path d="{pontos}" fill="none" stroke="{LARANJA}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>'

BRACOS = {
    "baixo": (braco("M112 370 Q84 420 92 470"), braco("M288 370 Q316 420 308 470")),
    "cima": (braco("M112 370 Q70 320 76 250"), braco("M288 370 Q330 320 324 250")),
    "aponta": (braco("M112 370 Q84 420 92 470"), braco("M288 370 Q340 350 380 330")),
    "queixo": (braco("M112 370 Q150 360 170 312"), braco("M288 370 Q316 420 308 470")),
    "cabeca": (braco("M112 370 Q60 300 96 190"), braco("M288 370 Q340 300 304 190")),
    "explica": (braco("M112 370 Q70 380 60 340"), braco("M288 370 Q330 380 340 340")),
}

REACOES = {
    # nome: (olhos, boca, braços, extra)
    "neutro": ("normal", "fechada", "baixo", ""),
    "falando_aberto": ("normal", "aberta", "explica", ""),
    "falando_meio": ("normal", "meia", "explica", ""),
    "comemorando": ("feliz", "aberta", "cima", "confete"),
    "impressionado": ("estrela", "o", "baixo", "brilho"),
    "pensativo_intenso": ("pensando", "torta", "queixo", "duvida"),
    "apontando": ("feliz", "sorriso", "aponta", ""),
    "surpreso": ("arregalado", "o", "cima", "susto"),
    "piscando": ("piscando", "sorriso", "aponta", ""),
    "confuso": ("confuso", "torta", "cabeca", "duvida"),
    "chocado": ("x", "grito", "cabeca", "susto"),
}

EXTRAS = {
    "": "",
    "confete": "".join(f'<rect x="{x}" y="{y}" width="16" height="16" rx="3" fill="{c}" transform="rotate({r} {x} {y})"/>' for x, y, c, r in
                       [(40, 80, AMARELO, 20), (330, 60, "#5ff3ff", -15), (70, 150, "#ff5ea8", 40), (350, 150, AMARELO, 10), (20, 220, "#5ff3ff", -30), (370, 230, "#ff5ea8", 25)]),
    "brilho": "".join(f'<path transform="translate({x} {y})" d="M0 -18 L5 -5 L18 0 L5 5 L0 18 L-5 5 L-18 0 L-5 -5 Z" fill="{AMARELO}"/>' for x, y in [(50, 110), (350, 90), (360, 200)]),
    "duvida": f'<text x="320" y="120" font-family="Arial Black, sans-serif" font-size="90" fill="{AMARELO}" stroke="{CONTORNO}" stroke-width="6" paint-order="stroke">?</text>',
    "susto": "".join(f'<path d="M{x} {y} l{dx} {dy}" stroke="{CONTORNO}" stroke-width="10" stroke-linecap="round"/>' for x, y, dx, dy in [(70, 120, -30, -20), (60, 170, -36, 0), (330, 120, 30, -20), (340, 170, 36, 0)]),
}


def svg(olhos: str, boca: str, bracos: str, extra: str) -> str:
    esq, dir_ = BRACOS[bracos]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 520" width="400" height="520">
  {EXTRAS[extra]}
  <path d="M200 96 L200 50" {T} fill="none"/>
  <circle cx="200" cy="40" r="20" fill="{AMARELO}" {T}/>
  {esq}{dir_}
  <rect x="120" y="330" width="160" height="150" rx="34" fill="{LARANJA}" {T}/>
  <rect x="150" y="372" width="100" height="62" rx="8" fill="#ffffff" {T.replace('10', '7')}/>
  <rect x="150" y="372" width="100" height="18" rx="6" fill="#2f5bff"/>
  <text x="200" y="420" text-anchor="middle" font-family="Arial Black, sans-serif" font-size="15" fill="{CONTORNO}">ESTAGIÁRIO</text>
  <rect x="150" y="480" width="40" height="30" rx="10" fill="{LARANJA_ESC}" {T}/>
  <rect x="210" y="480" width="40" height="30" rx="10" fill="{LARANJA_ESC}" {T}/>
  <rect x="70" y="96" width="260" height="236" rx="64" fill="{LARANJA}" {T}/>
  <rect x="64" y="180" width="22" height="64" rx="10" fill="{LARANJA_ESC}" {T}/>
  <rect x="314" y="180" width="22" height="64" rx="10" fill="{LARANJA_ESC}" {T}/>
  <rect x="100" y="146" width="200" height="150" rx="44" fill="{VISOR}" {T}/>
  <path d="M118 166 Q140 152 170 154" stroke="#ffffff" stroke-opacity=".25" stroke-width="10" stroke-linecap="round" fill="none"/>
  {OLHOS[olhos]}
  {BOCAS[boca]}
</svg>
'''


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nome, partes in REACOES.items():
        (DESTINO / f"{nome}.svg").write_text(svg(*partes), encoding="utf-8")
    print(f"{len(REACOES)} reações em {DESTINO}")


if __name__ == "__main__":
    main()
