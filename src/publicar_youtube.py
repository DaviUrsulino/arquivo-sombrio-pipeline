"""Passo 3 do pipeline: publica o vídeo final automaticamente no YouTube
Shorts, via YouTube Data API v3 (gratuita, cota de 100 uploads/dia).

Setup necessário (uma vez só):
    1. console.cloud.google.com -> criar/selecionar projeto -> ativar
       "YouTube Data API v3".
    2. Nesse mesmo projeto: "APIs e serviços" -> "Credenciais" -> criar
       credencial "ID do cliente OAuth", tipo "App para computador".
    3. Baixar o JSON gerado e salvar como client_secret.json na raiz do
       projeto (mesma pasta do .env).

Uso:
    python src/publicar_youtube.py --video video_final.mp4 \
        --titulo "Título do Short" --descricao "Descrição..."

Na primeira execução abre o navegador pra você autorizar o acesso à sua
conta do YouTube — depois disso o token fica salvo em token.json e as
próximas execuções não pedem login de novo.
"""

import argparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube"]
ARQUIVO_CLIENT_SECRET = "client_secret.json"
ARQUIVO_TOKEN = "token.json"


def autenticar(arquivo_client_secret: str = ARQUIVO_CLIENT_SECRET, arquivo_token: str = ARQUIVO_TOKEN):
    credenciais = None
    try:
        credenciais = Credentials.from_authorized_user_file(arquivo_token, SCOPES)
    except FileNotFoundError:
        pass

    if not credenciais or not credenciais.valid:
        if credenciais and credenciais.expired and credenciais.refresh_token:
            credenciais.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                arquivo_client_secret, SCOPES
            )
            credenciais = flow.run_local_server(port=0)

        with open(arquivo_token, "w", encoding="utf-8") as f:
            f.write(credenciais.to_json())

    return credenciais


def publicar_short(
    caminho_video: str, titulo: str, descricao: str, tags: list[str],
    arquivo_client_secret: str = ARQUIVO_CLIENT_SECRET, arquivo_token: str = ARQUIVO_TOKEN,
):
    """arquivo_client_secret/arquivo_token permitem publicar em contas
    diferentes (ex: conta "Arquivo Sombrio" vs conta "Em Alta") sem misturar
    credenciais."""
    credenciais = autenticar(arquivo_client_secret, arquivo_token)
    youtube = build("youtube", "v3", credentials=credenciais)

    corpo = {
        "snippet": {
            "title": titulo,
            "description": descricao,
            "tags": tags,
            "categoryId": "24",  # Entretenimento
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            # Declara conteúdo alterado/sintético (voz e imagens geradas por
            # IA) -- exigido pela política de transparência do YouTube desde
            # out/2024. NÃO declarar não impede publicação, mas expõe a um
            # sistema de 3 avisos que pode suspender monetização; declarar
            # não reduz alcance/monetização (ver YouTube Help, "How this
            # content was made"), então não custa nada marcar sempre.
            "containsSyntheticMedia": True,
        },
    }

    midia = MediaFileUpload(caminho_video, chunksize=-1, resumable=True)
    requisicao = youtube.videos().insert(
        part="snippet,status", body=corpo, media_body=midia
    )

    resposta = None
    while resposta is None:
        status, resposta = requisicao.next_chunk()
        if status:
            print(f"Upload: {int(status.progress() * 100)}%")

    video_id = resposta["id"]
    print(f"\nPublicado: https://youtube.com/shorts/{video_id}")
    return video_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="video_final.mp4")
    parser.add_argument("--titulo", required=True)
    parser.add_argument("--descricao", default="")
    parser.add_argument(
        "--tags", default="terror,creepypasta,arquivosombrio", help="separadas por vírgula"
    )
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    publicar_short(args.video, args.titulo, args.descricao, tags)


if __name__ == "__main__":
    main()
