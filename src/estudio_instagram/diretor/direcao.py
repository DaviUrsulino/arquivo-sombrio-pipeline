"""Diretor: transforma as frases do roteiro num storyboard, cena por cena, usando só o que o motor sabe desenhar.

Regra central (estudo de referências): a frase escolhe a cena. Cada frase vira UMA ação do robô com UM objeto
concreto que mostra a ideia da frase, dentro de um mundo que combina com o tema. Nada de cena repetida.

O resultado é validado e, quando dá, consertado aqui mesmo (valor fora do catálogo vira um padrão seguro), para
o vídeo nunca quebrar por causa de um campo errado do LLM.
"""

from ..llm import gerar_json
from . import catalogo as cat

SISTEMA = """Você é diretor de motion design de Reels animados em 3D (estilo brinquedo de vinil, como os perfis de
animação que mais viralizam). O protagonista é sempre o mesmo robô (marca do perfil). Você recebe as frases
narradas e escreve, para CADA frase, a cena que aparece enquanto ela é dita.

PRINCÍPIOS:
- A FRASE ESCOLHE A CENA: o objeto mostra a coisa concreta da frase (dinheiro = moedas, tempo = relógio, notícia =
  jornal, liberou = cadeado abrindo, muita gente = equipe, ranking = troféu/auditório, número = contador...).
  O robô sempre FAZ algo com o objeto (ação). Nunca deixe o robô só parado.
- MUNDO pelo tema do vídeo (ver lista). Pode mudar de mundo no meio para marcar virada (máximo 3 mundos no vídeo).
  Use o mundo "cor" (fundo chapado) em 1 frase abstrata ou de número grande, para variar o ritmo.
- Nada repete em cenas seguidas: ação, objeto e câmera mudam a cada cena.
- "titulo": pílula no topo, 1 a 3 palavras MAIÚSCULAS (até 18 letras) que resumem a frase, como manchete. Nunca
  rótulos de roteiro (GANCHO, CTA, PROVA).
- "texto_objeto" (quando o objeto aceita texto): até 18 letras, o que está escrito no objeto (tela, placa, jornal).
- "numero" (quando o objeto aceita número): só número que está na frase ou nos fatos.
- HUD: um contador que sobe ao longo do vídeo e conta algo do tema (ex.: VÍDEOS, MINUTOS SALVOS, ESTRELAS, DIA).
  Cada cena pode ter "hud_valor" (número crescente). Ou "etapas" (2 a 5 itens) quando o vídeo é um passo a passo;
  aí hud_valor é quantas etapas já foram feitas.
- emoção do robô combina com a frase (surpreso no gancho chocante, pensando no "isso porque", rindo/feliz no "ou seja").
- transição: "chicote" na maioria, "voxel" em 1 ou 2 viradas fortes, "corte" no máximo 1 vez.
- A ÚLTIMA cena (o pedido de comentário) é sempre: acao "acena", objeto null, camera "frente", emocao "feliz".

CATÁLOGO:
__CATALOGO__

Responda só JSON:
{"mundo": "mundo principal", "chapeu": "chapéu do robô no vídeo todo (ou nenhum)",
 "hud": {"tipo": "contador", "rotulo": "ATÉ 12 LETRAS"} ou {"tipo": "etapas", "itens": ["...", "..."]},
 "cenas": [{"titulo": "...", "mundo": "(opcional, só se mudar)", "fundo_cor": "(só no mundo cor)", "acao": "...",
   "objeto": "... ou null", "texto_objeto": "...", "numero": 0, "camera": "...", "emocao": "...",
   "chapeu": "(opcional)", "hud_valor": 0, "transicao": "..."}]}
O número de cenas é EXATAMENTE o número de frases, na mesma ordem."""


def _usuario(frases: list[str], fatos: str) -> str:
    linhas = "\n".join(f"{i + 1}. {f}" for i, f in enumerate(frases))
    return f"FRASES ({len(frases)}):\n{linhas}\n\nFATOS DO TEMA (contexto):\n{fatos[:2500]}"


