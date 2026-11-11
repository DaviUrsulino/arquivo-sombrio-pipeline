"""Fórmula do Reels de 558 mil views que o Davi mandou pedindo 'faz igual' (@_aighostlab, DfiRG6Dpn5T):
assunto gigante + ferramenta que serve a quem curte o assunto + legenda de UMA linha que é só o CTA."""
from datetime import datetime, timedelta, timezone

from src.estudio_instagram import assunto_ferramenta as af


def test_legenda_e_uma_linha_so_com_o_pedido():
    """A do modelo é 'Comenta CORTES e recebe o sistema que faz os cortes do GTA 6 por você'. Uma linha, um pedido."""
    l = af.legenda("corta sozinho os melhores momentos de uma gravação longa", "CLIPE")
    assert l.count("\n") == 0
    assert l.startswith("Comenta CLIPE")
    assert "#" not in l and "salva" not in l.lower() and "manda pro amigo" not in l.lower()


def test_promessa_fala_com_quem_curte_o_assunto_nao_com_dev():
    proibidas = ("claude", "github", "repositório", "agente", "prompt", "terminal", "deploy")
    for slug, assunto, repo, palavra, promessa in af.PARES:
        assert not any(p in promessa.lower() for p in proibidas), f"{slug}: promessa de nicho"
        assert not any(p in assunto.lower() for p in proibidas), f"{slug}: assunto de nicho"
        assert palavra.isupper() and palavra.isalpha() and len(palavra) <= 8, f"{slug}: palavra ruim"
        assert "/" in repo, slug


def test_um_por_dia_sem_repetir_par():
    agora = datetime(2026, 11, 11, 3, tzinfo=timezone.utc)
    assert af.precisa({}, agora)
    feito = {f"{af.PREFIXO}cortes-de-gameplay": {"quando": (agora - timedelta(hours=2)).isoformat()}}
    assert not af.precisa(feito, agora)
    assert af.proximo(feito)[0] != "cortes-de-gameplay"


def test_nao_confunde_com_as_outras_frentes():
    agora = datetime(2026, 11, 11, 3, tzinfo=timezone.utc)
    outras = {"utilidade:x": {"quando": (agora - timedelta(hours=1)).isoformat()},
              "curiosidade:y": {"quando": (agora - timedelta(hours=1)).isoformat()}}
    assert af.precisa(outras, agora)


def test_extra_leva_assunto_promessa_e_palavra_pro_roteirista():
    t = af.extra("GTA 6 e os clipes de jogo", "corta os melhores momentos", "CLIPE")
    assert "GTA 6 e os clipes de jogo" in t and "corta os melhores momentos" in t and "CLIPE" in t
    assert "__ASSUNTO__" not in t and "__PROMESSA__" not in t and "__PALAVRA__" not in t
