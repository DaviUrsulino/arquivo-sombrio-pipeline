<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1350" />
    <title>Carrossel pixel</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      @font-face {
        font-family: "Space Mono";
        src: url("assets/fonts/SpaceMono-Bold.woff2") format("woff2");
        font-weight: 700;
      }
      :root {
        --laranja: #ff9d3c; --azul: #5fb4ff; --verde: #4ee06a; --roxo: #b48cff;
        --vermelho: #ff5c5c; --amarelo: #ffd84a; --branco: #f4f1ea;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1350px; overflow: hidden; background: #0a0818; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Space Mono", monospace; font-weight: 700; color: var(--branco); }
      .slide { position: absolute; inset: 0; background: linear-gradient(180deg, #120b2e 0%, #0b0a1f 55%, #1a0f2b 100%); }
      .estrelas { position: absolute; inset: 0; }
      .scan { position: absolute; inset: 0; pointer-events: none; opacity: .22; background: repeating-linear-gradient(0deg, rgba(0,0,0,.55) 0 3px, transparent 3px 6px); }
      .chao {
        position: absolute; left: 0; right: 0; bottom: 0; height: 200px;
        background: repeating-linear-gradient(90deg, rgba(255,255,255,.07) 0 4px, transparent 4px 72px), repeating-linear-gradient(0deg, rgba(255,255,255,.07) 0 4px, transparent 4px 72px);
        border-top: 6px solid rgba(255,157,60,.6);
      }
      .hud { position: absolute; top: 56px; left: 60px; right: 60px; display: flex; align-items: center; gap: 24px; font-size: 36px; letter-spacing: .06em; color: var(--amarelo); text-shadow: 4px 4px 0 #000; }
      .hud .barra { flex: 1; height: 30px; border: 6px solid #f4f1ea; background: #1a1433; padding: 4px; }
      .hud .barra i { display: block; height: 100%; background: repeating-linear-gradient(90deg, var(--verde) 0 18px, #2a9d46 18px 22px); }
      .titulo { position: absolute; left: 0; width: 1080px; text-align: center; line-height: 1.12; text-transform: uppercase; padding: 0 50px; }
      .titulo div { text-shadow: 6px 6px 0 #000; }
      .sub { position: absolute; left: 0; width: 1080px; text-align: center; padding: 0 70px; font-size: 48px; line-height: 1.25; text-shadow: 4px 4px 0 #000; }
      .janela { position: absolute; left: 70px; width: 940px; background: #0d0b1c; border: 8px solid #f4f1ea; box-shadow: 14px 14px 0 #000; }
      .janela .barra { display: flex; gap: 14px; align-items: center; padding: 16px 20px; background: #f4f1ea; }
      .janela .barra b { width: 22px; height: 22px; display: block; }
      .janela .barra em { margin-left: auto; font-style: normal; color: #0d0b1c; font-size: 30px; }
      .janela .corpo { padding: 40px 44px 46px; }
      .janela .cmd { font-size: 104px; color: var(--verde); text-shadow: 4px 4px 0 #000; }
      .janela .cursor { display: inline-block; width: 48px; height: 94px; background: var(--verde); vertical-align: -12px; margin-left: 6px; }
      .janela .desc { margin-top: 28px; font-size: 46px; line-height: 1.3; overflow-wrap: anywhere; }
      .robo { position: absolute; image-rendering: pixelated; }
      .rodape { position: absolute; left: 60px; right: 60px; bottom: 28px; display: flex; justify-content: space-between; font-size: 30px; color: #9a96a8; text-shadow: 3px 3px 0 #000; }
      .selo { position: absolute; left: 0; width: 1080px; text-align: center; }
      .selo div { display: inline-block; font-size: 70px; padding: 16px 44px; background: var(--amarelo); color: #0d0b1c; border: 8px solid #000; box-shadow: 10px 10px 0 #000; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1350" data-duration="{{DURACAO}}">
{{SLIDES}}
    </div>
    <script>
      const D = window.DADOS;
      const tl = gsap.timeline({ paused: true });
      const SVG = "http://www.w3.org/2000/svg";
      const cor = (nome) => `var(--${nome || "branco"})`;
      const PX = 10;
      const CORES = { O: "#ff9d3c", D: "#2a1608", W: "#ffffff", P: "#2a1608", Y: "#ffd84a", M: "#2a1608", B: "#c96a14" };
      const BASE = [
        "......YY......", ".......D......", "..DDDDDDDDDD..", ".DOOOOOOOOOOD.", ".DOWWOOOOWWOD.",
        ".DOWPOOOOPWOD.", ".DOOOOOOOOOOD.", ".DOMMMMMMMMOD.", "..DDDDDDDDDD..", "...DOOOOOOD...",
        "..DOOBOOBOOD..", ".DDOOOOOOOODD.", "..D.DOOOOD.D..", "....DD..DD....", "...DDD..DDD...",
      ];
      function robo(x, y, escala = 1) {
        const svg = document.createElementNS(SVG, "svg");
        const p = PX * escala;
        svg.setAttribute("width", 14 * p); svg.setAttribute("height", BASE.length * p);
        svg.setAttribute("viewBox", `0 0 14 ${BASE.length}`); svg.setAttribute("shape-rendering", "crispEdges");
        svg.setAttribute("class", "robo"); svg.style.left = x + "px"; svg.style.top = y + "px";
        BASE.forEach((linha, yy) => [...linha].forEach((c, xx) => {
          if (c === ".") return;
          const r = document.createElementNS(SVG, "rect");
          r.setAttribute("x", xx); r.setAttribute("y", yy); r.setAttribute("width", 1); r.setAttribute("height", 1);
          r.setAttribute("fill", CORES[c]); svg.appendChild(r);
        }));
        return svg;
      }
      function estrelas(pai, semente0) {
        const caixa = document.createElement("div"); caixa.className = "estrelas";
        let semente = semente0;
        const rnd = () => ((semente = (semente * 9301 + 49297) % 233280) / 233280);
        for (let i = 0; i < 50; i++) {
          const s = document.createElement("div"); const t = 4 + Math.floor(rnd() * 3) * 2;
          s.style.cssText = `position:absolute;left:${Math.floor(rnd() * 1080)}px;top:${Math.floor(rnd() * 1100)}px;width:${t}px;height:${t}px;background:#fff;opacity:${0.25 + rnd() * 0.6}`;
          caixa.appendChild(s);
        }
        pai.appendChild(caixa);
      }
      function hud(pai, texto, progresso) {
        const h = document.createElement("div"); h.className = "hud";
        h.innerHTML = `<span>${texto}</span><div class="barra"><i style="width:${progresso * 100}%"></i></div>`;
        pai.appendChild(h);
      }
      function titulo(pai, y, linhas, tamanho) {
        const t = document.createElement("div"); t.className = "titulo"; t.style.top = y + "px";
        linhas.forEach((l) => {
          const d = document.createElement("div"); d.style.fontSize = (l.tamanho || tamanho) + "px"; d.style.color = cor(l.cor);
          d.textContent = l.texto; t.appendChild(d);
        });
        pai.appendChild(t);
      }
      function janela(pai, y, comando, texto, rotulo) {
        const j = document.createElement("div"); j.className = "janela"; j.style.top = y + "px";
        j.innerHTML = `<div class="barra"><b style="background:#ff5c5c"></b><b style="background:#ffd84a"></b><b style="background:#4ee06a"></b><em>${rotulo || "terminal"}</em></div><div class="corpo"><div class="cmd" style="font-size:${comando.length <= 12 ? 104 : comando.length <= 26 ? 66 : 46}px;overflow-wrap:anywhere;line-height:1.15">${comando}<i class="cursor"></i></div><div class="desc">${texto}</div></div>`;
        pai.appendChild(j);
      }

      document.fonts.ready.then(() => {
        const total = D.slides.length;
        D.slides.forEach((s, i) => {
          const el = document.getElementById("s" + (i + 1));
          estrelas(el, 11 + i * 17);
          const chao = document.createElement("div"); chao.className = "chao"; el.appendChild(chao);
          if (s.tipo === "capa") {
            hud(el, "NOVO JOGO", 0.1);
            titulo(el, 150, s.linhas, s.tamanho || 104);
            const sub = document.createElement("div"); sub.className = "sub"; sub.style.top = "760px"; sub.style.color = "#f4f1ea";
            sub.textContent = s.subtitulo; el.appendChild(sub);
            el.appendChild(robo(380, 960, 1.6));
            const seta = document.createElement("div"); seta.className = "sub"; seta.style.top = "1210px"; seta.style.fontSize = "44px"; seta.style.color = "#ffd84a";
            seta.textContent = "ARRASTA PRO LADO >>>"; el.appendChild(seta);
          } else if (s.tipo === "ponto") {
            hud(el, s.fase, s.progresso);
            titulo(el, 170, s.linhas, 76);
            const cx = document.createElement("div"); cx.className = "janela"; cx.style.top = "430px";
            cx.innerHTML = `<div class="barra"><b style="background:#ff5c5c"></b><b style="background:#ffd84a"></b><b style="background:#4ee06a"></b><em>${s.rotulo || "nota"}</em></div><div class="corpo"><div class="desc" style="font-size:56px;margin-top:0">${s.texto}</div></div>`;
            el.appendChild(cx);
            el.appendChild(robo(800, 1070, 1.0));
          } else if (s.tipo === "comando") {
            hud(el, s.fase, s.progresso);
            titulo(el, 170, s.linhas, 76);
            janela(el, 470, s.comando, s.texto, s.rotulo);
            el.appendChild(robo(800, 1070, 1.0));
          } else {
            hud(el, "FASE FINAL", 1);
            titulo(el, 210, s.linhas, 100);
            const sub = document.createElement("div"); sub.className = "sub"; sub.style.top = "620px"; sub.textContent = s.subtitulo; el.appendChild(sub);
            const selo = document.createElement("div"); selo.className = "selo"; selo.style.top = "850px";
            selo.innerHTML = `<div>${s.selo || "SIGA E COMENTE " + s.palavra}</div>`; el.appendChild(selo);
            if (s.extra) { const ex = document.createElement("div"); ex.className = "sub"; ex.style.top = "1030px"; ex.style.fontSize = "42px"; ex.style.color = "#ffd84a"; ex.textContent = s.extra; el.appendChild(ex); }
            el.appendChild(robo(380, 1040, 1.3));
          }
          const rod = document.createElement("div"); rod.className = "rodape";
          rod.innerHTML = `<span>@robo.estagiario</span><span>${i + 1}/${total}</span>`; el.appendChild(rod);
          const scan = document.createElement("div"); scan.className = "scan"; el.appendChild(scan);
          tl.set(el, { opacity: 1 }, i);
        });
        window.__timelines["main"] = tl;
      });
    </script>
  </body>
</html>