def consertar(plano: dict, frases: list[str], formato: str | None = None) -> tuple[dict, list[str]]:
    """Normaliza o storyboard; devolve (plano, erros graves que pedem nova tentativa)."""
    erros = []
    cenas = plano.get("cenas") or []
    if len(cenas) != len(frases):
        return plano, [f"precisa de exatamente {len(frases)} cenas (veio {len(cenas)})"]
    if plano.get("mundo") not in cat.MUNDOS:
        plano["mundo"] = "palco"
    if plano.get("chapeu") not in cat.CHAPEUS:
        plano["chapeu"] = "nenhum"
    hud = plano.get("hud") or {}
    if hud.get("tipo") not in ("contador", "etapas"):
        # o HUD fica na tela o vídeo inteiro: o rótulo tem que ter a ver com o formato, senão não dá motivo
        # pra ficar até o fim (ver estilo_formato.HUD_PADRAO e o Reels de 1,9 milhão do @escolhas.app)
        from .. import estilo_formato
        plano["hud"] = estilo_formato.hud(formato)
    mundos_usados = set()
    anterior = {}
    for i, (c, f) in enumerate(zip(cenas, frases)):
        c["fala"] = f
        if c.get("mundo") and c["mundo"] not in cat.MUNDOS:
            c.pop("mundo")
        mundos_usados.add(c.get("mundo") or plano["mundo"])
        if c.get("mundo") == "cor" and c.get("fundo_cor") not in cat.CORES_FUNDO:
            c["fundo_cor"] = ["roxo", "amarelo", "azul", "rosa"][i % 4]
        if c.get("acao") not in cat.ACOES:
            erros.append(f"cena {i + 1}: ação '{c.get('acao')}' não existe")
            c["acao"] = ["aponta", "apresenta", "segura", "observa"][i % 4]
        obj = c.get("objeto")
        if obj in ("", "null", "nenhum"):
            c["objeto"] = obj = None
        if obj is not None and obj not in cat.OBJETOS:
            erros.append(f"cena {i + 1}: objeto '{obj}' não existe")
            c["objeto"] = None
        if c.get("camera") not in cat.CAMERAS:
            c["camera"] = cat.CAMERAS[i % len(cat.CAMERAS)]
        if c.get("emocao") not in cat.EMOCOES:
            c["emocao"] = "feliz"
        if c.get("chapeu") and c["chapeu"] not in cat.CHAPEUS:
            c.pop("chapeu")
        if c.get("transicao") not in cat.TRANSICOES:
            c["transicao"] = "chicote"
        c["titulo"] = str(c.get("titulo") or "").upper()[:22]
        if c.get("texto_objeto"):
            c["texto_objeto"] = str(c["texto_objeto"]).upper()[:22]
        try:
            if c.get("numero") is not None:
                c["numero"] = float(str(c["numero"]).replace(".", "").replace(",", ".")) if isinstance(c["numero"], str) else float(c["numero"])
        except ValueError:
            c.pop("numero")
        if i > 0:
            for campo in ("acao", "camera"):
                if c.get(campo) == anterior.get(campo):
                    alternativas = cat.CAMERAS if campo == "camera" else ["aponta", "apresenta", "observa", "pula", "segura"]
                    c[campo] = next(a for a in alternativas if a != anterior.get(campo))
            if c.get("objeto") and c.get("objeto") == anterior.get("objeto"):
                erros.append(f"cena {i + 1}: objeto repetido da cena anterior")
        anterior = c
    _variedade(plano, cenas)
    final = cenas[-1]
    final.update({"acao": "acena", "objeto": None, "camera": "frente", "emocao": "feliz"})
    if len(mundos_usados) > 4:
        erros.append("mundos demais (máximo 3)")
    sem_objeto = sum(1 for c in cenas[:-1] if not c.get("objeto"))
    if sem_objeto > 1:
        erros.append(f"{sem_objeto} cenas sem objeto; toda cena (menos a última) precisa de um objeto concreto")
    return plano, erros


ACOES_DE_GANCHO = ("assusta", "aponta", "segura", "apresenta", "comemora", "carimba", "martela")
MUNDO_DE_VIRADA = {"palco": "oficina", "oficina": "laboratorio", "noir": "escritorio", "apartamento": "cidade",
                   "espaco": "laboratorio", "laboratorio": "oficina", "escritorio": "cidade", "cidade": "escritorio",
                   "auditorio": "palco", "cor": "palco"}


