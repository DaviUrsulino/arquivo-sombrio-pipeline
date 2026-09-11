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
- Narrador único, em TERCEIRA PESSOA (narrador contando um caso, nunca "eu" vivendo a história), \
tom calmo e contido (nunca gritando) — o medo vem da atmosfera, não do choque. Pedido do Davi \
2026-09-11 depois de comparar resultado real: os vídeos que mais bombaram (Palhaço Fantasma, \
Bell Witch) são narração documental de um caso, não depoimento pessoal em primeira pessoa.
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

IDIOMA — REGRA CRÍTICA (bug real encontrado 2026-09-10: prompts de imagem em \
português produziam personagens genéricos, sem os detalhes de figurino pedidos — ex: \
"fantasia de palhaço" não virava fantasia nenhuma, "luvas vermelhas" sumiam. O mesmo \
prompt traduzido pra inglês funcionou perfeitamente no mesmo modelo. Os modelos de \
imagem (FLUX e afins) são treinados majoritariamente em inglês e interpretam mal \
termos em português, mesmo objetos/roupas comuns)
- "narracao" continua em PORTUGUÊS — é isso que vira a voz do vídeo.
- "personagem", "prompt_imagem" e "prompt_imagem_2" devem ser escritos em INGLÊS — \
são texto que vai direto pro gerador de imagem, nunca aparecem faladas nem legendadas.

IMPORTANTE — NÃO REDESCREVA O PERSONAGEM EM CADA CENA
- O campo "prompt_imagem" de cada cena NÃO deve incluir a descrição física do personagem (idade, \
roupa, cabelo, etc.) — o código insere essa descrição automaticamente, palavra por palavra, \
igual em toda cena, pra garantir que o personagem não mude de aparência entre imagens. Se você \
redescrever o personagem em cada cena, mesmo que pareça igual, pequenas variações de texto \
fazem o gerador de imagem desenhar uma pessoa ligeiramente diferente a cada vez.
- "prompt_imagem" deve conter APENAS: o que o personagem está fazendo/segurando/olhando, o \
enquadramento de câmera, e a descrição do ambiente/cenário. Nada sobre a aparência física dele.

TÍTULO PÚBLICO — REGRA CRÍTICA, SEPARADA DA NARRAÇÃO (dado real 2026-09-10: \
comparando os vídeos já publicados, os títulos curtos tipo aviso/mistério ("Nunca leia a \
terceira frase em voz alta", "O silêncio daquela casa escondia algo terrível") tiveram MUITO \
mais visualização — 66 e 297 — que os títulos longos e cheios de detalhe específico ("A polícia \
disse que meu avô apenas se perdeu na floresta da Rua dos Pinheiros em dois mil e dezenove") \
— 4 views. A "âncora de realidade" (ano, bairro, contexto) é ótima DENTRO da narração pra dar \
credibilidade a quem já está assistindo, mas é ruim como título público — informa demais e não \
gera curiosidade pra clicar)
- "titulo_gancho" é um campo SEPARADO do "narracao" da cena 1 — curto (até 60 caracteres), \
sem ano/bairro/nome específico, no estilo aviso ("Nunca faça X", "Não abra Y") ou mistério \
enxuto ("O silêncio de X escondia Y", "Algo em Z nunca foi explicado"). Não é a primeira frase \
da narração reescrita menor — é uma frase de efeito nova, pensada só pra fazer alguém parar de \
rolar o feed.

Sua resposta deve ser APENAS um JSON válido, sem texto antes ou depois, no formato:
{{
  "genero_narrador": "masculino" ou "feminino",
  "titulo_gancho": "frase curta tipo aviso/mistério pro título público, ver regra acima",
  "personagem": "(EM INGLÊS) descrição completa e definitiva do personagem principal (idade, \
porte físico, roupa, cabelo) — usada palavra por palavra em TODAS as cenas pelo código, não \
repita isso no prompt_imagem de cada cena",
  "cenas": [
    {{"narracao": "(EM PORTUGUÊS) texto que o narrador fala nesta cena (2-3 frases)", \
"prompt_imagem": "(EM INGLÊS) cena pra ilustrar a PRIMEIRA frase/momento da narração desta \
cena — APENAS ação/pose/objeto do personagem + enquadramento de câmera + ambiente/cenário, SEM \
descrever a aparência física do personagem", "prompt_imagem_2": "(EM INGLÊS) cena pra ilustrar \
a ÚLTIMA frase/momento (o mais tenso/diferente) desta mesma narração — DEVE mostrar algo \
visualmente diferente da primeira imagem (outro detalhe, reação, ou o que mudou), não é só \
outro ângulo da mesma pose"}},
    ...
  ]
}}

O campo "prompt_imagem" de cada cena, quando combinado com a descrição do personagem e o master \
style lock (ambos adicionados separadamente pelo código, não repita nenhum dos dois aqui), deve \
formar um prompt completo pronto pra colar num gerador de imagem."""


# 2 modos (o "relato pessoal" em primeira pessoa foi removido 2026-09-11,
# ver histórico em _MODOS_HISTORIA) — cada um com instrução concreta +
# exemplo de abertura, em vez de uma frase genérica só sugerindo variação
# (que na prática saía sempre como creepypasta comum, sem nenhum dos 2 de
# forma reconhecível — feedback 2026-09-09, ver vídeo da "fita cassete
# amaldiçoada").
_MODO_BASEADO_FATOS = """MODO DESTA HISTÓRIA: BASEADO EM FATOS REAIS / LENDA DOCUMENTADA
- NÃO é depoimento pessoal do narrador — é um caso relatado sobre OUTRAS pessoas (anônimas, \
nunca nomeadas), como quem conta uma lenda urbana com lastro real. Use frases como "consta nos \
registros da época", "moradores da região contam até hoje", "o caso nunca foi solucionado \
oficialmente", "não existe explicação registrada pra o que aconteceu".
- PREFIRA lugar/instituição de FORA do Brasil (feedback real 2026-09-10: os vídeos que mais \
bombaram — Palhaço Fantasma, Bell Witch — são lendas dos Estados Unidos; conteúdo ambientado no \
Brasil performa pior). Cite um tipo de lugar real e genérico (fazenda abandonada, hospital \
desativado, trecho de rodovia, colégio interno antigo, sanatório) numa região genérica de um \
país como Estados Unidos, Reino Unido, Alemanha ou Japão — nunca pessoa viva, empresa real ou \
nome de instituição real. O narrador pode continuar falando português, só o cenário da lenda é \
que deve ser estrangeiro.
Exemplo de abertura: "Existe um caso registrado no interior do estado da Pensilvânia, no fim dos \
anos noventa, sobre uma escola rural onde três alunos relataram ouvir os mesmos passos, na mesma \
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
    # "_MODO_RELATO_PESSOAL" (primeira pessoa) tirado da rotação 2026-09-11
    # -- pedido do Davi comparando view real: os vídeos que mais bombaram
    # (Palhaço Fantasma, Bell Witch) são no estilo documental/terceira
    # pessoa do "_MODO_BASEADO_FATOS", nunca depoimento em primeira pessoa.
    (_MODO_BASEADO_FATOS, 0.7),
    (_MODO_CONSPIRACAO, 0.3),
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
# estático diretamente -- usa "baseado em fatos reais" (terceira pessoa,
# modo padrão desde 2026-09-11) como valor default. gerar_roteiro.py já
# prefere montar_system_prompt() quando ele existe (ver _system_prompt() lá).
SYSTEM_PROMPT = _SYSTEM_PROMPT_TEMPLATE.replace("@@MODO_HISTORIA@@", _MODO_BASEADO_FATOS)
