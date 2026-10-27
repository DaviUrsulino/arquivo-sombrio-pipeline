// Motor dos moldes "estúdio" (escuro, rabisco, neon): lê window.DADOS (mesmo formato do pixel2) e monta a
// timeline GSAP. Cada molde define window.TEMA com o que muda de um estilo pro outro (ícone, entrada, transição,
// fundo animado); a estrutura de cada visual (título, contador, cadeia, lista, terminal...) é a mesma.
// Regras: nada aleatório (semente fixa), tudo na timeline (o render do Hyperframes navega por ela).
(function () {
  const D = window.DADOS;
  const T = window.TEMA;
  const principal = gsap.timeline({ paused: true });
  let tl = principal;
  let semente = 7;
  const rnd = () => ((semente = (semente * 9301 + 49297) % 233280) / 233280);
  const COR = (n) => T.cores[n] || T.cores.branco;
  const mil = (n) => (n >= 10000 ? Math.floor(n / 1000) + " mil" : n >= 1000 ? (n / 1000).toFixed(1).replace(".", ",") + " mil" : String(n));

  function el(pai, tag, classe, estilo, html) {
    const d = document.createElement(tag);
    if (classe) d.className = classe;
    if (estilo) Object.assign(d.style, estilo);
    if (html !== undefined) d.innerHTML = html;
    pai.appendChild(d);
    return d;
  }
  function svgIcone(nome, cor, tamanho, traco) {
    const miolo = D.icones[nome] || D.icones["sparkles"] || "";
    const s = `<svg class="ic" width="${tamanho}" height="${tamanho}" viewBox="0 0 24 24" fill="none" stroke="${cor}" stroke-width="${traco || T.traco}" stroke-linecap="round" stroke-linejoin="round">${miolo}</svg>`;
    const caixa = document.createElement("div");
    caixa.innerHTML = s;
    const svg = caixa.firstElementChild;
    svg.querySelectorAll("path,circle,rect,line,polyline,polygon,ellipse").forEach((f) => f.setAttribute("pathLength", "1"));
    return svg;
  }
  // desenha o traço de um svg (path com pathLength=1) — usado no rabisco e no neon.
  function desenhar(svg, t, dur) {
    const formas = svg.querySelectorAll("[pathLength]");
    tl.fromTo(formas, { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: dur || 0.6, stagger: 0.08, ease: "power2.inOut" }, t);
  }
  const API = { tl, el, svgIcone, desenhar, COR, rnd, D, mil, palavras: (pai, t, cl) => palavras(pai, t, cl), entrar: (a, t, i) => entrar(a, t, i), V: null };

  function pintarTile(tile, hex) {
    if (T.pintarTile) return T.pintarTile(tile, hex);
    tile.style.background = hex + "24"; tile.style.borderColor = hex + "99"; tile.style.boxShadow = `0 0 60px ${hex}55`;
  }
  function entrar(alvo, t, i) { T.entrar(API, alvo, t, i || 0); }

  // palavras que entram uma a uma
  function palavras(pai, texto, classe) {
    return texto.split(" ").map((p) => el(pai, "span", classe || "pal", null, p + " "));
  }

  const V = {
    titulo_pixel(palco, e, c) {
      if (e.linhas[0] && e.linhas[0].texto === "COMENTA") return V.cta(palco, e, e.linhas[e.linhas.length - 1].texto);
      const caixa = el(palco, "div", "titulo");
      const todas = [];
      e.linhas.forEach((l, i) => {
        const chars = l.texto.length;
        const tam = Math.min((l.tamanho || 120) * T.escalaTitulo, 1000 / (chars * T.larguraLetra));
        const linha = el(caixa, "div", "titulo-linha", { fontSize: tam + "px", color: i === e.linhas.length - 1 ? COR(T.destaqueTitulo || l.cor) : COR(l.cor === "laranja" ? T.acento : l.cor) });
        todas.push(...palavras(linha, l.texto, "pal"));
      });
      // Cena 1: o primeiro quadro é a capa no feed e a 1ª impressão de quem rola a tela. O gancho inteiro precisa
      // estar legível já em t=0 (retenção medida em 2026-10-27: 3,5 s; a pessoa sai antes do título terminar de entrar).
      const primeira = c && c.inicio < 0.01;
      const inicio = primeira ? 0 : e.t, passo = primeira ? 0 : 0.1;
      if (primeira) todas.forEach((p) => tl.set(p, { opacity: 1 }, 0));
      if (T.sublinhado) T.sublinhado(API, caixa, primeira ? 0 : e.t + 0.25 + todas.length * 0.1);
      if (primeira) todas.forEach((p, i) => tl.fromTo(p, { scale: 1.15 }, { scale: 1, duration: 0.4, ease: "back.out(2)" }, 0));
      else todas.forEach((p, i) => entrar(p, inicio + i * passo, i));
    },
    contador(palco, e) {
      const r = D.repos[e.repo] || { estrelas: 0, repo: e.repo };
      const caixa = el(palco, "div", "contador");
      const chip = el(caixa, "div", "chip");
      chip.appendChild(svgIcone("github", COR("branco"), 54));
      el(chip, "span", "", null, r.repo);
      const linha = el(caixa, "div", "num-linha");
      const estrela = svgIcone("star", COR("amarelo"), 150);
      estrela.classList.add("estrela");
      linha.appendChild(estrela);
      const num = el(linha, "div", "num", null, "0");
      el(caixa, "div", "rotulo", null, "estrelas no GitHub");
      entrar(chip, e.t, 0);
      entrar(linha, e.t + 0.2, 1);
      T.desenharIcone && desenhar(estrela, e.t + 0.2, 0.7);
      const st = { v: 0 };
      tl.to(st, { v: r.estrelas, duration: 1.4, ease: "power3.out", onUpdate: () => { num.textContent = mil(Math.round(st.v)); } }, e.t + 0.3);
      entrar(caixa.lastElementChild, e.t + 0.6, 2);
    },
    cadeia(palco, e) {
      // sempre na vertical: no 9:16 três nós lado a lado ficam pequenos demais pra ler.
      const caixa = el(palco, "div", "cadeia");
      e.nos.forEach((n, i) => {
        if (i > 0) {
          const seta = el(caixa, "div", "seta");
          seta.appendChild(svgIcone("arrow-down", COR(T.acento), 70, 3));
          entrar(seta, (e.ts[i] || e.t) - 0.15, i);
        }
        const no = el(caixa, "div", "no");
        const tile = el(no, "div", "tile"); pintarTile(tile, COR(n.cor));
        const ic = svgIcone(n.icone, T.corIcone ? T.corIcone(n.cor) : COR(n.cor), 92);
        tile.appendChild(ic);
        el(no, "div", "no-rot", null, n.rotulo);
        const t = (e.ts && e.ts[i]) || e.t + i * 0.5;
        entrar(no, t, i);
        if (T.desenharIcone) desenhar(ic, t + 0.05, 0.7);
      });
    },
    lista(palco, e) {
      const caixa = el(palco, "div", "lista");
      e.itens.forEach((txt, i) => {
        const it = el(caixa, "div", "item");
        const ic = svgIcone("check", COR("verde"), 64, 3);
        el(it, "div", "marca").appendChild(ic);
        el(it, "div", "item-txt", null, txt);
        const t = (e.ts && e.ts[i]) || e.t + i * 0.4;
        entrar(it, t, i);
        if (T.desenharIcone) desenhar(ic, t + 0.1, 0.4);
      });
    },
    terminal(palco, e) {
      const jan = el(palco, "div", "janela");
      el(jan, "div", "barra", null, `<i></i><i></i><i></i><span>${e.rotulo || "terminal"}</span>`);
      const corpo = el(jan, "div", "corpo");
      const cmd = el(corpo, "div", "cmd", null, `<b>$</b> `);
      const letras = [...e.comando].map((ch) => el(cmd, "span", "", { opacity: 0 }, ch === " " ? "&nbsp;" : ch));
      const cursor = el(cmd, "span", "cursor", null, "▌");
      const t0 = (e.ts && e.ts[0]) || e.t;
      entrar(jan, t0, 0);
      tl.to(letras, { opacity: 1, duration: 0.01, stagger: Math.min(0.06, 1.2 / letras.length), ease: "none" }, t0 + 0.35);
      tl.to(cursor, { opacity: 0, duration: 0.01, repeat: 9, yoyo: true, repeatDelay: 0.25 }, t0 + 0.35);
      if (e.texto) {
        const ok = el(corpo, "div", "saida", null, `✓ ${e.texto}`);
        entrar(ok, (e.ts && e.ts[1]) || t0 + 1.4, 1);
      }
    },
    icone_pixel(palco, e) {
      const caixa = el(palco, "div", "icone-grande");
      const tile = el(caixa, "div", "tile big"); pintarTile(tile, COR(e.cor));
      const ic = svgIcone(e.icone, T.corIcone ? T.corIcone(e.cor) : COR(e.cor), 260);
      tile.appendChild(ic);
      const rot = el(caixa, "div", "rotulo-grande", null, e.rotulo || "");
      entrar(tile, e.t, 0);
      if (T.desenharIcone) desenhar(ic, e.t + 0.1, 0.9);
      entrar(rot, e.t + 0.35, 1);
      if (T.raios) T.raios(API, caixa, e.t + 0.3);
    },
    comparar(palco, e) {
      const caixa = el(palco, "div", "comparar");
      [e.esq, e.dir].forEach((lado, i) => {
        const card = el(caixa, "div", "card", { borderColor: COR(lado.cor) });
        const ic = svgIcone(lado.icone || "zap", COR(lado.cor), 110);
        card.appendChild(ic);
        el(card, "div", "card-tit", { color: COR(lado.cor) }, lado.titulo);
        (lado.linhas || []).forEach((l) => el(card, "div", "card-lin", null, `${l.rotulo}<span style="width:${(l.valor / 8) * 100}%;background:${COR(lado.cor)}"></span>`));
        entrar(card, (e.ts && e.ts[i]) || e.t + i * 0.5, i);
      });
    },
    niveis(palco, e) {
      const caixa = el(palco, "div", "niveis");
      e.itens.forEach((n, i) => {
        const col = el(caixa, "div", "nivel");
        const barra = el(col, "div", "barra-n", { height: 140 + n.altura * 160 + "px", background: COR(n.cor) });
        el(col, "div", "no-rot", null, n.rotulo);
        const t = (e.ts && e.ts[i]) || e.t + i * 0.4;
        tl.fromTo(barra, { scaleY: 0 }, { scaleY: 1, duration: 0.6, ease: "back.out(1.6)", transformOrigin: "bottom" }, t);
        entrar(col.lastElementChild, t + 0.2, i);
      });
    },
    banner_repo(palco, e) {
      const jan = el(palco, "div", "janela nav");
      el(jan, "div", "barra", null, `<i></i><i></i><i></i>`);
      const url = el(jan, "div", "url");
      url.appendChild(svgIcone("github", COR("branco"), 46));
      el(url, "span", "", null, e.url);
      entrar(jan, e.t, 0);
    },
    cta(palco, e, palavra) {
      const tit = el(palco, "div", "titulo");
      const l1 = el(tit, "div", "titulo-linha", { fontSize: 130 * T.escalaTitulo + "px", color: COR("branco") });
      const ps = palavras(l1, "QUER O LINK?", "pal");
      ps.forEach((p, i) => entrar(p, e.t + i * 0.1, i));
      const post = el(palco, "div", "comentario");
      el(post, "div", "avatar", null, "");
      const corpo = el(post, "div", "com-corpo");
      el(corpo, "div", "com-user", null, "voce");
      const txt = el(corpo, "div", "com-txt");
      const letras = [...palavra].map((ch) => el(txt, "span", "", { opacity: 0 }, ch));
      const cur = el(txt, "span", "cursor", null, "|");
      const cor = el(post, "div", "coracao");
      cor.appendChild(svgIcone("heart", COR("vermelho"), 54));
      const t1 = e.t + 0.9;
      entrar(post, t1, 1);
      tl.to(letras, { opacity: 1, duration: 0.01, stagger: 0.12, ease: "none" }, t1 + 0.4);
      tl.to(cur, { opacity: 0, duration: 0.01, repeat: 7, yoyo: true, repeatDelay: 0.22 }, t1 + 0.4);
      const fim = t1 + 0.5 + letras.length * 0.12;
      tl.fromTo(cor, { scale: 0.4, opacity: 0.3 }, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(3)" }, fim);
      tl.to(cor.querySelector("svg"), { fill: COR("vermelho"), duration: 0.1 }, fim);
      const dm = el(palco, "div", "dm", null, "");
      dm.appendChild(svgIcone("send", COR(T.acento), 52));
      el(dm, "span", "", null, "link chega no seu direct");
      entrar(dm, fim + 0.5, 2);
    },
    sala_pixel(palco, e) { V.icone_pixel(palco, { ...e, icone: "users", rotulo: e.rotulo }); },
    selo_pixel(palco, e) {
      const s = el(palco, "div", "selo", null, e.texto);
      entrar(s, e.t, 0);
    },
  };
  API.V = V;
  function generico(palco, e) {
    const txt = e.rotulo || e.texto || (e.linhas || []).map((l) => l.texto).join(" ") || "";
    V.icone_pixel(palco, { t: e.t, icone: e.icone || "sparkles", cor: e.cor || "laranja", rotulo: txt });
  }

  // legenda: palavra por palavra, com a palavra-chave do bloco colorida
  function legenda() {
    const caixa = document.getElementById("legenda");
    const destaques = new Set((D.destaques || []).map((p) => p.toLowerCase()));
    const limpa = (p) => p.toLowerCase().replace(/[^a-zà-ú0-9]/g, "");
    D.legenda.forEach((b) => {
      const bloco = el(caixa, "div", "bloco");
      const ps = b.texto.split(" ");
      let alvo = ps.findIndex((p) => destaques.has(limpa(p)));
      if (alvo < 0) { let maior = 0; ps.forEach((p, i) => { if (limpa(p).length > maior) { maior = limpa(p).length; alvo = i; } }); }
      const spans = ps.map((p, i) => el(bloco, "span", i === alvo ? "w dest" : "w", null, p));
      tl.set(bloco, { opacity: 1 }, b.t);
      const passo = Math.min(0.22, (b.fim - b.t) / (ps.length + 1));
      spans.forEach((s, i) => T.palavraLegenda(API, s, b.t + i * passo, i === alvo));
      tl.set(bloco, { opacity: 0 }, b.fim);
    });
  }

  // personagem: o Robô Estagiário (assets/robo, gerado por scripts/gerar_robo_reacoes.py), uma imagem por reação; troca por cena (humor) e "fala" alternando boca aberta/meia.
  const POSE_POR_HUMOR = { normal: "falando_aberto", feliz: "comemorando", animado: "impressionado", pensando: "pensativo_intenso" };
  function personagem() {
    const caixa = document.getElementById("personagem");
    if (!caixa) return;
    const nomes = ["neutro", "falando_aberto", "falando_meio", "comemorando", "impressionado", "pensativo_intenso", "apontando", "surpreso", "piscando", "confuso", "chocado"];
    const imgs = {};
    nomes.forEach((n) => { imgs[n] = el(caixa, "img", "pose", { opacity: 0 }); imgs[n].src = "assets/robo/" + n + ".svg"; });
    const mostrar = (n, t) => nomes.forEach((k) => tl.set(imgs[k], { opacity: k === n ? 1 : 0 }, t));
    D.cenas.forEach((c, i) => {
      const ultima = i === D.cenas.length - 1;
      const pose = ultima ? "apontando" : i === 0 ? "surpreso" : POSE_POR_HUMOR[c.humor] || "falando_aberto";
      mostrar(pose, c.inicio);
      tl.fromTo(caixa, { y: 30, scaleY: 0.94 }, { y: 0, scaleY: 1, duration: 0.35, ease: "back.out(3)", transformOrigin: "bottom" }, c.inicio);
      if (pose === "falando_aberto") {
        for (let t = c.inicio + 0.18; t < c.inicio + c.duracao - 0.3; t += 0.36) { mostrar("falando_meio", t); mostrar("falando_aberto", t + 0.18); }
      }
    });
  }

  document.fonts.ready.then(() => {
    if (T.fundo) T.fundo(API, D.duracao);
    const topo = document.getElementById("topo");
    const repo = Object.values(D.repos || {})[0];
    if (topo && repo) {
      const ch = el(topo, "div", "topo-chip");
      ch.appendChild(svgIcone("github", COR("branco"), 40));
      el(ch, "span", "", null, repo.repo);
      tl.fromTo(ch, { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }, 0.2);
    }
    const part = document.getElementById("particulas");
    if (part && T.particula) {
      for (let i = 0; i < 26; i++) {
        const p = el(part, "div", "particula");
        const x = rnd() * 1080, y = 400 + rnd() * 1500, dur = 6 + rnd() * 8;
        T.particula(API, p, x, y, dur, rnd() * dur, D.duracao);
      }
    }
    D.cenas.forEach((c, i) => {
      const secao = document.getElementById("cena-" + c.id);
      const palco = secao.firstElementChild;
      // cena 1: as entradas vão numa linha do tempo à parte que entra no vídeo já adiantada (ver abaixo)
      if (i === 0) { tl = gsap.timeline({ paused: true }); API.tl = tl; }
      c.elementos.forEach((e) => {
        // cenas com várias âncoras (cadeia, lista, terminal) só trazem `ts`; o começo da cena é a primeira
        if (e.t === undefined) e.t = e.ts && e.ts.length ? e.ts[0] : c.inicio + 0.1;
        // cena 1 começa a desenhar no quadro zero: o gancho não pode esperar a primeira palavra falada
        if (i === 0) e.t = 0;
        // a identidade pode trocar a cena inteira de um tipo (ex.: cadeia vira diagrama hub no pixel UI)
        const ehCta = e.tipo === "titulo_pixel" && e.linhas && e.linhas[0] && e.linhas[0].texto === "COMENTA";
        const proprio = T.visuais && (ehCta ? T.visuais.cta : T.visuais[e.tipo]);
        if (proprio) return ehCta ? proprio(API, palco, e, e.linhas[e.linhas.length - 1].texto, c, i) : proprio(API, palco, e, c, i);
        (V[e.tipo] || generico)(palco, e, c);
      });
      if (T.aoEntrarCena) T.aoEntrarCena(API, secao, palco, c, i);
      if (i === 0) {
        // adianta as entradas da cena 1 em 1,6 s: no quadro zero o gancho já está montado e legível
        const pre = tl;
        tl = principal; API.tl = principal;
        principal.add(pre.tweenFromTo(1.6, Math.max(1.7, pre.duration()), { ease: "none" }), 0);
      }
      tl.set(secao, { opacity: 1 }, c.inicio);
      T.transicao(API, palco, c, i);
      // câmera: empurrão lento, nunca parada; margem do layout garante que nada corta.
      tl.fromTo(palco, { scale: 1 }, { scale: 1.045, duration: c.duracao, ease: "none" }, c.inicio);
      tl.set(secao, { opacity: 0 }, c.inicio + c.duracao);
    });
    if (T.legendaPropria) T.legendaPropria(API); else legenda();
    personagem();
    const barra = document.getElementById("progresso");
    if (barra) tl.fromTo(barra, { scaleX: 0 }, { scaleX: 1, duration: D.duracao, ease: "none", transformOrigin: "left" }, 0);
    window.__timelines = window.__timelines || {};
    window.__timelines["main"] = principal;
  });
})();
