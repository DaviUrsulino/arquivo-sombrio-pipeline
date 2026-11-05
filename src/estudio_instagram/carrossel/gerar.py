"""Carrossel animado: cada lâmina é um vídeo curto (1080x1350, 6 s, em loop) feito no HyperFrames.

Por que (Davi, 05/11): o carrossel antigo repetia o vídeo e ninguém salvava. Carrossel é o formato de SALVAR
(skill carousel-writer): capa que promete, uma ideia por lâmina, fim pedindo para salvar. Aqui cada lâmina
tem uma animação própria que mostra o que a ferramenta faz, com o número real de estrelas do GitHub.

    python -m src.estudio_instagram.carrossel.gerar roteiro.json saida/
"""

import json
import subprocess
import sys
from pathlib import Path

MODELO = Path(__file__).with_name("lamina.html")
DUR = 6


def _estrelas(n: int) -> str:
    return f"{n / 1000:.1f} mil".replace(".", ",") if n >= 1000 else str(n)


VISUAIS = {
    # linha do tempo de editor: faixas entram e a agulha corre
    "editor": ('''<div class="barra" id="b1" style="left:40px;top:60px;width:420px;background:#ff6b4a"></div>
<div class="barra" id="b2" style="left:300px;top:140px;width:500px;background:#5ef2c2"></div>
<div class="barra" id="b3" style="left:120px;top:220px;width:360px;background:#ffd166"></div>
<div class="barra" id="b4" style="left:520px;top:300px;width:300px;background:#a78bfa"></div>
<div id="agulha" style="position:absolute;left:30px;top:30px;width:6px;height:360px;background:#f4f1ea"></div>''',
               '''tl.fromTo(["#b1","#b2","#b3","#b4"], {x: 900}, {x: 0, duration: 0.7, stagger: 0.25, ease}, 0.6);
tl.fromTo("#agulha", {x: 0}, {x: 840, duration: 4.6, ease: "none"}, 1.2);'''),
    # grade de peças que acendem em onda
    "grade": ("".join(f'<div class="peca g" style="left:{40 + (k % 9) * 98}px;top:{40 + (k // 9) * 92}px;background:#26262c"></div>'
                      for k in range(36)),
              '''tl.fromTo(".g", {scale: 0.2, backgroundColor: "#26262c"}, {scale: 1, backgroundColor: "#5ef2c2", duration: 0.35,
  stagger: {each: 0.07, from: "start"}, ease: "back.out(2)"}, 0.5);
tl.to(".g", {backgroundColor: "#ff6b4a", duration: 0.3, stagger: {each: 0.05, from: "end"}}, 3.6);'''),
    # 66 amostras de estilo virando
    "estilos": ("".join(f'<div class="peca s" style="width:64px;height:64px;left:{34 + (k % 11) * 76}px;top:{40 + (k // 11) * 62}px;'
                        f'background:hsl({k * 37 % 360},70%,60%)"></div>' for k in range(66)),
                '''tl.fromTo(".s", {rotationY: 90, opacity: 0}, {rotationY: 0, opacity: 1, duration: 0.4, stagger: {each: 0.035, grid: [6, 11], from: "center"}, ease}, 0.5);
tl.to(".s", {y: -10, duration: 0.3, yoyo: true, repeat: 1, stagger: {each: 0.02, grid: [6, 11], from: "edges"}}, 3.8);'''),
    # curva de matemática se desenhando
    "curva": ('''<svg width="920" height="430" viewBox="0 0 920 430" style="position:absolute;left:0;top:0">
<line x1="40" y1="215" x2="880" y2="215" stroke="#3a3a42" stroke-width="4"/><line x1="80" y1="30" x2="80" y2="400" stroke="#3a3a42" stroke-width="4"/>
<path id="seno" d="M80 215 C150 40 230 40 300 215 S450 390 520 215 S670 40 740 215 S850 330 880 280" fill="none" stroke="#5ef2c2" stroke-width="10" stroke-linecap="round"/>
<circle id="ponto" cx="80" cy="215" r="16" fill="#ff6b4a"/></svg>''',
              '''const len = document.querySelector("#seno").getTotalLength();
tl.fromTo("#seno", {strokeDasharray: len, strokeDashoffset: len}, {strokeDashoffset: 0, duration: 3.6, ease: "power1.inOut"}, 0.6);
const pts = Array.from({length: 61}, (_, i) => document.querySelector("#seno").getPointAtLength(len * i / 60));
pts.forEach((p, i) => tl.set("#ponto", {attr: {cx: p.x, cy: p.y}}, 0.6 + 3.6 * i / 60));'''),
    # código vira fita de quadros
    "codigo": ('''<div id="cod" class="mono" style="position:absolute;left:40px;top:40px;font-size:44px;color:#5ef2c2">&lt;Video&gt;</div>
<div id="fita" style="position:absolute;left:0;top:170px;height:200px;width:2000px;display:flex;gap:18px">'''
               + "".join(f'<div style="width:220px;height:200px;border-radius:16px;background:hsl({20 + k * 45},70%,58%)"></div>' for k in range(8))
               + "</div>",
               '''tl.fromTo("#cod", {opacity: 0, x: -40}, {opacity: 1, x: 0, duration: 0.5, ease}, 0.5);
tl.fromTo("#fita", {x: 920}, {x: -900, duration: 4.4, ease: "none"}, 1.2);'''),
    # HTML vira vídeo: tag se abre e vira um player
    "html": ('''<div id="tag" class="mono" style="position:absolute;left:0;right:0;top:120px;text-align:center;font-size:110px;color:#ffd166">&lt;html&gt;</div>
<div id="tela" style="position:absolute;left:230px;top:60px;width:460px;height:310px;border-radius:22px;background:#ff6b4a;opacity:0">
<div style="position:absolute;left:190px;top:105px;width:0;height:0;border-left:90px solid #0d0d0f;border-top:52px solid transparent;border-bottom:52px solid transparent"></div></div>''',
             '''tl.fromTo("#tag", {scale: 0.6, opacity: 0}, {scale: 1, opacity: 1, duration: 0.6, ease}, 0.5);
tl.to("#tag", {scale: 1.6, opacity: 0, duration: 0.5}, 2.0);
tl.fromTo("#tela", {scale: 0.3, opacity: 0}, {scale: 1, opacity: 1, duration: 0.6, ease: "back.out(1.8)"}, 2.3);
tl.to("#tela", {rotation: 3, duration: 0.25, yoyo: true, repeat: 5}, 3.2);'''),
}


