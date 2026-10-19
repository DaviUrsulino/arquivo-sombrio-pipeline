"""Freio de segurança: se o Instagram reclamar de excesso de atividade, tudo pausa por 24 horas.

Quando a Graph API devolve "Application request limit reached" / "action is blocked" (código 4, subcódigo 2207051),
insistir só piora. O pipeline grava `pautas/pausa.json` e o maestro e o próprio pipeline respeitam até a hora marcada.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parents[2] / "pautas" / "pausa.json"
SINAIS_DE_BLOQUEIO = ("2207051", "Application request limit reached", "action is blocked", "restrict certain activity")
HORAS = 24


def e_bloqueio(mensagem: str) -> bool:
    return any(sinal.lower() in mensagem.lower() for sinal in SINAIS_DE_BLOQUEIO)


def ativar(motivo: str, agora: datetime | None = None, arquivo: Path = ARQUIVO):
    agora = agora or datetime.now(timezone.utc)
    arquivo.write_text(json.dumps({
        "ate": (agora + timedelta(hours=HORAS)).isoformat(timespec="seconds"), "motivo": motivo[:300],
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def ativa(agora: datetime | None = None, arquivo: Path = ARQUIVO) -> bool:
    if not arquivo.exists():
        return False
    ate = datetime.fromisoformat(json.loads(arquivo.read_text(encoding="utf-8"))["ate"])
    return (agora or datetime.now(timezone.utc)) < ate


def motivo(arquivo: Path = ARQUIVO) -> str:
    return json.loads(arquivo.read_text(encoding="utf-8")).get("motivo", "") if arquivo.exists() else ""
