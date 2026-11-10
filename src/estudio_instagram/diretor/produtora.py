"""Produtora automática: um filme sob medida por pauta, em rodízio pelos 66 estilos do Lemo-Opuscar.

Por que existe: nos testes de 2026-11-04 o Davi aprovou exatamente os vídeos em que um agente Claude escreveu o
filme inteiro sob medida com uma skill de estilo forte (esquete desenhada, pixel RPG, dossiê). O motor 3D do palco,
que recombina peças genéricas, ficou "mais ou menos". Aqui o pipeline faz a parte que precisa ser confiável
(fatos, roteiro com a fórmula, voz, conferência) e entrega a parte criativa para o Claude Code com a skill do estilo.

Fluxo: pauta (repositório) -> roteiro.escrever (fórmula + 3 ganchos, só fatos) -> próximo estilo do rodízio ->
`claude -p` com a skill lemo-opuscar e um briefing fechado -> QA do MP4 (portao.qa) -> pasta pronta para aprovação.

SEGURANÇA: o agente roda sem pedir permissão. Por isso ele NUNCA recebe texto da internet (README etc.): recebe só
as frases do roteiro (já geradas e validadas aqui como JSON) e o briefing escrito neste arquivo. Assim um README
malicioso não consegue dar instruções ao agente.

    python -m src.estudio_instagram.diretor.produtora --repo dono/nome          (uma pauta)
    python -m src.estudio_instagram.diretor.produtora --auto                    (pega o assunto quente do dia)
    python -m src.estudio_instagram.diretor.produtora --repo dono/nome --estilo ukiyoe
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import portao, roteiro
from .. import segredos

RAIZ = Path(__file__).resolve().parents[3]
BIBLIOTECA = Path(os.environ.get("LEMO_OPUSCAR", Path.home() / "lemo-opuscar"))
SAIDA = RAIZ / "videos_produzidos"
ESTADO = RAIZ / "pautas" / "produtora.json"
EXTRAS = {"hand-drawn-cartoon": "desenho animado de livro ilustrado, traço à mão, cores chapadas (skill hand-drawn-cartoon)",
          "cartoon-3d-short": "personagens 2D de desenho num mundo 3D colorido, câmera deslizando (skill cartoon-3d-short)",
          "esquete": "esquete em diálogo entre o Davi e o robô (skill hand-drawn-cartoon), duas vozes",
          "3d-toy-character": "mascote 3D de vinil com luz de estúdio (skill 3d-toy-character)",
          "kinetic-typography": "tipografia cinética: o texto é a animação (skill kinetic-typography)",
          "data-story-charts": "história contada por gráfico animado com números reais (skill data-story-charts)"}


def estilos() -> list[dict]:
    """Os 66 estilos da biblioteca (style.json) + estilos extras de outras skills."""
    lista = []
    for arq in sorted((BIBLIOTECA / "styles").glob("*/style.json")):
        if arq.parent.name.startswith("_"):  # _template é o molde para criar estilo próprio, não um estilo
            continue
        j = json.loads(arq.read_text(encoding="utf-8"))
        lista.append({"slug": arq.parent.name, "nome": j.get("en", arq.parent.name), "categoria": j.get("category_en", ""),
                      "usos": j.get("uses", []),
                      "num": j.get("num")})
    # intercala os extras (esquete etc.) a cada 4 estilos, em vez de deixá-los para o fim do rodízio de 66 dias;
    # e alterna as categorias da biblioteca para dois dias seguidos não saírem parecidos
    por_cat = {}
    for e in lista:
        por_cat.setdefault(e["categoria"], []).append(e)
    alternada = []
    while any(por_cat.values()):
        for cat in list(por_cat):
            if por_cat[cat]:
                alternada.append(por_cat[cat].pop(0))
    extras = [{"slug": s, "nome": d, "categoria": "extra"} for s, d in EXTRAS.items()]
    final = []
    for i, e in enumerate(alternada):
        if i % 4 == 1 and extras:
            final.append(extras.pop(0))
        final.append(e)
    return final + extras


def _estado() -> dict:
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {"estilos_usados": [], "repos_usados": [], "producoes": []}


COMBINA = """Você é diretor de arte de Reels. Escolha os 4 estilos de filme que MAIS combinam com este assunto, pensando
em quem assiste (jogo de videogame pede estilo de game, neon, ação ou 3D; finanças pede gráfico, dossiê ou editorial;
ferramenta de IA pede tecnologia, terminal, brinquedo 3D ou esquete). Nunca escolha um estilo que brigue com o clima.
Responda só JSON: {"estilos": ["slug1", "slug2", "slug3", "slug4"]} usando os slugs da lista."""


# Davi, 06/11: "só me siga, em vez de ficar comente também... pra não ser sempre a mesma coisa". O fechamento roda
# entre 4 pedidos; a legenda continua com o "Comenta X" (o link sai pelo direct em todos). cta_tipo vai pra fila
# para o analista comparar qual traz mais seguidor.
FECHAMENTOS = [
    ("comenta", "Me segue e comenta {p} que eu te mando o link. Todo dia tem uma IA nova aqui."),
    ("segue", "Me segue que amanhã tem outra dessas. Todo dia uma IA nova aqui."),
    ("comenta", "Me segue e comenta {p} que eu te mando o link. Todo dia tem uma IA nova aqui."),
    ("salva", "Salva esse vídeo pra testar depois. E me segue pra não perder a próxima."),
    ("comenta", "Me segue e comenta {p} que eu te mando o link. Todo dia tem uma IA nova aqui."),
    ("manda", "Manda esse vídeo pra aquele amigo que precisa ver isso. E me segue pra mais."),
]


def fechamento(n: int, palavra: str) -> tuple[str, str]:
    tipo, texto = FECHAMENTOS[n % len(FECHAMENTOS)]
    return tipo, texto.format(p=palavra)


def estilos_fracos(desempenho: dict | None = None, corte: float = 0.2) -> set[str]:
    """Estilos que já foram postados e ficaram muito abaixo do perfil (mediana de views abaixo de 20% da mediana
    geral). Dossiê fez 130 views com o perfil na casa de 1.200: não vale repetir até os números mudarem."""
    if desempenho is None:
        try:
            desempenho = json.loads((RAIZ / "pautas" / "desempenho.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return set()
    geral = (desempenho.get("geral") or {}).get("views_medianas") or 0
    return {nome.removeprefix("produtora-") for nome, d in (desempenho.get("por_estilo") or {}).items()
            if nome.startswith("produtora-") and geral and d.get("views_medianas", geral) < corte * geral}


def estilo_para(assunto: str, estado: dict, todos: list[dict], llm=None, fracos: set[str] | None = None) -> dict:
    """Davi, 04/11: estilo de arquivo/dossiê num vídeo de GTA ficou ruim. O rodízio cego trocou por: estilos que
    combinam com o assunto, em ordem; sai o que mais combina e não foi usado nos últimos 8 vídeos."""
    from ..llm import gerar_json
    lista = "\n".join(f"{e['slug']}: {e['nome']} ({e['categoria']}; {', '.join(e.get('usos', []))})" for e in todos)
    try:
        r = (llm or gerar_json)(COMBINA, f"ASSUNTO: {assunto}\n\nESTILOS:\n{lista}")
        bons = [e for slug in r.get("estilos", []) for e in todos if e["slug"] == slug]
    except Exception as erro:
        print(f"não consegui casar estilo com o assunto ({erro}); sigo o rodízio")
        bons = []
    fracos = estilos_fracos() if fracos is None else fracos
    bons = [e for e in bons if e["slug"] not in fracos] or bons
    if not bons:
        return proximo_estilo(estado, todos)
    recentes = estado.get("estilos_usados", [])[-8:]
    return next((e for e in bons if e["slug"] not in recentes), bons[0])  # o que mais combina, se não saiu há pouco


def proximo_estilo(estado: dict, todos: list[dict]) -> dict:
    """Rodízio: só repete um estilo depois de usar todos; nunca o mesmo duas vezes seguidas."""
    usados = estado.get("estilos_usados", [])
    livres = [e for e in todos if e["slug"] not in usados]
    if not livres:
        usados.clear()
        livres = [e for e in todos if not estado.get("producoes") or e["slug"] != estado["producoes"][-1]["estilo"]]
    return livres[0]


def briefing(frases: list[str], estilo: dict, pasta: Path, palavra: str, extra: str = "", tela: str = "",
             historia: bool = False) -> str:
    """O que o Claude Code recebe. Só texto nosso + as frases do roteiro (sem nada vindo da internet)."""
    lista = json.dumps(frases, ensure_ascii=False, indent=1)
    if estilo["slug"] == "esquete":
        como = ("FORMATO: esquete cômica em diálogo entre o criador \"Davi\" (jovem, moletom) e o robô assistente (mascote do perfil: "
                "corpo arredondado coral, cabeça creme que é uma tela escura com olhos verde-menta brilhando, antena com luz vermelha). "
                "Use a skill hand-drawn-cartoon (~/.agents/skills/hand-drawn-cartoon/SKILL.md). Reescreva as frases como diálogo curto e "
                "engraçado entre os dois SEM mudar os fatos nem a última frase. Duas vozes: Davi = Puck, robô = Orus.")
    elif estilo["slug"] in EXTRAS:
        como = (f"ESTILO: {EXTRAS[estilo['slug']]}. Leia e siga ~/.agents/skills/{estilo['slug']}/SKILL.md (HyperFrames). "
                + ("" if historia else "Personagem, quando houver, é o robô do perfil: corpo arredondado coral, cabeça creme que é "
                   "uma tela escura com olhos verde-menta brilhando, antena com luz vermelha."))
    else:
        como = (f"ESTILO: \"{estilo['nome']}\" da biblioteca Lemo-Opuscar (slug {estilo['slug']}). Use a skill lemo-opuscar "
                f"(Skill tool) ou leia direto {BIBLIOTECA}/AGENTS.md, {BIBLIOTECA}/DIRECTOR.md e {BIBLIOTECA}/styles/{estilo['slug']}/STYLE.md. "
                "A biblioteca já está instalada nesse caminho (não clone de novo). Siga o STYLE.md à risca: é ele que dá a qualidade.")
    personagem = ("- Personagens: os da HISTÓRIA (ver DIREÇÃO abaixo), com o MESMO desenho em todas as cenas (cabelo, roupa, "
                  "cores fixas): é uma série, o público tem que reconhecer o personagem no próximo episódio." if historia else
                  "- Personagem: se o estilo tiver personagem, use o robô do perfil descrito acima, adaptado ao estilo.")
    if historia:
        extra = extra + f"""
