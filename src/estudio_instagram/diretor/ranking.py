"""Ranking com prova: "as N skills mais instaladas pra X", com o número real de instalações do skills.sh.

Formato medido no estudo (macelista 16,9 mil; clubedasskills 12,3 mil): "#5 ... #1", cada item com 1 benefício
concreto e a métrica real como prova, em cenário de programa de auditório. A métrica vem do `npx skills find`,
nunca do LLM.

    python -m src.estudio_instagram.diretor.ranking --busca "social media" --busca "instagram" --tema "crescer no Instagram" --saida videos_teste/05-ranking
"""

import argparse
import json
import re
import subprocess
import urllib.request
from pathlib import Path

from ..llm import gerar_json

RAIZ = Path(__file__).resolve().parents[3]
LINHA = re.compile(r"^([\w.-]+/[\w.-]+)@([\w.: -]+?)\s+([\d.,]+)([KM]?) installs", re.M)


def buscar(consulta: str) -> list[dict]:
    out = subprocess.run(["npx", "--yes", "skills", "find", consulta], capture_output=True, text=True, timeout=180, cwd="/tmp").stdout
    out = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", out)
    itens = []
    for repo, skill, n, suf in LINHA.findall(out):
        v = float(n.replace(",", ""))
        v *= 1000 if suf == "K" else 1_000_000 if suf == "M" else 1
        itens.append({"repo": repo, "skill": skill.strip(), "instalacoes": int(v)})
    return itens


def descricao(repo: str, skill: str) -> str:
    """Primeira linha útil do SKILL.md (description do frontmatter), direto do GitHub."""
    for caminho in (f"skills/{skill}/SKILL.md", f"{skill}/SKILL.md", f".claude/skills/{skill}/SKILL.md", "SKILL.md"):
        for ramo in ("main", "master"):
            try:
                with urllib.request.urlopen(f"https://raw.githubusercontent.com/{repo}/{ramo}/{caminho}", timeout=15) as r:
                    txt = r.read().decode("utf-8", "replace")
                m = re.search(r"^description:\s*(.+)$", txt, re.M)
                if m:
                    return m.group(1).strip().strip('"')[:400]
            except Exception:
                continue
    return ""


ROTEIRISTA = """Você escreve o roteiro de um Reel-ranking de 30 a 40 segundos para o perfil @ursulino.ia. Recebe os ITENS
reais (skill, repositório, número real de instalações e descrição). Ordem: do 5º ao 1º (contagem regressiva).

- Frase 1 (gancho): "As cinco skills mais instaladas pra TEMA, e a primeira é ..." (provoque curiosidade sem revelar).
  Varie a forma, mas mantenha: número, tema de desejo do público, mistério sobre a 1ª.
- Uma frase por item: "Em quinto, NOME, com X mil instalações: o que ela faz por você em linguagem de leigo."
  (até 16 palavras; diga o número de instalações por extenso aproximado; o benefício só pode vir da descrição)
- Frase final antes do pedido: "Ou seja, ..." (o que a pessoa ganha usando as cinco).
- NÃO escreva o pedido de comentário (adicionado depois).
- Português do Brasil falado, sem emoji, sem símbolos, nomes de skill falados de forma pronunciável.
Responda só JSON: {"frases": ["gancho", "item 5", "item 4", "item 3", "item 2", "item 1", "Ou seja, ..."],
 "titulos": ["pílula de cada frase, até 18 letras MAIÚSCULAS"], "nomes_curtos": ["nome curto de cada item, 5º ao 1º"],
 "legenda": "legenda curta sem emoji"}"""

CHAPEUS = ["fone", "detetive", "capacete", "diretor", "coroa"]
OBJ_ITEM = ["livros", "lupa", "claquete", "grafico", "trofeu"]


