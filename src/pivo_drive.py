"""Automação do fluxo "pivô": lê pastas de vídeo (fotos + narração já
prontas, feitas pelo irmão do Davi) direto do Google Drive, monta o vídeo
final (transição, tremida, legenda, trilha) e sobe o resultado numa pasta
de saída -- sem precisar copiar nada manualmente pra essa máquina.

Setup necessário (uma vez só, feito pelo Davi):
    1. console.cloud.google.com -> mesmo projeto do client_secret.json já
       usado pro YouTube -> "APIs e serviços" -> ativar "Google Drive API".
    2. No Google Drive da conta davizera0601@gmail.com, criar duas pastas:
       "Vídeos pra Fazer" (onde o irmão cria uma subpasta por vídeo, com as
       fotos + o áudio da narração dentro) e "Vídeos Prontos" (onde os
       vídeos montados são enviados, sem subpasta). Compartilhar as duas
       com a conta do irmão (edição).
    3. Pegar o ID de cada pasta pela URL do Drive
       (drive.google.com/drive/folders/<ID>) e configurar como variável de
       ambiente DRIVE_PASTA_ENTRADA_ID / DRIVE_PASTA_SAIDA_ID (.env local
       ou secret do GitHub Actions).
    4. Rodar `python src/pivo_drive.py --auth` uma vez localmente -- abre o
       navegador pra autorizar o acesso à conta davizera0601@gmail.com
       (login/senha são digitados pelo próprio Davi no navegador, nunca por
       este script). Gera token_drive.json, que depois vai como secret
       GOOGLE_DRIVE_TOKEN_JSON no GitHub Actions (mesmo padrão do
       token.json do YouTube).

Uso (depois do setup):
    python src/pivo_drive.py               # processa todas as pastas novas
    python src/pivo_drive.py --auth         # só autentica (gera token_drive.json)
"""

import argparse
import io
import os
import re
import ssl
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from montar_video_local import montar_video_de_audio_e_imagens  # noqa: E402

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive"]
ARQUIVO_CLIENT_SECRET = "client_secret.json"
ARQUIVO_TOKEN_DRIVE = "token_drive.json"
NOME_PASTA_PROCESSADOS = "Processados"

EXTENSOES_IMAGEM = (".jpg", ".jpeg", ".png")
EXTENSOES_AUDIO = (".mp3", ".wav", ".m4a", ".mpeg", ".mpga")
# .txt com o roteiro escrito marcado ([FOTO 1]..[FOTO N]) -- formato novo
# 2026-09-12, opcional (pastas antigas/sem roteiro caem pro fallback de
# detecção de pausa dentro de montar_video_de_audio_e_imagens).
EXTENSAO_ROTEIRO = ".txt"
# Bug real 2026-09-30: o irmão do Davi escreveu o roteiro marcado num Word
# (.docx) em vez de .txt puro -- baixar_arquivos_da_pasta ignorava o
# arquivo inteiro (extensão não reconhecida), então caía sempre no
# fallback de detecção de pausa mesmo com o roteiro pronto na pasta.
EXTENSAO_ROTEIRO_DOCX = ".docx"
# Trilha de fundo CUSTOM por pasta (pedido do Davi 2026-09-30, canal virando
# estilo "mistério"): sem isso, montar_video_de_audio_e_imagens sempre mixa
# a mesma trilha fixa (TRILHAS_POR_PLATAFORMA["tiktok"]) em todo vídeo do
# pivô -- vídeo "sonho"/"morte" saíram com a trilha errada (a de terror) no
# mesmo processamento que já rodou. O irmão do Davi baixa a música nova como
# vídeo (ex: "Warm Nights Song.mp4", só o áudio importa) -- ffmpeg lê a
# faixa de áudio de um container de vídeo sem problema, não precisa
# extrair antes.
EXTENSOES_MUSICA_CUSTOM = (".mp4", ".mov", ".m4v")

