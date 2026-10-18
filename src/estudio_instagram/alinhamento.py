"""Descobre em que segundo cada palavra é falada, olhando só o áudio (para vozes que não informam o tempo).

O Gemini TTS devolve o áudio, mas não o tempo por palavra. A legenda e os visuais precisam dele. Sem
modelo de reconhecimento de fala, a conta é esta:

1. Mede a energia do áudio a cada 10 ms e acha onde a voz começa e termina.
2. Acha as pausas dentro da fala (silêncio de 90 ms ou mais).
3. Quebra o texto em frases pelas vírgulas e pontos, e encaixa cada quebra na pausa mais próxima.
4. Dentro de cada trecho, reparte o tempo entre as palavras pelo tamanho delas.

Não é perfeito (erra uns décimos de segundo dentro de um trecho), mas a legenda e o visual disparam
numa frase de 3 a 5 segundos, onde esse erro não aparece.
"""

from array import array
from dataclasses import dataclass

from .sincronia import PalavraNoTempo

TAXA = 24000
QUADRO = TAXA // 100  # 10 ms
PAUSA_MIN_QUADROS = 9
QUEBRAS = (",", ";", ":", ".", "!", "?")


@dataclass(frozen=True)
class Analise:
    inicio: int  # índice do quadro
    fim: int
    pausas: list[tuple[int, int]]  # (primeiro quadro, último quadro) de cada silêncio interno


