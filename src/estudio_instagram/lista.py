"""Formato "lista": 5 repositórios do GitHub num Reels curto + carrossel (o padrão que mais viraliza nas contas de referência).

Reels campeões de perfis de IA/dev (80 a 250 mil views) são listas: "5 plugins para turbinar o Claude Code".
Aqui o LLM recebe 5 repositórios reais (dados + início do README) e devolve só: gancho, tema e, para cada um, nome,
como se fala, uma frase com fato do README e um ícone. O código monta a narração, as cenas, os slides e a legenda,
e confere tudo (RN-1: nenhum número que não esteja nos READMEs; ícones e cores que existem).

A pauta devolvida é do formato `pixel2`, então o pipeline monta, publica e o bot de DM funcionam como já funcionam.
"""

import re

from . import cenas_pixel, pauta
from .github_dados import DadosRepo
from .llm import gerar_json
from .roteirista import Recusado, VOZ_PADRAO

QUANTIDADE = 5
ORDINAIS = ["um", "dois", "três", "quatro", "cinco"]
CORES_ITENS = ["azul", "verde", "laranja", "roxo", "amarelo"]
LETRAS_MAX_LINHA = 14

SISTEMA = """Você é roteirista de Reels CURTOS (25 a 35 segundos) do perfil brasileiro @robo.estagiario, sobre ferramentas de IA para quem programa. Formato LISTA: 5 repositórios do GitHub num mesmo vídeo.

Você recebe 5 repositórios com DADOS REAIS e o início do README. REGRAS DE FATO (inegociáveis):
- Use SOMENTE o que está no README ou nos dados. Nada de número, benchmark, comparação, preço ou capacidade que o README não diga.
- Não prometa resultado. Descreva o que a ferramenta faz.
- Se uma ferramenta faz rodízio de contas ou chaves para contornar limite, viola termos de serviço, rouba credenciais, é de ataque, golpe, cripto especulativa ou conteúdo adulto, ou o README não deixa claro o que ela faz, NÃO a inclua: liste em "excluir" e escolha as outras (o objetivo é devolver os itens que sobraram, com no mínimo 3).

ESTILO (é lido em voz alta): português do Brasil, frases completas com verbo, de 6 a 10 palavras, sem emoji, sem hashtag, sem símbolos como / @ #. Escreva siglas e comandos do jeito que se fala.

SAÍDA: um único objeto JSON, sem texto fora dele:
{"tema":"até 6 palavras em minúsculas que completam 'Cinco repositórios grátis para ...' (ex.: criar vídeo com IA)",
 "gancho":["LINHA 1 EM MAIÚSCULAS ATÉ 14 LETRAS","LINHA 2 EM MAIÚSCULAS ATÉ 14 LETRAS"],
 "subtitulo":"frase de uma linha para a legenda, minúscula",
 "itens":[{"repo":"dono/repo","rotulo":"NOME EM MAIÚSCULAS ATÉ 20 LETRAS","falado":"como se fala o nome","frase":"o que faz, de 6 a 10 palavras, só com fatos do README","icone":"um destes: __ICONES__"}],
 "excluir":[]}
Ordene os itens do mais impressionante ao menos. O gancho é a promessa do vídeo (ex.: ["5 REPOS PARA","CRIAR VÍDEO"]), começando por número ou ação concreta."""


