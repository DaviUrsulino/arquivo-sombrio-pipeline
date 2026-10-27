<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio rabisco</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      @font-face { font-family: "Mao"; src: url("assets/fonts/PatrickHand-Regular.ttf"); }
      @font-face { font-family: "Grotesk"; src: url("assets/fonts/SpaceGrotesk.ttf"); font-weight: 300 700; }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      :root { --papel: #fbf8f1; --tinta: #161616; --apagado: #6b665c; --acento: #2563eb; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--papel); }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Mao", cursive; color: var(--tinta); }
      #papel { position: absolute; inset: 0; background-image: radial-gradient(rgba(0,0,0,.09) 2px, transparent 2.5px); background-size: 46px 46px; }
      .cena { position: absolute; inset: 0; opacity: 0; }
      .palco { position: absolute; left: 70px; right: 70px; top: 200px; height: 1170px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 46px; transform-origin: 50% 45%; filter: url(#tremido); }
      .ic { overflow: visible; }

      .titulo { text-align: center; position: relative; }
      .titulo-linha { font-family: "Grotesk"; font-weight: 700; line-height: 1.02; letter-spacing: -3px; text-transform: lowercase; }
      .pal { display: inline-block; white-space: pre; }
      .sub { position: absolute; left: 6%; right: 6%; bottom: -34px; height: 40px; }

      .chip { display: inline-flex; align-items: center; gap: 16px; padding: 12px 28px; border: 4px solid var(--tinta); border-radius: 20px 26px 18px 24px; background: #fff; font-family: "Mono"; font-weight: 700; font-size: 36px; box-shadow: 6px 7px 0 var(--tinta); }
      .contador { display: flex; flex-direction: column; align-items: center; gap: 26px; }
      .num-linha { display: flex; align-items: center; gap: 20px; }
      .estrela { fill: #ffd84a; }
      .num { font-family: "Grotesk"; font-weight: 700; font-size: 250px; line-height: 1; white-space: nowrap; letter-spacing: -8px; }
      .rotulo { font-size: 66px; color: var(--apagado); }

      .cadeia { display: flex; flex-direction: column; align-items: center; gap: 4px; }
      .no { display: flex; align-items: center; gap: 36px; width: 900px; padding: 26px 34px; background: #fff; border: 5px solid var(--tinta); border-radius: 34px 26px 38px 24px; box-shadow: 8px 9px 0 var(--tinta); }
      .no:nth-child(4n+3) { transform: rotate(-1.2deg); } .no:nth-child(4n+1) { transform: rotate(0.8deg); }
      .tile { width: 170px; height: 170px; flex: none; display: grid; place-items: center; border-radius: 48% 52% 45% 55% / 55% 45% 55% 45%; }
      .tile .ic { width: 70%; height: 70%; }
      .tile.big { width: 420px; height: 420px; }
      .no-rot { font-family: "Mao"; font-size: 100px; line-height: 1; }
      .seta { height: 76px; }

      .lista { display: flex; flex-direction: column; gap: 30px; width: 940px; }
      .item { display: flex; align-items: center; gap: 30px; padding: 26px 34px; background: #fff; border: 5px solid var(--tinta); border-radius: 26px 34px 22px 30px; box-shadow: 7px 8px 0 var(--tinta); }
      .item:nth-child(even) { transform: rotate(-1deg); }
      .marca { width: 96px; height: 96px; flex: none; display: grid; place-items: center; border: 4px solid var(--tinta); border-radius: 18px 24px 16px 22px; background: #c9f7d3; }
      .item-txt { font-size: 84px; line-height: 1; }

      .janela { width: 940px; overflow: hidden; background: #fff; border: 5px solid var(--tinta); border-radius: 30px 24px 34px 26px; box-shadow: 10px 11px 0 var(--tinta); }
      .barra { display: flex; align-items: center; gap: 14px; padding: 20px 26px; border-bottom: 5px solid var(--tinta); background: #e9f0ff; font-family: "Mao"; font-size: 40px; }
      .barra i { width: 26px; height: 26px; border-radius: 50%; border: 4px solid var(--tinta); background: #ff6b6b; display: block; }
      .barra i:nth-child(2) { background: #ffd84a; } .barra i:nth-child(3) { background: #4ee06a; }
      .barra span { margin-left: auto; }
      .corpo { padding: 40px; font-family: "Mono"; }
      .cmd { font-size: 62px; font-weight: 800; word-break: break-all; } .cmd b { color: var(--acento); } .cursor { color: var(--acento); }
      .saida { margin-top: 26px; font-family: "Mao"; font-size: 56px; color: #15803d; }
      .url { display: flex; align-items: center; gap: 22px; padding: 40px; font-family: "Mono"; font-size: 44px; }

      .icone-grande { display: flex; flex-direction: column; align-items: center; gap: 50px; position: relative; }
      .rotulo-grande { font-family: "Grotesk"; font-weight: 700; font-size: 130px; letter-spacing: -4px; text-align: center; line-height: 1; text-transform: lowercase; }
      .comparar { display: flex; gap: 30px; }
      .card { width: 450px; padding: 36px; background: #fff; border: 5px solid; border-radius: 30px; box-shadow: 8px 9px 0 var(--tinta); display: flex; flex-direction: column; gap: 18px; }
      .card-tit { font-size: 80px; } .card-lin { font-size: 44px; } .card-lin span { display: block; height: 18px; margin-top: 8px; border: 3px solid var(--tinta); border-radius: 10px; }
      .niveis { display: flex; align-items: flex-end; gap: 50px; height: 800px; }
      .nivel { display: flex; flex-direction: column; align-items: center; gap: 16px; }
      .barra-n { width: 200px; border: 5px solid var(--tinta); border-radius: 22px 22px 6px 6px; }
      .selo { padding: 16px 40px; border: 5px solid var(--tinta); background: #ffd84a; border-radius: 999px; font-size: 70px; }

      #topo { position: absolute; left: 0; right: 0; top: 100px; height: 90px; display: flex; justify-content: center; align-items: flex-start; }
      .topo-chip { display: inline-flex; align-items: center; gap: 14px; padding: 10px 26px; border: 4px solid var(--tinta); border-radius: 999px; background: #fff; font-family: "Mono"; font-weight: 700; font-size: 30px; }
      #particulas { position: absolute; inset: 0; }
      .particula { position: absolute; width: 22px; height: 22px; }
      .comentario { display: flex; align-items: center; gap: 28px; width: 920px; padding: 30px 34px; background: #fff; border: 5px solid var(--tinta); border-radius: 34px; box-shadow: 10px 11px 0 var(--tinta); }
      .avatar { width: 110px; height: 110px; flex: none; border-radius: 50%; border: 4px solid var(--tinta); background: linear-gradient(135deg, #feda75, #fa7e1e, #d62976, #962fbf); }
      .com-corpo { flex: 1; } .com-user { font-size: 44px; color: var(--apagado); }
      .com-txt { font-family: "Grotesk"; font-weight: 700; font-size: 120px; line-height: 1; color: var(--acento); letter-spacing: -3px; }
      .dm { display: inline-flex; align-items: center; gap: 18px; font-size: 60px; }

      #legenda { position: absolute; left: 50px; right: 50px; top: 1450px; height: 260px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 22px; opacity: 0; }
      .w { font-family: "Grotesk"; font-weight: 700; font-size: 92px; line-height: 1.1; letter-spacing: -2px; color: var(--tinta); display: inline-block; -webkit-text-stroke: 0; text-shadow: 5px 5px 0 #fff, -3px -3px 0 #fff, 3px -3px 0 #fff, -3px 3px 0 #fff; }
      .w.dest { color: #fff; background: var(--acento); padding: 0 18px; border-radius: 14px; text-shadow: none; transform: rotate(-2deg); }
    </style>
  </head>
  <body>
    <svg width="0" height="0" style="position:absolute">
      <filter id="tremido"><feTurbulence id="turb" type="fractalNoise" baseFrequency="0.018" numOctaves="2" seed="3" /><feDisplacementMap in="SourceGraphic" scale="5" /></filter>
    </svg>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="papel" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="particulas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
{{CENAS}}
      <div id="topo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="7"></div>
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const PASTEL = { laranja: "#ffd2a8", azul: "#bcd6ff", verde: "#c9f7d3", roxo: "#e1d2ff", vermelho: "#ffc2c2", amarelo: "#fff0a3", branco: "#f1efe9", rosa: "#ffd1f0" };
      window.TEMA = {
        cores: { laranja: "#f97316", azul: "#2563eb", verde: "#16a34a", roxo: "#7c3aed", vermelho: "#dc2626", amarelo: "#eab308", branco: "#161616", rosa: "#db2777" },
        acento: "azul", destaqueTitulo: "azul", traco: 2.3, escalaTitulo: 1.0, larguraLetra: 0.55, desenharIcone: true,
        corIcone: () => "#161616",
        pintarTile(tile, hex) {
          const nome = Object.keys(this.cores).find((k) => this.cores[k] === hex) || "azul";
          tile.style.background = PASTEL[nome];
        },
        entrar(A, alvo, t, i) {
          // carimbo: cai girando e assenta com um quique, como papel colado
          const giro = i % 2 ? 6 : -6;
          A.tl.fromTo(alvo, { opacity: 0, scale: 0.6, rotation: giro }, { opacity: 1, scale: 1, rotation: 0, duration: 0.45, ease: "back.out(2.4)" }, t);
        },
        sublinhado(A, caixa, t) {
          const s = A.el(caixa, "div", "sub", null, '<svg width="100%" height="40" viewBox="0 0 400 40" preserveAspectRatio="none"><path pathLength="1" d="M5 28 C 90 8, 180 34, 260 18 S 370 12, 395 22" fill="none" stroke="#2563eb" stroke-width="9" stroke-linecap="round"/></svg>');
          A.tl.fromTo(s.querySelector("path"), { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }, t);
        },
        palavraLegenda(A, s, t, dest) {
          A.tl.fromTo(s, { opacity: 0, scale: dest ? 1.5 : 0.7, rotation: dest ? -8 : 0 }, { opacity: 1, scale: 1, rotation: dest ? -2 : 0, duration: 0.25, ease: "back.out(3)" }, t);
        },
        transicao(A, palco, c, i) {
          // virada de página: desliza de lado alternando, com leve rotação
          const lado = i % 2 ? -1 : 1;
          A.tl.fromTo(palco, { opacity: 0, x: 400 * lado, rotation: 4 * lado }, { opacity: 1, x: 0, rotation: 0, duration: 0.5, ease: "back.out(1.4)" }, c.inicio);
          A.tl.to(palco, { opacity: 0, x: -300 * lado, rotation: -3 * lado, duration: 0.18, ease: "power2.in" }, c.inicio + c.duracao - 0.18);
        },
        raios(A, caixa, t) {
          for (let k = 0; k < 8; k++) {
            const ang = (k / 8) * Math.PI * 2;
            const r = A.el(caixa, "div", "", { position: "absolute", left: "50%", top: "210px", width: "60px", height: "10px", marginLeft: "-30px", background: "#eab308", borderRadius: "6px", transformOrigin: "50% 50%" });
            const x = Math.cos(ang) * 290, y = Math.sin(ang) * 290;
            A.tl.fromTo(r, { x: x * 0.7, y: y * 0.7, rotation: (ang * 180) / Math.PI, opacity: 0, scaleX: 0.2 }, { x, y, opacity: 1, scaleX: 1, duration: 0.35, ease: "back.out(3)" }, t + k * 0.03);
          }
        },
        particula(A, p, x, y, dur, atraso, total) {
          // rabiscos de estrelinha espalhados que piscam
          p.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 2v20M2 12h20M5 5l14 14M19 5L5 19" stroke="#eab308" stroke-width="3" stroke-linecap="round"/></svg>';
          A.tl.set(p, { x, y: y - 300, opacity: 0 }, 0);
          for (let t = atraso; t < total; t += dur) A.tl.fromTo(p, { opacity: 0, scale: 0.3, rotation: 0 }, { opacity: 0.7, scale: 1.2, rotation: 90, duration: 0.6, yoyo: true, repeat: 1, ease: "back.out(2)" }, t);
        },
        fundo(A, dur) {
          // o "tremido" do traço muda de semente 8x por segundo: parece desenho feito à mão quadro a quadro
          const turb = document.getElementById("turb"); const st = { f: 0 };
          A.tl.to(st, { f: dur * 8, duration: dur, ease: "none", onUpdate: () => turb.setAttribute("seed", String(Math.floor(st.f) % 5 + 1)) }, 0);
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