# Pedido do Davi 2026-09-11: não mover a pasta original pra "Processados" na
# hora -- se o vídeo saiu cortado ou com algum problema, o irmão (e o Davi)
# ainda precisam achar fácil as fotos/áudio originais pra refazer. Em vez de
# mover na hora, marca a pasta como processada (appProperties, que sobrevive
# entre execuções do cron já que cada run é um processo novo) e só move de
# fato depois desse prazo, numa passada separada em toda execução.
PRAZO_ARQUIVAMENTO = timedelta(hours=24)
CHAVE_PROCESSADO_EM = "processado_em"


def autenticar_drive(arquivo_client_secret: str = ARQUIVO_CLIENT_SECRET, arquivo_token: str = ARQUIVO_TOKEN_DRIVE):
    credenciais = None
    try:
        credenciais = Credentials.from_authorized_user_file(arquivo_token, SCOPES)
    except FileNotFoundError:
        pass

    if not credenciais or not credenciais.valid:
        if credenciais and credenciais.expired and credenciais.refresh_token:
            try:
                credenciais.refresh(Request())
            except RefreshError:
                # Mesmo bug de src/publicar_youtube.py: sem isso, o persist
                # do workflow reintroduz um token quebrado por cima de uma
                # correção manual feita enquanto a run ainda está de pé.
                if os.path.exists(arquivo_token):
                    os.remove(arquivo_token)
                raise
        else:
            flow = InstalledAppFlow.from_client_secrets_file(arquivo_client_secret, SCOPES)
            credenciais = flow.run_local_server(port=0)

        with open(arquivo_token, "w", encoding="utf-8") as f:
            f.write(credenciais.to_json())

    return credenciais


def _chave_ordenacao_arquivo(nome: str):
    # Bug real 2026-09-24: quando alguém nomeia a foto na mão com um índice
    # explícito (ex: "la_11_2K_....jpeg", "navio_9_2K_....jpeg"), esse número
    # é a ordem PRETENDIDA -- mas se a foto foi regerada depois (carimbo de
    # geração mais novo que o de fotos posteriores), ordenar só pelo carimbo
    # (ver abaixo) jogava ela pro lugar errado (video LA e video navio, os
    # dois saíram com foto fora de ordem mesmo com roteiro certo). Índice
    # explícito imediatamente antes de "_2K_" tem prioridade sobre o carimbo.
    indice_explicito = re.search(r"_(\d+)_2K_", nome)
    if indice_explicito:
        return (-2, int(indice_explicito.group(1)), nome)

    # Bug real 2026-09-21: fotos baixadas do Google Flow chegam com nome tipo
    # "Boy_clutching_kite_string_2K_20260918172835.jpeg" -- o primeiro número
    # é sempre o "2" de "2K", então todas empatavam e caíam em ordem
    # alfabética pela descrição (vídeo 4 e 5 saíram com as fotos fora de
    # ordem). O carimbo de 14 dígitos (AAAAMMDDHHMMSS) no fim do nome é a
    # ordem em que o Flow gerou -- a mesma da narração.
    carimbo = re.search(r"(?<!\d)(20\d{12})(?!\d)", nome)
    if carimbo:
        return (-1, int(carimbo.group(1)), nome)
    numeros = re.findall(r"\d+", nome)
    return (int(numeros[0]), nome) if numeros else (float("inf"), nome)


