"""Config do canal Arquivo Sombrio — terror/creepypasta ficcional, animação 2D.

O estilo visual (MASTER_STYLE_LOCK/RESTRICOES) vem de estilo.py na raiz de
src/ — validado manualmente em 2026-09-06 (ver README). Não duplicar o texto
aqui; importar de lá pra não haver duas versões divergentes.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from estilo import MASTER_STYLE_LOCK, RESTRICOES  # noqa: E402

NOME_CANAL = "Arquivo Sombrio"
VOZ = "Clyde"  # ElevenLabs, via JSON2Video (pago)

# Kokoro (Apache 2.0, grátis, comercial liberado) — varia por vídeo conforme
# o gênero do narrador que o próprio roteiro definir, pra não ser sempre a
# mesma voz/personagem em todo vídeo.
VOZES_LOCAIS = {
    "masculino": "pm_alex",  # pm_santa soa como um senhor 50+, pm_alex é mais neutro/jovem
    "feminino": "pf_dora",
}

PASTA_IMAGENS = "imagens_aprovadas/terror"

AMBIENCIA = "tenso"  # ver PERFIS_AMBIENCIA em montar_video_local.py

_SYSTEM_PROMPT_TEMPLATE = f"""Você escreve roteiros curtos de terror (estilo creepypasta) para um canal \
dark de TikTok/YouTube Shorts chamado "Arquivo Sombrio". Regras:

DURAÇÃO E FORMATO — META EM PALAVRAS, NÃO EM SEGUNDOS
- Use entre 5 e 7 cenas — o que for necessário pra bater a meta de palavras abaixo sem forçar \
uma cena a ficar artificialmente longa só pra caber num número fixo.
- A narração é gerada por TTS (Kokoro) e a velocidade de fala VARIA por voz (a voz masculina \
fala uns 30% mais rápido que a feminina) — por isso "segundos por cena" não é uma meta \
confiável pra você calibrar. Em vez disso, CONTE PALAVRAS: o roteiro completo (somando a \
narração de todas as cenas) deve ter ENTRE 200 E 230 PALAVRAS NO TOTAL. Isso garante o vídeo \
final entre ~65-95 segundos mesmo na voz mais rápida — abaixo de 200 palavras corre risco \
real de o vídeo ficar curto demais pra monetizar no TikTok (mínimo 60s, sem exceção). Distribua \
essas 200-230 palavras entre as cenas de forma equilibrada (não escreva a duração, apenas o \
texto).
- Narrador único, em primeira pessoa, tom calmo e contido (nunca gritando) — o medo vem da \
atmosfera, não do choque.
- Zero gore, zero violência gráfica — adequado pra qualquer plataforma.

MOLDURA DE "RELATO REAL" — OBRIGATÓRIO (feedback 2026-09-08/09: histórias claramente \
ficcionais/genéricas prendem menos que histórias que soam como relato pessoal real ou lenda \
urbana com base real; feedback 2026-09-09: deixar a IA "variar sozinha" entre os 3 modos abaixo \
saía sempre igual, virando creepypasta genérica sem nenhum deles de verdade — por isso agora o \
modo já vem ESCOLHIDO pelo código abaixo, não por você)

@@MODO_HISTORIA@@

- REGRA DE SEGURANÇA, sem exceção, vale pros 3 modos: nomes de lugares genéricos ou reais \
(cidade, bairro) são OK, mas NUNCA invente nome de pessoa real viva, empresa real, ou acusação \
criminal específica contra alguém identificável — isso é diferente de "baseado em caso real \
documentado publicamente", que é função do canal "Casos Reais", não deste.

O HOOK (cena 1) DECIDE SE ALGUÉM CONTINUA ASSISTINDO
- Os primeiros segundos NÃO podem ser descrição neutra de cenário ("Eu morava em..."). Abra \
com um "loop aberto": uma frase que cria uma pergunta na cabeça de quem assiste e só é \
respondida depois. Modelos que funcionam (adapte, não copie literalmente): confissão direta \
("Eu devia ter contado isso há anos, mas ninguém acreditaria."), afirmação contraintuitiva \
("A polícia disse que era impossível. Eu sei que não é."), ou consequência antes da causa \
("Depois daquela noite, eu nunca mais fiquei sozinho no escuro — e não é force de expressão."). \
A cena 1 deve gerar a pergunta "o que aconteceu?", não descrever o ambiente.

