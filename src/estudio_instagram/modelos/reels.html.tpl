<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Rabisco</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/vendor/rough.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      @font-face {
        font-family: "Patrick Hand";
        src: url("assets/fonts/PatrickHand-Regular.ttf") format("truetype");
      }
      :root {
        --laranja: #ff9d3c;
        --azul: #5fb4ff;
        --verde: #4ee06a;
        --roxo: #b48cff;
        --vermelho: #ff5c5c;
        --amarelo: #ffd84a;
        --branco: #f1efe8;
        --tinta-fraca: #8a8780;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #060607; }
      #root {
        position: relative;
        width: 100%;
        height: 100%;
        overflow: hidden;
        font-family: "Patrick Hand", cursive;
        color: var(--branco);
      }
      #fundo {
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse 70% 55% at 50% 45%, #17181c 0%, #0b0b0d 55%, #040405 100%);
      }
      .cena { position: absolute; inset: 0; }
      .palco { position: absolute; inset: 0; transform-origin: 50% 45%; }
      .el { position: absolute; left: 0; width: 1080px; }
      .centro { display: flex; justify-content: center; text-align: center; }
      .txt { white-space: pre-wrap; line-height: 1.12; text-shadow: 0 0 18px currentColor; }
      .txt span { opacity: 1; }
      svg.risco { position: absolute; overflow: visible; filter: drop-shadow(0 0 7px currentColor); }
      svg.risco path, svg.risco rect, svg.risco circle, svg.risco line, svg.risco polyline, svg.risco polygon, svg.risco ellipse {
        stroke-dasharray: 1.02;
        stroke-dashoffset: 1.02;
      }
      .preenche { position: absolute; overflow: hidden; }
      #legendas { position: absolute; left: 0; top: 1610px; width: 1080px; height: 160px; }
      .bloco-legenda {
        position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
        padding: 0 70px; text-align: center; font-size: 74px; line-height: 1.05; opacity: 0;
        color: #ffffff; text-shadow: 0 4px 0 #000, 0 0 22px rgba(0,0,0,0.9);
      }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
{{CENAS}}
      <div id="legendas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="2"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const D = window.DADOS;
      const tl = gsap.timeline({ paused: true });
      const SVG = "http://www.w3.org/2000/svg";
      let semente = 7;

      const cor = (nome) => `var(--${nome || "branco"})`;

      function bloco(palco, y, classes = "") {
        const el = document.createElement("div");
        el.className = "el " + classes;
        el.style.top = y + "px";
        palco.appendChild(el);
        return el;
      }

      function texto(pai, conteudo, tamanho, corNome, extra = {}) {
        const t = document.createElement("div");
        t.className = "txt";
        t.style.fontSize = tamanho + "px";
        t.style.color = cor(corNome);
        Object.assign(t.style, extra);
        for (const ch of conteudo) {
          const s = document.createElement("span");
          s.textContent = ch;
          t.appendChild(s);
        }
        pai.appendChild(t);
        return t;
      }

      function digitar(t, inicio, porLetra = 0.032) {
        const letras = t.querySelectorAll("span");
        tl.fromTo(letras, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: porLetra, ease: "none" }, inicio);
        return inicio + letras.length * porLetra;
      }

      function tela(pai, x, y, w, h, corNome) {
        const s = document.createElementNS(SVG, "svg");
        s.setAttribute("class", "risco");
        s.setAttribute("width", w);
        s.setAttribute("height", h);
        s.setAttribute("viewBox", `0 0 ${w} ${h}`);
        s.style.left = x + "px";
        s.style.top = y + "px";
        s.style.color = cor(corNome);
        pai.appendChild(s);
        return s;
      }

      function retanguloArredondado(x, y, w, h, r) {
        return `M${x + r},${y} L${x + w - r},${y} Q${x + w},${y} ${x + w},${y + r} L${x + w},${y + h - r} Q${x + w},${y + h} ${x + w - r},${y + h} L${x + r},${y + h} Q${x},${y + h} ${x},${y + h - r} L${x},${y + r} Q${x},${y} ${x + r},${y} Z`;
      }

      function rabisco(s, forma, opcoes = {}) {
        const rc = rough.svg(s);
        const base = { stroke: "currentColor", strokeWidth: 4, roughness: 1.3, bowing: 1.2, seed: semente++, ...opcoes };
        let no;
        if (forma.tipo === "caixa") no = rc.path(retanguloArredondado(forma.x, forma.y, forma.w, forma.h, forma.r ?? 26), base);
        if (forma.tipo === "linha") no = rc.line(forma.x1, forma.y1, forma.x2, forma.y2, base);
        if (forma.tipo === "seta") {
          no = rc.line(forma.x1, forma.y, forma.x2, forma.y, base);
          const ponta = rc.linearPath([[forma.x2 - 30, forma.y - 24], [forma.x2, forma.y], [forma.x2 - 30, forma.y + 24]], base);
          s.appendChild(no);
          s.appendChild(ponta);
          return [...no.querySelectorAll("path"), ...ponta.querySelectorAll("path")];
        }
        if (forma.tipo === "retangulo") no = rc.rectangle(forma.x, forma.y, forma.w, forma.h, base);
        s.appendChild(no);
        return [...no.querySelectorAll("path")];
      }

      function icone(s, nome, x, y, tamanho, espessura = 1.7) {
        const g = document.createElementNS(SVG, "g");
        g.innerHTML = D.icones[nome];
        const escala = tamanho / 24;
        g.setAttribute("transform", `translate(${x} ${y}) scale(${escala})`);
        g.setAttribute("fill", "none");
        g.setAttribute("stroke", "currentColor");
        g.setAttribute("stroke-width", espessura);
        g.setAttribute("stroke-linecap", "round");
        g.setAttribute("stroke-linejoin", "round");
        s.appendChild(g);
        return [...g.querySelectorAll("path, rect, circle, line, polyline, polygon, ellipse")];
      }

      function tracar(formas, inicio, duracao = 0.55) {
        formas.forEach((f) => f.setAttribute("pathLength", "1"));
        const passo = formas.length > 1 ? Math.min(0.08, duracao / formas.length) : 0;
        tl.to(formas, { strokeDashoffset: 0, duration: duracao, stagger: passo, ease: "power1.inOut" }, inicio);
        return inicio + duracao + passo * (formas.length - 1);
      }

      function medir(conteudo, tamanho) {
        const sonda = document.createElement("span");
        sonda.style.cssText = `position:absolute;visibility:hidden;white-space:pre;font-family:'Patrick Hand';font-size:${tamanho}px`;
        sonda.textContent = conteudo;
        document.body.appendChild(sonda);
        const w = sonda.offsetWidth;
        sonda.remove();
        return w;
      }

      function caixaComIcone(palco, x, y, tam, nomeIcone, corNome, t) {
        const s = tela(palco, x, y, tam, tam, corNome);
        const fim = tracar(rabisco(s, { tipo: "caixa", x: 0, y: 0, w: tam, h: tam }), t, 0.5);
        const lado = tam * 0.56;
        tracar(icone(s, nomeIcone, (tam - lado) / 2, (tam - lado) / 2, lado), fim - 0.15, 0.6);
      }

      const construtores = {
        numero(palco, e, c) {
          const b = bloco(palco, e.y - 170, "centro");
          const t = texto(b, e.texto, 330, e.cor || c.cor, { lineHeight: "1" });
          const fim = digitar(t, e.t, 0.09);
          const s = tela(palco, 300, e.y + 150, 480, 40, e.cor || c.cor);
          tracar(rabisco(s, { tipo: "linha", x1: 0, y1: 20, x2: 480, y2: 14 }, { strokeWidth: 6 }), fim, 0.4);
        },
        texto(palco, e, c) {
          const b = bloco(palco, e.y, "centro");
          b.style.padding = "0 80px";
          digitar(texto(b, e.texto, e.grande ? 104 : 72, e.cor), e.t);
        },
        icone(palco, e, c) {
          const tam = e.tamanho || 220;
          caixaComIcone(palco, (1080 - tam) / 2, e.y, tam, e.icone, e.cor || c.cor, e.t);
        },
        etiqueta(palco, e, c) {
          const tamFonte = 60;
          const w = medir(e.texto, tamFonte) + 100;
          const h = 110;
          const x = (1080 - w) / 2;
          const s = tela(palco, x, e.y, w, h, e.cor || c.cor);
          const fim = tracar(rabisco(s, { tipo: "caixa", x: 0, y: 0, w, h, r: 50 }), e.t, 0.45);
          const b = bloco(palco, e.y + 18, "centro");
          digitar(texto(b, e.texto, tamFonte, e.cor || c.cor), fim - 0.2);
        },
        cabecalho(palco, e, c) {
          const b = bloco(palco, 300, "centro");
          const fim = digitar(texto(b, e.texto, 84, c.cor), e.t);
          const w = Math.min(860, medir(e.texto, 84) + 40);
          const s = tela(palco, (1080 - w) / 2, 410, w, 30, c.cor);
          tracar(rabisco(s, { tipo: "linha", x1: 0, y1: 16, x2: w, y2: 10 }, { strokeWidth: 4 }), fim, 0.35);
        },
        lista(palco, e, c) {
          e.itens.forEach((item, i) => {
            const y = e.y + i * 130;
            const s = tela(palco, 200, y, 90, 90, c.cor);
            const fim = tracar(rabisco(s, { tipo: "caixa", x: 0, y: 0, w: 80, h: 80, r: 18 }), e.ts[i], 0.35);
            tracar(icone(s, "check", 14, 14, 52, 2.4), fim - 0.1, 0.3);
            const b = bloco(palco, y + 4);
            b.style.left = "320px";
            b.style.width = "700px";
            digitar(texto(b, item, 66), fim);
          });
        },
        fluxo(palco, e, c) {
          const lados = [[90, e.esquerda, e.ts[0]], [630, e.direita, e.ts[1]]];
          lados.forEach(([x, lado, t]) => {
            caixaComIcone(palco, x, e.y, 360, lado.icone, lado.cor, t);
            const b = bloco(palco, e.y + 390);
            b.style.left = x - 40 + "px";
            b.style.width = "440px";
            b.classList.add("centro");
            digitar(texto(b, lado.texto, 60, lado.cor), t + 0.6);
          });
          const s = tela(palco, 470, e.y + 150, 160, 60, "branco");
          tracar(rabisco(s, { tipo: "seta", x1: 10, x2: 150, y: 30 }), e.ts[0] + 0.9, 0.45);
        },
        cartao(palco, e, c) {
          const s = tela(palco, 90, e.y, 900, 340, e.cor);
          const fim = tracar(rabisco(s, { tipo: "caixa", x: 0, y: 0, w: 900, h: 340 }), e.t, 0.55);
          caixaComIcone(palco, 130, e.y + 70, 200, e.icone, e.cor, fim - 0.2);
          const n = bloco(palco, e.y + 30);
          n.style.left = "380px";
          n.style.width = "580px";
          const tamNumero = Math.min(150, Math.floor(150 * 560 / medir(e.numero, 150)));
          const fimNumero = digitar(texto(n, e.numero, tamNumero, e.cor, { lineHeight: "1" }), fim, 0.08);
          const t = bloco(palco, e.y + 195);
          t.style.left = "380px";
          t.style.width = "580px";
          digitar(texto(t, e.texto, 52, "branco"), fimNumero, 0.025);
        },
        barra(palco, e, c) {
          const s = tela(palco, 90, e.y, 100, 100, e.cor);
          tracar(icone(s, e.icone, 0, 0, 90, 1.8), e.t, 0.5);
          const r = bloco(palco, e.y + 10);
          r.style.left = "210px";
          r.style.width = "500px";
          digitar(texto(r, e.rotulo, 70), e.t + 0.1);
          const v = bloco(palco, e.y - 10);
          v.style.left = "640px";
          v.style.width = "350px";
          v.style.textAlign = "right";
          digitar(texto(v, e.texto, 96, e.cor), e.t + 0.9, 0.06);
          const w = 900;
          const contorno = tela(palco, 90, e.y + 130, w, 110, e.cor);
          tracar(rabisco(contorno, { tipo: "caixa", x: 0, y: 0, w, h: 110, r: 16 }), e.t + 0.2, 0.5);
          const largura = Math.round((w - 24) * (e.valor / e.max));
          const janela = document.createElement("div");
          janela.className = "preenche";
          Object.assign(janela.style, { left: "102px", top: e.y + 142 + "px", width: largura + "px", height: "86px" });
          palco.appendChild(janela);
          const sFill = tela(janela, 0, 0, largura, 86, e.cor);
          const hach = rabisco(sFill, { tipo: "retangulo", x: 0, y: 0, w: largura, h: 86 }, { fill: "currentColor", fillStyle: "hachure", hachureGap: 14, fillWeight: 3, strokeWidth: 0.01 });
          hach.forEach((p) => p.setAttribute("pathLength", "1"));
          tl.set(hach, { strokeDashoffset: 0 }, 0);
          tl.fromTo(janela, { width: 0 }, { width: largura, duration: 1.3, ease: "power2.out" }, e.t + 0.6);
        },
        comparacao(palco, e, c) {
          const lados = [[70, e.esquerda, e.ts[0]], [570, e.direita, e.ts[1]]];
          lados.forEach(([x, lado, t]) => {
            const s = tela(palco, x, e.y, 440, 600, lado.cor);
            const fim = tracar(rabisco(s, { tipo: "caixa", x: 0, y: 0, w: 440, h: 600 }), t, 0.55);
            const titulo = bloco(palco, e.y + 30, "centro");
            titulo.style.left = x + "px";
            titulo.style.width = "440px";
            digitar(texto(titulo, lado.titulo, 62, lado.cor), fim - 0.2);
            const si = tela(palco, x + 150, e.y + 140, 140, 140, lado.cor);
            tracar(icone(si, lado.icone, 0, 0, 140, 2), fim + 0.2, 0.5);
            const meio = bloco(palco, e.y + 330, "centro");
            meio.style.left = x + "px";
            meio.style.width = "440px";
            digitar(texto(meio, lado.texto, 72), fim + 0.6);
            const rod = bloco(palco, e.y + 470, "centro");
            rod.style.left = x + "px";
            rod.style.width = "440px";
            digitar(texto(rod, lado.rodape, 50, lado.cor), fim + 1.1);
          });
        },
        destaque(palco, e, c) {
          const s = tela(palco, 70, e.y, 940, 190, e.cor);
          const caixa = rabisco(s, { tipo: "caixa", x: 0, y: 0, w: 940, h: 190, r: 30 }, { strokeWidth: 5 });
          const caixa2 = rabisco(s, { tipo: "caixa", x: 10, y: 10, w: 920, h: 170, r: 26 }, { strokeWidth: 2.5, roughness: 1.8 });
          const fim = tracar([...caixa, ...caixa2], e.t, 0.6);
          const b = bloco(palco, e.y + 45, "centro");
          digitar(texto(b, e.texto, 92, e.cor), fim - 0.2, 0.045);
        },
      };

      document.fonts.ready.then(() => {
        D.cenas.forEach((c, i) => {
          const palco = document.getElementById("cena-" + c.id).firstElementChild;
          c.elementos.forEach((e) => construtores[e.tipo](palco, e, c));
          tl.fromTo(palco, { scale: 1 }, { scale: 1.035, duration: c.duracao, ease: "none" }, c.inicio);
          if (i < D.cenas.length - 1) {
            tl.to(palco, { opacity: 0, filter: "blur(14px)", duration: 0.32, ease: "power2.in" }, c.inicio + c.duracao - 0.32);
          } else {
            tl.to(palco, { opacity: 0, duration: 0.6, ease: "power1.in" }, c.inicio + c.duracao - 0.6);
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
