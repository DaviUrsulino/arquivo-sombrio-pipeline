"""Qual estilo de animação serve para cada FORMATO de vídeo (não para cada assunto).

O `estilo_para()` da produtora já casa estilo com o ASSUNTO ("vídeo de jogo pede estilo de game"). Faltava a outra
metade: o formato. Documentário é direção, não tema — o vídeo do @marcondes.ai sobre o Elon (reel Dfj6T7CR9WW,
23,5 mil curtidas em 7 h) não tem personagem nenhum: é um objeto-herói por cena (logo sobre o globo, placas de
vídeo empilhadas, corredor de data center), câmera lenta e legenda queimada. Pôr um mascote cartoon ali quebraria
o vídeo, por mais que o assunto fosse "tecnologia".

Daí este mapa. Ele reduz a lista de candidatos ANTES do LLM escolher, então o LLM continua decidindo qual dos
bons combina mais com o assunto — só não pode mais escolher um estilo que briga com a forma do vídeo.

As listas saem de duas fontes, nesta ordem:
1. O que as referências medidas usam em cada formato (`segredos/estudos/2026-11-10/`).
2. O nosso próprio desempenho por estilo (`pautas/desempenho.json`), que o `estilos_fracos()` já aplica depois.
"""
from __future__ import annotations

# formato -> (estilos em ordem de preferência, por que esse grupo serve a esse formato)
FORMATOS: dict[str, tuple[list[str], str]] = {
    "documentario": (
        ["satellite-briefing", "teardown", "data-physical", "visual-investigation", "briefing-board",
         "lidar-survey", "archive-lighttable", "news-package", "dark-keynote", "circuit-board", "white-model"],
        "fato de empresa, figura ou acontecimento grande: um objeto-herói por cena, câmera lenta, sem mascote "
        "(padrão do @marcondes.ai e do @voceconstruiu, que mostram a coisa funcionando em vez de alguém explicando)",
    ),
    "historia_personagem": (
        ["hand-drawn-cartoon", "cartoon-3d-short", "scifi-toon", "midcentury-toon", "cel-anime-80s",
         "rubber-hose", "esquete", "3d-toy-character"],
        "série, cotidiano, humor ou qualquer coisa com alguém vivendo a situação: precisa de personagem que ATUA, "
        "com expressão exagerada (padrão do @escolhas.app, @bieldozero, @crafty_animations e @canwebuildthis)",
    ),
    "utilidade": (
        ["living-screencast", "desktop-flythrough", "telestrator", "pictogram-motion", "iso-infographic",
         "whiteboard", "glass-product", "isometric-picture-book"],
        "'como conseguir X': o espectador precisa VER a coisa acontecendo na tela ou o passo a passo, não um "
        "personagem falando (padrão do vídeo de 307 mil do @guics.dev, que mostra a busca sendo digitada)",
    ),
    "numero": (
        ["data-story-charts", "dataviz", "data-physical", "iso-infographic", "transit-map", "countdown"],
        "ranking, comparação, quanto custa, quanto economiza: o número é o herói e precisa crescer na tela",
    ),
}
PADRAO = "historia_personagem"  # na dúvida, personagem que atua rende mais que tela parada

# O HUD que fica na tela o vídeo inteiro, por formato. O Reels de 1,9 milhão do @escolhas.app (102 mil curtidas,
# 22,7 mil comentários) mantém "DIAS RESTANTES: 4" e "GLOW-UP: 75%" com barra enchendo do começo ao fim: quem
# assiste não está vendo uma história, está acompanhando um placar. O nosso HUD existia mas caía num rótulo
# genérico ("VÍDEOS"), que não dá a ninguém motivo para ficar até o fim.
HUD_PADRAO: dict[str, dict] = {
    "documentario": {"tipo": "contador", "rotulo": "O NÚMERO"},
    "historia_personagem": {"tipo": "contador", "rotulo": "TENSÃO"},
    "utilidade": {"tipo": "etapas", "itens": []},
    "numero": {"tipo": "contador", "rotulo": "A CONTA"},
}


def hud(formato: str | None) -> dict:
    """O HUD que faz sentido para este formato. Sem formato conhecido, o contador genérico de sempre."""
    return dict(HUD_PADRAO.get(formato or "", {"tipo": "contador", "rotulo": "VÍDEOS"}))


def recomendados(formato: str) -> list[str]:
    return FORMATOS.get(formato, FORMATOS[PADRAO])[0]


def motivo(formato: str) -> str:
    return FORMATOS.get(formato, FORMATOS[PADRAO])[1]


def filtrar(todos: list[dict], formato: str | None) -> list[dict]:
    """Os estilos do catálogo que servem a este formato, na ordem de preferência. Sem formato, com formato
    desconhecido (erro de digitação não pode virar filtro errado em silêncio) ou se nenhum do mapa existir no
    catálogo, devolve o catálogo inteiro — nunca deixa a produção sem opção."""
    if formato not in FORMATOS:
        return todos
    por_slug = {e["slug"]: e for e in todos}
    escolhidos = [por_slug[s] for s in recomendados(formato) if s in por_slug]
    return escolhidos or todos