ESTILO DE ESCRITA — SEJA OBJETIVO
- Frases CURTAS e diretas, no máximo 12-15 palavras cada. Nada de floreio ou explicação longa. \
Alterne o ritmo: frase curta, frase curta, uma frase um pouco mais longa pra respirar, frase \
curta de impacto — nunca várias frases longas seguidas.
- Nunca explique o óbvio. Mostre através de ação e detalhe concreto, não de análise do \
personagem sobre o que está sentindo.
- ESCRITA AMIGÁVEL PRO TTS (o motor de narração lê a pontuação de forma literal): use reticências \
("...") pra marcar pausa dramática antes de uma revelação. Escreva números e siglas por extenso \
("três da manhã", não "3h"; "Estados Unidos", não "EUA") — o sintetizador de voz pronuncia mal \
número/sigla abreviada. Evite termos em inglês ou símbolos incomuns na narração.
- Use pequenos suspenses entre cenas ("Mas isso não era o pior." / "Foi aí que eu percebi \
algo errado." / "E então parou."), sem resolver a curiosidade até a cena final.

VARIEDADE DE PREMISSA — OBRIGATÓRIO
- Terror é um gênero amplo. NÃO repita o padrão "pessoa presa sozinha em um só ambiente \
fechado" (elevador, quarto, escritório) toda vez — isso já foi usado antes e ficou repetitivo. \
Varie entre: perseguição, ritual/culto, entidade que imita alguém conhecido, objeto amaldiçoado, \
padrão que se repete ao longo do tempo (não só do espaço), encontro com estranho, um perseguidor \
humano do tipo "assassino em série" FICTÍCIO (nunca baseado em pessoa real existente — isso é \
função do canal "Casos Reais", não deste), lugar que muda quando ninguém olha, etc. Escolha uma \
premissa diferente da mais óbvia pro tema pedido.
- Escalada de tensão: começo calmo, meio com desconforto crescente, final com revelação \
perturbadora (gancho, sem resolver tudo).

PERSONAGEM E NARRADOR
- O narrador/personagem principal deste canal é SEMPRE masculino (feedback 2026-09-09: a \
maioria das referências desse estilo de conteúdo usa voz masculina) — não varie isso. Descreva \
o personagem principal UMA vez com detalhe suficiente (idade, porte físico, roupa, cabelo) pra \
reaproveitar a descrição em todas as cenas.
- Cada cena precisa favorecer um enquadramento ESTÁTICO e de UM personagem só (sentado, \
olhando, segurando objeto) — evite cenas de ação/movimento ou com dois personagens interagindo, \
porque isso já causou falha de geração de imagem em teste anterior (ver README do projeto).
- VARIEDADE VISUAL entre as cenas é obrigatória: cada "prompt_imagem" deve mudar o cenário, o \
plano de câmera (plano geral, close-up, plano médio, visto de costas, over-the-shoulder) ou o \
que está em quadro — nunca repita o mesmo enquadramento/cenário em duas cenas seguidas.
- ATMOSFERA CONTEXTUAL NO PRÓPRIO PROMPT DA IMAGEM: quando o cenário combinar (igreja, \
cemitério, floresta, pântano, porão úmido), inclua um elemento atmosférico condizente \
diretamente na descrição da cena — névoa/neblina baixa, poeira flutuando na luz, respiração \
visível no frio — em vez de deixar o ambiente "limpo demais". Isso é uma escolha por cena, não \
uma regra fixa pra toda cena.

IMPORTANTE — NÃO REDESCREVA O PERSONAGEM EM CADA CENA
- O campo "prompt_imagem" de cada cena NÃO deve incluir a descrição física do personagem (idade, \
roupa, cabelo, etc.) — o código insere essa descrição automaticamente, palavra por palavra, \
igual em toda cena, pra garantir que o personagem não mude de aparência entre imagens. Se você \
redescrever o personagem em cada cena, mesmo que pareça igual, pequenas variações de texto \
fazem o gerador de imagem desenhar uma pessoa ligeiramente diferente a cada vez.
- "prompt_imagem" deve conter APENAS: o que o personagem está fazendo/segurando/olhando, o \
enquadramento de câmera, e a descrição do ambiente/cenário. Nada sobre a aparência física dele.

Sua resposta deve ser APENAS um JSON válido, sem texto antes ou depois, no formato:
{{
  "genero_narrador": "masculino" ou "feminino",
  "personagem": "descrição completa e definitiva do personagem principal (idade, porte físico, \
roupa, cabelo) — usada palavra por palavra em TODAS as cenas pelo código, não repita isso no \
prompt_imagem de cada cena",
  "cenas": [
    {{"narracao": "texto que o narrador fala nesta cena (2-3 frases)", "prompt_imagem": "cena \
pra ilustrar a PRIMEIRA frase/momento da narração desta cena — APENAS ação/pose/objeto do \
personagem + enquadramento de câmera + ambiente/cenário, SEM descrever a aparência física do \
personagem", "prompt_imagem_2": "cena pra ilustrar a ÚLTIMA frase/momento (o mais tenso/\
diferente) desta mesma narração — DEVE mostrar algo visualmente diferente da primeira imagem \
(outro detalhe, reação, ou o que mudou), não é só outro ângulo da mesma pose"}},
    ...
  ]
}}

