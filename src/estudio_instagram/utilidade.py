"""Vídeo de utilidade prática: a ferramenta é o meio, a promessa é da vida de quem assiste.

Medido em 2026-11-10 (`segredos/estudos/2026-11-10/`), com controle dentro da mesma conta, duas vezes:

- @guics.dev (mesmo motor que o nosso, Claude + 3D, vendendo o mesmo tipo de método, 2.927 seguidores):
  truque de busca no Google para achar vaga remota = 307 mil views; "transformei o Claude no meu estúdio 3D" = 2.974.
- @eupauloleme (17,2 mil seguidores): utilidade doméstica em 3D = 4,9 milhões e 1,6 milhão; dica do nicho dele = 538.

Mesma produção, até 1000x de diferença, só trocando o assunto. Aqui a gente continua falando de ferramenta de
verdade (os fatos saem do README, como sempre — RN-1 intacta), mas cada uma entra com uma PROMESSA escrita para
quem nunca programou. O resto do caminho é o mesmo dos outros vídeos de ferramenta.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import series

# (slug, repositório, promessa de apelo amplo). A promessa é o que a pessoa ganha na vida dela, não o que a
# ferramenta faz. Ordem = ordem de uso.
UTILIDADES = [
    ("achar-vaga-remota", "nilsherzig/LLocalSearch",
     "achar vaga de emprego remota que não aparece na busca normal"),
    ("transcrever-audio-longo", "openai/whisper",
     "transcrever uma hora de áudio ou aula em texto, de graça, no seu computador"),
    ("tirar-fundo-de-foto", "danielgatis/rembg",
     "tirar o fundo de qualquer foto sem pagar aplicativo"),
    ("resumir-pdf-gigante", "Mintplex-Labs/anything-llm",
     "jogar um PDF de 200 páginas e perguntar o que você quer saber, em português"),
    ("legenda-em-video", "m1guelpf/auto-subtitle",
     "pôr legenda em qualquer vídeo do celular sem editor"),
    ("melhorar-foto-antiga", "TencentARC/GFPGAN",
     "recuperar foto antiga de família que ficou borrada ou riscada"),
    ("organizar-conta-do-mes", "actualbudget/actual",
     "enxergar para onde o seu salário foi no mês, sem planilha e sem mensalidade"),
    ("assistente-no-computador", "open-webui/open-webui",
     "ter um assistente tipo Jarvis rodando no seu próprio computador, de graça"),
    # 15/11: banco ampliado com desejos de público amplo (dinheiro, tempo, de graça, celular, família)
    ("chatgpt-sem-internet", "ollama/ollama",
     "ter um ChatGPT que roda no seu computador, sem internet e sem pagar mensalidade"),
    ("backup-de-fotos-gratis", "immich-app/immich",
     "guardar todas as fotos do seu celular sem pagar armazenamento do Google"),
    ("editar-pdf-gratis", "Stirling-Tools/Stirling-PDF",
     "juntar, dividir, assinar e comprimir PDF sem pagar nem mandar o arquivo pra site estranho"),
    ("pdf-escaneado-vira-texto", "ocrmypdf/OCRmyPDF",
     "transformar PDF escaneado em texto que dá pra pesquisar e copiar"),
    ("sua-propria-netflix", "jellyfin/jellyfin",
     "montar a sua própria Netflix com os filmes e séries que você já tem, de graça"),
    ("guardar-senhas-sem-mensalidade", "keepassxreboot/keepassxc",
     "guardar todas as suas senhas num lugar só, sem pagar mensalidade e sem ninguém ver"),
    ("papelada-da-casa-em-segundos", "paperless-ngx/paperless-ngx",
     "achar qualquer conta, nota fiscal ou documento da casa em segundos, em vez de revirar gaveta"),
    ("baixar-video-de-qualquer-site", "yt-dlp/yt-dlp",
     "baixar um vídeo de praticamente qualquer site pra ver depois, sem aplicativo"),
    ("imagem-por-ia-gratis", "AUTOMATIC1111/stable-diffusion-webui",
     "gerar imagem por IA no seu computador, sem limite e sem pagar por imagem"),
    ("gravar-tela-gratis", "obsproject/obs-studio",
     "gravar a tela e transmitir ao vivo de graça, sem marca d'água"),
    ("video-com-ia-escrevendo-html", "heygen-com/hyperframes",
     "criar vídeo com IA só escrevendo texto, de graça e open source"),
]
INTERVALO = timedelta(hours=10)  # 15/11: dica é o formato que o Davi quer; até dois por dia
PREFIXO = "utilidade:"


def proxima(estado: dict) -> tuple[str, str, str] | None:
    return next((u for u in UTILIDADES if f"{PREFIXO}{u[0]}" not in estado), None)


def precisa(estado: dict, agora: datetime | None = None) -> bool:
    agora = agora or datetime.now(timezone.utc)
    feitas = [datetime.fromisoformat(v["quando"]) for k, v in estado.items() if k.startswith(PREFIXO)]
    return not feitas or agora - max(feitas) >= INTERVALO


def extra(promessa: str) -> str:
    """O ângulo que vai junto dos FATOS no prompt do roteirista."""
    from . import segredos
    return segredos.texto("extra_utilidade").replace("__PROMESSA__", promessa)


def registrar(slug: str):
    series.registrar(f"{PREFIXO}{slug}", slug)
