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
import urllib.error
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
        try:
            with self._abrir(pedido, timeout=60) as resposta:
                return json.load(resposta)
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode(errors="replace")[:400].replace(self.token, "[token]")
            raise RuntimeError(f"Instagram recusou {caminho} (HTTP {erro.code}): {detalhe}") from erro

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

    def publicar_reels(self, video_url: str, legenda: str, teste: bool = False, colaboradores: list[str] | None = None) -> PostPublicado:
        """`teste=True` publica como Trial Reel: vai primeiro só pra quem não segue e o Instagram promove pros
        seguidores sozinho se performar (SS_PERFORMANCE). Só existe pra conta com 1.000+ seguidores.

        `colaboradores`: até 3 @ (sem o @) convidados pra collab; o post aparece no perfil deles quando aceitam."""
        corpo = {"media_type": "REELS", "video_url": video_url, "caption": legenda}
        if colaboradores:
            corpo["collaborators"] = json.dumps([c.lstrip("@") for c in colaboradores[:3]])
        if teste:
            corpo["trial_params"] = json.dumps({"graduation_strategy": "SS_PERFORMANCE"})
        criado = self._pedir(f"{self.ig_user_id}/media", corpo)
        self._esperar_pronto(criado["id"])
        publicado = self._pedir(f"{self.ig_user_id}/media_publish", {"creation_id": criado["id"]})
        return PostPublicado(publicado["id"])

    def publicar_story(self, video_url: str) -> PostPublicado:
        """Story de vídeo (9:16, até 60 s). A API não aceita figurinha de link nem enquete; só a mídia."""
        criado = self._pedir(f"{self.ig_user_id}/media", {"media_type": "STORIES", "video_url": video_url})
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

    def comentarios_recentes(self, quantas_midias: int = 80) -> list[dict]:
        """Comentários das últimas mídias: id, texto, usuário e hora. Só olha mídia com comentário.

        80 cobre a janela de 7 dias da resposta privada (JANELA em respondedor.py) mesmo na
        cadência atual de 5 rodadas/dia (10 mídias/dia) — com 10 fixo, um post de ontem com
        comentário já saía da lista assim que o dia seguinte publicava mais mídia nova.
        Listar mídia é 1 chamada só (barato); só gasta chamada extra em mídia que tem comentário.
        """
        midias = self._ler(f"{self.ig_user_id}/media", fields="id,comments_count", limit=quantas_midias)["data"]
        comentarios = []
        for midia in midias:
            if not midia.get("comments_count"):
                continue
            achados = self._ler(f"{midia['id']}/comments", fields="id,text,username,timestamp,from", limit=50)
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

    def enviar_mensagem(self, igsid: str, texto: str) -> dict:
        """DM normal para quem já escreveu para a conta (janela de 24 h depois da última mensagem da pessoa)."""
        corpo = json.dumps({"recipient": {"id": igsid}, "message": {"text": texto}}).encode()
        pedido = urllib.request.Request(
            f"{BASE}/{self.ig_user_id}/messages?access_token={urllib.parse.quote(self.token)}",
            data=corpo,
            headers={"User-Agent": "estudio-automatico/1.0", "Content-Type": "application/json"},
            method="POST",
        )
        with self._abrir(pedido, timeout=60) as resposta:
            return json.load(resposta)

    def conversas_recentes(self, limite: int = 30) -> list[dict]:
        """Conversas de DM mais recentes: [{"usuario_id", "mensagens": [{"de", "texto", "hora"}]}] (mais nova primeiro)."""
        dados = self._ler(
            f"{self.ig_user_id}/conversations", platform="instagram", limit=limite,
            fields="participants,messages.limit(4){from,message,created_time}",
        )
        if not hasattr(self, "_meu_username"):
            self._meu_username = self._ler("me", fields="username").get("username")
        conversas = []
        for conversa in dados.get("data", []):
            outros = [p["id"] for p in conversa.get("participants", {}).get("data", [])
                      if p.get("username") != self._meu_username]
            if not outros:
                continue
            mensagens = [
                {"de": (m.get("from") or {}).get("id"), "texto": m.get("message") or "", "hora": m.get("created_time")}
                for m in conversa.get("messages", {}).get("data", [])
            ]
            conversas.append({"usuario_id": outros[0], "mensagens": mensagens})
        return conversas

    def segue_a_conta(self, igsid: str) -> bool | None:
        """A pessoa segue a conta? None se a API não souber (ex.: ela ainda não escreveu, erro 230)."""
        try:
            dados = self._ler(igsid, fields="is_user_follow_business")
        except urllib.error.HTTPError:
            return None
        valor = dados.get("is_user_follow_business")
        return valor if isinstance(valor, bool) else None

    def responder_publico(self, comment_id: str, texto: str) -> dict:
        """Resposta pública embaixo do comentário (ex.: "te mandei no direct")."""
        return self._pedir(f"{comment_id}/replies", {"message": texto})

    def seguidores(self) -> int:
        return int(self._ler(self.ig_user_id, fields="followers_count").get("followers_count", 0))

    def publicados_nas_ultimas_24h(self) -> int:
        """Quantos posts feitos pela API a conta já usou na janela de 24 h (limite oficial: 100)."""
        dados = self._ler(f"{self.ig_user_id}/content_publishing_limit", fields="quota_usage")
        return int(dados["data"][0]["quota_usage"])
