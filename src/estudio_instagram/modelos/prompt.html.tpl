<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Prompt pronto</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      :root {
        --laranja: #ff9d3c; --azul: #5fb4ff; --verde: #4ee06a; --roxo: #b48cff;
        --vermelho: #ff5c5c; --amarelo: #ffd84a; --branco: #f1efe8;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #08080a; }
      #root {
        position: relative; width: 100%; height: 100%; overflow: hidden;
        font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
        color: var(--branco);
      }
      #fundo {
        position: absolute; inset: 0;
        background: radial-gradient(ellipse 85% 55% at 50% 22%, #16161d 0%, #0a0a0d 55%, #050506 100%);
      }
      #grao {
        position: absolute; inset: -4%; width: 108%; height: 108%; opacity: 0.05; mix-blend-mode: overlay;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/></filter><rect width="100%25" height="100%25" filter="url(%23n)"/></svg>');
      }
      .cena { position: absolute; inset: 0; }
      .palco { position: absolute; inset: 0; transform-origin: 50% 40%; }
      .el { position: absolute; left: 0; width: 1080px; opacity: 0; }
      .centro { display: flex; justify-content: center; text-align: center; }
      .titulo {
        font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em;
        line-height: 1.08; white-space: pre-wrap; padding: 0 70px;
        text-shadow: 0 0 40px rgba(255,255,255,.18);
      }
      .titulo span { opacity: 1; }
      .emoji { font-size: 320px; filter: drop-shadow(0 25px 45px rgba(0,0,0,.7)); }
      .card {
        position: absolute; left: 70px; width: 940px; border-radius: 30px;
        background: linear-gradient(165deg, #1b1b22, #121217 55%, #0e0e12);
        border: 1px solid rgba(255,255,255,0.09);
        box-shadow: 0 50px 100px rgba(0,0,0,.65), inset 0 1px 0 rgba(255,255,255,.06);
        padding: 46px 48px 32px;
      }
      .card-expandir {
        position: absolute; top: 28px; right: 32px; width: 34px; height: 34px; opacity: .35;
      }
      .card-texto {
        font-size: 44px; line-height: 1.42; color: #e9e7e2; white-space: pre-wrap; padding-right: 50px;
      }
      .card-texto span { opacity: 1; }
      .card-barra { display: flex; align-items: center; justify-content: space-between; margin-top: 38px; padding-top: 28px; border-top: 1px solid rgba(255,255,255,.07); }
      .card-icones { display: flex; align-items: center; gap: 22px; }
      .card-icone-botao {
        width: 64px; height: 64px; border-radius: 999px; display: flex; align-items: center; justify-content: center;
        background: rgba(255,255,255,.06); color: rgba(255,255,255,.55);
      }
      .card-enviar {
        width: 68px; height: 68px; border-radius: 999px; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 10px 24px rgba(0,0,0,.4);
      }
      .pill-rotulo {
        position: absolute; top: -26px; left: 48px; display: inline-flex; align-items: center; gap: 10px;
        padding: 10px 26px; border-radius: 999px; font-size: 28px; font-weight: 700; letter-spacing: .02em;
        background: #0a0a0c; border: 1px solid rgba(255,255,255,.14);
      }
      #legendas { position: absolute; left: 0; top: 1700px; width: 1080px; height: 150px; }
      .bloco-legenda {
        position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
        padding: 0 70px; text-align: center; font-size: 62px; font-weight: 700; line-height: 1.05; opacity: 0;
        color: #ffffff; text-shadow: 0 4px 0 #000, 0 0 22px rgba(0,0,0,0.9);
      }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="grao" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
{{CENAS}}
      <div id="legendas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="3"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const D = window.DADOS;
      const tl = gsap.timeline({ paused: true });
      const SVG = "http://www.w3.org/2000/svg";
      const cor = (nome) => `var(--${nome || "branco"})`;

      function bloco(palco, y, classes = "") {
        const el = document.createElement("div");
        el.className = "el " + classes;
        el.style.top = y + "px";
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

      function digitar(t, inicio, porLetra = 0.016) {
        const letras = t.querySelectorAll("span");
        tl.set(t.parentElement, { opacity: 1 }, inicio);
        tl.fromTo(letras, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: porLetra, ease: "none" }, inicio);
        return inicio + letras.length * porLetra;
      }

      function svgIcone(nome, tamanho, corCss, espessura = 2) {
        const s = document.createElementNS(SVG, "svg");
        s.setAttribute("width", tamanho);
        s.setAttribute("height", tamanho);
        s.setAttribute("viewBox", "0 0 24 24");
        s.setAttribute("fill", "none");
        s.setAttribute("stroke", "currentColor");
        s.setAttribute("stroke-width", espessura);
        s.setAttribute("stroke-linecap", "round");
        s.setAttribute("stroke-linejoin", "round");
        s.style.color = corCss;
        s.innerHTML = D.icones[nome];
        return s;
      }

      const construtores = {
        cabecalho(palco, e, c) {
          const b = bloco(palco, e.y, "centro");
          const t = document.createElement("div");
          t.className = "titulo";
          t.style.fontSize = (e.tamanho || 92) + "px";
          t.style.color = cor(e.cor || c.cor);
          textoPorSpan(t, e.texto);
          b.appendChild(t);
          tl.fromTo(b, { opacity: 0, y: -14 }, { opacity: 1, y: 0, duration: 0.01 }, e.t);
          digitar(t, e.t, 0.022);
        },
        emoji(palco, e, c) {
          const b = bloco(palco, e.y, "centro");
          const em = document.createElement("div");
          em.className = "emoji";
          em.textContent = e.emoji;
          b.appendChild(em);
          tl.fromTo(b, { opacity: 0, scale: 0.55 }, { opacity: 1, scale: 1, duration: 0.55, ease: "back.out(2)" }, e.t);
          tl.to(em, { y: -16, duration: (e.duracaoPulso || 1.6), ease: "sine.inOut", yoyo: true, repeat: -1 }, e.t + 0.4);
        },
        card_prompt(palco, e, c) {
          const wrap = document.createElement("div");
          wrap.style.position = "absolute";
          wrap.style.left = "0";
          wrap.style.top = e.y + "px";
          wrap.style.width = "1080px";
          wrap.style.opacity = "0";
          const card = document.createElement("div");
          card.className = "card";
          card.style.borderColor = cor(e.cor || c.cor) + "40";
          wrap.appendChild(card);

          const pill = document.createElement("div");
          pill.className = "pill-rotulo";
          pill.style.color = cor(e.cor || c.cor);
          pill.textContent = e.rotulo || "PROMPT";
          card.appendChild(pill);

          card.appendChild(svgIcone("search", 30, "rgba(255,255,255,.3)"));
          card.lastChild.classList.add("card-expandir");

          const corpo = document.createElement("div");
          corpo.className = "card-texto";
          textoPorSpan(corpo, e.texto);
          card.appendChild(corpo);

          const barra = document.createElement("div");
          barra.className = "card-barra";
          const icones = document.createElement("div");
          icones.className = "card-icones";
          (e.icones_esquerda || ["palette", "sparkles", "message-circle"]).forEach((nome) => {
            const botao = document.createElement("div");
            botao.className = "card-icone-botao";
            botao.appendChild(svgIcone(nome, 32, "rgba(255,255,255,.6)"));
            icones.appendChild(botao);
          });
          barra.appendChild(icones);
          const enviar = document.createElement("div");
          enviar.className = "card-enviar";
          enviar.style.background = cor(e.cor || c.cor);
          enviar.appendChild(svgIcone(e.icone || "zap", 34, "#0a0a0c", 2.4));
          barra.appendChild(enviar);
          card.appendChild(barra);

          palco.appendChild(wrap);
          tl.fromTo(wrap, { opacity: 0, y: 60, scale: 0.94 }, { opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "back.out(1.4)" }, e.t);
          digitar(corpo, e.t + 0.3, e.velocidade || 0.011);
        },
      };

      document.fonts.ready.then(() => {
        D.cenas.forEach((c, i) => {
          const palco = document.getElementById("cena-" + c.id).firstElementChild;
          c.elementos.forEach((e) => construtores[e.tipo](palco, e, c));
          tl.fromTo(palco, { scale: 1.06 }, { scale: 1.12, duration: c.duracao, ease: "none" }, c.inicio);
          if (i < D.cenas.length - 1) {
            tl.to(palco, { opacity: 0, duration: 0.28, ease: "power2.in" }, c.inicio + c.duracao - 0.28);
          } else {
            tl.to(palco, { opacity: 0, duration: 0.5, ease: "power1.in" }, c.inicio + c.duracao - 0.5);
          }
        });
        const caixaLegenda = document.getElementById("legendas");
        D.legenda.forEach((b) => {
          const el = document.createElement("div");
          el.className = "bloco-legenda";
          el.textContent = b.texto;
          caixaLegenda.appendChild(el);
          tl.set(el, { opacity: 1 }, b.t);
          tl.set(el, { opacity: 0 }, b.fim);
        });
        window.__timelines["main"] = tl;
      });
    </script>
  </body>
</html>
