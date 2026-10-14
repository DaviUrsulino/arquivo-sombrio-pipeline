import io
import json

import pytest

from src.estudio_instagram.publicacao import Publora


class RespostaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class AbridorFalso:
    """Dublê de urlopen: devolve a próxima resposta da fila e registra cada pedido feito."""

    def __init__(self, respostas: list[bytes]):
        self.respostas = list(respostas)
        self.pedidos = []

    def __call__(self, pedido, timeout=None):
        self.pedidos.append(pedido)
        return RespostaFalsa(self.respostas.pop(0))


def _json(d):
    return json.dumps(d).encode()


def test_reels_cria_posta_video_e_ativa_na_ordem_certa(tmp_path):
    video = tmp_path / "reels.mp4"
    video.write_bytes(b"video-falso")
    abrir = AbridorFalso([
        _json({"postGroupId": "abc123"}),
        _json({"uploadUrl": "https://s3.fake/upload", "fileUrl": "https://s3.fake/reels.mp4", "mediaId": "m1"}),
        b"",
        _json({"success": True}),
    ])
    publora = Publora("chave-x", "instagram-9", abrir=abrir)

    resultado = publora.publicar_reels(video, "legenda do reels", agora=True)

    assert resultado.post_group_id == "abc123"
    caminhos = [p.full_url for p in abrir.pedidos]
    assert caminhos == [
        "https://api.publora.com/api/v1/create-post",
        "https://api.publora.com/api/v1/get-upload-url",
        "https://s3.fake/upload",
        "https://api.publora.com/api/v1/update-post/abc123",
    ]
    criacao = json.loads(abrir.pedidos[0].data)
    assert criacao == {"content": "legenda do reels", "platforms": ["instagram-9"],
                        "platformSettings": {"instagram": {"videoType": "REELS"}}}
    upload = abrir.pedidos[2]
    assert upload.data == b"video-falso" and upload.get_method() == "PUT"
    ativacao = json.loads(abrir.pedidos[3].data)
    assert ativacao == {"status": "scheduled", "publishNow": True}


def test_reels_manda_a_chave_no_cabecalho(tmp_path):
    video = tmp_path / "reels.mp4"
    video.write_bytes(b"x")
    abrir = AbridorFalso([
        _json({"postGroupId": "g"}), _json({"uploadUrl": "https://s3.fake/u", "fileUrl": "", "mediaId": ""}),
        b"", _json({}),
    ])
    Publora("minha-chave", "instagram-9", abrir=abrir).publicar_reels(video, "x", agora=True)
    assert abrir.pedidos[0].get_header("X-publora-key") == "minha-chave"


def test_carrossel_envia_cada_slide_em_ordem(tmp_path):
    slides = []
    for i in range(3):
        slide = tmp_path / f"slide-{i}.png"
        slide.write_bytes(f"img{i}".encode())
        slides.append(slide)
    respostas = [_json({"postGroupId": "g1"})]
    for i in range(3):
        respostas += [_json({"uploadUrl": f"https://s3.fake/{i}", "fileUrl": "", "mediaId": str(i)}), b""]
    respostas.append(_json({}))
    abrir = AbridorFalso(respostas)

    Publora("chave", "instagram-9", abrir=abrir).publicar_carrossel(slides, "legenda", quando="2026-11-01T10:00:00Z")

    urls_upload = [p.full_url for p in abrir.pedidos if p.full_url.startswith("https://s3.fake/")]
    assert urls_upload == ["https://s3.fake/0", "https://s3.fake/1", "https://s3.fake/2"]
    ativacao = json.loads(abrir.pedidos[-1].data)
    assert ativacao == {"status": "scheduled", "scheduledTime": "2026-11-01T10:00:00Z"}


@pytest.mark.parametrize("n", [0, 1, 11])
def test_carrossel_recusa_fora_do_limite_do_instagram(tmp_path, n):
    slides = [tmp_path / f"s{i}.png" for i in range(n)]
    for s in slides:
        s.write_bytes(b"x")
    with pytest.raises(ValueError, match="2 a 10"):
        Publora("chave", "instagram-9", abrir=AbridorFalso([])).publicar_carrossel(slides, "legenda")
