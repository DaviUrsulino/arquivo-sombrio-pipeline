from src.estudio_instagram.voz import EmCadeia, Narracao


class Falha:
    def sintetizar(self, t):
        raise RuntimeError("cota")


class Ok:
    def __init__(self, nome):
        self.nome = nome

    def sintetizar(self, t):
        return Narracao(self.nome.encode(), [])


def test_cadeia_usa_a_primeira_voz_que_funciona_pra_todas_as_falas():
    c = EmCadeia(Falha(), Falha(), Ok("gradium"), Ok("edge"))
    c.preparar(["a", "b"])
    assert c.sintetizar("a").audio_pcm == b"gradium" and c.sintetizar("b").audio_pcm == b"gradium"
