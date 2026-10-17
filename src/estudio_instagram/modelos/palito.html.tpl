<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Personagem de palito</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      @font-face {
        font-family: "Patrick Hand";
        src: url("assets/fonts/PatrickHand-Regular.ttf") format("truetype");
      }
      :root {
        --tinta: #1b1b1b; --laranja: #f07f12; --azul: #2d7de0; --verde: #1fa84a; --roxo: #7a4fe0;
        --vermelho: #e03a3a; --amarelo: #e6b800; --branco: #1b1b1b;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #f3eee2; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Patrick Hand", "Segoe UI", sans-serif; color: var(--tinta); }
      #fundo { position: absolute; inset: 0; background: radial-gradient(ellipse 100% 70% at 50% 35%, #f8f4ea 0%, #f3eee2 60%, #e9e2d0 100%); }
      #papel {
        position: absolute; inset: 0; opacity: .5;
        background-image: repeating-linear-gradient(0deg, transparent 0 59px, rgba(70,90,140,.16) 59px 61px);
      }
      .cena { position: absolute; inset: 0; }
      .palco { position: absolute; inset: 0; }
      .el { position: absolute; opacity: 0; }
      .titulo { font-size: 128px; line-height: 1.02; text-align: center; white-space: pre-wrap; }
      .titulo span { opacity: 1; }
      .balao {
        position: absolute; opacity: 0; background: #fffdf6; border: 8px solid var(--tinta);
        border-radius: 44px; padding: 26px 40px; font-size: 64px; line-height: 1.05; text-align: center;
        white-space: pre-wrap; box-shadow: 10px 12px 0 rgba(27,27,27,.9);
      }
      .balao span { opacity: 1; }
      .balao.caixa { border-radius: 22px; }
      .chip {
        position: absolute; left: 0; width: 1080px; display: flex; justify-content: center; opacity: 0;
      }
      .chip div {
        font-size: 62px; padding: 8px 40px; border: 7px solid var(--tinta); border-radius: 18px;
        background: #fffdf6; box-shadow: 8px 9px 0 rgba(27,27,27,.9);
      }
      .selo { position: absolute; left: 0; width: 1080px; display: flex; justify-content: center; opacity: 0; }
      .selo div {
        font-size: 78px; letter-spacing: .05em; padding: 12px 52px; color: var(--vermelho);
        border: 8px solid var(--vermelho); border-radius: 18px; background: rgba(224,58,58,.06);
      }
      .figura { position: absolute; opacity: 0; width: 640px; height: 896px; left: 220px; }
      #legendas { position: absolute; left: 0; top: 1700px; width: 1080px; height: 150px; }
      .bloco-legenda {
        position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
        text-align: center; font-size: 80px; line-height: 1; opacity: 0;
      }
      .bloco-legenda span { background: var(--tinta); color: #fff; padding: 8px 34px 12px; border-radius: 24px; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="papel" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
{{CENAS}}
      <div id="legendas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="3"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const D = window.DADOS;
      const tl = gsap.timeline({ paused: true });
      const SVG = "http://www.w3.org/2000/svg";
      const cor = (nome) => `var(--${nome || "tinta"})`;

      function bloco(palco, y) {
        const el = document.createElement("div");
        el.className = "el";
        el.style.top = y + "px"; el.style.left = "0"; el.style.width = "1080px";
        el.style.display = "flex"; el.style.justifyContent = "center";
        palco.appendChild(el);
        return el;
      }

      function textoPorSpan(pai, conteudo) {
        for (const ch of conteudo) {
          const s = document.createElement("span");
          s.textContent = ch;
          pai.appendChild(s);
        }
      }

      function digitar(t, inicio, porLetra = 0.025) {
        const letras = t.querySelectorAll("span");
        tl.set(t.parentElement, { opacity: 1 }, inicio);
        tl.fromTo(letras, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: porLetra, ease: "none" }, inicio);
      }

      function no(nome, atributos, pai) {
        const el = document.createElementNS(SVG, nome);
        Object.entries(atributos).forEach(([k, v]) => el.setAttribute(k, v));
        pai.appendChild(el);
        return el;
      }

      // pose: ângulo de cada braço (0 = pendurado; positivo = vai para a esquerda da tela), boca e olhos.
      const POSES = {
        aponta:         { bracoE: 16,  bracoD: -122, boca: "sorriso",  olhos: "ponto" },
        sobrecarregado: { bracoE: 152, bracoD: -152, boca: "ondulada", olhos: "grande", suor: true },
        alivio:         { bracoE: 112, bracoD: -112, boca: "sorrisao", olhos: "fechado" },
        acena:          { bracoE: 14,  bracoD: -132, boca: "sorrisao", olhos: "ponto", acena: true },
      };

      function desenharPersonagem(pose) {
        const svg = document.createElementNS(SVG, "svg");
        svg.setAttribute("viewBox", "0 0 400 560");
        svg.setAttribute("width", 640); svg.setAttribute("height", 896);
        svg.style.overflow = "visible";
        const traco = { stroke: "#1b1b1b", "stroke-width": 11, "stroke-linecap": "round", "stroke-linejoin": "round", fill: "none" };
        const corpo = no("g", {}, svg);
        no("path", { ...traco, d: "M200 147 L200 310" }, corpo);
        no("path", { ...traco, d: "M200 310 L155 440" }, corpo);
        no("path", { ...traco, d: "M200 310 L245 440" }, corpo);
        const bracos = [];
        [["E", pose.bracoE], ["D", pose.bracoD]].forEach(([lado]) => {
          const g = no("g", {}, corpo);
          no("path", { ...traco, d: "M200 185 L200 295" }, g);
          no("circle", { cx: 200, cy: 300, r: 10, fill: "#1b1b1b" }, g);
          bracos.push(g);
        });
        const cabeca = no("g", {}, corpo);
        no("path", { ...traco, "stroke-width": 8, d: "M200 44 L200 14" }, cabeca);
        no("circle", { cx: 200, cy: 10, r: 11, fill: "#f07f12", stroke: "#1b1b1b", "stroke-width": 6 }, cabeca);
        no("circle", { cx: 200, cy: 95, r: 52, fill: "#fffdf6", stroke: "#1b1b1b", "stroke-width": 11 }, cabeca);
        if (pose.olhos === "ponto") {
          no("circle", { cx: 182, cy: 88, r: 7, fill: "#1b1b1b" }, cabeca);
          no("circle", { cx: 218, cy: 88, r: 7, fill: "#1b1b1b" }, cabeca);
        } else if (pose.olhos === "grande") {
          [182, 218].forEach((x) => {
            no("circle", { cx: x, cy: 88, r: 13, fill: "#fff", stroke: "#1b1b1b", "stroke-width": 5 }, cabeca);
            no("circle", { cx: x + 2, cy: 90, r: 4, fill: "#1b1b1b" }, cabeca);
          });
        } else {
          no("path", { ...traco, "stroke-width": 6, d: "M172 92 Q182 80 192 92" }, cabeca);
          no("path", { ...traco, "stroke-width": 6, d: "M208 92 Q218 80 228 92" }, cabeca);
        }
        const bocas = {
          sorriso: "M176 112 Q200 132 224 112",
          sorrisao: "M170 108 Q200 144 230 108 Z",
          ondulada: "M176 120 Q188 106 200 120 T224 120",
        };
        no("path", { ...traco, "stroke-width": 7, d: bocas[pose.boca], fill: pose.boca === "sorrisao" ? "#fff" : "none" }, cabeca);
        let suor = null;
        if (pose.suor) suor = no("path", { d: "M262 70 Q272 92 262 100 Q252 92 262 70 Z", fill: "#2d7de0", stroke: "#1b1b1b", "stroke-width": 4 }, cabeca);
        return { svg, bracos, cabeca, suor, corpo };
      }

      const construtores = {
        cabecalho(palco, e, c) {
          const b = bloco(palco, e.y);
          const t = document.createElement("div");
          t.className = "titulo";
          t.style.fontSize = (e.tamanho || 128) + "px";
          t.style.color = cor(e.cor || c.cor);
          textoPorSpan(t, e.texto);
          b.appendChild(t);
          tl.fromTo(b, { opacity: 0, rotation: -1.5 }, { opacity: 1, rotation: 0, duration: 0.01 }, e.t);
          digitar(t, e.t, 0.032);
        },
        selo(palco, e, c) {
          const b = document.createElement("div");
          b.className = "selo"; b.style.top = e.y + "px";
          const d = document.createElement("div");
          d.textContent = e.texto;
          b.appendChild(d);
          palco.appendChild(b);
          tl.fromTo(b, { opacity: 0, scale: 1.8, rotation: -8 }, { opacity: 1, scale: 1, rotation: -3, duration: 0.3, ease: "back.out(2.2)" }, e.t);
        },
        personagem(palco, e, c) {
          const pose = POSES[e.pose];
          const { svg, bracos, cabeca, suor, corpo } = desenharPersonagem(pose);
          const envolta = document.createElement("div");
          envolta.className = "figura";
          envolta.style.top = e.y + "px";
          envolta.appendChild(svg);
          palco.appendChild(envolta);
          tl.fromTo(envolta, { opacity: 0, y: 90, scale: 0.7 }, { opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "back.out(1.9)" }, e.t);
          bracos.forEach((g, i) => {
            const alvo = i === 0 ? pose.bracoE : pose.bracoD;
            tl.set(g, { svgOrigin: "200 185", rotation: 0 }, 0);
            tl.to(g, { rotation: alvo, duration: 0.5, ease: "back.out(1.6)" }, e.t + 0.25);
          });
          if (pose.acena) {
            tl.to(bracos[1], { rotation: pose.bracoD + 28, duration: 0.28, ease: "sine.inOut", yoyo: true, repeat: 9 }, e.t + 0.8);
          }
          if (suor) tl.fromTo(suor, { y: -6, opacity: 0 }, { y: 16, opacity: 1, duration: 0.8, ease: "power1.in", repeat: 3 }, e.t + 0.5);
          tl.set(cabeca, { svgOrigin: "200 147" }, 0);
          tl.to(cabeca, { rotation: pose.suor ? 4 : 2.5, duration: pose.suor ? 0.16 : 0.9, ease: "sine.inOut", yoyo: true, repeat: pose.suor ? 11 : 3 }, e.t + 0.7);
        },
        balao(palco, e, c) {
          const b = document.createElement("div");
          b.className = "balao" + (e.estilo === "caixa" ? " caixa" : "");
          b.style.left = e.x + "px"; b.style.top = e.y + "px"; b.style.width = (e.largura || 420) + "px";
          b.style.color = cor(e.cor);
          if (e.cor) b.style.borderColor = cor(e.cor);
          const t = document.createElement("div");
          textoPorSpan(t, e.texto);
          b.appendChild(t);
          palco.appendChild(b);
          tl.fromTo(b, { opacity: 0, scale: 0.6, rotation: e.rot ? e.rot - 4 : -4 }, { opacity: 1, scale: 1, rotation: e.rot || 0, duration: 0.4, ease: "back.out(2)" }, e.t);
          digitar(t, e.t + 0.15, 0.03);
        },
        // Etiquetas que "caem" e se empilham — o contexto enchendo.
        chips(palco, e, c) {
          e.itens.forEach((texto, i) => {
            const chip = document.createElement("div");
            chip.className = "chip";
            chip.style.top = (e.y - i * 130) + "px";
            const d = document.createElement("div");
            d.textContent = texto;
            d.style.transform = `rotate(${[-3, 2.5, -2][i % 3]}deg)`;
            chip.appendChild(d);
            palco.appendChild(chip);
            tl.fromTo(chip, { opacity: 0, y: -520 }, { opacity: 1, y: 0, duration: 0.55, ease: "bounce.out" }, e.ts[i]);
          });
        },
      };

      document.fonts.ready.then(() => {
        D.cenas.forEach((c, i) => {
          const palco = document.getElementById("cena-" + c.id).firstElementChild;
          c.elementos.forEach((e) => construtores[e.tipo](palco, e, c));
          tl.fromTo(palco, { scale: 1.0 }, { scale: 1.035, duration: c.duracao, ease: "none" }, c.inicio);
          if (i < D.cenas.length - 1) {
            tl.to(palco, { opacity: 0, duration: 0.22, ease: "power2.in" }, c.inicio + c.duracao - 0.22);
          } else {
            tl.to(palco, { opacity: 0, duration: 0.5, ease: "power1.in" }, c.inicio + c.duracao - 0.5);
          }
        });
        const caixaLegenda = document.getElementById("legendas");
        D.legenda.forEach((b) => {
          const el = document.createElement("div");
          el.className = "bloco-legenda";
          const s = document.createElement("span");
          s.textContent = b.texto;
          el.appendChild(s);
          caixaLegenda.appendChild(el);
          tl.set(el, { opacity: 1 }, b.t);
          tl.set(el, { opacity: 0 }, b.fim);
        });
        window.__timelines["main"] = tl;
      });
    </script>
  </body>
</html>
