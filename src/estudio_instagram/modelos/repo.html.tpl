<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Repositório em destaque</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      :root {
        --laranja: #ff9d3c; --azul: #5fb4ff; --verde: #4ee06a; --roxo: #b48cff;
        --vermelho: #ff5c5c; --amarelo: #ffd84a; --branco: #f1efe8;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #07080c; }
      #root {
        position: relative; width: 100%; height: 100%; overflow: hidden;
        font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: var(--branco);
      }
      #fundo {
        position: absolute; inset: 0;
        background:
          radial-gradient(ellipse 80% 40% at 50% 38%, rgba(95,180,255,.20) 0%, transparent 70%),
          radial-gradient(ellipse 90% 60% at 50% 30%, #12141c 0%, #090a0f 60%, #040507 100%);
      }
      #pontos {
        position: absolute; inset: 0; opacity: .12;
        background-image: radial-gradient(#fff 1.4px, transparent 1.6px); background-size: 54px 54px;
      }
      .cena { position: absolute; inset: 0; }
      .palco { position: absolute; inset: 0; }
      .el { position: absolute; opacity: 0; }
      .titulo { font-weight: 800; text-transform: uppercase; letter-spacing: .03em; line-height: 1.04; text-align: center; white-space: pre-wrap; padding: 0 60px; text-shadow: 0 0 40px rgba(255,255,255,.16); }
      .titulo span { opacity: 1; }
      .mundo { position: absolute; left: 0; width: 1080px; perspective: 1500px; opacity: 0; }
      .cartao-repo {
        position: relative; width: 880px; margin: 0 auto; border-radius: 36px; padding: 48px 52px 44px;
        background: linear-gradient(165deg, #151922 0%, #0d1117 60%);
        border: 2px solid rgba(255,255,255,.12);
        box-shadow: 0 70px 130px rgba(0,0,0,.75), 0 0 90px rgba(95,180,255,.18), inset 0 1px 0 rgba(255,255,255,.08);
      }
      .cartao-topo { display: flex; align-items: center; gap: 22px; }
      .cartao-topo svg { flex: none; }
      .cartao-nome { font-size: 44px; font-weight: 600; color: #8ab4ff; overflow-wrap: anywhere; line-height: 1.1; }
      .cartao-nome b { color: #fff; font-weight: 800; }
      .cartao-desc { margin-top: 30px; font-size: 46px; line-height: 1.3; color: #d6d9e0; }
      .cartao-rodape { margin-top: 38px; display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
      .selinho {
        display: inline-flex; align-items: center; gap: 12px; padding: 12px 28px; border-radius: 999px;
        font-size: 40px; font-weight: 700; border: 2px solid rgba(255,255,255,.16); background: rgba(255,255,255,.05);
      }
      .selinho.ouro { color: #ffd84a; border-color: rgba(255,216,74,.55); background: rgba(255,216,74,.10); }
      .gigante { font-size: 270px; font-weight: 800; line-height: 1; text-align: center; color: #ffd84a; text-shadow: 0 0 70px rgba(255,216,74,.45); width: 1080px; }
      .gigante-rotulo { font-size: 66px; font-weight: 700; text-align: center; width: 1080px; color: #d6d9e0; letter-spacing: .04em; text-transform: uppercase; }
      .no {
        position: absolute; width: 300px; height: 330px; border-radius: 32px; opacity: 0; border: 5px solid;
        background: linear-gradient(165deg, #1b1f2a, #10131a); display: flex; flex-direction: column;
        align-items: center; justify-content: center; gap: 18px; box-shadow: 0 40px 80px rgba(0,0,0,.6);
      }
      .no .rotulo { font-size: 40px; font-weight: 700; text-align: center; line-height: 1.1; padding: 0 16px; white-space: pre-wrap; }
      .seta { position: absolute; overflow: visible; left: 0; top: 0; }
      #legendas { position: absolute; left: 0; top: 1660px; width: 1080px; height: 190px; }
      .bloco-legenda {
        position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
        padding: 0 60px; text-align: center; font-size: 76px; font-weight: 800; line-height: 1.05; opacity: 0;
        color: #fff; text-shadow: 0 5px 0 #000, 0 0 26px rgba(0,0,0,.95);
      }
      .bloco-legenda .dest { color: #4ee06a; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <div id="fundo" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></div>
      <div id="pontos" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
{{CENAS}}
      <div id="legendas" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="3"></div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const D = window.DADOS;
      const tl = gsap.timeline({ paused: true });
      const SVG = "http://www.w3.org/2000/svg";
      const cor = (nome) => `var(--${nome || "branco"})`;
      const mil = (n) => (n >= 10000 ? Math.floor(n / 1000) + " mil" : n >= 1000 ? (n / 1000).toFixed(1).replace(".", ",") + " mil" : String(n));

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

      function svgIcone(nome, tamanho, corCss, espessura = 1.8) {
        const s = document.createElementNS(SVG, "svg");
        s.setAttribute("width", tamanho); s.setAttribute("height", tamanho);
        s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("fill", "none");
        s.setAttribute("stroke", "currentColor"); s.setAttribute("stroke-width", espessura);
        s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
        s.style.color = corCss;
        s.innerHTML = D.icones[nome];
        return s;
      }

      function criarCartao(e) {
        const dados = D.repos[e.repo];
        const [dono, nome] = dados.repo.split("/");
        const cartao = document.createElement("div");
        cartao.className = "cartao-repo";
        const topo = document.createElement("div");
        topo.className = "cartao-topo";
        topo.appendChild(svgIcone("github", 84, "#ffffff", 1.6));
        const n = document.createElement("div");
        n.className = "cartao-nome";
        n.innerHTML = `${dono} / <b>${nome}</b>`;
        topo.appendChild(n);
        cartao.appendChild(topo);
        const desc = document.createElement("div");
        desc.className = "cartao-desc";
        desc.textContent = dados.descricao;
        cartao.appendChild(desc);
        const rodape = document.createElement("div");
        rodape.className = "cartao-rodape";
        const estrelas = document.createElement("div");
        estrelas.className = "selinho ouro";
        estrelas.appendChild(svgIcone("star", 44, "#ffd84a", 2));
        const numero = document.createElement("span");
        estrelas.appendChild(numero);
        rodape.appendChild(estrelas);
        const lic = document.createElement("div");
        lic.className = "selinho";
        lic.textContent = dados.licenca;
        rodape.appendChild(lic);
        cartao.appendChild(rodape);
        return { cartao, numero, total: dados.estrelas };
      }

      function contar(numero, total, t, duracao = 1.4) {
        const estado = { v: 0 };
        numero.textContent = "0";
        tl.to(estado, { v: total, duration: duracao, ease: "power2.out", onUpdate: () => { numero.textContent = mil(Math.round(estado.v)); } }, t);
      }

      const construtores = {
        cabecalho(palco, e, c) {
          const b = bloco(palco, e.y);
          const t = document.createElement("div");
          t.className = "titulo";
          t.style.fontSize = (e.tamanho || 120) + "px";
          t.style.color = cor(e.cor || "branco");
          textoPorSpan(t, e.texto);
          b.appendChild(t);
          tl.set(b, { opacity: 1 }, e.t);
          tl.fromTo(t.querySelectorAll("span"), { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: 0.026, ease: "none" }, e.t);
        },
        cartao_repo(palco, e, c) {
          const mundo = document.createElement("div");
          mundo.className = "mundo";
          mundo.style.top = e.y + "px";
          const { cartao, numero, total } = criarCartao(e);
          if (e.escala) cartao.style.transform = `scale(${e.escala})`;
          mundo.appendChild(cartao);
          palco.appendChild(mundo);
          tl.set(cartao, { transformPerspective: 1500 }, 0);
          tl.set(mundo, { opacity: 1 }, e.t);
          tl.fromTo(cartao, { rotationY: -48, rotationX: 24, y: 160, opacity: 0 }, { rotationY: -13, rotationX: 7, y: 0, opacity: 1, duration: 0.9, ease: "power3.out" }, e.t);
          tl.to(cartao, { y: -22, rotationY: -8, duration: 2.2, ease: "sine.inOut", yoyo: true, repeat: 5 }, e.t + 0.9);
          contar(numero, total, e.t + 0.5);
        },
        estrelas_gigante(palco, e, c) {
          const dados = D.repos[e.repo];
          const numero = document.createElement("div");
          numero.className = "el gigante"; numero.style.top = e.y + "px"; numero.style.left = "0";
          const rotulo = document.createElement("div");
          rotulo.className = "el gigante-rotulo"; rotulo.style.top = (e.y + 300) + "px"; rotulo.style.left = "0";
          rotulo.textContent = "★ estrelas no GitHub";
          palco.appendChild(numero); palco.appendChild(rotulo);
          tl.fromTo(numero, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(2)" }, e.ts[0]);
          tl.to(numero, { scale: 1.06, duration: 1.6, ease: "sine.inOut", yoyo: true, repeat: 3 }, e.ts[0] + 0.6);
          tl.fromTo(rotulo, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4 }, e.ts[0] + 0.4);
          contar(numero, dados.estrelas, e.ts[0], 1.3);
          const lic = document.createElement("div");
          lic.className = "el selinho";
          lic.style.top = (e.y + 470) + "px"; lic.style.left = "50%"; lic.style.marginLeft = "-170px";
          lic.style.fontSize = "56px"; lic.style.padding = "18px 44px";
          lic.appendChild(svgIcone("shield-check", 60, "#4ee06a", 2));
          const t = document.createElement("span"); t.textContent = dados.licenca; lic.appendChild(t);
          palco.appendChild(lic);
          tl.fromTo(lic, { opacity: 0, y: 40, scale: .8 }, { opacity: 1, y: 0, scale: 1, duration: 0.45, ease: "back.out(1.8)" }, e.ts[1]);
        },
        // Três nós em linha ligados por setas.
        fluxo_linha(palco, e, c) {
          const xs = [40, 390, 740];
          e.itens.forEach((it, i) => {
            const n = document.createElement("div");
            n.className = "no";
            n.style.left = xs[i] + "px"; n.style.top = e.y + "px"; n.style.borderColor = cor(it.cor);
            n.appendChild(svgIcone(it.icone, 120, cor(it.cor)));
            const r = document.createElement("div");
            r.className = "rotulo"; r.style.color = cor(it.cor); r.textContent = it.rotulo;
            n.appendChild(r);
            palco.appendChild(n);
            tl.fromTo(n, { opacity: 0, y: 40, scale: .8 }, { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "back.out(1.8)" }, e.ts[i]);
            if (i > 0) {
              const s = document.createElementNS(SVG, "svg");
              s.setAttribute("class", "seta"); s.setAttribute("width", 1080); s.setAttribute("height", 1920);
              const x1 = xs[i - 1] + 300 + 8, x2 = xs[i] - 8, y = e.y + 165;
              const haste = document.createElementNS(SVG, "path");
              haste.setAttribute("d", `M${x1} ${y} L${x2 - 6} ${y}`);
              const ponta = document.createElementNS(SVG, "path");
              ponta.setAttribute("d", `M${x2 - 30} ${y - 22} L${x2} ${y} L${x2 - 30} ${y + 22}`);
              [haste, ponta].forEach((p) => {
                p.setAttribute("fill", "none"); p.setAttribute("stroke", cor(it.cor)); p.setAttribute("stroke-width", 10);
                p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-linejoin", "round"); s.appendChild(p);
              });
              palco.appendChild(s);
              tl.set(haste, { attr: { "stroke-dasharray": 40, "stroke-dashoffset": 40 } }, 0);
              tl.set(ponta, { opacity: 0 }, 0);
              tl.to(haste, { attr: { "stroke-dashoffset": 0 }, duration: 0.3 }, e.ts[i] - 0.3);
              tl.to(ponta, { opacity: 1, duration: 0.1 }, e.ts[i] - 0.05);
            }
          });
        },
      };

      document.fonts.ready.then(() => {
        D.cenas.forEach((c, i) => {
          const palco = document.getElementById("cena-" + c.id).firstElementChild;
          c.elementos.forEach((e) => {
            construtores[e.tipo](palco, e, c);
          });
          tl.fromTo(palco, { scale: 1.0 }, { scale: 1.04, duration: c.duracao, ease: "none" }, c.inicio);
          if (i < D.cenas.length - 1) {
            tl.to(palco, { opacity: 0, duration: 0.25, ease: "power2.in" }, c.inicio + c.duracao - 0.25);
          } else {
            tl.to(palco, { opacity: 0, duration: 0.5, ease: "power1.in" }, c.inicio + c.duracao - 0.5);
          }
        });
        const caixaLegenda = document.getElementById("legendas");
        const destaque = new Set((D.destaques || []).map((p) => p.toLowerCase()));
        D.legenda.forEach((b) => {
          const el = document.createElement("div");
          el.className = "bloco-legenda";
          const linha = document.createElement("div");
          linha.innerHTML = b.texto.split(" ").map((p) => {
            const limpa = p.toLowerCase().replace(/[^a-zà-ú0-9]/g, "");
            return destaque.has(limpa) ? `<span class="dest">${p}</span>` : p;
          }).join(" ");
          el.appendChild(linha);
          caixaLegenda.appendChild(el);
          tl.set(el, { opacity: 1 }, b.t);
          tl.set(el, { opacity: 0 }, b.fim);
        });
        window.__timelines["main"] = tl;
      });
    </script>
  </body>
</html>
