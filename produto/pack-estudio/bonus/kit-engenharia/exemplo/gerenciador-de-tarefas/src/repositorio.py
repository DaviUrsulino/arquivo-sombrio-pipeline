"""Persistência SQLite (ADR-0001). SQL sempre parametrizado."""
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional

from .dominio import Tarefa


class RepositorioSqlite:
    def __init__(self, caminho: str):
        self._con = sqlite3.connect(caminho, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._con:
            # AUTOINCREMENT: id de tarefa apagada nunca é reutilizado
            self._con.execute(
                "CREATE TABLE IF NOT EXISTS tarefas ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL,"
                "concluida INTEGER NOT NULL DEFAULT 0, criada_em TEXT NOT NULL)"
            )

    @staticmethod
    def _t(linha) -> Tarefa:
        return Tarefa(linha[0], linha[1], bool(linha[2]), linha[3])

    def adicionar(self, titulo: str) -> Tarefa:
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock, self._con:
            cur = self._con.execute(
                "INSERT INTO tarefas (titulo, concluida, criada_em) VALUES (?, 0, ?)", (titulo, agora)
            )
            return Tarefa(cur.lastrowid, titulo, False, agora)

    def listar(self, concluida: Optional[bool]) -> list[Tarefa]:
        sql = "SELECT id, titulo, concluida, criada_em FROM tarefas"
        args: tuple = ()
        if concluida is not None:
            sql += " WHERE concluida = ?"
            args = (int(concluida),)
        with self._lock:
            return [self._t(r) for r in self._con.execute(sql + " ORDER BY id", args)]

    def obter(self, id: int) -> Optional[Tarefa]:
        with self._lock:
            r = self._con.execute(
                "SELECT id, titulo, concluida, criada_em FROM tarefas WHERE id = ?", (id,)
            ).fetchone()
        return self._t(r) if r else None

    def salvar(self, tarefa: Tarefa) -> None:
        with self._lock, self._con:
            self._con.execute(
                "UPDATE tarefas SET titulo = ?, concluida = ? WHERE id = ?",
                (tarefa.titulo, int(tarefa.concluida), tarefa.id),
            )

    def remover(self, id: int) -> bool:
        with self._lock, self._con:
            return self._con.execute("DELETE FROM tarefas WHERE id = ?", (id,)).rowcount > 0
