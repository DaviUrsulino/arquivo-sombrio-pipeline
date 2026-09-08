"""Cada módulo aqui é a configuração de um canal/nicho: SYSTEM_PROMPT (roteiro),
MASTER_STYLE_LOCK/RESTRICOES (estilo de imagem), VOZ (ElevenLabs) e PASTA_IMAGENS.

Adicionar um canal novo é criar um módulo aqui e registrar em CANAIS abaixo —
o resto do pipeline (gerar_roteiro.py, montar_video.py) já funciona pra
qualquer canal registrado, sem precisar mudar mais nada.
"""

from . import terror, true_crime

CANAIS = {
    "terror": terror,
    "true_crime": true_crime,
}


def carregar_canal(nome: str):
    if nome not in CANAIS:
        opcoes = ", ".join(CANAIS)
        raise ValueError(f"Canal desconhecido: {nome!r}. Opções: {opcoes}")
    return CANAIS[nome]
