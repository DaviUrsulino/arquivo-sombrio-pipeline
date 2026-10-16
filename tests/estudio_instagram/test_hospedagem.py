import json
from types import SimpleNamespace

import pytest

from src.estudio_instagram.hospedagem import publicar


class ExecutorFalso:
    def __init__(self, assets, falha_no_upload=False):
        self.assets = assets
        self.falha_no_upload = falha_no_upload
        self.chamadas = []

    def __call__(self, args, capture_output=True, text=True):
        self.chamadas.append(args)
        if args[1:3] == ["release", "upload"]:
            if self.falha_no_upload:
                return SimpleNamespace(returncode=1, stdout="", stderr="release não encontrada")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if args[1:3] == ["release", "view"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"assets": self.assets}), stderr="")
        raise AssertionError(f"comando inesperado: {args}")


def test_publicar_sobe_arquivo_com_nome_pedido_e_devolve_url(tmp_path):
    arquivo = tmp_path / "video-original.mp4"
    arquivo.write_bytes(b"video")
    url_esperada = "https://github.com/x/y/releases/download/midia-publicacao/pauta-x-reels.mp4"
    executor = ExecutorFalso([{"name": "pauta-x-reels.mp4", "url": url_esperada}])

    url = publicar(arquivo, "pauta-x-reels.mp4", executar=executor)

    assert url == url_esperada
    upload_args = executor.chamadas[0]
    assert upload_args[:3] == ["gh", "release", "upload"]
    assert upload_args[3] == "midia-publicacao"
    assert upload_args[4].endswith("pauta-x-reels.mp4")


def test_publicar_propaga_erro_se_upload_falhar(tmp_path):
    arquivo = tmp_path / "x.mp4"
    arquivo.write_bytes(b"x")
    executor = ExecutorFalso([], falha_no_upload=True)
    with pytest.raises(RuntimeError, match="não encontrada"):
        publicar(arquivo, "x.mp4", executar=executor)
