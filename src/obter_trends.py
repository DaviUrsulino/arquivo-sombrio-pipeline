"""Duas fontes automáticas e legítimas de "o que está em alta agora" —
NENHUMA delas é scraping (não lê HTML de página de terceiro, não imita
app/dispositivo, não acessa endpoint não-documentado):

1. Feed RSS público do Google Trends (trends.google.com) -- destinado a
   consumo automatizado, sem chave/login.
2. Endpoint oficial e documentado da YouTube Data API v3 (`videos.list`,
   `chart=mostPopular`) -- mesma API que já usamos pra publicar vídeo,
   reaproveita a autenticação OAuth existente.

Usado por src/canais/tendencias.py pra injetar o assunto/formato do
momento como INSPIRAÇÃO ABSTRATA (nunca copiando o conteúdo literalmente
nem citando pessoa real — ver instrução embutida em tendencias.py).
Decisão 2026-09-09: em vez de scraping de TikTok/Reels (risco de ToS e
pra auditoria pendente, decisão já tomada antes), a automação de "o que
está bombando" roda 100% em cima de fontes com API pública/oficial."""

import xml.etree.ElementTree as ET

import requests

URL_RSS = "https://trends.google.com/trending/rss?geo=BR"


def obter_trend_brasil() -> str | None:
    """Retorna o título do assunto #1 em alta no Brasil agora (Google
    Trends), ou None se o feed falhar por qualquer motivo (o chamador deve
    cair pro tema genérico/manual nesse caso, nunca travar o pipeline por
    causa disso)."""
    try:
        resp = requests.get(URL_RSS, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        item = root.find(".//item/title")
        return item.text.strip() if item is not None and item.text else None
    except Exception as e:
        print(f"[obter_trends] falhou ao buscar trend do Brasil: {e}")
        return None


def obter_titulos_trending_youtube_br(arquivo_token: str, limite: int = 10) -> list[str]:
    """Retorna títulos dos vídeos mais populares do YouTube no Brasil agora
    (endpoint oficial `videos.list?chart=mostPopular`, mesma API/credencial
    já usada pra publicar) -- lista vazia se falhar por qualquer motivo."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        credenciais = Credentials.from_authorized_user_file(
            arquivo_token, ["https://www.googleapis.com/auth/youtube"]
        )
        if credenciais.expired and credenciais.refresh_token:
            credenciais.refresh(Request())

        youtube = build("youtube", "v3", credentials=credenciais)
        resposta = youtube.videos().list(
            part="snippet", chart="mostPopular", regionCode="BR", maxResults=limite
        ).execute()
        return [item["snippet"]["title"] for item in resposta.get("items", [])]
    except Exception as e:
        print(f"[obter_trends] falhou ao buscar trending do YouTube BR: {e}")
        return []


if __name__ == "__main__":
    print("Google Trends:", obter_trend_brasil())
    print("YouTube trending BR:", obter_titulos_trending_youtube_br("token_tendencias.json"))
