"""Catálogo único do que o motor do palco sabe desenhar. O diretor (LLM) só pode escolher daqui, e o motor JS
lê o mesmo catálogo (gravado em assets/catalogo.js), então os dois lados nunca divergem.

Cada objeto tem uma descrição curta para o LLM saber quando usar e se aceita texto ou número.
"""

import json
from pathlib import Path

MUNDOS = {
    "palco": "palco de teatro com cortina roxa, varal de luzes e piso de madeira; mundo padrão, serve pra tudo",
    "oficina": "oficina com parede de ferramentas e bancada; serve pra construir, consertar, desmontar, engenharia reversa",
    "noir": "filme noir preto e branco, persiana, abajur; serve pra mistério, segredo, investigação, golpe, canal dark",
    "apartamento": "sala de apartamento com sofá, TV e tapete; serve pra vida em casa, TV, celular, rotina, família",
    "espaco": "espaço com estrelas e planeta; serve pra futuro, lançamento, coisa gigante, previsão",
    "laboratorio": "laboratório branco e verde-água com frascos; serve pra teste, experimento, ciência, comparação",
    "escritorio": "escritório com mesa, monitor e janela da cidade; serve pra trabalho, empresa, produtividade, dinheiro",
    "cidade": "praça de cidade low-poly com prédios; serve pra muita gente, mercado, todo mundo usando",
    "auditorio": "programa de auditório com pódio e telão de LED; serve pra ranking, top 5, competição, prêmio",
    "cor": "fundo de cor chapada (use fundo_cor); serve pra frase abstrata, número grande, virada de ritmo",
}

ACOES = {
    "apresenta": "abre os braços apresentando o objeto",
    "aponta": "aponta para o objeto",
    "segura": "segura o objeto na mão e mostra",
    "martela": "bate no objeto com um martelo",
    "corta": "corta o objeto com uma tesoura",
    "digita": "digita no objeto (notebook, celular)",
    "pensa": "mão no queixo, pensando",
    "comemora": "pula com os braços pra cima, confete",
    "assusta": "pula pra trás assustado",
    "pula": "pula de alegria",
    "empurra": "empurra o objeto pra dentro da cena",
    "observa": "se inclina para olhar o objeto de perto (com lupa se houver)",
    "acena": "acena para a câmera",
    "corre": "corre atravessando a cena",
    "carimba": "bate um carimbo no objeto",
}

OBJETOS = {
    "celular": ("celular grande com uma tela", "texto"),
    "notebook": ("notebook aberto com uma tela", "texto"),
    "monitor": ("monitor grande / telão", "texto"),
    "contador": ("contador mecânico de dígitos que gira até o número", "numero"),
    "grafico": ("gráfico de barras que cresce", "numero"),
    "maquina": ("máquina com funil e engrenagens que cospe um resultado (processo, automação)", "texto"),
    "martelo": ("martelo", None),
    "tesoura": ("tesoura cortando uma fita de filme", None),
    "lupa": ("lupa gigante", None),
    "carimbo": ("carimbo que marca uma palavra (APROVADO, REPROVADO, GRÁTIS)", "texto"),
    "caixa": ("caixa de papelão com etiqueta", "texto"),
    "cadeado": ("cadeado que abre (liberado, destravado)", None),
    "moedas": ("pilha de moedas e notas (dinheiro, preço, economia)", "numero"),
    "foguete": ("foguete decolando (crescimento, lançamento)", None),
    "trofeu": ("troféu dourado (vencedor, primeiro lugar)", None),
    "relogio": ("relógio com ponteiros girando rápido (tempo, horas, minutos)", None),
    "calendario": ("calendário com um número (dias)", "numero"),
    "livros": ("pilha de livros (curso, tutorial, conhecimento)", "texto"),
    "jornal": ("jornal com manchete (notícia)", "texto"),
    "balao": ("balão de fala de quadrinho com frase curta", "texto"),
    "placa": ("placa de madeira com texto", "texto"),
    "estrela": ("estrela grande do GitHub com número", "numero"),
    "lampada": ("lâmpada acendendo (ideia)", None),
    "presente": ("caixa de presente que abre (grátis, bônus)", None),
    "escudo": ("escudo (segurança, proteção)", None),
    "chave": ("chave dourada (solução, acesso)", None),
    "equipe": ("vários robozinhos coloridos (equipe, agentes, muita gente)", "numero"),
    "claquete": ("claquete de cinema (vídeo, filmagem)", "texto"),
    "lixeira": ("lixeira (jogar fora, descartar)", None),
    "ampulheta": ("ampulheta (espera, demora)", None),
    "nuvem": ("nuvem (internet, servidor)", None),
    "raio": ("raio amarelo (rápido, energia)", None),
}

CAMERAS = ["frente", "aproxima", "afasta", "lateral", "cima", "baixo", "orbita", "close_objeto"]
EMOCOES = ["feliz", "surpreso", "pensando", "bravo", "apaixonado", "triste", "determinado", "rindo", "neutro"]
CHAPEUS = ["nenhum", "detetive", "diretor", "capacete", "coroa", "fone", "mago", "cozinheiro"]
TRANSICOES = ["corte", "chicote", "voxel"]
CORES_FUNDO = ["roxo", "azul", "amarelo", "verde", "rosa", "laranja", "preto", "branco"]


def para_js() -> str:
    dados = {"mundos": list(MUNDOS), "acoes": list(ACOES), "objetos": {k: v[1] for k, v in OBJETOS.items()},
             "cameras": CAMERAS, "emocoes": EMOCOES, "chapeus": CHAPEUS, "transicoes": TRANSICOES, "cores": CORES_FUNDO}
    return "window.CATALOGO=" + json.dumps(dados, ensure_ascii=False) + ";"


def para_llm() -> str:
    linhas = ["MUNDOS (o mundo do vídeo; pode trocar de mundo no meio, no máximo 2 vezes):"]
    linhas += [f"- {k}: {v}" for k, v in MUNDOS.items()]
    linhas += ["", "AÇÕES DO ROBÔ (uma por cena; nunca repita a mesma em cenas seguidas):"]
    linhas += [f"- {k}: {v}" for k, v in ACOES.items()]
    linhas += ["", "OBJETOS (um por cena; [texto] aceita texto_objeto até 18 letras, [numero] aceita numero):"]
    linhas += [f"- {k}: {d}" + (f" [{t}]" if t else "") for k, (d, t) in OBJETOS.items()]
    linhas += ["", f"CÂMERAS: {', '.join(CAMERAS)}", f"EMOÇÕES DO ROBÔ: {', '.join(EMOCOES)}",
               f"CHAPÉUS: {', '.join(CHAPEUS)}", f"TRANSIÇÕES: {', '.join(TRANSICOES)}", f"CORES DE FUNDO (mundo cor): {', '.join(CORES_FUNDO)}"]
    return "\n".join(linhas)


def gravar_js(destino: Path):
    Path(destino).write_text(para_js(), encoding="utf-8")
