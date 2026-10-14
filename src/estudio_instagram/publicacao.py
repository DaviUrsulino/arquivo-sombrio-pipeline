"""Publica Reels e carrossel no Instagram via Publora (publora.com).

Evita a própria Instagram Graph API: a Publora já tem o app da Meta aprovado, então
conectar uma conta é só um login OAuth, sem precisar verificar telefone de novo.

Fluxo (igual para Reels e carrossel): cria o post como rascunho, faz upload de cada
arquivo de mídia (recebe uma URL assinada do S3, envia o arquivo com PUT), depois
publica ou agenda.
"""

import json
import mimetypes
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

BASE = "https://api.publora.com/api/v1"


@dataclass(frozen=True)
class PostPublicado:
    post_group_id: str
    agendado_para: str | None


class Publora:
    def __init__(self, chave: str, canal: str, abrir=urllib.request.urlopen):
        self.chave = chave
        self.canal = canal  # formato "instagram-xxxxx"
        self._abrir = abrir

    def _pedir(self, caminho: str, corpo: dict, metodo: str = "POST") -> dict:
        pedido = urllib.request.Request(
            f"{BASE}/{caminho}",
            data=json.dumps(corpo).encode(),
            headers={"x-publora-key": self.chave, "Content-Type": "application/json", "User-Agent": "estudio-automatico/1.0"},
            method=metodo,
        )
        with self._abrir(pedido, timeout=60) as resposta:
            return json.load(resposta)

    def criar_rascunho(self, legenda: str) -> str:
        """Cria o post (sem mídia ainda) e devolve o postGroupId."""
        resposta = self._pedir("create-post", {"content": legenda, "platforms": [self.canal]})
        return resposta["postGroupId"]

    def _enviar_arquivo(self, arquivo: Path, tipo: Literal["image", "video"], post_group_id: str):
        tipo_conteudo = mimetypes.guess_type(arquivo.name)[0] or ("video/mp4" if tipo == "video" else "image/jpeg")
        assinada = self._pedir("get-upload-url", {
            "fileName": arquivo.name, "contentType": tipo_conteudo, "type": tipo, "postGroupId": post_group_id,
        })
        pedido = urllib.request.Request(
            assinada["uploadUrl"], data=arquivo.read_bytes(),
            headers={"Content-Type": tipo_conteudo}, method="PUT",
        )
        with self._abrir(pedido, timeout=300):
            pass

    def _ativar(self, post_group_id: str, *, agora: bool, quando: str | None) -> PostPublicado:
        corpo = {"status": "scheduled", "scheduledTime": quando} if not agora else {"status": "scheduled", "publishNow": True}
        self._pedir(f"update-post/{post_group_id}", corpo, metodo="PUT")
        return PostPublicado(post_group_id, quando)

    def publicar_reels(self, video: Path, legenda: str, *, agora: bool = False, quando: str | None = None) -> PostPublicado:
        post_group_id = self._pedir("create-post", {
            "content": legenda, "platforms": [self.canal],
            "platformSettings": {"instagram": {"videoType": "REELS"}},
        })["postGroupId"]
        self._enviar_arquivo(video, "video", post_group_id)
        return self._ativar(post_group_id, agora=agora, quando=quando)

    def publicar_carrossel(self, slides: list[Path], legenda: str, *, agora: bool = False, quando: str | None = None) -> PostPublicado:
        if not 2 <= len(slides) <= 10:
            raise ValueError(f"carrossel precisa de 2 a 10 imagens, recebeu {len(slides)}")
        post_group_id = self.criar_rascunho(legenda)
        for slide in slides:
            self._enviar_arquivo(slide, "image", post_group_id)
        return self._ativar(post_group_id, agora=agora, quando=quando)