QUALIDADE MÁXIMA (Davi: "quero que esses vídeos sejam virais"). Este vídeo concorre com séries de 1 a 3 milhões de views:
- Antes de animar, escreva {pasta}/storyboard.md: cada frase vira uma cena com enquadramento (plano geral, médio,
  close), movimento de câmera e a AÇÃO do personagem. Varie: nunca duas cenas seguidas com o mesmo enquadramento.
- Atuação: o personagem pisca, respira, reage com o rosto e o corpo (antecipação, squash and stretch, olhar).
  Nada de boneco parado com a boca mexendo.
- Ritmo: corte ou movimento novo a cada 1 a 2 s; impacto visual nas viradas (zoom rápido, tremida, flash, carimbo).
- Som: efeitos sonoros nas ações (passos, vibração, chave, porta, clarão) e trilha baixa que cresce na tensão.
- Confira: gere a folha de contato, olhe cena por cena e REFAÇA qualquer cena feia, vazia ou parada antes do final.
"""
    fecho = ("- Fechamento: a última frase pede o follow. Mostre as opções de voto (se houver) como dois botões grandes na tela "
             "e o botão SEGUIR @ursulino.ia pulsando no fim." if historia else
             f"- Fechamento: caixa de comentário digitando {palavra} + botão seguir @ursulino.ia.")
    return f"""Você é a produtora automática do perfil brasileiro @ursulino.ia (IA para quem cria conteúdo, programa ou está começando).