def _variedade(plano: dict, cenas: list[dict]):
    """Regras medidas pelo crítico na 1ª rodada: gancho forte, 3 mundos, câmeras variadas, HUD sempre subindo."""
    n = len(cenas)
    c0 = cenas[0]  # gancho: câmera chegando perto, ação forte, surpresa
    if c0.get("camera") not in ("aproxima", "baixo", "orbita"):
        c0["camera"] = "aproxima"
    if c0.get("acao") not in ACOES_DE_GANCHO:
        c0["acao"] = "assusta"
    if c0.get("emocao") in ("neutro", "triste", None):
        c0["emocao"] = "surpreso"
    # pelo menos 3 mundos diferentes num vídeo de 6+ cenas (um deles o fundo chapado)
    principal = plano["mundo"]
    mundo_de = lambda c: c.get("mundo") or principal
    if n >= 6 and len({mundo_de(c) for c in cenas}) < 3:
        if not any(mundo_de(c) == "cor" for c in cenas):
            k = next((i for i, c in enumerate(cenas) if str(c.get("fala", "")).lower().startswith("e olha")), n // 2 + 1)
            cenas[k]["mundo"], cenas[k]["fundo_cor"] = "cor", cenas[k].get("fundo_cor") or "amarelo"
        if len({mundo_de(c) for c in cenas}) < 3:
            k = 2 if mundo_de(cenas[2]) == principal else 3
            cenas[k]["mundo"] = MUNDO_DE_VIRADA.get(principal, "oficina")
    # nenhum mundo em mais de 3 cenas (o crítico reprovou 4 cenas seguidas na oficina)
    contagem = {}
    for i, c in enumerate(cenas[:-1]):
        m = mundo_de(c)
        contagem[m] = contagem.get(m, 0) + 1
        if contagem[m] > 3:
            alt = MUNDO_DE_VIRADA.get(m, "palco")
            if i and mundo_de(cenas[i - 1]) == alt:
                alt = "cor"
            c["mundo"] = alt
            if alt == "cor":
                c["fundo_cor"] = c.get("fundo_cor") or ["rosa", "azul", "verde"][i % 3]
            contagem[alt] = contagem.get(alt, 0) + 1
    # câmera: nenhuma mais de 2 vezes e nunca igual à anterior
    usos = {}
    for i, c in enumerate(cenas[:-1]):
        cam = c["camera"]
        if usos.get(cam, 0) >= 2 or (i and cam == cenas[i - 1]["camera"]):
            cam = min(cat.CAMERAS, key=lambda x: (usos.get(x, 0), x == cenas[i - 1]["camera"] if i else False))
            c["camera"] = cam
        usos[cam] = usos.get(cam, 0) + 1
    # HUD contador: valores crescentes em todas as cenas (um estado que avança é o que prende)
    if plano.get("hud", {}).get("tipo") == "contador":
        vals = [c.get("hud_valor") for c in cenas]
        ok = all(isinstance(v, (int, float)) for v in vals) and all(b > a for a, b in zip(vals, vals[1:-1]))
        if not ok:
            topo = max([v for v in vals if isinstance(v, (int, float))] + [100])
            for i, c in enumerate(cenas):
                c["hud_valor"] = round(topo * (i / max(1, n - 2)) ** 1.6) if i < n - 1 else topo


def dirigir(frases: list[str], fatos: str, palavra: str, llm=gerar_json, tentativas: int = 3,
            formato: str | None = None) -> dict:
    sistema = SISTEMA.replace("__CATALOGO__", cat.para_llm())
    pedido = _usuario(frases, fatos)
    melhor, erros = None, ["sem resposta"]
    for _ in range(tentativas):
        plano = llm(sistema, pedido)
        plano, erros = consertar(plano, frases, formato)
        melhor = plano
        if not erros:
            break
        pedido = _usuario(frases, fatos) + "\n\nCORRIJA:\n- " + "\n- ".join(erros)
    if melhor is None or len(melhor.get("cenas") or []) != len(frases):
        raise RuntimeError("storyboard inválido: " + "; ".join(erros))
    melhor["palavra"] = palavra
    return melhor