def _energias(pcm: bytes) -> list[float]:
    amostras = array("h")
    amostras.frombytes(pcm[: len(pcm) // 2 * 2])
    return [
        sum(abs(a) for a in amostras[i:i + QUADRO]) / QUADRO
        for i in range(0, len(amostras) - QUADRO + 1, QUADRO)
    ]


def analisar(pcm: bytes) -> Analise:
    energias = _energias(pcm)
    if not energias:
        raise ValueError("áudio vazio")
    ordenadas = sorted(energias)
    referencia = ordenadas[int(len(ordenadas) * 0.95)]
    limiar = max(60.0, referencia * 0.07)
    fala = [e > limiar for e in energias]
    if not any(fala):
        raise ValueError("áudio sem fala")
    inicio = fala.index(True)
    fim = len(fala) - 1 - fala[::-1].index(True)
    pausas, i = [], inicio
    while i <= fim:
        if not fala[i]:
            j = i
            while j <= fim and not fala[j]:
                j += 1
            if j - i >= PAUSA_MIN_QUADROS:
                pausas.append((i, j - 1))
            i = j
        else:
            i += 1
    return Analise(inicio, fim, pausas)


def aparar(pcm: bytes, antes_ms: int = 60, depois_ms: int = 90) -> tuple[bytes, float]:
    """Corta o silêncio do começo e do fim. Devolve (pcm cortado, quantos segundos foram tirados do começo)."""
    a = analisar(pcm)
    primeiro = max(0, a.inicio * QUADRO - TAXA * antes_ms // 1000)
    ultimo = min(len(pcm) // 2, (a.fim + 1) * QUADRO + TAXA * depois_ms // 1000)
    return pcm[primeiro * 2: ultimo * 2], primeiro / TAXA


def _peso(palavra: str) -> float:
    letras = sum(c.isalnum() for c in palavra)
    return letras + 1.5  # cada palavra leva um tempo mínimo, mesmo as curtas


def _casar_pausas(quebras: list[tuple[int, float]], a: Analise, fala_total: int) -> dict[int, tuple[int, int]]:
    """Casa cada quebra de frase (vírgula, ponto) com uma pausa real do áudio, sem cruzar a ordem.

    Pausa longa é muito mais provável de ser vírgula do que pausa curta (a fala tem silêncios curtos
    entre palavras). Programação dinâmica: custo = distância da posição esperada, com bônus por pausa
    longa; pular uma quebra (sem pausa para ela) também custa.
    """
    candidatas = [p for p in a.pausas if p[1] - p[0] + 1 >= PAUSA_MIN_QUADROS]
    n, m = len(quebras), len(candidatas)
    if not n or not m:
        return {}
    PULAR = 1.2
    INF = float("inf")

    def custo(i: int, j: int) -> float:
        esperado = a.inicio + quebras[i][1] * fala_total
        centro = (candidatas[j][0] + candidatas[j][1]) / 2
        comprimento = min(candidatas[j][1] - candidatas[j][0] + 1, 40) / 40
        return abs(centro - esperado) / fala_total * 12 - comprimento * 1.0

    # melhor[i][j]: custo mínimo tendo tratado as quebras 0..i-1 e usado pausas só antes da j-ésima
    melhor = [[INF] * (m + 1) for _ in range(n + 1)]
    volta = [[None] * (m + 1) for _ in range(n + 1)]
    for j in range(m + 1):
        melhor[0][j] = 0.0
    for i in range(1, n + 1):
        for j in range(m + 1):
            if melhor[i - 1][j] + PULAR < melhor[i][j]:
                melhor[i][j], volta[i][j] = melhor[i - 1][j] + PULAR, ("pula", j)
            if j > 0:
                c = melhor[i - 1][j - 1] + custo(i - 1, j - 1)
                if c < melhor[i][j]:
                    melhor[i][j], volta[i][j] = c, ("usa", j - 1)
                if melhor[i][j - 1] < melhor[i][j]:
                    melhor[i][j], volta[i][j] = melhor[i][j - 1], ("anda", j - 1)
    usadas, i, j = {}, n, m
    while i > 0:
        passo = volta[i][j]
        if passo is None:
            break
        if passo[0] == "usa":
            usadas[quebras[i - 1][0]] = candidatas[passo[1]]
            i, j = i - 1, passo[1]
        elif passo[0] == "pula":
            i -= 1
        else:
            j = passo[1]
    return usadas


def alinhar(texto: str, pcm: bytes) -> list[PalavraNoTempo]:
    """Tempo (em segundos, contado do início do `pcm`) em que cada palavra de `texto` começa."""
    palavras = texto.split()
    if not palavras:
        return []
    a = analisar(pcm)
    pesos = [_peso(p) for p in palavras]
    total = sum(pesos)

    # Quebras de frase: depois de qual palavra (índice) e onde ela cai na linha do tempo (0 a 1).
    quebras, acumulado = [], 0.0
    for indice, (palavra, peso) in enumerate(zip(palavras, pesos)):
        acumulado += peso
        if palavra.endswith(QUEBRAS) and indice < len(palavras) - 1:
            quebras.append((indice, acumulado / total))

    fala_total = a.fim + 1 - a.inicio
    usadas = _casar_pausas(quebras, a, fala_total)

    # Trechos de fala entre as pausas escolhidas.
    cortes = sorted(usadas.items())
    trechos, inicio_trecho, primeira = [], a.inicio, 0
    for indice, (p_ini, p_fim) in cortes:
        trechos.append((primeira, indice + 1, inicio_trecho, p_ini))
        primeira, inicio_trecho = indice + 1, p_fim + 1
    trechos.append((primeira, len(palavras), inicio_trecho, a.fim + 1))

    saida = []
    for p_ini, p_fim, q_ini, q_fim in trechos:
        soma = sum(pesos[p_ini:p_fim]) or 1.0
        corrido = 0.0
        for k in range(p_ini, p_fim):
            quadro = q_ini + (q_fim - q_ini) * corrido / soma
            saida.append(PalavraNoTempo(round(quadro * QUADRO / TAXA, 3), palavras[k]))
            corrido += pesos[k]
    return saida


def cortar_em_cenas(textos: list[str], pcm: bytes) -> list[tuple[bytes, list[PalavraNoTempo]]]:
    """Divide uma narração única em uma fatia de áudio por cena, cortando no meio da pausa entre frases.

    `textos` são as falas de cada cena, na ordem em que foram faladas juntas. Devolve, para cada cena,
    (áudio da cena, palavras com tempo contado do começo da fatia).
    """
    completo = " ".join(textos)
    palavras = alinhar(completo, pcm)
    contagens = [len(t.split()) for t in textos]
    a = analisar(pcm)
    total_s = len(pcm) / 2 / TAXA
    # início estimado de cada cena (tempo da primeira palavra dela)
    inicios, i = [], 0
    for n in contagens:
        inicios.append(palavras[i].t)
        i += n
    cortes = [0.0]
    for estimado in inicios[1:]:
        candidatas = [(abs((p0 + p1) / 2 * QUADRO / TAXA - estimado), (p0 + p1 + 1) / 2 * QUADRO / TAXA) for p0, p1 in a.pausas]
        perto = min(candidatas, default=None)
        cortes.append(perto[1] if perto and perto[0] <= 0.6 else max(0.0, estimado - 0.05))
    cortes.append(total_s)

    saida, i = [], 0
    for k, n in enumerate(contagens):
        ini, fim = cortes[k], cortes[k + 1]
        fatia = pcm[int(ini * TAXA) * 2: int(fim * TAXA) * 2]
        relativas = [PalavraNoTempo(round(max(0.0, w.t - ini), 3), w.palavra) for w in palavras[i:i + n]]
        saida.append((fatia, relativas))
        i += n
    return saida
