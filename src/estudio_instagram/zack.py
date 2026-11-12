"""Frente "Zack": curiosidade absurda no molde do Zack D. Films, para os dois canais do YouTube e, nos temas de
tecnologia, para o Instagram.

Davi, 11/11: "o YouTube pra mim é viralizar. Foda-se o nome, foda-se tudo. Vai pegar o que mais viraliza e faz."
O que mais viraliza em Short animado, medido em 11/11 (`segredos/FORMATOS.md`, seções 8 e 9): o canal Zack D.
Films, com piso de milhões por vídeo e topo de 50 milhões. Transcrevi 5 vídeos dele (`referencias/transcricoes/
youtube-zackdfilms/`): 28 a 38 s, a primeira frase já é o mecanismo, segunda pessoa, número concreto, uma virada
com "Mas", a última frase é a imagem mais forte, e ZERO pedido no fim. Em 3 dos 5 a câmera entra onde nenhuma
câmera entra (dentro da pele, dentro do peito, a represa feita de gente).

Os fatos vêm da Wikipédia (mesmo leitor do `historias_tech.py`); o prompt (`segredos/prompts/zack.txt`) proíbe
inventar número. Cada tema tem um MOLDE (e-se, por-que, dentro, caso-real, como-sobrevive) para o ciclo de teste
medir qual molde rende mais, não só qual assunto.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from . import series

# (slug, artigo da Wikipédia em inglês, molde, ângulo que o roteirista segue, serve ao Instagram?)
# Instagram (@ursulino.ia) só leva os temas com pé em tecnologia: Davi, 11/11, "pelo menos algo que tenha
# minimamente a ver". YouTube leva todos.
TEMAS = [
    ("mensagem-no-cabo-submarino", "Submarine communications cable", "dentro",
     "por onde passa a sua mensagem: dentro do cabo no fundo do mar, a fibra fina como um fio de cabelo, "
     "quantos quilômetros de cabo existem e o que acontece quando um rompe", True),
    ("onze-dias-sem-dormir", "Randy Gardner sleep deprivation experiment", "e-se",
     "o que aconteceu com o corpo e a cabeça dele a cada dia sem dormir, até o dia 11", False),
    ("dentro-da-picada-do-mosquito", "Mosquito", "dentro",
     "o que a probóscide faz dentro da sua pele: as agulhas, a saliva que impede o sangue de coagular, "
     "por que coça", False),
    ("dentro-do-chip-do-celular", "Integrated circuit", "dentro",
     "o que tem dentro do chip: bilhões de transistores menores que um vírus, como se grava isso no silício", True),
    ("cair-na-lava", "Lava", "e-se",
     "o que acontece com um corpo que cai na lava: temperatura, densidade (você não afunda) e por quê", False),
    ("raio-por-dentro-do-corpo", "Lightning injury", "dentro",
     "o caminho da corrente pelo corpo, as marcas de Lichtenberg na pele, por que a maioria sobrevive", False),
    ("tunel-que-atravessa-a-terra", "Gravity train", "e-se",
     "se você pulasse num túnel que atravessa a Terra de lado a lado: quanto tempo leva, a velocidade no "
     "centro, por que você volta", False),
    ("coco-do-aviao", "Aircraft lavatory", "dentro",
     "para onde vai o que você dá descarga no avião: o vácuo, o tanque, o mito do gelo azul", False),
    ("queda-de-dez-mil-metros", "Vesna Vulović", "caso-real",
     "a queda de 10 mil metros sem paraquedas e por que ela sobreviveu", False),
    ("duas-bombas-atomicas", "Tsutomu Yamaguchi", "caso-real",
     "o homem que estava em Hiroshima e em Nagasaki nos dois dias das bombas", False),
    ("bicho-que-sobrevive-no-espaco", "Tardigrade", "como-sobrevive",
     "como o tardígrado sobrevive ao vácuo, à radiação e a anos sem água", False),
    ("engolido-por-uma-baleia", "Blue whale", "e-se",
     "se uma baleia-azul tentasse te engolir: o tamanho da garganta dela, o que cabe, o que não cabe", False),
    ("dentro-da-bateria-do-celular", "Lithium-ion battery", "dentro",
     "o que acontece dentro da bateria quando ela carrega, e por que ela pega fogo quando fura", True),
    ("sua-foto-dentro-do-data-center", "Data center", "dentro",
     "onde a sua foto fica guardada de verdade: o prédio, o calor, a água usada para resfriar", True),
]
MOLDES = {"e-se": "E se...", "por-que": "Por que X faz Y", "dentro": "a câmera entra onde nenhuma câmera entra",
          "caso-real": "caso real que parece mentira", "como-sobrevive": "como X sobrevive a Y"}
INTERVALO = {"youtube": timedelta(hours=6), "instagram": timedelta(hours=20)}
PREFIXO = "zack:"
# Roteiro do YouTube mora à parte: `series.historia_para_produzir()` pega QUALQUER json de pautas/historias/ com
# "produzir": true, e um Short do YouTube não pode sair no Instagram por engano (nem o contrário).
ROTEIROS_YOUTUBE = series.RAIZ / "pautas" / "youtube" / "roteiros"
NOTA_MINIMA = 7.0
# O "boneco sempre igual" (regra 4 do Zack): um personagem genérico e constante, NOSSO, nunca o dele.
PERSONAGEM = ("um homem comum de camiseta cinza lisa e calça jeans, careca, rosto simples e sempre o mesmo em todos os "
              "vídeos; sem logo, sem nome na roupa")
PROIBIDO_NO_INICIO = re.compile(r"^(você sabia|voce sabia|hoje|olha só|olha so|conheça|bem-vindo)", re.I)
PEDIDO = re.compile(r"\b(comenta|comente|segue|me siga|curte|curta|link na bio|parte 2|inscreva)\b", re.I)


def problemas(r: dict) -> list[str]:
    """O que o molde exige e o previsor de nota não confere."""
    erros = []
    corpo = r.get("corpo")
    if not isinstance(corpo, list) or not 6 <= len(corpo) <= 9:
        return ["'corpo' precisa ter de 6 a 9 frases"]
    titulo = str(r.get("titulo", "")).strip()
    if not 10 <= len(titulo) <= 70:
        erros.append("'titulo' precisa ter de 10 a 70 caracteres")
    if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", titulo):
        erros.append("'titulo' não pode ter emoji")
    for f in corpo:
        n = len(str(f).split())
        if not 5 <= n <= 18:
            erros.append(f"frase '{str(f)[:40]}' tem {n} palavras (use 5 a 18)")
        if PEDIDO.search(str(f)):
            erros.append(f"frase '{str(f)[:40]}' faz pedido; o molde não pede nada")
    if PROIBIDO_NO_INICIO.search(str(corpo[0]).strip()):
        erros.append("a primeira frase tem que ser o mecanismo, não introdução")
    segunda = sum(bool(re.search(r"\b(você|voce|seu|sua|seus|suas)\b", str(f), re.I)) for f in corpo)
    if segunda < 2:
        erros.append("faltou a segunda pessoa (você, sua pele, seu corpo) em pelo menos 2 frases")
    if sum(bool(re.search(r"\d", str(f))) for f in corpo) < 2:
        erros.append("faltou número concreto em pelo menos 2 frases")
    if not any(re.match(r"^(mas|só que|so que)\b", str(f).strip(), re.I) for f in corpo[1:]):
        erros.append("falta a frase de virada começando com 'Mas' ou 'Só que'")
    tela = str(r.get("texto_tela", "")).split()
    if not 2 <= len(tela) <= 6:
        erros.append("'texto_tela' precisa ter de 2 a 6 palavras")
    if PEDIDO.search(str(r.get("legenda", ""))):
        erros.append("'legenda' não pode pedir nada")
    return erros


def escrever(slug: str, titulo_wiki: str, molde: str, angulo: str, plataforma: str = "youtube",
             llm=None, ler=None, corte: float = NOTA_MINIMA) -> dict:
    from . import segredos
    from .historias_tech import fatos as ler_fatos
    from .llm import gerar_json
    gerar = llm or gerar_json
    base = (ler or ler_fatos)(titulo_wiki)
    if len(base) < 1200:
        raise ValueError(f"artigo da Wikipédia curto demais ({len(base)} caracteres)")
    pedido = {"FATOS": base, "MOLDE": f"{molde}: {MOLDES[molde]}", "ANGULO": angulo}
    r, ultima_nota = {}, None
    for tentativa in range(3):
        r = gerar(segredos.texto("zack"), json.dumps(pedido, ensure_ascii=False))
        erros = problemas(r)
        if erros:
            pedido["critica_do_editor"] = "; ".join(erros)
            pedido["roteiro_rejeitado"] = {k: r.get(k) for k in ("titulo", "texto_tela", "corpo")}
            continue
        try:
            texto = (f"TEXTO NA TELA: {r['texto_tela']}\nABERTURA: {r['corpo'][0]}\n"
                     f"CORPO: {' '.join(r['corpo'][1:])}\nFECHAMENTO: (nenhum pedido, termina na imagem mais forte)")
            nota = gerar(segredos.texto("viral_nota"), texto)
            ultima_nota = float(nota.get("nota") or 0)
            print(f"zack {slug}: nota {ultima_nota} ({nota.get('problema')})", flush=True)
        except Exception as erro:
            print(f"previsor falhou ({erro}); sigo com o roteiro")
            break
        if ultima_nota >= corte:
            break
        pedido["critica_do_editor"] = nota.get("problema")
        pedido["roteiro_rejeitado"] = {k: r.get(k) for k in ("titulo", "texto_tela", "corpo")}
    erros = problemas(r)
    if erros:
        raise ValueError("roteiro fora do molde: " + "; ".join(erros))
    if ultima_nota is not None and ultima_nota < corte:
        raise ValueError(f"roteiro reprovado pelo previsor (nota {ultima_nota}, mínimo {corte})")
    corpo = [str(f).strip() for f in r["corpo"]]
    return {"slug": slug, "serie": slug, "episodio": 1, "opcoes": None, "produzir": True,
            "formato": "zack", "molde": molde, "plataforma": plataforma, "titulo": r["titulo"].strip(),
            "fonte": f"https://en.wikipedia.org/wiki/{titulo_wiki.replace(' ', '_')}",
            "direcao": ("MOLDE ZACK D. FILMS. A câmera entra onde nenhuma câmera entra (corte transversal, por dentro, "
                        "raio-X). Personagem fixo: " + PERSONAGEM + ". " + (r.get("direcao") or "")),
            # ganchos = só a primeira frase (o molde não tem 3 aberturas: o título faz a pergunta e a fala responde)
            "roteiro": {"texto_tela": r["texto_tela"], "ganchos": [corpo[0]], "corpo": corpo[1:], "cta": "",
                        "legenda": r.get("legenda", ""), "palavra": ""}}


def proximo_tema(estado: dict, plataforma: str) -> tuple | None:
    return next((t for t in TEMAS if f"{PREFIXO}{t[0]}" not in estado and (plataforma == "youtube" or t[4])), None)


def roteiro_youtube_pendente(estado: dict | None = None):
    """Roteiro do YouTube já escrito que ainda não virou vídeo, ou None."""
    estado = series._ler(series.ESTADO) if estado is None else estado
    for arq in sorted(ROTEIROS_YOUTUBE.glob("*.json")) if ROTEIROS_YOUTUBE.exists() else []:
        if f"produzido:{arq.stem}" not in estado:
            return arq
    return None


def precisa(estado: dict, plataforma: str = "youtube", agora: datetime | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    feitas = [datetime.fromisoformat(v["quando"]) for k, v in estado.items()
              if k.startswith(PREFIXO) and (v.get("plataforma") or "youtube") == plataforma]
    return not feitas or agora - max(feitas) >= INTERVALO[plataforma]


def gerar_se_preciso(plataforma: str = "youtube", agora: datetime | None = None):
    """Escreve o próximo roteiro do molde se já passou o intervalo. Caminho do JSON em pautas/historias/, ou None."""
    estado = series._ler(series.ESTADO)
    if not precisa(estado, plataforma, agora):
        return None
    tema = proximo_tema(estado, plataforma)
    if not tema:
        return None
    slug, titulo_wiki, molde, angulo, _ig = tema
    try:
        h = escrever(slug, titulo_wiki, molde, angulo, plataforma)
    except Exception as erro:
        print(f"não consegui escrever o zack {slug} ({erro})")
        return None
    pasta = ROTEIROS_YOUTUBE if plataforma == "youtube" else series.HISTORIAS
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{slug}.json"
    destino.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
    series.registrar(f"{PREFIXO}{slug}", destino.stem, plataforma=plataforma)
    return destino
