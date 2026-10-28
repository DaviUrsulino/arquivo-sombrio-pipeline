from src.estudio_instagram.estudo_animacao import escolher


def _p(dono, cod, v, tipo="Video"):
    return {"ownerUsername": dono, "shortCode": cod, "videoPlayCount": v, "type": tipo, "videoUrl": "x"}


def test_escolhe_pelo_desempenho_relativo_ao_perfil():
    posts = [_p("grande", "g1", 10000), _p("grande", "g2", 10000), _p("pequeno", "p1", 100), _p("pequeno", "p2", 900)]
    assert escolher(posts, 1)[0]["shortCode"] == "p2"


def test_ignora_foto():
    assert escolher([_p("a", "f", 999, tipo="Image")]) == []
