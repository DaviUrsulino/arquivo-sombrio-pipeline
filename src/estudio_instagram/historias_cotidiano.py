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

from . import estilo_formato
from . import series

# Situações de cotidiano que qualquer pessoa entende, sem tecnologia. Cada uma vira uma série nova.
# Ordem = ordem de uso. A marca do perfil continua sendo o visual; o assunto é que abre o alcance.
SITUACOES = [
    # 15/11, @contosderisco (21,9 mil seg.): 12 de 12 Reels acima de 48 mil, mediana ~470 mil, picos de 4,4 e 4,5 mi, 70 a 80 s.
    # Formato: "E se todo mundo ficasse cego... menos você? Regra número 1: não conte pra ninguém.", episódio numerado
    # ("E SE · Ep. 1"), A ou B nos comentários OU "inventa a C: a melhor entra na próxima parte", fecho "Manda pra única
    # pessoa que você contaria". É premissa hipotética com REGRA, e VOCÊ é o protagonista, não plot de thriller.
    ("e-se-so-voce-fica-acordado", "E se todo mundo na sua cidade dormisse às 21h e só você ficasse acordado? Regra número 1: não acorde ninguém. Você é o protagonista (segunda pessoa). Placar fixo: HORAS ATÉ AMANHECER 9 e PESSOAS QUE ACORDARAM 0. A cada escolha do público uma coisa muda na cidade parada."),
    ("e-se-todo-mundo-esquecesse-seu-nome", "E se, de manhã, todo mundo esquecesse o seu nome, menos uma pessoa? Regra número 1: você tem 24 horas pra descobrir quem. Você é o protagonista. Placar fixo: PESSOAS TESTADAS 0 / 10 e HORAS 24. O público escolhe quem você testa."),
    # 15/11, medição ao vivo (segredos/estudos/2026-11-15/): série de PLOT (sequestro, irmão perdido) decai em 6 episódios
    # (miniverse 1,1 mi -> 7,8 mil; biel 330 mil -> 55 mil), e série de UM PROTAGONISTA COM META E PRAZO, com o público
    # decidindo o próximo passo e um placar fixo, não decai (@escolhas.app 450 mil a 3,2 mi em todo episódio;
    # @ocaradafotoclt 0,7 a 1,7 mi em todo episódio, "30 dias pra virar esse cara"). Por isso as séries abaixo são todas
    # "uma pessoa, uma meta numérica, um prazo". As de mundo ("Nesse mundo...", @nessemundo_br) ficam no fim: funcionam
    # como história solta, não como série.
    ("trinta-dias-pro-aluguel", "A Dani tem 30 dias e R$ 2.400 pra pagar o aluguel, e só ganha dinheiro fazendo favor pros vizinhos do prédio, cada um com um preço e uma exigência esquisita. Placar fixo: R$ 0 / 2.400 e dia 1 / 30. Cada vizinho é um nível, com uma pequena vitória ou derrota."),
    ("quatro-dias-pro-encontro-as-cegas", "O Caio tem 4 dias pra deixar de ser o cara que ninguém quer ter um encontro com, antes de um encontro às cegas marcado pela irmã. Placar fixo: GLOW-UP 20% e dias restantes 4. O público escolhe o que ele tenta a cada dia (cabelo, roupa, papo); cada tentativa dá uma nota de 0 a 10."),
    ("de-zero-a-dez-mil-vendendo-a-casa", "O Rui, 26 anos, tem 30 dias pra juntar R$ 10.000 vendendo as coisas que tem em casa, começando por uma bicicleta quebrada. Placar fixo: R$ 0 / 10.000 e dia 1 / 30. Cada comprador é uma cena com uma pechincha diferente, e o público escolhe o que ele vende primeiro."),
    ("trinta-dias-pra-virar-cozinheiro", "A Lia, 31 anos, nunca cozinhou e tem 30 dias pra fazer o jantar de 12 pessoas do aniversário da avó. Placar fixo: PRATOS QUE DERAM CERTO 0 / 12 e dia 1 / 30. O público escolhe o prato que ela tenta a cada dia, e cada um dá errado de um jeito."),
    ("o-cara-que-pagou-a-rifa-errada", "O Léo, 12 anos, vendeu 200 rifas de R$ 1 pra pagar a bicicleta do irmão e esqueceu de pôr o prêmio. O sorteio é sábado às 16h na praça, em 3 dias. Placar fixo: RIFAS VENDIDAS 200 e horas restantes 72. O público escolhe qual prêmio ele inventa; refrão 'é surpresa'."),
    ("a-fila-do-cartorio", "O Seu Osvaldo, 71 anos, pega a senha 187 num cartório que está atendendo a senha 12 e jura que não vai embora sem a certidão da esposa. Placar fixo: SENHA 12 / 187 e horas na fila. Cada pessoa da fila tem um segredo, e a certidão tem uma surpresa no fim."),
    ("nesse-mundo-bilhete-do-amor", "Nesse mundo, no aniversário de 29 anos todo mundo recebe um bilhete que diz quantos dias faltam pra pessoa da vida dele aparecer. O Caio recebeu o dele: faltam 11 dias. Placar fixo: DIAS 11. Comédia romântica: ele passa os 11 dias tratando bem demais todo mundo que encontra."),
    ("nesse-mundo-cada-um-tem-um-relogio", "Nesse mundo, todo mundo tem um relógio no pulso que conta quantas vezes ainda vai ouvir 'eu te amo' na vida. O do Tomás marca 3. A mãe dele tem o dela em 4 mil. Placar fixo: TOMÁS 3. Série emocional: ele decide gastar os 3 com cuidado, e o refrão é a mãe dizendo 'depois você me liga'."),
]
# Estilos que seguram mais tempo de tela nos nossos números (tempo médio assistido de 15 a 20 s).
ESTILOS = ["hand-drawn-cartoon", "cartoon-3d-short", "scifi-toon", "midcentury-toon", "cel-anime-80s"]
INTERVALO = timedelta(hours=12)  # 15/11: até duas séries novas por dia
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
            "estilo": estilo_formato.menos_usado("historia_personagem") or ESTILOS[n % len(ESTILOS)],
            "direcao": ("HISTÓRIA DE COTIDIANO, público amplo, sem nada de tecnologia. SITCOM, não trailer: cada frase é um "
                        "ACONTECIMENTO com piada (algo dá errado, alguém reage), nunca descrição de ambiente; tem payoff "
                        "dentro do episódio, não só o cliffhanger. " + (r.get("direcao") or "")),
            "placar": str(r.get("placar") or "").strip(),
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