Faça UM Reel vertical pronto, sem perguntar nada (ninguém vai responder). Faça TUDO você mesmo, em primeiro plano,
até o final.mp4 existir: NÃO delegue para sub-agentes e NÃO deixe render rodando em segundo plano, porque este
processo termina quando você der a resposta final. Não publique nada, não faça git commit/push,
não mexa em nada fora de {pasta} (exceto ler a biblioteca e rodar os comandos indicados).

{como}

ROTEIRO (aprovado, frase por frase; não invente fatos nem números; pode encurtar palavras para caber no tempo):
{lista}

REGRAS DO VÍDEO (estudo de 108 Reels virais):
- GANCHO (0 a 1,5 s, decide se o Reel viaja): o primeiro quadro já mostra o fato mais forte em movimento, nunca logo,
  título ou introdução. Texto grande na tela, legível sem som: "{tela or frases[0]}". Ele some quando a 2ª frase começa.
- 1080x1920, 30 fps, com áudio, duração igual à da narração (25 a 60 s). Cada frase é UMA cena com uma ação visual concreta ligada ao que a frase diz;
  algo novo na tela a cada 1 a 3 s; nunca um slide de texto parado.
- Um estado na tela que avança (contador, barra, "prova 3/7", nível) do começo ao fim.
- Legenda curta sincronizada com a voz por volta de y=1300; nada importante nos 560 px de baixo nem colado na borda direita.
{personagem}
{fecho}
- Sem emoji. Textos na tela em português do Brasil.
{extra}
RENDER: esta máquina não tem GPU. O WebGL roda por software (LEMO_ANGLE=swiftshader já está definido): é lento, mas
funciona; não desista do 3D. Capture sempre em 1080x1920 (vertical): ajuste o tamanho da página/viewport do projeto.

VOZ: grave as frases (lista JSON) em {pasta}/frases.json e rode da raiz do repositório:
  cd {RAIZ} && {sys.executable} -m src.estudio_instagram.diretor.narracao {pasta}/frases.json {pasta}/ Orus
