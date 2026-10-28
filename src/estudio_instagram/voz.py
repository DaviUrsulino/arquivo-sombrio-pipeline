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


# Como o brasileiro fala termos de tecnologia. Cada termo vira UMA palavra só, para o número de palavras
# não mudar: assim a legenda continua escrita certa ("GitHub") e só o áudio usa a grafia falada.
PRONUNCIA = {
    "github": "Guitrab", "claude": "Clód", "code": "Cóude", "codex": "Códex", "gemini": "Jêmini",
    "cli": "cêeleai", "mcp": "emecepê", "html": "agatêemeéle", "css": "cêésseésse", "ia": "iá",
    "readme": "ridmi", "pyvideotrans": "PáiVídeoTréns", "skyvern": "Scáivern", "powerpoint": "Páuerpóint", "chatgpt": "Tchatdjipití", "markitdown": "Márquitdáun", "pdf": "pedeéfe", "word": "Uórd", "excel": "Éksel", "api": "apeí", "cursor": "Cârsor", "npm": "enepeême", "json": "djêison",
}


def _limpa(token: str) -> str:
    return "".join(c for c in token.lower() if c.isalnum())


def aplicar_pronuncia(texto: str) -> tuple[str, list[str]]:
    """Troca termos pelo jeito de falar. Devolve (texto falado, palavras originais na mesma ordem)."""
    originais, falados = [], []
    for token in texto.split():
        originais.append(token)
        chave = _limpa(token)
        if chave in PRONUNCIA:
            sufixo = token[len(token.rstrip(".,;:!?")):]  # mantém a pontuação final, que dá a pausa
            falados.append(PRONUNCIA[chave] + sufixo)
        else:
            falados.append(token)
    return " ".join(falados), originais


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

        falado, originais = aplicar_pronuncia(texto)

        async def _rodar():
            comunicacao = edge_tts.Communicate(falado, self.voz, rate=self.ritmo, boundary="WordBoundary")
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
        if len(palavras) == len(originais):  # volta a escrever "GitHub" na legenda, não "Guitrab"
            palavras = [PalavraNoTempo(p.t, original.strip(".,;:!?") or p.palavra) for p, original in zip(palavras, originais)]
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
            if hasattr(self.principal, "sintetizar_varios"):
                self._prontas = self.principal.sintetizar_varios(textos)
            else:
                self._prontas = {t: self.principal.sintetizar(t) for t in textos}
        except Exception as erro:  # não só RuntimeError: falha de rede crua não pode matar o vídeo do dia
            print(f"voz principal indisponível ({str(erro)[:160]}); usando a voz reserva")
            self._prontas = {}
            self.usando_reserva = True

    def sintetizar(self, texto: str) -> Narracao:
        if not self.usando_reserva and texto in self._prontas:
            return self._prontas[texto]
        return (self.reserva if self.usando_reserva else self.principal).sintetizar(texto)


class GeminiTTS:
    """Voz do Gemini TTS (voz "Orus" por padrão, escolhida pelo Davi). Natural e fala bem os termos de tecnologia.

    A API devolve só o áudio (PCM 24 kHz); o tempo por palavra vem de `alinhamento.alinhar`, que olha as
    pausas do próprio áudio. Faz tentativas com espera quando a API pede calma (HTTP 429/503).
    """

    MODELO = "gemini-2.5-flash-preview-tts"
    INSTRUCAO = "Fale em português do Brasil, de forma natural e animada, como uma pessoa contando uma descoberta para um amigo: "
    ESPERAS_S = (12, 25, 45, 60)

    def __init__(self, voz: str = "Orus", pasta_cache: Path | None = None, chave: str | None = None,
                 abrir=urllib.request.urlopen, esperar=None):
        import time
        self.voz = voz
        self.pasta_cache = Path(pasta_cache) if pasta_cache else None
        self._chave = chave
        self._abrir = abrir
        self._esperar = esperar or time.sleep

    def _chave_api(self) -> str:
        chave = (self._chave or os.getenv("GEMINI_API_KEY", "")).strip()
        if not chave:
            raise RuntimeError("GEMINI_API_KEY não definida")
        return chave

    def _arquivo_cache(self, texto: str) -> Path | None:
        if not self.pasta_cache:
            return None
        chave = hashlib.sha1(f"{self.MODELO}|{self.voz}|{texto}".encode()).hexdigest()[:16]
        return self.pasta_cache / f"gemini-{chave}.pcm"

    def _pedir_pcm(self, texto: str) -> bytes:
        corpo = json.dumps({
            "contents": [{"parts": [{"text": self.INSTRUCAO + texto}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": self.voz}}},
            },
        }).encode()
        ultimo = None
        for tentativa in range(len(self.ESPERAS_S) + 1):
            pedido = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.MODELO}:generateContent", data=corpo,
                headers={"Content-Type": "application/json", "x-goog-api-key": self._chave_api()}, method="POST",
            )
            try:
                with self._abrir(pedido, timeout=120) as resposta:
                    dados = json.load(resposta)
                return base64.b64decode(dados["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
            except urllib.error.HTTPError as erro:
                detalhe = erro.read().decode(errors="replace")[:200]
                ultimo = f"HTTP {erro.code} {detalhe}"
                if erro.code not in (429, 500, 502, 503, 504) or tentativa == len(self.ESPERAS_S):
                    break
                self._esperar(self.ESPERAS_S[tentativa])
            except (KeyError, IndexError, ValueError) as erro:  # resposta sem áudio (ex.: bloqueio de conteúdo)
                ultimo = f"resposta sem áudio ({erro})"
                if tentativa == len(self.ESPERAS_S):
                    break
                self._esperar(3)
            except urllib.error.URLError as erro:  # falha de rede crua (timeout, DNS, conexão recusada)
                ultimo = f"falha de rede ({erro.reason})"
                if tentativa == len(self.ESPERAS_S):
                    break
                self._esperar(self.ESPERAS_S[tentativa])
        raise RuntimeError(f"Gemini TTS recusou: {ultimo}")

    def _pcm(self, texto: str) -> bytes:
        arquivo = self._arquivo_cache(texto)
        if arquivo and arquivo.exists():
            return arquivo.read_bytes()
        pcm = self._pedir_pcm(texto)
        if arquivo:
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            arquivo.write_bytes(pcm)
        return pcm

    def sintetizar(self, texto: str) -> Narracao:
        from .alinhamento import alinhar, aparar

        pcm, _ = aparar(self._pcm(texto))
        return Narracao(pcm, alinhar(texto, pcm))

    def sintetizar_varios(self, textos: list[str]) -> dict[str, Narracao]:
        """Um único pedido para o vídeo inteiro (o plano grátis só aguenta poucos pedidos por dia).

        Fala tudo junto, o que também deixa a entonação mais natural, e corta nas pausas entre as frases.
        """
        from .alinhamento import aparar, cortar_em_cenas

        pcm, _ = aparar(self._pcm(" ".join(textos)))
        fatias = cortar_em_cenas(textos, pcm)
        return {texto: Narracao(fatia, palavras) for texto, (fatia, palavras) in zip(textos, fatias)}
