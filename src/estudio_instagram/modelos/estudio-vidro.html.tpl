<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio vidro</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      /* Identidade inspirada no @igao.ia: preto absoluto, frase curta no topo com a palavra-chave em itálico
         serifado dentro de uma caixinha, e o resto é interface de app de verdade (cards de vidro, chips,
         linha do tempo, listas) montando peça por peça. */
      @font-face { font-family: "Grot"; src: url("assets/fonts/SpaceGrotesk.ttf"); font-weight: 300 700; }
      @font-face { font-family: "Serif"; src: url("assets/fonts/InstrumentSerif-Italic.ttf"); }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #000; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Grot", sans-serif; color: #e9e9ee; }
      #bolhas { position: absolute; inset: 0; }
      .bolha { position: absolute; border-radius: 50%; filter: blur(120px); opacity: .32; }
      .cena { position: absolute; inset: 0; opacity: 0; }
      .palco { position: absolute; left: 40px; width: 760px; top: 200px; height: 950px; zoom: 1.32; display: flex; flex-direction: column; align-items: center; gap: 24px; }
      .palco .vidro { width: 760px; }
      .frase { font-size: 64px; font-weight: 500; letter-spacing: -1.5px; color: #cfcfd6; text-align: center; margin-bottom: 30px; }
      .frase .caixa { font-family: "Serif"; font-size: 76px; color: #fff; border: 2px solid #6d7cff; border-radius: 10px; padding: 0 14px; background: rgba(109,124,255,.12); }
      .vidro { width: 960px; border-radius: 28px; background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.03)); border: 1.5px solid rgba(255,255,255,.12); box-shadow: 0 30px 80px rgba(0,0,0,.6), inset 0 1px 0 rgba(255,255,255,.12); overflow: hidden; }
      .vidro .topo { display: flex; align-items: center; gap: 12px; padding: 18px 24px; border-bottom: 1px solid rgba(255,255,255,.08); font-family: "Mono"; font-size: 24px; color: #8b8b96; }
      .vidro .topo i { width: 14px; height: 14px; border-radius: 50%; background: #3a3a44; display: block; }
      .vidro .corpo { padding: 30px; }
      .linha-app { display: flex; align-items: center; gap: 22px; }
      .logo { width: 110px; height: 110px; border-radius: 26px; display: grid; place-items: center; flex: none; }
      .tt { font-size: 52px; font-weight: 700; letter-spacing: -1px; } .st { font-size: 28px; color: #8b8b96; margin-top: 4px; }
      .chips { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
      .chip { border-radius: 16px; border: 1.5px solid rgba(78,224,140,.45); background: rgba(78,224,140,.07); padding: 18px; font-family: "Mono"; font-size: 26px; color: #9ff0c0; display: flex; flex-direction: column; gap: 10px; }
      .chip small { color: #8b8b96; font-size: 20px; }
      .lin { display: flex; align-items: center; gap: 20px; padding: 22px 26px; border-radius: 18px; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.07); font-size: 40px; font-weight: 600; margin-bottom: 14px; }
      .lin .bolinha { width: 22px; height: 22px; border-radius: 50%; background: #4ee08c; box-shadow: 0 0 16px #4ee08c; flex: none; }
      .lin .tag { margin-left: auto; font-family: "Mono"; font-size: 22px; padding: 6px 12px; border-radius: 8px; background: rgba(255,90,90,.15); color: #ff7b7b; }
      .trilha { position: relative; height: 140px; margin-top: 20px; border-radius: 14px; background: rgba(255,255,255,.03); overflow: hidden; }
      .clipe { position: absolute; top: 24px; height: 40px; border-radius: 8px; }
      .onda { position: absolute; left: 0; right: 0; bottom: 14px; height: 50px; display: flex; align-items: center; gap: 4px; padding: 0 10px; }
      .onda span { flex: 1; background: #ff5a5a; border-radius: 3px; }
      .agulha { position: absolute; top: 0; bottom: 0; width: 4px; background: #fff; box-shadow: 0 0 12px #fff; }
      .cmd { font-family: "Mono"; font-weight: 700; font-size: 50px; color: #fff; word-break: break-all; } .cmd b { color: #6d7cff; }
      .saida { font-family: "Mono"; font-size: 28px; color: #4ee08c; margin-top: 20px; }
      .numero { font-size: 220px; font-weight: 700; letter-spacing: -10px; line-height: 1; text-align: center; }
      .barra-g { display: flex; align-items: flex-end; gap: 14px; height: 260px; margin-top: 20px; }
      .barra-g span { flex: 1; border-radius: 10px 10px 4px 4px; background: linear-gradient(180deg, #6d7cff, rgba(109,124,255,.15)); transform-origin: bottom; }
      .com { display: flex; align-items: center; gap: 20px; }
      .com .av { width: 90px; height: 90px; border-radius: 50%; background: linear-gradient(135deg, #feda75, #fa7e1e, #d62976, #962fbf); flex: none; }
      .com .tx { font-size: 96px; font-weight: 700; letter-spacing: -2px; }
      .enviar { margin-left: auto; width: 90px; height: 90px; border-radius: 50%; background: #6d7cff; display: grid; place-items: center; }
      #legenda { position: absolute; left: 60px; right: 60px; top: 1560px; height: 170px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 14px; opacity: 0; }
      .w { font-size: 56px; font-weight: 600; color: #e9e9ee; display: inline-block; letter-spacing: -1px; }
      .w.dest { font-family: "Serif"; font-weight: 400; font-size: 66px; color: #fff; border: 2px solid #6d7cff; border-radius: 8px; padding: 0 10px; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="bolhas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0">
        <div class="bolha" id="b1" style="left:-200px;top:300px;width:700px;height:700px;background:#6d7cff"></div>
        <div class="bolha" id="b2" style="left:600px;top:900px;width:600px;height:600px;background:#ff5a5a"></div>
        <div class="bolha" id="b3" style="left:200px;top:1300px;width:500px;height:500px;background:#4ee08c"></div>
      </div>
{{CENAS}}
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <audio id="trilha" src="assets/musica/trilha-pixel.mp3" data-start="0" data-duration="{{DURACAO}}" data-track-index="10" data-volume="0.12"></audio>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const COR_V = { laranja: "#ff9d4d", azul: "#6d7cff", verde: "#4ee08c", roxo: "#b48cff", vermelho: "#ff5a5a", amarelo: "#ffd84a", branco: "#e9e9ee", rosa: "#ff7ad9" };
      const repo = () => Object.values(window.DADOS.repos || {})[0] || { repo: "", estrelas: 0 };
      // frase do topo: palavra a palavra, com a palavra-chave em itálico dentro da caixa
      function frase(A, palco, antes, chave, t) {
        const f = A.el(palco, "div", "frase");
        const ps = antes.split(" ").map((p) => A.el(f, "span", "", { display: "inline-block" }, p + "&nbsp;"));
        const c = A.el(f, "span", "caixa", { display: "inline-block" }, chave);
        A.tl.fromTo(ps, { opacity: 0, y: 20, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, stagger: 0.08 }, t);
        A.tl.fromTo(c, { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2.5)" }, t + ps.length * 0.08);
      }
      function vidro(A, pai, titulo, t) {
        const v = A.el(pai, "div", "vidro");
        A.el(v, "div", "topo", null, `<i></i><i></i><i></i><span style="margin-left:8px">${titulo}</span>`);
        A.tl.fromTo(v, { opacity: 0, y: 80, scale: 0.94, filter: "blur(10px)" }, { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }, t);
        return A.el(v, "div", "corpo");
      }
      const cai = (A, el, t) => A.tl.fromTo(el, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }, t);

      window.TEMA = {
        cores: COR_V, acento: "azul", traco: 1.8, escalaTitulo: 1, larguraLetra: 0.5,
        entrar(A, alvo, t) { cai(A, alvo, t); },
        palavraLegenda(A, s, t) { A.tl.fromTo(s, { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.2 }, t); },
        transicao(A, palco, c) {
          A.tl.fromTo(palco, { opacity: 0 }, { opacity: 1, duration: 0.25 }, c.inicio);
          A.tl.to(palco, { opacity: 0, y: -40, filter: "blur(12px)", duration: 0.2 }, c.inicio + c.duracao - 0.2);
        },
        fundo(A, dur) {
          A.tl.fromTo("#b1", { x: 0, y: 0 }, { x: 300, y: 200, duration: dur, ease: "sine.inOut" }, 0);
          A.tl.fromTo("#b2", { x: 0, y: 0 }, { x: -400, y: -300, duration: dur, ease: "sine.inOut" }, 0);
          A.tl.fromTo("#b3", { x: 0 }, { x: 300, duration: dur, ease: "sine.inOut" }, 0);
        },
        visuais: {
          titulo_pixel(A, palco, e) {
            const ls = e.linhas.map((l) => l.texto.toLowerCase());
            frase(A, palco, ls.slice(0, -1).join(" "), ls[ls.length - 1], e.t);
            const c = vidro(A, palco, "github.com/" + repo().repo, e.t + 0.5);
            const la = A.el(c, "div", "linha-app");
            const lg = A.el(la, "div", "logo", { background: "#6d7cff22", border: "1.5px solid #6d7cff66" }); lg.appendChild(A.svgIcone("bot", "#6d7cff", 70));
            A.el(la, "div", "", null, `<div class="tt">${repo().repo.split("/")[1]}</div><div class="st">${(repo().descricao || "").slice(0, 60)}…</div>`);
            const tr = A.el(c, "div", "trilha");
            const onda = A.el(tr, "div", "onda");
            const barras = Array.from({ length: 48 }, (_, k) => A.el(onda, "span", "", { height: 10 + ((k * 37) % 40) + "px" }));
            const ag = A.el(tr, "div", "agulha");
            A.tl.fromTo(barras, { scaleY: 0 }, { scaleY: 1, duration: 0.3, stagger: 0.015 }, e.t + 0.9);
            A.tl.fromTo(ag, { x: 0 }, { x: 880, duration: 3, ease: "none" }, e.t + 0.9);
          },
          contador(A, palco, e) {
            frase(A, palco, "a comunidade", "aprovou", e.t);
            const c = vidro(A, palco, "insights · stars", e.t + 0.4);
            const n = A.el(c, "div", "numero", null, "0");
            const st = { v: 0 };
            A.tl.to(st, { v: repo().estrelas, duration: 1.4, ease: "power3.out", onUpdate: () => (n.textContent = A.mil(Math.round(st.v))) }, e.t + 0.5);
            const g = A.el(c, "div", "barra-g");
            const bs = Array.from({ length: 12 }, (_, k) => A.el(g, "span", "", { height: 20 + k * k * 1.6 + "px" }));
            A.tl.fromTo(bs, { scaleY: 0 }, { scaleY: 1, duration: 0.5, stagger: 0.06, ease: "back.out(1.6)" }, e.t + 0.6);
          },
          cadeia(A, palco, e) {
            frase(A, palco, "o que ele", "faz", e.t);
            const c = vidro(A, palco, "pipeline", e.t + 0.3);
            const chips = A.el(c, "div", "chips");
            e.nos.forEach((n, k) => {
              const ch = A.el(chips, "div", "chip", { borderColor: (COR_V[n.cor] || "#4ee08c") + "88", background: (COR_V[n.cor] || "#4ee08c") + "12", color: COR_V[n.cor] || "#9ff0c0" });
              ch.appendChild(A.svgIcone(n.icone, COR_V[n.cor] || "#4ee08c", 56));
              A.el(ch, "div", "", null, `/${n.rotulo.toLowerCase().replace(/ /g, "-")}`); A.el(ch, "small", "", null, "ativo");
              A.tl.fromTo(ch, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2.5)" }, e.ts ? e.ts[k] : e.t + k * 0.4);
            });
          },
          lista(A, palco, e) {
            frase(A, palco, "tudo isso", "incluso", e.t);
            const c = vidro(A, palco, "recursos", e.t + 0.3);
            e.itens.forEach((txt, k) => { const l = A.el(c, "div", "lin", null, `<span class="bolinha"></span>${txt}<span class="tag">local</span>`); cai(A, l, e.ts ? e.ts[k] : e.t + k * 0.4); });
          },
          terminal(A, palco, e) {
            frase(A, palco, "pra rodar é", "simples", e.t);
            const t0 = e.ts ? e.ts[0] : e.t;
            const c = vidro(A, palco, e.rotulo || "terminal", t0 + 0.3);
            const cmd = A.el(c, "div", "cmd", null, "<b>❯</b> ");
            const ls = [...e.comando].map((ch) => A.el(cmd, "span", "", { opacity: 0 }, ch === " " ? "&nbsp;" : ch));
            A.tl.to(ls, { opacity: 1, duration: 0.01, stagger: 0.05 }, t0 + 0.7);
            if (e.texto) { const s = A.el(c, "div", "saida", null, "✓ " + e.texto); cai(A, s, e.ts ? e.ts[1] : t0 + 1.4); }
          },
          icone_pixel(A, palco, e) {
            const ps = (e.rotulo || "").toLowerCase().split(" ");
            frase(A, palco, ps.slice(0, -1).join(" "), ps[ps.length - 1], e.t);
            const c = vidro(A, palco, "status", e.t + 0.3);
            const la = A.el(c, "div", "linha-app");
            const lg = A.el(la, "div", "logo", { background: (COR_V[e.cor] || "#4ee08c") + "22", width: "160px", height: "160px" }); lg.appendChild(A.svgIcone(e.icone, COR_V[e.cor] || "#4ee08c", 100));
            A.el(la, "div", "", null, `<div class="tt">${e.rotulo || ""}</div><div class="st">verificado agora</div>`);
            [["sem chave de API", "#4ee08c"], ["sem assinatura", "#4ee08c"], ["seus dados ficam no PC", "#6d7cff"]].forEach(([txt, cor], k) => {
              const l = A.el(c, "div", "lin", { marginTop: k ? "0" : "26px" }, `<span class="bolinha" style="background:${cor};box-shadow:0 0 16px ${cor}"></span>${txt}`); cai(A, l, e.t + 0.8 + k * 0.3);
            });
          },
          cta(A, palco, e, palavra) {
            frase(A, palco, "quer o link?", "comenta", e.t);
            const c = vidro(A, palco, "comentários", e.t + 0.4);
            const com = A.el(c, "div", "com"); A.el(com, "div", "av");
            const tx = A.el(com, "div", "tx");
            const ls = [...palavra].map((ch) => A.el(tx, "span", "", { opacity: 0 }, ch));
            const env = A.el(com, "div", "enviar"); env.appendChild(A.svgIcone("send", "#fff", 46));
            A.tl.to(ls, { opacity: 1, duration: 0.01, stagger: 0.12 }, e.t + 1);
            A.tl.fromTo(env, { scale: 1 }, { scale: 1.25, duration: 0.15, yoyo: true, repeat: 1 }, e.t + 1.2 + palavra.length * 0.12);
          },
        },
      };
    </script>
    <script src="assets/vendor/estudio-motor.js"></script>
  </body>
</html>
