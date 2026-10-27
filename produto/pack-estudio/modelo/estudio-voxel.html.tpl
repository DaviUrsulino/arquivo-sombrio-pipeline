<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio voxel</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/vendor/three.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      /* Identidade inspirada no @macelista: fundo azul-roxo granulado, letreiro de lâmpadas com neon rosa,
         títulos em fita crepe, monitor retrô bege, mascote voxel 3D e legendas em etiquetas laranja. */
      @font-face { font-family: "Anton"; src: url("assets/fonts/Anton-Regular.ttf"); }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #14152a; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; color: #fff; font-family: "Anton"; }
      #fundo { position: absolute; inset: 0; background: radial-gradient(ellipse at 70% 0%, #2c3a8c 0%, transparent 55%), radial-gradient(ellipse at 10% 90%, #4a1f45 0%, transparent 55%), #15152a; }
      #grao { position: absolute; inset: 0; opacity: .5; background-image: radial-gradient(rgba(255,255,255,.07) 1px, transparent 1.4px); background-size: 5px 5px; }
      #assinatura { position: absolute; right: 50px; top: 90px; font-family: "Mono"; font-size: 24px; color: #cfd2ff; }
      #assinatura::before { content: "●"; color: #6fe38a; margin-right: 8px; }
      #gl { position: absolute; inset: 0; width: 1080px; height: 1920px; }
      .cena { position: absolute; inset: 0; opacity: 0; }
      .palco { position: absolute; left: 50px; right: 50px; top: 150px; height: 1300px; display: flex; flex-direction: column; align-items: center; gap: 50px; }
      .letreiro { position: relative; padding: 30px 60px; border-radius: 14px; background: #1a1730; border: 4px solid #2d2850; text-align: center; }
      .letreiro .neon { font-size: 104px; line-height: .98; text-transform: uppercase; color: #ff9bd3; text-shadow: 0 0 10px #ff4fb4, 0 0 30px #ff4fb4, 0 0 60px #ff2d9a; }
      .lamp { position: absolute; width: 12px; height: 12px; border-radius: 50%; background: #ffd27a; box-shadow: 0 0 12px #ffb02e; }
      .fita { position: relative; padding: 14px 48px; background: #efe6d2; color: #1d1d24; font-size: 76px; text-transform: uppercase; transform: rotate(-2deg); box-shadow: 0 10px 20px rgba(0,0,0,.35); }
      .fita::before, .fita::after { content: ""; position: absolute; top: -18px; width: 90px; height: 40px; background: rgba(210,205,190,.75); }
      .fita::before { left: -30px; transform: rotate(-30deg); } .fita::after { right: -30px; transform: rotate(30deg); }
      .monitor { width: 820px; padding: 26px 26px 50px; border-radius: 34px; background: linear-gradient(180deg, #f2ecdc, #d9d1bd); box-shadow: 0 30px 60px rgba(0,0,0,.5), inset 0 -8px 0 #c3b99f; position: relative; }
      .monitor .tela { height: 460px; border-radius: 16px; background: #0d0f1c; overflow: hidden; position: relative; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 18px; }
      .monitor .rodape { position: absolute; left: 40px; right: 40px; bottom: 14px; display: flex; justify-content: space-between; font-family: "Mono"; font-size: 18px; color: #8a8270; }
      .monitor .pe { position: absolute; left: 350px; bottom: -70px; width: 120px; height: 70px; background: #cfc6b0; }
      .monitor .base { position: absolute; left: 270px; bottom: -86px; width: 280px; height: 22px; border-radius: 10px; background: #d9d1bd; }
      .janela { width: 440px; border-radius: 16px; background: #1f2135; border: 3px solid #3a3d5c; padding: 14px; }
      .janela .t { display: flex; gap: 6px; margin-bottom: 12px; } .janela .t i { width: 12px; height: 12px; border-radius: 50%; background: #ff5f57; display: block; } .janela .t i:nth-child(2) { background: #febc2e; } .janela .t i:nth-child(3) { background: #28c840; }
      .janela .c { display: flex; align-items: center; gap: 14px; font-size: 54px; text-transform: uppercase; }
      .jans { display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; width: 980px; }
      .cmd { font-family: "Mono"; font-weight: 800; font-size: 46px; color: #e7e9ff; padding: 0 40px; word-break: break-all; } .cmd b { color: #6fe38a; }
      .grande { font-size: 210px; color: #fff; line-height: 1; text-shadow: 0 0 40px rgba(111,124,255,.6); }
      #etiquetas { position: absolute; left: 400px; right: 40px; top: 1560px; height: 260px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 12px 14px; opacity: 0; }
      .w { display: inline-block; background: #e8672f; color: #fff; font-size: 56px; text-transform: uppercase; padding: 4px 18px 0; border-radius: 8px; box-shadow: 0 6px 0 #a8441a, 0 12px 24px rgba(0,0,0,.4); }
      .w.dest { background: #ffd23f; color: #1d1d24; box-shadow: 0 6px 0 #b8901a, 0 12px 24px rgba(0,0,0,.4); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="grao" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="assinatura" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1">@ursulino.ia</div>
{{CENAS}}
      <canvas id="gl" class="clip" width="1080" height="1920" data-start="0" data-duration="{{DURACAO}}" data-track-index="6"></canvas>
      <div id="etiquetas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"><div id="legenda" style="position:absolute;inset:0"></div></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const repo = () => Object.values(window.DADOS.repos || {})[0] || { repo: "", estrelas: 0 };
      // ---------- cena 3D: mascote voxel (cabeça amarela, boina vermelha, camisa listrada) + pódio ----------
      const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById("gl"), alpha: true, antialias: true, preserveDrawingBuffer: true });
      renderer.setPixelRatio(1); renderer.setSize(1080, 1920, false); renderer.outputEncoding = THREE.sRGBEncoding;
      const cena3 = new THREE.Scene();
      const cam = new THREE.OrthographicCamera(-540, 540, 960, -960, 1, 4000); cam.position.set(0, 0, 2000);
      cena3.add(new THREE.HemisphereLight(0xdfe3ff, 0x2a1a30, 0.9));
      const sol = new THREE.DirectionalLight(0xfff1d6, 0.9); sol.position.set(400, 600, 900); cena3.add(sol);
      const voxel = (w, h, d, cor) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color: cor, roughness: 0.6 }));
      // Robô Estagiário em blocos: cabeça laranja com visor escuro, olhos ciano, antena amarela e crachá.
      const mascote = new THREE.Group();
      const cabeca = voxel(260, 220, 200, 0xff8a2a); mascote.add(cabeca);
      const visor = voxel(200, 140, 12, 0x1b1d2b); visor.position.set(0, -6, 101); mascote.add(visor);
      [-140, 140].forEach((x) => { const o = voxel(24, 70, 70, 0xd9661a); o.position.set(x, 0, 0); mascote.add(o); });
      const haste = voxel(14, 60, 14, 0x2a1608); haste.position.y = 140; mascote.add(haste);
      const bola = voxel(44, 44, 44, 0xffd84a); bola.position.y = 186; mascote.add(bola);
      const olhoMat = new THREE.MeshBasicMaterial({ color: 0x5ff3ff });
      const olhos = [-46, 46].map((x) => { const o = new THREE.Mesh(new THREE.BoxGeometry(38, 50, 6), olhoMat); o.position.set(x, 4, 110); mascote.add(o); return o; });
      const brilhos = olhos.map((o) => { const b = voxel(10, 10, 4, 0xffffff); b.position.set(o.position.x + 9, 18, 114); mascote.add(b); return b; });
      const boca = new THREE.Mesh(new THREE.BoxGeometry(46, 10, 6), olhoMat); boca.position.set(0, -44, 110); mascote.add(boca);
      const corpo = voxel(190, 150, 150, 0xff8a2a); corpo.position.y = -200; mascote.add(corpo);
      const cracha = voxel(110, 66, 8, 0xffffff); cracha.position.set(0, -200, 78); mascote.add(cracha);
      const faixa = voxel(110, 18, 10, 0x2f5bff); faixa.position.set(0, -176, 79); mascote.add(faixa);
      [-125, 125].forEach((x) => { const br = voxel(36, 120, 36, 0xff8a2a); br.position.set(x, -205, 0); mascote.add(br); });
      [-50, 50].forEach((x) => { const p = voxel(50, 40, 60, 0xd9661a); p.position.set(x, -295, 0); mascote.add(p); });
      mascote.rotation.set(0.25, -0.5, 0);
      cena3.add(mascote);
      const podio = new THREE.Group();
      const p1 = voxel(220, 300, 220, 0x3346e0), p2 = voxel(220, 200, 220, 0x3346e0); p1.position.set(-120, 0, 0); p2.position.set(120, -50, 0); podio.add(p1, p2); podio.rotation.set(0.35, -0.6, 0); podio.visible = false; cena3.add(podio);
      const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
      const back = (x) => { x = clamp(x, 0, 1); const c = 1.9; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
      let janelaPodio = null;
      function desenhar3(t) {
        const D = window.DADOS;
        const ativa = D.cenas.findIndex((c) => t >= c.inicio && t < c.inicio + c.duracao);
        const c = D.cenas[Math.max(0, ativa)];
        // mascote no canto inferior esquerdo, quica a cada cena, pisca, balança a cabeça falando
        const desde = t - c.inicio;
        mascote.position.set(-340, -520 + Math.max(0, Math.sin(Math.min(desde, 0.5) * Math.PI * 2) * 40 * (1 - desde * 2)), 0);
        mascote.scale.setScalar(0.9 * back(desde / 0.4) * 0.3 + 0.63);
        mascote.rotation.y = -0.5 + Math.sin(t * 2.2) * 0.12; mascote.rotation.z = Math.sin(t * 6) * 0.03;
        const piscar = (t % 3.1) < 0.12; olhos.forEach((o) => (o.scale.y = piscar ? 0.15 : 1)); brilhos.forEach((b) => (b.visible = !piscar)); bola.scale.setScalar(1 + 0.15 * Math.abs(Math.sin(t * 4)));
        boca.scale.y = 1 + Math.abs(Math.sin(t * 14)) * 2.4;
        // pódio aparece só na cena do contador
        podio.visible = !!janelaPodio && t >= janelaPodio[0] && t < janelaPodio[1];
        if (podio.visible) { const k = back((t - janelaPodio[0]) / 0.6); podio.position.set(160, -140, 0); podio.scale.set(1, Math.max(0.01, k), 1); podio.rotation.y = -0.6 + Math.sin(t) * 0.1; }
        renderer.render(cena3, cam);
      }
      function fita(A, pai, txt, t) { const f = A.el(pai, "div", "fita", null, txt); A.tl.fromTo(f, { opacity: 0, scale: 1.4, rotation: -10 }, { opacity: 1, scale: 1, rotation: -2, duration: 0.35, ease: "back.out(2.5)" }, t); return f; }
      function monitor(A, pai, t) {
        const m = A.el(pai, "div", "monitor"); const tela = A.el(m, "div", "tela");
        A.el(m, "div", "rodape", null, `<span>●●●</span><span>github: ${repo().repo}</span>`); A.el(m, "div", "pe"); A.el(m, "div", "base");
        A.tl.fromTo(m, { opacity: 0, y: 120 }, { opacity: 1, y: 0, duration: 0.5, ease: "back.out(1.6)" }, t);
        return tela;
      }
      function janelaMini(A, pai, icone, cor, txt, t) {
        const j = A.el(pai, "div", "janela"); A.el(j, "div", "t", null, "<i></i><i></i><i></i>");
        const c = A.el(j, "div", "c"); c.appendChild(A.svgIcone(icone, cor, 56, 2.2)); A.el(c, "span", "", null, txt);
        A.tl.fromTo(j, { opacity: 0, scale: 0.4, rotation: -8 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.35, ease: "back.out(2.6)" }, t);
        return j;
      }

      window.TEMA = {
        cores: { laranja: "#e8672f", azul: "#6f7cff", verde: "#6fe38a", roxo: "#b48cff", vermelho: "#ff5c5c", amarelo: "#ffd23f", branco: "#ffffff", rosa: "#ff9bd3" },
        acento: "laranja", traco: 2.2, escalaTitulo: 1, larguraLetra: 0.5,
        entrar(A, alvo, t) { A.tl.fromTo(alvo, { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2.5)" }, t); },
        // legenda vira etiquetas laranja que vão se acumulando, uma por palavra
        palavraLegenda(A, s, t, dest) { A.tl.fromTo(s, { opacity: 0, y: 40, rotation: dest ? -6 : 0, scale: 0.6 }, { opacity: 1, y: 0, rotation: dest ? -3 : 0, scale: 1, duration: 0.22, ease: "back.out(3)" }, t); },
        transicao(A, palco, c) {
          A.tl.fromTo(palco, { opacity: 0 }, { opacity: 1, duration: 0.05 }, c.inicio);
          A.tl.to(palco, { opacity: 0, scale: 0.9, duration: 0.15 }, c.inicio + c.duracao - 0.15);
        },
        fundo(A, dur) {
          const relogio = { t: 0 };
          A.tl.to(relogio, { t: dur, duration: dur, ease: "none", onUpdate: () => desenhar3(A.tl.time()) }, 0);
          window.addEventListener("hf-seek", (ev) => desenhar3(ev.detail.time));
        },
        visuais: {
          titulo_pixel(A, palco, e) {
            // letreiro de lâmpadas: o neon acende piscando, como placa de bar
            const l = A.el(palco, "div", "letreiro");
            for (let k = 0; k < 26; k++) { const p = k < 9 ? [k / 8, 0] : k < 13 ? [1, (k - 8) / 5] : k < 22 ? [1 - (k - 13) / 8, 1] : [0, 1 - (k - 21) / 5]; A.el(l, "div", "lamp", { left: `calc(${p[0] * 100}% - 6px)`, top: `calc(${p[1] * 100}% - 6px)` }); }
            const n = A.el(l, "div", "neon", null, e.linhas.map((x) => x.texto).join("<br>"));
            A.tl.fromTo(l, { opacity: 0 }, { opacity: 1, duration: 0.2 }, e.t);
            A.tl.fromTo(n, { opacity: 0.15 }, { opacity: 1, duration: 0.06, repeat: 6, yoyo: true, ease: "steps(1)" }, e.t + 0.3);
            const tela = monitor(A, palco, e.t + 0.6);
            const ic = A.svgIcone("github", "#e7e9ff", 150, 1.6); tela.appendChild(ic);
            A.el(tela, "div", "", { fontSize: "64px" }, repo().repo.split("/")[1] || "");
          },
          contador(A, palco, e, c) {
            fita(A, palco, "estrelas no github", e.t);
            const g = A.el(palco, "div", "grande", null, "0");
            const st = { v: 0 };
            A.tl.to(st, { v: repo().estrelas, duration: 1.3, ease: "power3.out", onUpdate: () => (g.textContent = A.mil(Math.round(st.v)) + " ★") }, e.t + 0.3);
            janelaPodio = [e.t + 0.6, c.inicio + c.duracao];
          },
          cadeia(A, palco, e) {
            fita(A, palco, "o vai e volta", e.t);
            const js = A.el(palco, "div", "jans", { marginTop: "60px" });
            e.nos.forEach((n, k) => janelaMini(A, js, n.icone, window.TEMA.cores[n.cor] || "#fff", n.rotulo, e.ts ? e.ts[k] : e.t + k * 0.4));
          },
          lista(A, palco, e) {
            fita(A, palco, "vem junto", e.t);
            const js = A.el(palco, "div", "jans");
            const ics = ["brain", "search", "zap", "message-circle", "sparkles"];
            e.itens.forEach((txt, k) => janelaMini(A, js, ics[k % ics.length], "#ffd23f", txt, e.ts ? e.ts[k] : e.t + k * 0.4).style.width = "460px");
          },
          terminal(A, palco, e) {
            fita(A, palco, "como instalar", e.t);
            const t0 = e.ts ? e.ts[0] : e.t;
            const tela = monitor(A, palco, t0 + 0.3);
            const cmd = A.el(tela, "div", "cmd", null, "<b>$</b> ");
            const ls = [...e.comando].map((ch) => A.el(cmd, "span", "", { opacity: 0 }, ch === " " ? "&nbsp;" : ch));
            A.tl.to(ls, { opacity: 1, duration: 0.01, stagger: 0.05 }, t0 + 0.8);
          },
          icone_pixel(A, palco, e) {
            fita(A, palco, e.rotulo || "", e.t);
            const tela = monitor(A, palco, e.t + 0.4);
            const ic = A.svgIcone(e.icone, window.TEMA.cores[e.cor] || "#6fe38a", 240, 2); tela.appendChild(ic);
            A.tl.fromTo(ic, { scale: 0, rotation: -90 }, { scale: 1, rotation: 0, duration: 0.5, ease: "back.out(2.5)" }, e.t + 0.8);
          },
          cta(A, palco, e, palavra) {
            fita(A, palco, "quer o link?", e.t);
            const tela = monitor(A, palco, e.t + 0.4);
            A.el(tela, "div", "", { fontFamily: "Mono", fontSize: "34px", color: "#8a8fb8" }, "comente:");
            const w = A.el(tela, "div", "", { fontSize: "170px", color: "#ff9bd3", textShadow: "0 0 30px #ff4fb4" });
            const ls = [...palavra].map((ch) => A.el(w, "span", "", { opacity: 0 }, ch));
            A.tl.to(ls, { opacity: 1, duration: 0.01, stagger: 0.12 }, e.t + 0.9);
          },
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
