"""Faz um vídeo de ponta a ponta com direção: fatos -> roteiro (3 ganchos) -> storyboard -> voz -> montagem ->
render -> portão de qualidade (com uma rodada automática de correção se reprovar).

    python -m src.estudio_instagram.diretor.fazer --repo dono/nome --saida videos_teste/01-nome
    python -m src.estudio_instagram.diretor.fazer --fatos fatos.txt --saida videos_teste/02-tema
    python -m src.estudio_instagram.diretor.fazer --plano plano.json --saida ...   (storyboard pronto, pula o LLM)

Não publica nada: só gera a pasta com final.mp4, folha_cenas.jpg, portao.json, roteiro.json, plano.json e legenda.txt.
"""

import argparse
import json
import shutil
from pathlib import Path

from dotenv import load_dotenv

from . import direcao, montar, narracao, portao, roteiro

RAIZ = Path(__file__).resolve().parents[3]


def fatos_do_repo(repo: str) -> str:
    from .. import github_dados
    from ..roteirista import buscar_readme
    d = github_dados.buscar(repo)
    readme = buscar_readme(repo)
    return (f"Repositório no GitHub: {d.repo} (endereço {d.url})\nEstrelas no GitHub: {d.estrelas}\nLicença: {d.licenca}\n"
            f"Descrição: {d.descricao}\n\nREADME (trecho):\n{readme[:5000]}")


def _renderizar(pasta_proj: Path, mp4: Path):
    """Render local com GPU do navegador (WebGL por software levava ~13 min por vídeo de 28 s)."""
    import os
    from ..render import _hyperframes
    mp4 = Path(mp4).resolve()
    extra = ["--browser-gpu", "--workers", os.environ.get("PALCO_WORKERS", "3")] if os.environ.get("PALCO_GPU", "0") == "1" else []
    _hyperframes("render", "--quality", "high", *extra, "--output", str(mp4), pasta=Path(pasta_proj))


def produzir(fatos: str, saida: Path, gancho: int = 0, plano: dict | None = None, rot: dict | None = None,
             correcao: bool = True, voz=None, chapeu: str | None = None, mundo: str | None = None,
             palavra: str | None = None) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    voz = voz or narracao.voz_padrao()
    if plano is None:
        rot = rot or roteiro.escrever(fatos)
        if palavra:  # a palavra da pauta manda: o respondedor de Direct procura exatamente ela
            rot["palavra"] = palavra.upper()
            rot["cta"] = f"Comenta {rot['palavra']} e me segue que eu te mando o link."
        (saida / "roteiro.json").write_text(json.dumps(rot, ensure_ascii=False, indent=1), encoding="utf-8")
        frases = roteiro.frases(rot, gancho)
        plano = direcao.dirigir(frases, fatos, rot["palavra"])
        if chapeu:
            plano["chapeu"] = chapeu
        if mundo:
            plano["mundo"] = mundo
    frases = [c["fala"] for c in plano["cenas"]]
    info = narracao.narrar_frases(frases, voz, saida / "voz.wav")
    (saida / "falas.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")

    def rodada(pl: dict, nome: str) -> dict:
        proj = saida / f"proj_{nome}"
        montar.montar(pl, info, saida / "voz.wav", proj)
        mp4 = saida / f"{nome}.mp4"
        _renderizar(proj, mp4)
        res = portao.avaliar(mp4, info, saida)
        shutil.copy(saida / "folha_cenas.jpg", saida / f"folha_{nome}.jpg")
        (saida / f"portao_{nome}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        (saida / f"plano_{nome}.json").write_text(json.dumps(pl, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{nome}] média {res['media']} aprovado={res['aprovado']} qa={res['qa']['problemas']}")
        return {"res": res, "mp4": mp4, "plano": pl, "nome": nome}

    v1 = rodada(plano, "v1")
    melhor = v1
    corr = (v1["res"].get("critica") or {}).get("correcoes") or []
    if correcao and not v1["res"]["aprovado"] and corr and rot is not None:
        extra = "\n\nUM CRÍTICO VIU OS QUADROS DA VERSÃO ANTERIOR E PEDIU (os números são as cenas):\n- " + "\n- ".join(corr)
        try:
            plano2 = direcao.dirigir(frases, fatos + extra, plano["palavra"])
            if chapeu:
                plano2["chapeu"] = chapeu
            v2 = rodada(plano2, "v2")
            if (v2["res"]["media"] or 0) >= (v1["res"]["media"] or 0):
                melhor = v2
        except Exception as erro:
            print("correção falhou:", erro)
    shutil.copy(melhor["mp4"], saida / "final.mp4")
    shutil.copy(saida / f"folha_{melhor['nome']}.jpg", saida / "folha_cenas.jpg")
    (saida / "plano.json").write_text(json.dumps(melhor["plano"], ensure_ascii=False, indent=1), encoding="utf-8")
    (saida / "portao.json").write_text(json.dumps(melhor["res"], ensure_ascii=False, indent=1), encoding="utf-8")
    if rot:
        (saida / "legenda.txt").write_text(rot.get("legenda", ""), encoding="utf-8")
    for p in saida.glob("proj_*"):  # economiza disco: guarda só o projeto vencedor
        if p.name != f"proj_{melhor['nome']}":
            shutil.rmtree(p, ignore_errors=True)
    return melhor["res"]


def main():
    load_dotenv(RAIZ / ".env")
    p = argparse.ArgumentParser()
    p.add_argument("--repo")
    p.add_argument("--fatos", type=Path)
    p.add_argument("--plano", type=Path)
    p.add_argument("--gancho", type=int, default=0)
    p.add_argument("--chapeu")
    p.add_argument("--mundo")
    p.add_argument("--sem-correcao", action="store_true")
    p.add_argument("--saida", type=Path, required=True)
    a = p.parse_args()
    if a.plano:
        res = produzir("", a.saida, plano=json.loads(a.plano.read_text(encoding="utf-8")), correcao=False)
    else:
        fatos = fatos_do_repo(a.repo) if a.repo else a.fatos.read_text(encoding="utf-8")
        (a.saida).mkdir(parents=True, exist_ok=True)
        (a.saida / "fatos.txt").write_text(fatos, encoding="utf-8")
        res = produzir(fatos, a.saida, gancho=a.gancho, correcao=not a.sem_correcao, chapeu=a.chapeu, mundo=a.mundo)
    print(json.dumps({"media": res["media"], "aprovado": res["aprovado"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
