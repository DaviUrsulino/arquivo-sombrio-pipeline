"""Canal "Em Alta" — conta separada dedicada a formatos/temas em alta no
momento, gerando um vídeo narrado ORIGINAL inspirado no tema do dia (nunca
copiando conteúdo de terceiro).

IMPORTANTE — limitação conhecida: pesquisa de tendência 100% ao vivo (via
Gemini com Google Search grounding) foi testada em 2026-09-07 e deu 429
(cota esgotada/indisponível no plano gratuito da API). Enquanto isso não
mudar, TEMAS_ROTATIVOS abaixo precisa ser atualizado periodicamente à mão
(pesquisa manual, tipo a que já foi feita pro terror/true_crime) em vez de
pesquisa automática a cada execução. Se um dia tiver uma API de busca paga
configurada, dá pra trocar `escolher_tema_do_dia` por uma pesquisa real.

Diferente de terror.py/true_crime.py, o estilo visual muda por tema em vez
de ser fixo — `montar_canal_dinamico()` monta um objeto com a mesma
interface dos outros canais (SYSTEM_PROMPT, MASTER_STYLE_LOCK, RESTRICOES,
VOZES_LOCAIS, PASTA_IMAGENS, NOME_CANAL) pra reusar o resto do pipeline sem
precisar mudar nada nele.
"""

import types

NOME_CANAL = "Em Alta"

VOZES_LOCAIS = {
    "masculino": "pm_alex",
    "feminino": "pf_dora",
}

PASTA_IMAGENS = "imagens_aprovadas/tendencias"

ESTILO_PADRAO = (
    "Flat cel-shaded 2D animation, bold clean outlines, warm modern color "
    "palette, soft lighting, contemporary social-media illustration style. "
    "Not photorealistic, not 3D render. "
)

RESTRICOES_PADRAO = "No gore, no blood, no real named individual depicted, family-friendly."

# Atualizar esta lista periodicamente com pesquisa manual do que está em
# alta em formato de vídeo curto (curiosidades, fatos, histórias reais
# curtas e virais, etc) — cada item é (tema, estilo_visual opcional).
TEMAS_ROTATIVOS = [
    "uma curiosidade científica real que soa falsa mas é comprovada",
    "um fato histórico obscuro que poucas pessoas conhecem",
    "uma coincidência real documentada que parece roteiro de filme",
    "um recorde mundial bizarro e verídico",
    "um mistério da natureza que a ciência só explicou recentemente",
    "uma invenção acidental que mudou o mundo",
    "um erro de cálculo ou engenharia real que causou consequências gigantescas",
    "um animal com uma habilidade ou comportamento que parece ficção científica",
    "uma decisão de negócio real que pareceu péssima na época mas deu certo (ou o contrário)",
    "um fenômeno psicológico real que explica um comportamento humano comum",
    "uma tecnologia antiga que era surpreendentemente avançada pro seu tempo",
    "um lugar real na Terra com uma característica física que parece impossível",
    "uma regra ou lei bizarra e real que ainda está em vigor em algum lugar",
    "um erro histórico que as pessoas ainda repetem por engano até hoje",
    "uma experiência científica real que teve um resultado completamente inesperado",
    "um objeto do cotidiano com uma origem ou motivo de existir surpreendente",
]

# Rotina de manutenção sugerida: revisar esta lista a cada poucas semanas —
# tirar tema que sempre gerar roteiro fraco, acrescentar categoria nova.
# Não é pesquisa de tendência ao vivo (isso ainda depende de uma API de
# busca paga, ver comentário no topo do arquivo).


def escolher_tema_do_dia() -> str:
    import random
    return random.choice(TEMAS_ROTATIVOS)


SYSTEM_PROMPT_TEMPLATE = """Você escreve roteiros curtos e narrados para um canal de TikTok/\
YouTube Shorts chamado "Em Alta", cujo tema muda a cada vídeo de acordo com o que está \
performando bem no formato curto. O tema de hoje é: {topico}

Escreva um roteiro ORIGINAL inspirado nesse tema (história curta, curiosidade surpreendente, \
ou fato real contado de forma envolvente) — nunca copie ou resuma um vídeo específico de outra \
pessoa.

DURAÇÃO E FORMATO — META EM PALAVRAS, NÃO EM SEGUNDOS
- Use entre 5 e 7 cenas. A velocidade de fala do TTS VARIA por voz (masculina ~30% mais rápida \
que feminina) — "segundos por cena" não é confiável. CONTE PALAVRAS: o roteiro completo \
(somando todas as cenas) deve ter ENTRE 200 E 230 PALAVRAS NO TOTAL — garante ~65-95 segundos \
mesmo na voz mais rápida. Abaixo de 200 palavras arrisca ficar curto demais pra monetizar \
(mínimo 60s, sem exceção). Não escreva a duração, apenas o texto.
- Narrador único, tom envolvente e direto, sem enrolação.

O HOOK (cena 1) DECIDE SE ALGUÉM CONTINUA ASSISTINDO
- Abra com uma frase que gera uma pergunta na cabeça de quem assiste (loop aberto: confissão, \
afirmação contraintuitiva, ou consequência antes da causa) — nunca uma descrição neutra do \
assunto.

ESTILO DE ESCRITA
- Frases curtas e diretas, uma ideia por frase, sem floreio.

Sua resposta deve ser APENAS um JSON válido, no formato:
{{
  "genero_narrador": "masculino" ou "feminino",
  "personagem": "descrição do protagonista/narrador recorrente nas cenas, ou null se o tema \
não pedir um personagem fixo",
  "cenas": [
    {{"narracao": "texto falado nesta cena", "prompt_imagem": "descrição da cena pra gerar \
imagem — ambiente, ação, enquadramento, SEM redescrever a aparência do personagem se houver \
um (isso é inserido automaticamente pelo código)"}},
    ...
  ]
}}"""


def montar_canal_dinamico(topico: str, estilo_visual: str | None = None, restricoes: str | None = None):
    """Monta um objeto com a mesma interface de terror.py/true_crime.py, mas
    com o SYSTEM_PROMPT construído em cima do tema escolhido pra essa
    execução."""
    return types.SimpleNamespace(
        NOME_CANAL=NOME_CANAL,
        VOZES_LOCAIS=VOZES_LOCAIS,
        PASTA_IMAGENS=PASTA_IMAGENS,
        MASTER_STYLE_LOCK=estilo_visual or ESTILO_PADRAO,
        RESTRICOES=restricoes or RESTRICOES_PADRAO,
        SYSTEM_PROMPT=SYSTEM_PROMPT_TEMPLATE.format(topico=topico),
    )
