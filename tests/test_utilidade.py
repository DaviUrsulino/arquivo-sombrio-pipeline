"""Vídeo de utilidade (10/11): a promessa é da vida de quem assiste, a ferramenta é só o meio."""
from datetime import datetime, timedelta, timezone

from src.estudio_instagram import utilidade


def test_uma_por_dia_e_sem_repetir_utilidade():
    agora = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    assert utilidade.precisa({}, agora)
    feita = {f"{utilidade.PREFIXO}achar-vaga-remota": {"quando": (agora - timedelta(hours=3)).isoformat()}}
    assert not utilidade.precisa(feita, agora)
    assert utilidade.proxima(feita)[0] != "achar-vaga-remota"


def test_nao_conta_historia_como_utilidade():
    """Séries e histórias usam o mesmo arquivo de estado; cada frente só conta o seu prefixo."""
    agora = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    outras = {"tech:knight-capital": {"quando": (agora - timedelta(hours=1)).isoformat()},
              "cotidiano:porta-que-nao-abre": {"quando": (agora - timedelta(hours=1)).isoformat()}}
    assert utilidade.precisa(outras, agora)


def test_toda_promessa_fala_do_espectador_nao_da_ferramenta():
    """O erro medido nas referências é a promessa virar 'a ferramenta faz X'. Nenhuma pode citar o nosso mundo."""
    proibidas = ("claude", "github", "agente", "skill", "repositório", "repositorio", "prompt", "deploy")
    for slug, repo, promessa in utilidade.UTILIDADES:
        assert promessa[0].islower(), f"{slug}: promessa completa a frase, começa minúscula (siglas no meio podem)"
        assert not any(p in promessa for p in proibidas), f"{slug}: promessa de nicho ({promessa})"
        assert len(promessa.split()) <= 16, f"{slug}: promessa longa demais"
        assert "/" in repo, slug


def test_extra_leva_a_promessa_pro_roteirista():
    texto = utilidade.extra("tirar o fundo de qualquer foto sem pagar aplicativo")
    assert "tirar o fundo de qualquer foto sem pagar aplicativo" in texto
    assert "__PROMESSA__" not in texto
