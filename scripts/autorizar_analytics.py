"""Autoriza a leitura do YouTube Analytics (retenção, % assistido, compartilhamentos) de uma conta, UMA vez.

Cria um token SEPARADO do de publicação (token_analytics*.json), com permissão só de leitura: o token que posta os
Shorts não é tocado. Davi, 13/11: "reautorizo, só manda aí".

Antes, uma vez por projeto Google Cloud (são dois: arquivo_sombrio e tendencias):
    console.cloud.google.com -> escolher o projeto do canal -> APIs e serviços -> Biblioteca ->
    "YouTube Analytics API" -> Ativar.

Depois, para cada canal (o navegador abre; escolha O CANAL certo na tela de login, não misture os dois):
    python scripts/autorizar_analytics.py arquivo_sombrio
    python scripts/autorizar_analytics.py tendencias

Cada comando grava o token na raiz. Para o GitHub (o workflow diário lê de lá), cole quando o comando pedir:
    gh secret set YOUTUBE_ANALYTICS_TOKEN_JSON -R DaviUrsulino/arquivo-sombrio-pipeline < token_analytics.json
    gh secret set YOUTUBE_ANALYTICS_TOKEN_JSON_TENDENCIAS -R DaviUrsulino/arquivo-sombrio-pipeline < token_analytics_tendencias.json
"""
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

RAIZ = Path(__file__).resolve().parents[1]
SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly", "https://www.googleapis.com/auth/youtube.readonly"]
CONTAS = {"arquivo_sombrio": ("client_secret.json", "token_analytics.json"),
          "tendencias": ("client_secret_tendencias.json", "token_analytics_tendencias.json")}

if __name__ == "__main__":
    conta = sys.argv[1] if len(sys.argv) > 1 else ""
    if conta not in CONTAS:
        raise SystemExit(f"uso: python scripts/autorizar_analytics.py {{{'|'.join(CONTAS)}}}")
    secret, token = CONTAS[conta]
    cred = InstalledAppFlow.from_client_secrets_file(str(RAIZ / secret), SCOPES).run_local_server(port=0, prompt="consent")
    (RAIZ / token).write_text(cred.to_json(), encoding="utf-8")
    print(f"ok: {token} gravado para a conta {conta} (tem refresh_token: {bool(cred.refresh_token)})")