def obter_ou_criar_subpasta(service, nome: str, pasta_pai_id: str) -> str:
    """Acha a subpasta pelo nome dentro de pasta_pai_id, ou cria se não
    existir (usado pra "Processados")."""
    query = (
        f"name = '{nome}' and '{pasta_pai_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    resultado = service.files().list(q=query, fields="files(id, name)").execute()
    achados = resultado.get("files", [])
    if achados:
        return achados[0]["id"]

    metadados = {
        "name": nome,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [pasta_pai_id],
    }
    pasta = service.files().create(body=metadados, fields="id").execute()
    return pasta["id"]


def listar_subpastas_pendentes(service, pasta_entrada_id: str, pasta_processados_id: str) -> list[dict]:
    """Lista subpastas de trabalho dentro da pasta de entrada ainda não
    processadas -- ignora a própria pasta "Processados" e qualquer pasta que
    já tenha sido processada com sucesso (marcada via appProperties, ver
    `marcar_como_processada`) mas ainda não foi arquivada."""
    query = (
        f"'{pasta_entrada_id}' in parents and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    resultado = service.files().list(q=query, fields="files(id, name, appProperties)").execute()
    return [
        p
        for p in resultado.get("files", [])
        if p["id"] != pasta_processados_id and not (p.get("appProperties") or {}).get(CHAVE_PROCESSADO_EM)
    ]


def marcar_como_processada(service, pasta_id: str):
    """Marca a pasta como processada com sucesso, sem movê-la ainda -- o
    arquivamento de verdade (mover pra "Processados") só acontece depois de
    PRAZO_ARQUIVAMENTO, pra dar tempo de perceber e refazer se o vídeo sair
    com problema."""
    agora = datetime.now(timezone.utc).isoformat()
    service.files().update(fileId=pasta_id, body={"appProperties": {CHAVE_PROCESSADO_EM: agora}}).execute()


def arquivar_pastas_processadas_antigas(service, pasta_entrada_id: str, pasta_processados_id: str):
    """Move pra "Processados" as pastas que já foram processadas há mais de
    PRAZO_ARQUIVAMENTO -- roda em toda execução, separado do processamento
    de pastas novas."""
    query = (
        f"'{pasta_entrada_id}' in parents and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    resultado = service.files().list(q=query, fields="files(id, name, appProperties)").execute()
    agora = datetime.now(timezone.utc)

    for pasta in resultado.get("files", []):
        if pasta["id"] == pasta_processados_id:
            continue
        processado_em = (pasta.get("appProperties") or {}).get(CHAVE_PROCESSADO_EM)
        if not processado_em:
            continue
        if agora - datetime.fromisoformat(processado_em) < PRAZO_ARQUIVAMENTO:
            continue
        mover_para_processados(service, pasta["id"], pasta_entrada_id, pasta_processados_id)
        print(f"  pasta '{pasta['name']}' arquivada em Processados (processada há mais de 24h)")


def _extrair_texto_docx(caminho: str) -> str:
    """Extrai o texto puro (parágrafo por parágrafo) de um .docx, só com o
    que já vem na biblioteca padrão (zipfile + XML -- um .docx é só um zip
    com word/document.xml dentro) -- suficiente pra pegar os marcadores
    [FOTO N] que _carregar_roteiro_marcado precisa, sem puxar dependência
    nova só pra isso (ver bug real do av<19 nesta mesma semana -- toda
    dependência nova é mais um jeito de o cron quebrar sozinho)."""
    import xml.etree.ElementTree as ET
    import zipfile

    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with zipfile.ZipFile(caminho) as z:
        xml_bytes = z.read("word/document.xml")
    raiz = ET.fromstring(xml_bytes)

    paragrafos = []
    for p in raiz.iter(f"{{{ns_w}}}p"):
        texto_paragrafo = "".join(t.text or "" for t in p.iter(f"{{{ns_w}}}t"))
        paragrafos.append(texto_paragrafo)
    return "\n".join(paragrafos)


def baixar_arquivos_da_pasta(
    service, pasta_id: str, destino_local: str
) -> tuple[list[str], str | None, str | None, str | None]:
    """Baixa todo arquivo de imagem/áudio/roteiro/trilha-custom dentro da
    pasta pro diretório local, mantendo o nome original (a ordem numérica
    das imagens é resolvida por quem chama, igual já acontece no modo
    --audio local). O roteiro (.txt com marcadores [FOTO N], ver
    EXTENSAO_ROTEIRO/montar_video_de_audio_e_imagens) e a trilha custom
    (ver EXTENSOES_MUSICA_CUSTOM) são opcionais -- pasta sem eles ainda
    funciona (cai pro fallback de detecção de pausa e pra trilha padrão
    fixa, respectivamente)."""
    resultado = service.files().list(
        q=f"'{pasta_id}' in parents and trashed = false",
        fields="files(id, name, mimeType)",
    ).execute()

    imagens, audio, roteiro, musica_custom = [], None, None, None
    for arquivo in resultado.get("files", []):
        nome = arquivo["name"]
        extensao = os.path.splitext(nome)[1].lower()
        reconhecida = (
            extensao in EXTENSOES_IMAGEM or extensao in EXTENSOES_AUDIO
            or extensao == EXTENSAO_ROTEIRO or extensao == EXTENSAO_ROTEIRO_DOCX
            or extensao in EXTENSOES_MUSICA_CUSTOM
        )
        if not reconhecida:
            continue

        caminho_local = os.path.join(destino_local, nome)
        request = service.files().get_media(fileId=arquivo["id"])
        with open(caminho_local, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            concluido = False
            while not concluido:
                _, concluido = downloader.next_chunk()

        if extensao in EXTENSOES_IMAGEM:
            imagens.append(caminho_local)
        elif extensao in EXTENSOES_AUDIO:
            if audio is not None:
                print(f"  AVISO: mais de um áudio na pasta, usando o primeiro ({os.path.basename(audio)})")
            else:
                audio = caminho_local
        elif extensao in EXTENSOES_MUSICA_CUSTOM:
            if musica_custom is not None:
                print(f"  AVISO: mais de uma trilha custom na pasta, usando a primeira ({os.path.basename(musica_custom)})")
            else:
                musica_custom = caminho_local
        else:
            if roteiro is not None:
                print(f"  AVISO: mais de um roteiro na pasta, usando o primeiro ({os.path.basename(roteiro)})")
                continue
            if extensao == EXTENSAO_ROTEIRO_DOCX:
                # _carregar_roteiro_marcado só lê .txt puro -- extrai o
                # texto do .docx pra um .txt irmão no mesmo diretório
                # temporário antes de expor como "roteiro".
                caminho_txt = os.path.splitext(caminho_local)[0] + ".txt"
                with open(caminho_txt, "w", encoding="utf-8") as f:
                    f.write(_extrair_texto_docx(caminho_local))
                roteiro = caminho_txt
            else:
                roteiro = caminho_local

    # Duas fotos com o MESMO nome (Flow gera duplicata quando dois downloads
    # caem no mesmo segundo) baixam pro mesmo caminho local -- sem isso a
    # foto entrava 2x na lista e estourava a contagem de [FOTO N] do roteiro
    # (video4, 2026-09-21: 17 fotos pra 16 marcadores).
    imagens = list(dict.fromkeys(imagens))
    imagens.sort(key=lambda c: _chave_ordenacao_arquivo(os.path.basename(c)))
    return imagens, audio, roteiro, musica_custom


def subir_video(service, caminho_video: str, pasta_saida_id: str, nome: str, tentativas: int = 3):
    """Sobe o vídeo montado pro Drive, tentando de novo em caso de falha de
    rede transitória (ex: SSLEOFError, 2026-09-24 -- vídeo já tinha sido
    montado com sucesso e a run inteira quebrava sem tentar de novo, tendo
    que remontar o vídeo do zero na próxima execução)."""
    metadados = {"name": nome, "parents": [pasta_saida_id]}
    ultimo_erro = None
    for tentativa in range(1, tentativas + 1):
        try:
            media = MediaFileUpload(caminho_video, mimetype="video/mp4", resumable=True)
            arquivo = service.files().create(body=metadados, media_body=media, fields="id").execute()
            return arquivo["id"]
        except (ssl.SSLError, OSError, TimeoutError) as e:
            ultimo_erro = e
            print(f"  upload falhou (tentativa {tentativa}/{tentativas}): {e}")
            time.sleep(5 * tentativa)
    raise RuntimeError(f"Upload pro Drive falhou após {tentativas} tentativas: {ultimo_erro}")


def mover_para_processados(service, pasta_id: str, pasta_entrada_id: str, pasta_processados_id: str):
    service.files().update(
        fileId=pasta_id, addParents=pasta_processados_id, removeParents=pasta_entrada_id, fields="id, parents",
    ).execute()


def processar_pasta(service, pasta: dict, pasta_saida_id: str) -> bool:
    """Processa uma pasta de trabalho: baixa fotos+áudio, monta o vídeo,
    sobe o resultado. Retorna True se deu tudo certo (só então o chamador
    marca a pasta como processada, ver `marcar_como_processada` -- falha não
    marca, fica disponível pra nova tentativa)."""
    print(f"\n=== Processando pasta '{pasta['name']}' ===")
    with tempfile.TemporaryDirectory() as pasta_tmp:
        imagens, audio, roteiro, musica_custom = baixar_arquivos_da_pasta(service, pasta["id"], pasta_tmp)
        if not imagens or not audio:
            print(f"  pasta incompleta (imagens={len(imagens)}, audio={'sim' if audio else 'não'}) -- pulando")
            return False

        print(
            f"  {len(imagens)} imagens + 1 áudio"
            + (" + 1 roteiro marcado" if roteiro else " (sem roteiro marcado, usando detecção de pausa)")
            + (f" + trilha custom ({os.path.basename(musica_custom)})" if musica_custom else "")
        )
        caminho_saida = os.path.join(pasta_tmp, "video_final.mp4")
        try:
            montar_video_de_audio_e_imagens(
                audio, imagens, caminho_saida, plataforma="tiktok", caminho_roteiro=roteiro,
                caminho_trilha_custom=musica_custom,
            )
        except Exception as e:
            print(f"  ERRO ao montar vídeo: {e}")
            return False

        nome_saida = f"{pasta['name']}.mp4"
        try:
            subir_video(service, caminho_saida, pasta_saida_id, nome_saida)
        except Exception as e:
            print(f"  ERRO ao subir vídeo: {e}")
            return False
        print(f"  enviado como '{nome_saida}' pra pasta de saída")
        return True


def processar_tudo():
    pasta_entrada_id = os.environ["DRIVE_PASTA_ENTRADA_ID"]
    pasta_saida_id = os.environ["DRIVE_PASTA_SAIDA_ID"]

    credenciais = autenticar_drive()
    service = build("drive", "v3", credentials=credenciais)

    pasta_processados_id = obter_ou_criar_subpasta(service, NOME_PASTA_PROCESSADOS, pasta_entrada_id)
    pendentes = listar_subpastas_pendentes(service, pasta_entrada_id, pasta_processados_id)

    if not pendentes:
        print("Nenhuma pasta nova pra processar.")
    else:
        print(f"{len(pendentes)} pasta(s) pendente(s): {[p['name'] for p in pendentes]}")
        for pasta in pendentes:
            try:
                sucesso = processar_pasta(service, pasta, pasta_saida_id)
            except Exception as e:
                # Bug real 2026-09-24: uma exceção não tratada numa pasta
                # (ex: falha de rede no upload) derrubava a run inteira,
                # deixando as pastas SEGUINTES da lista sem nem tentar
                # nessa execução (video navio ficou parado esperando o
                # video LA, que tinha acabado de quebrar no upload).
                print(f"  ERRO inesperado processando '{pasta['name']}': {e}")
                sucesso = False
            if sucesso:
                marcar_como_processada(service, pasta["id"])
                print(f"  pasta '{pasta['name']}' processada (fica na entrada por 24h antes de arquivar)")

    arquivar_pastas_processadas_antigas(service, pasta_entrada_id, pasta_processados_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth", action="store_true", help="só autentica e gera token_drive.json")
    args = parser.parse_args()

    if args.auth:
        autenticar_drive()
        print(f"Autenticado, token salvo em {ARQUIVO_TOKEN_DRIVE}")
        return

    processar_tudo()


if __name__ == "__main__":
    main()