def capa(r: dict) -> tuple[str, str]:
    corpo = f'''<div class="topo"><span>@ursulino.ia</span><span><b>SALVA</b> PRA DEPOIS</span></div>
<div class="selo" id="selo">GRÁTIS</div>
<div class="capa-titulo" id="titulo">{r["capa"]}</div>
<div class="capa-sub" id="sub">{r["capa_sub"]}</div>
<div class="arrasta" id="seta">ARRASTA →</div>'''
    anim = '''tl.fromTo("#titulo", {y: 80, opacity: 0}, {y: 0, opacity: 1, duration: 0.8, ease}, 0.2);
tl.fromTo("#selo", {scale: 2.5, opacity: 0}, {scale: 1, opacity: 1, duration: 0.45, ease: "back.out(2)"}, 0.9);
tl.fromTo("#sub", {opacity: 0}, {opacity: 1, duration: 0.6}, 1.3);
tl.fromTo("#seta", {x: 0}, {x: 26, duration: 0.5, yoyo: true, repeat: 7, ease: "sine.inOut"}, 1.8);'''
    return corpo, anim


def ferramenta(r: dict, k: int, total: int) -> tuple[str, str]:
    f = r["itens"][k]
    vis_html, vis_anim = VISUAIS[f["visual"]]
    corpo = f'''<div class="topo"><span>IA GRÁTIS <b>{k + 1}/{total}</b></span><span>@ursulino.ia</span></div>
<div class="num" id="num">{k + 1:02d}</div>
<div class="nome" id="nome">{f["nome"]}</div>
<div class="faz" id="faz">{f["faz"]}</div>
<div class="palco" id="palco">{vis_html}</div>
<div class="estrelas" id="est">★ <span id="cont">0</span> estrelas no GitHub</div>
<div class="arrasta">→</div>'''
    anim = f'''tl.fromTo("#num", {{x: -120, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.6, ease}}, 0.1);
tl.fromTo("#nome", {{y: 60, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.6, ease}}, 0.2);
tl.fromTo("#faz", {{opacity: 0}}, {{opacity: 1, duration: 0.6}}, 0.5);
const alvo = {{v: 0}};
tl.fromTo(alvo, {{v: 0}}, {{v: {f["estrelas"]}, duration: 1.6, ease: "power2.out",
  onUpdate: () => {{ const n = Math.round(alvo.v); document.querySelector("#cont").textContent =
    n >= 1000 ? (n / 1000).toFixed(1).replace(".", ",") + " mil" : String(n); }} }}, 0.8);
{vis_anim}'''
    return corpo, anim


def fim(r: dict) -> tuple[str, str]:
    corpo = f'''<div class="topo"><span>@ursulino.ia</span><span>TODAS <b>GRÁTIS</b></span></div>
<div class="capa-titulo" id="titulo" style="top:260px">SALVA<br/><span class="c">ESSE</span> POST</div>
<div class="capa-sub" id="sub" style="top:760px;font-size:46px;line-height:1.35">Comenta <span style="color:#5ef2c2">{r["palavra"]}</span>
que eu te mando os {len(r["itens"])} links no direct.<br/><br/>E me segue: toda semana tem lista nova.</div>'''
    anim = '''tl.fromTo("#titulo", {scale: 1.3, opacity: 0}, {scale: 1, opacity: 1, duration: 0.6, ease}, 0.2);
tl.fromTo("#sub", {y: 40, opacity: 0}, {y: 0, opacity: 1, duration: 0.6, ease}, 0.8);
tl.to("#titulo", {scale: 1.04, duration: 0.6, yoyo: true, repeat: 5, ease: "sine.inOut"}, 1.6);'''
    return corpo, anim


def montar(roteiro: dict, saida: Path, renderizar: bool = True) -> list[Path]:
    modelo = MODELO.read_text(encoding="utf-8")
    total = len(roteiro["itens"])
    laminas = [capa(roteiro)] + [ferramenta(roteiro, k, total) for k in range(total)] + [fim(roteiro)]
    videos = []
    for k, (corpo, anim) in enumerate(laminas):
        pasta = saida / f"lamina-{k:02d}"
        pasta.mkdir(parents=True, exist_ok=True)
        html = modelo.replace("__DUR__", str(DUR)).replace("__CORPO__", corpo).replace("__ANIM__", anim)
        (pasta / "index.html").write_text(html, encoding="utf-8")
        mp4 = saida / f"lamina-{k:02d}.mp4"
        if renderizar:
            subprocess.run(["npx", "--yes", "hyperframes", "render", "--quality", "high", "--output", str(mp4.resolve())],
                           cwd=pasta, check=True, capture_output=True)
        videos.append(mp4)
    return videos


if __name__ == "__main__":
    r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for v in montar(r, Path(sys.argv[2])):
        print(v)
