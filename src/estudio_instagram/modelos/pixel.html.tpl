<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Pixel arcade</title>
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
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #0a0818; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Space Mono", monospace; font-weight: 700; color: var(--branco); }
      #fundo { position: absolute; inset: 0; background: linear-gradient(180deg, #120b2e 0%, #0b0a1f 45%, #1a0f2b 100%); }
      #estrelas { position: absolute; inset: 0; }
      #scan {
        position: absolute; inset: 0; pointer-events: none; opacity: .22;
        background: repeating-linear-gradient(0deg, rgba(0,0,0,.55) 0 3px, transparent 3px 6px);
      }
      #chao {
        position: absolute; left: 0; right: 0; bottom: 0; height: 330px;
        background:
          linear-gradient(180deg, rgba(255,157,60,.0) 0%, rgba(255,157,60,.12) 100%),
          repeating-linear-gradient(90deg, rgba(255,255,255,.07) 0 4px, transparent 4px 72px),
          repeating-linear-gradient(0deg, rgba(255,255,255,.07) 0 4px, transparent 4px 72px);
        border-top: 6px solid rgba(255,157,60,.6);
      }
      .cena { position: absolute; inset: 0; }
      .palco { position: absolute; inset: 0; }
      .el { position: absolute; opacity: 0; }
      .hud {
        position: absolute; left: 60px; right: 60px; display: flex; align-items: center; gap: 28px;
        font-size: 40px; letter-spacing: .06em; color: var(--amarelo); opacity: 0; text-shadow: 4px 4px 0 #000;
      }
      .hud .barra { flex: 1; height: 34px; border: 6px solid #f4f1ea; background: #1a1433; padding: 4px; }
      .hud .barra i { display: block; height: 100%; background: repeating-linear-gradient(90deg, var(--verde) 0 18px, #2a9d46 18px 22px); width: 0; }
      .titulo { width: 1080px; text-align: center; line-height: 1.12; text-transform: uppercase; padding: 0 50px; }
      .titulo div { text-shadow: 6px 6px 0 #000, -2px -2px 0 rgba(0,0,0,.6); letter-spacing: .02em; }
      .titulo span { opacity: 1; }
      .janela {
        position: absolute; left: 70px; width: 940px; background: #0d0b1c; border: 8px solid #f4f1ea;
        box-shadow: 14px 14px 0 #000; opacity: 0;
      }
      .janela .barra { display: flex; gap: 14px; align-items: center; padding: 16px 20px; background: #f4f1ea; }
      .janela .barra b { width: 22px; height: 22px; display: block; }
      .janela .barra em { margin-left: auto; font-style: normal; color: #0d0b1c; font-size: 30px; }
      .janela .corpo { padding: 40px 44px 44px; }
      .janela .cmd { font-size: 92px; color: var(--verde); text-shadow: 4px 4px 0 #000; white-space: nowrap; }
      .janela .cmd span { opacity: 1; }
      .janela .cursor { display: inline-block; width: 44px; height: 84px; background: var(--verde); vertical-align: -10px; margin-left: 6px; }
      .janela .desc { margin-top: 30px; font-size: 52px; line-height: 1.25; color: var(--branco); }
      .janela .desc span { opacity: 1; }
      .robo { position: absolute; opacity: 0; image-rendering: pixelated; }
      .selo-pixel { position: absolute; left: 0; width: 1080px; text-align: center; opacity: 0; }
      .selo-pixel div { display: inline-block; font-size: 62px; padding: 14px 40px; background: var(--amarelo); color: #0d0b1c; border: 8px solid #000; box-shadow: 10px 10px 0 #000; }
      #legendas { position: absolute; left: 0; top: 1640px; width: 1080px; height: 200px; }
      .bloco-legenda {
        position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; opacity: 0;
        text-align: center; padding: 0 50px; font-size: 70px; line-height: 1.1; color: #fff; text-transform: uppercase;
        text-shadow: 5px 5px 0 #000, -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000;
      }
      .bloco-legenda .dest { color: var(--amarelo); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="estrelas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
      <div id="chao" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="2"></div>
{{CENAS}}
      <div id="scan" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="4"></div>
      <div id="legendas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="5"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const D = window.DADOS;
      const tl = gsap.timeline({ paused: true });
      const SVG = "http://www.w3.org/2000/svg";
      const cor = (nome) => `var(--${nome || "branco"})`;
      const PX = 14; // tamanho de cada "pixel" do robô

      // Estrelas fixas (posições determinísticas, nada de Math.random: o render precisa ser repetível).
      (function estrelas() {
        const caixa = document.getElementById("estrelas");
        let semente = 7;
        const rnd = () => ((semente = (semente * 9301 + 49297) % 233280) / 233280);
        for (let i = 0; i < 70; i++) {
          const s = document.createElement("div");
          const t = 4 + Math.floor(rnd() * 3) * 2;
          s.style.cssText = `position:absolute;left:${Math.floor(rnd() * 1080)}px;top:${Math.floor(rnd() * 1500)}px;width:${t}px;height:${t}px;background:#fff;opacity:${0.25 + rnd() * 0.6}`;
          caixa.appendChild(s);
        }
      })();

      // Sprite do robô: cada letra é um pixel. O = corpo laranja, D = contorno, W = branco, P = pupila, Y = ponta da antena.
      const CORES = { O: "#ff9d3c", D: "#2a1608", W: "#ffffff", P: "#2a1608", Y: "#ffd84a", M: "#2a1608", B: "#c96a14" };
      const BASE = [
        "......YY......",
        ".......D......",
        "..DDDDDDDDDD..",
        ".DOOOOOOOOOOD.",
        ".DOWWOOOOWWOD.",
        ".DOWPOOOOPWOD.",
        ".DOOOOOOOOOOD.",
        ".DOOMMMMMMOOD.",
        "..DDDDDDDDDD..",
        "...DOOOOOOD...",
        "..DOOBOOBOOD..",
        ".DDOOOOOOOODD.",
        "..D.DOOOOD.D..",
        "....DD..DD....",
        "...DDD..DDD...",
      ];
      const POSES = {
        normal: {},
        feliz: { 7: ".DOMOOOOOOMOD." },
        animado: { 7: ".DOMMMMMMMMOD.", 10: "DDOOBOOBOODD..".slice(0, 14), 11: "DDOOOOOOOODD..", 12: "D...DOOOOD..D.", 13: "....DD..DD...." },
        pensando: { 5: ".DOWPOOOOWPOD.", 7: ".DOOOOMMMOOOD." },
      };
      function desenharRobo(pose) {
        const grade = BASE.slice();
        Object.entries(POSES[pose] || {}).forEach(([linha, texto]) => { grade[linha] = texto.padEnd(14, ".").slice(0, 14); });
        const svg = document.createElementNS(SVG, "svg");
        svg.setAttribute("width", 14 * PX); svg.setAttribute("height", grade.length * PX);
        svg.setAttribute("viewBox", `0 0 14 ${grade.length}`); svg.setAttribute("shape-rendering", "crispEdges");
        grade.forEach((linha, y) => [...linha].forEach((c, x) => {
          if (c === ".") return;
          const r = document.createElementNS(SVG, "rect");
          r.setAttribute("x", x); r.setAttribute("y", y); r.setAttribute("width", 1); r.setAttribute("height", 1);
          r.setAttribute("fill", CORES[c] || "#ff00ff");
          svg.appendChild(r);
        }));
        return svg;
      }

      function porLetra(pai, conteudo, estilo) {
        for (const ch of conteudo) {
          const s = document.createElement("span");
          s.textContent = ch;
          pai.appendChild(s);
        }
      }
      function digitar(letras, inicio, passo) {
        tl.fromTo(letras, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: passo, ease: "none" }, inicio);
      }

      const construtores = {
        hud(palco, e, c) {
          const h = document.createElement("div");
          h.className = "hud"; h.style.top = e.y + "px";
          h.innerHTML = `<span>${e.texto}</span><div class="barra"><i></i></div>`;
          palco.appendChild(h);
          tl.fromTo(h, { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.3 }, e.t);
          tl.to(h.querySelector("i"), { width: (e.progresso * 100) + "%", duration: 0.8, ease: "steps(10)" }, e.t + 0.2);
        },
        titulo_pixel(palco, e, c) {
          const caixa = document.createElement("div");
          caixa.className = "el titulo"; caixa.style.top = e.y + "px"; caixa.style.left = "0";
          const todas = [];
          e.linhas.forEach((l) => {
            const d = document.createElement("div");
            d.style.fontSize = (l.tamanho || e.tamanho || 120) + "px";
            d.style.color = cor(l.cor);
            porLetra(d, l.texto);
            todas.push(...d.querySelectorAll("span"));
            caixa.appendChild(d);
          });
          palco.appendChild(caixa);
          tl.set(caixa, { opacity: 1 }, e.t);
          tl.fromTo(caixa, { y: -40 }, { y: 0, duration: 0.25, ease: "steps(5)" }, e.t);
          digitar(todas, e.t, 0.03);
        },
        robo(palco, e, c) {
          const r = document.createElement("div");
          r.className = "robo"; r.style.left = e.x + "px"; r.style.top = e.y + "px";
          if (e.escala) r.style.transform = `scale(${e.escala})`, r.style.transformOrigin = "0 0";
          r.appendChild(desenharRobo(e.pose || "normal"));
          palco.appendChild(r);
          tl.fromTo(r, { opacity: 0, y: 80 }, { opacity: 1, y: 0, duration: 0.4, ease: "steps(6)" }, e.t);
          tl.to(r, { y: -PX, duration: 0.5, ease: "steps(1)", yoyo: true, repeat: 40 }, e.t + 0.5);
        },
        terminal(palco, e, c) {
          const j = document.createElement("div");
          j.className = "janela"; j.style.top = e.y + "px";
          j.innerHTML = `<div class="barra"><b style="background:#ff5c5c"></b><b style="background:#ffd84a"></b><b style="background:#4ee06a"></b><em>${e.rotulo || "terminal"}</em></div><div class="corpo"><div class="cmd"></div><div class="desc"></div></div>`;
          palco.appendChild(j);
          const cmd = j.querySelector(".cmd"), desc = j.querySelector(".desc");
          porLetra(cmd, e.comando);
          const cursor = document.createElement("i"); cursor.className = "cursor"; cmd.appendChild(cursor);
          porLetra(desc, e.texto);
          tl.fromTo(j, { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.3, ease: "steps(4)" }, e.ts[0]);
          const letrasCmd = [...cmd.querySelectorAll("span")];
          digitar(letrasCmd, e.ts[0] + 0.2, 0.07);
          tl.to(cursor, { opacity: 0, duration: 0.01, yoyo: true, repeat: 30, repeatDelay: 0.35 }, e.ts[0] + 0.6);
          digitar([...desc.querySelectorAll("span")], e.ts[1], 0.028);
        },
        selo_pixel(palco, e, c) {
          const b = document.createElement("div");
          b.className = "selo-pixel"; b.style.top = e.y + "px";
          b.innerHTML = `<div>${e.texto}</div>`;
          palco.appendChild(b);
          tl.fromTo(b, { opacity: 0, scale: 1.6 }, { opacity: 1, scale: 1, duration: 0.25, ease: "steps(4)" }, e.t);
        },
      };

      document.fonts.ready.then(() => {
        D.cenas.forEach((c, i) => {
          const palco = document.getElementById("cena-" + c.id).firstElementChild;
          c.elementos.forEach((e) => construtores[e.tipo](palco, e, c));
          if (i < D.cenas.length - 1) {
            tl.to(palco, { opacity: 0, duration: 0.2, ease: "steps(3)" }, c.inicio + c.duracao - 0.2);
          } else {
            tl.to(palco, { opacity: 0, duration: 0.4, ease: "steps(4)" }, c.inicio + c.duracao - 0.4);
          }
        });
        const caixaLegenda = document.getElementById("legendas");
        const destaque = new Set((D.destaques || []).map((p) => p.toLowerCase()));
        D.legenda.forEach((b) => {
          const el = document.createElement("div");
          el.className = "bloco-legenda";
          const linha = document.createElement("div");
          linha.innerHTML = b.texto.split(" ").map((p) => {
            const limpa = p.toLowerCase().replace(/[^a-zà-ú0-9\/]/g, "");
            return destaque.has(limpa) ? `<span class="dest">${p}</span>` : p;
          }).join(" ");
          el.appendChild(linha);
          caixaLegenda.appendChild(el);
          tl.set(el, { opacity: 1 }, b.t);
          tl.set(el, { opacity: 0 }, b.fim);
        });
        window.__timelines["main"] = tl;
      });
    </script>
  </body>
</html>
