<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio cartão</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      /* Identidade inspirada nos criativos do @oandrenuneu (Edit IA PRO) e @motionia.br: fundo azul-marinho
         com listra diagonal, bandeirola amarela no topo anunciando o assunto da cena, cartão creme central
         tipo mockup de app/terminal, e o Robô Estagiário parado embaixo acompanhando a fala. */
      @font-face { font-family: "Arch"; src: url("assets/fonts/ArchivoBlack.ttf"); }
      @font-face { font-family: "Hand"; src: url("assets/fonts/PatrickHand-Regular.ttf"); }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      @font-face { font-family: "Mont"; src: url("assets/fonts/Montserrat.ttf"); font-weight: 100 900; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #181e4b; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Mont", sans-serif; color: #15163a; }
      #fundo { position: absolute; inset: 0; background: linear-gradient(165deg, #28336d 0%, #181e4b 70%); }
      #listras { position: absolute; inset: -200px; bottom: 420px; background: repeating-linear-gradient(118deg, rgba(255,255,255,.035) 0 26px, transparent 26px 64px); }
      #chao { position: absolute; left: 0; right: 0; bottom: 0; height: 460px; background: #daa167; }
      #chao::before { content: ""; position: absolute; inset: 0; background-image:
          repeating-linear-gradient(0deg, rgba(0,0,0,.08) 0 4px, transparent 4px 70px),
          repeating-linear-gradient(90deg, rgba(0,0,0,.08) 0 4px, transparent 4px 140px);
        background-position: 0 0, 70px 70px; }
      #chao-linha { position: absolute; left: 0; right: 0; bottom: 460px; height: 6px; background: #0d1030; opacity: .5; }
      #mesa { position: absolute; left: -18px; bottom: 390px; width: 170px; z-index: 3; }
      #mesa .tampo { position: absolute; left: 0; top: 0; width: 170px; height: 16px; background: #6b4226; border-radius: 3px; box-shadow: 0 4px 0 rgba(0,0,0,.15); }
      #mesa .perna { position: absolute; top: 16px; width: 12px; height: 150px; background: #6b4226; }
      #mesa .perna.esq { left: 14px; } #mesa .perna.dir { right: 14px; }
      #progresso { position: absolute; left: 0; top: 0; width: 1080px; height: 10px; background: #ffd84a; z-index: 5; }
      #personagem { position: absolute; left: 60px; top: 1430px; width: 290px; height: 380px; z-index: 4; }
      #personagem .pose { position: absolute; left: 0; bottom: 0; width: 290px; }
      .contador-ferr { position: absolute; left: 0; right: 70px; top: 440px; display: flex; justify-content: flex-end; z-index: 3; }
      .contador-ferr div { background: #fff; color: #17183a; font-family: "Mont"; font-weight: 800; font-size: 26px; text-transform: uppercase; padding: 14px 26px; border-radius: 40px; box-shadow: 0 10px 20px rgba(0,0,0,.3); }
      .contador-ferr span { color: #c96a14; font-family: "Arch"; font-size: 32px; margin-left: 8px; }
      .cena { position: absolute; inset: 0; opacity: 0; }
      .palco { position: absolute; left: 0; width: 1080px; top: 300px; display: flex; flex-direction: column; align-items: center; gap: 36px; }
      .handle { background: #fff; color: #17183a; font-family: "Mont"; font-weight: 800; font-size: 28px; padding: 14px 34px; border-radius: 40px; margin-bottom: -6px; box-shadow: 0 10px 20px rgba(0,0,0,.3); }
      .bandeirola { position: relative; background: #fdefd7; color: #17183a; font-family: "Arch"; text-transform: uppercase; font-size: 40px; letter-spacing: -0.5px; padding: 28px 56px; text-align: center; max-width: 880px;
        clip-path: polygon(0% 10px, 2% 0%, 6% 8px, 11% 0%, 16% 8px, 21% 0%, 26% 8px, 31% 0%, 36% 8px, 41% 0%, 46% 8px, 51% 0%, 56% 8px, 61% 0%, 66% 8px, 71% 0%, 76% 8px, 81% 0%, 86% 8px, 91% 0%, 96% 8px, 100% 0%,
          100% 100%, 96% calc(100% - 8px), 91% 100%, 86% calc(100% - 8px), 81% 100%, 76% calc(100% - 8px), 71% 100%, 66% calc(100% - 8px), 61% 100%, 56% calc(100% - 8px), 51% 100%, 46% calc(100% - 8px), 41% 100%, 36% calc(100% - 8px), 31% 100%, 26% calc(100% - 8px), 21% 100%, 16% calc(100% - 8px), 11% 100%, 6% calc(100% - 8px), 1% 100%, 0% calc(100% - 10px));
        box-shadow: 0 16px 30px rgba(0,0,0,.4); }
      .fita { position: absolute; top: -18px; width: 92px; height: 46px; background: #e0b02a; opacity: .92; box-shadow: 0 4px 10px rgba(0,0,0,.3); }
      .fita.esq { left: -20px; transform: rotate(-38deg); }
      .fita.dir { right: -20px; transform: rotate(38deg); }
      .cartao { width: 900px; background: #f6f1e3; border-radius: 30px; box-shadow: 0 40px 90px rgba(0,0,0,.45); overflow: hidden; }
      .cartao .topo { display: flex; align-items: center; gap: 12px; padding: 20px 28px; background: #ece4cc; border-bottom: 2px solid #ddd2ad; font-family: "Mono"; font-size: 24px; color: #8a7d55; }
      .cartao .topo i { width: 16px; height: 16px; border-radius: 50%; background: #d8cba3; display: block; }
      .cartao .corpo { padding: 44px 48px; }
      .linha-app { display: flex; align-items: center; gap: 24px; }
      .logo { width: 128px; height: 128px; border-radius: 24px; display: grid; place-items: center; flex: none; }
      .tt { font-size: 50px; font-weight: 800; letter-spacing: -1px; color: #17183a; } .st { font-size: 28px; color: #6d6450; margin-top: 6px; }
      .lin { display: flex; align-items: center; gap: 22px; padding: 26px 8px; font-size: 44px; font-weight: 700; color: #17183a; border-bottom: 2px dashed #e1d6b3; }
      .lin:last-child { border-bottom: none; }
      .lin .bolinha { width: 26px; height: 26px; border-radius: 50%; background: #39c06a; box-shadow: 0 0 0 6px #39c06a2a; flex: none; }
      .numero { font-size: 210px; font-family: "Arch"; line-height: 1; text-align: center; color: #17183a; }
      .sub-num { text-align: center; font-size: 34px; color: #6d6450; margin-top: 10px; }
      .cmd { font-family: "Mono"; font-weight: 700; font-size: 44px; color: #17183a; word-break: break-all; } .cmd b { color: #c96a14; }
      .saida { font-family: "Mono"; font-size: 28px; color: #2f8f52; margin-top: 22px; }
      .com { display: flex; align-items: center; gap: 22px; }
      .com .av { width: 92px; height: 92px; border-radius: 50%; background: linear-gradient(135deg, #feda75, #fa7e1e, #d62976, #962fbf); flex: none; }
      .com .tx { font-size: 86px; font-weight: 800; color: #17183a; letter-spacing: -2px; }
      .enviar { margin-left: auto; width: 92px; height: 92px; border-radius: 50%; background: #ffd84a; display: grid; place-items: center; }
      .preco-duas { display: flex; gap: 24px; }
      .preco-card { flex: 1; background: #fffaf0; border-radius: 20px; border: 3px solid #e1d6b3; padding: 30px 20px; text-align: center; }
      .preco-card b { display: block; font-family: "Arch"; font-size: 30px; color: #6d6450; margin-bottom: 10px; }
      .preco-card .pv { font-family: "Arch"; font-size: 64px; color: #17183a; }
      .preco-card small { display: block; font-size: 22px; color: #8a7d55; margin-top: 8px; }
      #legenda { position: absolute; left: 70px; right: 70px; top: 1600px; height: 170px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 14px; opacity: 0; }
      .w { font-size: 56px; font-weight: 800; color: #fff; display: inline-block; letter-spacing: -1px; text-shadow: 0 2px 8px rgba(0,0,0,.4); }
      .w.dest { font-family: "Hand"; font-weight: 400; font-size: 70px; color: #ffd84a; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="listras" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
      <div id="chao" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="2"></div>
      <div id="chao-linha" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="2"></div>
      <div id="mesa" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="4">
        <div class="tampo"></div><div class="perna esq"></div><div class="perna dir"></div>
      </div>
      <div id="personagem" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="5"></div>
      <div id="contador" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="3"></div>
{{CENAS}}
      <div id="progresso" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="7"></div>
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <audio id="trilha" src="assets/musica/trilha-pixel.mp3" data-start="0" data-duration="{{DURACAO}}" data-track-index="10" data-volume="0.15"></audio>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const COR_C = { laranja: "#ff9d4d", azul: "#2f6fe0", verde: "#39c06a", roxo: "#8a5fd6", vermelho: "#e0453f", amarelo: "#e0a913", branco: "#17183a", rosa: "#d6559a" };
      const repo = () => Object.values(window.DADOS.repos || {})[0] || { repo: "", estrelas: 0 };

      // bandeirola: papel rasgado com fita nos cantos, igual as referências; handle fixo acima.
      let handleFeito = false;
      function bandeirola(A, palco, texto, t) {
        if (!handleFeito) { const h = A.el(palco, "div", "handle", null, "@robo.estagiario"); A.tl.set(h, { opacity: 1 }, 0); handleFeito = true; }
        const wrap = A.el(palco, "div", "", { position: "relative" });
        A.el(wrap, "div", "fita esq");
        A.el(wrap, "div", "fita dir");
        const b = A.el(wrap, "div", "bandeirola", null, texto);
        A.tl.fromTo(wrap, { opacity: 0, y: -50, rotation: -2 }, { opacity: 1, y: 0, rotation: 0, duration: 0.4, ease: "back.out(2.4)" }, t);
      }
      function cartao(A, pai, titulo, t) {
        const c = A.el(pai, "div", "cartao");
        A.el(c, "div", "topo", null, `<i></i><i></i><i></i><span style="margin-left:8px">${titulo}</span>`);
        A.tl.fromTo(c, { opacity: 0, y: 70, scale: 0.94 }, { opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "expo.out" }, t);
        return A.el(c, "div", "corpo");
      }
      const cai = (A, el, t) => A.tl.fromTo(el, { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }, t);

      window.TEMA = {
        cores: COR_C, acento: "amarelo", traco: 2, escalaTitulo: 1, larguraLetra: 0.5,
        entrar(A, alvo, t) { cai(A, alvo, t); },
        palavraLegenda(A, s, t) { A.tl.fromTo(s, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.18 }, t); },
        transicao(A, palco, c) {
          A.tl.fromTo(palco, { opacity: 0 }, { opacity: 1, duration: 0.25 }, c.inicio);
          A.tl.to(palco, { opacity: 0, y: -30, duration: 0.18 }, c.inicio + c.duracao - 0.18);
        },
        fundo(A, dur) {
          A.tl.fromTo("#listras", { x: 0, y: 0 }, { x: -60, y: -40, duration: dur, ease: "sine.inOut" }, 0);
          const caixa = document.getElementById("contador");
          const total = A.D.cenas.length;
          const el = A.el(caixa, "div", "contador-ferr", null, `<div>FERRAMENTAS <span id="contador-n">0/${total}</span></div>`);
          A.D.cenas.forEach((c, i) => A.tl.set("#contador-n", { textContent: `${i + 1}/${total}` }, c.inicio));
        },
        visuais: {
          titulo_pixel(A, palco, e) {
            bandeirola(A, palco, e.linhas.map((l) => l.texto).join(" "), e.t);
            const c = cartao(A, palco, "github.com/" + repo().repo, e.t + 0.5);
            const la = A.el(c, "div", "linha-app");
            const lg = A.el(la, "div", "logo", { background: "#ffd84a33", border: "2px solid #c99a1a" }); lg.appendChild(A.svgIcone("bot", "#8a6a14", 70));
            A.el(la, "div", "", null, `<div class="tt">${(repo().repo || "").split("/")[1] || ""}</div><div class="st">${(repo().descricao || "").slice(0, 54)}…</div>`);
          },
          contador(A, palco, e) {
            bandeirola(A, palco, e.rotulo || "NÚMERO DO DIA", e.t);
            const c = cartao(A, palco, "estrelas no GitHub", e.t + 0.4);
            const n = A.el(c, "div", "numero", null, "0");
            const st = { v: 0 };
            A.tl.to(st, { v: e.valor !== undefined ? e.valor : repo().estrelas, duration: 1.4, ease: "power3.out", onUpdate: () => (n.textContent = A.mil(Math.round(st.v))) }, e.t + 0.5);
            A.el(c, "div", "sub-num", null, "e crescendo");
          },
          lista(A, palco, e) {
            bandeirola(A, palco, "O QUE ELE FAZ", e.t);
            const c = cartao(A, palco, "recursos", e.t + 0.3);
            e.itens.forEach((txt, k) => { const l = A.el(c, "div", "lin", null, `<span class="bolinha"></span>${txt}`); cai(A, l, e.ts ? e.ts[k] : e.t + k * 0.4); });
          },
          terminal(A, palco, e) {
            bandeirola(A, palco, "RODA SOZINHO", e.t);
            const t0 = e.ts ? e.ts[0] : e.t;
            const c = cartao(A, palco, e.rotulo || "terminal", t0 + 0.3);
            const cmd = A.el(c, "div", "cmd", null, "<b>❯</b> ");
            const ls = [...e.comando].map((ch) => A.el(cmd, "span", "", { opacity: 0 }, ch === " " ? "&nbsp;" : ch));
            A.tl.to(ls, { opacity: 1, duration: 0.01, stagger: 0.05 }, t0 + 0.7);
            if (e.texto) { const s = A.el(c, "div", "saida", null, "✓ " + e.texto); cai(A, s, e.ts ? e.ts[1] : t0 + 1.4); }
          },
          icone_pixel(A, palco, e) {
            bandeirola(A, palco, e.rotulo || "", e.t);
            const c = cartao(A, palco, "status", e.t + 0.3);
            const la = A.el(c, "div", "linha-app");
            const lg = A.el(la, "div", "logo", { background: (COR_C[e.cor] || "#39c06a") + "22", width: "160px", height: "160px" }); lg.appendChild(A.svgIcone(e.icone, COR_C[e.cor] || "#39c06a", 100));
            A.el(la, "div", "", null, `<div class="tt">${e.rotulo || ""}</div><div class="st">confirmado</div>`);
          },
          preco_pixel(A, palco, e) {
            bandeirola(A, palco, "QUANTO CUSTA", e.t);
            const c = cartao(A, palco, "comparação", e.t + 0.3);
            const grid = A.el(c, "div", "preco-duas");
            [[e.esq, 0], [e.dir, 1]].forEach(([lado, i]) => {
              const card = A.el(grid, "div", "preco-card", null, `<b>${lado.titulo}</b><div class="pv">${lado.preco}</div><small>${lado.legenda || ""}</small>`);
              A.tl.fromTo(card, { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }, (e.ts ? e.ts[i] : e.t + i * 0.4));
            });
          },
          cta(A, palco, e, palavra) {
            bandeirola(A, palco, "COMENTA " + palavra, e.t);
            const c = cartao(A, palco, "comentários", e.t + 0.4);
            const com = A.el(c, "div", "com"); A.el(com, "div", "av");
            const tx = A.el(com, "div", "tx");
            const ls = [...palavra].map((ch) => A.el(tx, "span", "", { opacity: 0 }, ch));
            const env = A.el(com, "div", "enviar"); env.appendChild(A.svgIcone("send", "#17183a", 46));
            A.tl.to(ls, { opacity: 1, duration: 0.01, stagger: 0.12 }, e.t + 1);
            A.tl.fromTo(env, { scale: 1 }, { scale: 1.25, duration: 0.15, yoyo: true, repeat: 1 }, e.t + 1.2 + palavra.length * 0.12);
          },
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
