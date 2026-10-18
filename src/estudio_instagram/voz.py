"""Narração com tempo por palavra.

`ProvedorDeVoz` é a interface; `ElevenLabs` é a implementação usada em produção. Os testes
usam um dublê que implementa a mesma interface, sem rede e sem gastar crédito.
"""

import base64
import hashlib
import json
import os
import subprocess
import urllib.error
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
        try:
            with self._abrir(pedido, timeout=120) as resposta:
                return json.load(resposta)
        except urllib.error.HTTPError as erro:
            # O ElevenLabs devolve 401 tanto para chave inválida quanto para cota esgotada; o motivo vem no corpo.
            detalhe = erro.read().decode(errors="replace")[:300]
            raise RuntimeError(f"ElevenLabs recusou (HTTP {erro.code}): {detalhe}") from erro

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


class EdgeTTS:
    """Voz reserva gratuita (vozes neurais do Edge), com tempo por palavra. Sem chave e sem cota.

    Entra quando o ElevenLabs recusa por cota. Soa mais "assistente" que o ElevenLabs, mas nunca
    deixa o cron sem post.
    """

    def __init__(self, voz: str = "pt-BR-AntonioNeural", ritmo: str = "+8%"):
        self.voz = voz
        self.ritmo = ritmo

    def sintetizar(self, texto: str) -> Narracao:
        import asyncio

        import edge_tts  # só aqui: o job só instala quando precisa

        async def _rodar():
            comunicacao = edge_tts.Communicate(texto, self.voz, rate=self.ritmo, boundary="WordBoundary")
            audio, palavras = bytearray(), []
            async for evento in comunicacao.stream():
                if evento["type"] == "audio":
                    audio += evento["data"]
                elif evento["type"] == "WordBoundary":
                    palavras.append(PalavraNoTempo(round(evento["offset"] / 1e7, 3), evento["text"]))
            return bytes(audio), palavras

        mp3, palavras = asyncio.run(_rodar())
        if not mp3 or not palavras:
            raise RuntimeError("EdgeTTS não devolveu áudio ou tempos de palavra")
        return Narracao(mp3_para_pcm(mp3), palavras)


class ComReserva:
    """Usa `principal`; se ele recusar (cota, chave), usa `reserva` para o vídeo INTEIRO.

    `preparar` sintetiza todas as falas de uma vez antes de montar o vídeo. Assim, se a cota acabar
    no meio, nenhuma fala sai com a voz principal e o vídeo não mistura duas vozes.
    """

    def __init__(self, principal: ProvedorDeVoz, reserva: ProvedorDeVoz):
        self.principal = principal
        self.reserva = reserva
        self._prontas: dict[str, Narracao] = {}
        self.usando_reserva = False

    def preparar(self, textos: list[str]):
        try:
            self._prontas = {t: self.principal.sintetizar(t) for t in textos}
        except RuntimeError as erro:
            print(f"voz principal indisponível ({str(erro)[:160]}); usando a voz reserva")
            self._prontas = {}
            self.usando_reserva = True

    def sintetizar(self, texto: str) -> Narracao:
        if not self.usando_reserva and texto in self._prontas:
            return self._prontas[texto]
        return (self.reserva if self.usando_reserva else self.principal).sintetizar(texto)
