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
from datetime import datetime, timedelta, timezone

from . import series

# Situações de cotidiano que qualquer pessoa entende, sem tecnologia. Cada uma vira uma série nova.
# Ordem = ordem de uso. A marca do perfil continua sendo o visual; o assunto é que abre o alcance.
SITUACOES = [
    # 11/11 (comparação frase a frase com o Reels de 1,9 mi do @escolhas.app, segredos/FORMATOS.md seção 10): o
    # deles é SITCOM (peruca, 17ª tentativa, capa presa na porta) e o nosso era trailer de suspense. As situações de
    # comédia entram na frente; o suspense fica para depois.
    ("quatro-dias-para-o-encontro", "Ele tem 4 dias até um encontro com alguém que nunca viu, e a única pessoa que pode treiná-lo é o vizinho esquisito. Comédia: cada tentativa dá errado de um jeito novo."),
    ("sogra-chega-no-domingo", "A sogra chega no domingo e ela prometeu que sabe cozinhar. Tem 3 dias para aprender um prato, com o namorado atrapalhando. Comédia."),
    ("presente-de-dois-mil", "Ele comprou um presente de 2 mil reais no cartão da namorada sem querer, e tem 5 dias para resolver antes da fatura. Comédia de enrolação."),
    ("primeiro-dia-na-cadeira-do-chefe", "No primeiro dia de trabalho ele senta sem saber na cadeira do chefe e todo mundo passa a tratá-lo como chefe. Comédia: até onde ele leva."),
    ("porta-que-nao-abre", "A pessoa volta para casa de madrugada e a chave não gira na fechadura. A luz da sala está acesa, e ela mora sozinha."),
    ("mensagem-do-proprio-numero", "O celular toca às 3 da manhã e quem está ligando é o próprio número dela."),
    ("elevador-que-passou-do-andar", "O elevador do prédio passa direto pelo andar dela e continua subindo, e o prédio só tem 12 andares."),
    ("vizinho-que-devolveu-a-chave", "Um vizinho bate na porta e devolve uma cópia da chave do apartamento dela, dizendo que achou na portaria."),
    ("foto-antiga-no-celular-novo", "Ela compra um celular novo e, na galeria, já existe uma foto da sala da casa dela."),
    ("onibus-que-nao-para", "O último ônibus da noite não para no ponto, e o motorista olha fixo para ela ao passar."),
    ("encomenda-que-ela-nao-pediu", "Chega uma encomenda no nome dela, com o endereço certo, e dentro tem uma coisa que ela perdeu há anos."),
    ("barulho-no-apartamento-de-cima", "O apartamento de cima faz barulho de móvel arrastando toda madrugada, mas está vazio há meses."),
    ("amiga-que-ninguem-lembra", "No aniversário dela, ninguém do grupo lembra da amiga que aparece em todas as fotos da festa do ano passado."),
    ("carro-que-segue-de-longe", "Voltando do trabalho a pé, ela percebe o mesmo carro parado em três esquinas diferentes."),
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
    if not 6 <= len(r.get("corpo") or []) <= 8:
        erros.append("o corpo precisa de 6 a 8 frases")
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
