// Motor do PALCO (identidade com direção): robô de vinil com rosto de tela que ATUA em cada frase, mundos que
// mudam com o tema, acervo de objetos que entram por cena, câmera sempre em movimento, HUD de estado, legenda de
// uma palavra em chip, pílula de título e fechamento com caixa de comentário.
// Entradas: window.ROT (storyboard do diretor), window.ESQ (falas com tempo por palavra + envelope da boca),
// window.CATALOGO (o que existe). Tudo é função do tempo t: desenhar(t) é chamado pela timeline do HyperFrames,
// então qualquer quadro renderiza igual (nada de Math.random sem semente, nada de relógio).
(function () {
  const ROT = window.ROT, E = window.ESQ, F = E.falas, FIM = E.duracao, W = 1080, H = 1920;
  const CEN = ROT.cenas;
  const ini = F.map((f, i) => (i === 0 ? 0 : f.t - 0.12));
  const fimCena = (i) => ini[i + 1] ?? FIM;
  const cenaEm = (t) => { let i = 0; while (i + 1 < ini.length && t >= ini[i + 1]) i++; return i; };

  // ---------- utilidades determinísticas ----------
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const seg = (t, a, b) => clamp((t - a) / (b - a));
  const suave = (x) => x * x * (3 - 2 * x);
  const suave5 = (x) => x * x * x * (x * (x * 6 - 15) + 10);
  const backOut = (x, s = 1.9) => 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2;
  const pulso = (t, a, b) => (t < a || t > b ? 0 : Math.sin(Math.PI * (t - a) / (b - a)));
  const mix = (a, b, x) => a + (b - a) * x;
  const hash = (n) => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  let semente = 11; const rnd = () => (semente = (semente * 16807) % 2147483647) / 2147483647;

  // ---------- renderizador ----------
  if (THREE.ColorManagement) THREE.ColorManagement.legacyMode = false; // cores dos materiais em sRGB (sem isso tudo sai lavado)
  const canvas = document.getElementById("gl");
  // a página de verificação do HyperFrames pode não ter WebGL: sem contexto, o motor segue (timeline registrada) e só não desenha
  let r; try { r = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true }); }
  catch (e) { console.error('palco: sem WebGL nesta página'); r = { setSize() {}, setPixelRatio() {}, render() {}, shadowMap: {}, semGL: true }; }
  r.setSize(W, H, false); r.setPixelRatio(1);
  r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
  r.outputEncoding = THREE.sRGBEncoding; r.toneMapping = THREE.NoToneMapping;
  const cena = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(40, W / H, 0.1, 400);
  const hemi = new THREE.HemisphereLight(0xffffff, 0xcfc4e0, 0.55); cena.add(hemi);
  const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(-5, 11, 8); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024); Object.assign(key.shadow.camera, { left: -9, right: 9, top: 9, bottom: -9, far: 40 }); key.shadow.bias = -0.0004; key.shadow.radius = 6;
  cena.add(key);
  const fill = new THREE.DirectionalLight(0xdfe6ff, 0.55); fill.position.set(6, 3, 6); cena.add(fill);
  const rim = new THREE.DirectionalLight(0xffffff, 1.1); rim.position.set(0, 6, -8); cena.add(rim);

  // materiais "vinil de brinquedo": fosco-acetinado, nunca metálico
  const vinil = (c, rough = 0.45) => new THREE.MeshPhysicalMaterial({ color: c, roughness: rough, metalness: 0, clearcoat: 0.3, clearcoatRoughness: 0.45 });
  const fosco = (c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85, metalness: 0 });
  const brilho = (c) => new THREE.MeshBasicMaterial({ color: c });
  const sombra = (m) => { m.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); return m; };
  const malha = (geo, matl, x = 0, y = 0, z = 0, pai) => { const m = new THREE.Mesh(geo, matl); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; if (pai) pai.add(m); return m; };
  function rbox(w, h, d, rr) { // caixa de cantos arredondados (extrusão de retângulo arredondado com bisel)
    rr = Math.min(rr, w / 2 - 0.01, h / 2 - 0.01); const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
    s.moveTo(x + rr, y); s.lineTo(x + w - rr, y); s.quadraticCurveTo(x + w, y, x + w, y + rr); s.lineTo(x + w, y + h - rr);
    s.quadraticCurveTo(x + w, y + h, x + w - rr, y + h); s.lineTo(x + rr, y + h); s.quadraticCurveTo(x, y + h, x, y + h - rr);
    s.lineTo(x, y + rr); s.quadraticCurveTo(x, y, x + rr, y);
    const b = Math.min(rr * 0.8, d / 2 - 0.01);
    const g = new THREE.ExtrudeGeometry(s, { depth: Math.max(0.01, d - 2 * b), bevelEnabled: true, bevelThickness: b, bevelSize: b * 0.9, bevelSegments: 5, curveSegments: 10 });
    g.translate(0, 0, -(d - 2 * b) / 2); g.computeVertexNormals(); return g;
  }
  const bola = (rad, matl, x, y, z, pai, sx = 1, sy = 1, sz = 1) => { const m = malha(new THREE.SphereGeometry(rad, 32, 24), matl, x, y, z, pai); m.scale.set(sx, sy, sz); return m; };
  const cil = (rt, rb, h, matl, x, y, z, pai, seg_ = 24) => malha(new THREE.CylinderGeometry(rt, rb, h, seg_), matl, x, y, z, pai);

  // texturas de texto (canvas); refeitas quando as fontes terminam de carregar
  const FONTE = '"Titulo", "Archivo Black", Impact, sans-serif';
  const texturas = [];
  function texTexto(w, h, pintar) { const c = document.createElement("canvas"); c.width = w; c.height = h; const g = c.getContext("2d");
    const tex = new THREE.CanvasTexture(c); tex.encoding = THREE.sRGBEncoding; tex.anisotropy = 4; const item = { c, g, tex, pintar }; pintar(g, w, h); tex.needsUpdate = true; texturas.push(item); return tex; }
  function caber(g, txt, maxW, tam, peso = "") { g.font = `${peso}${tam}px ${FONTE}`; while (g.measureText(txt).width > maxW && tam > 12) { tam -= 2; g.font = `${peso}${tam}px ${FONTE}`; } return tam; }
  function linhas(txt, max) { const ps = String(txt || "").split(/\s+/), ls = [""]; ps.forEach((p) => { if ((ls[ls.length - 1] + " " + p).trim().length > max) ls.push(p); else ls[ls.length - 1] = (ls[ls.length - 1] + " " + p).trim(); }); return ls.filter(Boolean).slice(0, 3); }
  if (document.fonts) document.fonts.ready.then(() => { texturas.forEach((it) => { it.pintar(it.g, it.c.width, it.c.height); it.tex.needsUpdate = true; }); });

  const COR = { roxo: "#6c4bd8", azul: "#3f7fe0", amarelo: "#f6c445", verde: "#3fbf7f", rosa: "#ef5d8f", laranja: "#f08a3c", preto: "#15151c", branco: "#f3f0ea" };

  // ======================================================================
  // MUNDOS
  // ======================================================================
  const mundos = {};
  const MUNDO_CFG = {
    palco: { fundo: "#2a1840", nevoa: "#2a1840", key: 1.9, hemi: 0.5, keyCor: 0xfff1de },
    oficina: { fundo: "#3a2a22", nevoa: "#3a2a22", key: 2.0, hemi: 0.6, keyCor: 0xffe2b8 },
    noir: { fundo: "#141414", nevoa: "#141414", key: 2.4, hemi: 0.25, keyCor: 0xffffff },
    apartamento: { fundo: "#f1e6d6", nevoa: "#f1e6d6", key: 2.0, hemi: 0.7, keyCor: 0xfff4e0 },
    espaco: { fundo: "#070a1c", nevoa: "#070a1c", key: 2.1, hemi: 0.35, keyCor: 0xdde6ff },
    laboratorio: { fundo: "#7fcfc2", nevoa: "#7fcfc2", key: 1.8, hemi: 0.6, keyCor: 0xffffff },
    escritorio: { fundo: "#2f4a7a", nevoa: "#2f4a7a", key: 2.0, hemi: 0.6, keyCor: 0xfff1dc },
    cidade: { fundo: "#9fd0f2", nevoa: "#bfe0f6", key: 2.2, hemi: 0.7, keyCor: 0xfff2d8 },
    auditorio: { fundo: "#120c2a", nevoa: "#120c2a", key: 2.1, hemi: 0.4, keyCor: 0xffffff },
    cor: { fundo: "#6c4bd8", nevoa: "#6c4bd8", key: 1.9, hemi: 0.75, keyCor: 0xffffff },
    ilha: { fundo: "#8fd3ff", nevoa: "#bfe6ff", key: 2.2, hemi: 0.75, keyCor: 0xfff2d8 },
  };
  function piso(cor1, cor2, listras = 14) { return texTexto(512, 512, (g) => { for (let i = 0; i < listras; i++) { g.fillStyle = i % 2 ? cor1 : cor2; g.fillRect(i * 512 / listras, 0, 512 / listras + 1, 512); }
    g.strokeStyle = "rgba(0,0,0,.18)"; g.lineWidth = 2; for (let i = 0; i <= listras; i++) { g.beginPath(); g.moveTo(i * 512 / listras, 0); g.lineTo(i * 512 / listras, 512); g.stroke(); } }); }
  function chao(grupo, matl, w = 60, d = 40) { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), matl); m.rotation.x = -Math.PI / 2; m.receiveShadow = true; grupo.add(m); return m; }
  function parede(grupo, matl, z = -6, w = 60, h = 30) { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), matl); m.position.set(0, h / 2 - 1, z); m.receiveShadow = true; grupo.add(m); return m; }
  const lampadas = []; // brilho que pisca/acende

  const CONSTRUTOR = {
    palco(g) {
      chao(g, new THREE.MeshStandardMaterial({ map: piso("#8a4f2c", "#7a4426"), roughness: 0.7 }));
      const cortina = new THREE.Group(); g.add(cortina);
      for (let i = 0; i < 44; i++) { const c = cil(0.42, 0.42, 26, fosco(i % 2 ? "#5b2d9e" : "#4e258a"), -22 + i, 12, -6.5, cortina, 12); c.castShadow = false; }
      for (let i = 0; i < 26; i++) { const x = -12 + i * 0.95, y = 9.2 - Math.sin((i / 25) * Math.PI) * 1.4;
        const b = bola(0.13, brilho("#ffd98a"), x, y, -4.5, g); lampadas.push(b); }
      const fio = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(Array.from({ length: 26 }, (_, i) => new THREE.Vector3(-12 + i * 0.95, 9.35 - Math.sin((i / 25) * Math.PI) * 1.4, -4.5))), 60, 0.025, 6), fosco("#222")); g.add(fio);
      const spot = new THREE.Mesh(new THREE.ConeGeometry(4.2, 14, 40, 1, true), new THREE.MeshBasicMaterial({ color: 0xfff3d0, transparent: true, opacity: 0.07, depthWrite: false, side: THREE.DoubleSide }));
      spot.position.set(0, 7, -0.5); g.add(spot);
    },
    oficina(g) {
      chao(g, new THREE.MeshStandardMaterial({ map: piso("#6e4a32", "#5f3f2a", 10), roughness: 0.8 }));
      const tex = texTexto(512, 512, (c) => { c.fillStyle = "#c9a27a"; c.fillRect(0, 0, 512, 512); c.fillStyle = "#8a6a4a"; for (let y = 16; y < 512; y += 32) for (let x = 16; x < 512; x += 32) { c.beginPath(); c.arc(x, y, 4, 0, 7); c.fill(); } });
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(4, 3);
      parede(g, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9 }), -5.5);
      const banc = new THREE.Group(); banc.position.set(-4.5, 0, -3.6); g.add(banc);
      malha(rbox(5, 0.35, 1.6, 0.08), vinil("#8b5a2b"), 0, 2.1, 0, banc); [-2.2, 2.2].forEach((x) => malha(rbox(0.3, 2.1, 1.2, 0.08), vinil("#5a3a1e"), x, 1.05, 0, banc));
      const cores = ["#e74c3c", "#3498db", "#f1c40f", "#2ecc71", "#e67e22"];
      for (let i = 0; i < 9; i++) { const x = -7 + i * 1.6, y = 5 + (i % 3) * 1.2; const f = malha(rbox(0.22, 1.4, 0.15, 0.06), vinil(cores[i % 5]), x, y, -5.3, g); malha(rbox(0.6, 0.35, 0.18, 0.08), vinil("#444"), x, y + 0.85, -5.3, g); }
      const lamp = bola(0.35, brilho("#ffe8a0"), 3.5, 7.5, -3, g); lampadas.push(lamp);
      cil(0.02, 0.02, 3, fosco("#222"), 3.5, 9.2, -3, g);
      const luz = new THREE.PointLight(0xffd59a, 0.8, 14); luz.position.set(3.5, 7, -2.5); g.add(luz);
    },
    noir(g) {
      chao(g, fosco("#2a2a2a"));
      const tex = texTexto(512, 512, (c) => { c.fillStyle = "#3a3a3a"; c.fillRect(0, 0, 512, 512); c.fillStyle = "#d8d8d8"; for (let i = 0; i < 9; i++) { c.save(); c.translate(256, 0); c.transform(1, 0, -0.35, 1, 0, 0); c.fillRect(-160 + i * 0, 60 + i * 44, 360, 22); c.restore(); } });
      parede(g, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.95 }), -5.5);
      const mesa = new THREE.Group(); mesa.position.set(-4.2, 0, -2.8); g.add(mesa);
      malha(rbox(4, 0.3, 2, 0.06), fosco("#3b3b3b"), 0, 2.2, 0, mesa); [-1.7, 1.7].forEach((x) => malha(rbox(0.25, 2.2, 1.6, 0.05), fosco("#2e2e2e"), x, 1.1, 0, mesa));
      cil(0.06, 0.06, 1.2, fosco("#555"), 1, 2.9, 0, mesa); const cup = cil(0.2, 0.55, 0.5, fosco("#4a4a4a"), 1.3, 3.5, 0, mesa); cup.rotation.z = -0.6;
      const lamp = bola(0.18, brilho("#fffbe8"), 1.45, 3.35, 0, mesa); lampadas.push(lamp);
      const fum = new THREE.Mesh(new THREE.PlaneGeometry(30, 20), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.035, depthWrite: false })); fum.position.set(0, 6, -2); g.add(fum);
    },
    apartamento(g) {
      chao(g, new THREE.MeshStandardMaterial({ map: piso("#c99a6b", "#bb8c5f", 12), roughness: 0.75 }));
      parede(g, fosco("#efe2cf"), -5.5); const lat = parede(g, fosco("#e6d4bd"), 0); lat.rotation.y = Math.PI / 2; lat.position.set(-8, 14, 0);
      const tapete = malha(new THREE.CylinderGeometry(4, 4, 0.04, 48), fosco("#4f7bd1"), 0, 0.02, 0.5, g);
      const sofa = new THREE.Group(); sofa.position.set(-4.6, 0, -3.6); g.add(sofa);
      malha(rbox(4.6, 1, 1.6, 0.3), vinil("#e0764f"), 0, 0.8, 0, sofa); malha(rbox(4.6, 1.4, 0.5, 0.25), vinil("#d4683f"), 0, 1.6, -0.6, sofa);
      const tv = new THREE.Group(); tv.position.set(4.6, 0, -4.4); g.add(tv);
      malha(rbox(3, 1, 1, 0.1), vinil("#7a5235"), 0, 0.5, 0, tv); malha(rbox(3.6, 2.1, 0.2, 0.08), vinil("#1d1d22"), 0, 2.4, 0, tv);
      malha(new THREE.PlaneGeometry(3.3, 1.8), brilho("#3b5bd6"), 0, 2.4, 0.12, tv);
      const vaso = cil(0.35, 0.28, 0.7, vinil("#d9d2c4"), 7, 0.35, -3, g); bola(0.8, vinil("#3e9a57"), 7, 1.4, -3, g, 1, 1.2, 1);
      const jan = malha(new THREE.PlaneGeometry(3, 2.4), brilho("#bfe3ff"), -1, 5.6, -5.45, g); malha(rbox(3.3, 0.15, 0.2, 0.05), vinil("#fff"), -1, 5.6, -5.4, g);
    },
    espaco(g) {
      const pts = new THREE.BufferGeometry(), pos = []; for (let i = 0; i < 900; i++) { pos.push((rnd() - 0.5) * 120, rnd() * 70 - 10, -20 - rnd() * 40); }
      pts.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); g.add(new THREE.Points(pts, new THREE.PointsMaterial({ color: 0xffffff, size: 0.18 })));
      const pl = bola(5, vinil("#7b5cf0", 0.6), 9, 9, -22, g); const anel = new THREE.Mesh(new THREE.TorusGeometry(7.5, 0.35, 12, 64), vinil("#f0c86b")); anel.position.copy(pl.position); anel.rotation.x = 1.2; g.add(anel);
      const lua = bola(1.6, vinil("#cfd3e6", 0.8), -9, 12, -16, g);
      const base = malha(new THREE.CylinderGeometry(6, 6.5, 0.6, 40), vinil("#3a3f5c"), 0, -0.3, 0, g);
      for (let i = 0; i < 6; i++) bola(0.3 + rnd() * 0.5, vinil("#5b6280", 0.7), -8 + rnd() * 16, 3 + rnd() * 8, -6 - rnd() * 6, g);
    },
    laboratorio(g) {
      chao(g, new THREE.MeshStandardMaterial({ map: piso("#d9ece9", "#c8e0dc", 8), roughness: 0.6 }));
      parede(g, fosco("#5fb8ab"), -5.5);
      const est = new THREE.Group(); est.position.set(-4, 0, -4.8); g.add(est);
      for (let k = 0; k < 3; k++) { malha(rbox(5, 0.18, 1, 0.05), vinil("#ffffff"), 0, 2 + k * 1.6, 0, est);
        for (let j = 0; j < 4; j++) { const c = ["#3fbf7f", "#ef5d8f", "#3f7fe0", "#f6c445"][(j + k) % 4]; cil(0.22, 0.32, 0.7, new THREE.MeshPhysicalMaterial({ color: c, transmission: 0, roughness: 0.2, clearcoat: 1, transparent: true, opacity: 0.8 }), -1.8 + j * 1.2, 2.45 + k * 1.6, 0, est); } }
      malha(rbox(4, 1.6, 1.6, 0.15), vinil("#ffffff"), 4.5, 0.8, -3.5, g);
    },
    escritorio(g) {
      chao(g, new THREE.MeshStandardMaterial({ map: piso("#b7794a", "#a86d42", 12), roughness: 0.75 }));
      parede(g, fosco("#3d5f98"), -5.5);
      const jan = malha(new THREE.PlaneGeometry(9, 4.5), brilho("#ffb37a"), 0, 6.4, -5.45, g);
      for (let i = 0; i < 9; i++) malha(new THREE.PlaneGeometry(0.8, 1 + hash(i) * 3), brilho("#3a2a5a"), -4 + i, 4.6 + hash(i) * 1.5, -5.4, g);
      const mesa = new THREE.Group(); mesa.position.set(-4.6, 0, -2.8); g.add(mesa);
      malha(rbox(4.4, 0.25, 2, 0.06), vinil("#f2f2f2"), 0, 2.2, 0, mesa); [-2, 2].forEach((x) => malha(rbox(0.2, 2.2, 1.8, 0.05), vinil("#9aa4b4"), x, 1.1, 0, mesa));
      malha(rbox(2.2, 1.4, 0.15, 0.08), vinil("#22262e"), 0, 3.3, -0.4, mesa); malha(new THREE.PlaneGeometry(2, 1.2), brilho("#56c2ff"), 0, 3.3, -0.31, mesa);
      bola(0.7, vinil("#3e9a57"), 6.5, 1.4, -3.5, g, 1, 1.3, 1); cil(0.4, 0.3, 0.8, vinil("#fff"), 6.5, 0.4, -3.5, g);
    },
    cidade(g) {
      chao(g, fosco("#7fbf5f"), 140, 140);
      const praca = malha(new THREE.CylinderGeometry(7, 7, 0.06, 48), fosco("#d8c39a"), 0, 0.03, 0, g);
      const cores = ["#f08a3c", "#3f7fe0", "#ef5d8f", "#f6c445", "#3fbf7f", "#ffffff", "#8e6bd8"];
      for (let i = 0; i < 26; i++) { const a = Math.PI * (1.05 + 0.9 * i / 25), R = 13 + (i % 3) * 4, h = 3 + hash(i) * 9;
        const p = malha(rbox(2.6, h, 2.6, 0.3), vinil(cores[i % 7]), Math.cos(a) * R, h / 2, Math.sin(a) * R * 0.8 - 3, g);
        for (let k = 0; k < Math.floor(h / 1.4); k++) malha(new THREE.PlaneGeometry(1.6, 0.5), brilho("#fff6c8"), p.position.x, 1 + k * 1.3, p.position.z + 1.32, g); }
      for (let i = 0; i < 14; i++) { const x = -10 + i * 1.6; cil(0.12, 0.15, 1, vinil("#6b4423"), x, 0.5, 6, g); bola(0.6, vinil("#3e9a57"), x, 1.4, 6, g); }
    },
    auditorio(g) {
      chao(g, new THREE.MeshStandardMaterial({ color: "#241a4a", roughness: 0.3, metalness: 0 }));
      const led = texTexto(512, 512, (c) => { c.fillStyle = "#0d0920"; c.fillRect(0, 0, 512, 512); for (let y = 8; y < 512; y += 16) for (let x = 8; x < 512; x += 16) { c.fillStyle = (x + y) % 48 === 0 ? "#ff5fa2" : (x * y) % 7 === 0 ? "#5fd0ff" : "#2a1f55"; c.beginPath(); c.arc(x, y, 5, 0, 7); c.fill(); } });
      led.wrapS = led.wrapT = THREE.RepeatWrapping; led.repeat.set(3, 2);
      parede(g, new THREE.MeshBasicMaterial({ map: led }), -6);
      const podio = new THREE.Group(); podio.position.set(0, 0, -2.6); g.add(podio);
      [[0, 1.6, "#f6c445", "1"], [-2.4, 1.0, "#c7ccd8", "2"], [2.4, 0.7, "#e08a4c", "3"]].forEach(([x, h, c, n]) => {
        malha(rbox(2.2, h, 1.8, 0.12), vinil(c), x, h / 2, 0, podio);
        const tex = texTexto(128, 128, (cc) => { cc.clearRect(0, 0, 128, 128); cc.fillStyle = "#1b1b2a"; cc.font = `100px ${FONTE}`; cc.textAlign = "center"; cc.fillText(n, 64, 106); });
        malha(new THREE.PlaneGeometry(0.9, 0.9), new THREE.MeshBasicMaterial({ map: tex, transparent: true }), x, h / 2, 0.92, podio); });
      for (let i = 0; i < 8; i++) { const s = new THREE.Mesh(new THREE.ConeGeometry(1.6, 12, 24, 1, true), new THREE.MeshBasicMaterial({ color: i % 2 ? 0xff7ac0 : 0x7ad8ff, transparent: true, opacity: 0.06, depthWrite: false, side: THREE.DoubleSide }));
        s.position.set(-10 + i * 2.9, 8, -4); s.rotation.z = (i - 3.5) * 0.08; g.add(s); }
    },
    ilha(g) {
      const mar = new THREE.Mesh(new THREE.PlaneGeometry(300, 300), vinil("#2f9fd8", 0.3)); mar.rotation.x = -Math.PI / 2; mar.position.y = -0.35; mar.receiveShadow = true; g.add(mar); g.userData.mar = mar;
      const areia = malha(new THREE.CylinderGeometry(7.5, 8.6, 0.8, 48), vinil("#f1d59a", 0.8), 0, -0.05, 0, g);
      malha(new THREE.CylinderGeometry(9.2, 9.4, 0.1, 48), new THREE.MeshBasicMaterial({ color: 0xbfeaff, transparent: true, opacity: 0.6 }), 0, -0.3, 0, g);
      const coqueiro = (x, z, inc) => { const tr = new THREE.Group(); tr.position.set(x, 0.3, z); tr.rotation.z = inc; g.add(tr);
        for (let k = 0; k < 6; k++) cil(0.22 - k * 0.02, 0.26 - k * 0.02, 0.8, vinil("#a8743e"), 0, 0.4 + k * 0.75, 0, tr, 10);
        for (let k = 0; k < 6; k++) { const f = malha(new THREE.ConeGeometry(0.45, 2.6, 6), vinil("#3e9a57"), 0, 4.8, 0, tr); f.rotation.set(1.25, k * 1.05, 0); f.position.set(Math.sin(k * 1.05) * 1, 4.7, Math.cos(k * 1.05) * 1); } };
      coqueiro(-5.2, -3.5, 0.15); coqueiro(5.5, -2.8, -0.2); coqueiro(-4.5, 3.6, 0.1);
      const fogo = new THREE.Group(); fogo.position.set(0, 0.35, 0); g.add(fogo);
      for (let k = 0; k < 5; k++) { const l = cil(0.12, 0.12, 1.3, vinil("#6b4423"), 0, 0.1, 0, fogo, 8); l.rotation.set(Math.PI / 2, 0, k * 1.26); }
      const chama = malha(new THREE.ConeGeometry(0.45, 1.2, 12), brilho("#ffb03b"), 0, 0.7, 0, fogo); const chama2 = malha(new THREE.ConeGeometry(0.28, 0.8, 12), brilho("#fff1a0"), 0, 0.6, 0, fogo);
      const luzF = new THREE.PointLight(0xffa040, 1.2, 9); luzF.position.set(0, 1.4, 0); fogo.add(luzF); g.userData.chamas = [chama, chama2, luzF];
      const pilha = new THREE.Group(); pilha.position.set(3.2, 0.35, 2.4); g.add(pilha); g.userData.pilha = [];
      for (let k = 0; k < 16; k++) { const cx = malha(rbox(0.62, 0.5, 0.62, 0.06), vinil(k % 2 ? "#c99556" : "#b9854a"), (k % 4) * 0.66 - 1, 0.25 + Math.floor(k / 8) * 0.52, Math.floor((k % 8) / 4) * 0.66, pilha); g.userData.pilha.push(cx); }
      const navio = new THREE.Group(); g.add(navio); malha(rbox(4.5, 1.2, 1.8, 0.4), vinil("#f3f0ea"), 0, 0.3, 0, navio); malha(rbox(1.8, 1, 1.4, 0.2), vinil("#ef5d8f"), -0.5, 1.3, 0, navio);
      cil(0.18, 0.18, 1.2, vinil("#333"), 0.6, 2, 0, navio); navio.visible = false; g.userData.navio = navio;
    },
    cor(g) {
      const m = new THREE.MeshStandardMaterial({ color: "#6c4bd8", roughness: 0.9 });
      const cic = new THREE.Mesh(new THREE.CylinderGeometry(30, 30, 40, 64, 1, true, Math.PI * 0.5, Math.PI), m); cic.material.side = THREE.BackSide; cic.position.set(0, 19.9, 10); g.add(cic);
      const ch = chao(g, m, 120, 120); g.userData.matCor = m;
    },
  };
  const usados = new Set([ROT.mundo || "palco", ...CEN.map((c) => c.mundo).filter(Boolean)]);
  usados.forEach((n) => { if (!CONSTRUTOR[n]) return; const g = new THREE.Group(); g.visible = false; CONSTRUTOR[n](g); sombra(g); cena.add(g); mundos[n] = g; });
  if (!mundos.palco) { const g = new THREE.Group(); g.visible = false; CONSTRUTOR.palco(g); sombra(g); cena.add(g); mundos.palco = g; }

  // ======================================================================
  // ROBÔ (marca fixa): corpo coral, cabeça creme com tela de rosto, antena
  // ======================================================================
  const C = { corpo: "#e85a3c", barriga: "#ff9d80", cabeca: "#efe4d2", tela: "#1b2530", olho: "#63f5ad", perna: "#3a3f4a" };
  const robo = new THREE.Group(); cena.add(robo);
  const corpo = new THREE.Group(); robo.add(corpo);
  malha(rbox(1.5, 1.25, 1.15, 0.42), vinil(C.corpo), 0, 1.15, 0, corpo);
  malha(rbox(0.85, 0.6, 0.2, 0.25), vinil(C.barriga, 0.5), 0, 1.1, 0.55, corpo);
  const pernas = [-0.36, 0.36].map((x) => { const p = new THREE.Group(); p.position.set(x, 0.62, 0); corpo.add(p);
    malha(new THREE.CapsuleGeometry(0.17, 0.32, 8, 16), vinil(C.perna), 0, -0.25, 0, p); bola(0.24, vinil(C.perna), 0, -0.5, 0.09, p, 1, 0.6, 1.3); return p; });
  const cabeca = new THREE.Group(); cabeca.position.set(0, 2.72, 0); corpo.add(cabeca);
  malha(rbox(2.5, 1.95, 1.75, 0.55), vinil(C.cabeca), 0, 0, 0, cabeca);
  const rostoTex = texTexto(512, 384, () => {});
  const rosto = malha(new THREE.PlaneGeometry(2.0, 1.5), new THREE.MeshBasicMaterial({ map: rostoTex }), 0, -0.02, 0.89, cabeca); rosto.castShadow = false;
  cil(0.05, 0.05, 0.7, vinil("#9aa0a8"), 0, 1.25, 0, cabeca); const luzAntena = bola(0.17, brilho("#ff5a5a"), 0, 1.65, 0, cabeca);
  [-1.28, 1.28].forEach((x) => { const o = cil(0.32, 0.32, 0.18, vinil(C.corpo), x, 0, 0, cabeca); o.rotation.z = Math.PI / 2; });
  function braco(lado) { const p = new THREE.Group(); p.position.set(lado * 0.88, 1.55, 0.05); corpo.add(p);
    malha(new THREE.CapsuleGeometry(0.15, 0.55, 8, 16), vinil(C.corpo), 0, -0.38, 0, p); bola(0.22, vinil(C.barriga, 0.5), 0, -0.82, 0, p);
    const mao = new THREE.Object3D(); mao.position.set(0, -0.9, 0.12); p.add(mao); p.userData.mao = mao; return p; }
  const bE = braco(-1), bD = braco(1);
  sombra(robo);
  // sombra de contato (a sombra do sol sozinha não encolhe quando ele pula)
  const blobTex = texTexto(128, 128, (g) => { const rg = g.createRadialGradient(64, 64, 0, 64, 64, 64); rg.addColorStop(0, "rgba(20,10,30,.55)"); rg.addColorStop(1, "rgba(20,10,30,0)"); g.fillStyle = rg; g.fillRect(0, 0, 128, 128); });
  const blob = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1.6), new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false })); blob.rotation.x = -Math.PI / 2; blob.position.y = 0.015; cena.add(blob);

  // chapéus
  const chapeus = {};
  function fazChapeu(n) { const g = new THREE.Group(); g.position.set(0, 0.98, 0); cabeca.add(g); g.visible = false;
    if (n === "detetive") { cil(1.25, 1.25, 0.08, vinil("#2b2b2b"), 0, 0.05, 0, g, 40); cil(0.75, 0.85, 0.65, vinil("#333"), 0, 0.38, 0, g, 40); cil(0.86, 0.86, 0.14, vinil("#8a1d1d"), 0, 0.15, 0, g, 40); }
    if (n === "diretor") { bola(0.95, vinil("#a1203a"), -0.15, 0.12, 0, g, 1, 0.35, 1); bola(0.12, vinil("#a1203a"), -0.1, 0.42, 0, g); }
    if (n === "capacete") { const c = bola(1.05, vinil("#f6c445"), 0, 0, 0, g, 1, 0.6, 1); cil(1.3, 1.3, 0.06, vinil("#f6c445"), 0, 0, 0.1, g, 40); }
    if (n === "coroa") { cil(0.8, 0.8, 0.45, vinil("#f6c445", 0.3), 0, 0.22, 0, g, 8); for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283; bola(0.11, vinil("#ef5d8f"), Math.cos(a) * 0.8, 0.5, Math.sin(a) * 0.8, g); } }
    if (n === "fone") { const arc = new THREE.Mesh(new THREE.TorusGeometry(1.35, 0.1, 12, 40, Math.PI), vinil("#222")); arc.position.y = -0.45; g.add(arc); [-1.35, 1.35].forEach((x) => bola(0.36, vinil("#3f7fe0"), x, -0.6, 0, g, 0.6, 1, 1)); }
    if (n === "mago") { const c = malha(new THREE.ConeGeometry(0.8, 1.9, 32), vinil("#4b3fb8"), 0, 0.9, 0, g); cil(1.15, 1.15, 0.08, vinil("#4b3fb8"), 0, 0, 0, g, 40); bola(0.13, brilho("#ffe27a"), 0.15, 1.1, 0.5, g); }
    if (n === "cozinheiro") { cil(0.7, 0.65, 0.7, vinil("#ffffff"), 0, 0.35, 0, g, 30); bola(0.75, vinil("#ffffff"), 0, 0.85, 0, g, 1.05, 0.6, 1.05); }
    sombra(g); chapeus[n] = g; return g; }
  new Set([ROT.chapeu, ...CEN.map((c) => c.chapeu)].filter((c) => c && c !== "nenhum")).forEach(fazChapeu);

  // ---------- rosto na tela ----------
  const BOCA = E.boca || [];
  function falando(t) { const k = Math.floor(t * (E.fps || 30)); return BOCA[k] || 0; }
  function piscada(t) { // piscadas irregulares a cada ~2-4 s
    let base = 0.8; for (let n = 0; n < 40; n++) { base += 2 + hash(n + 3) * 2.2; if (t >= base && t < base + 0.13) return 1 - Math.abs((t - base) / 0.065 - 1); if (base > t) break; } return 0; }
  function pintaRosto(t, emocao, olhar) {
    const g = rostoTex.image.getContext("2d"), w = 512, h = 384;
    g.fillStyle = C.tela; g.fillRect(0, 0, w, h);
    const grd = g.createRadialGradient(256, 150, 30, 256, 192, 300); grd.addColorStop(0, "rgba(99,245,173,.10)"); grd.addColorStop(1, "rgba(0,0,0,0)"); g.fillStyle = grd; g.fillRect(0, 0, w, h);
    const ox = olhar.x * 26, oy = olhar.y * 18, pis = piscada(t), cor = emocao === "apaixonado" ? "#ff6fa4" : emocao === "bravo" ? "#ff7a5a" : C.olho;
    g.fillStyle = cor; g.strokeStyle = cor; g.lineCap = "round"; g.lineWidth = 26; g.shadowColor = cor; g.shadowBlur = 24;
    const olhos = [[170 + ox, 160 + oy], [342 + ox, 160 + oy]];
    olhos.forEach(([x, y], k) => {
      g.beginPath();
      if (emocao === "feliz" || emocao === "rindo") { g.arc(x, y + 18, 42, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); return; }
      if (emocao === "apaixonado") { const s = 1 + 0.08 * Math.sin(t * 10); g.save(); g.translate(x, y); g.scale(s, s); g.moveTo(0, 34); g.bezierCurveTo(-70, -10, -30, -60, 0, -22); g.bezierCurveTo(30, -60, 70, -10, 0, 34); g.fill(); g.restore(); return; }
      if (emocao === "triste") { g.arc(x, y - 6, 38, Math.PI * 0.15, Math.PI * 0.85); g.stroke(); if (k === 1) { g.fillStyle = "#7fd8ff"; g.beginPath(); g.arc(x + 20, y + 50 + (t * 40) % 40, 10, 0, 7); g.fill(); g.fillStyle = cor; } return; }
      const surpreso = emocao === "surpreso", alt = surpreso ? 120 : 92, lar = surpreso ? 92 : 62;
      const fech = Math.max(pis, emocao === "determinado" ? 0.35 : 0, emocao === "pensando" && k === 0 ? 0.45 : 0);
      const hh = Math.max(10, alt * (1 - fech));
      g.beginPath(); if (g.roundRect) g.roundRect(x - lar / 2, y - hh / 2, lar, hh, lar / 2); else g.rect(x - lar / 2, y - hh / 2, lar, hh); g.fill();
      if (emocao === "bravo") { g.fillStyle = C.tela; g.beginPath(); const d = k === 0 ? 1 : -1; g.moveTo(x - 60, y - 70 + d * 30); g.lineTo(x + 60, y - 70 - d * 30); g.lineTo(x + 60, y - 120); g.lineTo(x - 60, y - 120); g.fill(); g.fillStyle = cor; }
    });
    // boca: abre com o envelope da voz
    const ab = clamp(falando(t) * 1.3), bx = 256 + ox * 0.5, by = 282 + oy * 0.4;
    g.shadowBlur = 16;
    if (emocao === "rindo") { g.beginPath(); g.moveTo(bx - 60, by - 8); g.quadraticCurveTo(bx, by + 70 + ab * 20, bx + 60, by - 8); g.closePath(); g.fill(); }
    else if (emocao === "surpreso") { g.beginPath(); g.ellipse(bx, by + 6, 20 + ab * 10, 26 + ab * 18, 0, 0, 7); g.lineWidth = 12; g.stroke(); }
    else if (ab > 0.08) { g.beginPath(); if (g.roundRect) g.roundRect(bx - 40, by - 6, 80, 12 + ab * 46, 14); else g.rect(bx - 40, by - 6, 80, 12 + ab * 46); g.fill(); }
    else if (emocao === "triste" || emocao === "bravo") { g.beginPath(); g.lineWidth = 12; g.arc(bx, by + 34, 34, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); }
    else { g.beginPath(); g.lineWidth = 12; g.arc(bx, by - 26, 34, Math.PI * 0.2, Math.PI * 0.8); g.stroke(); }
    g.shadowBlur = 0;
    for (let y = 0; y < h; y += 6) { g.fillStyle = "rgba(255,255,255,.035)"; g.fillRect(0, y, w, 2); } // linhas de tela
    rostoTex.needsUpdate = true;
  }

  // ======================================================================
  // OBJETOS (acervo)
  // ======================================================================
  const TEXTO_OBJ = (c) => String(c.texto_objeto || "").toUpperCase();
  function telaTexto(c, fundo = "#0f1a2b", tinta = "#ffffff", destaque = "#63f5ad") {
    return texTexto(512, 800, (g, w, h) => { g.fillStyle = fundo; g.fillRect(0, 0, w, h);
      const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, "rgba(255,255,255,.08)"); gr.addColorStop(1, "rgba(0,0,0,.2)"); g.fillStyle = gr; g.fillRect(0, 0, w, h);
      g.fillStyle = destaque; g.fillRect(40, 60, 140, 16); g.fillStyle = "rgba(255,255,255,.25)"; g.fillRect(40, 96, 300, 12); g.fillRect(40, 122, 220, 12);
      const ls = linhas(TEXTO_OBJ(c) || "PRONTO", 9); g.textAlign = "center"; g.fillStyle = tinta;
      let tam = 110; ls.forEach((l) => { tam = Math.min(tam, caber(g, l, w - 70, 110)); });
      ls.forEach((l, k) => { g.font = `${tam}px ${FONTE}`; g.fillStyle = k === ls.length - 1 ? destaque : tinta; g.fillText(l, w / 2, 360 + k * (tam + 18) - (ls.length - 1) * (tam + 18) / 2); });
      for (let k = 0; k < 3; k++) { g.fillStyle = "rgba(255,255,255,.12)"; if (g.roundRect) { g.beginPath(); g.roundRect(40, 560 + k * 66, w - 80, 46, 14); g.fill(); } } }); }
  function placaTexto(w, h, txt, fundo, tinta, borda) { return texTexto(w, h, (g) => { g.fillStyle = fundo; g.fillRect(0, 0, w, h); if (borda) { g.strokeStyle = borda; g.lineWidth = 14; g.strokeRect(10, 10, w - 20, h - 20); }
    const ls = linhas(txt, 10); let tam = Math.floor(h * 0.42 / Math.max(1, ls.length) * 1.6); ls.forEach((l) => { tam = Math.min(tam, caber(g, l, w - 60, tam)); });
    g.fillStyle = tinta; g.textAlign = "center"; g.textBaseline = "middle"; ls.forEach((l, k) => { g.font = `${tam}px ${FONTE}`; g.fillText(l, w / 2, h / 2 + (k - (ls.length - 1) / 2) * tam * 1.08); }); }); }
  const num = (n) => { n = Number(n) || 0; return n >= 1e6 ? (n / 1e6).toFixed(1).replace(".0", "").replace(".", ",") + " MI" : n >= 1e4 ? Math.round(n / 1000) + " MIL" : n >= 1000 ? (n / 1000).toFixed(1).replace(".", ",") + " MIL" : String(Math.round(n)); };

  // cada construtor devolve {g, tam:'grande'|'pequeno', anima(lt, t)}
  const OBJ = {
    celular(c) { const g = new THREE.Group(); malha(rbox(1.7, 3.3, 0.22, 0.28), vinil("#20232b"), 0, 0, 0, g);
      malha(new THREE.PlaneGeometry(1.5, 2.95), new THREE.MeshBasicMaterial({ map: telaTexto(c) }), 0, 0, 0.12, g); bola(0.05, brilho("#555"), 0, 1.5, 0.12, g); return { g, tam: "grande" }; },
    notebook(c) { const g = new THREE.Group(); malha(rbox(3.2, 0.15, 2.1, 0.08), vinil("#c3c8d2"), 0, 0, 0, g);
      const tampa = new THREE.Group(); tampa.position.set(0, 0.07, -1.02); g.add(tampa); malha(rbox(3.2, 2.1, 0.12, 0.08), vinil("#b3b8c2"), 0, 1.05, 0, tampa);
      malha(new THREE.PlaneGeometry(2.95, 1.85), new THREE.MeshBasicMaterial({ map: placaTexto(640, 400, TEXTO_OBJ(c) || "PRONTO", "#101826", "#63f5ad") }), 0, 1.05, 0.07, tampa);
      for (let i = 0; i < 24; i++) malha(rbox(0.28, 0.05, 0.22, 0.03), vinil("#2b2f38"), -1.3 + (i % 8) * 0.37, 0.1, -0.5 + Math.floor(i / 8) * 0.33, g);
      return { g, tam: "grande", anima: (lt) => { tampa.rotation.x = -0.25 - 0.9 * (1 - backOut(seg(lt, 0, 0.5))); } }; },
    monitor(c) { const g = new THREE.Group(); malha(rbox(4.2, 2.7, 0.25, 0.15), vinil("#1f222a"), 0, 0.5, 0, g);
      malha(new THREE.PlaneGeometry(3.9, 2.4), new THREE.MeshBasicMaterial({ map: placaTexto(780, 480, TEXTO_OBJ(c) || "AO VIVO", "#141b33", "#ffffff") }), 0, 0.5, 0.14, g);
      cil(0.12, 0.12, 1, vinil("#444"), 0, -1.2, -0.1, g); malha(rbox(1.6, 0.12, 0.9, 0.05), vinil("#444"), 0, -1.7, -0.1, g); return { g, tam: "grande" }; },
    contador(c) { const g = new THREE.Group(); const alvo = Math.max(0, Math.round(Number(c.numero) || 0)), dig = Math.max(3, String(alvo).length);
      malha(rbox(dig * 0.78 + 0.5, 1.5, 0.7, 0.18), vinil("#1d1d24"), 0, 0, 0, g);
      const tex = texTexto(dig * 128, 160, () => {}); const pl = malha(new THREE.PlaneGeometry(dig * 0.78, 1.15), new THREE.MeshBasicMaterial({ map: tex }), 0, 0, 0.36, g);
      const rot = c.texto_objeto ? placaTexto(512, 96, TEXTO_OBJ(c), "#1d1d24", "#f6c445") : null; if (rot) malha(new THREE.PlaneGeometry(dig * 0.78, 0.3), new THREE.MeshBasicMaterial({ map: rot }), 0, -0.92, 0.36, g);
      let ultimo = -1; g.scale.setScalar(1); const larg = dig * 0.78 + 0.5; g.userData.fit = Math.min(1, 3.2 / larg);
      return { g, tam: "grande", anima: (lt) => { const v = Math.round(alvo * suave(seg(lt, 0.25, 1.6))); if (v === ultimo) return; ultimo = v;
        const cg = tex.image.getContext("2d"), s = String(v).padStart(dig, "0"); cg.fillStyle = "#0d0d12"; cg.fillRect(0, 0, dig * 128, 160);
        for (let k = 0; k < dig; k++) { cg.fillStyle = "#f4efe6"; cg.fillRect(k * 128 + 8, 8, 112, 144); cg.fillStyle = "#1b1b22"; cg.font = `120px ${FONTE}`; cg.textAlign = "center"; cg.fillText(s[k], k * 128 + 64, 128); cg.fillStyle = "rgba(0,0,0,.18)"; cg.fillRect(k * 128 + 8, 78, 112, 4); }
        tex.needsUpdate = true; } }; },
    grafico(c) { const g = new THREE.Group(); const barras = [], hs = [0.6, 1.0, 1.5, 2.3, 3.4];
      hs.forEach((h, k) => { const b = malha(rbox(0.55, 1, 0.55, 0.1), vinil(k === 4 ? "#3fbf7f" : "#8f7ae8"), -1.4 + k * 0.7, 0, 0, g); b.userData.h = h; barras.push(b); });
      const seta = new THREE.Group(); g.add(seta); malha(new THREE.ConeGeometry(0.3, 0.6, 16), vinil("#3fbf7f"), 0, 0, 0, seta);
      const rot = placaTexto(512, 140, c.numero ? "+" + num(c.numero) : TEXTO_OBJ(c) || "CRESCEU", "#ffffff", "#1b1b22"); const pl = malha(new THREE.PlaneGeometry(2.4, 0.66), new THREE.MeshBasicMaterial({ map: rot }), 0, 4.3, 0.2, g);
      return { g, tam: "grande", anima: (lt) => { barras.forEach((b, k) => { const u = backOut(seg(lt, 0.15 + k * 0.12, 0.6 + k * 0.12)); const h = Math.max(0.05, b.userData.h * u); b.scale.y = h; b.position.y = h / 2; });
        seta.position.set(1.4, 3.6 + Math.sin(lt * 6) * 0.08, 0); pl.scale.setScalar(backOut(seg(lt, 0.8, 1.2))); } }; },
    maquina(c) { const g = new THREE.Group(); malha(rbox(3.6, 2.2, 1.8, 0.25), vinil("#efe7da"), 0, 1.1, 0, g); malha(rbox(3.7, 0.3, 1.9, 0.1), vinil("#7a5ce0"), 0, 2.3, 0, g);
      const fun = malha(new THREE.CylinderGeometry(0.9, 0.25, 1.1, 32, 1, true), vinil("#7a5ce0"), -0.9, 3, 0, g); fun.material.side = THREE.DoubleSide;
      const engs = [[-0.9, 1.1], [0, 0.8], [0.9, 1.2]].map(([x, y]) => { const e = new THREE.Group(); e.position.set(x, y, 0.92); g.add(e); malha(new THREE.CylinderGeometry(0.42, 0.42, 0.12, 12), vinil("#8a8f99"), 0, 0, 0, e).rotation.x = Math.PI / 2;
        for (let k = 0; k < 10; k++) { const d = malha(new THREE.BoxGeometry(0.13, 0.16, 0.12), vinil("#8a8f99"), Math.cos(k * 0.628) * 0.48, Math.sin(k * 0.628) * 0.48, 0, e); d.rotation.z = k * 0.628; } return e; });
      const saida = new THREE.Group(); g.add(saida); malha(rbox(1.2, 0.8, 0.12, 0.08), vinil("#ef5d8f"), 0, 0, 0, saida);
      const pl = new THREE.Mesh(new THREE.PlaneGeometry(1.05, 0.65), new THREE.MeshBasicMaterial({ map: placaTexto(256, 160, TEXTO_OBJ(c) || "PRONTO", "#ef5d8f", "#ffffff") })); pl.position.z = 0.07; saida.add(pl);
      return { g, tam: "grande", anima: (lt) => { engs.forEach((e, k) => (e.rotation.z = lt * (k % 2 ? -3 : 3))); const u = seg(lt, 0.8, 1.5); saida.position.set(1.4 + u * 1.2, 0.9 + Math.sin(u * Math.PI) * 0.6, 0.5); saida.visible = lt > 0.8; saida.scale.setScalar(backOut(seg(lt, 0.8, 1.1))); } }; },
    martelo() { const g = new THREE.Group(); malha(new THREE.CapsuleGeometry(0.08, 1.2, 6, 12), vinil("#a8743e"), 0, 0.2, 0, g); malha(rbox(0.75, 0.4, 0.4, 0.08), vinil("#7d8592"), 0, 0.95, 0, g); return { g, tam: "pequeno", ferramenta: true }; },
    tesoura() { const g = new THREE.Group(); const l1 = new THREE.Group(), l2 = new THREE.Group(); g.add(l1, l2);
      [l1, l2].forEach((l, k) => { malha(rbox(0.12, 1.1, 0.05, 0.04), vinil("#d9dde4", 0.25), 0, 0.55, k * 0.05, l); const a = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.06, 10, 24), vinil(k ? "#ef5d8f" : "#3f7fe0")); a.position.set(0, -0.2, k * 0.05); l.add(a); });
      return { g, tam: "pequeno", ferramenta: true, anima: (lt) => { const a = 0.35 * Math.abs(Math.sin(lt * 7)); l1.rotation.z = a; l2.rotation.z = -a; } }; },
    lupa() { const g = new THREE.Group(); const aro = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.09, 16, 40), vinil("#2b2b33")); aro.position.y = 0.8; g.add(aro);
      malha(new THREE.CircleGeometry(0.52, 32), new THREE.MeshPhysicalMaterial({ color: 0xbfe7ff, roughness: 0.05, transparent: true, opacity: 0.35, clearcoat: 1 }), 0, 0.8, 0.01, g); malha(new THREE.CapsuleGeometry(0.08, 0.6, 6, 12), vinil("#a8743e"), 0, -0.05, 0, g); return { g, tam: "pequeno", ferramenta: true }; },
    carimbo(c) { const g = new THREE.Group(); malha(rbox(0.9, 0.3, 0.6, 0.08), vinil("#c0392b"), 0, 0, 0, g); cil(0.12, 0.12, 0.5, vinil("#5a3a1e"), 0, 0.4, 0, g); bola(0.22, vinil("#5a3a1e"), 0, 0.72, 0, g);
      return { g, tam: "pequeno", ferramenta: true, marca: TEXTO_OBJ(c) || "APROVADO" }; },
    caixa(c) { const g = new THREE.Group(); malha(rbox(1.8, 1.4, 1.5, 0.12), vinil("#c99556"), 0, 0.7, 0, g); malha(rbox(1.82, 0.08, 0.35, 0.02), vinil("#e6c08a"), 0, 1.4, 0, g);
      malha(new THREE.PlaneGeometry(1.2, 0.55), new THREE.MeshBasicMaterial({ map: placaTexto(320, 140, TEXTO_OBJ(c) || "FRÁGIL", "#fff8e6", "#1b1b22") }), 0, 0.75, 0.77, g); return { g, tam: "pequeno" }; },
    cadeado() { const g = new THREE.Group(); malha(rbox(1.2, 1, 0.5, 0.15), vinil("#f6c445", 0.3), 0, 0, 0, g); const arco = new THREE.Mesh(new THREE.TorusGeometry(0.38, 0.1, 12, 30, Math.PI), vinil("#9aa0a8", 0.3)); arco.position.y = 0.5; g.add(arco);
      bola(0.1, vinil("#333"), 0, 0.05, 0.26, g); return { g, tam: "pequeno", anima: (lt) => { const u = backOut(seg(lt, 0.7, 1.0)); arco.position.y = 0.5 + 0.35 * u; arco.rotation.y = -1.2 * u; } }; },
    moedas(c) { const g = new THREE.Group(); for (let k = 0; k < 4; k++) for (let j = 0; j < 3 + k % 2 * 2; j++) { const m = cil(0.38, 0.38, 0.12, vinil("#f6c445", 0.3), -0.9 + k * 0.6, 0.06 + j * 0.13, (k % 2) * 0.2, g, 28); }
      for (let k = 0; k < 3; k++) { const n = malha(rbox(1.3, 0.04, 0.65, 0.02), vinil("#58b368"), 0.3, 0.9 + k * 0.05, -0.6, g); n.rotation.y = k * 0.3; }
      if (c.numero) { const pl = malha(new THREE.PlaneGeometry(2.4, 0.7), new THREE.MeshBasicMaterial({ map: placaTexto(480, 140, "R$ " + num(c.numero), "#ffffff", "#1b1b22"), transparent: true }), 0, 2.1, 0, g); }
      return { g, tam: "pequeno" }; },
    foguete() { const g = new THREE.Group(); cil(0.45, 0.45, 1.8, vinil("#f3f0ea"), 0, 0, 0, g); malha(new THREE.ConeGeometry(0.45, 0.8, 30), vinil("#ef5d8f"), 0, 1.3, 0, g); bola(0.2, vinil("#3f7fe0"), 0, 0.3, 0.4, g);
      [0, 2.09, 4.19].forEach((a) => { const f = malha(rbox(0.1, 0.7, 0.6, 0.04), vinil("#ef5d8f"), Math.cos(a) * 0.45, -0.7, Math.sin(a) * 0.45, g); f.rotation.y = -a; });
      const fogo = malha(new THREE.ConeGeometry(0.35, 1, 20), brilho("#ffb03b"), 0, -1.4, 0, g); fogo.rotation.x = Math.PI;
      return { g, tam: "pequeno", anima: (lt) => { g.position.y += Math.pow(seg(lt, 0.6, 2.2), 2) * 4; fogo.scale.set(1, 0.8 + 0.4 * Math.abs(Math.sin(lt * 30)), 1); } }; },
    trofeu() { const g = new THREE.Group(); const ouro = vinil("#f2c230", 0.25); malha(new THREE.CylinderGeometry(0.7, 0.35, 1, 32, 1, true), ouro, 0, 0.9, 0, g).material.side = THREE.DoubleSide;
      [-0.75, 0.75].forEach((x) => { const a = new THREE.Mesh(new THREE.TorusGeometry(0.25, 0.07, 10, 24), ouro); a.position.set(x, 1, 0); g.add(a); }); cil(0.12, 0.12, 0.5, ouro, 0, 0.2, 0, g); malha(rbox(0.9, 0.3, 0.7, 0.06), vinil("#5a3a1e"), 0, -0.15, 0, g); return { g, tam: "pequeno" }; },
    relogio() { const g = new THREE.Group(); cil(1, 1, 0.25, vinil("#ffffff"), 0, 0, 0, g, 40).rotation.x = Math.PI / 2; const aro = new THREE.Mesh(new THREE.TorusGeometry(1, 0.1, 12, 40), vinil("#ef5d8f")); g.add(aro);
      const p1 = new THREE.Group(), p2 = new THREE.Group(); g.add(p1, p2); p1.position.z = p2.position.z = 0.16; malha(rbox(0.08, 0.7, 0.03, 0.02), vinil("#222"), 0, 0.33, 0, p1); malha(rbox(0.1, 0.5, 0.03, 0.02), vinil("#222"), 0, 0.23, 0, p2);
      return { g, tam: "pequeno", anima: (lt) => { p1.rotation.z = -lt * 9; p2.rotation.z = -lt * 0.8; } }; },
    calendario(c) { const g = new THREE.Group(); malha(rbox(1.8, 2, 0.15, 0.1), vinil("#ffffff"), 0, 0, 0, g); malha(rbox(1.8, 0.5, 0.17, 0.08), vinil("#ef5d8f"), 0, 0.78, 0, g);
      malha(new THREE.PlaneGeometry(1.5, 1.2), new THREE.MeshBasicMaterial({ map: placaTexto(300, 240, String(c.numero ?? TEXTO_OBJ(c) ?? "7"), "#ffffff", "#1b1b22") }), 0, -0.2, 0.09, g); return { g, tam: "grande" }; },
    livros(c) { const g = new THREE.Group(); ["#3f7fe0", "#ef5d8f", "#f6c445", "#3fbf7f", "#8e6bd8"].forEach((cor, k) => { const l = malha(rbox(1.7, 0.32, 1.2, 0.05), vinil(cor), (hash(k) - 0.5) * 0.3, 0.16 + k * 0.33, 0, g); l.rotation.y = (hash(k + 9) - 0.5) * 0.4;
        malha(new THREE.PlaneGeometry(1.2, 0.2), new THREE.MeshBasicMaterial({ map: placaTexto(256, 48, TEXTO_OBJ(c) || "TUTORIAL", cor, "#ffffff") }), 0, 0, 0.61, l); }); return { g, tam: "pequeno" }; },
    jornal(c) { const g = new THREE.Group(); malha(rbox(2.6, 3.4, 0.06, 0.03), fosco("#f2eee4"), 0, 0, 0, g);
      const tex = texTexto(520, 680, (cg, w, h) => { cg.fillStyle = "#f2eee4"; cg.fillRect(0, 0, w, h); cg.fillStyle = "#1b1b1b"; cg.textAlign = "center"; cg.font = `40px ${FONTE}`; cg.fillText("EDIÇÃO EXTRA", w / 2, 60); cg.fillRect(30, 80, w - 60, 4);
        const ls = linhas(TEXTO_OBJ(c) || "URGENTE", 11); let tam = 90; ls.forEach((l) => { tam = Math.min(tam, caber(cg, l, w - 60, 90)); }); ls.forEach((l, k) => { cg.font = `${tam}px ${FONTE}`; cg.fillText(l, w / 2, 180 + k * (tam + 8)); });
        cg.fillStyle = "#b9b4a8"; cg.fillRect(40, 400, 200, 220); for (let k = 0; k < 9; k++) cg.fillRect(270, 400 + k * 24, 210, 10); });
      malha(new THREE.PlaneGeometry(2.5, 3.3), new THREE.MeshBasicMaterial({ map: tex }), 0, 0, 0.04, g); return { g, tam: "grande", anima: (lt) => { g.rotation.z = (1 - backOut(seg(lt, 0, 0.6))) * 6; } }; },
    balao(c) { const g = new THREE.Group(); const tex = placaTexto(640, 360, TEXTO_OBJ(c) || "OI!", "#ffffff", "#1b1b22"); malha(rbox(3.2, 1.8, 0.25, 0.6), vinil("#ffffff"), 0, 0, 0, g);
      malha(new THREE.PlaneGeometry(2.9, 1.6), new THREE.MeshBasicMaterial({ map: tex }), 0, 0, 0.14, g); const p = malha(new THREE.ConeGeometry(0.3, 0.7, 4), vinil("#ffffff"), -0.9, -1.1, 0, g); p.rotation.z = 0.5; return { g, tam: "grande" }; },
    placa(c) { const g = new THREE.Group(); malha(rbox(3.4, 1.7, 0.22, 0.12), vinil("#c98a4a"), 0, 0.6, 0, g); malha(new THREE.PlaneGeometry(3.1, 1.45), new THREE.MeshBasicMaterial({ map: placaTexto(620, 290, TEXTO_OBJ(c) || "ABERTO", "#f4e2c4", "#4a2a12") }), 0, 0.6, 0.12, g);
      [-1.2, 1.2].forEach((x) => cil(0.09, 0.09, 2.2, vinil("#7a4a22"), x, -0.6, -0.05, g)); return { g, tam: "grande" }; },
    estrela(c) { const g = new THREE.Group(); const s = new THREE.Shape(); for (let k = 0; k < 10; k++) { const a = k / 10 * Math.PI * 2 + Math.PI / 2, rr = k % 2 ? 0.45 : 1.05; k ? s.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : s.moveTo(Math.cos(a) * rr, Math.sin(a) * rr); }
      const st = malha(new THREE.ExtrudeGeometry(s, { depth: 0.25, bevelEnabled: true, bevelThickness: 0.1, bevelSize: 0.08, bevelSegments: 4 }), vinil("#f6c445", 0.3), 0, 0.6, 0, g);
      const pl = malha(new THREE.PlaneGeometry(2.8, 0.75), new THREE.MeshBasicMaterial({ map: placaTexto(560, 150, num(c.numero) + " ⭑", "#1b1b22", "#f6c445") }), 0, -1, 0.2, g);
      return { g, tam: "grande", anima: (lt) => { st.rotation.y = Math.sin(lt * 2) * 0.4; } }; },
    lampada() { const g = new THREE.Group(); const vid = bola(0.75, new THREE.MeshPhysicalMaterial({ color: 0xfff4c2, emissive: 0x000000, roughness: 0.15, clearcoat: 1 }), 0, 0.5, 0, g); cil(0.35, 0.35, 0.5, vinil("#9aa0a8"), 0, -0.35, 0, g);
      return { g, tam: "pequeno", anima: (lt) => { vid.material.emissive.setRGB(...(lt > 0.6 ? [1, 0.85, 0.3] : [0, 0, 0])); vid.material.emissiveIntensity = lt > 0.6 ? 1.2 + 0.3 * Math.sin(lt * 12) : 0; } }; },
    presente() { const g = new THREE.Group(); malha(rbox(1.5, 1.2, 1.5, 0.1), vinil("#3fbf7f"), 0, 0.6, 0, g); const tampa = new THREE.Group(); g.add(tampa);
      malha(rbox(1.65, 0.3, 1.65, 0.08), vinil("#3fbf7f"), 0, 0, 0, tampa); malha(rbox(0.3, 0.32, 1.7, 0.05), vinil("#ef5d8f"), 0, 0, 0, tampa); malha(rbox(0.3, 1.25, 1.55, 0.05), vinil("#ef5d8f"), 0, 0.6, 0, g);
      return { g, tam: "pequeno", anima: (lt) => { const u = backOut(seg(lt, 0.7, 1.1)); tampa.position.y = 1.35 + u * 1.2; tampa.rotation.z = u * 0.6; } }; },
    escudo() { const g = new THREE.Group(); const s = new THREE.Shape(); s.moveTo(0, -1.2); s.quadraticCurveTo(1.1, -0.6, 1, 0.9); s.lineTo(0, 1.2); s.lineTo(-1, 0.9); s.quadraticCurveTo(-1.1, -0.6, 0, -1.2);
      malha(new THREE.ExtrudeGeometry(s, { depth: 0.2, bevelEnabled: true, bevelThickness: 0.1, bevelSize: 0.08, bevelSegments: 4 }), vinil("#3f7fe0"), 0, 0.3, 0, g);
      const v = new THREE.Shape(); v.moveTo(-0.45, 0.3); v.lineTo(-0.1, -0.1); v.lineTo(0.5, 0.6); v.lineTo(0.38, 0.72); v.lineTo(-0.1, 0.12); v.lineTo(-0.33, 0.42); malha(new THREE.ExtrudeGeometry(v, { depth: 0.1, bevelEnabled: false }), vinil("#ffffff"), 0, 0.15, 0.33, g);
      return { g, tam: "pequeno" }; },
    chave() { const g = new THREE.Group(); const ouro = vinil("#f2c230", 0.25); const a = new THREE.Mesh(new THREE.TorusGeometry(0.45, 0.14, 12, 32), ouro); a.position.y = 0.8; g.add(a); malha(rbox(0.2, 1.6, 0.18, 0.06), ouro, 0, -0.2, 0, g);
      malha(rbox(0.4, 0.15, 0.18, 0.04), ouro, 0.25, -0.8, 0, g); malha(rbox(0.3, 0.15, 0.18, 0.04), ouro, 0.2, -0.5, 0, g); return { g, tam: "pequeno" }; },
    equipe(c) { const g = new THREE.Group(); const n = clamp(Math.round(Number(c.numero) || 5), 3, 9), cores = ["#3f7fe0", "#3fbf7f", "#f6c445", "#8e6bd8", "#ef5d8f", "#f08a3c"]; const bots = [];
      for (let k = 0; k < n; k++) { const b = new THREE.Group(); b.position.set((k - (n - 1) / 2) * 0.95, 0, -((k % 2) * 0.6)); g.add(b); malha(rbox(0.7, 0.6, 0.55, 0.2), vinil(cores[k % 6]), 0, 0.45, 0, b); malha(rbox(0.85, 0.7, 0.65, 0.22), vinil("#f6efe4"), 0, 1.1, 0, b);
        malha(new THREE.PlaneGeometry(0.62, 0.45), brilho("#1b2530"), 0, 1.1, 0.34, b); [-0.13, 0.13].forEach((x) => malha(new THREE.PlaneGeometry(0.09, 0.14), brilho("#63f5ad"), x, 1.12, 0.35, b)); bots.push(b); }
      return { g, tam: "grande", anima: (lt) => { bots.forEach((b, k) => { b.position.y = Math.abs(Math.sin(lt * 6 + k)) * 0.12; b.scale.setScalar(backOut(seg(lt, k * 0.08, 0.35 + k * 0.08))); }); } }; },
    claquete(c) { const g = new THREE.Group(); malha(rbox(2, 1.4, 0.15, 0.06), vinil("#1d1d24"), 0, 0, 0, g); const top = new THREE.Group(); top.position.set(-1, 0.75, 0); g.add(top);
      const bar = malha(rbox(2, 0.3, 0.15, 0.04), vinil("#f3f0ea"), 1, 0.15, 0, top);
      malha(new THREE.PlaneGeometry(1.8, 0.9), new THREE.MeshBasicMaterial({ map: placaTexto(360, 180, TEXTO_OBJ(c) || "CENA 1", "#1d1d24", "#ffffff") }), 0, -0.1, 0.08, g);
      return { g, tam: "pequeno", anima: (lt) => { top.rotation.z = lt < 0.6 ? 0.5 * (1 - seg(lt, 0.4, 0.6)) : 0; } }; },
    lixeira() { const g = new THREE.Group(); cil(0.7, 0.55, 1.5, vinil("#8a93a0"), 0, 0.75, 0, g, 28); cil(0.78, 0.78, 0.15, vinil("#6d7581"), 0, 1.55, 0, g, 28); return { g, tam: "pequeno" }; },
    ampulheta() { const g = new THREE.Group(); [-0.95, 0.95].forEach((y) => cil(0.75, 0.75, 0.15, vinil("#8b5a2b"), 0, y, 0, g, 24)); const vid = new THREE.MeshPhysicalMaterial({ color: 0xdff4ff, roughness: 0.1, transparent: true, opacity: 0.4 });
      malha(new THREE.ConeGeometry(0.6, 0.9, 24), vid, 0, 0.45, 0, g).rotation.x = Math.PI; malha(new THREE.ConeGeometry(0.6, 0.9, 24), vid, 0, -0.45, 0, g);
      const areia = malha(new THREE.ConeGeometry(0.45, 0.5, 24), vinil("#f6c445"), 0, -0.6, 0, g); return { g, tam: "pequeno", anima: (lt) => { g.rotation.z = lt < 0.5 ? Math.PI * (1 - suave(seg(lt, 0, 0.5))) : 0; areia.scale.y = 0.3 + seg(lt, 0.5, 3); } }; },
    nuvem() { const g = new THREE.Group(); [[0, 0, 0.8], [-0.8, -0.2, 0.6], [0.8, -0.2, 0.6], [0.4, 0.4, 0.55], [-0.4, 0.35, 0.5]].forEach(([x, y, rr]) => bola(rr, vinil("#ffffff", 0.7), x, y, 0, g)); return { g, tam: "pequeno" }; },
    raio() { const g = new THREE.Group(); const s = new THREE.Shape(); s.moveTo(0.2, 1.3); s.lineTo(-0.6, -0.1); s.lineTo(-0.05, -0.1); s.lineTo(-0.35, -1.3); s.lineTo(0.6, 0.25); s.lineTo(0.05, 0.25); s.lineTo(0.2, 1.3);
      malha(new THREE.ExtrudeGeometry(s, { depth: 0.25, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.05, bevelSegments: 3 }), new THREE.MeshPhysicalMaterial({ color: 0xffd23f, emissive: 0xffaa00, emissiveIntensity: 0.6, roughness: 0.3 }), 0, 0, 0, g); return { g, tam: "pequeno" }; },
  };
  // ação de ferramenta põe a ferramenta na mão
  const FERRAMENTA_DA_ACAO = { martela: "martelo", corta: "tesoura", carimba: "carimbo", observa: "lupa" };

  // monta os objetos de todas as cenas (cada cena tem o seu, com o texto dela)
  const montagem = CEN.map((c, i) => {
    const m = { alvo: null, mao: null };
    const fer = FERRAMENTA_DA_ACAO[c.acao];
    const nomeObj = OBJ[c.objeto] ? c.objeto : null;
    if (fer && OBJ[fer]) { m.mao = OBJ[fer](c); sombra(m.mao.g); m.mao.g.visible = false; cena.add(m.mao.g); }
    if (nomeObj && nomeObj !== fer) {
      m.alvo = OBJ[nomeObj](c); sombra(m.alvo.g); m.alvo.g.visible = false; cena.add(m.alvo.g);
      if (c.acao === "segura" && m.alvo.tam === "pequeno") { m.mao = m.alvo; m.alvo = null; }
    } else if (fer && !nomeObj) { m.alvo = OBJ.caixa({ texto_objeto: c.texto_objeto || "" }); sombra(m.alvo.g); m.alvo.g.visible = false; cena.add(m.alvo.g); }
    else if (fer && nomeObj === fer) { m.alvo = OBJ.placa({ texto_objeto: c.texto_objeto || "" }); sombra(m.alvo.g); m.alvo.g.visible = false; cena.add(m.alvo.g); }
    if (c.acao === "carimba") { const txt = (m.mao && m.mao.marca) || TEXTO_OBJ(c) || "APROVADO"; const verm = /REPRO|NÃO|NAO|ERRO|FALHA/.test(txt);
      m.marca = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 0.9), new THREE.MeshBasicMaterial({ map: placaTexto(520, 180, txt, "rgba(0,0,0,0)", verm ? "#d63031" : "#1e9e55", verm ? "#d63031" : "#1e9e55"), transparent: true, depthTest: false })); m.marca.renderOrder = 5; m.marca.visible = false; cena.add(m.marca); }
    return m;
  });

  // partículas: confete (comemora), voxels (transição), poeira (aterrissagem)
  const CORES_CONF = ["#f6c445", "#ef5d8f", "#3f7fe0", "#3fbf7f", "#ffffff", "#8e6bd8"];
  const confete = Array.from({ length: 90 }, (_, k) => { const m = malha(new THREE.BoxGeometry(0.14, 0.14, 0.03), brilho(CORES_CONF[k % 6]), 0, -50, 0, cena); m.castShadow = false; return m; });
  const voxels = Array.from({ length: 70 }, (_, k) => { const m = malha(new THREE.BoxGeometry(0.28, 0.28, 0.28), vinil(CORES_CONF[k % 6]), 0, -50, 0, cena); return m; });

  // ======================================================================
  // DIREÇÃO: pose do robô por ação, posição dos objetos, câmera
  // ======================================================================
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  // o lado do robô alterna por cena (espelha a composição) para nenhuma cena parecer a anterior
  const LADO = (c) => (CEN.indexOf(c) % 2 ? -1 : 1);
  const ROBO_X = (c, m) => (m.alvo ? (m.alvo.tam === "grande" ? -1.25 : -1.1) * LADO(c) : 0);
  // composição das referências: objeto grande ATRÁS e acima do robô (como o celular gigante atrás do mascote); pequeno ao lado, no chão
  const NO_CHAO = { equipe: 0, grafico: 0, maquina: 0, notebook: 0.05, placa: 2.1, monitor: 2.2 };
  const ALVO_POS = (c, m) => (m.alvo && m.alvo.tam === "grande" ? V(0.7 * LADO(c), (NO_CHAO[c.objeto] ?? 3.9) * (c.objeto in NO_CHAO ? 1 : 1), c.objeto in NO_CHAO ? -1.6 : -2.4) : V(1.65 * LADO(c), 1.0, 0.5));
  // planos bem diferentes entre si (o crítico reclamou de câmeras parecidas); "rol" inclina o horizonte
  const CAMS = {
    frente: (k) => ({ p: V(0, 3.2, mix(19.5, 17.5, k)), a: V(0, 2.3, 0), rol: 0 }),
    aproxima: (k) => ({ p: V(mix(1.2, 0.4, k), mix(3.0, 2.8, k), mix(19, 14.5, k)), a: V(0, 2.4, 0), rol: 0.03 }),
    afasta: (k) => ({ p: V(0, mix(3.4, 6, k), mix(15, 24, k)), a: V(0, 2.2, 0), rol: 0 }),
    lateral: (k) => ({ p: V(mix(-11, -7.5, k), 3.4, mix(14, 16, k)), a: V(0.3, 2.2, 0), rol: -0.05 }),
    cima: (k) => ({ p: V(mix(-2, 2, k), mix(18, 16, k), mix(11, 10, k)), a: V(0, 1.2, -0.5), rol: 0 }),
    baixo: (k) => ({ p: V(mix(-1, 1, k), 0.5, mix(17, 15.5, k)), a: V(0, 3.6, 0), rol: 0.06 }),
    orbita: (k) => { const a = mix(-0.7, 0.6, k); return { p: V(Math.sin(a) * 18, 3.6, Math.cos(a) * 18), a: V(0, 2.3, 0), rol: 0 }; },
    close_objeto: (k) => ({ p: V(mix(1.8, 1.0, k), mix(3.4, 3.2, k), mix(16.5, 14.5, k)), a: V(0.2, 2.6, -0.5), rol: -0.03 }),
  };

  function pose(c, lt, dur, t) {
    // valores-base (repouso) + respiração
    const p = { y: 0, lean: 0, giro: 0, sx: 1, sy: 1, bE: { x: 0, z: 0.35 }, bD: { x: 0, z: -0.35 }, cab: { x: 0, z: 0 }, olhar: { x: 0.3, y: 0 }, x: 0, pe: 0 };
    const resp = 0.015 * Math.sin(t * 2.6); p.sy += resp; p.sx -= resp * 0.5;
    const ent = seg(lt, 0, 0.45), ant = pulso(lt, 0, 0.14); // antecipação nos primeiros quadros
    p.sy -= 0.07 * ant; p.sx += 0.05 * ant;
    switch (c.acao) {
      case "apresenta": { const u = backOut(seg(lt, 0.1, 0.55)); p.bE = { x: -0.2, z: 0.35 + 1.15 * u }; p.bD = { x: -0.2, z: -0.35 - 1.15 * u }; p.lean = -0.08 * u; p.olhar = { x: 0, y: 0 }; break; }
      case "aponta": { const u = backOut(seg(lt, 0.1, 0.45)); p.bD = { x: -0.9 * u, z: -0.35 - 1.05 * u }; p.bE = { x: 0, z: 0.55 }; p.giro = 0.35 * u; p.olhar = { x: 0.9, y: -0.1 }; break; }
      case "segura": { const u = backOut(seg(lt, 0.05, 0.45)); p.bD = { x: -1.25 * u, z: -0.5 * u }; p.bE = { x: -0.3, z: 0.4 }; p.olhar = { x: 0.6, y: 0.2 }; p.y = 0.04 * Math.sin(lt * 4); break; }
      case "martela": { const ciclo = (lt - 0.35) / 0.6, fase = ciclo - Math.floor(ciclo), ativo = lt > 0.35 && ciclo < 3;
        const ang = ativo ? (fase < 0.55 ? mix(0.2, 2.6, suave(fase / 0.55)) : mix(2.6, 0.2, Math.pow((fase - 0.55) / 0.45, 0.5))) : 1.2 * seg(lt, 0, 0.35);
        p.bD = { x: -ang, z: -0.25 }; p.lean = ativo ? (fase > 0.55 ? 0.12 : -0.05) : 0; p.giro = 0.5; p.olhar = { x: 0.9, y: 0.5 }; break; }
      case "corta": { p.bD = { x: -1.3, z: -0.7 }; p.bE = { x: -0.9, z: 0.3 }; p.giro = 0.45; p.olhar = { x: 0.9, y: 0.3 }; p.lean = 0.08; break; }
      case "carimba": { const desce = seg(lt, 0.45, 0.6), sobe = seg(lt, 0.9, 1.2); const ang = mix(mix(0.3, 2.8, seg(lt, 0, 0.45)), 0.6, desce) + 2.2 * sobe * 0;
        p.bD = { x: -ang, z: -0.3 }; p.giro = 0.5; p.lean = 0.15 * desce * (1 - sobe); p.sy -= 0.08 * pulso(lt, 0.58, 0.72); p.olhar = { x: 0.9, y: 0.5 }; break; }
      case "digita": { const a = Math.sin(lt * 22) * 0.12; p.bE = { x: -1.1 + a, z: 0.2 }; p.bD = { x: -1.1 - a, z: -0.2 }; p.lean = 0.12; p.giro = 0.45; p.olhar = { x: 0.6, y: 0.6 }; break; }
      case "pensa": { const u = backOut(seg(lt, 0.05, 0.5)); p.bD = { x: -1.9 * u, z: -0.55 - 0.4 * u }; p.bE = { x: -0.25, z: 0.6 }; p.cab = { x: 0, z: 0.12 * u }; p.olhar = { x: 0.6, y: -0.8 }; break; }
      case "comemora": { const h = Math.max(pulso(lt, 0.15, 0.75), pulso(lt, 0.85, 1.35) * 0.6); p.y = 1.3 * h; p.bE = { x: 0, z: 2.6 }; p.bD = { x: 0, z: -2.6 }; p.sy += 0.1 * h - 0.12 * (pulso(lt, 0.72, 0.85) + pulso(lt, 1.32, 1.45)); p.sx -= 0.05 * h; p.pe = h; p.olhar = { x: 0, y: -0.2 }; break; }
      case "assusta": { const h = pulso(lt, 0.05, 0.5); p.y = 0.8 * h; p.x = -0.9 * suave(seg(lt, 0.05, 0.5)); p.bE = { x: -0.4, z: 1.9 }; p.bD = { x: -0.4, z: -1.9 }; p.lean = -0.18; p.olhar = { x: 0.9, y: 0 }; break; }
      case "pula": { const h = Math.max(pulso(lt, 0.1, 0.6), pulso(lt, 0.7, 1.2), pulso(lt, 1.3, 1.8)); p.y = 0.9 * h; p.bE = { x: 0, z: 1.2 + h }; p.bD = { x: 0, z: -1.2 - h }; p.sy += 0.08 * h; p.pe = h; break; }
      case "empurra": { p.lean = 0.25; p.bE = { x: -1.5, z: 0.2 }; p.bD = { x: -1.5, z: -0.2 }; p.giro = 0.9; p.x = mix(-1.2, 0.2, suave(seg(lt, 0, 1.2))); p.pe = Math.abs(Math.sin(lt * 9)) * 0.6; p.olhar = { x: 0.9, y: 0.2 }; break; }
      case "observa": { const u = suave(seg(lt, 0.05, 0.6)); p.lean = 0.22 * u; p.giro = 0.5 * u; p.bD = { x: -1.3 * u, z: -0.3 }; p.olhar = { x: 1, y: 0.4 }; p.cab = { x: 0, z: -0.06 * Math.sin(lt * 2) }; break; }
      case "acena": { const u = backOut(seg(lt, 0.05, 0.4)); p.bD = { x: -0.7 * u, z: -2.3 * u - 0.35 * Math.sin(lt * 11) * u }; p.bE = { x: 0, z: 0.4 }; p.cab = { x: 0, z: 0.08 * Math.sin(lt * 5.5) }; p.olhar = { x: 0, y: 0 }; break; }
      case "corre": { p.x = mix(-4, 2.5, seg(lt, 0, dur)); p.giro = 1.4; p.pe = Math.abs(Math.sin(lt * 14)); p.bE = { x: Math.sin(lt * 14) * 1.1, z: 0.3 }; p.bD = { x: -Math.sin(lt * 14) * 1.1, z: -0.3 }; p.y = 0.12 * Math.abs(Math.sin(lt * 14)); p.lean = 0.15; break; }
      default: { p.bE = { x: 0, z: 0.4 + 0.05 * Math.sin(t * 3) }; p.bD = { x: 0, z: -0.4 - 0.05 * Math.sin(t * 3 + 1) }; }
    }
    // olhar acompanha o objeto do lado oposto quando o robô está à direita
    return p;
  }

  // ======================================================================
  // OVERLAYS HTML
  // ======================================================================
  const $ = (id) => document.getElementById(id);
  const tituloEl = $("titulo"), hudEl = $("hud"), hudVal = $("hud-val"), hudRot = $("hud-rot"), legEl = $("leg"), etapasEl = $("etapas");
  const HUD = ROT.hud || null;
  if (HUD && HUD.tipo === "contador") { hudRot.textContent = (HUD.rotulo || "").toUpperCase().slice(0, 14); hudEl.style.display = "flex"; }
  if (HUD && HUD.tipo === "etapas" && Array.isArray(HUD.itens)) { etapasEl.style.display = "flex"; HUD.itens.slice(0, 5).forEach((it, k) => { const d = document.createElement("div"); d.className = "et"; d.textContent = `${k + 1} ${String(it).toUpperCase().slice(0, 11)}`; etapasEl.appendChild(d); }); }
  const palavras = []; F.forEach((f) => (f.palavras || []).forEach((w) => palavras.push(w)));
  const limpa = (p) => String(p).replace(/[.,:;!?"“”()]/g, "");

  function overlays(t, i, lt) {
    const c = CEN[i] || {};
    // pílula de título: troca com pop no começo de cada cena
    const tt = String(c.titulo || "").toUpperCase();
    if (tituloEl.textContent !== tt) tituloEl.textContent = tt;
    const pop = backOut(seg(lt, 0, 0.3), 2.4); tituloEl.style.transform = `translateX(-50%) scale(${tt ? pop : 0}) rotate(${(i % 2 ? 1 : -1) * 1.2}deg)`;
    // HUD contador: interpola até o valor da cena
    if (HUD && HUD.tipo === "contador") { let ant = 0, alvo = 0; for (let k = 0; k <= i; k++) { if (CEN[k].hud_valor != null) { ant = k < i ? CEN[k].hud_valor : ant; alvo = CEN[k].hud_valor; } }
      let prev = 0; for (let k = 0; k < i; k++) if (CEN[k].hud_valor != null) prev = CEN[k].hud_valor;
      const v = Math.round(mix(prev, alvo, suave(seg(lt, 0.1, 0.8)))); hudVal.textContent = num(v); hudEl.style.transform = `scale(${1 + 0.18 * pulso(lt, 0.1, 0.45) * (alvo !== prev ? 1 : 0)})`; }
    if (HUD && HUD.tipo === "etapas") { let atual = -1; for (let k = 0; k <= i; k++) if (CEN[k].hud_valor != null) atual = CEN[k].hud_valor; [...etapasEl.children].forEach((d, k) => d.classList.toggle("on", k < atual)); }
    // legenda: uma palavra por vez, no tempo da voz
    let w = null; for (const p of palavras) { if (p.t - 0.05 <= t) w = p; else break; }
    const ultimaFala = F[F.length - 1], noFim = t > ultimaFala.t + ultimaFala.d + 0.25;
    const txt = w && !noFim ? limpa(w.p) : ""; if (legEl.textContent !== txt) { legEl.textContent = txt; }
    const tw = w ? t - w.t : 1; legEl.style.transform = `translateX(-50%) scale(${txt ? 1 + 0.22 * (1 - backOut(seg(tw, 0, 0.14))) * -1 + 0.22 : 0})`;
    legEl.style.opacity = txt ? 1 : 0;
    // fechamento: caixa de comentário digitando + seguir
    const fimCTA = i === CEN.length - 1; hudEl.style.opacity = fimCTA ? 0 : 1; etapasEl.style.opacity = fimCTA ? 0 : 1;
    const fc = F[F.length - 1], tf = t - fc.t; const PAL = String(ROT.palavra || "LINK").toUpperCase();
    $("cta").style.opacity = tf > 0 ? 1 : 0; $("cta").style.transform = `translateX(-50%) translateY(${(1 - backOut(seg(tf, 0, 0.35))) * 60}px)`;
    $("cta-tx").textContent = PAL.slice(0, Math.round(PAL.length * seg(tf, 0.25, 0.25 + PAL.length * 0.08)));
    const seguiu = tf > 1.7; $("seg-bt").textContent = seguiu ? "SEGUINDO ✓" : "SEGUIR"; $("seg-bt").classList.toggle("ok", seguiu); $("seg-bt").style.transform = `scale(${1 - 0.12 * pulso(tf, 1.55, 1.75)})`;
  }


  // ======================================================================
  // MODO EXPERIMENTO: várias IAs (robozinhos com crachá) numa ilha; eventos vêm do log real do jogo
  // ======================================================================
  const EXP = ROT.experimento || null;
  const jog = {};
  if (EXP) {
    const n = EXP.jogadores.length;
    EXP.jogadores.forEach((J, k) => {
      const g = new THREE.Group(); const a = Math.PI * (0.05 + 0.9 * k / Math.max(1, n - 1)) + Math.PI; const R = 4.4;
      g.position.set(Math.cos(a) * R * -1, 0.35, Math.sin(a) * R * -0.9 + 0.6); g.userData.base = g.position.clone(); cena.add(g);
      const corpoJ = new THREE.Group(); g.add(corpoJ);
      malha(rbox(1.0, 0.85, 0.8, 0.3), vinil(J.cor), 0, 0.75, 0, corpoJ);
      const cab = new THREE.Group(); cab.position.y = 1.75; corpoJ.add(cab); malha(rbox(1.5, 1.15, 1.05, 0.35), vinil("#efe4d2"), 0, 0, 0, cab);
      malha(new THREE.PlaneGeometry(1.2, 0.85), brilho("#1b2530"), 0, 0, 0.54, cab);
      const olhos = [-0.24, 0.24].map((x) => malha(new THREE.PlaneGeometry(0.17, 0.27), brilho("#63f5ad"), x, 0.03, 0.55, cab));
      [-0.28, 0.28].forEach((x) => { const p = malha(new THREE.CapsuleGeometry(0.11, 0.2, 6, 12), vinil("#3a3f4a"), x, 0.18, 0, corpoJ); });
      const tag = new THREE.Mesh(new THREE.PlaneGeometry(1.9, 0.5), new THREE.MeshBasicMaterial({ map: placaTexto(380, 100, J.nome.toUpperCase(), J.cor, "#ffffff"), transparent: true, depthTest: false }));
      tag.position.y = 3.05; tag.renderOrder = 4; g.add(tag);
      const xis = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.6), new THREE.MeshBasicMaterial({ map: texTexto(256, 256, (cg) => { cg.strokeStyle = "#e53935"; cg.lineWidth = 34; cg.lineCap = "round"; cg.beginPath(); cg.moveTo(40, 40); cg.lineTo(216, 216); cg.moveTo(216, 40); cg.lineTo(40, 216); cg.stroke(); }), transparent: true, depthTest: false }));
      xis.position.set(0, 1.7, 0.8); xis.renderOrder = 6; xis.visible = false; g.add(xis);
      sombra(g); jog[J.nome] = { g, corpoJ, cab, olhos, tag, xis, cor: J.cor, k };
    });
    robo.visible = false; blob.visible = false;
  }
  const balao = new THREE.Group(); cena.add(balao); balao.visible = false;
  let balaoTex = null, balaoTxt = "";
  function setBalao(txt) { if (txt === balaoTxt) return; balaoTxt = txt; balao.clear();
    const tex = texTexto(760, 300, (g, w, h) => { g.fillStyle = "#ffffff"; g.fillRect(0, 0, w, h); const ls = linhas(txt, 22).concat(linhas(txt, 22).length >= 3 ? [] : []);
      const todas = (() => { const ps = String(txt).split(/\s+/), out = [""]; ps.forEach((p) => { if ((out[out.length - 1] + " " + p).trim().length > 22) out.push(p); else out[out.length - 1] = (out[out.length - 1] + " " + p).trim(); }); return out.slice(0, 4); })();
      let tam = 64; todas.forEach((l) => { tam = Math.min(tam, caber(g, l, w - 50, 64)); });
      g.fillStyle = "#1b1b22"; g.textAlign = "center"; g.textBaseline = "middle"; todas.forEach((l, k) => { g.font = `${tam}px ${FONTE}`; g.fillText(l, w / 2, h / 2 + (k - (todas.length - 1) / 2) * tam * 1.1); }); }); malha(rbox(4.2, 1.7, 0.2, 0.55), vinil("#ffffff"), 0, 0, 0, balao);
    malha(new THREE.PlaneGeometry(3.9, 1.5), new THREE.MeshBasicMaterial({ map: tex }), 0, 0, 0.12, balao); const p = malha(new THREE.ConeGeometry(0.3, 0.8, 4), vinil("#ffffff"), -0.6, -1.05, 0, balao); p.rotation.z = 0.4; }
  // quem já desmaiou / foi banida em cada cena vem do LOG (o Python calcula pelo dia da cena)
  function estadoAte(i) { const c = CEN[i] || {}; return { fora: new Set(c.fora_antes || []), banidas: new Set(c.banidas || []) }; }
  function experimentoQuadro(t, i, lt, c) {
    const est = estadoAte(i), foco = c.foco && jog[c.foco] ? c.foco : null;
    Object.entries(jog).forEach(([nome, J]) => {
      const caiuAgora = (c.fora_agora || []).includes(nome); const caiu = est.fora.has(nome) || (caiuAgora && lt > 0.5);
      const base = J.g.userData.base; J.g.position.copy(base);
      const pulo = c.evento === "pega" && foco === nome ? Math.max(pulso(lt, 0.2, 0.7), pulso(lt, 0.8, 1.2) * 0.6) : c.evento === "resgate" && !caiu ? pulso((lt + J.k * 0.15) % 0.9, 0, 0.6) * 0.8 : 0.03 * Math.abs(Math.sin(t * 3 + J.k));
      J.g.position.y = base.y + pulo;
      J.corpoJ.rotation.z = caiu ? mix(0, 1.45, suave(seg(caiuAgora ? lt : 9, 0.5, 1.1))) : 0;
      J.g.lookAt(foco && foco !== nome ? jog[foco].g.position.x : 0, J.g.position.y, foco && foco !== nome ? jog[foco].g.position.z : 6);
      J.olhos.forEach((o) => { o.scale.y = caiu ? 0.15 : (piscada(t + J.k * 0.7) > 0.5 ? 0.15 : 1); o.material.color.set(caiu ? "#777" : est.banidas.has(nome) ? "#ff7a5a" : "#63f5ad"); });
      const banAgora = (c.banida_agora || []).includes(nome); J.xis.visible = est.banidas.has(nome) || (banAgora && lt > 0.4);
      if (J.xis.visible) J.xis.scale.setScalar(banAgora ? backOut(seg(lt, 0.4, 0.7)) : 1);
      J.tag.quaternion.copy(cam.quaternion); J.xis.quaternion.copy(cam.quaternion);
    });
    const ilha = mundos.ilha; if (ilha) {
      const ch = ilha.userData.chamas; ch[0].scale.set(1, 0.8 + 0.3 * Math.abs(Math.sin(t * 13)), 1); ch[1].scale.set(1, 0.8 + 0.3 * Math.abs(Math.sin(t * 17 + 1)), 1); ch[2].intensity = 1 + 0.3 * Math.sin(t * 11);
      const est0 = c.estoque ?? (() => { for (let k = i; k >= 0; k--) if (CEN[k].estoque != null) return CEN[k].estoque; return EXP.estoque_inicial; })();
      ilha.userData.pilha.forEach((cx, k) => (cx.visible = k < est0));
      ilha.userData.mar.position.y = -0.35 + 0.05 * Math.sin(t * 1.5);
      const nv = ilha.userData.navio; nv.visible = c.evento === "resgate"; if (nv.visible) nv.position.set(mix(28, 11, suave(seg(lt, 0, 2.5))), -0.1 + 0.1 * Math.sin(t * 2), -6);
    }
    // caixa voando da pilha para quem pegou
    if (c.evento === "pega" && foco) { /* reaproveita o balão de citação; a pilha já encolhe pelo estoque */ }
    // balão com a citação real
    const quem = c.citacao_de && jog[c.citacao_de] ? c.citacao_de : null;
    balao.visible = !!(quem && c.citacao) && lt > 0.15;
    if (balao.visible) { setBalao('"' + c.citacao + '"'); const p = jog[quem].g.position; balao.position.set(mix(p.x, 0, 0.35), 4.6, p.z + 0.5); balao.quaternion.copy(cam.quaternion); balao.scale.setScalar(backOut(seg(lt, 0.15, 0.45))); }
    return foco ? jog[foco].g.position.clone() : V(0, 0, 0.5);
  }

  // ======================================================================
  // QUADRO
  // ======================================================================
  let mundoAtual = null;
  function trocaMundo(nome, c) {
    const nm = mundos[nome] ? nome : "palco";
    Object.entries(mundos).forEach(([k, g]) => (g.visible = k === nm));
    const cfg = MUNDO_CFG[nm]; let fundo = cfg.fundo;
    if (nm === "cor") { fundo = COR[c.fundo_cor] || COR.roxo; mundos.cor.userData.matCor.color.set(fundo); }
    cena.background = new THREE.Color(fundo); cena.fog = new THREE.Fog(fundo, 22, 60);
    key.intensity = cfg.key; key.color.set(cfg.keyCor); hemi.intensity = cfg.hemi;
    mundoAtual = nm;
  }

  function desenhar(t) {
    t = clamp(t, 0, FIM);
    const i = cenaEm(t), c = CEN[i] || CEN[CEN.length - 1], m = montagem[i] || {}, lt = t - ini[i], dur = fimCena(i) - ini[i], k = suave5(clamp(lt / dur));
    trocaMundo(c.mundo || ROT.mundo || "palco", c);

    // robô
    const p = pose(c, lt, dur, t);
    const rx = ROBO_X(c, m) + p.x;
    robo.position.set(rx, p.y, 0); robo.rotation.y = p.giro * (rx < 0 ? 1 : -1) * 0.6; corpo.rotation.x = p.lean;
    corpo.scale.set(p.sx, p.sy, p.sx);
    bE.rotation.set(p.bE.x, 0, p.bE.z); bD.rotation.set(p.bD.x, 0, p.bD.z);
    pernas[0].rotation.x = p.pe ? Math.sin(t * 14) * 0.5 * p.pe : 0; pernas[1].rotation.x = p.pe ? -Math.sin(t * 14) * 0.5 * p.pe : 0;
    cabeca.rotation.set(p.cab.x, Math.sin(t * 1.3) * 0.06, p.cab.z + 0.03 * Math.sin(t * 1.9));
    blob.position.x = rx; blob.scale.setScalar(1 / (1 + 0.6 * p.y)); blob.material.opacity = 0.9 / (1 + 0.8 * p.y);
    const chap = c.chapeu || ROT.chapeu; Object.entries(chapeus).forEach(([n, g]) => (g.visible = n === chap));
    luzAntena.material.color.set(Math.floor(t * 2.5) % 2 ? "#ff5a5a" : "#ffc2c2");
    const emo = c.emocao || "feliz";
    pintaRosto(t, emo, p.olhar);

    // objetos: só os da cena atual
    montagem.forEach((mm, k) => { [mm.alvo, mm.mao].forEach((o) => { if (o) o.g.visible = false; }); if (mm.marca) mm.marca.visible = false; });
    if (m.alvo) { const o = m.alvo, base = ALVO_POS(c, m); o.g.visible = true; const u = backOut(seg(lt, 0.08, 0.5), 2.2);
      const emp = c.acao === "empurra" ? mix(-3, 0, suave(seg(lt, 0, 1.2))) : 0;
      o.g.position.set(base.x + emp, base.y + (o.tam === "grande" ? 0.06 * Math.sin(t * 2) : 0), base.z); o.g.scale.setScalar(Math.max(0.001, u) * (o.tam === "grande" ? 1.85 : 1.7) * (o.g.userData.fit || 1));
      o.g.rotation.set(0, -0.2 * LADO(c) + 0.05 * Math.sin(t * 1.5), 0);
      if (c.acao === "martela") { const ciclo = (lt - 0.35) / 0.6, fase = ciclo - Math.floor(ciclo); if (lt > 0.35 && ciclo < 3 && fase > 0.55 && fase < 0.7) o.g.scale.y *= 0.88; }
      if (o.anima) o.anima(lt, t); }
    if (m.mao) { const o = m.mao; o.g.visible = true; const ref = bD.userData.mao; ref.updateWorldMatrix(true, false); const wp = new THREE.Vector3(); ref.getWorldPosition(wp);
      o.g.position.copy(wp); const q = new THREE.Quaternion(); bD.getWorldQuaternion(q); o.g.quaternion.copy(q); o.g.rotateX(Math.PI);
      if (c.acao === "segura") { o.g.quaternion.identity(); o.g.position.x += 0.75 * LADO(c); o.g.position.y += 0.75; o.g.rotation.y = -0.3 + 0.1 * Math.sin(t * 2); }
      if (c.acao === "observa") { o.g.quaternion.identity(); o.g.rotation.z = 0.3; }
      o.g.scale.setScalar(backOut(seg(lt, 0.0, 0.3)) * (o.ferramenta ? 1 : 0.8)); if (o.anima) o.anima(lt, t); }
    if (m.marca) { const on = lt > 0.58; m.marca.visible = on; const a = ALVO_POS(c, m); m.marca.position.set(a.x, a.y + (m.alvo && m.alvo.tam === "grande" ? 0 : 0.9), a.z + 0.9); m.marca.rotation.z = -0.18; m.marca.scale.setScalar(on ? mix(1.6, 1, backOut(seg(lt, 0.58, 0.75))) : 1); }

    // confete na comemoração e no fim
    const tConf = c.acao === "comemora" ? lt - 0.15 : (i === CEN.length - 1 ? lt - 1.7 : -1);
    confete.forEach((q, n) => { if (tConf < 0) { q.position.y = -50; return; } const ph = tConf * 0.55 + hash(n) * 0.9; const yy = 9 - ((ph % 1.6) / 1.6) * 10;
      q.position.set(rx + (hash(n + 1) - 0.5) * 9, yy, (hash(n + 2) - 0.3) * 4); q.rotation.set(t * 5 + n, t * 4 + n * 0.3, 0); });
    // voxels na transição "voxel": explodem do objeto no começo da cena
    const tv = c.transicao === "voxel" ? lt : 99; const centro = m.alvo ? ALVO_POS(c, m) : V(rx, 2, 0);
    voxels.forEach((q, n) => { if (tv > 0.7) { q.position.y = -50; return; } const dir = V(hash(n) - 0.5, hash(n + 7) - 0.2, hash(n + 13) - 0.3).normalize(); const d = 4.5 * Math.sqrt(tv / 0.7);
      q.position.set(centro.x + dir.x * d, centro.y + dir.y * d - 4 * tv * tv, centro.z + dir.z * d); q.scale.setScalar(1 - tv / 0.7); q.rotation.set(tv * 9 + n, tv * 7, 0); });

    // lâmpadas do cenário piscam devagar
    lampadas.forEach((b, n) => b.material.color.setHSL(0.11, 1, 0.6 + 0.25 * Math.sin(t * 3 + n * 1.7)));

    let alvoExp = null; if (EXP) alvoExp = experimentoQuadro(t, i, lt, c);
    // câmera: plano da cena com empurrão constante (nunca parada) + chicote na entrada
    const camNome = CAMS[c.camera] ? c.camera : "frente";
    const cc = CAMS[camNome](k); let offX = rx * 0.35 + (m.alvo ? 0.35 * LADO(c) : 0);
    if (alvoExp) { offX = alvoExp.x * 0.8; cc.p.z += alvoExp.z * 0.8 + (c.foco ? -2 : 3); cc.a.z += alvoExp.z * 0.8; cc.a.y += c.foco ? 0.6 : 0; }
    let chic = 0; if (c.transicao === "chicote" && i > 0) chic = 1 - suave(seg(lt, 0, 0.22));
    cam.position.set(cc.p.x + offX + chic * 7, cc.p.y, cc.p.z); cam.lookAt(cc.a.x + offX + chic * 4, cc.a.y, cc.a.z); cam.rotateZ(cc.rol || 0);
    canvas.style.filter = chic > 0.05 ? `blur(${(chic * 14).toFixed(1)}px)` : "none";
    const kick = c.acao === "carimba" ? pulso(lt, 0.58, 0.75) : c.acao === "martela" ? (() => { const ciclo = (lt - 0.35) / 0.6, f = ciclo - Math.floor(ciclo); return lt > 0.35 && ciclo < 3 ? pulso(f, 0.55, 0.68) : 0; })() : 0;
    cam.position.y += kick * 0.08 * (Math.floor(t * 30) % 2 ? 1 : -1);

    r.render(cena, cam);
    overlays(t, i, lt);
  }

  // ======================================================================
  // TIMELINE (o HyperFrames navega por ela)
  // ======================================================================
  const tl = gsap.timeline({ paused: true });
  const est = { t: 0 }; tl.to(est, { t: FIM, duration: FIM, ease: "none", onUpdate: () => desenhar(est.t) }, 0);
  desenhar(0);
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
  window.addEventListener("hf-seek", (ev) => desenhar(ev.detail.time));
  window.__palco = { desenhar, ini, FIM };
})();
