"""Busca o assunto #1 em alta no Brasil agora via o feed RSS público do
Google Trends (https://trends.google.com/trending/rss?geo=BR) — não é
scraping de HTML de página de terceiro, é um feed público destinado a
consumo automatizado, sem bloqueio nem necessidade de chave/login.

Usado por src/canais/tendencias.py pra injetar o assunto do dia como
INSPIRAÇÃO ABSTRATA nos formatos de comédia/novela (nunca copiando o
assunto literalmente nem citando pessoa real — ver instrução embutida em
tendencias.py).
"""

import xml.etree.ElementTree as ET

import requests

URL_RSS = "https://trends.google.com/trending/rss?geo=BR"


def obter_trend_brasil() -> str | None:
    """Retorna o título do assunto #1 em alta no Brasil agora, ou None se o
    feed falhar por qualquer motivo (o chamador deve cair pro tema
    genérico/manual nesse caso, nunca travar o pipeline por causa disso)."""
    try:
        resp = requests.get(URL_RSS, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        item = root.find(".//item/title")
        return item.text.strip() if item is not None and item.text else None
    except Exception as e:
        print(f"[obter_trends] falhou ao buscar trend do Brasil: {e}")
        return None


if __name__ == "__main__":
    print(obter_trend_brasil())
