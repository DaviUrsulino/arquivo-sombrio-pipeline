<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio papel</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      /* Identidade inspirada no @nodir.ai_: papel creme, azul-marinho + laranja + verde-água, tipografia
         extrudada voando em 3D, anéis com régua, letras recortadas tipo bilhete e brinquedos 3D. */
      @font-face { font-family: "Anton"; src: url("assets/fonts/Anton-Regular.ttf"); }
      @font-face { font-family: "Arch"; src: url("assets/fonts/ArchivoBlack.ttf"); }
      @font-face { font-family: "Serif"; src: url("assets/fonts/InstrumentSerif-Italic.ttf"); }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      :root { --papel: #f1ecdf; --marinho: #2b2d42; --laranja: #e8683b; --agua: #5a9a8b; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--papel); }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; color: var(--marinho); perspective: 1400px; }
      #fundo { position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 50%, #f6f2e8 30%, #e6dfcd 100%); }
      #linhas { position: absolute; inset: 0; }
      #grao { position: absolute; inset: 0; opacity: .35; background-image: radial-gradient(rgba(43,45,66,.14) 1px, transparent 1.4px); background-size: 7px 7px; }
      .cena { position: absolute; inset: 0; opacity: 0; transform-style: preserve-3d; }
      .palco { position: absolute; inset: 0; transform-style: preserve-3d; }
      .ext { font-family: "Anton"; text-transform: uppercase; line-height: .9; position: absolute; left: 0; right: 0; text-align: center; transform-style: preserve-3d; }
      .ext.mar { color: var(--marinho); text-shadow: 2px 2px 0 #e8683b, 4px 4px 0 #e8683b, 6px 6px 0 #e8683b, 8px 8px 0 #d65a2f, 10px 10px 0 #c44f27, 12px 12px 0 #b4471f, 16px 22px 30px rgba(43,45,66,.35); }
      .ext.lar { color: var(--laranja); text-shadow: 2px 2px 0 #2b2d42, 4px 4px 0 #2b2d42, 6px 6px 0 #2b2d42, 8px 8px 0 #24263a, 10px 10px 0 #1e2032, 12px 12px 0 #181a2a, 16px 22px 30px rgba(43,45,66,.35); }
      .etq { position: absolute; font-family: "Mono"; font-weight: 700; font-size: 30px; color: var(--marinho); }
      .anel { position: absolute; left: 50%; top: 50%; border-radius: 50%; }
      .torre { position: absolute; left: 390px; width: 300px; background: linear-gradient(180deg, #e8683b 0%, #2b2d42 45%); border-radius: 6px; box-shadow: 20px 30px 40px rgba(43,45,66,.3); overflow: hidden; }
      .torre .marca-r { position: absolute; left: 30px; height: 6px; background: rgba(241,236,223,.85); }
      .tampa { position: absolute; left: 330px; width: 420px; height: 80px; background: #e8683b; border-radius: 10px; box-shadow: 0 16px 0 #b4471f, 20px 40px 40px rgba(43,45,66,.3); display: grid; place-items: center; }
      .tampa span { background: #f1ecdf; font-family: "Mono"; font-weight: 800; font-size: 40px; padding: 2px 18px; border-radius: 8px; }
      .pilula { position: absolute; padding: 14px 40px; border-radius: 999px; font-family: "Arch"; font-size: 64px; white-space: nowrap; box-shadow: 0 12px 0 rgba(0,0,0,.25), 12px 26px 30px rgba(43,45,66,.25); }
      .faixa { position: absolute; left: -40px; right: -40px; height: 220px; background: var(--marinho); color: #f1ecdf; display: flex; align-items: center; padding: 0 90px; font-family: "Mono"; font-weight: 800; font-size: 60px; box-shadow: 0 30px 50px rgba(43,45,66,.3); }
      .faixa small { font-family: "Serif"; font-weight: 400; font-size: 46px; color: #9fd1c4; margin-left: 30px; }
      .recorte { position: absolute; display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; left: 60px; right: 60px; }
      .rl { display: inline-block; font-size: 150px; line-height: 1; padding: 6px 14px; box-shadow: 6px 8px 0 rgba(43,45,66,.25); }
      .brinquedo { position: absolute; border-radius: 50%; }
      #legenda { position: absolute; left: 70px; right: 70px; top: 1590px; height: 170px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 16px; opacity: 0; }
      .w { font-family: "Arch"; font-size: 58px; color: var(--marinho); display: inline-block; letter-spacing: -1px; }
      .w.dest { font-family: "Serif"; font-size: 74px; color: var(--laranja); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <svg id="linhas" class="clip" viewBox="0 0 1080 1920" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></svg>
      <div id="grao" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
{{CENAS}}
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const NS = "http://www.w3.org/2000/svg";
      const repo = () => Object.values(window.DADOS.repos || {})[0] || { repo: "", estrelas: 0 };
      // anel com régua (ticks) em perspectiva: elipse SVG com traço tracejado girando
      function anel(A, pai, cx, cy, rx, ry, cor, t, dur, sentido) {
        const s = document.createElementNS(NS, "svg"); s.setAttribute("viewBox", "0 0 1080 1920"); s.style.cssText = "position:absolute;inset:0;width:1080px;height:1920px;overflow:visible";
        s.innerHTML = `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="${cor}" stroke-width="4"/><ellipse class="tick" cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="${cor}" stroke-width="26" stroke-dasharray="4 34"/>`;
        pai.appendChild(s);
        A.tl.fromTo(s, { opacity: 0, scale: 0.6, transformOrigin: `${cx}px ${cy}px` }, { opacity: 1, scale: 1, duration: 0.6, ease: "expo.out" }, t);
        A.tl.fromTo(s.querySelector(".tick"), { strokeDashoffset: 0 }, { strokeDashoffset: 380 * (sentido || 1), duration: dur, ease: "none" }, t);
        return s;
      }
      // palavra extrudada voando de trás pra frente em 3D, com borrão de movimento
      function voa(A, el, t, de) {
        A.tl.fromTo(el, { opacity: 0, z: -1600, rotationX: de.rx || 40, rotationY: de.ry || -50, rotationZ: de.rz || -10, filter: "blur(18px)" },
          { opacity: 1, z: 0, rotationX: 0, rotationY: 0, rotationZ: de.fz || 0, filter: "blur(0px)", duration: 0.75, ease: "expo.out" }, t);
      }
      function ext(A, pai, txt, cl, top, tam) { return A.el(pai, "div", "ext " + cl, { top: top + "px", fontSize: tam + "px" }, txt); }
      function tamPara(txt, max) { return Math.min(max, Math.floor(1700 / Math.max(4, txt.length))); }
      function brinquedos(A, pai, t, n) {
        const est = ["radial-gradient(circle at 35% 30%, #ffd2b8, #e8683b 55%, #9a3f1d)", "radial-gradient(circle at 35% 30%, #6b6f8a, #2b2d42 60%)",
          "repeating-linear-gradient(45deg, #2b2d42 0 18px, #e8a46b 18px 36px)", "radial-gradient(circle at 35% 30%, #d9efe9, #5a9a8b 60%)"];
        for (let k = 0; k < n; k++) {
          const r = 60 + A.rnd() * 110, x = A.rnd() * 1000 - 40, y = 300 + A.rnd() * 1100;
          const b = A.el(pai, "div", "brinquedo", { width: r + "px", height: r + "px", left: x + "px", top: y + "px", background: est[k % est.length], boxShadow: "14px 24px 30px rgba(43,45,66,.3)", borderRadius: k % 5 === 4 ? "18%" : "50%" });
          A.tl.fromTo(b, { opacity: 0, y: -900, rotation: -180 }, { opacity: 1, y: 0, rotation: 0, duration: 0.9, ease: "bounce.out" }, t + k * 0.05);
        }
      }

      window.TEMA = {
        cores: { laranja: "#e8683b", azul: "#2b2d42", verde: "#5a9a8b", roxo: "#2b2d42", vermelho: "#e8683b", amarelo: "#e8a46b", branco: "#2b2d42", rosa: "#e8683b" },
        acento: "laranja", traco: 2, escalaTitulo: 1, larguraLetra: 0.5,
        entrar(A, alvo, t) { voa(A, alvo, t, {}); },
        palavraLegenda(A, s, t, dest) { A.tl.fromTo(s, { opacity: 0, y: 20, rotation: dest ? -6 : 0 }, { opacity: 1, y: 0, rotation: dest ? -3 : 0, duration: 0.2, ease: "back.out(2)" }, t); },
        transicao(A, palco, c, i) {
          // corte em "chicote": a cena anterior sai girando e borrando
          A.tl.fromTo(palco, { opacity: 0 }, { opacity: 1, duration: 0.05 }, c.inicio);
          A.tl.to(palco, { opacity: 0, rotationY: 60, x: -500, filter: "blur(20px)", duration: 0.22, ease: "power3.in" }, c.inicio + c.duracao - 0.22);
        },
        fundo(A, dur) {
          // linhas de perspectiva saindo de um ponto de fuga que passeia devagar
          const g = document.getElementById("linhas");
          for (let k = 0; k < 18; k++) { const l = document.createElementNS(NS, "line"); l.setAttribute("stroke", k % 3 ? "rgba(90,154,139,.35)" : "rgba(232,104,59,.4)"); l.setAttribute("stroke-width", 2); g.appendChild(l); }
          const ps = { x: 540, y: 980 };
          const atualizar = () => [...g.children].forEach((l, k) => { const a = (k / 18) * Math.PI * 2; l.setAttribute("x1", ps.x); l.setAttribute("y1", ps.y); l.setAttribute("x2", ps.x + Math.cos(a) * 2400); l.setAttribute("y2", ps.y + Math.sin(a) * 2400); });
          atualizar();
          A.tl.to(ps, { x: 620, y: 860, duration: dur / 2, ease: "sine.inOut", yoyo: true, repeat: 1, onUpdate: atualizar }, 0);
        },
        visuais: {
          titulo_pixel(A, palco, e) {
            const ls = e.linhas.map((l) => l.texto);
            anel(A, palco, 540, 760, 470, 470, "#e8683b", e.t, 4, 1);
            ls.forEach((txt, k) => { const el = ext(A, palco, txt, k === ls.length - 1 ? "lar" : "mar", 420 + k * 230, tamPara(txt, 250)); voa(A, el, e.t + k * 0.35, { ry: k % 2 ? 50 : -50, fz: k % 2 ? 4 : -4 }); });
            const et = A.el(palco, "div", "etq", { left: "120px", top: (440 + ls.length * 230) + "px" }, "+" + A.mil(repo().estrelas) + " ★");
            A.tl.fromTo(et, { opacity: 0 }, { opacity: 1, duration: 0.3 }, e.t + 1);
          },
          contador(A, palco, e) {
            // torre-régua subindo enquanto o número no topo conta
            anel(A, palco, 540, 1330, 420, 110, "#e8683b", e.t, 4, -1);
            anel(A, palco, 540, 1330, 300, 78, "#2b2d42", e.t + 0.2, 4, 1);
            const torre = A.el(palco, "div", "torre", { top: "520px", height: "800px" });
            for (let k = 0; k < 18; k++) A.el(torre, "div", "marca-r", { top: 40 + k * 42 + "px", width: (k % 3 ? 90 : 200) + "px" });
            const tampa = A.el(palco, "div", "tampa", { top: "460px" }); const sp = A.el(tampa, "span", "", null, "+0");
            A.tl.fromTo(torre, { scaleY: 0, transformOrigin: "bottom" }, { scaleY: 1, duration: 1.3, ease: "expo.out" }, e.t);
            A.tl.fromTo(tampa, { y: 800 }, { y: 0, duration: 1.3, ease: "expo.out" }, e.t);
            const st = { v: 0 };
            A.tl.to(st, { v: repo().estrelas, duration: 1.3, ease: "expo.out", onUpdate: () => (sp.textContent = "+" + A.mil(Math.round(st.v)) + " ★") }, e.t);
            const t2 = ext(A, palco, "estrelas", "mar", 200, 180); voa(A, t2, e.t + 0.6, { rx: -40 });
          },
          cadeia(A, palco, e) {
            // anéis empilhados, cada nó é uma pílula que pousa no seu anel
            const cores = [["#2b2d42", "#f1ecdf"], ["#e8683b", "#2b2d42"], ["#5a9a8b", "#f1ecdf"], ["#f1ecdf", "#2b2d42"]];
            e.nos.forEach((n, k) => {
              const y = 560 + k * 300, t = e.ts ? e.ts[k] : e.t + k * 0.5;
              anel(A, palco, 540, y + 60, 430 - k * 30, 90, k % 2 ? "#e8683b" : "#5a9a8b", t, 3, k % 2 ? -1 : 1);
              const [bg, fg] = cores[k % cores.length];
              const p = A.el(palco, "div", "pilula", { left: 140 + (k % 2) * 160 + "px", top: y + "px", background: bg, color: fg, border: "4px solid #2b2d42", transform: `rotate(${k % 2 ? 4 : -5}deg)` }, n.rotulo);
              voa(A, p, t, { rx: 60, fz: 0 });
            });
          },
          lista(A, palco, e) {
            const cores = [["#2b2d42", "#f1ecdf"], ["#e8683b", "#2b2d42"], ["#f1ecdf", "#2b2d42"], ["#5a9a8b", "#f1ecdf"]];
            const ttl = ext(A, palco, "vem junto", "lar", 260, 190); voa(A, ttl, e.t, {});
            e.itens.forEach((txt, k) => {
              const [bg, fg] = cores[k % cores.length];
              const p = A.el(palco, "div", "pilula", { left: (k % 2 ? 260 : 80) + "px", top: 620 + k * 190 + "px", background: bg, color: fg, border: "4px solid #2b2d42" }, txt);
              A.tl.fromTo(p, { opacity: 0, x: k % 2 ? 900 : -900, rotation: k % 2 ? 25 : -25 }, { opacity: 1, x: 0, rotation: k % 2 ? 3 : -4, duration: 0.55, ease: "back.out(1.6)" }, e.ts ? e.ts[k] : e.t + k * 0.4);
            });
          },
          terminal(A, palco, e) {
            const ttl = ext(A, palco, "rode isso", "mar", 360, 200); voa(A, ttl, e.t, { ry: 50 });
            const f = A.el(palco, "div", "faixa", { top: "820px", transform: "rotate(-4deg)" });
            const cmd = A.el(f, "span"); [..."$ " + e.comando].forEach((ch) => A.el(cmd, "span", "l", { opacity: 0 }, ch === " " ? "&nbsp;" : ch));
            const t0 = e.ts ? e.ts[0] : e.t;
            A.tl.fromTo(f, { x: 1200 }, { x: 0, duration: 0.6, ease: "expo.out" }, t0 + 0.2);
            A.tl.to(f.querySelectorAll(".l"), { opacity: 1, duration: 0.01, stagger: 0.05 }, t0 + 0.6);
            if (e.texto) { const n = A.el(palco, "div", "faixa", { top: "1080px", height: "140px", background: "#5a9a8b", transform: "rotate(3deg)", fontFamily: "Serif", fontWeight: 400, fontSize: "56px" }, e.texto); A.tl.fromTo(n, { x: -1200 }, { x: 0, duration: 0.6, ease: "expo.out" }, e.ts ? e.ts[1] : t0 + 1.4); }
          },
          icone_pixel(A, palco, e) {
            brinquedos(A, palco, e.t + 0.4, 14);
            const ps = (e.rotulo || "").split(" ");
            ps.forEach((p, k) => { const el = ext(A, palco, p, k === ps.length - 1 ? "lar" : "mar", 560 + k * 250, tamPara(p, 280)); voa(A, el, e.t + k * 0.25, { ry: k % 2 ? 60 : -60 }); });
          },
          cta(A, palco, e, palavra) {
            // "COMENTA" em letras recortadas de revista + a palavra extrudada
            const r = A.el(palco, "div", "recorte", { top: "460px" });
            const fontes = ["Anton", "Arch", "Serif", "Mono"], fundos = ["#2b2d42", "#e8683b", "#f1ecdf", "#5a9a8b"];
            [..."COMENTA"].forEach((ch, k) => {
              const bg = fundos[k % 4];
              const l = A.el(r, "span", "rl", { fontFamily: fontes[(k * 3) % 4], background: bg, color: bg === "#f1ecdf" ? "#2b2d42" : "#f1ecdf", transform: `rotate(${(k % 3 - 1) * 6}deg)` }, ch);
              A.tl.fromTo(l, { opacity: 0, scale: 3, rotation: 40 }, { opacity: 1, scale: 1, rotation: (k % 3 - 1) * 6, duration: 0.25, ease: "power4.in" }, e.t + k * 0.08);
            });
            const w = ext(A, palco, palavra, "lar", 900, tamPara(palavra, 300)); voa(A, w, e.t + 0.9, { rx: -50 });
            anel(A, palco, 540, 1020, 480, 160, "#2b2d42", e.t + 0.9, 3, 1);
          },
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
