#!/usr/bin/env python3
"""Injeção de defeitos automática: prova se os seus testes realmente falham quando o código quebra.

Uso:
    python3 ferramentas/mutar.py src/regras.py --comando "python3 -m unittest -q"
    python3 ferramentas/mutar.py src/regras.py --comando "npm test --silent" --max 40

Para cada ponto do arquivo onde existe um operador (>=, ==, +, and, True...), troca por outro, roda a suíte e
informa se algum teste falhou (PEGOU) ou se tudo continuou verde (SOBREVIVEU). Sobrevivente = falta teste.
O arquivo é sempre restaurado ao final, mesmo com Ctrl+C. Rode com o git limpo, por segurança.
Funciona em qualquer linguagem de sintaxe parecida com C/Python/JavaScript.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

TROCAS = [(">=", ">"), (">", ">="), ("<=", "<"), ("<", "<="), ("==", "!="), ("!=", "=="),
          (" + ", " - "), (" - ", " + "), (" * ", " / "), (" and ", " or "), (" or ", " and "),
          ("&&", "||"), ("||", "&&"), ("True", "False"), ("False", "True"), ("true", "false"), ("false", "true")]
COMENTARIO = re.compile(r"^\s*(#|//|\*|/\*)")


def pontos(linhas: list[str]):
    for i, linha in enumerate(linhas):
        if COMENTARIO.match(linha):
            continue
        for velho, novo in TROCAS:
            for achado in re.finditer(re.escape(velho), linha):
                antes = linha[achado.start() - 1] if achado.start() > 0 else ""
                depois = linha[achado.end()] if achado.end() < len(linha) else ""
                prefixo = linha[: achado.start()]
                if prefixo.count('"') % 2 or prefixo.count("'") % 2 or prefixo.count("`") % 2:
                    continue  # dentro de texto (mensagem, string): mudar não altera comportamento
                if velho in (">", "<") and (depois in "=<>" or antes in "=<>-!"):
                    continue  # parte de >=, <=, >>, ->, =>: não é o operador simples
                yield i, achado.start(), velho, novo


# Sem cache de bytecode: o .pyc de um defeito anterior (mesmo tamanho, mesmo segundo) seria reaproveitado e daria resultado falso.
AMBIENTE = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def principal() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo")
    ap.add_argument("--comando", required=True, help="comando que roda os testes (sai com código != 0 se falhar)")
    ap.add_argument("--max", type=int, default=30, help="máximo de defeitos a injetar (padrão 30)")
    ap.add_argument("--tempo", type=int, default=120, help="limite em segundos por execução")
    args = ap.parse_args()

    caminho = Path(args.arquivo)
    original = caminho.read_text(encoding="utf-8")
    base = subprocess.run(args.comando, shell=True, capture_output=True, timeout=args.tempo, env=AMBIENTE)
    if base.returncode != 0:
        print("A suíte já falha SEM defeito injetado. Conserte os testes antes de medir.")
        return 2
    linhas = original.splitlines(keepends=True)
    candidatos = list(pontos(linhas))[: args.max]
    pegos, vivos = 0, []
    try:
        for i, col, velho, novo in candidatos:
            mutada = list(linhas)
            mutada[i] = linhas[i][:col] + novo + linhas[i][col + len(velho):]
            caminho.write_text("".join(mutada), encoding="utf-8")
            try:
                r = subprocess.run(args.comando, shell=True, capture_output=True, timeout=args.tempo, env=AMBIENTE)
                falhou = r.returncode != 0
            except subprocess.TimeoutExpired:
                falhou = True  # laço infinito causado pelo defeito também conta como detectado
            rotulo = f"{caminho}:{i + 1}  '{velho.strip()}' -> '{novo.strip()}'"
            if falhou:
                pegos += 1
                print(f"PEGOU       {rotulo}")
            else:
                vivos.append(rotulo)
                print(f"SOBREVIVEU  {rotulo}")
    finally:
        caminho.write_text(original, encoding="utf-8")
    total = len(candidatos)
    if not total:
        print("Nenhum ponto de mutação encontrado neste arquivo.")
        return 0
    print(f"\nPlacar: {pegos}/{total} defeitos detectados ({100 * pegos // total}%).")
    if vivos:
        print("Sobreviventes (escreva um teste que falhe para cada um, ou explique por que é equivalente):")
        for v in vivos:
            print("  -", v)
    return 1 if vivos else 0


if __name__ == "__main__":
    sys.exit(principal())
