<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Diagrama animado</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      @font-face {
        font-family: "Patrick Hand";
        src: url("assets/fonts/PatrickHand-Regular.ttf") format("truetype");
      }
      :root {
        --laranja: #ff9d3c; --azul: #5fb4ff; --verde: #4ee06a; --roxo: #b48cff;
        --vermelho: #ff5c5c; --amarelo: #ffd84a; --branco: #f1efe8;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #08080a; }
      #root {
        position: relative; width: 100%; height: 100%; overflow: hidden;
        font-family: "Patrick Hand", "Segoe UI", sans-serif; color: var(--branco);
      }
      #fundo { position: absolute; inset: 0; background: radial-gradient(ellipse 90% 55% at 50% 30%, #17171f 0%, #0a0a0d 60%, #050506 100%); }
      #grade {
        position: absolute; inset: 0; opacity: 0.07;
        background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px);
        background-size: 90px 90px;
      }
      .cena { position: absolute; inset: 0; }
      .palco { position: absolute; inset: 0; }
      .el { position: absolute; opacity: 0; }
      .titulo { font-size: 130px; line-height: 1.02; text-align: center; white-space: pre-wrap; text-shadow: 0 0 36px rgba(255,255,255,.14); }
      .titulo span { opacity: 1; }
      .no {
        position: absolute; width: 400px; height: 330px; border-radius: 34px; opacity: 0;
        background: linear-gradient(165deg, #1d1d25, #121217); border: 5px solid; display: flex;
        flex-direction: column; align-items: center; justify-content: center; gap: 18px;
        box-shadow: 0 40px 80px rgba(0,0,0,.6);
      }
      .no .rotulo { font-size: 62px; line-height: 1; text-align: center; white-space: pre-wrap; padding: 0 20px; }
      .seta { position: absolute; overflow: visible; }
      .selo {
        position: absolute; left: 0; width: 1080px; display: flex; justify-content: center; opacity: 0;
      }
      .selo div {
        font-size: 74px; letter-spacing: .06em; padding: 14px 54px; color: #ffd84a;
        border: 7px solid #ffd84a; border-radius: 22px; background: rgba(255, 216, 74, .08);
        box-shadow: 0 0 40px rgba(255, 216, 74, .25);
      }
      .emoji { font-size: 300px; text-align: center; width: 1080px; filter: drop-shadow(0 25px 45px rgba(0,0,0,.7)); }
      #legendas { position: absolute; left: 0; top: 1690px; width: 1080px; height: 170px; }
      .bloco-legenda {
        position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
        padding: 0 60px; text-align: center; font-size: 84px; line-height: 1.02; opacity: 0;
        color: #ffffff; text-shadow: 0 5px 0 #000, 0 0 26px rgba(0,0,0,.95);
      }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="grade" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
{{CENAS}}
      <div id="legendas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="3"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const D = window.DADOS;
      const tl = gsap.timeline({ paused: true });
      const SVG = "http://www.w3.org/2000/svg";
      const cor = (nome) => `var(--${nome || "branco"})`;

      function bloco(palco, y, classes = "") {
        const el = document.createElement("div");
        el.className = "el " + classes;
        el.style.top = y + "px";
        el.style.left = "0";
        el.style.width = "1080px";
        palco.appendChild(el);
        return el;
      }

      function textoPorSpan(pai, conteudo) {
        for (const ch of conteudo) {
          const s = document.createElement("span");
          s.textContent = ch;
          pai.appendChild(s);
        }
      }

      function digitar(t, inicio, porLetra = 0.022) {
        const letras = t.querySelectorAll("span");
        tl.set(t.parentElement, { opacity: 1 }, inicio);
        tl.fromTo(letras, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: porLetra, ease: "none" }, inicio);
      }

      function svgIcone(nome, tamanho, corCss) {
        const s = document.createElementNS(SVG, "svg");
        s.setAttribute("width", tamanho); s.setAttribute("height", tamanho);
        s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("fill", "none");
        s.setAttribute("stroke", "currentColor"); s.setAttribute("stroke-width", 1.7);
        s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
        s.style.color = corCss;
        s.innerHTML = D.icones[nome];
        return s;
      }

      function criarNo(palco, x, y, item) {
        const n = document.createElement("div");
        n.className = "no";
        n.style.left = x + "px"; n.style.top = y + "px";
        n.style.borderColor = cor(item.cor);
        n.appendChild(svgIcone(item.icone, 130, cor(item.cor)));
        const r = document.createElement("div");
        r.className = "rotulo"; r.style.color = cor(item.cor);
        r.textContent = item.rotulo;
        n.appendChild(r);
        palco.appendChild(n);
        return n;
      }

      // Seta desenhada traço a traço (stroke-dashoffset) com ponta no fim.
      function criarSeta(palco, x1, y1, x2, y2, corCss, t) {
        const s = document.createElementNS(SVG, "svg");
        s.setAttribute("class", "seta");
        s.setAttribute("width", 1080); s.setAttribute("height", 1920);
        s.style.left = "0"; s.style.top = "0";
        const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy);
        const ux = dx / len, uy = dy / len;
        const haste = document.createElementNS(SVG, "path");
        haste.setAttribute("d", `M${x1} ${y1} L${x2 - ux * 8} ${y2 - uy * 8}`);
        const ponta = document.createElementNS(SVG, "path");
        const px = -uy, py = ux;
        ponta.setAttribute("d", `M${x2 - ux * 46 + px * 26} ${y2 - uy * 46 + py * 26} L${x2} ${y2} L${x2 - ux * 46 - px * 26} ${y2 - uy * 46 - py * 26}`);
        [haste, ponta].forEach((p) => {
          p.setAttribute("fill", "none"); p.setAttribute("stroke", corCss);
          p.setAttribute("stroke-width", 12); p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-linejoin", "round");
          s.appendChild(p);
        });
        palco.appendChild(s);
        const total = len;
        tl.set(haste, { attr: { "stroke-dasharray": total, "stroke-dashoffset": total } }, 0);
        tl.set(ponta, { opacity: 0 }, 0);
        tl.to(haste, { attr: { "stroke-dashoffset": 0 }, duration: 0.4, ease: "power2.out" }, t);
        tl.to(ponta, { opacity: 1, duration: 0.1 }, t + 0.32);
      }

      function entrarNo(no, t) {
        tl.fromTo(no, { opacity: 0, y: 40, scale: 0.8 }, { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "back.out(1.8)" }, t);
      }

      const construtores = {
        cabecalho(palco, e, c) {
          const b = bloco(palco, e.y);
          b.style.display = "flex"; b.style.justifyContent = "center";
          const t = document.createElement("div");
          t.className = "titulo";
          t.style.fontSize = (e.tamanho || 130) + "px";
          t.style.color = cor(e.cor || c.cor);
          textoPorSpan(t, e.texto);
          b.appendChild(t);
          tl.fromTo(b, { opacity: 0, y: -18 }, { opacity: 1, y: 0, duration: 0.01 }, e.t);
          digitar(t, e.t, 0.03);
        },
        emoji(palco, e, c) {
          const b = bloco(palco, e.y);
          const em = document.createElement("div");
          em.className = "emoji"; em.textContent = e.emoji;
          b.appendChild(em);
          tl.fromTo(b, { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.55, ease: "back.out(2.2)" }, e.t);
          tl.to(em, { y: -18, duration: 1.4, ease: "sine.inOut", yoyo: true, repeat: -1 }, e.t + 0.4);
        },
        selo(palco, e, c) {
          const b = document.createElement("div");
          b.className = "selo"; b.style.top = e.y + "px";
          const d = document.createElement("div");
          d.textContent = e.texto;
          b.appendChild(d);
          palco.appendChild(b);
          tl.fromTo(b, { opacity: 0, scale: 1.7, rotation: -6 }, { opacity: 1, scale: 1, rotation: -2, duration: 0.35, ease: "back.out(2)" }, e.t);
        },
        // Nós ligados por setas. layout "vertical": 1 -> 2 -> 3. layout "bifurca": 1 em cima, 2 e 3 embaixo.
        fluxo_icones(palco, e, c) {
          const itens = e.itens;
          if (e.layout === "bifurca") {
            const topo = criarNo(palco, 340, e.y, itens[0]);
            const esq = criarNo(palco, 90, e.y + 560, itens[1]);
            const dir = criarNo(palco, 590, e.y + 560, itens[2]);
            entrarNo(topo, e.ts[0]); entrarNo(esq, e.ts[1]); entrarNo(dir, e.ts[2]);
            criarSeta(palco, 470, e.y + 345, 290, e.y + 545, cor(itens[1].cor), e.ts[1] - 0.45);
            criarSeta(palco, 610, e.y + 345, 790, e.y + 545, cor(itens[2].cor), e.ts[2] - 0.45);
          } else {
            const nos = itens.map((it, i) => criarNo(palco, 340, e.y + i * 500, it));
            nos.forEach((n, i) => entrarNo(n, e.ts[i]));
            for (let i = 0; i < nos.length - 1; i++) {
              criarSeta(palco, 540, e.y + i * 500 + 345, 540, e.y + (i + 1) * 500 - 15, cor(itens[i + 1].cor), e.ts[i + 1] - 0.45);
            }
          }
        },
      };

      document.fonts.ready.then(() => {
        D.cenas.forEach((c, i) => {
          const palco = document.getElementById("cena-" + c.id).firstElementChild;
          c.elementos.forEach((e) => construtores[e.tipo](palco, e, c));
          tl.fromTo(palco, { scale: 1.0 }, { scale: 1.04, duration: c.duracao, ease: "none" }, c.inicio);
          if (i < D.cenas.length - 1) {
            tl.to(palco, { opacity: 0, duration: 0.25, ease: "power2.in" }, c.inicio + c.duracao - 0.25);
          } else {
            tl.to(palco, { opacity: 0, duration: 0.5, ease: "power1.in" }, c.inicio + c.duracao - 0.5);
          }
        });
        const caixaLegenda = document.getElementById("legendas");
        D.legenda.forEach((b) => {
          const el = document.createElement("div");
          el.className = "bloco-legenda";
          el.textContent = b.texto;
          caixaLegenda.appendChild(el);
          tl.set(el, { opacity: 1 }, b.t);
          tl.set(el, { opacity: 0 }, b.fim);
        });
        window.__timelines["main"] = tl;
      });
    </script>
  </body>
</html>
