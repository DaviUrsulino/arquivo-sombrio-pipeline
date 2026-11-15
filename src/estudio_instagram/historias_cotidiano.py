"""Série "você decide" com tema de cotidiano universal — a frente de alcance do perfil.

Medido em 2026-11-10 (`segredos/estudos/2026-11-10/`, repositório privado): as 4 contas de história animada têm
mediana de 295 mil views (escolhas.app sozinha, 1,2 milhão), contra 2,7 mil das 6 contas de IA/dev do nosso nicho.
A nossa mediana (1.232) está dentro da faixa normal do nicho — o teto é do mercado, não da execução. E a animação
delas é mais simples que a nossa, então o fator é o ASSUNTO.

O motor de série já existia (`series.py`: conta os votos, escreve o próximo episódio, a produtora anima). O que
faltava era de onde nasce o episódio 1: só existia `historias_tech.py`, de casos reais de tecnologia, todos de
nicho. Aqui a situação vem de um banco de cotidiano (ficção, como a série "preso no shopping" que já rodou e foi
o 2º melhor Reels recente do perfil), o LLM escreve o episódio 1 terminando num dilema de duas opções, e daí para
frente o `series.py` cuida sozinho.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from . import series

# Situações de cotidiano que qualquer pessoa entende, sem tecnologia. Cada uma vira uma série nova.
# Ordem = ordem de uso. A marca do perfil continua sendo o visual; o assunto é que abre o alcance.
SITUACOES = [
    # 15/11 (Davi): "as novelinhas deles parecem muito mais interessantes que a nossa". Comparado frase a frase com
    # @nessemundo_br (1,7 mi), @gabriel.cta (990 mil) e @escolhas.app (1,9 mi): eles abrem com a REGRA DO MUNDO ou um
    # PRAZO COM DINHEIRO, e o resto é cena com número, nome, objeto, fala e refrão. As premissas abaixo seguem isso;
    # as antigas (situação genérica de "a chave não gira") ficaram em 1.200 views e saíram.
    ("nesse-mundo-bilhete-do-amor", "Nesse mundo, no aniversário de 29 anos todo mundo recebe um bilhete que diz quantos dias faltam pra pessoa da vida dele aparecer. O Caio recebeu o dele: faltam 11 dias. Comédia romântica: ele passa os 11 dias tratando bem demais todo mundo que encontra, e a pessoa pode ser qualquer uma."),
    ("trinta-dias-pro-aluguel", "A Dani tem 30 dias e R$ 2.400 pra pagar o aluguel, e só ganha dinheiro fazendo favor pros vizinhos do prédio, cada um com um preço e uma exigência esquisita. Série com placar fixo (R$ 0 / 2.400 e dia 1 / 30): cada vizinho é um nível, com uma pequena vitória ou derrota."),
    ("nesse-mundo-mentira-que-funciona", "Nesse mundo, todo mundo nasce com UMA mentira que sempre cola, e só descobre qual é quando usa. A Bia, 16 anos, gastou a dela pra faltar na prova de matemática e agora não pode mentir mais sobre nada de importante, justo na semana em que o pai vai perguntar quem quebrou a janela."),
    ("a-fila-do-cartorio", "O Seu Osvaldo, 71 anos, pega a senha 187 num cartório que está atendendo a senha 12 e jura que não vai embora sem a certidão da esposa. Comédia de espera com 8 horas de fila, o refrão 'senha 187' e cada pessoa da fila com um segredo; a certidão tem uma surpresa no fim."),
    ("nesse-mundo-cada-um-tem-um-relogio", "Nesse mundo, todo mundo tem um relógio no pulso que conta quantas vezes ainda vai ouvir 'eu te amo' na vida. O do Tomás marca 3. A mãe dele tem o dela em 4 mil. Série emocional: ele decide gastar os 3 com cuidado, e o refrão é a mãe dizendo 'depois você me liga'."),
    ("o-primeiro-dia-do-estagiario-fantasma", "A Marta trabalha há 6 meses numa empresa onde todo mundo trata o Heitor, que ela nunca viu, como se ele existisse: cumprimentam a cadeira vazia da mesa 14 e guardam café pra ele. Comédia: ela descobre que nunca perguntou nada porque tinha vergonha, e o crachá dele está no nome dela."),
    ("duzentos-reais-numa-rifa", "O Léo, 12 anos, vendeu 200 rifas de R$ 1 pra pagar a bicicleta do irmão e esqueceu de pôr o prêmio. O sorteio é sábado às 16h na praça. Comédia de enrolação com placar 'rifas vendidas' e um prêmio que ele precisa inventar em 3 dias, e o refrão 'é surpresa'."),
    ("nesse-mundo-o-cachorro-escolhe", "Nesse mundo, todo cachorro escolhe uma pessoa pra proteger no primeiro dia de vida e nunca troca. A Lorena, 34 anos, é escolhida por um vira-lata que a segue de longe há 9 meses sem deixar ela chegar perto. Série emocional: ela descobre quem o cachorro está protegendo dela."),
]
# Estilos que seguram mais tempo de tela nos nossos números (tempo médio assistido de 15 a 20 s).
ESTILOS = ["hand-drawn-cartoon", "cartoon-3d-short", "scifi-toon", "midcentury-toon", "cel-anime-80s"]
INTERVALO = timedelta(hours=20)  # no máximo uma série nova por dia
NOTA_MINIMA = 7.5
PREFIXO = "cotidiano:"


def proxima_situacao(estado: dict) -> tuple[str, str] | None:
    return next(((s, t) for s, t in SITUACOES if f"{PREFIXO}{s}" not in estado), None)


def precisa(estado: dict, agora: datetime | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    feitas = [datetime.fromisoformat(v["quando"]) for k, v in estado.items() if k.startswith(PREFIXO)]
    return not feitas or agora - max(feitas) >= INTERVALO


def problemas(r: dict) -> list[str]:
    """Confere o que o portão de nota não pega: o dilema e o voto na legenda (sem isso ninguém comenta)."""
    erros = []
    opcoes = r.get("opcoes") or []
    if len(opcoes) != 2 or not all(isinstance(o, str) and o.isalpha() and o.isupper() and len(o) <= 8 for o in opcoes):
        return ["'opcoes' precisa de 2 palavras MAIÚSCULAS, só letras sem acento, até 8 letras cada"]
    if opcoes[0] == opcoes[1]:
        erros.append("as duas opções são iguais")
    legenda = r.get("legenda") or ""
    if not all(o in legenda for o in opcoes):
        erros.append(f"a legenda precisa citar as duas opções ({opcoes[0]} e {opcoes[1]}), senão ninguém comenta")
    if not all(o in (r.get("cta") or "") for o in opcoes):
        erros.append("o cta precisa pedir o voto citando as duas opções")
    corpo = r.get("corpo") or []
    if not 12 <= len(corpo) <= 18:
        erros.append("o corpo precisa de 12 a 18 frases")
    elif sum(bool(re.search(r"[\"“”]", str(f))) for f in corpo) < 3:
        erros.append("faltam falas entre aspas: pelo menos 3 frases com diálogo")
    elif sum(bool(re.search(r"\d|\b(dois|duas|três|quatro|cinco|seis|sete|oito|nove|dez|vinte|trinta|cem|mil)\b", str(f), re.I))
             for f in corpo) < 3:
        erros.append("faltam números concretos (dinheiro, dias, idade): pelo menos 3 frases")
    return erros


def escrever(slug: str, situacao: str, n: int, llm=None) -> dict:
    from . import segredos
    from .llm import gerar_json
    gerar = llm or gerar_json
    pedido = {"SITUACAO": situacao}
    r = gerar(segredos.texto("historia_cotidiano"), json.dumps(pedido, ensure_ascii=False))
    for _ in range(2):  # 1) estrutura do dilema; 2) nota do previsor. Reescreve com a crítica, como as outras histórias.
        erros = problemas(r)
        if not erros:
            try:
                texto = (f"TEXTO NA TELA: {r['texto_tela']}\nABERTURA: {r['ganchos'][0]}\n"
                         f"CORPO: {' '.join(r['corpo'])}\nFECHAMENTO: {r['cta']}")
                nota = gerar(segredos.texto("viral_nota"), texto)
            except Exception as erro:
                print(f"previsor do cotidiano falhou ({erro}); sigo com o roteiro")
                break
            print(f"cotidiano {slug}: nota {nota.get('nota')} ({nota.get('problema')})", flush=True)
            if float(nota.get("nota") or 0) >= NOTA_MINIMA:
                break
            erros = [str(nota.get("problema") or "sem gancho forte")]
        pedido.update({"critica_do_editor": "; ".join(erros),
                       "roteiro_rejeitado": {k: r.get(k) for k in ("texto_tela", "ganchos", "corpo", "cta", "opcoes")}})
        r = gerar(segredos.texto("historia_cotidiano"), json.dumps(pedido, ensure_ascii=False))
    if problemas(r):
        raise ValueError("episódio sem dilema válido: " + "; ".join(problemas(r)))
    return {"slug": slug, "serie": slug, "episodio": 1, "opcoes": r["opcoes"], "produzir": True,
            "estilo": ESTILOS[n % len(ESTILOS)],
            "direcao": ("HISTÓRIA DE COTIDIANO, público amplo, sem nada de tecnologia. SITCOM, não trailer: cada frase é um "
                        "ACONTECIMENTO com piada (algo dá errado, alguém reage), nunca descrição de ambiente; tem payoff "
                        "dentro do episódio, não só o cliffhanger. " + (r.get("direcao") or "")),
            "roteiro": {"texto_tela": r["texto_tela"], "ganchos": r["ganchos"][:1], "corpo": r["corpo"],
                        "cta": r["cta"], "legenda": r["legenda"], "palavra": ""}}


def gerar_se_preciso(agora: datetime | None = None):
    """Escreve o episódio 1 de uma série de cotidiano se faz 20 h da última. Caminho do roteiro, ou None."""
    estado = series._ler(series.ESTADO)
    if not precisa(estado, agora):
        return None
    situacao = proxima_situacao(estado)
    if not situacao:
        return None
    slug, texto = situacao
    n = sum(1 for k in estado if k.startswith(PREFIXO))
    try:
        h = escrever(slug, texto, n)
    except Exception as erro:
        print(f"não consegui escrever a história de cotidiano {slug} ({erro})")
        return None
    destino = series.HISTORIAS / f"{slug}.json"
    destino.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
    series.registrar(f"{PREFIXO}{slug}", destino.stem)
    return destino
