"""Narração com tempo por palavra.

`ProvedorDeVoz` é a interface; `ElevenLabs` é a implementação usada em produção. Os testes
usam um dublê que implementa a mesma interface, sem rede e sem gastar crédito.
"""

import base64
import hashlib
import json
import os
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .sincronia import PalavraNoTempo, palavras_do_alinhamento

TAXA_AMOSTRA = 24000
URL_ELEVENLABS = "https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps"


@dataclass
class Narracao:
    audio_pcm: bytes  # PCM 16 bits, mono, TAXA_AMOSTRA
    palavras: list[PalavraNoTempo]

    def duracao(self) -> float:
        return len(self.audio_pcm) / 2 / TAXA_AMOSTRA


class ProvedorDeVoz(Protocol):
    def sintetizar(self, texto: str) -> Narracao: ...


def mp3_para_pcm(mp3: bytes) -> bytes:
    resultado = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(TAXA_AMOSTRA), "-"],
        input=mp3, check=True, capture_output=True,
    )
    return resultado.stdout


class ElevenLabs:
    """Chama o endpoint with-timestamps e guarda a resposta em cache por hash.

    Rodar de novo com o mesmo texto, voz e modelo não chama a API.
    """

    def __init__(self, voz: str, modelo: str, pasta_cache: Path, chave: str | None = None, abrir=urllib.request.urlopen):
        self.voz = voz
        self.modelo = modelo
        self.pasta_cache = Path(pasta_cache)
        self._chave = chave
        self._abrir = abrir

    def _arquivo_cache(self, texto: str) -> Path:
        chave = hashlib.sha1(f"{self.voz}|{self.modelo}|{texto}".encode()).hexdigest()[:16]
        return self.pasta_cache / f"{chave}.json"

    def _chave_api(self) -> str:
        chave = self._chave or os.getenv("ELEVENLABS_API_KEY", "").strip()
        if not chave:
            raise RuntimeError("ELEVENLABS_API_KEY não definida")
        return chave

    def _pedir(self, texto: str) -> dict:
        pedido = urllib.request.Request(
            URL_ELEVENLABS.format(voz=self.voz),
            data=json.dumps({"text": texto, "model_id": self.modelo, "language_code": "pt"}).encode(),
            headers={"xi-api-key": self._chave_api(), "Content-Type": "application/json"},
        )
        with self._abrir(pedido, timeout=120) as resposta:
            return json.load(resposta)

    def sintetizar(self, texto: str) -> Narracao:
        arquivo = self._arquivo_cache(texto)
        if arquivo.exists():
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
        else:
            dados = self._pedir(texto)
            self.pasta_cache.mkdir(parents=True, exist_ok=True)
            arquivo.write_text(json.dumps(dados), encoding="utf-8")
        alinhamento = dados["alignment"]
        palavras = palavras_do_alinhamento(alinhamento["characters"], alinhamento["character_start_times_seconds"])
        return Narracao(mp3_para_pcm(base64.b64decode(dados["audio_base64"])), palavras)
