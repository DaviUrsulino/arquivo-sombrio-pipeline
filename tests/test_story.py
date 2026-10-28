import subprocess

from src.estudio_instagram import story


def test_story_corta_o_gancho_e_poe_faixa(tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, check: chamadas.append(cmd))
    story.preparar(tmp_path / "r.mp4", tmp_path / "s.mp4")
    cmd = chamadas[0]
    assert cmd[cmd.index("-t") + 1] == str(story.DURACAO_S)
    assert story.FAIXA in cmd[cmd.index("-vf") + 1]
