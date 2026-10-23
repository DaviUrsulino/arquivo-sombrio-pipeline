"""Escreve o roteiro de um Reels (molde pixel2) a partir do README de um repositório do GitHub.

O LLM recebe os dados reais do repositório e o README, e devolve uma lista de frases, cada uma
com o visual que aparece na tela. Tudo que ele devolve é conferido antes de gastar crédito de voz:

- só visuais do vocabulário, com ícones e cores que existem;
- todo número falado precisa existir no README (RN-1: nada de fato inventado);
- se a resposta não passar, o erro volta para o modelo e ele tenta de novo (até `tentativas`).

Se o LLM falhar de vez, quem chamou cai no formato antigo, de modelo de frase (selecao.py).
"""

import json
import re
import urllib.request

from . import cenas_pixel, github_dados, pauta
from .github_dados import DadosRepo
from .llm import gerar_json

VOZ_PADRAO = {"id": "iP95p4xoKVk53GoZ742B", "modelo": "eleven_multilingual_v2"}
MAX_README = 9000
CORES_VALIDAS = pauta.CORES
HUMORES = cenas_pixel.HUMORES

class Recusado(ValueError):
    """O modelo achou que a ferramenta não deve virar post (ver REGRAS DE RECUSA no prompt)."""


SISTEMA = """Você é roteirista de Reels CURTOS de 20 a 30 segundos (a maioria das pessoas sai nos primeiros segundos, então cada frase precisa valer) de um perfil brasileiro de Instagram sobre ferramentas de IA para quem programa (@robo.estagiario). Tom: informativo, direto e curioso, como quem conta uma descoberta útil para um amigo.

Você recebe DADOS REAIS de um repositório do GitHub e o README dele. REGRAS DE FATO (inegociáveis):
- Use SOMENTE o que está no README ou nos dados. Nada de número, benchmark, comparação, preço ou capacidade que não esteja lá. Se o README não diz, não diga.
- Comando de instalação ou de uso: copie exatamente do README, nunca invente.
- Não prometa resultado ("vai dobrar sua produtividade"). Descreva o que a ferramenta faz.
- Número de estrelas: escreva o marcador {estrelas:DONO/REPO} (será trocado pelo valor real). Não escreva outro número em dígitos, exceto os que estão no README. Números pequenos, por extenso ("vinte e uma").

ESTILO DA NARRAÇÃO (é lida em voz alta):
- Português do Brasil, frases de 8 a 11 palavras (cada uma dura de 4 a 5 segundos), sempre completas e com verbo (nada de estilo telegráfico, de manchete nem de lista de substantivos), uma ideia por frase, sem "galera", sem emoji, sem hashtag.
- Escreva siglas e comandos do jeito que se fala ("barra plan", "ponto md"), sem símbolos como / @ # *.
- Nunca peça para comentar nem cite palavra-chave: o fecho é adicionado depois.

REGRAS DE RECUSA: se a ferramenta (a) faz rodízio ou compartilhamento de contas, assinaturas ou chaves para contornar limite de uso ou cota de provedores, (b) burla ou viola termos de serviço de algum provedor, (c) rouba, extrai ou expõe credenciais, (d) é de ataque ou invasão, golpe, cripto especulativa ou conteúdo adulto, ou (e) o README não deixa claro o que ela faz, NÃO escreva roteiro. Responda só {"recusar": true, "motivo": "uma frase"}.

ESTRUTURA: 5 cenas (o vídeo inteiro, com o fecho de 6 s que é adicionado depois, deve ficar perto de 30 segundos). Cada cena precisa de tempo para o olho ler o visual: nada de cena que dure menos de 4 segundos. Cada cena = UMA frase falada + UM visual diferente do anterior.
1. Gancho (visual titulo_pixel): a promessa mais específica e surpreendente que o README sustenta, dita nas primeiras palavras. Precisa fazer quem tá passando o dedo na tela parar nos primeiros 2 segundos — isso é mais importante que descrever a ferramenta direito. Prefira SEMPRE tensão/aposta sobre descrição plana: o que dá errado sem isso, o que a maioria faz errado, ou um número específico que choca, em vez de só dizer o que a ferramenta faz (ex.: nunca "Seu agente faz auditoria em seis fases" — isso é descrição, não gancho; prefira algo como "Seu agente de código tem acesso total e ninguém confere" ou "Isso aqui já achou falha que humano não via"). Até 10 palavras e o texto do titulo_pixel da cena 1 só usa palavras que a própria narração diz (a tela repete o que a voz fala, sem acrescentar informação), comece pelo que a pessoa ganha ou pela ação concreta (de preferência com um número do README ou "sem" + algo que ela odeia fazer). Nunca comece com "Conheça", "Olha só" nem com o nome do projeto; o nome vem depois. Nada de exagero que o README não sustente.
2. Estrelas (visual contador, narração com o marcador {estrelas:DONO/REPO} no meio da frase, nunca como primeira palavra; ex.: "O projeto já tem {estrelas:DONO/REPO} estrelas no GitHub.").
3 a 5. O que é, o que dá para fazer e como instalar ou usar (com dados do README). Só o essencial: uma ideia forte por cena.

VISUAIS (campo "visual" da cena; só estes "tipo", cores: laranja azul verde roxo vermelho amarelo branco rosa):
- titulo_pixel: {"tipo":"titulo_pixel","linhas":[{"texto":"A IA CRIA","cor":"branco","tamanho":120},{"texto":"VÍDEO","cor":"laranja","tamanho":150}]}  (2 a 3 linhas, MAIÚSCULAS, até 14 letras por linha, tamanhos 100 a 170)
- icone_pixel: {"tipo":"icone_pixel","icone":"check","cor":"verde","rotulo":"SAI IGUAL TODA VEZ"}  (rotulo até 22 letras, MAIÚSCULAS)
- cadeia: {"tipo":"cadeia","layout":"horizontal","nos":[{"icone":"code-xml","rotulo":"HTML","cor":"azul"},{"icone":"zap","rotulo":"Ferramenta","cor":"amarelo"},{"icone":"clapperboard","rotulo":"Vídeo","cor":"verde"}]}  (2 ou 3 nós; layout "horizontal" ou "vertical"; rotulo até 14 letras; mostra um fluxo A -> B -> C)
- comparar: {"tipo":"comparar","esq":{"titulo":"RÁPIDO","icone":"zap","cor":"amarelo","linhas":[{"rotulo":"velocidade","valor":8}]},"dir":{"titulo":"AVANÇADO","icone":"brain","cor":"roxo","linhas":[{"rotulo":"controle","valor":8}]}}  (valor de 0 a 8; só use se o README realmente descreve dois modos ou duas opções)
- niveis: {"tipo":"niveis","itens":[{"rotulo":"BÁSICO","altura":1,"cor":"verde"},{"rotulo":"MÉDIO","altura":2,"cor":"azul"},{"rotulo":"AVANÇADO","altura":3,"cor":"amarelo"}]}  (2 ou 3 colunas; altura 1 a 3)
- lista: {"tipo":"lista","itens":["Claude Code","Codex","Cursor"]}  (2 a 4 itens de até 22 letras)
- terminal: {"tipo":"terminal","rotulo":"terminal","comando":"npx exemplo init","texto":"o que esse comando faz"}  (comando COPIADO do README; texto opcional)
- contador: {"tipo":"contador","repo":"DONO/REPO"}  (estrelas do GitHub contando; use na cena 2)
- banner_repo: {"tipo":"banner_repo","url":"github.com/dono/repo"}  (mostra o endereço do repositório; use no máximo uma vez)
- sala_pixel: {"tipo":"sala_pixel","personagens":3,"rotulo":"3 AGENTES AO VIVO","cor":"azul"}  (2 a 4 bichinhos pixel numa mesa, cada um trabalhando; use SÓ quando o README descreve vários agentes, bots, workers ou processos rodando ao mesmo tempo/em paralelo — não use pra ferramenta de um processo só)
Ícones disponíveis: __ICONES__.

"humor" da cena (reação do robô): normal, feliz, animado ou pensando.

SAÍDA: um único objeto JSON, sem texto fora dele:
{"subtitulo":"frase de uma linha para a legenda do post, minúscula",
 "passos":["de 3 a 4 passos curtos e numeráveis para usar ou instalar a ferramenta, só com o que o README diz (comando copiado do README); vão na legenda para a pessoa salvar o post. Se o README não tem como usar, devolva lista vazia"],
 "destaques":["até 8 palavras da narração que valem destaque na legenda, minúsculas, sem acento se possível"],
 "cenas":[{"narracao":"...","humor":"feliz","visual":{...}}],
 "slides":[
   {"tipo":"capa","linhas":[{"texto":"A IA CRIA","cor":"branco","tamanho":108},{"texto":"VÍDEO COM HTML","cor":"laranja","tamanho":80}],"subtitulo":"conheça o NOME"},
   {"tipo":"ponto","fase":"O QUE É","progresso":0.25,"linhas":[{"texto":"TÍTULO CURTO","cor":"azul"}],"rotulo":"nome","texto":"2 frases do que é, só com fatos do README."},
   {"tipo":"comando","fase":"INSTALAR","progresso":0.5,"linhas":[{"texto":"COMO USAR","cor":"verde"}],"comando":"comando do README","texto":"nota curta","rotulo":"terminal"},
   {"tipo":"ponto","fase":"EXEMPLO","progresso":0.75,"linhas":[{"texto":"O QUE DÁ","cor":"laranja"}],"rotulo":"nota","texto":"o que dá para fazer, com fatos do README."},
   {"tipo":"ponto","fase":"BÔNUS","progresso":1.0,"linhas":[{"texto":"LICENÇA","cor":"amarelo"}],"rotulo":"nota","texto":"licença e requisito do README."}
 ]}
Os slides do carrossel (5, exatamente nessa ordem de tipos) repetem o essencial do vídeo. Linhas de título dos slides: MAIÚSCULAS, até 18 letras."""


