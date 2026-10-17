"""Publica Reels e carrossel direto na Instagram Graph API (graph.instagram.com), sem
depender de terceiro. Ver ADR-0005 (supera a decisão de usar Publora do ADR-0004).

A API só aceita `video_url`/`image_url` publicamente acessível — não dá pra mandar o
arquivo local. O pipeline hospeda o arquivo antes (ver hospedagem.py) e só manda a URL
aqui.

Fluxo do Reels: cria o container (media), espera o Instagram terminar de baixar o vídeo
(status_code vira FINISHED), publica. Fluxo do carrossel: cria um container por imagem,
depois um container pai referenciando os filhos, espera, publica.
"""

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

BASE = "https://graph.instagram.com/v22.0"
TENTATIVAS_STATUS = 60
INTERVALO_STATUS_S = 5


@dataclass(frozen=True)
class PostPublicado:
    media_id: str


class InstagramGraph:
    def __init__(self, token: str, ig_user_id: str, abrir=urllib.request.urlopen, esperar=time.sleep):
        self.token = token
        self.ig_user_id = ig_user_id
        self._abrir = abrir
        self._esperar = esperar

    def _pedir(self, caminho: str, corpo: dict) -> dict:
        corpo = {**corpo, "access_token": self.token}
        pedido = urllib.request.Request(
            f"{BASE}/{caminho}",
            data=urllib.parse.urlencode(corpo).encode(),
            headers={"User-Agent": "estudio-automatico/1.0"},
            method="POST",
        )
        with self._abrir(pedido, timeout=60) as resposta:
            return json.load(resposta)

    def _status(self, creation_id: str) -> str:
        pedido = urllib.request.Request(
            f"{BASE}/{creation_id}?fields=status_code&access_token={self.token}",
            headers={"User-Agent": "estudio-automatico/1.0"},
        )
        with self._abrir(pedido, timeout=30) as resposta:
            return json.load(resposta)["status_code"]

    def _esperar_pronto(self, creation_id: str):
        status = None
        for _ in range(TENTATIVAS_STATUS):
            status = self._status(creation_id)
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"Instagram recusou a mídia {creation_id} (status ERROR)")
            self._esperar(INTERVALO_STATUS_S)
        raise RuntimeError(f"mídia {creation_id} não ficou pronta a tempo (status ainda {status})")

    def publicar_reels(self, video_url: str, legenda: str) -> PostPublicado:
        criado = self._pedir(f"{self.ig_user_id}/media", {
            "media_type": "REELS", "video_url": video_url, "caption": legenda,
        })
        self._esperar_pronto(criado["id"])
        publicado = self._pedir(f"{self.ig_user_id}/media_publish", {"creation_id": criado["id"]})
        return PostPublicado(publicado["id"])

    def publicar_carrossel(self, image_urls: list[str], legenda: str) -> PostPublicado:
        if not 2 <= len(image_urls) <= 10:
            raise ValueError(f"carrossel precisa de 2 a 10 imagens, recebeu {len(image_urls)}")
        filhos = [
            self._pedir(f"{self.ig_user_id}/media", {"image_url": url, "is_carousel_item": "true"})["id"]
            for url in image_urls
        ]
        criado = self._pedir(f"{self.ig_user_id}/media", {
            "media_type": "CAROUSEL", "children": ",".join(filhos), "caption": legenda,
        })
        self._esperar_pronto(criado["id"])
        publicado = self._pedir(f"{self.ig_user_id}/media_publish", {"creation_id": criado["id"]})
        return PostPublicado(publicado["id"])

    def _ler(self, caminho: str, **consulta) -> dict:
        consulta = {**consulta, "access_token": self.token}
        pedido = urllib.request.Request(
            f"{BASE}/{caminho}?{urllib.parse.urlencode(consulta)}",
            headers={"User-Agent": "estudio-automatico/1.0"},
        )
        with self._abrir(pedido, timeout=30) as resposta:
            return json.load(resposta)

    def comentarios_recentes(self, quantas_midias: int = 10) -> list[dict]:
        """Comentários das últimas mídias: id, texto, usuário e hora. Só olha mídia com comentário."""
        midias = self._ler(f"{self.ig_user_id}/media", fields="id,comments_count", limit=quantas_midias)["data"]
        comentarios = []
        for midia in midias:
            if not midia.get("comments_count"):
                continue
            achados = self._ler(f"{midia['id']}/comments", fields="id,text,username,timestamp", limit=50)
            comentarios += [{**c, "midia_id": midia["id"]} for c in achados.get("data", [])]
        return comentarios

    def responder_comentario(self, comment_id: str, texto: str) -> dict:
        """Resposta privada (DM) a um comentário. A Meta aceita uma por comentário, em até 7 dias."""
        corpo = json.dumps({"recipient": {"comment_id": comment_id}, "message": {"text": texto}}).encode()
        pedido = urllib.request.Request(
            f"{BASE}/{self.ig_user_id}/messages?access_token={urllib.parse.quote(self.token)}",
            data=corpo,
            headers={"User-Agent": "estudio-automatico/1.0", "Content-Type": "application/json"},
            method="POST",
        )
        with self._abrir(pedido, timeout=60) as resposta:
            return json.load(resposta)

    def responder_publico(self, comment_id: str, texto: str) -> dict:
        """Resposta pública embaixo do comentário (ex.: "te mandei no direct")."""
        return self._pedir(f"{comment_id}/replies", {"message": texto})
