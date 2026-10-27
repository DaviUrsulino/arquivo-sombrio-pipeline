<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio pixel UI</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      /* Identidade inspirada no @99hud: fundo claro/azul alternando, fonte pixel, janelas retrô com sombra dura,
         carimbos tortos, diagrama hub com linha tracejada e personagem reagindo no canto. */
      @font-face { font-family: "Pix"; src: url("assets/fonts/Silkscreen-Bold.ttf"); }
      @font-face { font-family: "PixR"; src: url("assets/fonts/Silkscreen-Regular.ttf"); }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      :root { --tinta: #111; --laranja: #e8683b; --azul: #2f5bff; --verde: #19b64a; --cinza: #e9ebf0; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--cinza); }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Pix", monospace; color: var(--tinta); }
      #fundo { position: absolute; inset: 0; background: var(--cinza); }
      #pontos { position: absolute; inset: 0; background-image: radial-gradient(rgba(0,0,0,.12) 2px, transparent 2.5px); background-size: 36px 36px; }
      .cena { position: absolute; inset: 0; opacity: 0; }
      .palco { position: absolute; left: 50px; right: 50px; top: 120px; height: 1180px; display: flex; flex-direction: column; align-items: center; gap: 46px; }
      .cab { display: flex; flex-direction: column; align-items: center; gap: 14px; margin-top: 30px; text-align: center; }
      .tag { background: var(--tinta); color: #fff; font-family: "PixR"; font-size: 24px; padding: 6px 14px; }
      .h1 { font-size: 78px; line-height: 1.05; letter-spacing: 4px; text-transform: uppercase; }
      .h2 { font-size: 78px; line-height: 1.05; letter-spacing: 4px; text-transform: uppercase; color: var(--laranja); }
      .azul .h1 { color: #fff; } .azul .h2 { color: #ffd84a; }
      .ch { display: inline-block; }
      .jan { background: #fff; border: 6px solid var(--tinta); box-shadow: 14px 14px 0 var(--tinta); width: 900px; }
      .jan.preta { background: #15151a; color: #fff; }
      .jan .barra { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 6px solid var(--tinta); font-family: "PixR"; font-size: 22px; }
      .jan.preta .barra { border-color: #333; color: #aaa; }
      .jan .barra i { width: 18px; height: 18px; display: block; border: 3px solid var(--tinta); background: #ff5f57; } .jan .barra i:nth-child(2) { background: #febc2e; } .jan .barra i:nth-child(3) { background: #28c840; }
      .jan .miolo { padding: 36px; display: flex; align-items: center; gap: 30px; }
      .quad { width: 130px; height: 130px; flex: none; display: grid; place-items: center; border: 6px solid var(--tinta); box-shadow: 6px 6px 0 var(--tinta); }
      .nome { font-size: 56px; } .sub { font-family: "PixR"; font-size: 26px; color: #777; margin-top: 8px; }
      .carimbo { position: absolute; font-size: 64px; padding: 10px 26px; border: 6px solid currentColor; background: #fff; letter-spacing: 4px; box-shadow: 6px 6px 0 currentColor; }
      .numeros { display: flex; gap: 22px; }
      .num { width: 140px; height: 140px; display: grid; place-items: center; font-size: 80px; color: #fff; border: 6px solid var(--tinta); box-shadow: 8px 8px 0 var(--tinta); }
      .item { width: 900px; padding: 22px 30px; background: #fff; border: 5px solid var(--tinta); box-shadow: 8px 8px 0 var(--tinta); font-size: 46px; display: flex; gap: 24px; align-items: center; }
      .item b { color: #fff; font-size: 40px; padding: 4px 16px; border: 4px solid var(--tinta); }
      .hub { position: relative; width: 980px; height: 900px; }
      .hub svg { position: absolute; inset: 0; }
      .hub .centro { position: absolute; left: 400px; top: 360px; width: 180px; height: 180px; background: var(--laranja); border: 6px solid var(--tinta); box-shadow: 8px 8px 0 var(--tinta); display: grid; place-items: center; }
      .hub .no { position: absolute; width: 300px; padding: 22px 16px; background: #fff; border: 5px solid var(--tinta); box-shadow: 7px 7px 0 var(--tinta); text-align: center; font-size: 36px; }
      .hub .no { display: flex; flex-direction: column; align-items: center; gap: 10px; } .hub .no .ic { flex: none; }
      .barra-uso { width: 900px; padding: 26px 30px; background: #fff; border: 6px solid var(--tinta); box-shadow: 12px 12px 0 var(--tinta); }
      .barra-uso .rot { display: flex; justify-content: space-between; font-family: "PixR"; font-size: 30px; margin-bottom: 18px; }
      .barra-uso .trilho { height: 64px; border: 5px solid var(--tinta); } .barra-uso .ench { height: 100%; background: var(--verde); transform-origin: left; }
      .grande { font-size: 210px; line-height: 1; letter-spacing: 6px; }
      .cmd { font-family: "Mono"; font-weight: 800; font-size: 54px; padding: 40px; word-break: break-all; } .cmd b { color: #ffd84a; }
      .ok { font-family: "PixR"; font-size: 30px; color: #6fe38a; padding: 0 40px 40px; }
      .com { display: flex; align-items: center; gap: 22px; padding: 26px; font-family: "PixR"; font-size: 30px; color: #888; }
      .com .tx { font-family: "Pix"; font-size: 96px; color: var(--azul); }
      .pub { margin-left: auto; color: var(--azul); }
      #personagem { position: absolute; right: 20px; bottom: 20px; width: 330px; height: 430px; }
      #personagem .pose { position: absolute; left: 0; bottom: 0; width: 330px; }
      #legenda { position: absolute; left: 40px; width: 640px; top: 1360px; height: 200px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 4px 14px; opacity: 0; }
      .w { font-family: "Pix"; font-size: 50px; color: #fff; -webkit-text-stroke: 10px var(--tinta); paint-order: stroke fill; display: inline-block; }
      .w.dest { color: #ffd84a; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="pontos" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
{{CENAS}}
      <div id="personagem" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="6"></div>
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const CORES_PX = { laranja: "#e8683b", azul: "#2f5bff", verde: "#19b64a", roxo: "#8b4dff", vermelho: "#ff2e4d", amarelo: "#ffc21a", branco: "#111111", rosa: "#ff3fae" };
      const SEQ = ["#2f5bff", "#e8683b", "#19b64a", "#ff2e4d", "#8b4dff"];
      // cabeçalho: tag pequena + 2 linhas em fonte pixel, digitando letra a letra
      function cabecalho(A, palco, tag, l1, l2, t) {
        const cab = A.el(palco, "div", "cab");
        if (tag) A.el(cab, "div", "tag", null, tag);
        const linhas = [[l1, "h1"], [l2, "h2"]].filter(([x]) => x).map(([txt, cl]) => { const d = A.el(cab, "div", cl); return [...txt].map((ch) => A.el(d, "span", "ch", null, ch === " " ? "&nbsp;" : ch)); });
        const letras = linhas.flat();
        A.tl.fromTo(letras, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: Math.min(0.035, 0.7 / letras.length), ease: "none" }, t);
        return cab;
      }
      function janela(A, pai, titulo, preta) {
        const j = A.el(pai, "div", "jan" + (preta ? " preta" : ""));
        A.el(j, "div", "barra", null, `<i></i><i></i><i></i><span style="margin-left:10px">${titulo}</span>`);
        return [j, A.el(j, "div", "miolo")];
      }
      function pop(A, el, t) { A.tl.fromTo(el, { opacity: 0, scale: 0.4 }, { opacity: 1, scale: 1, duration: 0.3, ease: "steps(4)" }, t); }
      function carimbo(A, pai, texto, cor, x, y, rot, t) {
        const c = A.el(pai, "div", "carimbo", { left: x + "px", top: y + "px", color: cor, transform: `rotate(${rot}deg)` }, texto);
        A.tl.fromTo(c, { opacity: 0, scale: 2.4 }, { opacity: 1, scale: 1, duration: 0.25, ease: "power4.in" }, t);
        A.tl.fromTo(c, { x: -6 }, { x: 0, duration: 0.06, repeat: 3, yoyo: true }, t + 0.25);
      }
      const repo = () => Object.values(window.DADOS.repos || {})[0] || { repo: "", estrelas: 0 };
      let parte = 0;

      window.TEMA = {
        cores: CORES_PX, acento: "laranja", traco: 2.4, escalaTitulo: 1, larguraLetra: 0.6, desenharIcone: false,
        entrar(A, alvo, t) { A.tl.fromTo(alvo, { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.3, ease: "steps(4)" }, t); },
        palavraLegenda(A, s, t, dest) { A.tl.fromTo(s, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.12, ease: "steps(2)" }, t); },
        transicao(A, palco, c, i) {
          A.tl.fromTo(palco, { opacity: 0 }, { opacity: 1, duration: 0.01 }, c.inicio);
        },
        aoEntrarCena(A, secao, palco, c, i) {
          // fundo alterna cinza / azul / lavanda a cada cena, com corte seco
          const cores = ["#e9ebf0", "#2f5bff", "#e9ebf0", "#c9d6ff", "#2f5bff", "#e9ebf0"];
          const cor = i === A.D.cenas.length - 1 ? "#c9d6ff" : cores[i % cores.length];
          A.tl.set("#fundo", { backgroundColor: cor }, c.inicio);
          if (cor === "#2f5bff") palco.classList.add("azul");
        },
        visuais: {
          titulo_pixel(A, palco, e, c, i) {
            const l = e.linhas.map((x) => x.texto);
            cabecalho(A, palco, null, l.slice(0, -1).join(" "), l[l.length - 1], e.t);
            const [j, m] = janela(A, palco, "github.com");
            const q = A.el(m, "div", "quad", { background: "#e8683b" }); q.appendChild(A.svgIcone("github", "#fff", 80, 2.4));
            A.el(m, "div", "", null, `<div class="nome">${repo().repo.split("/")[1] || ""}</div><div class="sub">${repo().repo}</div>`);
            pop(A, j, e.t + 0.6);
          },
          contador(A, palco, e) {
            cabecalho(A, palco, null, "+ de", A.mil(repo().estrelas), e.t);
            const b = A.el(palco, "div", "barra-uso");
            A.el(b, "div", "rot", null, `<span>estrelas</span><span style="color:#2f5bff">github</span>`);
            const ench = A.el(A.el(b, "div", "trilho"), "div", "ench");
            pop(A, b, e.t + 0.3);
            A.tl.fromTo(ench, { scaleX: 0 }, { scaleX: 1, duration: 1.2, ease: "steps(10)" }, e.t + 0.5);
            const g = A.el(palco, "div", "grande", null, "★"); g.style.color = "#ffc21a"; pop(A, g, e.t + 0.4);
            carimbo(A, palco, "EM ALTA", "#19b64a", 520, 760, -8, e.t + 1.6);
          },
          cadeia(A, palco, e) {
            cabecalho(A, palco, "como funciona", "tudo", "conectado", e.t);
            const hub = A.el(palco, "div", "hub");
            const pos = [[40, 60], [640, 60], [40, 640], [640, 640], [340, 0], [340, 740]];
            const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"); svg.setAttribute("viewBox", "0 0 980 900"); hub.appendChild(svg);
            const centro = A.el(hub, "div", "centro"); centro.appendChild(A.svgIcone("bot", "#fff", 110, 2.2)); pop(A, centro, e.t);
            e.nos.forEach((n, k) => {
              const [x, y] = pos[k % pos.length];
              const ln = document.createElementNS("http://www.w3.org/2000/svg", "line");
              ln.setAttribute("x1", 490); ln.setAttribute("y1", 450); ln.setAttribute("x2", x + 150); ln.setAttribute("y2", y + 70);
              ln.setAttribute("stroke", "#111"); ln.setAttribute("stroke-width", 6); ln.setAttribute("stroke-dasharray", "18 14"); svg.appendChild(ln);
              const no = A.el(hub, "div", "no", { left: x + "px", top: y + "px" });
              no.appendChild(A.svgIcone(n.icone, CORES_PX[n.cor] || "#111", 70, 2.4)); A.el(no, "div", "", null, n.rotulo);
              const t = e.ts ? e.ts[k] : e.t + k * 0.4;
              A.tl.fromTo(ln, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t); A.tl.fromTo(ln, { strokeDashoffset: 200 }, { strokeDashoffset: 0, duration: 2, ease: "none" }, t);
              pop(A, no, t + 0.1);
            });
          },
          lista(A, palco, e) {
            cabecalho(A, palco, `${e.itens.length} recursos`, "o que", "vem junto", e.t);
            const ns = A.el(palco, "div", "numeros");
            const caixas = e.itens.map((_, k) => { const q = A.el(ns, "div", "num", { background: SEQ[k % SEQ.length] }, String(k + 1)); return q; });
            e.itens.forEach((txt, k) => {
              const t = e.ts ? e.ts[k] : e.t + k * 0.4;
              pop(A, caixas[k], t);
              const it = A.el(palco, "div", "item", null, `<b style="background:${SEQ[k % SEQ.length]}">${k + 1}</b>${txt}`);
              A.tl.fromTo(it, { opacity: 0, x: -60 }, { opacity: 1, x: 0, duration: 0.25, ease: "steps(3)" }, t + 0.05);
            });
          },
          terminal(A, palco, e) {
            cabecalho(A, palco, "passo a passo", "como", "instalar", e.t);
            const [j] = janela(A, palco, e.rotulo || "terminal", true);
            const cmd = A.el(j, "div", "cmd", null, "<b>&gt;</b> ");
            const letras = [...e.comando].map((ch) => A.el(cmd, "span", "", { opacity: 0 }, ch === " " ? "&nbsp;" : ch));
            pop(A, j, (e.ts ? e.ts[0] : e.t) + 0.3);
            A.tl.to(letras, { opacity: 1, duration: 0.01, stagger: 0.05 }, (e.ts ? e.ts[0] : e.t) + 0.6);
            if (e.texto) { const ok = A.el(j, "div", "ok", null, "✓ " + e.texto); A.tl.fromTo(ok, { opacity: 0 }, { opacity: 1, duration: 0.01 }, e.ts ? e.ts[1] : e.t + 1.5); }
          },
          icone_pixel(A, palco, e) {
            cabecalho(A, palco, null, "e o melhor:", e.rotulo || "", e.t);
            const [j, m] = janela(A, palco, "resultado");
            m.style.justifyContent = "center"; m.style.padding = "70px";
            const q = A.el(m, "div", "quad", { width: "300px", height: "300px", background: CORES_PX[e.cor] || "#19b64a" }); q.appendChild(A.svgIcone(e.icone, "#fff", 200, 2.6));
            pop(A, j, e.t + 0.4);
            carimbo(A, palco, e.rotulo || "OK", CORES_PX[e.cor] || "#19b64a", 360, 860, 6, e.t + 1.3);
          },
          cta(A, palco, e, palavra) {
            cabecalho(A, palco, null, "quer", "testar?", e.t);
            const [j] = janela(A, palco, "comentários");
            const com = A.el(j, "div", "com", null, `<span>adicione um comentário…</span>`);
            pop(A, j, e.t + 0.4);
            const tx = A.el(com, "div", "tx"); const ph = com.firstElementChild;
            A.tl.to(ph, { opacity: 0, duration: 0.01 }, e.t + 1);
            const letras = [...palavra].map((ch) => A.el(tx, "span", "", { opacity: 0 }, ch));
            A.tl.to(letras, { opacity: 1, duration: 0.01, stagger: 0.12 }, e.t + 1);
            A.el(com, "div", "pub", null, "publicar");
            carimbo(A, palco, "LINK NO DIRECT", "#2f5bff", 160, 640, -5, e.t + 1.4 + palavra.length * 0.12);
          },
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
