"""Identidades visuais (escritório, vila 3D, ...): vídeo montado a partir de um ACERVO de cenas, não de um molde fixo.

Cada identidade mora em modelos/identidades/<nome>/ (index.html + assets) e lê dois arquivos gerados aqui:
- assets/roteiro.js  -> window.ROT = {palavra, repo, cenas: [{fala, tipo, ...campos da cena}]}
- assets/falas.js    -> window.ESQ = {falas: [{texto, t, d}], duracao, boca, fps} + assets/voz.wav

O LLM recebe o repositório, o README e o gancho do roteirista e escolhe, para cada frase, um tipo de cena do
acervo da identidade e o conteúdo dela (títulos, linhas de tela, notificações...). Assim cada vídeo tem cenas
próprias do assunto, dentro do mesmo estilo. A última frase é sempre o pedido de comentário.
"""

import json
import random
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from .github_dados import DadosRepo
from .llm import gerar_json
from .voz import TAXA_AMOSTRA, aplicar_pronuncia

RAIZ = Path(__file__).resolve().parents[2]
PASTA = Path(__file__).resolve().parent / "modelos" / "identidades"
ASSETS_COMUNS = Path(__file__).resolve().parent / "modelos" / "assets"
PAUSA_S, INICIO_S, FIM_S = 0.25, 0.4, 1.2

REGRAS = """REGRAS GERAIS (valem para toda identidade):
- 5 frases faladas + a frase final de comentário (que você NÃO escreve, ela é adicionada depois). Cada frase com 6 a 11
  palavras, português do Brasil, verbo no presente, sem emoji, sem hashtag, sem símbolos.
- A 1ª frase é o GANCHO recebido, sem mudar o sentido (pode encurtar). Ele fala da dor ou do ganho de quem assiste.
- Vídeo curto (~20 s), como o Reel de 54 mil views do perfil: gancho -> o que a ferramenta faz de concreto (2 frases)
  -> prova (estrelas, empresa, número real do README) -> grátis/código aberto se for verdade.
- Use só fatos do README e dos dados. Não invente número, empresa nem recurso.
- Fale com quem NÃO é programador: nada de jargão (DOM, XPath, seletor, SDK) nas telas nem nas falas.
- titulo_b com no máximo 12 letras.
- Títulos falam do conteúdo (ex.: NÃO COBRA / SALÁRIO), nunca rótulos de roteiro como PROVA SOCIAL, GANCHO, CTA.
- Os campos de cada cena ficam no MESMO objeto da cena (não aninhe dentro de outra chave).
- Cada cena usa um tipo DIFERENTE do acervo sempre que der, e o conteúdo da tela mostra a coisa concreta da frase.
Responda só JSON: {"cenas": [{"fala": "...", "tipo": "...", ...campos do tipo}]}"""

ACERVOS = {
    "escritorio": """IDENTIDADE "ESCRITÓRIO": fundo preto com brilho vermelho, título em 2 linhas (titulo_a curto e claro,
titulo_b 1 a 2 palavras grandes, MAIÚSCULAS, até 14 letras), o funcionário de IA "Max" de terno e telas de sistema.
Todo item tem "titulo_a" e "titulo_b". Tipos do acervo e campos extras:
- "time": {"nomes": [2 a 4 apelidos curtos de funcionários, o 1º é o Max]}  (apresenta a equipe)
- "folha": {"cabecalho": "NOME DA TABELA", "linhas": [["RÓTULO", "VALOR"], ... 3 a 4], "total": ["TOTAL", "VALOR"]}
- "celular": {"notificacoes": [{"de": "QUEM", "texto": "mensagem curta"}, ... 1 a 2]}
- "conversor": {"janela": "MAX // ALGO", "linhas": [3 a 5 linhas curtas de saída, estilo terminal ou documento]}
- "grade": {"itens": [exatamente 4 rótulos curtos]}  (4 cartões que vão sendo marcados)
- "chat": {"pergunta": "pedido curto do usuário", "resposta": "resposta curta e concreta da IA"}
- "cracha": {}  (crachá com o nome real do repositório e as estrelas; use na frase da prova)""",
    "vila": """IDENTIDADE "VILA 3D": um mundo low-poly estilo jogo; o Robô Estagiário leva a tarefa até um prédio com telão,
a vila inteira assiste. A câmera muda a cada frase sozinha. Campos de topo (fora de cenas): "predio" (nome do prédio, até 12
letras MAIÚSCULAS, ex. CINEMA IA, OFICINA IA, CARTÓRIO IA), "contador" (o que o placar conta, até 10 letras, ex. DUBLADOS,
ARQUIVOS, BUGS), "objeto" (o que o robô carrega: "rolo", "caixa" ou "pasta"). Cada cena tem "tipo" e "tela" (o que o telão mostra):
- "aerea": vista da vila; tela {"titulo": "ANTES", "texto": "o problema em até 18 letras"}
- "entrega": robô leva o objeto; tela igual à anterior
- "passos": tela {"passos": [3 etapas de até 11 letras MAIÚSCULAS]}
- "resultado": tela {"titulo": "DEPOIS", "texto": "o resultado em até 18 letras"}
- "plateia": a vila chega pra ver; tela igual à anterior
- "placa": placa gigante com o repositório e estrelas (dados reais); tela igual à anterior
- "notebook": robô com notebook e confete; tela {"titulo": "GRÁTIS", "texto": "até 18 letras"}
Use 5 cenas, nesta ordem: aerea, passos, resultado, plateia, placa. Responda {"predio": ..., "contador": ..., "objeto": ..., "cenas": [...]}""",
}

