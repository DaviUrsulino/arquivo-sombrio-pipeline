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

# Formato "novela de mascote" — inspirado nas "novelas de frutas" que
# viralizaram em 2026 (personagem fofo tipo mascote vivendo drama exagerado
# de novela). Pesquisado em 2026-09-08: a estética é fofa/infantil, mas o
# CONTEÚDO não é infantil — é justamente o contraste (visual fofo + drama
# adulto exagerado) que gera o engajamento. Ainda assim, mantém zero
# violência/conteúdo explícito, drama é só emocional (ciúme, traição,
# segredo, reconciliação), pra não escorregar pra território sensível.
# Expandido em 2026-09-08 pra além de fruta (pesquisa confirmou que o
# formato migrou pra qualquer bicho/objeto antropomorfizado — inseto,
# marisco, animal marinho — sem perder o gancho).
PROTAGONISTAS_NOVELA = [
    "um abacate antropomorfizado com rosto fofo e expressivo, personagem recorrente chamado Abacatudo",
    "um morango antropomorfizado com rosto fofo e expressivo, personagem recorrente chamado Moranguete",
    "uma xícara de café antropomorfizada com rosto fofo, personagem recorrente chamado Cafezito",
    "um guarda-chuva antropomorfizado com rosto fofo, personagem recorrente chamado Chuvisco",
    "um cavalo-marinho antropomorfizado com rosto fofo e expressivo, personagem recorrente chamado Marinho",
    "uma joaninha antropomorfizada com rosto fofo e expressivo, personagem recorrente chamada Joaninha",
    "um caramujo antropomorfizado com rosto fofo e expressivo, personagem recorrente chamado Caramelo",
    "uma pipoca antropomorfizada com rosto fofo e expressivo, personagem recorrente chamada Pipoquinha",
]

TEMAS_NOVELA = [
    "descobriu que o melhor amigo está namorando escondido a pessoa que ele amava",
    "planeja confrontar alguém da família numa festa depois de anos guardando um segredo",
    "recebeu uma carta que revela que não é quem sempre pensou que era",
    "está prestes a se casar mas alguém do passado reaparece na noite anterior",
    "descobre uma traição enquanto se prepara pra comemorar um aniversário importante",
    "precisa escolher entre lealdade a um amigo e um amor que sempre negou sentir",
]

# Formato "objeto falante" — pesquisado em 2026-09-08: objeto do dia a dia
# vira personagem com voz reclamando/desabafando da própria vida em tom
# cômico, direto pra câmera (não é drama de novela, é monólogo engraçado).
PROTAGONISTAS_OBJETO_FALANTE = [
    "uma geladeira antropomorfizada com rosto expressivo numa cozinha",
    "um tênis de corrida antropomorfizado com rosto expressivo",
    "uma bolsa de academia antropomorfizada com rosto expressivo",
    "um aspirador de pó antropomorfizado com rosto expressivo",
    "uma escova de dentes antropomorfizada com rosto expressivo",
    "um despertador antropomorfizado com rosto expressivo numa mesa de cabeceira",
    "um carregador de celular antropomorfizado com rosto expressivo",
]

SITUACOES_OBJETO_FALANTE = [
    "desabafando sobre como é maltratado pelo dono todos os dias",
    "reclamando de ter sido substituído por um modelo mais novo e mais bonito",
    "contando o que realmente pensa sobre a rotina do dono, sem filtro",
    "revelando um segredo constrangedor que só ele testemunhou",
    "fazendo um discurso dramático sobre o dia mais humilhante da sua existência",
    "comemorando de forma exagerada uma pequena vitória do cotidiano",
]

# Formato "história em POV histórico" — pesquisado em 2026-09-08: narrador
# reage em primeira pessoa a ser "transportado" pra uma época histórica,
# contraste entre mentalidade moderna e cenário do passado.
EPOCAS_HISTORIA_POV = [
    "a Peste Negra na Europa medieval, 1351",
    "a corte de Versalhes na França, 1780",
    "a Roma Antiga durante o auge do Império, ano 80",
    "o Velho Oeste americano, 1875",
    "a era vitoriana em Londres, 1890",
    "o Egito Antigo durante a construção das pirâmides",
    "a Revolução Industrial em uma fábrica inglesa, 1840",
    "um navio pirata no Caribe, 1720",
]