def buscar_readme(repo: str, abrir=urllib.request.urlopen) -> str:
    pedido = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/readme",
        headers={**github_dados._cabecalhos(), "Accept": "application/vnd.github.raw+json"},
    )
    with abrir(pedido, timeout=30) as resposta:
        texto = resposta.read().decode("utf-8", errors="replace")
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    texto = re.sub(r"<img[^>]*>|<picture>.*?</picture>|!\[[^\]]*\]\([^)]*\)", "", texto, flags=re.S)  # imagens e badges não ajudam
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
    return texto[:MAX_README]


def _usuario(dados: DadosRepo, readme: str) -> str:
    return (
        f"REPOSITÓRIO: {dados.repo}\nURL: {dados.url}\nESTRELAS (use o marcador, não o número): {dados.estrelas}\n"
        f"LICENÇA: {dados.licenca}\nDESCRIÇÃO CURTA: {dados.descricao}\n\nREADME:\n\"\"\"\n{readme}\n\"\"\"\n\n"
        f"Escreva o roteiro. O marcador de estrelas desta ferramenta é {{estrelas:{dados.repo}}} e o repo do contador é \"{dados.repo}\"."
    )


def _numeros(texto: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", texto))


def _problemas_roteiro(resposta: dict, dados: DadosRepo, readme: str, icones: set[str]) -> list[str]:
    erros = []
    cenas = resposta.get("cenas")
    if not isinstance(cenas, list) or not 4 <= len(cenas) <= 10:
        return [f"preciso de 5 a 6 cenas em 'cenas', recebi {len(cenas) if isinstance(cenas, list) else 'nenhuma'}"]
    permitidos = _numeros(readme) | _numeros(dados.licenca) | _numeros(dados.descricao)
    for i, cena in enumerate(cenas, start=1):
        if not isinstance(cena, dict) or not cena.get("narracao") or not isinstance(cena.get("visual"), dict):
            erros.append(f"cena {i}: precisa de 'narracao' e 'visual'")
            continue
        tipo = cena["visual"].get("tipo")
        if tipo not in cenas_pixel.TIPOS_VISUAIS - {"selo_pixel"}:
            erros.append(f"cena {i}: visual desconhecido {tipo!r}")
        if i == 1 and tipo != "titulo_pixel":
            erros.append("a cena 1 tem que ser titulo_pixel")
        if i == 1 and tipo == "titulo_pixel":
            falado = {cenas_pixel.normalizar(w) for w in cena["narracao"].split()}
            na_tela = [cenas_pixel.normalizar(w) for l in cena["visual"].get("linhas", []) for w in str(l.get("texto", "")).split()]
            fora = [w for w in na_tela if w and w not in falado and len(w) > 2]
            if len(fora) > 1:
                erros.append(f"cena 1: o título da tela tem palavras que a voz não diz ({', '.join(fora[:3])}); a tela repete a narração")
        if i > 1 and tipo == cenas[i - 2].get("visual", {}).get("tipo") and tipo not in ("terminal", "icone_pixel"):
            erros.append(f"cena {i}: repete o visual da cena anterior ({tipo}); varie")
        sem_marcador = re.sub(r"\{estrelas:[^}]*\}", "", cena["narracao"])
        for numero in _numeros(sem_marcador):
            if numero not in permitidos:
                erros.append(f"cena {i}: o número {numero} não aparece no README. Tire ou use só números do README")
        palavras = len(cena["narracao"].split())
        if not 5 <= palavras <= 22:
            erros.append(f"cena {i}: narração com {palavras} palavras (quero de 8 a 14)")
        if re.search(r"coment[ae]", cena["narracao"], re.I):
            erros.append(f"cena {i}: não peça para comentar; o fecho é adicionado depois")
        v = cena["visual"]
        for no in v.get("nos", []):
            if no.get("icone") not in icones:
                erros.append(f"cena {i}: ícone {no.get('icone')!r} não existe")
        if v.get("icone") and v["icone"] not in icones:
            erros.append(f"cena {i}: ícone {v['icone']!r} não existe")
        if tipo == "contador" and v.get("repo") != dados.repo:
            erros.append(f"cena {i}: contador.repo tem que ser {dados.repo}")
    if cenas and "{estrelas:" not in " ".join(c.get("narracao", "") for c in cenas):
        erros.append("falta o marcador {estrelas:...} em alguma narração")
    passos = resposta.get("passos", [])
    if not isinstance(passos, list) or len(passos) > 4 or any(not isinstance(p, str) or len(p) > 120 for p in passos):
        erros.append("'passos' precisa ser uma lista de até 4 textos de até 120 letras")
    else:
        for passo in passos:
            for numero in _numeros(passo):
                if numero not in permitidos:
                    erros.append(f"passo '{passo[:30]}': o número {numero} não aparece no README")
    slides = resposta.get("slides")
    if not isinstance(slides, list) or len(slides) != 5 or [s.get("tipo") for s in slides][:1] != ["capa"]:
        erros.append("'slides' precisa de exatamente 5 itens, o primeiro do tipo capa")
    return erros


def montar_pauta(resposta: dict, dados: DadosRepo, palavra_chave: str) -> dict:
    nome = dados.repo.split("/", 1)[1]
    slides = list(resposta["slides"]) + [{
        "tipo": "cta", "linhas": [{"texto": "QUER O LINK", "cor": "branco"}, {"texto": "DO REPO?", "cor": "verde"}],
        "subtitulo": "Mando o link do repositório no direct.", "palavra": palavra_chave,
        "extra": "Quer fazer vídeos assim? Link na bio.",
    }]
    return {
        "titulo": f"{nome}: roteiro automático", "formato": "pixel2", "palavra_chave": palavra_chave,
        "perfil": "@robo.estagiario", "voz": VOZ_PADRAO,
        "capa": {"subtitulo": resposta.get("subtitulo") or dados.descricao[:120].lower()},
        "chamada": {"pergunta": "quer o link do repositório?"},
        "itens": [{"repo": dados.repo, "nome": nome, "cor": "azul", "promessa": dados.descricao[:80], "texto": dados.descricao[:120]}],
        "destaques": [d.lower() for d in resposta.get("destaques", [])][:10] + [palavra_chave.lower()],
        "cenas_roteiro": [
            {"narracao": c["narracao"], "humor": c.get("humor", "normal"), "visual": c["visual"]} for c in resposta["cenas"]
        ],
        "slides": slides,
        "passos": [p.strip() for p in resposta.get("passos", []) if p.strip()],
    }


def gerar_pauta(dados: DadosRepo, readme: str, palavra_chave: str, icones: set[str],
                llm=gerar_json, tentativas: int = 3) -> dict:
    """Devolve a pauta pixel2 pronta e validada, ou levanta ValueError com os problemas da última tentativa."""
    sistema = SISTEMA.replace("__ICONES__", ", ".join(sorted(icones)))
    usuario = _usuario(dados, readme)
    erros: list[str] = []
    for _ in range(tentativas):
        pedido = usuario if not erros else usuario + "\n\nSUA RESPOSTA ANTERIOR TEVE ESTES PROBLEMAS, corrija todos:\n- " + "\n- ".join(erros)
        resposta = llm(sistema, pedido)
        if resposta.get("recusar"):
            raise Recusado(f"{dados.repo} recusado: {resposta.get('motivo', 'sem motivo')}")
        erros = _problemas_roteiro(resposta, dados, readme, icones)
        if not erros:
            nova = montar_pauta(resposta, dados, palavra_chave)
            try:
                final = cenas_pixel.normalizar_pauta(nova)
            except (ValueError, KeyError) as erro:
                erros = [f"estrutura inválida: {erro}"]
                continue
            erros = pauta.problemas(final, icones)
            if not erros:
                return nova
    raise ValueError("roteiro não passou na validação: " + "; ".join(erros[:6]))