TIPOS = {"escritorio": {"time", "folha", "celular", "conversor", "grade", "chat", "cracha"},
         "vila": {"aerea", "entrega", "passos", "resultado", "plateia", "placa", "notebook"}}


def identidades() -> list[str]:
    return sorted(ACERVOS)


def _usuario(dados: DadosRepo, readme: str, gancho: str) -> str:
    return (f"GANCHO: {gancho}\nRepositório: {dados.repo}\nDescrição: {dados.descricao}\nEstrelas: {dados.estrelas}\n"
            f"Licença: {dados.licenca}\n\nREADME (começo):\n{readme[:6000]}")


def problemas(nome: str, resposta: dict) -> list[str]:
    erros = []
    cenas = resposta.get("cenas")
    if not isinstance(cenas, list) or not 4 <= len(cenas) <= 6:
        return ["'cenas' precisa ter de 4 a 6 itens"]
    for i, c in enumerate(cenas):
        if isinstance(c.get(c.get("tipo")), dict):  # o LLM às vezes aninha os campos sob o nome do tipo
            c.update(c.pop(c["tipo"]))
        if c.get("tipo") not in TIPOS[nome]:
            erros.append(f"cena {i}: tipo '{c.get('tipo')}' fora do acervo")
        n = len((c.get("fala") or "").split())
        if not 4 <= n <= 14:
            erros.append(f"cena {i}: fala com {n} palavras")
        if nome == "escritorio" and not (c.get("titulo_a") and c.get("titulo_b")):
            erros.append(f"cena {i}: falta titulo_a/titulo_b")
    if nome == "vila" and not all(resposta.get(k) for k in ("predio", "contador", "objeto")):
        erros.append("faltam predio/contador/objeto")
    return erros


def planejar(nome: str, dados: DadosRepo, readme: str, gancho: str, palavra: str, llm=gerar_json, tentativas: int = 3) -> dict:
    sistema = ACERVOS[nome] + "\n\n" + REGRAS
    pedido = _usuario(dados, readme, gancho)
    for _ in range(tentativas):
        resposta = llm(sistema, pedido)
        erros = problemas(nome, resposta)
        if not erros:
            break
        pedido = _usuario(dados, readme, gancho) + "\n\nCORRIJA:\n- " + "\n- ".join(erros)
    else:
        raise RuntimeError("roteiro da identidade inválido: " + "; ".join(erros))
    resposta["cenas"].append({"fala": f"Comenta {palavra} que eu te mando o link no direct.", "tipo": "comenta",
                              "titulo_a": "QUER O LINK?", "titulo_b": "COMENTA"})
    resposta["palavra"] = palavra
    resposta["repo"] = {"nome": dados.repo, "descricao": dados.descricao, "estrelas": dados.estrelas, "url": dados.url}
    resposta["semente"] = random.Random(dados.repo).randint(1, 10_000)  # muda casas, cores e luz da vila por vídeo
    return resposta