def escolher_formato_do_dia() -> str:
    """Sorteia o formato do vídeo, com peso maior pro mais validado
    (curiosidade) e menor pros mais novos/menos testados — ajustar os
    pesos conforme os formatos novos forem provando (ou não) que
    performam bem."""
    import random
    formatos = ["curiosidade", "novela", "objeto_falante", "historia_pov"]
    pesos = [40, 25, 20, 15]
    return random.choices(formatos, weights=pesos)[0]


def escolher_tema_do_dia(formato: str | None = None) -> str:
    import random
    formato = formato or escolher_formato_do_dia()

    if formato == "novela":
        protagonista = random.choice(PROTAGONISTAS_NOVELA)
        situacao = random.choice(TEMAS_NOVELA)
        return f"novela_mascote::{protagonista} que {situacao}"

    if formato == "objeto_falante":
        protagonista = random.choice(PROTAGONISTAS_OBJETO_FALANTE)
        situacao = random.choice(SITUACOES_OBJETO_FALANTE)
        return f"objeto_falante::{protagonista}, {situacao}"

    if formato == "historia_pov":
        epoca = random.choice(EPOCAS_HISTORIA_POV)
        return f"historia_pov::{epoca}"

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


ESTILO_NOVELA = (
    "Flat vector cartoon mascot design, extremely cute and expressive, thick soft outlines, "
    "big glossy eyes, bright saturated colors, dramatic soap-opera style lighting with warm "
    "backlight, telenovela close-up framing. Not photorealistic, not 3D render, not scary. "
)

SYSTEM_PROMPT_TEMPLATE_NOVELA = """Você escreve roteiros curtos no formato "novela de mascote" \
pra um canal de TikTok/YouTube Shorts chamado "Em Alta" — o mesmo estilo das "novelas de \
frutas" (Abacatudo, Moranguete) que viralizaram em 2026: um personagem-mascote fofo e \
antropomorfizado vivendo um drama de novela exagerado. O CONTRASTE é o que funciona: visual \
super fofo/infantil + drama emocional adulto e teatral (ciúme, traição, segredo, decisão \
difícil) — NUNCA violência, nunca conteúdo explícito, o drama é só emocional/dramático, tom \
teatral e over-the-top de propósito (isso é o "gancho" do formato, não é sério de verdade).

Protagonista e situação de hoje: {topico}

DURAÇÃO E FORMATO — META EM PALAVRAS, NÃO EM SEGUNDOS
- Use entre 5 e 7 cenas. CONTE PALAVRAS: o roteiro completo (somando todas as cenas) deve ter \
ENTRE 200 E 230 PALAVRAS NO TOTAL — garante ~65-95 segundos mesmo na voz mais rápida do TTS. \
Abaixo de 200 palavras arrisca ficar curto demais pra monetizar (mínimo 60s, sem exceção).
- Narração em primeira pessoa, como se o próprio mascote estivesse contando o drama pro \
espectador, tom teatral e dramático (novela mesmo, exagerado de propósito).

ESTRUTURA DE NOVELA — OBRIGATÓRIA
- Comece já no meio da tensão (nunca com contexto neutro) — frase de abertura tipo "Eu nunca \
devia ter aberto aquela porta." ou "Ele jurou que nunca faria isso comigo.".
- Escale o drama cena a cena (revelação, reação, confronto).
- TERMINE EM GANCHO DE CONTINUAÇÃO — a última cena não resolve o conflito, deixa uma pergunta \
no ar e sinaliza que tem "próximo capítulo" (sem prometer data, só o gancho narrativo).

Sua resposta deve ser APENAS um JSON válido, no formato:
{{
  "genero_narrador": "masculino" ou "feminino",
  "personagem": "descrição visual completa e definitiva do mascote (o que é, cor, rosto, \
detalhe fofo marcante) — usada palavra por palavra em TODAS as cenas pelo código, não repita \
isso no prompt_imagem de cada cena",
  "cenas": [
    {{"narracao": "texto falado nesta cena, tom teatral de novela", "prompt_imagem": "APENAS \
ação/expressão/pose do personagem + enquadramento de câmera + ambiente — SEM redescrever a \
aparência física do personagem"}},
    ...
  ]
}}"""


