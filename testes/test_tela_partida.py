import time
import tkinter as tk
import unittest
from unittest.mock import patch

from interface import NimLab
from jogo import Estado, Jogador
from telas.partida import TelaPartida


class TesteTelaPartida(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.aplicativo = NimLab()
            cls.aplicativo.withdraw()
        except tk.TclError as erro:
            raise unittest.SkipTest(f"Tk não está disponível: {erro}") from erro

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "aplicativo"):
            cls.aplicativo.destroy()

    def setUp(self):
        self.tela = self.aplicativo._telas["partida"]
        self.assertIsInstance(self.tela, TelaPartida)

    def iniciar(self, pilha_a, pilha_b, agente_max, agente_min, seed="7"):
        self.tela.pilha_a_var.set(str(pilha_a))
        self.tela.pilha_b_var.set(str(pilha_b))
        self.tela.jogador_inicial_var.set(Jogador.MAX.value)
        self.tela.agente_max_var.set(agente_max)
        self.tela.agente_min_var.set(agente_min)
        self.tela.semente_var.set(seed)
        self.tela.iniciar_partida()
        self.aplicativo.update()

    def aguardar_calculo(self):
        limite = time.monotonic() + 5
        while self.tela._calculo_em_andamento and time.monotonic() < limite:
            self.aplicativo.update()
            time.sleep(0.01)
        self.aplicativo.update()
        self.assertFalse(self.tela._calculo_em_andamento)

    def test_jogada_humana_atualiza_estado_e_identifica_vencedor(self):
        self.iniciar(1, 0, "Humano", "Minimax completo")
        self.tela.pilha_jogada_var.set("A")
        self.tela.quantidade_jogada_var.set("1")

        self.tela.proxima_jogada()

        self.assertEqual(self.tela._estado, Estado(0, 0, Jogador.MIN))
        self.assertEqual(len(self.tela._historico), 1)
        self.assertIn("vencedor: MAX", self.tela._vez_var.get())
        self.assertEqual(self.tela._tabela.get_children().__len__(), 1)

    def test_jogada_automatica_registra_nos_e_permite_proximo_turno(self):
        self.iniciar(1, 1, "Minimax completo", "Alpha-Beta completo")

        self.tela.proxima_jogada()
        self.aguardar_calculo()

        self.assertEqual(len(self.tela._historico), 1)
        primeira = self.tela._historico[0]
        self.assertEqual(primeira["agente"], "Minimax completo")
        self.assertIsInstance(primeira["nos_visitados"], int)
        self.assertGreater(primeira["nos_visitados"], 0)
        self.assertIsNone(primeira["semente"])

        self.tela.proxima_jogada()
        self.aguardar_calculo()
        self.assertEqual(len(self.tela._historico), 2)
        self.assertEqual(
            self.tela._historico[1]["agente"],
            "Alpha-Beta completo",
        )

    def test_agentes_com_profundidade_sao_executados(self):
        for nome_agente in ("Alpha-Beta limitado", "Agente principal"):
            with self.subTest(agente=nome_agente):
                self.iniciar(1, 1, nome_agente, "Humano")
                self.tela.proxima_jogada()
                self.aguardar_calculo()

                registro = self.tela._historico[0]
                self.assertEqual(registro["agente"], nome_agente)
                self.assertIsInstance(registro["nos_visitados"], int)
                self.assertGreater(registro["nos_visitados"], 0)

    def test_agente_aleatorio_registra_semente_e_nos_nao_aplicaveis(self):
        self.iniciar(1, 1, "Humano", "Aleatório", seed="2026")
        self.tela.pilha_jogada_var.set("A")
        self.tela.quantidade_jogada_var.set("1")
        self.tela.proxima_jogada()

        self.tela.proxima_jogada()
        self.aguardar_calculo()

        aleatoria = self.tela._historico[1]
        self.assertEqual(aleatoria["agente"], "Aleatório")
        self.assertIsNone(aleatoria["nos_visitados"])
        self.assertIsInstance(aleatoria["semente"], int)

    def test_jogada_ilegal_nao_altera_estado_ou_historico(self):
        self.iniciar(1, 0, "Humano", "Minimax completo")
        self.tela.pilha_jogada_var.set("A")
        self.tela.quantidade_jogada_var.set("2")

        with patch("telas.partida.messagebox.showerror") as mostrar_erro:
            self.tela.proxima_jogada()

        self.assertEqual(self.tela._estado, Estado(1, 0, Jogador.MAX))
        self.assertEqual(self.tela._historico, [])
        mostrar_erro.assert_called_once()

    def test_jogador_min_pode_iniciar(self):
        self.tela.pilha_a_var.set("1")
        self.tela.pilha_b_var.set("0")
        self.tela.jogador_inicial_var.set(Jogador.MIN.value)
        self.tela.agente_max_var.set("Humano")
        self.tela.agente_min_var.set("Humano")
        self.tela.semente_var.set("7")
        self.tela.iniciar_partida()

        self.assertEqual(self.tela._estado, Estado(1, 0, Jogador.MIN))
        self.assertIn("Na vez: MIN", self.tela._vez_var.get())

    def test_navegacao_acessa_todas_as_telas(self):
        identificadores = (
            "partida",
            "algoritmos",
            "experimentos",
            "resultados",
            "guia",
        )

        for identificador in identificadores:
            with self.subTest(tela=identificador):
                self.aplicativo.mostrar_tela(identificador)
                self.aplicativo.update()
                pagina = self.aplicativo._paginas_rolaveis[identificador]
                self.assertGreater(pagina.canvas.winfo_width(), 0)
                self.assertGreater(pagina.canvas.winfo_height(), 0)

    def test_historico_disponibiliza_rolagem_horizontal(self):
        self.assertTrue(self.tela._tabela.cget("xscrollcommand"))


if __name__ == "__main__":
    unittest.main()
