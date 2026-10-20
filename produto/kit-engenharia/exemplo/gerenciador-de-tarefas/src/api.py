"""Camada HTTP: traduz HTTP <-> ServicoTarefas (ADR-0002)."""
import hmac
import json
import os
import re
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .dominio import ErroNaoEncontrado, ErroValidacao, ServicoTarefas
from .repositorio import RepositorioSqlite

CORPO_MAX = 4096
ROTA_ITEM = re.compile(r"^/tarefas/(\d{1,18})$")


class _Resposta(Exception):
    def __init__(self, status, corpo=None):
        self.status, self.corpo = status, corpo


def _handler_para(servico: ServicoTarefas, token):
    class Handler(BaseHTTPRequestHandler):
        server_version = "Tarefas"
        sys_version = ""

        def log_message(self, *a):  # sem log de cabeçalhos/corpo (pode conter token)
            pass

        def _enviar(self, status, corpo=None):
            dados = b"" if corpo is None else json.dumps(corpo, ensure_ascii=False).encode()
            self.send_response(status)
            if dados:
                self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(dados)

        def _autenticar(self):
            if token is None:
                return
            recebido = self.headers.get("Authorization", "")
            if not hmac.compare_digest(recebido.encode(), ("Bearer " + token).encode()):
                raise _Resposta(401, {"erro": "não autorizado"})

        def _corpo_json(self):
            bruto = self.headers.get("Content-Length")
            if bruto is None:
                raise _Resposta(411, {"erro": "Content-Length obrigatório"})
            if not bruto.isdigit():
                raise _Resposta(400, {"erro": "Content-Length inválido"})
            n = int(bruto)
            if n > CORPO_MAX:
                raise _Resposta(413, {"erro": f"corpo excede {CORPO_MAX} bytes"})
            try:
                obj = json.loads(self.rfile.read(n).decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                raise _Resposta(400, {"erro": "JSON inválido"})
            if not isinstance(obj, dict):
                raise _Resposta(400, {"erro": "corpo deve ser um objeto JSON"})
            return obj

        def _tratar(self, metodo):
            try:
                self._autenticar()
                url = urlsplit(self.path)
                if url.path == "/tarefas":
                    self._colecao(metodo, url)
                else:
                    m = ROTA_ITEM.match(url.path)
                    if not m:
                        raise _Resposta(404, {"erro": "rota não encontrada"})
                    self._item(metodo, int(m.group(1)))
            except _Resposta as r:
                self._enviar(r.status, r.corpo)
            except ErroValidacao as e:
                self._enviar(400, {"erro": str(e)})
            except ErroNaoEncontrado as e:
                self._enviar(404, {"erro": str(e)})
            except Exception:
                self._enviar(500, {"erro": "erro interno"})

        def _colecao(self, metodo, url):
            if metodo == "GET":
                q = parse_qs(url.query).get("concluida")
                filtro = None
                if q is not None:
                    if q[0] not in ("true", "false"):
                        raise _Resposta(400, {"erro": "concluida deve ser true ou false"})
                    filtro = q[0] == "true"
                self._enviar(200, [asdict(t) for t in servico.listar(filtro)])
            elif metodo == "POST":
                self._enviar(201, asdict(servico.criar(self._corpo_json().get("titulo"))))
            else:
                raise _Resposta(405, {"erro": "método não permitido"})

        def _item(self, metodo, id):
            if metodo == "GET":
                self._enviar(200, asdict(servico.obter(id)))
            elif metodo == "PATCH":
                self._enviar(200, asdict(servico.atualizar(id, self._corpo_json())))
            elif metodo == "DELETE":
                servico.apagar(id)
                self._enviar(204)
            else:
                raise _Resposta(405, {"erro": "método não permitido"})

        def do_GET(self): self._tratar("GET")
        def do_POST(self): self._tratar("POST")
        def do_PATCH(self): self._tratar("PATCH")
        def do_DELETE(self): self._tratar("DELETE")
        def do_PUT(self): self._tratar("PUT")

    return Handler


def criar_servidor(servico: ServicoTarefas, host="127.0.0.1", porta=8000, token=None):
    srv = ThreadingHTTPServer((host, porta), _handler_para(servico, token))
    srv.servico = servico
    return srv


if __name__ == "__main__":
    s = criar_servidor(
        ServicoTarefas(RepositorioSqlite(os.environ.get("TAREFAS_DB", "tarefas.db"))),
        "127.0.0.1",
        int(os.environ.get("TAREFAS_PORTA", "8000")),
        token=os.environ.get("TAREFAS_TOKEN") or None,
    )
    print("Escutando em http://%s:%s" % s.server_address)
    s.serve_forever()
