<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Estúdio 3D</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/vendor/three.min.js"></script>
    <script src="assets/dados.js"></script>
    <style>
      @font-face { font-family: "Mont"; src: url("assets/fonts/Montserrat.ttf"); font-weight: 100 900; }
      @font-face { font-family: "Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #050307; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Mont", sans-serif; color: #f3eee9; }
      #gl { position: absolute; inset: 0; width: 1080px; height: 1920px; }
      #grao { position: absolute; inset: 0; opacity: .5; background-image: repeating-linear-gradient(0deg, rgba(255,255,255,.025) 0 1px, transparent 1px 3px); }
      #vinheta { position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 46%, transparent 40%, rgba(0,0,0,.85) 100%); }
      #kicker { position: absolute; top: 120px; left: 0; right: 0; text-align: center; font-family: "Mono"; font-size: 30px; color: #ff4f72; letter-spacing: 2px; opacity: .9; }
      #titulos { position: absolute; top: 175px; left: 50px; right: 50px; height: 420px; }
      .tit { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; text-align: center; opacity: 0; }
      .tit .l1 { font-weight: 900; font-size: 112px; line-height: 1; letter-spacing: -3px; text-transform: uppercase; color: #ece6dd; text-shadow: 0 8px 40px rgba(0,0,0,.8); }
      .tit .l2 { font-weight: 900; font-size: 112px; line-height: 1.02; letter-spacing: -3px; text-transform: uppercase; color: #ff2d55; text-shadow: 0 0 40px rgba(255,45,85,.45); }
      .tit .l3 { margin-top: 16px; font-family: "Mono"; font-size: 34px; color: #ff6b88; letter-spacing: 1px; }
      .ch { display: inline-block; }
      #numero { position: absolute; left: 0; right: 0; top: 760px; text-align: center; font-weight: 900; font-size: 300px; letter-spacing: -10px; color: #fff; opacity: 0; text-shadow: 0 0 60px rgba(255,45,85,.7); }
      #comentario { position: absolute; left: 80px; right: 80px; top: 880px; display: flex; align-items: center; gap: 30px; padding: 34px 38px; border-radius: 26px; background: rgba(14,8,12,.82); border: 2px solid rgba(255,45,85,.6); box-shadow: 0 0 80px rgba(255,45,85,.35); opacity: 0; }
      #comentario .av { width: 110px; height: 110px; border-radius: 50%; flex: none; background: linear-gradient(135deg, #feda75, #fa7e1e, #d62976, #962fbf); }
      #comentario .u { font-size: 34px; color: #b9a8b0; font-weight: 600; }
      #comentario .tx { font-weight: 900; font-size: 120px; line-height: 1; color: #ff2d55; letter-spacing: -2px; }
      #legenda { position: absolute; left: 60px; right: 60px; top: 1470px; height: 240px; }
      .bloco { position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 0 20px; opacity: 0; }
      .w { display: inline-block; font-weight: 900; font-size: 84px; line-height: 1.12; letter-spacing: -2px; text-transform: uppercase; color: #f3eee9; text-shadow: 0 6px 30px rgba(0,0,0,.95); }
      .w.dest { color: #ff2d55; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{{DURACAO}}">
      <canvas id="gl" class="clip" width="1080" height="1920" data-start="0" data-duration="{{DURACAO}}" data-track-index="0"></canvas>
      <div id="grao" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
      <div id="vinheta" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="1"></div>
      <div id="kicker" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="2"></div>
      <div id="titulos" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="3"></div>
      <div id="numero" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="4"></div>
      <div id="comentario" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="4"><div class="av"></div><div><div class="u">você comentou</div><div class="tx"></div></div></div>
      <div id="legenda" class="clip" data-start="0" data-duration="{{DURACAO}}" data-track-index="8"></div>
      <div style="display:none">{{CENAS}}</div>
      <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="{{DURACAO}}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      // Cada cena do roteiro vira um "plano" 3D: um objeto-herói que conta a frase (monitor, túnel de estrelas,
      // torre de blocos, terminal flutuando...), com a câmera sempre em movimento. Tudo é função do tempo t
      // (render(t)), então o Hyperframes pode buscar qualquer quadro fora de ordem.
      const D = window.DADOS;
      const W = 1080, H = 1920;
      const VERMELHO = 0xff2d55, CIANO = 0x31e7ff;
      const HEXC = { laranja: 0xff7a2d, azul: 0x4aa8ff, verde: 0x39e07a, roxo: 0xb26bff, vermelho: 0xff2d55, amarelo: 0xffc93c, branco: 0xf3eee9, rosa: 0xff5ed1 };
      const css = (n) => "#" + n.toString(16).padStart(6, "0");
      const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
      const ease = (x) => 1 - Math.pow(1 - clamp(x, 0, 1), 3);
      const easeIO = (x) => { x = clamp(x, 0, 1); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
      const back = (x) => { x = clamp(x, 0, 1); const c = 1.9; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
      const hash = (i) => { const s = Math.sin(i * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
      const mil = (n) => (n >= 10000 ? Math.floor(n / 1000) + " mil" : n >= 1000 ? (n / 1000).toFixed(1).replace(".", ",") + " mil" : String(n));

      const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById("gl"), antialias: true, preserveDrawingBuffer: true });
      renderer.setPixelRatio(1); renderer.setSize(W, H, false);
      renderer.outputEncoding = THREE.sRGBEncoding;
      const cena = new THREE.Scene();
      cena.background = new THREE.Color(0x050307);
      cena.fog = new THREE.FogExp2(0x0a0408, 0.045);
      const cam = new THREE.PerspectiveCamera(42, W / H, 0.1, 200);
      cena.add(new THREE.HemisphereLight(0x6a5a7a, 0x080204, 0.35));
      const chave = new THREE.DirectionalLight(0xffd9c4, 1.1); chave.position.set(4, 8, 6); cena.add(chave);
      const aro = new THREE.PointLight(VERMELHO, 2.2, 30); aro.position.set(-4, 2, -4); cena.add(aro);

      // ---------- texturas desenhadas em canvas ----------
      function texBrilho(cor) {
        const c = document.createElement("canvas"); c.width = c.height = 128; const x = c.getContext("2d");
        const g = x.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.25, cor); g.addColorStop(1, "rgba(0,0,0,0)");
        x.fillStyle = g; x.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c);
      }
      const BRILHO_V = texBrilho("rgba(255,45,85,.6)"), BRILHO_B = texBrilho("rgba(255,220,200,.5)"), BRILHO_C = texBrilho("rgba(49,231,255,.6)");
      function brilho(tex, tam) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: 0.45 })); s.scale.set(tam, tam, 1); return s; }
      const IMG_ICONE = {};
      function carregarIcone(nome, cor) {
        const chaveI = nome + cor; if (IMG_ICONE[chaveI]) return Promise.resolve();
        const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 24 24" fill="none" stroke="${cor}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${D.icones[nome] || D.icones.sparkles}</svg>`;
        return new Promise((ok) => { const im = new Image(); im.onload = () => { IMG_ICONE[chaveI] = im; ok(); }; im.onerror = ok; im.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg); });
      }
      function texTile(nome, cor, rotulo) {
        const c = document.createElement("canvas"); c.width = 512; c.height = rotulo ? 640 : 512; const x = c.getContext("2d");
        x.fillStyle = "#0d0709"; x.fillRect(0, 0, 512, c.height);
        x.strokeStyle = cor; x.lineWidth = 10; x.strokeRect(14, 14, 484, c.height - 28);
        const g = x.createRadialGradient(256, 230, 10, 256, 230, 260); g.addColorStop(0, cor + "55"); g.addColorStop(1, "#0000"); x.fillStyle = g; x.fillRect(0, 0, 512, c.height);
        const im = IMG_ICONE[nome + cor]; if (im) x.drawImage(im, 116, rotulo ? 70 : 116, 280, 280);
        if (rotulo) { x.fillStyle = "#f3eee9"; x.font = "900 64px Mont"; x.textAlign = "center"; x.fillText(rotulo.toUpperCase(), 256, 560, 460); }
        const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; return t;
      }
      function texTexto(linhas, largura, altura, fundo) {
        const c = document.createElement("canvas"); c.width = largura; c.height = altura; const x = c.getContext("2d");
        const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding;
        t.userData.desenhar = (fn) => { x.clearRect(0, 0, largura, altura); if (fundo) { x.fillStyle = fundo; x.fillRect(0, 0, largura, altura); } fn(x); t.needsUpdate = true; };
        return t;
      }

      // ---------- cenário fixo: chão de grade, poeira, neblina vermelha ----------
      const chao = new THREE.GridHelper(200, 100, VERMELHO, 0x5a0f22); chao.position.y = -2.2; chao.material.transparent = true; chao.material.opacity = 0.55; cena.add(chao);
      const brilhoChao = brilho(BRILHO_V, 16); brilhoChao.position.set(0, -2, -14); cena.add(brilhoChao);
      const poeira = (() => {
        const n = 700, pos = new Float32Array(n * 3);
        for (let i = 0; i < n; i++) { pos[i * 3] = (hash(i) - 0.5) * 40; pos[i * 3 + 1] = hash(i + 99) * 14 - 2; pos[i * 3 + 2] = -hash(i + 7) * 60 + 8; }
        const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
        const p = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffb3c2, size: 0.05, transparent: true, opacity: 0.7, depthWrite: false })); cena.add(p); return p;
      })();

      // ---------- planos ----------
      const PLANOS = [];
      function plano(c, construir) { const g = new THREE.Group(); g.visible = false; cena.add(g); const p = { c, g, ...construir(g, c) }; PLANOS.push(p); return p; }
      const local = (c, t) => clamp((t - c.inicio) / c.duracao, 0, 1);
      const tAncora = (e, i) => (e.ts && e.ts[i] !== undefined ? e.ts[i] : e.t);

      const CONSTRUTORES = {
        // monitor no escuro com onda de voz ao redor: "assistente que roda no seu PC"
        titulo_pixel(g, c, e) {
          const corpo = new THREE.Mesh(new THREE.BoxGeometry(3.4, 2.2, 0.18), new THREE.MeshStandardMaterial({ color: 0x18121a, roughness: 0.5, metalness: 0.4 }));
          const telaTex = texTexto([], 680, 440, "#08040a");
          const tela = new THREE.Mesh(new THREE.PlaneGeometry(3.15, 1.98), new THREE.MeshBasicMaterial({ map: telaTex, toneMapped: false })); tela.position.z = 0.1;
          const pe = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.9, 0.25), corpo.material); pe.position.y = -1.5;
          const base = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.08, 0.8), corpo.material); base.position.y = -1.95;
          const mon = new THREE.Group(); mon.add(corpo, tela, pe, base); g.add(mon);
          const halo = brilho(BRILHO_V, 9); halo.position.z = -0.6; g.add(halo);
          const barras = [];
          for (let i = 0; i < 64; i++) {
            const a = (i / 64) * Math.PI * 2;
            const b = new THREE.Mesh(new THREE.BoxGeometry(0.06, 1, 0.06), new THREE.MeshBasicMaterial({ color: i % 2 ? VERMELHO : 0xff8aa1 }));
            b.position.set(Math.cos(a) * 2.9, Math.sin(a) * 2.9 * 0.62 - 0.1, -0.3); b.rotation.z = a - Math.PI / 2; g.add(b); barras.push(b);
          }
          return {
            render(t, u) {
              const ent = ease((t - e.t) / 0.9);
              mon.scale.setScalar(0.6 + 0.4 * back((t - e.t) / 0.7));
              telaTex.userData.desenhar((x) => {
                x.strokeStyle = "#ff2d55"; x.lineWidth = 6; x.beginPath();
                for (let k = 0; k <= 680; k += 8) { const amp = 90 * Math.sin(t * 9 + k * 0.03) * Math.sin(k * 0.0046 * Math.PI) * (0.4 + 0.6 * Math.abs(Math.sin(t * 3.1))); x.lineTo(k, 220 + amp * ent); }
                x.stroke(); x.fillStyle = "#ff2d5533"; x.font = "600 26px Mono"; x.fillText("● ouvindo — modelo local", 30, 50);
              });
              barras.forEach((b, i) => { const v = 0.15 + 0.9 * Math.abs(Math.sin(t * 6 + i * 0.7)) * Math.abs(Math.sin(i * 0.31 + t)); b.scale.y = v * ent + 0.01; });
              cam.position.set(Math.sin(u * 0.8) * 1.6, 0.4 + u * 0.4, 11 - 3.2 * easeIO(u));
              cam.lookAt(0, 0.1, 0);
            },
          };
        },
        // túnel de estrelas: a câmera voa através de milhares de estrelas e o número aparece
        contador(g, c, e) {
          const n = 900, pos = new Float32Array(n * 3);
          for (let i = 0; i < n; i++) { const a = hash(i) * Math.PI * 2, r = 1.2 + hash(i + 3) * 7; pos[i * 3] = Math.cos(a) * r; pos[i * 3 + 1] = Math.sin(a) * r * 0.9 + 1; pos[i * 3 + 2] = -hash(i + 11) * 80; }
          const geo = new THREE.BufferGeometry(); geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
          const est = new THREE.Points(geo, new THREE.PointsMaterial({ map: BRILHO_B, color: 0xffd27a, size: 0.55, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); g.add(est);
          const centro = brilho(BRILHO_V, 14); centro.position.set(0, 1, -40); g.add(centro);
          const repo = D.repos[e.repo] || { estrelas: 0 };
          return {
            render(t, u) {
              cam.position.set(Math.sin(u * 3) * 0.3, 1 + Math.cos(u * 2) * 0.2, 6 - 46 * easeIO(u));
              cam.lookAt(0, 1, cam.position.z - 10);
              cam.rotation.z = u * 0.5;
              const k = ease((t - e.t - 0.2) / 1.5);
              numero.textContent = mil(Math.round(repo.estrelas * k)) + " ★";
            },
            numero: true,
          };
        },
        // nós viram blocos de luz em fila no espaço; a câmera viaja de um pro outro
        cadeia(g, c, e) {
          const nos = e.nos.map((n, i) => {
            const cor = css(HEXC[n.cor] || VERMELHO);
            const m = new THREE.Mesh(new THREE.BoxGeometry(2.4, 3, 0.3), [
              new THREE.MeshStandardMaterial({ color: 0x140b10 }), new THREE.MeshStandardMaterial({ color: 0x140b10 }),
              new THREE.MeshStandardMaterial({ color: 0x140b10 }), new THREE.MeshStandardMaterial({ color: 0x140b10 }),
              new THREE.MeshBasicMaterial({ map: texTile(n.icone, cor, n.rotulo) }), new THREE.MeshStandardMaterial({ color: 0x140b10 }),
            ]);
            m.position.set((i % 2 ? 1.4 : -1.4), 0.6, -i * 7); g.add(m);
            const h = brilho(i % 2 ? BRILHO_C : BRILHO_V, 7); h.position.set(m.position.x, 0.6, m.position.z - 0.5); g.add(h);
            return m;
          });
          const feixes = nos.slice(1).map((m, i) => {
            const a = nos[i].position, b = m.position, d = a.distanceTo(b);
            const f = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, d, 8), new THREE.MeshBasicMaterial({ color: VERMELHO }));
            f.position.copy(a).add(b).multiplyScalar(0.5); f.lookAt(b); f.rotateX(Math.PI / 2); g.add(f); return f;
          });
          return {
            render(t, u) {
              nos.forEach((m, i) => { const k = back((t - tAncora(e, i)) / 0.6); m.scale.setScalar(Math.max(0.001, k)); m.rotation.y = (1 - ease((t - tAncora(e, i)) / 0.8)) * 1.6 * (i % 2 ? -1 : 1); });
              feixes.forEach((f, i) => { f.scale.y = Math.max(0.001, ease((t - tAncora(e, i + 1) + 0.3) / 0.5)); });
              // câmera acompanha o nó atual
              let alvo = 0; e.nos.forEach((_, i) => { if (t >= tAncora(e, i) - 0.1) alvo = i; });
              const prev = Math.max(0, alvo - 1), k = easeIO((t - tAncora(e, alvo) + 0.1) / 0.7);
              const z = -(prev + (alvo - prev) * k) * 7, x = (alvo % 2 ? 1.4 : -1.4) * k + (prev % 2 ? 1.4 : -1.4) * (1 - k);
              cam.position.set(x * 0.5, 2.2, z + 12.5); cam.lookAt(x * 0.5, 0.2, z - 2);
            },
          };
        },
        // cada item é uma laje que cai e empilha
        lista(g, c, e) {
          const lajes = e.itens.map((txt, i) => {
            const tex = texTexto([], 1024, 200, "#120a0e");
            tex.userData.desenhar((x) => { x.strokeStyle = "#ff2d55"; x.lineWidth = 8; x.strokeRect(4, 4, 1016, 192); x.fillStyle = "#39e07a"; x.font = "900 90px Mont"; x.fillText("✓", 40, 135); x.fillStyle = "#f3eee9"; x.font = "900 84px Mont"; x.fillText(txt.toUpperCase(), 150, 130, 840); });
            const lado = new THREE.MeshStandardMaterial({ color: 0x1d0f15, roughness: 0.6 });
            const m = new THREE.Mesh(new THREE.BoxGeometry(5.2, 1, 1.4), [lado, lado, lado, lado, new THREE.MeshBasicMaterial({ map: tex }), lado]);
            g.add(m); return m;
          });
          const h = brilho(BRILHO_V, 12); h.position.set(0, 0, -2); g.add(h);
          return {
            render(t, u) {
              lajes.forEach((m, i) => { const k = ease((t - tAncora(e, i)) / 0.45); m.position.set(0, -1.6 + i * 1.12 + (1 - k) * 9, 0); m.rotation.y = (1 - k) * 0.8; m.visible = k > 0; });
              cam.position.set(Math.sin(u * 0.9 - 0.45) * 5, 2.4 + u * 1.2, 15.5 - u * 2); cam.lookAt(0, 0.2 + u * 0.6, 0);
            },
          };
        },
        // terminal flutuando, digitando o comando de verdade
        terminal(g, c, e) {
          const tex = texTexto([], 1200, 640, "#07090c");
          const jan = new THREE.Mesh(new THREE.BoxGeometry(6, 3.2, 0.12), [0, 0, 0, 0, 0, 0].map((_, i) => (i === 4 ? new THREE.MeshBasicMaterial({ map: tex }) : new THREE.MeshStandardMaterial({ color: 0x101820 })))); g.add(jan);
          const h = brilho(BRILHO_C, 14); h.position.z = -1; g.add(h);
          const cmd = "$ " + e.comando;
          return {
            render(t, u) {
              const t0 = tAncora(e, 0), n = Math.floor(clamp((t - t0 - 0.3) / 0.05, 0, cmd.length));
              tex.userData.desenhar((x) => {
                x.fillStyle = "#121a24"; x.fillRect(0, 0, 1200, 70); ["#ff5f57", "#febc2e", "#28c840"].forEach((cc, i) => { x.fillStyle = cc; x.beginPath(); x.arc(40 + i * 40, 35, 13, 0, 7); x.fill(); });
                x.fillStyle = "#7b8a99"; x.font = "500 30px Mono"; x.fillText(e.rotulo || "terminal", 1000, 46);
                x.fillStyle = "#e9f6ff"; x.font = "700 64px Mono"; x.fillText(cmd.slice(0, n) + (Math.floor(t * 3) % 2 ? "▌" : " "), 50, 220, 1100);
                if (e.texto && t > tAncora(e, 1)) { x.fillStyle = "#39e07a"; x.font = "500 42px Mono"; x.fillText("✓ " + e.texto, 50, 340, 1100); }
              });
              jan.scale.setScalar(Math.max(0.001, back((t - t0) / 0.6)));
              cam.position.set(-1.5 + u * 3, 0.6 - u * 0.3, 16 - u * 2.5); cam.lookAt(0, 0, 0);
            },
          };
        },
        // ícone gigante girando com onda de choque no chão
        icone_pixel(g, c, e) {
          const cor = css(HEXC[e.cor] || VERMELHO);
          const m = new THREE.Mesh(new THREE.BoxGeometry(3, 3.6, 0.35), [0, 0, 0, 0, 0, 0].map((_, i) => (i === 4 ? new THREE.MeshBasicMaterial({ map: texTile(e.icone, cor, e.rotulo) }) : new THREE.MeshStandardMaterial({ color: 0x140b10, metalness: 0.5, roughness: 0.4 })))); g.add(m);
          const aneis = [0, 1, 2].map((i) => { const r = new THREE.Mesh(new THREE.RingGeometry(1, 1.06, 96), new THREE.MeshBasicMaterial({ color: HEXC[e.cor] || VERMELHO, transparent: true, side: THREE.DoubleSide })); r.rotation.x = -Math.PI / 2; r.position.y = -2.15; g.add(r); return r; });
          const h = brilho(BRILHO_V, 10); h.position.z = -1; g.add(h);
          return {
            render(t, u) {
              const k = back((t - e.t) / 0.7); m.scale.setScalar(Math.max(0.001, k)); m.rotation.y = (1 - ease((t - e.t) / 1.2)) * Math.PI * 2 + Math.sin(t) * 0.15; m.position.y = 0.4 + Math.sin(t * 1.6) * 0.12;
              aneis.forEach((r, i) => { const f = ((t - e.t - 0.3 - i * 0.4) % 1.6 + 1.6) % 1.6 / 1.6; r.scale.setScalar(0.5 + f * 6); r.material.opacity = (1 - f) * (t > e.t + 0.3 ? 0.9 : 0); });
              cam.position.set(Math.sin(u * 1.2 - 0.6) * 11, 1.4, Math.cos(u * 1.2 - 0.6) * 11); cam.lookAt(0, 0.2, 0);
            },
          };
        },
      };
      // chamada final: blocos orbitando e o comentário sendo digitado por cima
      function construirCta(g, c, e, palavra) {
        const blocos = [];
        for (let i = 0; i < 18; i++) {
          const m = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.5, 0.5), new THREE.MeshStandardMaterial({ color: i % 3 ? 0x2a0f18 : VERMELHO, emissive: i % 3 ? 0x000000 : 0x550012, roughness: 0.4 }));
          g.add(m); blocos.push(m);
        }
        const h = brilho(BRILHO_V, 18); h.position.set(0, 0.4, -3); g.add(h);
        return {
          render(t, u) {
            blocos.forEach((m, i) => { const a = (i / 18) * Math.PI * 2 + t * 0.6, r = 3.4 + (i % 3) * 0.7; m.position.set(Math.cos(a) * r, Math.sin(a * 2 + i) * 0.6 + 0.4, Math.sin(a) * r - 1); m.rotation.set(t + i, t * 0.7 + i, 0); });
            cam.position.set(0, 1.4 + u * 0.6, 10 - u * 2.5); cam.lookAt(0, 0.4, 0);
            const t1 = e.t + 0.8, n = Math.floor(clamp((t - t1 - 0.3) / 0.14, 0, palavra.length));
            comTx.textContent = palavra.slice(0, n) + (n < palavra.length || Math.floor(t * 3) % 2 ? "|" : "");
          },
          cta: [e.t + 0.8],
        };
      }

      const numero = document.getElementById("numero");
      const comTx = document.querySelector("#comentario .tx");
      const tl = gsap.timeline({ paused: true });

      function montar() {
        const repo = Object.values(D.repos || {})[0];
        document.getElementById("kicker").textContent = repo ? "// " + repo.repo.replace("/", "_") + ".exe" : "";
        const titulos = document.getElementById("titulos");
        D.cenas.forEach((c, i) => {
          const e = c.elementos[0];
          const ehCta = e.tipo === "titulo_pixel" && e.linhas[0] && e.linhas[0].texto === "COMENTA";
          const p = ehCta ? plano(c, (g) => construirCta(g, c, e, e.linhas[e.linhas.length - 1].texto))
            : plano(c, (g) => (CONSTRUTORES[e.tipo] || CONSTRUTORES.icone_pixel)(g, c, e.tipo in CONSTRUTORES ? e : { ...e, icone: e.icone || "sparkles", rotulo: e.rotulo || e.texto || "" }));
          // título de cada plano: linhas do visual quando houver, senão a manchete curta derivada do tipo
          const tit = document.createElement("div"); tit.className = "tit"; titulos.appendChild(tit);
          let l1 = "", l2 = "", l3 = "";
          if (ehCta) { l1 = "QUER O LINK?"; l3 = "comenta a palavra ↓"; }
          else if (e.tipo === "titulo_pixel") { l1 = e.linhas.slice(0, -1).map((l) => l.texto).join(" "); l2 = e.linhas[e.linhas.length - 1].texto; }
          else if (e.tipo === "contador") { l1 = "ESTRELAS"; l2 = "NO GITHUB"; }
          else if (e.tipo === "cadeia") { l1 = "COMO"; l2 = "FUNCIONA"; }
          else if (e.tipo === "lista") { l1 = "TUDO"; l2 = "INCLUSO"; }
          else if (e.tipo === "terminal") { l1 = "COMO"; l2 = "RODAR"; }
          else { l1 = e.rotulo || ""; }
          [["l1", l1], ["l2", l2], ["l3", l3]].forEach(([cl, txt]) => {
            if (!txt) return; const d = document.createElement("div"); d.className = cl; tit.appendChild(d);
            if (cl === "l3") { d.textContent = txt; return; }
            [...txt].forEach((ch) => { const s = document.createElement("span"); s.className = "ch"; s.textContent = ch === " " ? " " : ch; d.appendChild(s); });
          });
          const t0 = c.inicio + 0.05;
          tl.set(tit, { opacity: 1 }, t0);
          tl.fromTo(tit.querySelectorAll(".ch"), { opacity: 0, y: 60, rotateX: -90 }, { opacity: 1, y: 0, rotateX: 0, duration: 0.5, stagger: 0.025, ease: "back.out(2)" }, t0);
          const l3el = tit.querySelector(".l3"); if (l3el) tl.fromTo(l3el, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t0 + 0.4);
          tl.to(tit, { opacity: 0, y: -30, duration: 0.15 }, c.inicio + c.duracao - 0.15);
          if (p.numero) { tl.fromTo(numero, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(2)" }, e.t + 0.15); tl.to(numero, { opacity: 0, duration: 0.15 }, c.inicio + c.duracao - 0.15); }
          if (p.cta) tl.fromTo("#comentario", { opacity: 0, y: 80 }, { opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }, p.cta[0]);
        });
        // legenda palavra por palavra
        const caixa = document.getElementById("legenda");
        const dest = new Set((D.destaques || []).map((p) => p.toLowerCase()));
        const limpa = (p) => p.toLowerCase().replace(/[^a-zà-ú0-9]/g, "");
        D.legenda.forEach((b) => {
          const bl = document.createElement("div"); bl.className = "bloco"; caixa.appendChild(bl);
          const ps = b.texto.split(" "); let alvo = ps.findIndex((p) => dest.has(limpa(p)));
          if (alvo < 0) { let m = 0; ps.forEach((p, i) => { if (limpa(p).length > m) { m = limpa(p).length; alvo = i; } }); }
          const passo = Math.min(0.2, (b.fim - b.t) / (ps.length + 1));
          ps.forEach((p, i) => { const s = document.createElement("span"); s.className = i === alvo ? "w dest" : "w"; s.textContent = p; bl.appendChild(s);
            tl.fromTo(s, { opacity: 0, y: 24, scale: i === alvo ? 1.3 : 1 }, { opacity: 1, y: 0, scale: 1, duration: 0.22, ease: "back.out(2.5)" }, b.t + i * passo); });
          tl.set(bl, { opacity: 1 }, b.t); tl.set(bl, { opacity: 0 }, b.fim);
        });
        // relógio do 3D: um tween que cobre o vídeo inteiro e redesenha a cena a cada busca
        const relogio = { t: 0 };
        tl.to(relogio, { t: D.duracao, duration: D.duracao, ease: "none", onUpdate: () => desenhar(tl.time()) }, 0);
        window.__timelines = window.__timelines || {};
        window.__timelines["main"] = tl;
      }

      function desenhar(t) {
        let ativo = PLANOS[0];
        PLANOS.forEach((p) => { const on = t >= p.c.inicio && t < p.c.inicio + p.c.duracao; p.g.visible = on; if (on) ativo = p; });
        if (!ativo) return;
        ativo.g.visible = true;
        const u = local(ativo.c, t);
        ativo.render(t, u);
        // corte: nos primeiros 0,25 s de cada plano a câmera chega com um "puxão" extra
        const k = 1 - ease((t - ativo.c.inicio) / 0.35);
        cam.position.z += k * 3; cam.fov = 42 + k * 18; cam.updateProjectionMatrix();
        poeira.rotation.y = t * 0.02; poeira.position.z = (t * 0.8) % 20;
        chao.position.z = (t * 1.5) % 2;
        brilhoChao.material.opacity = 0.35 + 0.15 * Math.sin(t * 2);
        renderer.render(cena, cam);
      }

      window.__hf = window.__hf || {};
      window.__hf.buildReady = window.__hf.buildReady || {};
      const icones = new Set();
      D.cenas.forEach((c) => c.elementos.forEach((e) => { (e.nos || []).forEach((n) => icones.add([n.icone, css(HEXC[n.cor] || VERMELHO)])); if (e.icone) icones.add([e.icone, css(HEXC[e.cor] || VERMELHO)]); }));
      icones.add(["sparkles", css(VERMELHO)]);
      window.__hf.buildReady.cena3d = document.fonts.ready
        .then(() => Promise.all([...icones].map(([n, c]) => carregarIcone(n, c))))
        .then(() => { montar(); desenhar(0); });
      window.addEventListener("hf-seek", (ev) => desenhar(ev.detail.time));
    </script>
  </body>
</html>
