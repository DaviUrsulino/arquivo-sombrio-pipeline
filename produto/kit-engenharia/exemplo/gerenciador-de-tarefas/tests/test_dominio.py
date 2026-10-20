import unittest

import dataclasses

from src.dominio import ErroNaoEncontrado, ErroValidacao, ServicoTarefas
from src.repositorio import RepositorioSqlite


def novo_servico():
    return ServicoTarefas(RepositorioSqlite(":memory:"))


class TestCriar(unittest.TestCase):
    def setUp(self):
        self.s = novo_servico()

    def test_cria_com_titulo_valido(self):
        t = self.s.criar("Comprar pão")
        self.assertEqual((t.id, t.titulo, t.concluida), (1, "Comprar pão", False))

    def test_titulo_e_aparado(self):  # RN-01
        self.assertEqual(self.s.criar("  a  ").titulo, "a")

    def test_limite_200_aceito_201_rejeitado(self):  # RF-01 valor-limite
        self.assertEqual(len(self.s.criar("x" * 200).titulo), 200)
        with self.assertRaises(ErroValidacao):
            self.s.criar("x" * 201)

    def test_rejeita_vazio_espacos_e_tipo_errado(self):
        for ruim in ["", "   ", None, 5, ["a"], {"a": 1}, True]:
            with self.subTest(ruim=ruim), self.assertRaises(ErroValidacao):
                self.s.criar(ruim)

    def test_aparar_antes_de_medir(self):
        # 200 chars + espaços extras é válido (o limite vale após strip)
        self.assertEqual(len(self.s.criar(" " + "x" * 200 + " ").titulo), 200)

    def test_sql_injection_guardado_literal(self):  # RNF-04
        feio = "'; DROP TABLE tarefas;--"
        self.s.criar(feio)
        self.assertEqual(self.s.listar()[0].titulo, feio)


class TestListarObterApagar(unittest.TestCase):
    def setUp(self):
        self.s = novo_servico()
        self.a = self.s.criar("a")
        self.b = self.s.criar("b")
        self.s.atualizar(self.b.id, {"concluida": True})

    def test_listar_filtra(self):  # RF-02
        self.assertEqual([t.titulo for t in self.s.listar()], ["a", "b"])
        self.assertEqual([t.titulo for t in self.s.listar(True)], ["b"])
        self.assertEqual([t.titulo for t in self.s.listar(False)], ["a"])

    def test_obter_inexistente(self):  # RF-03
        with self.assertRaises(ErroNaoEncontrado):
            self.s.obter(99)

    def test_apagar(self):  # RF-05
        self.s.apagar(self.a.id)
        with self.assertRaises(ErroNaoEncontrado):
            self.s.obter(self.a.id)
        with self.assertRaises(ErroNaoEncontrado):
            self.s.apagar(self.a.id)

    def test_id_nao_reutilizado(self):
        self.s.apagar(self.b.id)
        self.assertEqual(self.s.criar("c").id, 3)


class TestAtualizar(unittest.TestCase):
    def setUp(self):
        self.s = novo_servico()
        self.t = self.s.criar("a")

    def test_conclui_e_persiste(self):  # RF-04
        self.s.atualizar(self.t.id, {"concluida": True})
        self.assertTrue(self.s.obter(self.t.id).concluida)

    def test_muda_titulo_validando(self):
        self.assertEqual(self.s.atualizar(self.t.id, {"titulo": " novo "}).titulo, "novo")
        with self.assertRaises(ErroValidacao):
            self.s.atualizar(self.t.id, {"titulo": ""})
        self.assertEqual(self.s.obter(self.t.id).titulo, "novo")

    def test_concluida_exige_booleano_real(self):  # RN-02
        for ruim in ["true", "sim", 1, 0, None]:
            with self.subTest(ruim=ruim), self.assertRaises(ErroValidacao):
                self.s.atualizar(self.t.id, {"concluida": ruim})

    def test_vazio_ou_campo_desconhecido(self):
        for ruim in [{}, {"id": 5}, {"titulo": "x", "extra": 1}]:
            with self.subTest(ruim=ruim), self.assertRaises(ErroValidacao):
                self.s.atualizar(self.t.id, ruim)

    def test_atualizar_inexistente(self):
        with self.assertRaises(ErroNaoEncontrado):
            self.s.atualizar(42, {"concluida": True})

    def test_falha_de_validacao_nao_altera_nada(self):
        with self.assertRaises(ErroValidacao):
            self.s.atualizar(self.t.id, {"concluida": True, "titulo": ""})
        self.assertFalse(self.s.obter(self.t.id).concluida)


if __name__ == "__main__":
    unittest.main()


class TestImutabilidade(unittest.TestCase):
    def test_tarefa_nao_pode_ser_alterada_depois_de_criada(self):  # achado da injeção de defeitos: frozen=True
        tarefa = ServicoTarefas(RepositorioSqlite(":memory:")).criar("x")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            tarefa.titulo = "outro"
