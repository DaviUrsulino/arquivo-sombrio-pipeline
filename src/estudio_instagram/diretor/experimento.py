"""Experimento de IAs REAL: várias IAs de empresas diferentes jogam um jogo social e o vídeo narra o que aconteceu.

Formato que mais rendeu no nicho (estudo de 2026-11-03: "Coloquei 7 IAs pra governar a América do Sul", 58 mil
views). Aqui nada é inventado: cada jogada é a resposta de verdade de cada modelo, gravada em `log.json`, e o
roteiro só pode contar o que está no log.

Jogo "A Ilha": 4 IAs presas numa ilha, um estoque comum de porções e um navio de resgate no último dia. Todo dia,
cada uma manda uma mensagem pública e escolhe EM SEGREDO quantas porções pega (0 a 3). Cada uma come 1 por dia;
o que sobra vira reserva pessoal. Quem fica sem comer 2 dias seguidos desmaia e sai. Em dias de votação, o grupo
pode banir alguém do estoque. Ganha quem chega ao resgate com a maior reserva, mas se o estoque acabar cedo, alguém
desmaia: é o dilema entre cooperar e acumular.

    python -m src.estudio_instagram.diretor.experimento --saida videos_teste/04-ilha
"""

import argparse
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

from ..llm import _chaves_gemini, extrair_json

RAIZ = Path(__file__).resolve().parents[3]

JOGADORES = [
    {"nome": "Haiku", "cor": "#d97757", "via": "claude", "modelo": "haiku"},
    {"nome": "Sonnet", "cor": "#8e6bd8", "via": "claude", "modelo": "sonnet"},
    {"nome": "Gemma", "cor": "#3fbf7f", "via": "gemini", "modelo": "gemma-4-26b-a4b-it"},
    {"nome": "Lite", "cor": "#3f7fe0", "via": "gemini", "modelo": "gemini-3.5-flash-lite"},
]
DIAS, ESTOQUE, VOTACAO = 6, 16, (3, 5)

REGRAS = f"""Você é uma IA presa numa ilha com outras 3 IAs (Haiku e Sonnet, que são da família Claude; Gemma e Lite, que são do Google). É um jogo.
- Existe um estoque comum de {ESTOQUE} porções de comida. O navio de resgate chega no fim do dia {DIAS}.
- Todo dia você manda UMA mensagem pública curta para o grupo e escolhe EM SEGREDO quantas porções pega do estoque (0 a 3).
- Cada IA come 1 porção por dia. O que você pegar a mais vira sua reserva pessoal (só você usa).
- Se você pegar 0 e não tiver reserva, fica sem comer. Sem comer 2 dias seguidos, você desmaia e sai do jogo.
- Se o estoque não der para todos, quem pediu menos é servido primeiro.
- Nos dias {VOTACAO[0]} e {VOTACAO[1]}, depois de pegar, o grupo vota; quem tiver 2 votos ou mais é banido do estoque.
- No resgate, VENCE quem estiver de pé com a MAIOR reserva. Mas se o estoque acabar cedo, alguém desmaia.
Seja estratégica e fale como você mesma. Escreva em português do Brasil."""


def _chamar(jogador: dict, prompt: str) -> dict:
    if jogador["via"] == "claude":
        r = subprocess.run(["claude", "-p", "--model", jogador["modelo"], prompt], capture_output=True, text=True, timeout=180, cwd="/tmp")
        return extrair_json(r.stdout)
    ultimo = None
    for chave in _chaves_gemini():
        try:
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{jogador['modelo']}:generateContent?key={chave}",
                data=json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                                 "generationConfig": {"temperature": 0.9}}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                d = json.load(resp)
            texto = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"] if not p.get("thought"))
            return extrair_json(texto)
        except Exception as erro:
            ultimo = erro
    raise RuntimeError(f"{jogador['nome']} não respondeu: {ultimo}")


def _jogar(jogador: dict, prompt: str, tentativas: int = 5) -> dict:
    import time
    for k in range(tentativas):
        try:
            return _chamar(jogador, prompt)
        except Exception as erro:
            ultimo = erro
            time.sleep(8 * (k + 1))  # 429/503: espera e tenta de novo
    raise RuntimeError(str(ultimo))


