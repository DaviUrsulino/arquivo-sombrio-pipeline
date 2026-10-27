<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio telão</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      /* Identidade inspirada no @jako.frames: sala escura, um monitor grande e um pequeno no canto mostrando a
         mesma tipografia cinética em cor chapada; a cor da tela vaza na parede e reflete na mesa. */
      @font-face { font-family: "Arch"; src: url("assets/fonts/ArchivoBlack.ttf"); }
      @font-face { font-family: "Serif"; src: url("assets/fonts/InstrumentSerif-Italic.ttf"); }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      @font-face { font-family: "Mont"; src: url("assets/fonts/Montserrat.ttf"); font-weight: 100 900; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #040405; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; color: #fff; }
      #sala { position: absolute; inset: 0; background: linear-gradient(180deg, #08080a 0%, #0c0c0f 60%, #050506 100%); }
      #luz { position: absolute; left: 40px; top: 260px; width: 1000px; height: 760px; border-radius: 50%; background: #ff7a00; filter: blur(140px); opacity: .55; }
      #mesa { position: absolute; left: 0; right: 0; top: 1240px; height: 680px; background: linear-gradient(180deg, #121215, #050506 70%); }
      #rig { position: absolute; inset: 0; perspective: 1800px; }
      .monitor { position: absolute; background: #0a0a0c; border: 16px solid #0a0a0c; border-radius: 14px; box-shadow: 0 40px 80px rgba(0,0,0,.8); overflow: hidden; }
      #grande { left: 70px; top: 380px; width: 940px; height: 600px; transform: rotateY(-9deg) rotateX(3deg); }
      #pequeno { left: 30px; top: 1080px; width: 420px; height: 300px; transform: rotateY(14deg); }
      .tela { position: absolute; inset: 0; background: #ff7a00; overflow: hidden; }
      .tela .ui { position: absolute; left: 14px; right: 14px; top: 10px; display: flex; justify-content: space-between; font-family: "Mono"; font-size: 13px; opacity: .55; color: currentColor; }
      .tela .reflexo { position: absolute; inset: 0; background: linear-gradient(115deg, rgba(255,255,255,.14) 0%, transparent 35%); }
      .quadro { position: absolute; left: 0; top: 0; width: 940px; height: 600px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; opacity: 0; transform-origin: 0 0; }
      #pequeno .quadro { transform: scale(0.85); left: -150px; top: -60px; }
      .k { font-family: "Arch"; font-size: 130px; line-height: .95; letter-spacing: -4px; text-transform: uppercase; }
      .k .p { display: inline-block; }
      .k .ac { color: var(--ac); }
      .sv { font-family: "Serif"; font-size: 64px; margin-top: 10px; }
      .num { font-family: "Arch"; font-size: 230px; letter-spacing: -8px; line-height: 1; }
      .mono { font-family: "Mono"; font-weight: 800; font-size: 54px; text-align: left; width: 860px; word-break: break-all; }
      #pe { position: absolute; left: 480px; top: 990px; width: 120px; height: 250px; background: linear-gradient(90deg, #0b0b0d, #18181c, #0b0b0d); }
      #reflexo-mesa { position: absolute; left: 70px; top: 1260px; width: 940px; height: 260px; background: #ff7a00; filter: blur(70px); opacity: .25; border-radius: 50%; }
      #legenda { position: absolute; left: 80px; right: 80px; top: 1560px; height: 180px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 16px; opacity: 0; }
      .w { font-family: "Mont"; font-weight: 800; font-size: 60px; color: #f2f2f2; display: inline-block; letter-spacing: -1px; }
      .w.dest { font-family: "Serif"; font-weight: 400; font-size: 72px; color: var(--ac-leg, #ff7a00); }
      .cena { position: absolute; inset: 0; opacity: 0; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="sala" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="luz" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="mesa" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="reflexo-mesa" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="pe" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="rig" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="2">
        <div id="grande" class="monitor"><div class="tela"><div class="ui"><span>● motion — claude</span><span>1080p</span></div></div></div>
        <div id="pequeno" class="monitor"><div class="tela"><div class="ui"><span>●</span><span>preview</span></div></div></div>
      </div>
{{CENAS}}
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      // paleta de telas: [fundo, texto, acento]
      const TELAS = [["#ff7a00", "#141414", "#5b3cff"], ["#0d0f14", "#ffffff", "#c6ff1a"], ["#c6ff1a", "#101010", "#ff3d00"], ["#7cc8ff", "#0b1a2b", "#ffffff"], ["#ffffff", "#111111", "#ff7a00"], ["#5b3cff", "#ffffff", "#c6ff1a"]];
      const telas = () => [...document.querySelectorAll(".tela")];
      // monta o mesmo quadro nas duas telas e devolve os pares de elementos pra animar junto
      function quadro(A, c, i, montar) {
        const [fundo, texto, ac] = i === A.D.cenas.length - 1 ? TELAS[0] : TELAS[i % TELAS.length];
        const qs = telas().map((tela) => { const q = A.el(tela, "div", "quadro", { color: texto, "--ac": ac }); montar(q); return q; });
        A.tl.set(telas(), { backgroundColor: fundo, color: texto }, c.inicio);
        A.tl.set(["#luz", "#reflexo-mesa"], { backgroundColor: fundo === "#0d0f14" ? "#3a3f55" : fundo }, c.inicio);
        A.tl.set("#legenda", { "--ac-leg": fundo === "#ffffff" || fundo === "#0d0f14" ? ac : fundo }, c.inicio);
        A.tl.set(qs, { opacity: 1 }, c.inicio);
        A.tl.set(qs, { opacity: 0 }, c.inicio + c.duracao);
        // flash da tela no corte
        A.tl.fromTo(["#luz"], { opacity: 0.95 }, { opacity: 0.55, duration: 0.5, ease: "power2.out" }, c.inicio);
        return qs;
      }
      const sel = (qs, s) => qs.flatMap((q) => [...q.querySelectorAll(s)]);
      function kinetic(A, q, palavras, acento) {
        const k = A.el(q, "div", "k");
        palavras.forEach((p) => { if (p === "\n") { A.el(k, "br"); return; } A.el(k, "span", "p" + (p === acento ? " ac" : ""), null, p + "&nbsp;"); });
        return k;
      }
      function entraPalavras(A, qs, t) {
        const ps = sel(qs, ".p");
        const n = ps.length / qs.length;
        qs.forEach((q, qi) => {
          const meus = [...q.querySelectorAll(".p")];
          A.tl.fromTo(meus, { y: 160, rotation: (k) => (k % 2 ? 12 : -12), scaleY: 1.6, opacity: 0 }, { y: 0, rotation: 0, scaleY: 1, opacity: 1, duration: 0.45, stagger: 0.12, ease: "back.out(2.2)" }, t);
        });
      }
      const repo = () => Object.values(window.DADOS.repos || {})[0] || { repo: "", estrelas: 0 };

      window.TEMA = {
        cores: {}, acento: "laranja", traco: 2, escalaTitulo: 1, larguraLetra: 0.6,
        entrar(A, alvo, t) { A.tl.fromTo(alvo, { opacity: 0 }, { opacity: 1, duration: 0.2 }, t); },
        palavraLegenda(A, s, t, dest) { A.tl.fromTo(s, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.15 }, t); },
        transicao() {},
        fundo(A, dur) {
          // câmera de mão: a sala inteira respira devagar
          A.tl.fromTo("#rig", { x: -10, y: 0, rotation: -0.3 }, { x: 10, y: -14, rotation: 0.3, duration: dur / 3, ease: "sine.inOut", yoyo: true, repeat: 2 }, 0);
        },
        visuais: {
          titulo_pixel(A, palco, e, c, i) {
            const linhas = e.linhas.map((l) => l.texto);
            const ultimo = linhas[linhas.length - 1].split(" ");
            const qs = quadro(A, c, i, (q) => { kinetic(A, q, [...linhas.slice(0, -1).join(" ").split(" "), "\n", ...ultimo], ultimo[ultimo.length - 1]); A.el(q, "div", "sv", null, "e roda offline."); });
            entraPalavras(A, qs, e.t);
            A.tl.fromTo(sel(qs, ".sv"), { opacity: 0 }, { opacity: 1, duration: 0.4 }, e.t + 1.2);
          },
          contador(A, palco, e, c, i) {
            const qs = quadro(A, c, i, (q) => { A.el(q, "div", "num", null, "0"); A.el(q, "div", "sv", null, "estrelas no GitHub."); });
            const st = { v: 0 }, nums = sel(qs, ".num");
            A.tl.to(st, { v: repo().estrelas, duration: 1.4, ease: "power3.out", onUpdate: () => nums.forEach((n) => (n.textContent = A.mil(Math.round(st.v)))) }, e.t + 0.2);
            A.tl.fromTo(nums, { scale: 0.5 }, { scale: 1, duration: 0.6, ease: "back.out(2)" }, e.t);
            A.tl.fromTo(sel(qs, ".sv"), { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.4 }, e.t + 1);
          },
          cadeia(A, palco, e, c, i) {
            // uma palavra gigante por vez, trocando no ritmo da fala
            const qs = quadro(A, c, i, (q) => e.nos.forEach((n) => { const k = A.el(q, "div", "k", { position: "absolute" }); A.el(k, "span", "p", null, n.rotulo); }));
            e.nos.forEach((n, k) => {
              const t = e.ts ? e.ts[k] : e.t + k * 0.5, fim = k + 1 < e.nos.length ? (e.ts ? e.ts[k + 1] : t + 0.5) : c.inicio + c.duracao;
              const alvos = qs.map((q) => q.querySelectorAll(".k")[k]);
              A.tl.fromTo(alvos, { opacity: 0, scale: 2.2, rotation: k % 2 ? 8 : -8 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.3, ease: "expo.out" }, t);
              if (k + 1 < e.nos.length) A.tl.to(alvos, { opacity: 0, y: -80, duration: 0.15 }, fim - 0.08);
            });
          },
          lista(A, palco, e, c, i) {
            const qs = quadro(A, c, i, (q) => { const k = A.el(q, "div", "k", { fontSize: "86px" }); e.itens.forEach((it) => { A.el(k, "span", "p", { display: "block" }, it); }); });
            e.itens.forEach((_, k) => {
              const alvos = qs.map((q) => q.querySelectorAll(".p")[k]);
              A.tl.fromTo(alvos, { opacity: 0, x: k % 2 ? 300 : -300, skewX: k % 2 ? -20 : 20 }, { opacity: 1, x: 0, skewX: 0, duration: 0.4, ease: "expo.out" }, e.ts ? e.ts[k] : e.t + k * 0.4);
            });
          },
          terminal(A, palco, e, c, i) {
            const qs = quadro(A, c, i, (q) => { const m = A.el(q, "div", "mono"); [..."$ " + e.comando].forEach((ch) => A.el(m, "span", "l", { opacity: 0 }, ch === " " ? "&nbsp;" : ch)); A.el(q, "div", "sv", { width: "860px", textAlign: "left" }, e.texto || ""); });
            const t0 = e.ts ? e.ts[0] : e.t;
            qs.forEach((q) => A.tl.to(q.querySelectorAll(".l"), { opacity: 1, duration: 0.01, stagger: 0.05 }, t0 + 0.2));
            A.tl.fromTo(sel(qs, ".sv"), { opacity: 0 }, { opacity: 1, duration: 0.3 }, e.ts ? e.ts[1] : t0 + 1.4);
          },
          icone_pixel(A, palco, e, c, i) {
            const palavras = (e.rotulo || "").split(" ");
            const qs = quadro(A, c, i, (q) => { kinetic(A, q, palavras, palavras[palavras.length - 1]); A.el(q, "div", "sv", null, "sem depender de ninguém."); });
            entraPalavras(A, qs, e.t);
            A.tl.fromTo(sel(qs, ".sv"), { opacity: 0 }, { opacity: 1, duration: 0.4 }, e.t + 0.9);
          },
          cta(A, palco, e, palavra, c, i) {
            const qs = quadro(A, c, i, (q) => { kinetic(A, q, ["COMENTA", "\n", palavra], palavra); A.el(q, "div", "sv", null, "que eu te mando o link."); });
            entraPalavras(A, qs, e.t);
            A.tl.fromTo(sel(qs, ".ac"), { scale: 1 }, { scale: 1.12, duration: 0.25, yoyo: true, repeat: 5, ease: "sine.inOut" }, e.t + 1);
            A.tl.fromTo(sel(qs, ".sv"), { opacity: 0 }, { opacity: 1, duration: 0.4 }, e.t + 1);
          },
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
