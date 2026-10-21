"""Dispara as rodadas de post do Instagram na hora certa (horário de Brasília).

O agendador (cron) do GitHub atrasa horas ou nem dispara: em 2026-10-19 só 2 das 5 rodadas do dia rodaram.
Por isso um workflow (instagram_maestro.yml) fica em laço olhando o relógio e, quando chega a hora de uma rodada,
dispara o `pipeline_instagram.yml` com `gh workflow run`. O que já foi disparado no dia fica em
`pautas/maestro.json`, para nunca repetir rodada.

Regras:
- Cada rodada tem uma tolerância de atraso: se o maestro acordar muito depois da hora, a rodada é dada como
  perdida em vez de empilhar várias de uma vez (o Instagram bloqueia ações em rajada: "action is blocked").
- Nunca dispara duas rodadas com menos de `INTERVALO_MIN_MIN` minutos de diferença.
- Se a pausa de segurança (`pautas/pausa.json`) estiver ativa, não dispara nada.

Uso:
    python -m src.estudio_instagram.maestro --minutos 340 --intervalo 120 --commit
    python -m src.estudio_instagram.maestro --simular
"""

import argparse
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import pausa

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO = RAIZ / "pautas" / "maestro.json"
BRASILIA = timezone(timedelta(hours=-3))
# (hora de Brasília, formato). Cada rodada posta 1 Reels + 1 carrossel: 4 rodadas = 8 posts por dia.
# Horários nos picos de 07-09h, 12-13h e 18-21h (pesquisa de 2026); o freio de 10 posts/24 h segue valendo.
# Modo seguro (2026-10-19): o Instagram devolveu "action is blocked" com 5 rodadas por dia, então são poucas e espaçadas.
RODADAS = [("08:00", "pixel2"), ("12:00", "pixel2"), ("18:30", "venda"), ("21:00", "lista")]
# Pauta pronta e aprovada que substitui o formato de uma rodada: {"AAAA-MM-DD": {"HH:MM": "caminho"}}.
PAUTAS_DO_DIA = {}
# Banco de vídeos: pautas prontas e aprovadas em pautas/viral/fila/. A rodada FILA_RODADA de cada dia usa a próxima
# que ainda não saiu (em ordem de nome); sem nada na fila, segue o formato normal da rodada.
FILA = RAIZ / "pautas" / "viral" / "fila"
FILA_RODADA = "12:00"  # horário de ouro: o vídeo mais forte do banco sai no pico do meio-dia
TOLERANCIA_ATRASO = timedelta(hours=2)
INTERVALO_MIN_MIN = 120  # nunca duas rodadas em menos de 2 horas


def _hora(dia: str, hhmm: str) -> datetime:
    return datetime.fromisoformat(f"{dia}T{hhmm}:00").replace(tzinfo=BRASILIA)


def decidir(agora: datetime, estado: dict) -> tuple[str | None, dict]:
    """Devolve (formato a disparar agora ou None, estado novo). Não faz nenhuma chamada externa."""
    agora = agora.astimezone(BRASILIA)
    dia = agora.date().isoformat()
    if estado.get("dia") != dia:
        estado = {"dia": dia, "feitos": {}, "fila_usadas": estado.get("fila_usadas", []),
                  "ultimo_disparo": estado.get("ultimo_disparo")}
    feitos = dict(estado["feitos"])
    ultimo = estado.get("ultimo_disparo")
    seguro = not ultimo or agora - datetime.fromisoformat(ultimo) >= timedelta(minutes=INTERVALO_MIN_MIN)

    escolhido = None
    for hhmm, formato in RODADAS:
        if hhmm in feitos:
            continue
        previsto = _hora(dia, hhmm)
        if previsto > agora:
            break
        if agora - previsto > TOLERANCIA_ATRASO:
            feitos[hhmm] = "perdida"
            continue
        if seguro and escolhido is None:
            pronta = PAUTAS_DO_DIA.get(dia, {}).get(hhmm)
            escolhido = (hhmm, f"pauta:{pronta}" if pronta else formato)
            feitos[hhmm] = f"disparada {agora.strftime('%H:%M')}"
    novo = {"dia": dia, "feitos": feitos, "ultimo_disparo": estado.get("ultimo_disparo"),
            "fila_usadas": estado.get("fila_usadas", [])}
    if escolhido:
        novo["ultimo_disparo"] = agora.isoformat(timespec="seconds")
    return (escolhido[1] if escolhido else None), novo


