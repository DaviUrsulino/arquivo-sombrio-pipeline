<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1350" />
    <title>Carrossel</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/vendor/rough.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      @font-face {
        font-family: "Patrick Hand";
        src: url("assets/fonts/PatrickHand-Regular.ttf") format("truetype");
      }
      :root {
        --laranja: #ff9d3c; --azul: #5fb4ff; --verde: #4ee06a; --roxo: #b48cff;
        --vermelho: #ff5c5c; --amarelo: #ffd84a; --branco: #f1efe8; --fraco: #9a968d;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1350px; overflow: hidden; background: #060607; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Patrick Hand", cursive; color: var(--branco); }
      .slide { position: absolute; inset: 0; }
      .fundo { position: absolute; inset: 0; background: radial-gradient(ellipse 75% 60% at 50% 42%, #18191d 0%, #0b0b0d 58%, #040405 100%); }
      .neon { text-shadow: 0 0 18px currentColor; }
      .abs { position: absolute; }
      svg.risco { position: absolute; overflow: visible; filter: drop-shadow(0 0 7px currentColor); }
      .rodape { position: absolute; left: 70px; right: 70px; bottom: 50px; display: flex; justify-content: space-between; font-size: 32px; color: var(--fraco); }
      .pagina { position: absolute; top: 60px; right: 70px; font-size: 34px; color: var(--fraco); }
      .card-og { position: absolute; left: 90px; width: 900px; height: 450px; border-radius: 18px; overflow: hidden; }
      .card-og img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .chip { display: inline-block; margin-right: 18px; padding: 10px 26px; border: 3px solid currentColor; border-radius: 40px; font-size: 36px; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1350" data-duration="{{DURACAO}}">
{{SLIDES}}
    </div>
    <script>
      const SVG = "http://www.w3.org/2000/svg";
      const cor = (n) => `var(--${n})`;
      let semente = 11;

      const D = window.DADOS;
      const TOTAL = D.itens.length + 2;
      const pag = (i) => `${String(i).padStart(2, "0")} / ${String(TOTAL).padStart(2, "0")}`;

      function tela(pai, x, y, w, h, corNome) {
        const s = document.createElementNS(SVG, "svg");
        s.setAttribute("class", "risco");
        s.setAttribute("width", w); s.setAttribute("height", h);
        s.setAttribute("viewBox", `0 0 ${w} ${h}`);
        Object.assign(s.style, { left: x + "px", top: y + "px", color: cor(corNome) });
        pai.appendChild(s);
        return s;
      }
      function caixa(pai, x, y, w, h, corNome, r = 24, largura = 4) {
        const s = tela(pai, x, y, w, h, corNome);
        const d = `M${r},0 L${w - r},0 Q${w},0 ${w},${r} L${w},${h - r} Q${w},${h} ${w - r},${h} L${r},${h} Q0,${h} 0,${h - r} L0,${r} Q0,0 ${r},0 Z`;
        s.appendChild(rough.svg(s).path(d, { stroke: "currentColor", strokeWidth: largura, roughness: 1.3, bowing: 1.2, seed: semente++ }));
      }
      function linha(pai, x, y, w, corNome) {
        const s = tela(pai, x, y, w, 30, corNome);
        s.appendChild(rough.svg(s).line(0, 16, w, 10, { stroke: "currentColor", strokeWidth: 5, roughness: 1.4, seed: semente++ }));
      }
      function texto(pai, conteudo, estilo) {
        const el = document.createElement("div");
        el.className = "abs";
        el.textContent = conteudo;
        Object.assign(el.style, estilo);
        pai.appendChild(el);
        return el;
      }
      function base(slide, pagina) {
        const f = document.createElement("div"); f.className = "fundo"; slide.appendChild(f);
        const rod = document.createElement("div"); rod.className = "rodape";
        rod.innerHTML = `<span>${D.perfil}</span><span>salva pra depois →</span>`;
        slide.appendChild(rod);
        if (pagina) texto(slide, pagina, { top: "60px", right: "70px", fontSize: "34px", color: "var(--fraco)" });
      }

      function capa(slide) {
        base(slide, pag(1) + " →");
        texto(slide, D.capa.linha1, { left: "70px", top: "150px", fontSize: "120px", lineHeight: "1", color: "var(--branco)" }).classList.add("neon");
        texto(slide, D.capa.linha2, { left: "70px", top: "275px", fontSize: "150px", lineHeight: "1", color: "var(--laranja)" }).classList.add("neon");
        linha(slide, 70, 440, 760, "laranja");
        texto(slide, D.capa.subtitulo, { left: "70px", top: "500px", width: "940px", fontSize: "84px", lineHeight: "1.05", color: "var(--branco)" }).classList.add("neon");
        caixa(slide, 70, 770, 640, 110, "amarelo", 50);
        texto(slide, D.capa.selo, { left: "70px", top: "790px", width: "640px", textAlign: "center", fontSize: "56px", color: "var(--amarelo)" }).classList.add("neon");
        texto(slide, "arrasta pro lado →", { left: "70px", top: "1010px", fontSize: "60px", color: "var(--fraco)" });
      }

      function repo(slide, r, pagina) {
        base(slide, pagina);
        texto(slide, r.n, { left: "70px", top: "70px", fontSize: "150px", lineHeight: "1", color: cor(r.cor) }).classList.add("neon");
        texto(slide, r.nome, { left: "250px", top: "95px", fontSize: "54px", color: "var(--fraco)" });
        texto(slide, r.promessa, { left: "70px", top: "240px", width: "940px", fontSize: "78px", lineHeight: "1.05", color: "var(--branco)" }).classList.add("neon");
        texto(slide, r.texto, { left: "70px", top: "430px", width: "940px", fontSize: "44px", lineHeight: "1.2", color: "#d6d3cb" });
        const og = document.createElement("div");
        og.className = "card-og"; og.style.top = "600px";
        og.innerHTML = `<img src="${r.cartao}" alt="">`;
        slide.appendChild(og);
        caixa(slide, 80, 590, 920, 470, r.cor, 26, 5);
        const chips = document.createElement("div");
        chips.className = "abs";
        Object.assign(chips.style, { left: "70px", top: "1110px", color: cor(r.cor) });
        chips.innerHTML = `<span class="chip neon">★ ${r.estrelas}</span><span class="chip neon">${r.licenca}</span><span class="chip neon">grátis</span>`;
        slide.appendChild(chips);
      }

      function chamada(slide) {
        base(slide, pag(TOTAL));
        texto(slide, D.chamada.pergunta, { left: "0", top: "280px", width: "1080px", textAlign: "center", fontSize: "110px", color: "var(--branco)" }).classList.add("neon");
        caixa(slide, 110, 500, 860, 220, "amarelo", 34, 6);
        caixa(slide, 122, 512, 836, 196, "amarelo", 30, 2.5);
        texto(slide, "comenta " + D.palavra_chave, { left: "110px", top: "545px", width: "860px", textAlign: "center", fontSize: "110px", color: "var(--amarelo)" }).classList.add("neon");
        texto(slide, D.chamada.promessa, { left: "0", top: "800px", width: "1080px", textAlign: "center", fontSize: "64px", color: "var(--branco)" });
        texto(slide, D.chamada.rodape, { left: "0", top: "910px", width: "1080px", textAlign: "center", fontSize: "48px", color: "var(--fraco)" });
      }

      document.fonts.ready.then(() => {
        capa(document.getElementById("s1"));
        D.itens.forEach((r, i) => repo(document.getElementById("s" + (i + 2)), r, pag(i + 2) + " →"));
        chamada(document.getElementById("s" + TOTAL));
        window.__timelines["main"] = gsap.timeline({ paused: true });
      });
    </script>
  </body>
</html>