Isso gera voz.wav e falas.json (início t e duração d de cada frase, tempo aproximado de cada palavra). Tudo na tela segue esses tempos.
Voz bem audível; música (se houver) bem baixa por baixo.

ENTREGA em {pasta}: final.mp4, poster.jpg, folha.jpg (12 quadros: ffmpeg -i final.mp4 -vf "fps=12/<duração>,scale=270:-1,tile=6x2" -frames:v 1 folha.jpg)
e roteiro.md (frases + o que cada cena mostra). Antes de terminar, olhe a folha.jpg e corrija o que estiver parado, ilegível,
cortado ou com cara de slide (pelo menos uma rodada). Confira com ffprobe. Apague renders temporários (o disco é pequeno).
Última mensagem: até 80 palavras dizendo o que cada cena mostra e o que ficou fraco."""


# Ferramentas liberadas para o agente: só leitura/escrita de arquivos e os comandos de vídeo que o fluxo usa.
# Qualquer outra coisa (rede arbitrária, git, apagar fora da pasta...) não é permitida e falha sem travar.
FERRAMENTAS = ["Read", "Write", "Edit", "Glob", "Grep", "Skill",
               "Bash(ffmpeg:*)", "Bash(ffprobe:*)", "Bash(node:*)", "Bash(npx hyperframes:*)", "Bash(npm run:*)",
               f"Bash({sys.executable} -m src.estudio_instagram.diretor.narracao:*)", f"Bash(cd {RAIZ} && {sys.executable} -m src.estudio_instagram.diretor.narracao:*)", "Bash(cd:*)", "Bash(ls:*)",
               "Bash(mkdir:*)", "Bash(cp:*)", "Bash(mv:*)", "Bash(rm -rf ./tmp:*)", "Bash(python3:*)", "Bash(sh:*)"]


def rodar_agente(prompt: str, pasta: Path, timeout_s: int = 4500, modelo: str | None = None) -> str:
    """Claude Code sem tela, com permissões RESTRITAS (lista FERRAMENTAS) e limitado à pasta + biblioteca + repositório.

    Não usa --dangerously-skip-permissions: o modo automático do Claude Code recusou rodar um agente sem permissões,
    e com razão. Ver a nota de segurança no topo do arquivo.
    """
    # Sem sub-agentes nem segundo plano: no 1º teste (04/11) o agente delegou o render a um sub-agente em segundo
    # plano e encerrou; o modo -p mata essas tarefas 10 min depois e o vídeo nunca saiu.
    cmd = ["claude", "-p", "--permission-mode", "acceptEdits", "--allowedTools", *FERRAMENTAS,
           "--disallowedTools", "Agent", "Task",
           "--add-dir", str(pasta), "--add-dir", str(BIBLIOTECA), "--add-dir", str(RAIZ),
           "--add-dir", str(Path.home() / ".agents" / "skills"), *(["--model", modelo] if modelo else []), "--", prompt]
    # LEMO_ANGLE=swiftshader: sem GPU (PC do Davi e GitHub Actions), o Chrome perde o contexto WebGL e os estilos 3D saem
    # em branco; forçando o SwiftShader o three.js renderiza por software (mais lento, mas funciona). Teste de 04/11.
    env = {**os.environ, "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0", "LEMO_ANGLE": os.environ.get("LEMO_ANGLE", "swiftshader")}
    r = subprocess.run(cmd, cwd=pasta, capture_output=True, text=True, timeout=timeout_s, env=env)
    (pasta / "agente.log").write_text((r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or "")[-4000:], encoding="utf-8")
    return r.stdout


VENDAS = RAIZ / "pautas" / "vendas"
REPO_VENDA = "venda/pack-estudio"  # rótulo interno (não é repositório)
PALAVRA_EM_ALTA = "MAQUINA"  # o respondedor manda o checkout da Máquina de Reels (aceita MÁQUINA também)
PALAVRA_VENDA = "ESTUDIO"  # o respondedor manda o link do pack para quem comenta essa palavra
EXTRA_VENDA = segredos.texto("extra_venda")  # texto no repositório privado (ver segredos.py)


EXTRA_EM_ALTA = segredos.texto("extra_em_alta")  # texto no repositório privado (ver segredos.py)
AVISO_EM_ALTA = ("- Assunto do momento: desenho 100% original. Não copie logo, personagem, capa nem arte oficial de jogo, "
                 "filme, marca ou pessoa real; evoque o tema com elementos genéricos (ex.: um carro esportivo, uma cidade "
                 "de praia neon), nunca a imagem oficial.\n- Última cena antes do fechamento: \"Esse vídeo eu fiz com IA\" "
                 "aparecendo como um carimbo/revelação do bastidor.\n")


def fatos_venda(pasta: Path = VENDAS) -> str:
    """Fatos do produto tirados dos roteiros de venda que o Davi já aprovou (texto nosso, não da internet)."""
    linhas = []
    for arq in sorted(pasta.glob("*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        linhas += [c["narracao"] for c in d.get("cenas_roteiro", [])]
        linhas.append(re.sub(r"#\S+|Comenta.*", "", d.get("legenda", "")).strip())
    return "\n".join(f"- {l}" for l in dict.fromkeys(l for l in linhas if l))


def produzir(repo: str, estilo_slug: str | None = None, gancho: int = 0, venda: bool = False,
             momento: dict | None = None, historia: dict | None = None, fatos: str | None = None,
             palavra: str | None = None, promessa: str | None = None) -> dict:
    from .fazer import fatos_do_repo
    estado = _estado()
    todos = estilos()
    assunto = (f"{momento['tema']}: {momento.get('angulo', '')}" if momento else
               "vídeo de venda: animação feita com IA, sem editor" if venda else f"ferramenta de IA do GitHub {repo}")
    estilo = next((e for e in todos if e["slug"] == estilo_slug), None) if estilo_slug else estilo_para(assunto, estado, todos)
    if estilo is None:
        raise SystemExit(f"estilo {estilo_slug} não existe; opções: {', '.join(e['slug'] for e in todos)}")
    extra_video = ""
    if historia:
        # Davi, 06/11: histórias animadas pra viralizar e captar seguidor (séries "você decide", história real
        # bizarra). O roteiro vem pronto (pautas/historias/*.json) e fecha pedindo o follow ("quer a parte 2?").
        repo = f"historia/{historia['slug']}"
        rot = json.loads(json.dumps(historia["roteiro"]))
        rot["cta_tipo"] = "segue"
        extra_video = historia.get("direcao", "")
    elif momento:
        repo = f"em-alta/{re.sub(r'[^a-z0-9]+', '-', momento['chave'].lower()).strip('-')}"
        rot = roteiro.escrever(momento["fatos"], extra=EXTRA_EM_ALTA.replace("__ANGULO__", momento.get("angulo", "")))
        # Davi, 05/11: assunto do momento é vídeo de venda. Atrai quem busca o tema e fecha mostrando a máquina.
        rot["palavra"] = PALAVRA_EM_ALTA
        rot["cta"] = ("Essa animação eu fiz sem editor, com uma máquina de IA. Quer saber como? "
                      "Me segue e comenta MÁQUINA que eu te mando.")
        extra_video = AVISO_EM_ALTA
    elif venda:
        repo = REPO_VENDA
        rot = roteiro.escrever(fatos_venda(), extra=EXTRA_VENDA)
        rot["palavra"] = PALAVRA_VENDA
        rot["cta"] = f"Me segue e comenta {PALAVRA_VENDA} que eu te mando o link."
    else:
        # teste A/B (04/11): no perfil, 45-60 s teve mediana 570 views contra 313 dos curtos (n=9 x 23). Alterna para
        # medir com os vídeos novos; o analista separa por duração (por_formato).
        longo = len(estado.get("producoes", [])) % 2 == 1
        # `promessa`: vídeo de utilidade prática (ver utilidade.py). A ferramenta vira o meio; a promessa, escrita
        # pra quem nunca programou, vira o assunto. Medido 10/11: é o que separa 307 mil views de 3 mil.
        extra_roteiro = ""
        if promessa:
            from .. import utilidade
            extra_roteiro = utilidade.extra(promessa)
        rot = roteiro.escrever(fatos or fatos_do_repo(repo), longo=longo, extra=extra_roteiro)
        rot["versao"] = "longa" if longo else "curta"
        rot["utilidade"] = bool(promessa)
        if palavra:  # site/ferramenta (Davi, 06/11: Gradium): a palavra tem resposta fixa em bot_respostas.json
            rot["palavra"] = palavra
        rot["cta_tipo"], rot["cta"] = fechamento(len(estado.get("producoes", [])), rot["palavra"])
    rot = roteiro.prever(rot, gancho)
    frases = roteiro.frases(rot, gancho)
    nome = f"{datetime.now():%Y-%m-%d-%H%M}-{re.sub(r'[^a-z0-9]+', '-', repo.split('/')[-1].lower())}-{estilo['slug']}"
    pasta = SAIDA / nome
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "pauta.json").write_text(json.dumps({"repo": repo, "estilo": estilo, "roteiro": rot, "gancho_usado": gancho},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    (pasta / "legenda.txt").write_text(rot.get("legenda", ""), encoding="utf-8")
    print(f"produzindo {repo} no estilo {estilo['nome']} -> {pasta}", flush=True)
    resposta = rodar_agente(briefing(frases, estilo, pasta, rot["palavra"], extra_video, rot.get("texto_tela", ""),
                                     historia=bool(historia)), pasta,
                            timeout_s=7200 if historia else 4500, modelo="opus" if historia else None)
    final = pasta / "final.mp4"
    res = {"pasta": str(pasta), "repo": repo, "estilo": estilo["slug"], "palavra": rot["palavra"], "ok": False, "venda": venda,
           "em_alta": bool(momento), "historia": bool(historia)}
    if final.exists():
        dur = portao._ffprobe_duracao(final)
        q = portao.qa(final, dur)  # duração conferida pelo próprio arquivo; o QA olha congelado, preto, volume e miolo vazio
        largura = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                  "-of", "csv=p=0", str(final)], capture_output=True, text=True).stdout.strip()
        largura = ",".join(x for x in largura.replace("\n", ",").split(",") if x)[:9]  # o ffprobe pode pôr vírgula no fim
        problemas = q["problemas"] + ([] if largura == "1080,1920" else [f"resolução {largura} (esperado 1080,1920)"]) + \
            ([] if 20 <= dur <= 75 else [f"duração {dur:.1f}s fora de 20-75 s"])
        res.update({"ok": not problemas, "duracao": round(dur, 1), "problemas": problemas, "resumo_agente": resposta[-800:]})
    else:
        res["problemas"] = ["o agente não entregou final.mp4 (ver agente.log)"]
    (pasta / "producao.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    estado.setdefault("estilos_usados", []).append(estilo["slug"])
    if not venda and not momento and not historia:
        estado.setdefault("repos_usados", []).append(repo)
    estado.setdefault("producoes", []).append({"quando": datetime.now().isoformat(timespec="minutes"), **{k: res[k] for k in ("repo", "estilo", "ok", "pasta", "em_alta")}})
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


FILA = RAIZ / "pautas" / "viral" / "fila"
FILA_VENDA = RAIZ / "pautas" / "viral" / "fila_venda"


BANCO_MAXIMO = 4  # 4 rodadas por dia (06/11); vídeos comuns esperando no banco (3 rodadas por dia); mais que isso envelhece e perde o assunto


def banco_cheio() -> bool:
    from .. import maestro
    return len(maestro.disponiveis(maestro._ler().get("fila_usadas", []))) >= max(BANCO_MAXIMO, maestro.banco_alvo())


EM_ALTA_POR_DIA = 1  # 05/11: na 1ª madrugada saíram 4 de esporte/celebridade seguidos; o perfil perde o nicho


def cabe_em_alta(agora: datetime | None = None) -> bool:
    """No máximo EM_ALTA_POR_DIA assunto do momento por 20 h; o resto são vídeos do nicho (ferramentas de IA)."""
    agora = agora or datetime.now()
    recentes = [x for x in _estado().get("producoes", []) if x.get("em_alta")
                and x.get("ok") and agora - datetime.fromisoformat(x["quando"]) < timedelta(hours=20)]
    return len(recentes) < EM_ALTA_POR_DIA


def precisa_venda() -> bool:
    """Sem vídeo de venda novo esperando no banco, a próxima produção automática é de venda (ter/sex 08:00 usam)."""
    from .. import maestro
    return maestro.proxima_da_fila(maestro._ler().get("fila_usadas", []), FILA_VENDA) is None


def para_fila(res: dict) -> Path:
    """Sobe o MP4 aprovado para a release de mídia e põe uma pauta de VÍDEO PRONTO na fila do maestro.

    O maestro publica na rodada do banco de vídeos (dentro da grade); o pipeline só baixa e posta (_executar_pronto).
    """
    from .. import hospedagem
    pasta = Path(res["pasta"])
    pauta_prod = json.loads((pasta / "pauta.json").read_text(encoding="utf-8"))
    rot = pauta_prod["roteiro"]
    url = hospedagem.publicar(pasta / "final.mp4", f"produtora-{pasta.name}.mp4")
    legenda = (rot.get("legenda") or "").strip()
    # a legenda vem do LLM com a palavra que ELE inventou; em venda/assunto do momento a palavra é trocada depois
    # (ESTUDIO). Sem isto saiu "Comenta GAME" na legenda e "Comenta ESTUDIO" no vídeo (05/11).
    # "comenta" cobre só uma conjugação -- o LLM também escreve "Comente" (06/11), passava direto pelo regex e
    # sobravam 2 chamadas pra ação na mesma legenda ("Comente MAQUINA" + "Comenta ESTUDIO" coladas no fim).
    if not res.get("historia"):  # história: o voto (Comenta A ou B) é do roteiro e não tem link pra mandar
        legenda = re.sub(r"(?i)\bcoment[ae]\s+[A-ZÀ-Ú]{3,}\b", f"Comenta {rot['palavra']}", legenda)
        # o LLM às vezes escreve 2 frases de CTA (uma por linha, cada uma com sua própria palavra errada); a troca
        # acima deixa as duas com a mesma palavra certa, mas repetidas -- fica só a primeira (06/11).
        vista, linhas = False, []
        for linha in legenda.split("\n"):
            eh_cta = re.search(rf"(?i)\bcomenta\s+{re.escape(rot['palavra'])}\b", linha)
            if eh_cta and vista:
                continue
            vista = vista or bool(eh_cta)
            linhas.append(linha)
        legenda = "\n".join(linhas)
        if rot["palavra"] not in legenda:
            legenda += f"\nMe segue e comenta {rot['palavra']} que eu te mando o link no direct."
    venda = res.get("venda", False)
    pauta = {"titulo": f"{res['repo'].split('/')[-1]}: produtora ({res['estilo']})", "formato": "pronto",
             "video_pronto_url": url, "palavra_chave": rot["palavra"], "legenda": legenda,
             **({"capa": rot["texto_tela"]} if rot.get("texto_tela") else {}),
             **({"cta_tipo": rot["cta_tipo"]} if rot.get("cta_tipo") else {}),
             **({"previsao": rot["previsao"].get("nota")} if rot.get("previsao") else {}),
             "itens": [] if venda or res.get("em_alta") or res["repo"].startswith("site/") else [{"repo": res["repo"]}], "estilo": res["estilo"], "gancho": "A",
             "ganchos_alternativos": [], **({"tipo": "venda"} if venda else {}),
             **({"tipo": "em-alta"} if res.get("em_alta") else {})}
    if res.get("historia"):
        pauta["itens"], pauta["tipo"] = [], "historia"
    fila = FILA_VENDA if venda else FILA
    fila.mkdir(parents=True, exist_ok=True)
    marca = "em-alta" if res.get("em_alta") else ("historia" if res.get("historia") else "produtora")
    destino = fila / f"{datetime.now():%Y-%m-%d-%H%M}-{marca}-{pasta.name.split('-', 4)[-1]}.json"
    destino.write_text(json.dumps(pauta, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino


def pauta_automatica() -> str:
    from .. import assunto_quente
    usados = set(_estado().get("repos_usados", []))
    for repo in assunto_quente.do_dia():
        if repo not in usados:
            return repo
    raise SystemExit("nenhum assunto quente novo hoje")


def main():
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
    p = argparse.ArgumentParser()
    p.add_argument("--repo")
    p.add_argument("--auto", action="store_true")
    p.add_argument("--estilo")
    p.add_argument("--gancho", type=int, default=0)
    p.add_argument("--fatos", help="arquivo de texto com os fatos de um site/ferramenta (sem repositório); use com --assunto")
    p.add_argument("--assunto", help="nome curto do site, ex.: gradium")
    p.add_argument("--palavra", help="palavra do comentário que manda o link (precisa estar em pautas/bot_respostas.json)")
    p.add_argument("--historia", help="roteiro pronto de história (pautas/historias/x.json); precisa de --estilo")
    p.add_argument("--wiki", help="título de artigo da Wikipédia em inglês: escreve a história desse assunto e produz "
                                  "(formato @marcondes.ai: fatos de uma empresa/figura gigante). Ex.: --wiki 'xAI' --estilo dark-keynote")
    p.add_argument("--listar", action="store_true")
    p.add_argument("--em-alta", action="store_true", help="vídeo do assunto do momento (no --auto vem primeiro)")
    p.add_argument("--venda", action="store_true", help="vídeo de venda do Pack Estúdio (com --auto, sai sozinho quando falta)")
    p.add_argument("--fila", action="store_true", help="se o vídeo passar na conferência, sobe e põe na fila do maestro")
    p.add_argument("--promessa", help="ângulo de utilidade prática: o que QUEM ASSISTE ganha, em linguagem de leigo "
                                      "(ver utilidade.py). Use com --repo. Ex.: 'tirar o fundo de qualquer foto de graça'")
    a = p.parse_args()
    a.repo_utilidade = a.utilidade_slug = None  # preenchidos pelo rodízio automático de utilidade (ver abaixo)
    if a.listar:
        for e in estilos():
            print(f"{e['slug']:24} {e['nome']}  ({e['categoria']})")
        return
    if not shutil.which("claude"):
        raise SystemExit("precisa do Claude Code instalado (comando claude)")
    # Ordem do automático (Davi, 04/11): assunto do momento primeiro (rápido, antes de esfriar); sem assunto bom,
    # repõe a venda; com o banco já cheio, não produz (vídeo guardado demais perde o tema do dia).
    if a.wiki:
        # Davi, 10/11, pedindo um vídeo igual ao do @marcondes.ai (reel Dfj6T7CR9WW): fato de empresa/figura gigante
        # em 3D escuro. O roteirista de história real já faz o texto; aqui só escolhemos o assunto e o estilo na mão.
        import re as _re
        from .. import historias_tech, series
        slug = _re.sub(r"[^a-z0-9]+", "-", a.wiki.lower()).strip("-")
        historia = historias_tech.escrever(slug, a.wiki, 0)
        destino = series.HISTORIAS / f"{slug}.json"
        destino.write_text(json.dumps(historia, ensure_ascii=False, indent=1), encoding="utf-8")
        series.registrar(f"tech:{slug}", destino.stem)
        a.historia = str(destino)
    if a.auto and not a.repo and not a.venda and not a.wiki:
        # série "você decide" (06/11): episódio com voto vencido vem antes de tudo (a parte 2 foi prometida "amanhã")
        from .. import series
        from .. import historias_cotidiano, historias_tech
        # cotidiano antes de tech (10/11): é a frente de alcance (mediana medida 295 mil contra 2,7 mil do nicho,
        # ver segredos/estudos/2026-11-10/). Cada um tem o seu intervalo de 20 h, então na prática alternam.
        proximo = (series.preparar_proximo() or series.historia_para_produzir()
                   or historias_cotidiano.gerar_se_preciso() or historias_tech.gerar_se_preciso())
        if proximo:
            a.historia = str(proximo)
        else:
            # sem história na vez: o vídeo de ferramenta sai com promessa de utilidade (10/11), que é o que
            # separa 307 mil views de 3 mil nas contas medidas. Sem utilidade nova na fila, segue o normal.
            # Guardado à parte de `a.repo` de propósito: o limite de banco cheio continua valendo para ele.
            from .. import utilidade
            estado_u = series._ler(series.ESTADO)
            escolha = utilidade.proxima(estado_u) if utilidade.precisa(estado_u) else None
            if escolha:
                a.utilidade_slug, a.repo_utilidade, a.promessa = escolha
    if a.fatos:
        res = produzir(f"site/{a.assunto}", a.estilo, fatos=Path(a.fatos).read_text(encoding="utf-8"), palavra=a.palavra)
        if a.fila and res.get("ok"):
            res["fila"] = str(para_fila(res).relative_to(RAIZ))
        print(json.dumps(res, ensure_ascii=False, indent=1))
        raise SystemExit(0 if res.get("ok") else 1)
    if a.historia:
        historia = json.loads(Path(a.historia).read_text(encoding="utf-8"))
        res = produzir(f"historia/{historia['slug']}", a.estilo or historia.get("estilo"), historia=historia)
        if a.fila and res.get("ok"):
            res["fila"] = str(para_fila(res).relative_to(RAIZ))
        if res.get("ok"):
            from .. import series
            series.marcar_produzida(Path(a.historia).stem)
        print(json.dumps(res, ensure_ascii=False, indent=1))
        raise SystemExit(0 if res.get("ok") else 1)
    from .. import em_alta
    momento = em_alta.do_momento() if (a.em_alta or (a.auto and not a.repo and not a.venda and cabe_em_alta())) else None
    if a.em_alta and not momento:
        raise SystemExit("nenhum assunto do momento rende vídeo agora")
    venda = not momento and (a.venda or (a.auto and not a.repo and precisa_venda()))
    if a.auto and not (momento or venda or a.repo) and banco_cheio():
        print(f"banco já tem {BANCO_MAXIMO} vídeos esperando e nenhum assunto do momento: não produzo agora")
        return
    repo = REPO_VENDA if venda else (a.repo or ("em-alta" if momento else None) or a.repo_utilidade
                                     or (pauta_automatica() if a.auto else None))
    if not repo:
        raise SystemExit("use --repo dono/nome, --auto, --em-alta ou --venda")
    if momento:
        print(f"assunto do momento: {momento['tema']} ({momento['angulo']})", flush=True)
    promessa = a.promessa if repo == a.repo_utilidade or (a.promessa and a.repo) else None
    if promessa:
        print(f"ângulo de utilidade: {promessa}", flush=True)
    res = produzir(repo, a.estilo, a.gancho, venda=venda, momento=momento, promessa=promessa)
    if momento and res.get("ok"):
        em_alta.registrar(momento["chave"])
    if a.utilidade_slug and res.get("ok"):
        from .. import utilidade
        utilidade.registrar(a.utilidade_slug)
    if a.fila and res.get("ok"):
        res["fila"] = str(para_fila(res).relative_to(RAIZ))
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if not res.get("ok"):
        raise SystemExit(1)  # workflow fica vermelho: vídeo que não passou na conferência não pode parecer sucesso


if __name__ == "__main__":
    main()