def narrar(cenas: list[dict], voz, destino: Path) -> dict:
    """Fala cada frase, emenda com pausas curtas, grava voz.wav e devolve os tempos + envelope da boca (30 fps)."""
    import numpy as np  # só aqui: o resto do pacote não depende de numpy
    voz.preparar([aplicar_pronuncia(c["fala"])[0] for c in cenas]) if hasattr(voz, "preparar") else None
    falas, trechos, t = [], [], INICIO_S
    for c in cenas:
        pcm = np.frombuffer(voz.sintetizar(aplicar_pronuncia(c["fala"])[0]).audio_pcm, dtype=np.int16).astype(np.float32) / 32768
        nz = np.flatnonzero(np.abs(pcm) > 0.01)  # corta silêncio das pontas pra emendar no ritmo
        pcm = pcm[max(0, nz[0] - 240): nz[-1] + 480] if len(nz) else pcm
        falas.append({"texto": c["fala"], "t": round(t, 3), "d": round(len(pcm) / TAXA_AMOSTRA, 3)})
        trechos.append((t, pcm))
        t += len(pcm) / TAXA_AMOSTRA + PAUSA_S
    duracao = t - PAUSA_S + FIM_S
    mix = np.zeros(int(duracao * TAXA_AMOSTRA), dtype=np.float32)
    for ini, pcm in trechos:
        a = int(ini * TAXA_AMOSTRA)
        mix[a:a + len(pcm)] += pcm
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(TAXA_AMOSTRA)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    passo = TAXA_AMOSTRA // 30
    rms = [float(np.sqrt(np.mean(mix[i:i + passo] ** 2))) for i in range(0, len(mix), passo)]
    topo = max(rms) or 1
    return {"falas": falas, "duracao": round(duracao, 3), "boca": [round(min(1.0, r / topo * 1.6), 3) for r in rms], "fps": 30}


def montar(nome: str, plano: dict, voz, pasta: Path) -> float:
    """Copia a identidade pra `pasta`, grava roteiro, voz e trilha. Devolve a duração em segundos."""
    if pasta.exists():
        shutil.rmtree(pasta)
    shutil.copytree(PASTA / nome, pasta)
    assets = pasta / "assets"
    for arq in ("gsap.min.js", "three.min.js"):
        if (ASSETS_COMUNS / "vendor" / arq).exists():
            shutil.copy(ASSETS_COMUNS / "vendor" / arq, assets / arq)
    for fonte in (ASSETS_COMUNS / "fonts").glob("*.ttf"):
        shutil.copy(fonte, assets / fonte.name)
    esq = narrar(plano["cenas"], voz, assets / "voz.wav")
    (assets / "falas.js").write_text("window.ESQ=" + json.dumps(esq, ensure_ascii=False) + ";", encoding="utf-8")
    (assets / "roteiro.js").write_text("window.ROT=" + json.dumps(plano, ensure_ascii=False) + ";", encoding="utf-8")
    subprocess.run([sys.executable, str(RAIZ / "scripts" / "gerar_lofi.py"), f"{esq['duracao']:.2f}", str(assets / "lofi.wav")],
                   check=True, capture_output=True)
    html = (pasta / "index.html").read_text(encoding="utf-8").replace("__DURACAO__", f"{esq['duracao']:.2f}")
    (pasta / "index.html").write_text(html, encoding="utf-8")
    return esq["duracao"]


def main():
    """Teste manual: monta (sem publicar) um vídeo de uma identidade pra um repositório."""
    import argparse
    from dotenv import load_dotenv
    from . import github_dados, render
    from .roteirista import buscar_readme
    from .voz import ComReserva, EdgeTTS, GeminiTTS
    p = argparse.ArgumentParser()
    p.add_argument("--identidade", choices=identidades(), required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--gancho", required=True)
    p.add_argument("--palavra", required=True)
    p.add_argument("--saida", type=Path, required=True)
    a = p.parse_args()
    load_dotenv(RAIZ / ".env")
    dados = github_dados.buscar(a.repo)
    plano = planejar(a.identidade, dados, buscar_readme(a.repo), a.gancho, a.palavra)
    print(json.dumps(plano, ensure_ascii=False, indent=1))
    pasta = a.saida.with_suffix("")
    montar(a.identidade, plano, ComReserva(GeminiTTS("Orus", RAIZ / "cache_voz"), EdgeTTS()), pasta)
    render.renderizar_reels(pasta, a.saida)


if __name__ == "__main__":
    main()
