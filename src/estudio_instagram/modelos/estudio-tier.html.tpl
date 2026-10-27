<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio tier</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      /* Identidade inspirada no @daniel.esantos: cenas escuras (vermelho no canto, grade) para gancho e ranking,
         cenas creme para o detalhe com o print real do repositório circulado à mão, barra de progresso no topo. */
      @font-face { font-family: "Anton"; src: url("assets/fonts/Anton-Regular.ttf"); }
      @font-face { font-family: "Serif"; src: url("assets/fonts/InstrumentSerif-Italic.ttf"); }
      @font-face { font-family: "Mont"; src: url("assets/fonts/Montserrat.ttf"); font-weight: 100 900; }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #0b0b0d; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Mont", sans-serif; color: #fff; }
      #escuro { position: absolute; inset: 0; background: radial-gradient(circle at 30% 18%, rgba(170,20,30,.55), transparent 55%), #0b0b0d; }
      #claro { position: absolute; inset: 0; opacity: 0; background: radial-gradient(ellipse at 50% 45%, #f7f6f2 30%, #d9d7d0 100%); }
      #grade { position: absolute; inset: 0; background-image: linear-gradient(rgba(128,128,128,.10) 1px, transparent 1px), linear-gradient(90deg, rgba(128,128,128,.10) 1px, transparent 1px); background-size: 60px 60px; }
      #progresso { position: absolute; left: 0; top: 0; width: 1080px; height: 10px; background: #e0262f; }
      .cena { position: absolute; inset: 0; opacity: 0; }
      .palco { position: absolute; left: 60px; right: 60px; top: 170px; height: 1200px; display: flex; flex-direction: column; gap: 34px; }
      .t-escuro { font-family: "Anton"; font-size: 132px; line-height: 1.02; text-transform: uppercase; }
      .marca { display: inline-block; background: #e0262f; padding: 0 18px; margin-top: 8px; }
      .ch { display: inline-block; }
      .nivel { align-self: flex-start; background: #f5c518; color: #111; font-family: "Mono"; font-weight: 800; font-size: 30px; padding: 4px 14px; }
      .t-claro { font-family: "Anton"; font-size: 120px; line-height: 1; color: #111; text-transform: uppercase; }
      .serif { font-family: "Serif"; font-size: 66px; color: #d9682b; margin-top: -18px; }
      .nav { width: 960px; border-radius: 18px; overflow: hidden; background: #0d1117; box-shadow: 0 30px 70px rgba(0,0,0,.35); position: relative; }
      .nav .bar { display: flex; align-items: center; gap: 10px; padding: 16px 20px; background: #161b22; font-family: "Mono"; font-size: 24px; color: #8b949e; }
      .nav .bar i { width: 16px; height: 16px; border-radius: 50%; background: #ff5f57; display: block; } .nav .bar i:nth-child(2) { background: #febc2e; } .nav .bar i:nth-child(3) { background: #28c840; }
      .nav .bar em { margin-left: auto; color: #e0262f; font-style: normal; font-weight: 800; }
      .nav img { display: block; width: 100%; }
      .selo-est { position: absolute; right: 26px; bottom: 26px; background: #0d1117; border: 4px solid #f5c518; border-radius: 14px; padding: 10px 22px; font-family: "Anton"; font-size: 64px; color: #f5c518; }
      .circulo { position: absolute; pointer-events: none; }
      .tier { display: flex; flex-direction: column; gap: 14px; width: 960px; }
      .linha-t { display: flex; gap: 14px; height: 150px; }
      .letra { width: 150px; flex: none; display: grid; place-items: center; font-family: "Anton"; font-size: 96px; color: #111; border-radius: 10px; }
      .slot { flex: 1; border-radius: 10px; background: rgba(255,255,255,.04); border: 2px solid rgba(255,255,255,.08); display: flex; align-items: center; padding: 0 26px; font-family: "Anton"; font-size: 54px; text-transform: uppercase; }
      .carimbo { align-self: flex-end; border: 5px solid #2fe36b; color: #2fe36b; font-family: "Anton"; font-size: 54px; padding: 6px 24px; transform: rotate(-6deg); box-shadow: 0 0 30px rgba(47,227,107,.35); }
      .cards { display: flex; flex-direction: column; gap: 20px; width: 960px; }
      .card { display: flex; align-items: center; gap: 26px; background: #fff; border-radius: 18px; padding: 26px 30px; box-shadow: 0 16px 40px rgba(0,0,0,.12); color: #111; }
      .card .ic-c { width: 100px; height: 100px; border-radius: 18px; flex: none; display: grid; place-items: center; }
      .card b { font-family: "Anton"; font-size: 60px; font-weight: 400; text-transform: uppercase; }
      .term { width: 960px; border-radius: 18px; overflow: hidden; background: #0d1117; box-shadow: 0 30px 70px rgba(0,0,0,.35); }
      .term .cmd { font-family: "Mono"; font-weight: 800; font-size: 56px; padding: 44px 36px; color: #e6edf3; word-break: break-all; } .term .cmd b { color: #2fe36b; }
      .term .ok { font-family: "Mono"; font-size: 32px; color: #8b949e; padding: 0 36px 40px; }
      .destaque-box { display: flex; align-items: center; gap: 26px; background: #fff; border-radius: 22px; padding: 34px; box-shadow: 0 20px 50px rgba(0,0,0,.14); width: 960px; color: #111; }
      .destaque-box .ic-c { width: 170px; height: 170px; border-radius: 26px; flex: none; display: grid; place-items: center; }
      .destaque-box .txt { font-family: "Anton"; font-size: 76px; line-height: 1; text-transform: uppercase; }
      .input { width: 960px; display: flex; align-items: center; gap: 20px; background: #161b22; border: 2px solid #30363d; border-radius: 999px; padding: 22px 30px; font-size: 36px; color: #8b949e; }
      .input .tx { font-family: "Anton"; font-size: 80px; color: #fff; }
      #personagem { position: absolute; left: 400px; top: 1150px; width: 280px; height: 364px; }
      #personagem .pose { position: absolute; left: 0; bottom: 0; width: 280px; }
      #legenda { position: absolute; left: 60px; right: 60px; top: 1560px; height: 160px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 14px; opacity: 0; }
      .w { font-weight: 800; font-size: 54px; color: var(--cor-leg, #fff); display: inline-block; padding: 0 6px; }
      .w.dest { background: #2fe36b; color: #0b0b0d; border-radius: 6px; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="escuro" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="claro" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="grade" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
{{CENAS}}
      <div id="personagem" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="6"></div>
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <div id="progresso" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="7"></div>
      <audio id="trilha" src="assets/musica/trilha-pixel.mp3" data-start="0" data-duration="{{DURACAO}}" data-track-index="10" data-volume="0.12"></audio>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const COR_T = { laranja: "#d9682b", azul: "#3b82f6", verde: "#22c55e", roxo: "#a78bfa", vermelho: "#e0262f", amarelo: "#f5c518", branco: "#111111", rosa: "#ec4899" };
      const ESCUROS = new Set(["titulo_pixel", "lista", "cta"]);
      const repo = () => Object.values(window.DADOS.repos || {})[0] || { repo: "", estrelas: 0 };
      let nivel = 0;
      function tituloEscuro(A, palco, linhas, t) {
        const caixa = A.el(palco, "div", "t-escuro");
        const letras = [];
        linhas.forEach((txt, k) => {
          const d = A.el(caixa, "div", k === linhas.length - 1 && linhas.length > 1 ? "marca" : "");
          if (k === linhas.length - 1 && linhas.length > 1) { A.tl.fromTo(d, { scaleX: 0 }, { scaleX: 1, duration: 0.35, ease: "expo.out", transformOrigin: "left" }, t + 0.35); }
          txt.split(" ").forEach((p) => letras.push(A.el(d, "span", "ch", null, p + "&nbsp;")));
        });
        A.tl.fromTo(letras, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.3, stagger: 0.08, ease: "back.out(2)" }, t);
      }
      function cabClaro(A, palco, tag, titulo, serif, t) {
        const n = A.el(palco, "div", "nivel", null, tag);
        const h = A.el(palco, "div", "t-claro", null, titulo);
        const s = A.el(palco, "div", "serif", null, serif);
        A.tl.fromTo(n, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.25 }, t);
        A.tl.fromTo(h, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }, t + 0.08);
        A.tl.fromTo(s, { opacity: 0 }, { opacity: 1, duration: 0.4 }, t + 0.3);
      }
      function sobe(A, el, t) { A.tl.fromTo(el, { opacity: 0, y: 70 }, { opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }, t); }
      // elipse vermelha "desenhada à mão" em volta de um alvo
      function circular(A, pai, x, y, w, h, t) {
        const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        s.setAttribute("class", "circulo"); s.setAttribute("width", w + 40); s.setAttribute("height", h + 40);
        s.style.left = x - 20 + "px"; s.style.top = y - 20 + "px";
        s.innerHTML = `<path pathLength="1" d="M ${w * 0.55 + 20} 22 C ${w + 30} 18, ${w + 34} ${h + 22}, ${w * 0.5 + 20} ${h + 24} C 6 ${h + 26}, 4 20, ${w * 0.6 + 20} 14" fill="none" stroke="#e0262f" stroke-width="7" stroke-linecap="round"/>`;
        pai.appendChild(s);
        A.tl.fromTo(s.querySelector("path"), { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }, t);
      }

      window.TEMA = {
        cores: COR_T, acento: "vermelho", traco: 2.2, escalaTitulo: 1, larguraLetra: 0.5, desenharIcone: false,
        entrar(A, alvo, t) { sobe(A, alvo, t); },
        palavraLegenda(A, s, t) { A.tl.fromTo(s, { opacity: 0 }, { opacity: 1, duration: 0.08 }, t); },
        transicao(A, palco, c, i) {
          A.tl.fromTo(palco, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }, c.inicio);
          A.tl.to(palco, { opacity: 0, duration: 0.12 }, c.inicio + c.duracao - 0.12);
        },
        aoEntrarCena(A, secao, palco, c, i) {
          const e = c.elementos[0];
          const escuro = ESCUROS.has(e.tipo);
          A.tl.to("#claro", { opacity: escuro ? 0 : 1, duration: 0.2 }, c.inicio);
          A.tl.set("#legenda", { "--cor-leg": escuro ? "#ffffff" : "#111111" }, c.inicio);
          A.tl.set("#personagem", { opacity: escuro ? 1 : 0 }, c.inicio);
        },
        visuais: {
          titulo_pixel(A, palco, e) { tituloEscuro(A, palco, e.linhas.map((l) => l.texto), e.t); },
          contador(A, palco, e) {
            nivel++;
            cabClaro(A, palco, "PRINT REAL", repo().repo.split("/")[1] || "", `${A.mil(repo().estrelas)} estrelas e subindo`, e.t);
            const nav = A.el(palco, "div", "nav");
            A.el(nav, "div", "bar", null, `<i></i><i></i><i></i><span style="margin-left:10px">github.com/${repo().repo}</span><em>● PRINT REAL</em>`);
            const im = A.el(nav, "img"); im.src = "assets/cartao.png"; im.onerror = () => { im.style.height = "380px"; im.style.background = "#161b22"; };
            const selo = A.el(nav, "div", "selo-est", null, "★ 0");
            sobe(A, nav, e.t + 0.4);
            const st = { v: 0 };
            A.tl.to(st, { v: repo().estrelas, duration: 1.2, ease: "power3.out", onUpdate: () => { selo.textContent = "★ " + A.mil(Math.round(st.v)); } }, e.t + 0.8);
            A.tl.fromTo(selo, { scale: 0.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(3)" }, e.t + 0.8);
            circular(A, nav, 600, 360, 340, 110, e.t + 1.6);
          },
          cadeia(A, palco, e) {
            cabClaro(A, palco, "COMO FUNCIONA", "Por dentro", "passo a passo, sem nuvem", e.t);
            const cards = A.el(palco, "div", "cards");
            e.nos.forEach((n, k) => {
              const c = A.el(cards, "div", "card");
              const ic = A.el(c, "div", "ic-c", { background: (COR_T[n.cor] || "#111") + "22" }); ic.appendChild(A.svgIcone(n.icone, COR_T[n.cor] || "#111", 64, 2.2));
              A.el(c, "b", "", null, n.rotulo);
              const ok = A.el(c, "div", "", { marginLeft: "auto" }); ok.appendChild(A.svgIcone("check", "#22c55e", 60, 3));
              sobe(A, c, e.ts ? e.ts[k] : e.t + k * 0.4);
            });
          },
          lista(A, palco, e) {
            tituloEscuro(A, palco, ["Tudo que", "vem junto"], e.t);
            const tier = A.el(palco, "div", "tier");
            const L = [["S", "#2fe36b"], ["A", "#a78bfa"], ["B", "#f5c518"]];
            const slots = L.map(([l, c]) => { const r = A.el(tier, "div", "linha-t"); A.el(r, "div", "letra", { background: c }, l); return A.el(r, "div", "slot"); });
            sobe(A, tier, e.t + 0.3);
            e.itens.forEach((txt, k) => {
              const slot = slots[Math.min(k, 2)];
              const s = A.el(slot, "span", "", { marginRight: "26px" }, txt);
              A.tl.fromTo(s, { opacity: 0, scale: 1.6 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }, e.ts ? e.ts[k] : e.t + k * 0.4);
              A.tl.fromTo(slot, { boxShadow: "0 0 0px rgba(245,197,24,0)" }, { boxShadow: "0 0 40px rgba(245,197,24,.6)", duration: 0.2, yoyo: true, repeat: 1 }, e.ts ? e.ts[k] : e.t + k * 0.4);
            });
            const c = A.el(palco, "div", "carimbo", null, "O Nº 1 TE SURPREENDE");
            A.tl.fromTo(c, { opacity: 0, scale: 2 }, { opacity: 1, scale: 1, duration: 0.25, ease: "power4.in" }, (e.ts ? e.ts[e.ts.length - 1] : e.t) + 0.5);
          },
          terminal(A, palco, e) {
            cabClaro(A, palco, "INSTALAR", "Um comando", "e já está rodando", e.t);
            const term = A.el(palco, "div", "term");
            A.el(term, "div", "bar", { display: "flex", gap: "10px", padding: "16px 20px", background: "#161b22", fontFamily: "Mono", fontSize: "24px", color: "#8b949e" }, `<span>${e.rotulo || "terminal"}</span>`);
            const cmd = A.el(term, "div", "cmd", null, "<b>$</b> ");
            const letras = [...e.comando].map((ch) => A.el(cmd, "span", "", { opacity: 0 }, ch === " " ? "&nbsp;" : ch));
            const t0 = e.ts ? e.ts[0] : e.t;
            sobe(A, term, t0 + 0.3);
            A.tl.to(letras, { opacity: 1, duration: 0.01, stagger: 0.05 }, t0 + 0.6);
            if (e.texto) { const ok = A.el(term, "div", "ok", null, "# " + e.texto); A.tl.fromTo(ok, { opacity: 0 }, { opacity: 1, duration: 0.2 }, e.ts ? e.ts[1] : t0 + 1.5); }
          },
          icone_pixel(A, palco, e) {
            cabClaro(A, palco, "DETALHE", e.rotulo || "", "o que pouca gente percebe", e.t);
            const b = A.el(palco, "div", "destaque-box");
            const ic = A.el(b, "div", "ic-c", { background: (COR_T[e.cor] || "#22c55e") + "22" }); ic.appendChild(A.svgIcone(e.icone, COR_T[e.cor] || "#22c55e", 110, 2.2));
            A.el(b, "div", "txt", null, e.rotulo || "");
            sobe(A, b, e.t + 0.4);
            circular(A, b, 0, 0, 960, 240, e.t + 1.2);
          },
          cta(A, palco, e, palavra) {
            tituloEscuro(A, palco, ["Comenta", palavra], e.t);
            const inp = A.el(palco, "div", "input", null, `<span>adicione um comentário…</span>`);
            sobe(A, inp, e.t + 0.6);
            const tx = A.el(inp, "div", "tx");
            A.tl.to(inp.firstElementChild, { opacity: 0, duration: 0.01 }, e.t + 1.1);
            const letras = [...palavra].map((ch) => A.el(tx, "span", "", { opacity: 0 }, ch));
            A.tl.to(letras, { opacity: 1, duration: 0.01, stagger: 0.12 }, e.t + 1.1);
          },
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