def _numeros(texto: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", texto))


def _usuario(dados: list[DadosRepo], readmes: dict[str, str]) -> str:
    blocos = []
    for d in dados:
        blocos.append(
            f"REPOSITÓRIO: {d.repo}\nLICENÇA: {d.licenca}\nDESCRIÇÃO CURTA: {d.descricao}\nREADME (início):\n\"\"\"\n"
            f"{readmes[d.repo][:1800]}\n\"\"\""
        )
    return "\n\n---\n\n".join(blocos) + "\n\nEscreva a lista. Devolva só o JSON."


def problemas(resposta: dict, dados: list[DadosRepo], readmes: dict[str, str], icones: set[str]) -> list[str]:
    erros = []
    repos = {d.repo for d in dados}
    itens = resposta.get("itens")
    if not isinstance(itens, list) or not 3 <= len(itens) <= QUANTIDADE:
        return [f"preciso de 3 a {QUANTIDADE} itens em 'itens', recebi {len(itens) if isinstance(itens, list) else 'nenhum'}"]
    permitidos = set()
    for d in dados:
        permitidos |= _numeros(readmes[d.repo]) | _numeros(d.licenca) | _numeros(d.descricao)
    vistos = set()
    for i, item in enumerate(itens, start=1):
        if not isinstance(item, dict):
            erros.append(f"item {i}: precisa ser um objeto")
            continue
        if item.get("repo") not in repos:
            erros.append(f"item {i}: repo {item.get('repo')!r} não está entre os recebidos")
        if item.get("repo") in vistos:
            erros.append(f"item {i}: repo repetido")
        vistos.add(item.get("repo"))
        rotulo, frase = item.get("rotulo", ""), item.get("frase", "")
        if not rotulo or len(rotulo) > 22 or rotulo != rotulo.upper():
            erros.append(f"item {i}: 'rotulo' em MAIÚSCULAS e até 22 letras")
        if not item.get("falado"):
            erros.append(f"item {i}: falta 'falado'")
        if not 4 <= len(frase.split()) <= 14:
            erros.append(f"item {i}: 'frase' com {len(frase.split())} palavras (quero de 6 a 10)")
        if re.search(r"coment[ae]", frase, re.I):
            erros.append(f"item {i}: não peça para comentar")
        if item.get("icone") not in icones:
            erros.append(f"item {i}: ícone {item.get('icone')!r} não existe")
        for numero in _numeros(frase):
            if numero not in permitidos:
                erros.append(f"item {i}: o número {numero} não aparece nos READMEs")
    gancho = resposta.get("gancho")
    if not isinstance(gancho, list) or len(gancho) != 2 or any(
        not g or len(g) > LETRAS_MAX_LINHA or g != g.upper() for g in gancho
    ):
        erros.append(f"'gancho' precisa de 2 linhas em MAIÚSCULAS, até {LETRAS_MAX_LINHA} letras cada")
    if not resposta.get("tema") or len(resposta["tema"].split()) > 7:
        erros.append("'tema' precisa de até 6 palavras")
    return erros


def montar_pauta(resposta: dict, dados: list[DadosRepo], palavra_chave: str) -> dict:
    por_repo = {d.repo: d for d in dados}
    itens = resposta["itens"]
    n = len(itens)
    numero_por_extenso = {3: "Três", 4: "Quatro", 5: "Cinco"}[n]
    cenas = [{
        "humor": "animado",
        "narracao": f"{numero_por_extenso} repositórios grátis para {resposta['tema'].strip().rstrip('.')}.",
        "visual": {"tipo": "titulo_pixel", "linhas": [
            {"texto": resposta["gancho"][0], "cor": "branco", "tamanho": 100},
            {"texto": resposta["gancho"][1], "cor": "laranja", "tamanho": 110}]},
    }]
    for i, item in enumerate(itens):
        cenas.append({
            "humor": "feliz" if i % 2 == 0 else "animado",
            "narracao": f"Número {ORDINAIS[i]}: {item['falado']}. {item['frase'].strip().rstrip('.')}.",
            "visual": {"tipo": "icone_pixel", "icone": item["icone"], "cor": CORES_ITENS[i % len(CORES_ITENS)],
                       "rotulo": item["rotulo"]},
        })
    slides = [{"tipo": "capa", "linhas": [
        {"texto": resposta["gancho"][0], "cor": "branco", "tamanho": 96},
        {"texto": resposta["gancho"][1], "cor": "laranja", "tamanho": 96}], "subtitulo": resposta.get("subtitulo", "")}]
    for i, item in enumerate(itens):
        slides.append({"tipo": "ponto", "fase": f"Nº {i + 1}", "progresso": round((i + 1) / n, 2),
                       "linhas": [{"texto": item["rotulo"][:18], "cor": CORES_ITENS[i % len(CORES_ITENS)]}],
                       "rotulo": item["repo"].split("/", 1)[1][:24], "texto": item["frase"].strip()})
    slides.append({"tipo": "cta", "linhas": [{"texto": "QUER OS LINKS", "cor": "branco"}, {"texto": "DOS REPOS?", "cor": "verde"}],
                   "subtitulo": "Mando os links no direct.", "palavra": palavra_chave, "extra": "Quer fazer vídeos assim? Link na bio."})
    itens_pauta = [{"repo": it["repo"], "nome": it["repo"].split("/", 1)[1], "cor": CORES_ITENS[i % len(CORES_ITENS)],
                    "promessa": por_repo[it["repo"]].descricao[:80], "texto": it["frase"][:120]} for i, it in enumerate(itens)]
    lista_texto = "\n".join(f"{i}. {it['rotulo'].title()}: {it['frase'].strip().rstrip('.')}." for i, it in enumerate(itens, 1))
    legenda = (f"{numero_por_extenso} repositórios grátis para {resposta['tema'].strip().rstrip('.')} 🤖\n\n"
               f"Salva este vídeo:\n{lista_texto}\n\n"
               f"Manda pra um amigo dev, segue o @robo.estagiario e comenta {palavra_chave} que eu te mando os links no direct.\n\n"
               "Quer aprender a fazer vídeos assim? Link na bio.\n\n#claudecode #github #ia #programacao #opensource")
    return {
        "titulo": f"lista: {resposta['tema'].strip()}", "formato": "pixel2", "palavra_chave": palavra_chave,
        "perfil": "@robo.estagiario", "voz": VOZ_PADRAO,
        "capa": {"subtitulo": resposta.get("subtitulo") or resposta["tema"]},
        "chamada": {"pergunta": "quer os links dos repositórios?"},
        "itens": itens_pauta, "destaques": [it["falado"].lower() for it in itens][:8] + [palavra_chave.lower()],
        "cenas_roteiro": cenas, "slides": slides, "legenda": legenda[:2200],
    }


def gerar_pauta(dados: list[DadosRepo], readmes: dict[str, str], palavra_chave: str, icones: set[str],
                llm=gerar_json, tentativas: int = 3) -> dict:
    """Pauta pixel2 pronta e validada para a lista, ou ValueError com os problemas da última tentativa."""
    sistema = SISTEMA.replace("__ICONES__", ", ".join(sorted(icones)))
    usuario = _usuario(dados, readmes)
    erros: list[str] = []
    for _ in range(tentativas):
        pedido = usuario if not erros else usuario + "\n\nSUA RESPOSTA ANTERIOR TEVE ESTES PROBLEMAS, corrija todos:\n- " + "\n- ".join(erros)
        resposta = llm(sistema, pedido)
        if resposta.get("recusar"):
            raise Recusado(f"lista recusada: {resposta.get('motivo', 'sem motivo')}")
        erros = problemas(resposta, dados, readmes, icones)
        if erros:
            continue
        vivos = [d for d in dados if d.repo in {i["repo"] for i in resposta["itens"]}]
        nova = montar_pauta(resposta, vivos, palavra_chave)
        try:
            final = cenas_pixel.normalizar_pauta(nova)
        except (ValueError, KeyError) as erro:
            erros = [f"estrutura inválida: {erro}"]
            continue
        erros = pauta.problemas(final, icones)
        if not erros:
            return nova
    raise ValueError("lista não passou na validação: " + "; ".join(erros[:6]))
