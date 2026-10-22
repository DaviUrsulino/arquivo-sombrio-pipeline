<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Pixel biblioteca</title>
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
        --vermelho: #ff5c5c; --amarelo: #ffd84a; --branco: #f4f1ea; --rosa: #ff7ad9;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #0b0814; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Space Mono", monospace; font-weight: 700; color: var(--branco); }
      canvas.pix { image-rendering: pixelated; image-rendering: crisp-edges; }
      #cenario { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
      #sombra { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(8,6,16,.78) 0%, rgba(8,6,16,.62) 55%, rgba(8,6,16,.7) 100%); }
      .tocha { position: absolute; width: 360px; height: 360px; border-radius: 50%; background: radial-gradient(circle, rgba(255,160,60,.42) 0%, rgba(255,120,30,.14) 45%, transparent 70%); mix-blend-mode: screen; }
      #scan { position: absolute; inset: 0; pointer-events: none; opacity: .16; background: repeating-linear-gradient(0deg, rgba(0,0,0,.6) 0 3px, transparent 3px 6px); }
      .cena, .palco { position: absolute; inset: 0; }
      .el { position: absolute; opacity: 0; }
      .centro { left: 0; width: 1080px; display: flex; flex-direction: column; align-items: center; }
      .rot { font-size: 64px; text-align: center; text-transform: uppercase; text-shadow: 5px 5px 0 #000; line-height: 1.1; padding: 0 60px; }
      .titulo { width: 1080px; text-align: center; line-height: 1.12; text-transform: uppercase; padding: 0 50px; }
      .titulo div { text-shadow: 6px 6px 0 #000; }
      .titulo span { opacity: 1; }
      .caixa { background: rgba(13,11,28,.94); border: 8px solid #f4f1ea; box-shadow: 12px 12px 0 #000; }
      .no { position: absolute; width: 320px; height: 360px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; opacity: 0; }
      .no .rot { font-size: 46px; padding: 0 8px; }
      .janela { position: absolute; left: 70px; width: 940px; background: #0d0b1c; border: 8px solid #f4f1ea; box-shadow: 14px 14px 0 #000; opacity: 0; }
      .janela .barra { display: flex; gap: 14px; align-items: center; padding: 16px 20px; background: #f4f1ea; }
      .janela .barra b { width: 22px; height: 22px; display: block; }
      .janela .barra em { margin-left: auto; font-style: normal; color: #0d0b1c; font-size: 30px; }
      .janela .corpo { padding: 34px 40px 40px; }
      .janela .cmd { font-size: 80px; color: var(--verde); text-shadow: 4px 4px 0 #000; white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.12; }
      .janela .cmd span, .janela .desc span { opacity: 1; }
      .janela .cursor { display: inline-block; width: 40px; height: 70px; background: var(--verde); vertical-align: -8px; margin-left: 6px; }
      .janela .desc { margin-top: 24px; font-size: 52px; line-height: 1.25; color: var(--branco); }
      .cartao { position: absolute; width: 440px; opacity: 0; background: rgba(13,11,28,.95); border: 8px solid #f4f1ea; box-shadow: 12px 12px 0 #000; }
      .cartao .topo { padding: 14px 10px; text-align: center; font-size: 36px; color: #0d0b1c; letter-spacing: .05em; }
      .cartao .meio { display: flex; justify-content: center; padding: 26px 0 16px; }
      .cartao .linha { padding: 8px 24px; font-size: 26px; color: #cfc9e0; }
      .cartao .seg { display: flex; gap: 6px; margin-top: 8px; }
      .cartao .seg i { display: block; width: 24px; height: 22px; background: #2b2542; }
      .cartao .seg i.on { background: var(--c); }
      .celular { position: absolute; left: 320px; width: 440px; height: 900px; background: #0c0b12; border: 10px solid #3a3a46; border-radius: 56px; box-shadow: 0 0 0 4px #000, 14px 14px 0 #000; opacity: 0; overflow: hidden; }
      .celular .entalhe { position: absolute; left: 50%; top: 14px; width: 130px; height: 28px; margin-left: -65px; background: #000; border-radius: 16px; }
      .celular .tela { position: absolute; inset: 0; padding: 70px 24px 24px; }
      .celular .tit { font-size: 34px; margin-bottom: 20px; }
      .celular .lin { display: flex; gap: 14px; align-items: center; margin-bottom: 22px; opacity: 0; }
      .celular .lin i { flex: none; width: 52px; height: 52px; border-radius: 50%; display: block; }
      .celular .lin div { font-size: 28px; line-height: 1.15; }
      .celular .lin small { display: block; font-size: 22px; color: #8d88a3; }
      .celular .app { width: 74px; height: 74px; border-radius: 18px; opacity: 0; }
      .grade { display: grid; grid-template-columns: repeat(4, 74px); gap: 28px 22px; justify-content: center; margin-top: 30px; }
      .banner { position: absolute; left: 60px; width: 960px; opacity: 0; display: flex; align-items: center; gap: 28px; padding: 22px 30px; background: #f4f1ea; border: 8px solid #000; box-shadow: 12px 12px 0 #000; color: #0d0b1c; }
      .banner small { display: block; font-size: 26px; color: #5a5470; text-transform: uppercase; }
      .banner b { font-size: 42px; word-break: break-all; }
      .gigante { font-size: 230px; line-height: 1; color: var(--amarelo); text-shadow: 8px 8px 0 #000; text-align: center; width: 1080px; }
      .lista-item { display: flex; align-items: center; gap: 26px; width: 940px; padding: 26px 30px; margin-bottom: 26px; opacity: 0; font-size: 58px; line-height: 1.15; }
      .selo-pixel { position: absolute; left: 0; width: 1080px; text-align: center; opacity: 0; }
      .selo-pixel div { display: inline-block; font-size: 62px; padding: 14px 40px; background: var(--amarelo); color: #0d0b1c; border: 8px solid #000; box-shadow: 10px 10px 0 #000; }
      .sala { position: absolute; left: 0; width: 1080px; opacity: 0; }
      .posto { position: absolute; top: 0; width: 220px; opacity: 0; text-align: center; }
      .posto-bicho { position: absolute; top: 0; left: 50%; width: 126px; margin-left: -63px; }
      .tela-mesa { position: absolute; top: 106px; left: 25px; width: 170px; height: 120px; background: #0d0b1c; border: 6px solid #000; box-shadow: 8px 8px 0 #000; overflow: hidden; padding: 16px 14px; box-sizing: border-box; }
      .tela-mesa .linha-codigo { position: absolute; left: 14px; height: 10px; border-radius: 2px; }
      .superficie { position: absolute; top: 226px; left: 13px; width: 194px; height: 18px; background: #3a2a1c; border: 4px solid #1c130c; box-shadow: 6px 6px 0 #000; }
      .sala .rot { position: absolute; top: 300px; left: 0; width: 1080px; }
      #robo { position: absolute; left: 0; top: 1290px; width: 210px; height: 225px; }
      #robo svg { position: absolute; left: 0; top: 0; opacity: 0; }
      #legenda { position: absolute; left: 0; top: 1590px; width: 1080px; height: 190px; }
      .bloco-legenda { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; opacity: 0; }
      .bloco-legenda div { background: rgba(8,6,16,.9); border: 4px solid rgba(244,241,234,.28); border-radius: 18px; padding: 14px 32px 18px; font-size: 62px; line-height: 1.1; text-align: center; text-transform: uppercase; max-width: 960px; }
      .bloco-legenda .dest { color: var(--amarelo); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <canvas id="cenario" class="pix clip" width="108" height="192" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></canvas>
      <div id="sombra" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
      <div id="tochas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="2"></div>
{{CENAS}}
      <div id="robo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="6"></div>
      <div id="scan" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="7"></div>
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <audio id="trilha" src="assets/musica/trilha-pixel.mp3" data-start="0" data-duration="{{DURACAO}}" data-track-index="10" data-volume="0.25"></audio>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const D = window.DADOS;
      const tl = gsap.timeline({ paused: true });
      const SVGNS = "http://www.w3.org/2000/svg";
      const cor = (nome) => `var(--${nome || "branco"})`;
      const HEX = { laranja: "#ff9d3c", azul: "#5fb4ff", verde: "#4ee06a", roxo: "#b48cff", vermelho: "#ff5c5c", amarelo: "#ffd84a", branco: "#f4f1ea", rosa: "#ff7ad9" };
      const formatar = (n, formato) => (formato === "ano" ? String(n) : formato === "cheio" ? n.toLocaleString("pt-BR") : mil(n));
      const mil = (n) => (n >= 10000 ? Math.floor(n / 1000) + " mil" : n >= 1000 ? (n / 1000).toFixed(1).replace(".", ",") + " mil" : String(n));

      // ---------- cenário: biblioteca em pixel art (108x192, ampliada 10x) ----------
      (function cenario() {
        const c = document.getElementById("cenario"); const x = c.getContext("2d");
        let semente = 21; const rnd = () => ((semente = (semente * 9301 + 49297) % 233280) / 233280);
        for (let y = 0; y < 192; y++) { const t = y / 192; x.fillStyle = `rgb(${Math.round(18 + 10 * t)},${Math.round(13 + 6 * t)},${Math.round(36 + 10 * t)})`; x.fillRect(0, y, 108, 1); }
        const lombadas = ["#7a3b3b", "#3b5a7a", "#4a6b3f", "#8a6a2f", "#5a3b7a", "#2f6b6b", "#7a4a2f", "#4b4b6b"];
        for (let estante = 0; estante < 5; estante++) {
          const topo = 8 + estante * 26, base = topo + 22;
          let px = 1;
          while (px < 107) {
            const w = 2 + Math.floor(rnd() * 3), h = 12 + Math.floor(rnd() * 9);
            x.fillStyle = lombadas[Math.floor(rnd() * lombadas.length)]; x.fillRect(px, base - h, w, h);
            x.fillStyle = "rgba(0,0,0,.28)"; x.fillRect(px + w - 1, base - h, 1, h);
            if (rnd() > 0.7) { x.fillStyle = "rgba(255,216,74,.55)"; x.fillRect(px, base - h + 2, w, 1); }
            px += w + (rnd() > 0.85 ? 2 : 0);
          }
          x.fillStyle = "#3a2a1c"; x.fillRect(0, base, 108, 3);
          x.fillStyle = "#1c130c"; x.fillRect(0, base + 3, 108, 1);
        }
        // chão de madeira
        x.fillStyle = "#1d1428"; x.fillRect(0, 142, 108, 50);
        x.fillStyle = "#3b2c52"; x.fillRect(0, 142, 108, 1);
        for (let y = 148; y < 192; y += 8) { x.fillStyle = "rgba(0,0,0,.35)"; x.fillRect(0, y, 108, 1); }
        for (let y = 143; y < 192; y += 8) for (let px = Math.floor(rnd() * 20); px < 108; px += 18 + Math.floor(rnd() * 10)) { x.fillStyle = "rgba(0,0,0,.3)"; x.fillRect(px, y, 1, 8); }
        // chamas das tochas (pixels)
        [[7, 118], [100, 118]].forEach(([px, py]) => {
          x.fillStyle = "#4a3320"; x.fillRect(px, py + 5, 2, 8);
          x.fillStyle = "#ff7a1a"; x.fillRect(px - 1, py + 1, 4, 5); x.fillStyle = "#ffd84a"; x.fillRect(px, py + 2, 2, 3);
        });
      })();
      (function tochas() {
        const caixa = document.getElementById("tochas");
        [[75, 1130], [1005, 1130]].forEach(([cx, cy], i) => {
          const t = document.createElement("div"); t.className = "tocha"; t.style.left = (cx - 180) + "px"; t.style.top = (cy - 180) + "px";
          caixa.appendChild(t);
          tl.to(t, { opacity: 0.55, scale: 1.08, duration: 0.7 + i * 0.13, ease: "steps(3)", yoyo: true, repeat: 60 }, 0);
        });
      })();

      // ---------- ícones lucide viram pixel art (rasteriza pequeno, corta o alfa, amplia sem suavizar) ----------
      const ICONES_PIX = {};
      function rasterizar(nome, corHex, grade = 30) {
        return new Promise((resolve) => {
          const svg = `<svg xmlns="${SVGNS}" width="${grade}" height="${grade}" viewBox="0 0 24 24" fill="none" stroke="${corHex}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">${D.icones[nome]}</svg>`;
          const img = new Image();
          img.onload = () => {
            const c = document.createElement("canvas"); c.width = grade; c.height = grade; const x = c.getContext("2d");
            x.drawImage(img, 0, 0, grade, grade);
            const d = x.getImageData(0, 0, grade, grade);
            for (let i = 0; i < d.data.length; i += 4) { d.data[i + 3] = d.data[i + 3] > 70 ? 255 : 0; }
            x.putImageData(d, 0, 0);
            resolve(c);
          };
          img.onerror = () => resolve(document.createElement("canvas"));
          img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
        });
      }
      function icone(nome, corNome, tamanho) {
        const origem = ICONES_PIX[nome + "|" + corNome];
        const c = document.createElement("canvas"); c.className = "pix"; c.width = origem.width; c.height = origem.height;
        c.getContext("2d").drawImage(origem, 0, 0);
        c.style.width = tamanho + "px"; c.style.height = tamanho + "px";
        // sombra dura estilo jogo
        c.style.filter = "drop-shadow(6px 6px 0 #000)";
        return c;
      }

      // ---------- robô ----------
      const PX = 15;
      const CORES = { O: "#ff9d3c", D: "#2a1608", W: "#ffffff", P: "#2a1608", Y: "#ffd84a", M: "#2a1608", B: "#c96a14" };
      const BASE = [
        "......YY......", ".......D......", "..DDDDDDDDDD..", ".DOOOOOOOOOOD.", ".DOWWOOOOWWOD.",
        ".DOWPOOOOPWOD.", ".DOOOOOOOOOOD.", ".DOOOOOOOOOOD.", "..DDDDDDDDDD..", "...DOOOOOOD...",
        "..DOOBOOBOOD..", ".DDOOOOOOOODD.", "..D.DOOOOD.D..", "....DD..DD....", "...DDD..DDD...",
      ];
      const POSES = {
        normal: {},
        feliz: { 7: ".DOOMOOOOMOOD." , 8: "..DDDMMMMDDD.." },
        animado: { 7: ".DOMMMMMMMMOD.", 9: "D..DOOOOOOD..D", 10: "DD.OOBOOBOO.DD", 11: ".D.OOOOOOOO.D.", 12: "..D.DOOOOD.D.." },
        pensando: { 5: ".DOWPOOOOWPOD.", 7: ".DOOOOMMMOOOD." },
      };
      function roboSvg(pose) {
        const g = BASE.slice(); Object.entries(POSES[pose] || {}).forEach(([l, t]) => { g[l] = t.padEnd(14, ".").slice(0, 14); });
        const s = document.createElementNS(SVGNS, "svg");
        s.setAttribute("width", 14 * PX); s.setAttribute("height", g.length * PX); s.setAttribute("viewBox", `0 0 14 ${g.length}`); s.setAttribute("shape-rendering", "crispEdges");
        g.forEach((l, y) => [...l].forEach((ch, x) => { if (ch === ".") return; const r = document.createElementNS(SVGNS, "rect"); r.setAttribute("x", x); r.setAttribute("y", y); r.setAttribute("width", 1); r.setAttribute("height", 1); r.setAttribute("fill", CORES[ch] || "#f0f"); s.appendChild(r); }));
        return s;
      }

      // bichinho de mesa: mesmo grid do robô principal, só troca a cor do corpo (cada colega um tom).
      function bichoSvg(corHexCorpo) {
        const PXB = 9;
        const s = document.createElementNS(SVGNS, "svg");
        s.setAttribute("width", 14 * PXB); s.setAttribute("height", BASE.length * PXB);
        s.setAttribute("viewBox", `0 0 14 ${BASE.length}`); s.setAttribute("shape-rendering", "crispEdges");
        BASE.forEach((l, y) => [...l].forEach((ch, x) => {
          if (ch === ".") return;
          const r = document.createElementNS(SVGNS, "rect");
          r.setAttribute("x", x); r.setAttribute("y", y); r.setAttribute("width", 1); r.setAttribute("height", 1);
          r.setAttribute("fill", ch === "O" ? corHexCorpo : (CORES[ch] || "#f0f"));
          s.appendChild(r);
        }));
        return s;
      }

      function porLetra(pai, texto) { for (const ch of texto) { const s = document.createElement("span"); s.textContent = ch; pai.appendChild(s); } }
      function digitar(letras, t, passo) { tl.fromTo(letras, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: passo, ease: "none" }, t); }
      function div(pai, classe, estilo = {}, html = "") { const d = document.createElement("div"); d.className = classe; Object.assign(d.style, estilo); d.innerHTML = html; pai.appendChild(d); return d; }
      function rotulo(pai, texto, corNome, y, tamanho) {
        const r = div(pai, "el centro", { top: y + "px" }); const d = div(r, "rot", { color: cor(corNome), fontSize: (tamanho || 54) + "px" }, ""); d.textContent = texto; return r;
      }
      function entrar(el, t, extra = {}) { tl.fromTo(el, { opacity: 0, y: 40, scale: 0.85, ...extra }, { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "steps(5)" }, t); }
      function ligacao(palco, x1, y1, x2, y2, corNome, t) {
        const s = document.createElementNS(SVGNS, "svg"); s.setAttribute("width", 1080); s.setAttribute("height", 1920); s.style.cssText = "position:absolute;left:0;top:0;overflow:visible";
        const l = document.createElementNS(SVGNS, "line"); l.setAttribute("x1", x1); l.setAttribute("y1", y1); l.setAttribute("x2", x2); l.setAttribute("y2", y2);
        l.setAttribute("stroke", HEX[corNome] || "#fff"); l.setAttribute("stroke-width", 8); l.setAttribute("stroke-dasharray", "14 12"); s.appendChild(l); palco.appendChild(s);
        tl.set(s, { opacity: 0 }, 0); tl.to(s, { opacity: 1, duration: 0.05 }, t); tl.fromTo(l, { attr: { "stroke-dashoffset": 80 } }, { attr: { "stroke-dashoffset": 0 }, duration: 0.5, ease: "none" }, t);
      }

      const construtores = {
        titulo_pixel(palco, e) {
          const caixa = div(palco, "el titulo", { top: e.y + "px", left: "0" }); const todas = [];
          e.linhas.forEach((l) => { const d = document.createElement("div"); d.style.fontSize = (l.tamanho || e.tamanho || 110) + "px"; d.style.color = cor(l.cor); porLetra(d, l.texto); todas.push(...d.querySelectorAll("span")); caixa.appendChild(d); });
          tl.set(caixa, { opacity: 1 }, e.t); tl.fromTo(caixa, { y: -40 }, { y: 0, duration: 0.25, ease: "steps(5)" }, e.t); digitar(todas, e.t, 0.03);
        },
        icone_pixel(palco, e) {
          const bloco = div(palco, "el centro", { top: e.y + "px", gap: "20px" });
          bloco.appendChild(icone(e.icone, e.cor, e.tamanho || 460));
          if (e.rotulo) { const r = div(bloco, "rot", { color: cor(e.cor) }); r.textContent = e.rotulo; }
          entrar(bloco, e.t); tl.to(bloco.firstChild, { y: -16, duration: 0.6, ease: "steps(2)", yoyo: true, repeat: 14 }, e.t + 0.5);
        },
        cadeia(palco, e) {
          const n = e.nos.length, h = e.layout === "horizontal";
          const X2 = [90, 670], X3 = [20, 380, 740];
          const pos = (i) => (h ? [(n === 2 ? X2 : X3)[i], e.y] : [380, e.y + i * 400]);
          e.nos.forEach((no, i) => {
            const [xx, y] = pos(i);
            const d = div(palco, "no", { left: xx + "px", top: y + "px" }); d.appendChild(icone(no.icone, no.cor, 230));
            const r = div(d, "rot", { color: cor(no.cor) }); r.textContent = no.rotulo; entrar(d, e.ts[i]);
            if (i > 0) { const [px, py] = pos(i - 1);
              ligacao(palco, px + (h ? 320 : 160), py + (h ? 120 : 340), xx + (h ? 0 : 160), y + (h ? 120 : 0), no.cor, e.ts[i] - 0.35); }
          });
        },
        niveis(palco, e) {
          const base = e.y + 700, larg = 260, gap = 40, total = e.itens.length * larg + (e.itens.length - 1) * gap, x0 = (1080 - total) / 2;
          e.itens.forEach((it, i) => {
            const h = 220 + it.altura * 150, x = x0 + i * (larg + gap);
            const col = div(palco, "el caixa", { left: x + "px", top: (base - h) + "px", width: larg + "px", height: h + "px", background: HEX[it.cor], borderColor: "#000", textAlign: "center", paddingTop: "24px", transformOrigin: "50% 100%" });
            col.innerHTML = `<div style="font-size:${it.rotulo.length > 8 ? 34 : 44}px;color:#0d0b1c">${it.rotulo}</div><div style="font-size:50px;color:#0d0b1c;margin-top:14px">${"★".repeat(it.altura)}</div>`;
            tl.fromTo(col, { opacity: 0, scaleY: 0.1 }, { opacity: 1, scaleY: 1, duration: 0.5, ease: "steps(6)" }, e.ts[i]);
          });
        },
        comparar(palco, e) {
          [[e.esq, 50, 0], [e.dir, 590, 1]].forEach(([lado, x, i]) => {
            const c = div(palco, "cartao", { left: x + "px", top: e.y + "px" });
            c.innerHTML = `<div class="topo" style="background:${HEX[lado.cor]}">${lado.titulo}</div><div class="meio"></div>` + lado.linhas.map((l) => `<div class="linha">${l.rotulo}<div class="seg">${Array.from({ length: 8 }, (_, k) => `<i class="${k < l.valor ? "on" : ""}" style="--c:${HEX[lado.cor]}"></i>`).join("")}</div></div>`).join("") + `<div style="height:20px"></div>`;
            c.querySelector(".meio").appendChild(icone(lado.icone, lado.cor, 170)); entrar(c, e.ts[i]);
          });
        },
        celular(palco, e) {
          const t = div(palco, "celular", { top: e.y + "px" });
          t.innerHTML = `<div class="entalhe"></div><div class="tela"><div class="tit" style="color:${HEX[e.cor || "branco"]}"></div></div>`;
          const tela = t.querySelector(".tela"); tela.querySelector(".tit").textContent = e.titulo || "";
          const cores = ["#ff7a59", "#5fb4ff", "#4ee06a", "#b48cff", "#ffd84a", "#ff7ad9"];
          const alvos = [];
          if (e.conteudo === "apps") { const g = div(tela, "grade"); (e.itens || Array.from({ length: 16 })).forEach((_, i) => { const a = div(g, "app", { background: cores[i % cores.length] }); alvos.push(a); }); }
          else { (e.itens || []).forEach((it, i) => { const l = div(tela, "lin", {}, `<i style="background:${cores[i % cores.length]}"></i><div>${it.nome}<small>${it.texto}</small></div>`); alvos.push(l); }); }
          tl.fromTo(t, { opacity: 0, y: 500 }, { opacity: 1, y: 0, duration: 0.5, ease: "steps(6)" }, e.ts[0]);
          const ini = e.ts[Math.min(1, e.ts.length - 1)];
          tl.fromTo(alvos, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.3, stagger: 0.18, ease: "steps(3)" }, ini);
        },
        banner_repo(palco, e) {
          const d = div(palco, "banner", { top: e.y + "px" });
          d.appendChild(icone("github", "preto", 100)); const tx = div(d, "", {}, `<small>${e.rotulo || "repositório gratuito"}</small><b>${e.url}</b>`);
          tl.fromTo(d, { opacity: 0, y: -80 }, { opacity: 1, y: 0, duration: 0.35, ease: "steps(5)" }, e.t);
        },
        contador(palco, e) {
          const valor = e.valor !== undefined ? e.valor : D.repos[e.repo].estrelas; const bloco = div(palco, "el centro", { top: e.y + "px", gap: "10px" });
          const ic = icone("star", "amarelo", 190); bloco.appendChild(ic);
          const num = div(bloco, "gigante"); const r = div(bloco, "rot", {}, ""); r.textContent = e.rotulo || "estrelas no GitHub";
          entrar(bloco, e.t); const est = { v: 0 }; num.textContent = "0";
          tl.to(est, { v: valor, duration: 1.4, ease: "power2.out", onUpdate: () => { num.textContent = formatar(Math.round(est.v), e.formato); } }, e.t + 0.1);
        },
        lista(palco, e) {
          const bloco = div(palco, "el centro", { top: e.y + "px", opacity: 1 });
          e.itens.forEach((txt, i) => {
            const li = div(bloco, "lista-item caixa"); li.appendChild(icone("check", "verde", 84)); const t = div(li, "", {}, ""); t.textContent = txt;
            tl.fromTo(li, { opacity: 0, x: -120 }, { opacity: 1, x: 0, duration: 0.35, ease: "steps(5)" }, e.ts[i]);
          });
        },
        terminal(palco, e) {
          const j = div(palco, "janela", { top: e.y + "px" });
          j.innerHTML = `<div class="barra"><b style="background:#ff5c5c"></b><b style="background:#ffd84a"></b><b style="background:#4ee06a"></b><em>${e.rotulo || "terminal"}</em></div><div class="corpo"><div class="cmd"></div><div class="desc"></div></div>`;
          const cmd = j.querySelector(".cmd"), desc = j.querySelector(".desc"); porLetra(cmd, e.comando);
          const cur = document.createElement("i"); cur.className = "cursor"; cmd.appendChild(cur); if (e.texto) porLetra(desc, e.texto);
          tl.fromTo(j, { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.3, ease: "steps(4)" }, e.ts[0]);
          digitar([...cmd.querySelectorAll("span")], e.ts[0] + 0.2, 0.06);
          tl.to(cur, { opacity: 0, duration: 0.01, yoyo: true, repeat: 30, repeatDelay: 0.35 }, e.ts[0] + 0.6);
          if (e.texto) digitar([...desc.querySelectorAll("span")], e.ts[1] || e.ts[0] + 1, 0.026);
        },
        sala_pixel(palco, e) {
          const n = Math.min(4, Math.max(2, e.personagens || 3));
          const paleta = ["laranja", "azul", "verde", "roxo", "amarelo"];
          // larguras de "linha de código" pré-definidas (determinístico: nada de Math.random, o
          // render precisa dar o mesmo frame sempre que buscado de novo).
          const PADROES = [0.92, 0.48, 0.78, 0.34, 0.68, 0.9, 0.42, 0.82, 0.58, 0.95];
          const LARG_POSTO = 220, GAP = 24;
          const total = n * LARG_POSTO + (n - 1) * GAP, x0 = (1080 - total) / 2;
          const caixa = div(palco, "el sala", { top: e.y + "px" });
          for (let i = 0; i < n; i++) {
            const corHex = HEX[paleta[i % paleta.length]];
            const posto = div(caixa, "posto", { left: (x0 + i * (LARG_POSTO + GAP)) + "px" });
            // o bichinho fica num wrapper próprio, posicionado absoluto (igual aos outros visuais
            // já testados do molde) -- svg solto dentro de flex não se mexia no render de verdade.
            const bichoWrap = div(posto, "posto-bicho");
            const bicho = bichoSvg(corHex);
            bichoWrap.appendChild(bicho);
            const telaMesa = div(posto, "tela-mesa");
            [0, 1, 2].forEach((j) => {
              const largura = PADROES[(i * 3 + j) % PADROES.length];
              div(telaMesa, "linha-codigo", {
                top: (12 + j * 20) + "px", width: Math.round(largura * 142) + "px",
                background: corHex, opacity: 0.85 - j * 0.15,
              });
            });
            div(posto, "superficie");
            // Só a entrada anima (confirmado que aparece no render final). Tween de movimento num
            // elemento criado em runtime, com os 3 personagens juntos, não apareceu em várias
            // tentativas isoladas -- fica estático por ora; ver ADR/nota pra investigar depois.
            tl.fromTo(posto, { opacity: 0, y: 30, scale: 0.85 }, { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "steps(5)" }, e.t + i * 0.08);
          }
          tl.set(caixa, { opacity: 1 }, e.t);
          if (e.rotulo) { const r = div(caixa, "rot", { color: cor(e.cor) }); r.textContent = e.rotulo; }
        },
        selo_pixel(palco, e) {
          const b = div(palco, "selo-pixel", { top: e.y + "px" }, `<div>${e.texto}</div>`);
          tl.fromTo(b, { opacity: 0, scale: 1.6 }, { opacity: 1, scale: 1, duration: 0.25, ease: "steps(4)" }, e.t);
        },
      };

      // ícones necessários (cor + nome) para rasterizar antes de montar a linha do tempo
      function iconesNecessarios() {
        const s = new Set(["github|preto", "star|amarelo", "check|verde"]);
        const olhar = (o) => { if (!o || typeof o !== "object") return; if (o.icone && D.icones[o.icone]) s.add(o.icone + "|" + (o.cor || "branco")); Object.values(o).forEach((v) => Array.isArray(v) ? v.forEach(olhar) : olhar(v)); };
        D.cenas.forEach((c) => c.elementos.forEach(olhar)); return [...s];
      }
      const HEX_RAST = { ...HEX, preto: "#0d0b1c" };

      document.fonts.ready.then(async () => {
        await Promise.all(iconesNecessarios().map(async (k) => { const [n, c] = k.split("|"); ICONES_PIX[k] = await rasterizar(n, HEX_RAST[c] || "#ffffff"); }));
        // robô: 4 poses empilhadas; troca por cena e anda no chão
        const robo = document.getElementById("robo"); const poses = {};
        Object.keys(POSES).forEach((p) => { const s = roboSvg(p); robo.appendChild(s); poses[p] = s; });
        tl.set(robo, { x: 120 }, 0);
        D.cenas.forEach((c, i) => {
          const palco = document.getElementById("cena-" + c.id).firstElementChild;
          c.elementos.forEach((e) => { if (construtores[e.tipo]) construtores[e.tipo](palco, e); });
          tl.set(palco, { opacity: 1 }, c.inicio);
          tl.to(palco, { opacity: 0, duration: 0.18, ease: "steps(3)" }, c.inicio + c.duracao - 0.18);
          const pose = c.humor && poses[c.humor] ? c.humor : "normal"; const alvoX = [120, 430, 760, 560, 240][i % 5];
          Object.entries(poses).forEach(([nome, s]) => tl.set(s, { opacity: nome === pose ? 1 : 0 }, c.inicio));
          tl.to(robo, { x: alvoX, duration: Math.min(1.1, c.duracao * 0.5), ease: "steps(8)" }, c.inicio + 0.1);
          tl.to(robo, { y: -PX, duration: 0.3, ease: "steps(1)", yoyo: true, repeat: Math.floor(c.duracao / 0.3) }, c.inicio + 0.1);
        });
        const caixa = document.getElementById("legenda"); const destaque = new Set((D.destaques || []).map((p) => p.toLowerCase()));
        D.legenda.forEach((b) => {
          const el = div(caixa, "bloco-legenda"); const t = document.createElement("div");
          t.innerHTML = b.texto.split(" ").map((p) => { const limpa = p.toLowerCase().replace(/[^a-zà-ú0-9\/.]/g, ""); return destaque.has(limpa) ? `<span class="dest">${p}</span>` : p; }).join(" ");
          el.appendChild(t); tl.set(el, { opacity: 1 }, b.t); tl.set(el, { opacity: 0 }, b.fim);
        });
        window.__timelines["main"] = tl;
      });
    </script>
  </body>
</html>
