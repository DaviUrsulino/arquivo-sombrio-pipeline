<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio glow</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      /* Identidade inspirada no @mateus.curta.ia: preto absoluto, glow vermelho radial atrás de tudo,
         anel de ícone neon, número gigante com barra de progresso, diagrama de nós conectados. Sem
         personagem nenhum -- é puro dado/UI abstrata, igual a referência. */
      @font-face { font-family: "Arch"; src: url("assets/fonts/ArchivoBlack.ttf"); }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      @font-face { font-family: "Mont"; src: url("assets/fonts/Montserrat.ttf"); font-weight: 100 900; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #050304; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Mont", sans-serif; color: #fff; }
      #fundo { position: absolute; inset: 0; background: radial-gradient(ellipse 700px 500px at 50% 18%, rgba(140,10,22,.16) 0%, rgba(30,3,6,.05) 50%, #050304 78%); }
      #estrelas { position: absolute; inset: 0; opacity: .8; background-image: radial-gradient(1.5px 1.5px at 20% 15%, #fff 0, transparent 100%), radial-gradient(1.5px 1.5px at 70% 8%, #fff 0, transparent 100%), radial-gradient(1px 1px at 45% 25%, #fff 0, transparent 100%), radial-gradient(1.5px 1.5px at 85% 30%, #fff 0, transparent 100%), radial-gradient(1px 1px at 10% 40%, #fff 0, transparent 100%), radial-gradient(1.5px 1.5px at 60% 50%, #fff 0, transparent 100%), radial-gradient(1px 1px at 30% 65%, #fff 0, transparent 100%), radial-gradient(1.5px 1.5px at 90% 70%, #fff 0, transparent 100%), radial-gradient(1px 1px at 15% 85%, #fff 0, transparent 100%), radial-gradient(1.5px 1.5px at 75% 90%, #fff 0, transparent 100%); background-size: 1080px 1920px; }
      #topo { position: absolute; left: 54px; right: 54px; top: 64px; z-index: 5; }
      #topo .topo-linha { display: flex; align-items: center; justify-content: space-between; font-family: "Mono"; font-size: 24px; color: #ff8a8a; text-transform: uppercase; letter-spacing: .08em; }
      #topo .topo-linha .cat { display: flex; align-items: center; gap: 10px; }
      #topo .topo-linha .cat i { width: 10px; height: 10px; background: #ff3b3b; transform: rotate(45deg); display: block; }
      #topo .topo-linha .passo { color: #6b6468; }
      #topo .segmentos { display: flex; gap: 8px; margin-top: 14px; }
      #topo .segmentos i { flex: 1; height: 5px; border-radius: 3px; background: #2a1316; display: block; }
      #topo .segmentos i.on { background: #ff3b3b; box-shadow: 0 0 10px #ff3b3b; }
      .cena { position: absolute; inset: 0; opacity: 0; }
      .palco { position: absolute; left: 0; width: 1080px; top: 420px; display: flex; flex-direction: column; align-items: center; gap: 48px; }
      .frase { font-family: "Arch"; font-size: 68px; text-transform: uppercase; letter-spacing: -1px; text-align: center; line-height: 1.1; max-width: 920px; color: #e8e2e4; }
      .frase .dest { color: #ff3b3b; }
      .orbita { position: relative; width: 420px; height: 420px; display: grid; place-items: center; }
      .orbita .anel-tracejado { position: absolute; inset: 40px; border-radius: 50%; border: 2px dashed rgba(255,59,59,.35); }
      .orbita .centro { position: relative; width: 190px; height: 190px; border-radius: 50%; background: #0c0809; border: 2px solid rgba(255,59,59,.5); display: grid; place-items: center; box-shadow: 0 0 40px rgba(255,59,59,.3); z-index: 2; }
      .orbita .satelite { position: absolute; width: 74px; height: 74px; border-radius: 50%; background: #0c0809; border: 2px solid rgba(255,59,59,.6); display: grid; place-items: center; box-shadow: 0 0 20px rgba(255,59,59,.35); }
      .capsula { display: flex; align-items: center; gap: 18px; border: 2px solid rgba(255,59,59,.4); border-radius: 16px; padding: 18px 28px; background: rgba(255,59,59,.05); }
      .capsula .cap-txt small { display: block; font-family: "Mono"; font-size: 20px; color: #8a7a7a; text-transform: uppercase; letter-spacing: .06em; }
      .capsula .cap-txt b { font-family: "Arch"; font-size: 44px; color: #ff3b3b; }
      .numero { font-family: "Arch"; font-size: 170px; line-height: 1; letter-spacing: -6px; text-shadow: 0 0 50px rgba(255,59,59,.65); }
      .barra-wrap { width: 760px; height: 14px; border-radius: 8px; background: rgba(255,255,255,.06); overflow: hidden; }
      .barra-fill { height: 100%; width: 0%; background: linear-gradient(90deg, #ff3b3b, #ff8a8a); box-shadow: 0 0 20px #ff3b3b; }
      .sub { font-family: "Mono"; font-size: 28px; color: #c98a8a; text-transform: uppercase; letter-spacing: .08em; }
      .nos { display: flex; align-items: center; gap: 0; }
      .no { width: 190px; height: 190px; border-radius: 50%; border: 3px solid rgba(255,59,59,.55); display: grid; place-items: center; background: rgba(255,59,59,.06); box-shadow: 0 0 50px rgba(255,59,59,.3); flex: none; }
      .no-rot { font-family: "Mono"; font-size: 24px; color: #ffb0b0; text-align: center; margin-top: 18px; text-transform: uppercase; }
      .no-col { display: flex; flex-direction: column; align-items: center; }
      .linha-no { width: 90px; height: 3px; background: linear-gradient(90deg, rgba(255,59,59,.1), #ff3b3b); margin: 0 -4px; }
      .lista-n { display: flex; flex-direction: column; gap: 30px; width: 860px; }
      .item-n { display: flex; align-items: center; gap: 24px; font-family: "Mono"; font-size: 38px; color: #f0dede; }
      .item-n .pt { width: 20px; height: 20px; border-radius: 50%; background: #ff3b3b; box-shadow: 0 0 18px #ff3b3b; flex: none; }
      .janela-n { width: 920px; border-radius: 22px; background: rgba(255,255,255,.03); border: 1.5px solid rgba(255,80,80,.3); overflow: hidden; }
      .janela-n .barra { display: flex; align-items: center; gap: 12px; padding: 18px 24px; border-bottom: 1px solid rgba(255,80,80,.2); font-family: "Mono"; font-size: 22px; color: #ff8a8a; }
      .janela-n .barra i { width: 14px; height: 14px; border-radius: 50%; background: rgba(255,80,80,.4); display: block; }
      .janela-n .corpo { padding: 40px; }
      .cmd-n { font-family: "Mono"; font-size: 42px; color: #ff8a8a; } .cmd-n b { color: #fff; }
      .saida-n { font-family: "Mono"; font-size: 26px; color: #8aff9a; margin-top: 22px; }
      .com-n { display: flex; align-items: center; gap: 26px; }
      .com-n .pt-g { width: 26px; height: 26px; border-radius: 50%; background: #ff3b3b; box-shadow: 0 0 24px #ff3b3b; }
      .com-n .tx { font-family: "Arch"; font-size: 84px; letter-spacing: -2px; color: #fff; text-shadow: 0 0 40px rgba(255,59,59,.6); }
      #legenda { position: absolute; left: 70px; right: 70px; top: 1600px; height: 170px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 14px; opacity: 0; }
      .w { font-size: 54px; font-weight: 700; color: #ece2e2; display: inline-block; letter-spacing: -1px; }
      .w.dest { font-family: "Arch"; font-size: 60px; color: #ff3b3b; text-shadow: 0 0 30px rgba(255,59,59,.7); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="estrelas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
      <div id="topo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="3">
        <div class="topo-linha"><span class="cat"><i></i>O PROJETO</span><span class="passo" id="topo-passo">01/05</span></div>
        <div class="segmentos" id="topo-segmentos"></div>
      </div>
{{CENAS}}
      <div id="progresso" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="7"></div>
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <audio id="trilha" src="assets/musica/trilha-pixel.mp3" data-start="0" data-duration="{{DURACAO}}" data-track-index="10" data-volume="0.12"></audio>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const COR_G = { laranja: "#ff8a4d", azul: "#ff3b3b", verde: "#ff3b3b", roxo: "#ff3b3b", vermelho: "#ff3b3b", amarelo: "#ff8a8a", branco: "#fff", rosa: "#ff3b3b" };
      const repo = () => Object.values(window.DADOS.repos || {})[0] || { repo: "", estrelas: 0 };

      function frase(A, palco, antes, chave, t) {
        const f = A.el(palco, "div", "frase");
        const ps = antes.toUpperCase().split(" ").map((p) => A.el(f, "span", "", { display: "inline-block" }, p + "&nbsp;"));
        const c = A.el(f, "span", "dest", { display: "inline-block" }, chave.toUpperCase());
        A.tl.fromTo(ps, { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.3, stagger: 0.07 }, t);
        A.tl.fromTo(c, { opacity: 0, scale: 1.3 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2.5)" }, t + ps.length * 0.07);
      }
      const cai = (A, el, t) => A.tl.fromTo(el, { opacity: 0, y: 24, filter: "blur(6px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.4, ease: "expo.out" }, t);

      window.TEMA = {
        cores: COR_G, acento: "vermelho", traco: 2, escalaTitulo: 1, larguraLetra: 0.5,
        entrar(A, alvo, t) { cai(A, alvo, t); },
        palavraLegenda(A, s, t) { A.tl.fromTo(s, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.2 }, t); },
        transicao(A, palco, c) {
          A.tl.fromTo(palco, { opacity: 0 }, { opacity: 1, duration: 0.25 }, c.inicio);
          A.tl.to(palco, { opacity: 0, filter: "blur(14px)", duration: 0.2 }, c.inicio + c.duracao - 0.2);
        },
        fundo(A, dur) {
          A.tl.fromTo("#fundo", { opacity: 0.85 }, { opacity: 1, duration: dur / 2, ease: "sine.inOut", yoyo: true, repeat: 1 }, 0);
          const total = A.D.cenas.length;
          const seg = document.getElementById("topo-segmentos");
          for (let i = 0; i < total; i++) A.el(seg, "i");
          const passo = document.getElementById("topo-passo");
          A.D.cenas.forEach((c, i) => {
            A.tl.set(passo, { textContent: String(i + 1).padStart(2, "0") + "/" + String(total).padStart(2, "0") }, c.inicio);
            [...seg.children].forEach((s, k) => A.tl.set(s, { className: k <= i ? "on" : "" }, c.inicio));
          });
        },
        visuais: {
          titulo_pixel(A, palco, e) {
            const ls = e.linhas.map((l) => l.texto.toLowerCase());
            frase(A, palco, ls.slice(0, -1).join(" "), ls[ls.length - 1], e.t);
          },
          contador(A, palco, e) {
            frase(A, palco, "", e.rotulo || "numero", e.t);
            const cap = A.el(palco, "div", "capsula");
            cap.appendChild(A.svgIcone("star", "#ff3b3b", 48));
            const txt = A.el(cap, "div", "cap-txt", null, `<small>estrelas no github</small><b>0</b>`);
            cai(A, cap, e.t + 0.4);
            const n = txt.querySelector("b");
            const st = { v: 0 };
            A.tl.to(st, { v: e.valor !== undefined ? e.valor : repo().estrelas, duration: 1.4, ease: "power3.out", onUpdate: () => (n.textContent = A.mil(Math.round(st.v))) }, e.t + 0.5);
          },
          cadeia(A, palco, e) {
            frase(A, palco, "", "fluxo", e.t);
            const caixa = A.el(palco, "div", "nos");
            e.nos.forEach((n, i) => {
              if (i > 0) { const l = A.el(caixa, "div", "linha-no"); A.tl.fromTo(l, { scaleX: 0 }, { scaleX: 1, duration: 0.3, transformOrigin: "left" }, (e.ts ? e.ts[i] : e.t + i * 0.5) - 0.15); }
              const col = A.el(caixa, "div", "no-col");
              const no = A.el(col, "div", "no"); no.appendChild(A.svgIcone(n.icone, "#ff3b3b", 80));
              A.el(col, "div", "no-rot", null, n.rotulo);
              cai(A, col, (e.ts ? e.ts[i] : e.t + i * 0.5));
            });
          },
          lista(A, palco, e) {
            frase(A, palco, "", "inclui", e.t);
            const c = A.el(palco, "div", "lista-n");
            e.itens.forEach((txt, k) => { const l = A.el(c, "div", "item-n", null, `<span class="pt"></span>${txt}`); cai(A, l, e.ts ? e.ts[k] : e.t + k * 0.4); });
          },
          terminal(A, palco, e) {
            frase(A, palco, "", e.rotulo || "rodar", e.t);
            const t0 = e.ts ? e.ts[0] : e.t;
            const j = A.el(palco, "div", "janela-n");
            A.el(j, "div", "barra", null, "<i></i><i></i><i></i><span>" + (e.rotulo || "terminal") + "</span>");
            const corpo = A.el(j, "div", "corpo");
            const cmd = A.el(corpo, "div", "cmd-n", null, "<b>❯</b> ");
            const ls = [...e.comando].map((ch) => A.el(cmd, "span", "", { opacity: 0 }, ch === " " ? "&nbsp;" : ch));
            cai(A, j, t0 + 0.3);
            A.tl.to(ls, { opacity: 1, duration: 0.01, stagger: 0.05 }, t0 + 0.7);
            if (e.texto) { const s = A.el(corpo, "div", "saida-n", null, "✓ " + e.texto); cai(A, s, e.ts ? e.ts[1] : t0 + 1.4); }
          },
          icone_pixel(A, palco, e) {
            frase(A, palco, "", e.rotulo || "", e.t);
            const orb = A.el(palco, "div", "orbita");
            A.el(orb, "div", "anel-tracejado");
            const centro = A.el(orb, "div", "centro"); centro.appendChild(A.svgIcone(e.icone, "#ff3b3b", 90));
            cai(A, centro, e.t + 0.3);
            const SATS = ["zap", "github", "check", "sparkles"];
            const raio = 170;
            SATS.forEach((nome, i) => {
              const ang = (Math.PI * 2 * i) / SATS.length - Math.PI / 2;
              const x = 210 + raio * Math.cos(ang) - 37, y = 210 + raio * Math.sin(ang) - 37;
              const sat = A.el(orb, "div", "satelite", { left: x + "px", top: y + "px" });
              sat.appendChild(A.svgIcone(nome, "#ff3b3b", 32));
              A.tl.fromTo(sat, { opacity: 0, scale: 0.4 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }, e.t + 0.5 + i * 0.08);
            });
          },
          cta(A, palco, e, palavra) {
            frase(A, palco, "comenta", palavra, e.t);
            const com = A.el(palco, "div", "com-n");
            A.el(com, "div", "pt-g");
            const tx = A.el(com, "div", "tx");
            const ls = [...palavra.toUpperCase()].map((ch) => A.el(tx, "span", "", { opacity: 0 }, ch));
            cai(A, com, e.t + 1);
            A.tl.to(ls, { opacity: 1, duration: 0.01, stagger: 0.12 }, e.t + 1.2);
          },
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
