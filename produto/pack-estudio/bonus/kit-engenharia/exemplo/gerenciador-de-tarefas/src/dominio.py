"""Regra de negócio. Não conhece HTTP nem SQL."""
from dataclasses import dataclass, replace
from typing import Optional, Protocol

TITULO_MAX = 200


class ErroDominio(Exception):
    pass


class ErroValidacao(ErroDominio):
    pass


class ErroNaoEncontrado(ErroDominio):
    pass


@dataclass(frozen=True)
class Tarefa:
    id: int
    titulo: str
    concluida: bool
    criada_em: str


class RepositorioTarefas(Protocol):
    def adicionar(self, titulo: str) -> Tarefa: ...
    def listar(self, concluida: Optional[bool]) -> list[Tarefa]: ...
    def obter(self, id: int) -> Optional[Tarefa]: ...
    def salvar(self, tarefa: Tarefa) -> None: ...
    def remover(self, id: int) -> bool: ...


def validar_titulo(valor) -> str:
    if not isinstance(valor, str):
        raise ErroValidacao("titulo deve ser texto")
    titulo = valor.strip()
    if not titulo:
        raise ErroValidacao("titulo não pode ser vazio")
    if len(titulo) > TITULO_MAX:
        raise ErroValidacao(f"titulo excede {TITULO_MAX} caracteres")
    return titulo


class ServicoTarefas:
    def __init__(self, repo: RepositorioTarefas):
        self._repo = repo

    def criar(self, titulo) -> Tarefa:
        return self._repo.adicionar(validar_titulo(titulo))

    def listar(self, concluida: Optional[bool] = None) -> list[Tarefa]:
        return self._repo.listar(concluida)

    def obter(self, id: int) -> Tarefa:
        t = self._repo.obter(id)
        if t is None:
            raise ErroNaoEncontrado("tarefa não encontrada")
        return t

    def atualizar(self, id: int, campos: dict) -> Tarefa:
        if not campos or set(campos) - {"titulo", "concluida"}:
            raise ErroValidacao("informe titulo e/ou concluida (nenhum outro campo)")
        novo = {}
        if "titulo" in campos:
            novo["titulo"] = validar_titulo(campos["titulo"])
        if "concluida" in campos:
            if not isinstance(campos["concluida"], bool):
                raise ErroValidacao("concluida deve ser true ou false")
            novo["concluida"] = campos["concluida"]
        atual = self.obter(id)
        t = replace(atual, **novo)
        self._repo.salvar(t)
        return t

    def apagar(self, id: int) -> None:
        if not self._repo.remover(id):
            raise ErroNaoEncontrado("tarefa não encontrada")
