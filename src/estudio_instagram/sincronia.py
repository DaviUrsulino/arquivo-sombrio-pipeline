"""Liga o tempo da fala ao que aparece na tela: âncoras dos elementos e blocos de legenda."""

import unicodedata
from dataclasses import dataclass

ADIANTAMENTO_S = 0.12
PALAVRAS_POR_LEGENDA = 3


@dataclass(frozen=True)
class PalavraNoTempo:
    t: float
    palavra: str


def normalizar(palavra: str) -> str:
    """Minúsculas, sem acento e sem pontuação: "Código," vira "codigo"."""
    sem_acento = unicodedata.normalize("NFD", palavra.lower())
    return "".join(c for c in sem_acento if c.isalnum())


def palavras_do_alinhamento(caracteres: list[str], inicios: list[float]) -> list[PalavraNoTempo]:
    """Junta o tempo por caractere (formato do ElevenLabs) em tempo por palavra.

    O tempo de cada palavra é o do primeiro caractere dela.
    """
    palavras, atual, inicio = [], "", None
    for caractere, t in zip(caracteres, inicios):
        if caractere.isspace():
            if atual:
                palavras.append(PalavraNoTempo(inicio, atual))
            atual, inicio = "", None
            continue
        if inicio is None:
            inicio = t
        atual += caractere
    if atual:
        palavras.append(PalavraNoTempo(inicio, atual))
    return palavras


def tempo_da_ancora(ancora: str, palavras: list[PalavraNoTempo], deslocamento: float = 0.0) -> float:
    """Momento (no vídeo inteiro) em que o elemento deve começar a aparecer.

    Usa a primeira ocorrência da palavra na cena e entra um pouco antes da fala,
    porque o desenho leva alguns décimos para ficar legível.
    """
    alvo = normalizar(ancora)
    for p in palavras:
        if normalizar(p.palavra) == alvo:
            return max(0.0, deslocamento + p.t - ADIANTAMENTO_S)
    raise ValueError(f"âncora '{ancora}' não aparece na narração")


def blocos_de_legenda(palavras: list[PalavraNoTempo], fim: float, tamanho: int = PALAVRAS_POR_LEGENDA) -> list[dict]:
    """Agrupa as palavras em blocos curtos; cada bloco fica na tela até o próximo começar."""
    blocos = []
    for i in range(0, len(palavras), tamanho):
        grupo = palavras[i:i + tamanho]
        seguinte = palavras[i + tamanho].t if i + tamanho < len(palavras) else fim
        blocos.append({"t": grupo[0].t, "fim": seguinte, "texto": " ".join(p.palavra for p in grupo)})
    return blocos
