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
import sys
import tempfile

from dotenv import load_dotenv
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


def autenticar_drive(arquivo_client_secret: str = ARQUIVO_CLIENT_SECRET, arquivo_token: str = ARQUIVO_TOKEN_DRIVE):
    credenciais = None
    try:
        credenciais = Credentials.from_authorized_user_file(arquivo_token, SCOPES)
    except FileNotFoundError:
        pass

    if not credenciais or not credenciais.valid:
        if credenciais and credenciais.expired and credenciais.refresh_token:
            credenciais.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(arquivo_client_secret, SCOPES)
            credenciais = flow.run_local_server(port=0)

        with open(arquivo_token, "w", encoding="utf-8") as f:
            f.write(credenciais.to_json())

    return credenciais


def _chave_ordenacao_arquivo(nome: str):
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
    """Lista subpastas de trabalho dentro da pasta de entrada, ignorando a
    própria pasta "Processados"."""
    query = (
        f"'{pasta_entrada_id}' in parents and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    resultado = service.files().list(q=query, fields="files(id, name)").execute()
    return [p for p in resultado.get("files", []) if p["id"] != pasta_processados_id]


def baixar_arquivos_da_pasta(service, pasta_id: str, destino_local: str) -> tuple[list[str], str | None]:
    """Baixa todo arquivo de imagem/áudio dentro da pasta pro diretório
    local, mantendo o nome original (a ordem numérica das imagens é
    resolvida por quem chama, igual já acontece no modo --audio local)."""
    resultado = service.files().list(
        q=f"'{pasta_id}' in parents and trashed = false",
        fields="files(id, name, mimeType)",
    ).execute()

    imagens, audio = [], None
    for arquivo in resultado.get("files", []):
        nome = arquivo["name"]
        extensao = os.path.splitext(nome)[1].lower()
        if extensao not in EXTENSOES_IMAGEM and extensao not in EXTENSOES_AUDIO:
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
        else:
            if audio is not None:
                print(f"  AVISO: mais de um áudio na pasta, usando o primeiro ({os.path.basename(audio)})")
            else:
                audio = caminho_local

    imagens.sort(key=lambda c: _chave_ordenacao_arquivo(os.path.basename(c)))
    return imagens, audio


def subir_video(service, caminho_video: str, pasta_saida_id: str, nome: str):
    metadados = {"name": nome, "parents": [pasta_saida_id]}
    media = MediaFileUpload(caminho_video, mimetype="video/mp4", resumable=True)
    arquivo = service.files().create(body=metadados, media_body=media, fields="id").execute()
    return arquivo["id"]


def mover_para_processados(service, pasta_id: str, pasta_entrada_id: str, pasta_processados_id: str):
    service.files().update(
        fileId=pasta_id, addParents=pasta_processados_id, removeParents=pasta_entrada_id, fields="id, parents",
    ).execute()


def processar_pasta(service, pasta: dict, pasta_saida_id: str) -> bool:
    """Processa uma pasta de trabalho: baixa fotos+áudio, monta o vídeo,
    sobe o resultado. Retorna True se deu tudo certo (só então a pasta é
    movida pra "Processados" pelo chamador -- falha não move, fica
    disponível pra nova tentativa)."""
    print(f"\n=== Processando pasta '{pasta['name']}' ===")
    with tempfile.TemporaryDirectory() as pasta_tmp:
        imagens, audio = baixar_arquivos_da_pasta(service, pasta["id"], pasta_tmp)
        if not imagens or not audio:
            print(f"  pasta incompleta (imagens={len(imagens)}, audio={'sim' if audio else 'não'}) -- pulando")
            return False

        print(f"  {len(imagens)} imagens + 1 áudio encontrados")
        caminho_saida = os.path.join(pasta_tmp, "video_final.mp4")
        try:
            montar_video_de_audio_e_imagens(audio, imagens, caminho_saida, plataforma="tiktok")
        except Exception as e:
            print(f"  ERRO ao montar vídeo: {e}")
            return False

        nome_saida = f"{pasta['name']}.mp4"
        subir_video(service, caminho_saida, pasta_saida_id, nome_saida)
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
        return

    print(f"{len(pendentes)} pasta(s) pendente(s): {[p['name'] for p in pendentes]}")
    for pasta in pendentes:
        sucesso = processar_pasta(service, pasta, pasta_saida_id)
        if sucesso:
            mover_para_processados(service, pasta["id"], pasta_entrada_id, pasta_processados_id)
            print(f"  pasta '{pasta['name']}' movida pra Processados")


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
