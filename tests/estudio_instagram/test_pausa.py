from datetime import datetime, timedelta, timezone

from src.estudio_instagram import pausa


def test_reconhece_o_bloqueio_do_instagram():
    msg = 'Instagram recusou x/media_publish (HTTP 403): {"error":{"message":"Application request limit reached","error_subcode":2207051}}'
    assert pausa.e_bloqueio(msg) and not pausa.e_bloqueio("HTTP 500 erro qualquer")


def test_pausa_dura_24h_e_depois_libera(tmp_path):
    arq = tmp_path / "pausa.json"
    agora = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    assert not pausa.ativa(agora, arq)
    pausa.ativar("bloqueio", agora, arq)
    assert pausa.ativa(agora + timedelta(hours=23), arq) and pausa.motivo(arq) == "bloqueio"
    assert not pausa.ativa(agora + timedelta(hours=25), arq)