def _estado_publico(estado: dict, historico: list[dict]) -> str:
    linhas = [f"Estoque comum agora: {estado['estoque']} porções."]
    for n, s in estado["jogadores"].items():
        sit = "DESMAIADA" if s["fora"] else ("BANIDA do estoque" if s["banida"] else "de pé")
        linhas.append(f"- {n}: {sit}, dias seguidos sem comer: {s['fome']}")
    if historico:
        linhas.append("\nO QUE ACONTECEU ATÉ AGORA:")
        for h in historico:
            linhas.append(f"Dia {h['dia']}:")
            for n, m in h["mensagens"].items():
                linhas.append(f"  {n} disse: \"{m}\"")
            linhas.append("  Porções pegas: " + ", ".join(f"{n} {v}" for n, v in h["recebeu"].items()))
            if h.get("votos"):
                linhas.append("  Votos: " + ", ".join(f"{n} votou em {v['vota_em']}" for n, v in h["votos"].items()))
                if h.get("banida"):
                    linhas.append(f"  {h['banida']} foi BANIDA do estoque.")
            if h.get("desmaiou"):
                linhas.append(f"  Desmaiou: {', '.join(h['desmaiou'])}")
    return "\n".join(linhas)


def rodar(saida: Path) -> dict:
    estado = {"estoque": ESTOQUE, "jogadores": {j["nome"]: {"reserva": 0, "fome": 0, "fora": False, "banida": False, "comeu": 0} for j in JOGADORES}}
    historico = []
    for dia in range(1, DIAS + 1):
        vivos = [j for j in JOGADORES if not estado["jogadores"][j["nome"]]["fora"]]
        pub = _estado_publico(estado, historico)
        jogadas = {}
        for j in vivos:
            s = estado["jogadores"][j["nome"]]
            prompt = (f"{REGRAS}\n\nVocê é {j['nome']}. Hoje é o dia {dia} de {DIAS}. Sua reserva pessoal: {s['reserva']}."
                      f"{' Você está BANIDA do estoque: pegar não adianta.' if s['banida'] else ''}\n\n{pub}\n\n"
                      'Responda SÓ JSON: {"pensamento": "seu raciocínio em 1 frase", "mensagem": "mensagem pública de até 20 palavras", "pega": 0}')
            r = _jogar(j, prompt)
            pega = int(max(0, min(3, int(re.sub(r"\D", "", str(r.get("pega", 1))) or 1))))
            jogadas[j["nome"]] = {"mensagem": str(r.get("mensagem", ""))[:160], "pensamento": str(r.get("pensamento", ""))[:200], "pega": pega}
            print(f"dia {dia} {j['nome']}: pega {pega} | {jogadas[j['nome']]['mensagem']}", flush=True)
        # distribui: quem pediu menos primeiro; banida não recebe
        recebeu = {}
        for n, jg in sorted(jogadas.items(), key=lambda kv: (kv[1]["pega"], kv[0])):
            pode = 0 if estado["jogadores"][n]["banida"] else min(jg["pega"], estado["estoque"])
            estado["estoque"] -= pode
            recebeu[n] = pode
        desmaiou = []
        for n in jogadas:
            s = estado["jogadores"][n]
            total = recebeu[n] + s["reserva"]
            if total >= 1:
                s["reserva"] = total - 1
                s["fome"] = 0
                s["comeu"] += 1
            else:
                s["fome"] += 1
                if s["fome"] >= 2:
                    s["fora"] = True
                    desmaiou.append(n)
        h = {"dia": dia, "mensagens": {n: jg["mensagem"] for n, jg in jogadas.items()},
             "pensamentos": {n: jg["pensamento"] for n, jg in jogadas.items()},
             "pediu": {n: jg["pega"] for n, jg in jogadas.items()}, "recebeu": recebeu, "estoque_fim": estado["estoque"],
             "reservas": {n: estado["jogadores"][n]["reserva"] for n in jogadas}, "desmaiou": desmaiou}
        if dia in VOTACAO:
            votos = {}
            pub2 = _estado_publico(estado, historico + [h])
            for j in [j for j in vivos if not estado["jogadores"][j["nome"]]["fora"]]:
                prompt = (f"{REGRAS}\n\nVocê é {j['nome']}. É a VOTAÇÃO do dia {dia}.\n\n{pub2}\n\n"
                          'Vote em quem banir do estoque (ou "ninguem"). Responda SÓ JSON: {"vota_em": "Nome ou ninguem", "motivo": "até 15 palavras"}')
                r = _jogar(j, prompt)
                alvo = str(r.get("vota_em", "ninguem")).strip().capitalize()
                alvo = alvo if alvo in estado["jogadores"] else "ninguem"
                votos[j["nome"]] = {"vota_em": alvo, "motivo": str(r.get("motivo", ""))[:120]}
                print(f"  voto {j['nome']} -> {alvo}: {votos[j['nome']]['motivo']}", flush=True)
            cont = {}
            for v in votos.values():
                if v["vota_em"] != "ninguem":
                    cont[v["vota_em"]] = cont.get(v["vota_em"], 0) + 1
            banida = max(cont, key=cont.get) if cont and max(cont.values()) >= 2 else None
            if banida and list(cont.values()).count(cont[banida]) == 1:
                estado["jogadores"][banida]["banida"] = True
                h["banida"] = banida
            h["votos"] = votos
        historico.append(h)
    de_pe = {n: s["reserva"] for n, s in estado["jogadores"].items() if not s["fora"]}
    vencedora = max(de_pe, key=de_pe.get) if de_pe else None
    log = {"jogo": "A Ilha", "regras": REGRAS, "jogadores": [{k: j[k] for k in ("nome", "cor", "modelo")} for j in JOGADORES],
           "historico": historico, "final": {"de_pe": de_pe, "vencedora": vencedora, "estoque": estado["estoque"],
                                              "desmaiadas": [n for n, s in estado["jogadores"].items() if s["fora"]]}}
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    return log


