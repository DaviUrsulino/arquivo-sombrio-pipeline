import http.client
import json
import threading
import unittest

from src.api import criar_servidor
from src.dominio import ServicoTarefas
from src.repositorio import RepositorioSqlite


class Base(unittest.TestCase):
    token = None

    def setUp(self):
        self.srv = criar_servidor(ServicoTarefas(RepositorioSqlite(":memory:")), "127.0.0.1", 0, token=self.token)
        self.porta = self.srv.server_address[1]
        threading.Thread(target=lambda: self.srv.serve_forever(0.01), daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def req(self, metodo, caminho, corpo=None, headers=None, bruto=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        h = dict(headers or {})
        dados = bruto
        if corpo is not None:
            dados = json.dumps(corpo).encode()
        if dados is not None:
            h["Content-Type"] = "application/json"
        c.request(metodo, caminho, body=dados, headers=h)
        r = c.getresponse()
        txt = r.read()
        c.close()
        return r.status, (json.loads(txt) if txt else None)


class TestFluxo(Base):
    def test_fluxo_completo(self):
        s, b = self.req("POST", "/tarefas", {"titulo": "Comprar pão"})
        self.assertEqual(s, 201)
        self.assertEqual((b["id"], b["titulo"], b["concluida"]), (1, "Comprar pão", False))
        self.assertEqual(self.req("GET", "/tarefas/1")[0], 200)
        s, b = self.req("PATCH", "/tarefas/1", {"concluida": True})
        self.assertEqual((s, b["concluida"]), (200, True))
        self.assertEqual(len(self.req("GET", "/tarefas?concluida=true")[1]), 1)
        self.assertEqual(len(self.req("GET", "/tarefas?concluida=false")[1]), 0)
        self.assertEqual(self.req("DELETE", "/tarefas/1")[0], 204)
        self.assertEqual(self.req("GET", "/tarefas/1")[0], 404)
        self.assertEqual(self.req("DELETE", "/tarefas/1")[0], 404)

    def test_erros_de_validacao(self):
        self.assertEqual(self.req("POST", "/tarefas", {"titulo": ""})[0], 400)
        self.assertEqual(self.req("POST", "/tarefas", {"titulo": "x" * 201})[0], 400)
        self.assertEqual(self.req("POST", "/tarefas", {})[0], 400)
        self.assertEqual(self.req("POST", "/tarefas", bruto=b"{nao json")[0], 400)
        self.assertEqual(self.req("POST", "/tarefas", bruto=b'["lista"]')[0], 400)
        self.assertEqual(self.req("POST", "/tarefas", bruto=b'\xff\xfe')[0], 400)
        self.assertEqual(self.req("GET", "/tarefas?concluida=talvez")[0], 400)

    def test_rotas_inexistentes_e_metodos(self):
        for m, p in [("GET", "/tarefas/abc"), ("GET", "/tarefas/-1"), ("GET", "/nada"), ("GET", "/tarefas/1/x"), ("GET", "/tarefas/"), ("GET", "/tarefas/" + "9" * 19)]:
            with self.subTest(m=m, p=p):
                self.assertEqual(self.req(m, p)[0], 404)
        self.assertEqual(self.req("PUT", "/tarefas/1", {"titulo": "x"})[0], 405)
        self.assertEqual(self.req("PATCH", "/tarefas", {"titulo": "x"})[0], 405)

    def test_corpo_limite_4096(self):  # RNF-02
        ok = b'{"titulo":"a"}' + b" " * (4096 - 14)
        self.assertEqual(len(ok), 4096)
        self.assertEqual(self.req("POST", "/tarefas", bruto=ok)[0], 201)
        self.assertEqual(self.req("POST", "/tarefas", bruto=ok + b" ")[0], 413)

    def test_sem_content_length_em_post(self):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        c.putrequest("POST", "/tarefas")
        c.endheaders()
        self.assertEqual(c.getresponse().status, 411)
        c.close()

    def test_content_length_invalido(self):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        c.putrequest("POST", "/tarefas")
        c.putheader("Content-Length", "-5")
        c.endheaders()
        self.assertEqual(c.getresponse().status, 400)
        c.close()

    def test_erro_interno_nao_vaza(self):  # RF-06
        def quebra(*a, **k):
            raise RuntimeError("segredo-interno /etc/xyz")
        self.srv.servico.listar = quebra
        s, b = self.req("GET", "/tarefas")
        self.assertEqual(s, 500)
        self.assertNotIn("segredo", json.dumps(b))


class TestToken(Base):
    token = "s3gredo-de-teste"

    def test_exige_token_em_toda_rota(self):  # RNF-01
        for m, p in [("GET", "/tarefas"), ("POST", "/tarefas"), ("GET", "/tarefas/1"),
                     ("PATCH", "/tarefas/1"), ("DELETE", "/tarefas/1")]:
            with self.subTest(m=m, p=p):
                self.assertEqual(self.req(m, p, {"titulo": "x"} if m in ("POST", "PATCH") else None)[0], 401)
                self.assertEqual(self.req(m, p, {"titulo": "x"} if m in ("POST", "PATCH") else None,
                                          headers={"Authorization": "Bearer errado"})[0], 401)
        self.assertEqual(self.req("GET", "/rota-que-nao-existe")[0], 401)

    def test_token_correto(self):
        h = {"Authorization": "Bearer " + self.token}
        self.assertEqual(self.req("POST", "/tarefas", {"titulo": "x"}, headers=h)[0], 201)
        self.assertEqual(self.req("GET", "/tarefas", headers=h)[0], 200)

    def test_token_prefixo_nao_basta(self):
        h = {"Authorization": "Bearer " + self.token[:-1]}
        self.assertEqual(self.req("GET", "/tarefas", headers=h)[0], 401)
        h = {"Authorization": "Bearer " + self.token + "x"}
        self.assertEqual(self.req("GET", "/tarefas", headers=h)[0], 401)


if __name__ == "__main__":
    unittest.main()