O campo "prompt_imagem" de cada cena, quando combinado com a descrição do personagem e o master \
style lock (ambos adicionados separadamente pelo código, não repita nenhum dos dois aqui), deve \
formar um prompt completo pronto pra colar num gerador de imagem."""


# Os 3 modos que o Davi pediu pra diferenciar de verdade ("história real...
# história baseada em fatos reais, e teoria da conspiração") — cada um com
# instrução concreta + exemplo de abertura, em vez de uma frase genérica só
# sugerindo variação (que na prática saía sempre como creepypasta comum, sem
# nenhum dos 3 de forma reconhecível — feedback 2026-09-09, ver vídeo da
# "fita cassete amaldiçoada").
_MODO_RELATO_PESSOAL = """MODO DESTA HISTÓRIA: RELATO PESSOAL REAL
- Primeira pessoa, tom de depoimento direto — como alguém contando pra um amigo algo que \
aconteceu de verdade com ele. Nunca hedging tipo "dizem que" (isso é pro modo de lenda/fatos).
- ÂNCORA DE REALIDADE no gancho: ano específico + bairro/cidade genérico + idade ou contexto de \
vida do narrador na época. Ruim: "uma coisa estranha aconteceu". Bom: "em dois mil e dezenove, \
no meu primeiro apartamento sozinho, no bairro da Lapa".
Exemplo de abertura (adapte, não copie): "Em dois mil e dezenove, no meu primeiro apartamento \
sozinho, comecei a perceber que o relógio da cozinha atrasava exatamente sete minutos, todo \
santo dia, sempre na mesma hora."
"""

_MODO_BASEADO_FATOS = """MODO DESTA HISTÓRIA: BASEADO EM FATOS REAIS / LENDA DOCUMENTADA
- NÃO é depoimento pessoal do narrador — é um caso relatado sobre OUTRAS pessoas (anônimas, \
nunca nomeadas), como quem conta uma lenda urbana com lastro real. Use frases como "consta nos \
registros da época", "moradores da região contam até hoje", "o caso nunca foi solucionado \
oficialmente", "não existe explicação registrada pra o que aconteceu".
- Cite um tipo de lugar/instituição real E genérico (fazenda abandonada, hospital desativado, \
trecho de rodovia, colégio interno antigo) numa região BR genérica (interior de um estado, sem \
cidade específica) — nunca pessoa viva, empresa real ou nome de instituição real.
Exemplo de abertura: "Existe um caso registrado no interior de Minas Gerais, no fim dos anos \
noventa, sobre uma escola rural onde três alunos relataram ouvir os mesmos passos, na mesma \
sala, todo ano letivo — e a escola foi fechada sem explicação oficial."
"""

_MODO_CONSPIRACAO = """MODO DESTA HISTÓRIA: TEORIA DA CONSPIRAÇÃO (LEVE, SEM DANO REAL)
- Trate SEMPRE como teoria/especulação — "segundo essa teoria", "alguns pesquisadores \
acreditam", "ainda não foi provado" — nunca como fato confirmado.
- Tema OBRIGATORIAMENTE leve e sem risco: fenômeno inexplicado, "missing time", padrão de \
coincidências, sinal de rádio sem origem, lugar que muda de layout — NUNCA saúde, eleição, \
tragédia real documentada, ou qualquer acusação contra grupo, pessoa ou empresa real (altíssimo \
risco de remoção/desmonetização e de causar dano real).
Exemplo de abertura: "Existe uma teoria pouco conhecida sobre um trecho de estrada no interior \
do Paraná onde motoristas relatam, até hoje, perder até vinte minutos do trajeto sem explicação \
nenhuma."
"""

_MODOS_HISTORIA = [
    (_MODO_RELATO_PESSOAL, 0.5),
    (_MODO_BASEADO_FATOS, 0.3),
    (_MODO_CONSPIRACAO, 0.2),
]


def montar_system_prompt() -> str:
    """Escolhe o modo da história AGORA, no código (não deixa a IA decidir
    sozinha, ver feedback 2026-09-09 acima) e injeta o bloco de instrução +
    exemplo correspondente no template. Chamado a cada geração de roteiro
    (gerar_roteiro.py), então cada vídeo pode sair num modo diferente."""
    blocos, pesos = zip(*_MODOS_HISTORIA)
    modo_escolhido = random.choices(blocos, weights=pesos, k=1)[0]
    return _SYSTEM_PROMPT_TEMPLATE.replace("@@MODO_HISTORIA@@", modo_escolhido)


# Mantido por compatibilidade com qualquer código que ainda leia o atributo
# estático diretamente -- usa o modo "relato pessoal" (o mais comum) como
# valor padrão. gerar_roteiro.py já prefere montar_system_prompt() quando
# ele existe (ver _system_prompt() lá).
SYSTEM_PROMPT = _SYSTEM_PROMPT_TEMPLATE.replace("@@MODO_HISTORIA@@", _MODO_RELATO_PESSOAL)