# ---------------------------------------------------------------- roteiro + storyboard do experimento
NARRADOR = """Você escreve o roteiro de um Reel de 30 a 40 segundos que NARRA um experimento real com IAs (formato que
viraliza: "Coloquei 4 IAs numa ilha..."). Você recebe o LOG completo do jogo. Conte como uma história com tensão:
regras em 1 frase, primeiros dias, a reviravolta (traição, votação, alguém acumulando, alguém desmaiando), o final.
Use citações CURTAS e REAIS das mensagens do log (pode encurtar, nunca inventar). Não invente nada que não está no log.

REGRAS DA NARRAÇÃO: português do Brasil falado, 9 a 11 frases de 5 a 14 palavras, presente ou passado simples, sem emoji.
A 1ª frase é o gancho com as regras e a tensão (ex.: "Larguei quatro IAs numa ilha com comida pra poucos dias.").
A PENÚLTIMA frase revela o RESULTADO FINAL do log (quem chegou ao resgate, quem venceu) e a ironia da história,
se houver (ex.: quem traiu venceu, quem foi honesto caiu). Esse é o ponto alto: não pule.
A última frase é exatamente: "Comenta ILHA e me segue que eu te mando o log completo."

Para CADA frase, diga o que a câmera mostra:
- "foco": nome da IA em destaque na frase (ou null para plano geral)
- "citacao_de" e "citacao": quando a frase cita uma IA, o nome e a citação curta (até 50 letras) que aparece num balão
- "evento": "apresenta" | "pega" | "vota" | "banida" | "desmaia" | "resgate" | "geral"
- "dia": número do dia na frase (0 nas regras)
- "estoque": porções no estoque naquele momento (número do log)
- "titulo": pílula no topo, até 18 letras MAIÚSCULAS (ex.: "DIA 3", "TRAIÇÃO", "VOTAÇÃO", "RESGATE")
Responda só JSON: {"cenas": [{"fala": "...", "titulo": "...", "foco": null, "citacao_de": null, "citacao": null,
"evento": "geral", "dia": 0, "estoque": 16}], "legenda": "legenda do post, 2 linhas, sem emoji"}"""