def proxima_da_fila(usadas: list[str], pasta: Path = FILA) -> str | None:
    """Caminho (relativo à raiz) da próxima pauta do banco que ainda não foi usada, ou None."""
    for arquivo in sorted(pasta.glob("*.json")) if pasta.exists() else []:
        relativo = arquivo.relative_to(RAIZ).as_posix()
        if relativo not in usadas:
            return relativo
    return None


def _ler() -> dict:
    return json.loads(ARQUIVO.read_text(encoding="utf-8")) if ARQUIVO.exists() else {}


def _gravar(estado: dict, commitar: bool):
    ARQUIVO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    if not commitar:
        return
    try:
        subprocess.run(["git", "add", str(ARQUIVO)], cwd=RAIZ, check=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=RAIZ).returncode == 0:
            return
        subprocess.run(["git", "commit", "-m", "chore: registra rodada do maestro [skip ci]"], cwd=RAIZ, check=True)
        subprocess.run(["git", "pull", "--rebase", "-q"], cwd=RAIZ, check=True)
        subprocess.run(["git", "push", "-q"], cwd=RAIZ, check=True)
    except subprocess.CalledProcessError as erro:
        print(f"não consegui gravar no git ({erro}); sigo, o estado local vale")


def disparar(formato: str):
    if formato.startswith("pauta:"):
        entrada = ["-f", f"pauta={formato.removeprefix('pauta:')}"]
    else:
        entrada = ["-f", f"formato={formato}"]
    subprocess.run(
        ["gh", "workflow", "run", "pipeline_instagram.yml", *entrada, "-f", "publicar=true"],
        cwd=RAIZ, check=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--minutos", type=float, default=0, help="fica em laço por tantos minutos (0 = uma passada)")
    parser.add_argument("--intervalo", type=int, default=120, help="segundos entre olhadas no relógio")
    parser.add_argument("--commit", action="store_true", help="grava o estado no git")
    parser.add_argument("--simular", action="store_true", help="só mostra o que faria")
    args = parser.parse_args()
    fim = time.monotonic() + args.minutos * 60
    while True:
        estado = _ler()
        formato, novo = decidir(datetime.now(BRASILIA), estado)
        if formato and pausa.ativa():
            print(f"pausa de segurança ativa ({pausa.motivo()}); não disparo a rodada {formato}", flush=True)
            formato = None
            novo = estado
        if formato and not formato.startswith("pauta:"):
            nova_rodada = [h for h in novo["feitos"] if h not in (estado["feitos"] if estado.get("dia") == novo["dia"] else {})]
            subprocess.run(["git", "pull", "--rebase", "-q"], cwd=RAIZ, check=False)  # pega pautas novas do banco
            usadas = novo.get("fila_usadas", estado.get("fila_usadas", []))
            da_fila = proxima_da_fila(usadas) if FILA_RODADA in nova_rodada else None
            if da_fila:
                formato = f"pauta:{da_fila}"
                novo["fila_usadas"] = [*usadas, da_fila]
            elif usadas:
                novo["fila_usadas"] = usadas
        if formato:
            print(f"hora de uma rodada ({formato}); estado: {novo['feitos']}", flush=True)
            if not args.simular:
                try:
                    disparar(formato)
                except subprocess.CalledProcessError as erro:
                    print(f"falhou ao disparar ({erro}); tento de novo na próxima olhada")
                    time.sleep(args.intervalo)
                    continue
        if novo != estado and not args.simular:
            _gravar(novo, args.commit)
        if not formato:
            print(f"nada a disparar agora; feitos hoje: {novo['feitos']}", flush=True)
        if time.monotonic() + args.intervalo >= fim:
            break
        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