ESTILO_OBJETO_FALANTE = (
    "Glossy 3D Pixar-style character render, cute anthropomorphic everyday object with big "
    "expressive eyes and a mouth, soft studio lighting, clean simple background, vibrant "
    "colors, animated movie still aesthetic. Not photorealistic, not flat 2D, not scary. "
)

SYSTEM_PROMPT_TEMPLATE_OBJETO_FALANTE = """Você escreve roteiros curtos no formato "objeto \
falante" pra um canal de TikTok/YouTube Shorts chamado "Em Alta" — um objeto do dia a dia \
antropomorfizado (tipo geladeira, tênis, aspirador de pó) fala direto pra câmera num monólogo \
cômico e exagerado sobre a própria existência. É formato de COMÉDIA, não de drama — tom \
sarcástico, espirituoso, autoconsciente e engraçado, nunca sombrio.

Objeto e situação de hoje: {topico}

DURAÇÃO E FORMATO — META EM PALAVRAS, NÃO EM SEGUNDOS
- Use entre 5 e 7 cenas. CONTE PALAVRAS: o roteiro completo (somando todas as cenas) deve ter \
ENTRE 200 E 230 PALAVRAS NO TOTAL — garante ~65-95 segundos mesmo na voz mais rápida do TTS. \
Abaixo de 200 palavras arrisca ficar curto demais pra monetizar (mínimo 60s, sem exceção).
- Narração em primeira pessoa, o próprio objeto falando direto pro espectador como se fosse \
uma câmera/celular na sua frente — tom de stand-up/desabafo cômico, frases curtas e cortantes.

ESTRUTURA — OBRIGATÓRIA
- Abra com uma frase de impacto cômico que já entrega a personalidade do objeto (ex: "Eu \
literalmente seguro sua vida inteira junta e ninguém nem lava minha prateleira.").
- Construa o "desabafo" com 2-3 exemplos concretos e específicos (não genéricos) do cotidiano \
do dono, cada um mais absurdo/engraçado que o anterior.
- Termine com uma virada cômica ou tirada final memorável (não precisa de gancho de \
continuação — este formato é episódico, cada vídeo se resolve sozinho).

Sua resposta deve ser APENAS um JSON válido, no formato:
{{
  "genero_narrador": "masculino" ou "feminino",
  "personagem": "descrição visual completa e definitiva do objeto antropomorfizado (o que é, \
cor, onde fica o rosto/olhos/boca, ambiente típico) — usada palavra por palavra em TODAS as \
cenas pelo código, não repita isso no prompt_imagem de cada cena",
  "cenas": [
    {{"narracao": "texto falado nesta cena, tom cômico de monólogo", "prompt_imagem": "APENAS \
expressão/pose do objeto + enquadramento de câmera + ambiente — SEM redescrever a aparência \
física do objeto"}},
    ...
  ]
}}"""


ESTILO_HISTORIA_POV = (
    "Flat cel-shaded 2D animation, bold clean outlines, historically-inspired color palette "
    "and period costume detail, cinematic dramatic lighting, contemporary illustration style "
    "blended with historical setting. Not photorealistic, not 3D render. "
)