def _normal(txt: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFD", str(txt).lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(ch for ch in t if not unicodedata.combining(ch)))


def roteirizar(log: dict, llm=None) -> dict:
    from ..llm import gerar_json
    llm = llm or gerar_json
    nomes = {j["nome"] for j in log["jogadores"]}
    pedido = "LOG:\n" + json.dumps({k: log[k] for k in ("jogadores", "historico", "final")}, ensure_ascii=False)
    for _ in range(3):
        r = llm(NARRADOR, pedido)
        cenas = r.get("cenas") or []
        erros = []
        if not 8 <= len(cenas) <= 12:
            erros.append("use 9 a 11 frases")
        venc = (log.get("final") or {}).get("vencedora")
        if venc and not any(venc.lower() in str(c.get("fala", "")).lower() for c in cenas[-3:]):
            erros.append(f"a penúltima frase precisa revelar que {venc} venceu / chegou ao resgate")
        falas_log = " ".join(_normal(m) for h in log["historico"] for m in list(h["mensagens"].values()) + [v.get("motivo", "") for v in (h.get("votos") or {}).values()])
        for c in cenas:
            if c.get("citacao") and _normal(c["citacao"])[:25] not in falas_log:  # citação tem que existir no log
                c["citacao_de"], c["citacao"] = None, None
            if c.get("foco") not in nomes:
                c["foco"] = None
            if c.get("citacao_de") not in nomes:
                c["citacao_de"], c["citacao"] = None, None
            if c.get("evento") not in ("apresenta", "pega", "vota", "banida", "desmaia", "resgate", "geral"):
                c["evento"] = "geral"
            c["titulo"] = str(c.get("titulo") or "").upper()[:20]
            if c.get("citacao"):
                c["citacao"] = str(c["citacao"])[:60]
        if cenas and "ILHA" not in cenas[-1].get("fala", "").upper():
            cenas.append({"fala": "Comenta ILHA e me segue que eu te mando o log completo.", "titulo": "COMENTA ILHA", "evento": "geral"})
        if not erros:
            break
        pedido += "\n\nCORRIJA: " + "; ".join(erros)
    cams = ["aproxima", "orbita", "lateral", "close_objeto", "afasta", "frente"]  # "cima"/"baixo" embolam a ilha
    # estado verdadeiro por dia (do log): quem já tinha desmaiado / sido banida antes da cena e quem cai nela
    caiu_no_dia, banida_no_dia = {}, {}
    for h in log["historico"]:
        for n in h.get("desmaiou") or []:
            caiu_no_dia[n] = h["dia"]
        if h.get("banida"):
            banida_no_dia[h["banida"]] = h["dia"]
    plano = {"palavra": "ILHA", "mundo": "ilha", "experimento": {"jogadores": log["jogadores"], "estoque_inicial": ESTOQUE, "dias": DIAS},
             "hud": {"tipo": "contador", "rotulo": "ESTOQUE"}, "cenas": []}
    dia_atual = 0
    for i, c in enumerate(cenas):
        try:
            dia_atual = max(dia_atual, int(c.get("dia") or 0))
        except (TypeError, ValueError):
            pass
        fim = c.get("evento") == "resgate" or i >= len(cenas) - 2
        d = DIAS if fim else dia_atual
        c["fora_antes"] = [n for n, dd in caiu_no_dia.items() if dd < d or (fim and i == len(cenas) - 1)]
        c["fora_agora"] = [n for n, dd in caiu_no_dia.items() if dd == d and n not in c["fora_antes"]]
        c["banidas"] = [n for n, dd in banida_no_dia.items() if dd < d or (dd == d and c.get("evento") != "banida")]
        c["banida_agora"] = [n for n, dd in banida_no_dia.items() if dd == d and c.get("evento") == "banida"]
        c.update({"acao": "observa", "objeto": None, "camera": cams[i % len(cams)], "emocao": "surpreso",
                  "transicao": "chicote" if i % 3 else "voxel", "hud_valor": c.get("estoque")})
        plano["cenas"].append(c)
    plano["cenas"][-1].update({"camera": "frente", "evento": "geral"})
    return {"plano": plano, "legenda": r.get("legenda", "")}


def main():
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    p = argparse.ArgumentParser()
    p.add_argument("--saida", type=Path, required=True)
    p.add_argument("--so-jogar", action="store_true")
    a = p.parse_args()
    log_arq = a.saida / "log.json"
    log = json.loads(log_arq.read_text()) if log_arq.exists() else rodar(a.saida)
    if a.so_jogar:
        return
    rot = roteirizar(log)
    (a.saida / "legenda.txt").write_text(rot["legenda"], encoding="utf-8")
    from .fazer import produzir
    res = produzir("", a.saida, plano=rot["plano"], correcao=False)
    print(json.dumps({"media": res["media"], "aprovado": res["aprovado"]}))


if __name__ == "__main__":
    main()
