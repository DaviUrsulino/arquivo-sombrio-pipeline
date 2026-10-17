import json
from datetime import datetime, timezone

from src.estudio_instagram.agendador import executar_vencidos
from src.estudio_instagram.graph_api import PostPublicado


class InstagramFalso:
    def __init__(self):
        self.chamadas = []

    def publicar_reels(self, video_url, legenda):
        self.chamadas.append((video_url, legenda))
        return PostPublicado(media_id=f"m{len(self.chamadas)}")


def _escrever(tmp_path, itens):
    arquivo = tmp_path / "agendadas.json"
    arquivo.write_text(json.dumps(itens), encoding="utf-8")
    return arquivo


def _item(postar_apos, **extra):
    return {"video_url": "https://x/v.mp4", "legenda": "oi", "postar_apos": postar_apos, **extra}


AGORA = datetime(2026, 10, 17, 22, 0, tzinfo=timezone.utc)


def test_publica_o_vencido_e_marca_como_publicado(tmp_path):
    arquivo = _escrever(tmp_path, [_item("2026-10-17T21:00:00+00:00")])
    ig = InstagramFalso()
    publicados = executar_vencidos(arquivo, ig, AGORA)
    assert len(publicados) == 1
    assert ig.chamadas == [("https://x/v.mp4", "oi")]
    salvo = json.loads(arquivo.read_text(encoding="utf-8"))[0]
    assert salvo["publicado"] is True and salvo["media_id"] == "m1"


def test_nao_publica_antes_da_hora(tmp_path):
    arquivo = _escrever(tmp_path, [_item("2026-10-17T23:00:00+00:00")])
    ig = InstagramFalso()
    assert executar_vencidos(arquivo, ig, AGORA) == []
    assert ig.chamadas == []


def test_nao_repete_o_que_ja_foi_publicado(tmp_path):
    arquivo = _escrever(tmp_path, [_item("2026-10-17T21:00:00+00:00", publicado=True)])
    ig = InstagramFalso()
    assert executar_vencidos(arquivo, ig, AGORA) == []
    assert ig.chamadas == []


def test_hora_sem_fuso_conta_como_utc(tmp_path):
    arquivo = _escrever(tmp_path, [_item("2026-10-17T21:00:00")])
    assert len(executar_vencidos(arquivo, InstagramFalso(), AGORA)) == 1