SYSTEM_PROMPT_TEMPLATE_HISTORIA_POV = """Você escreve roteiros curtos no formato "POV \
histórico" pra um canal de TikTok/YouTube Shorts chamado "Em Alta" — um narrador com \
mentalidade e vocabulário completamente modernos é "transportado" pra uma época histórica \
real e reage a ela em primeira pessoa, tempo presente, como se estivesse fazendo um vídeo de \
celular/vlog na época. O CONTRASTE (pessoa moderna reagindo a um mundo antigo) É O HUMOR/GANCHO \
do formato — mas os fatos históricos mencionados devem ser REAIS e verificáveis, só a reação é \
que é cômica/anacrônica.

Época de hoje: {topico}

DURAÇÃO E FORMATO — META EM PALAVRAS, NÃO EM SEGUNDOS
- Use entre 5 e 7 cenas. CONTE PALAVRAS: o roteiro completo (somando todas as cenas) deve ter \
ENTRE 200 E 230 PALAVRAS NO TOTAL — garante ~65-95 segundos mesmo na voz mais rápida do TTS. \
Abaixo de 200 palavras arrisca ficar curto demais pra monetizar (mínimo 60s, sem exceção).
- Narração em primeira pessoa, tempo presente, tom de "POV" (poste de celular reagindo ao \
vivo), misturando espanto genuíno com humor de contraste moderno-vs-antigo.

ESTRUTURA — OBRIGATÓRIA
- Abra com "POV: você acorda em [época]" ou variação direta disso, já estabelecendo o cenário.
- Cada cena seguinte reage a um detalhe histórico REAL e específico dessa época (higiene, \
comida, tecnologia, hierarquia social, etc) com humor de contraste, sem soar didático/aula.
- Baseie os detalhes em fatos históricos verdadeiros — não invente evento específico, use \
características gerais bem documentadas da época.
- Termine com uma reação final cômica que resume a experiência (sem gancho de continuação \
obrigatório, mas pode sugerir "será que consigo voltar" como fechamento leve).

Sua resposta deve ser APENAS um JSON válido, no formato:
{{
  "genero_narrador": "masculino" ou "feminino",
  "personagem": "descrição visual completa e definitiva de como o narrador aparece nas cenas \
(roupa de época + algum detalhe anacrônico sutil, aparência geral) — usada palavra por palavra \
em TODAS as cenas pelo código, não repita isso no prompt_imagem de cada cena",
  "cenas": [
    {{"narracao": "texto falado nesta cena, tom de POV/reação em primeira pessoa", "prompt_imagem": "APENAS \
ação/expressão/pose do personagem + enquadramento de câmera + ambiente/cenário histórico — SEM \
redescrever a aparência física do personagem"}},
    ...
  ]
}}"""


# Terceiro item de cada tupla é o perfil de ambiência sonora (ver
# PERFIS_AMBIENCIA em montar_video_local.py).
_TEMPLATES_POR_FORMATO = {
    "novela_mascote": (SYSTEM_PROMPT_TEMPLATE_NOVELA, ESTILO_NOVELA, "dramatico"),
    "objeto_falante": (SYSTEM_PROMPT_TEMPLATE_OBJETO_FALANTE, ESTILO_OBJETO_FALANTE, "leve"),
    "historia_pov": (SYSTEM_PROMPT_TEMPLATE_HISTORIA_POV, ESTILO_HISTORIA_POV, "epico"),
}


def montar_canal_dinamico(topico: str, estilo_visual: str | None = None, restricoes: str | None = None):
    """Monta um objeto com a mesma interface de terror.py/true_crime.py, mas
    com o SYSTEM_PROMPT construído em cima do tema escolhido pra essa
    execução. Temas prefixados com "<formato>::" usam o template, estilo
    visual e ambiência daquele formato em vez do padrão de curiosidade."""
    for prefixo, (template, estilo_formato, ambiencia) in _TEMPLATES_POR_FORMATO.items():
        if topico.startswith(f"{prefixo}::"):
            topico_real = topico.removeprefix(f"{prefixo}::")
            return types.SimpleNamespace(
                NOME_CANAL=NOME_CANAL,
                VOZES_LOCAIS=VOZES_LOCAIS,
                PASTA_IMAGENS=PASTA_IMAGENS,
                MASTER_STYLE_LOCK=estilo_visual or estilo_formato,
                RESTRICOES=restricoes or RESTRICOES_PADRAO,
                SYSTEM_PROMPT=template.format(topico=topico_real),
                AMBIENCIA=ambiencia,
            )

    return types.SimpleNamespace(
        NOME_CANAL=NOME_CANAL,
        VOZES_LOCAIS=VOZES_LOCAIS,
        PASTA_IMAGENS=PASTA_IMAGENS,
        MASTER_STYLE_LOCK=estilo_visual or ESTILO_PADRAO,
        RESTRICOES=restricoes or RESTRICOES_PADRAO,
        SYSTEM_PROMPT=SYSTEM_PROMPT_TEMPLATE.format(topico=topico),
        AMBIENCIA="leve",
    )