def montar_plano(itens: list[dict], tema: str, palavra: str) -> tuple[dict, str]:
    fatos = json.dumps([{"posicao": 5 - k, **it} for k, it in enumerate(itens)], ensure_ascii=False)
    pedido = f"TEMA: {tema}\nITENS (do 5º ao 1º):\n{fatos}"
    r = None
    for _ in range(3):
        r = gerar_json(ROTEIRISTA, pedido)
        if len(r.get("frases") or []) == 7:
            break
        pedido += "\n\nCORRIJA: exatamente 7 frases."
    frases = r["frases"][:7] + [f"Comenta {palavra} e me segue que eu te mando as cinco."]
    titulos = (r.get("titulos") or []) + [""] * 8
    nomes = (r.get("nomes_curtos") or [it["skill"] for it in itens])
    cams = ["aproxima", "orbita", "lateral", "baixo", "close_objeto", "cima", "afasta"]
    cenas = [{"fala": frases[0], "titulo": titulos[0] or "TOP 5", "acao": "apresenta", "objeto": "trofeu", "camera": "aproxima",
              "emocao": "surpreso", "transicao": "corte", "hud_valor": 0, "mundo": "auditorio"}]
    for k, it in enumerate(itens):
        pos = 5 - k
        cenas.append({"fala": frases[k + 1], "titulo": f"#{pos} {str(nomes[k]).upper()}"[:20], "acao": ["aponta", "segura", "observa", "apresenta", "comemora"][k],
                      "objeto": "contador" if k % 2 == 0 else "estrela", "numero": it["instalacoes"], "texto_objeto": "INSTALAÇÕES",
                      "camera": cams[(k + 1) % len(cams)], "emocao": ["feliz", "surpreso", "pensando", "apaixonado", "rindo"][k],
                      "chapeu": CHAPEUS[k], "transicao": "voxel" if pos == 1 else "chicote", "hud_valor": k + 1,
                      "mundo": "auditorio" if pos in (5, 3, 1) else ("cor" if pos == 4 else "palco"), "fundo_cor": "roxo" if pos == 4 else None})
    cenas.append({"fala": frases[6], "titulo": titulos[6] or "OU SEJA", "acao": "pula", "objeto": "presente", "camera": "afasta", "emocao": "rindo",
                  "transicao": "chicote", "hud_valor": 5, "mundo": "cor", "fundo_cor": "amarelo"})
    cenas.append({"fala": frases[7], "titulo": f"COMENTA {palavra}", "acao": "acena", "objeto": None, "camera": "frente", "emocao": "feliz",
                  "transicao": "chicote", "hud_valor": 5, "mundo": "auditorio"})
    plano = {"palavra": palavra, "mundo": "auditorio", "chapeu": "nenhum", "hud": {"tipo": "contador", "rotulo": "RANKING"}, "cenas": cenas}
    return plano, r.get("legenda", "")


def main():
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    p = argparse.ArgumentParser()
    p.add_argument("--busca", action="append", required=True)
    p.add_argument("--tema", required=True)
    p.add_argument("--palavra", default="SKILLS")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--saida", type=Path, required=True)
    a = p.parse_args()
    vistos, itens = set(), []
    for q in a.busca:
        for it in buscar(q):
            chave = (it["repo"], it["skill"])
            if chave not in vistos:
                vistos.add(chave)
                itens.append(it)
    itens = sorted(itens, key=lambda x: x["instalacoes"], reverse=True)[: a.n]
    for it in itens:
        it["descricao"] = descricao(it["repo"], it["skill"])
    itens = list(reversed(itens))  # do 5º ao 1º
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "itens.json").write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
    plano, legenda = montar_plano(itens, a.tema, a.palavra)
    (a.saida / "legenda.txt").write_text(legenda, encoding="utf-8")
    from .fazer import produzir
    res = produzir("", a.saida, plano=plano, correcao=False)
    print(json.dumps({"media": res["media"], "aprovado": res["aprovado"]}))


if __name__ == "__main__":
    main()
