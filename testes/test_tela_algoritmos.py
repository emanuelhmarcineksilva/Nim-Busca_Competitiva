import time
import tkinter as tk
from tkinter import ttk
import unittest

from telas.algoritmos import CONCEITOS, TelaAlgoritmos


class TesteTelaAlgoritmos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.janela = tk.Tk()
            cls.janela.withdraw()
        except tk.TclError as erro:
            raise unittest.SkipTest(f"Tk não está disponível: {erro}") from erro

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "janela"):
            cls.janela.destroy()

    def setUp(self):
        self.tela = TelaAlgoritmos(self.janela)
        self.tela.pack(fill="both", expand=True)
        self.janela.update()

    def tearDown(self):
        self.tela.destroy()
        self.janela.update()

    def test_todos_os_assuntos_exibem_as_secoes_solicitadas(self):
        self.assertEqual(len(CONCEITOS), 7)
        for conceito in CONCEITOS.values():
            with self.subTest(conceito=conceito):
                self.assertEqual(
                    set(conceito),
                    {"o_que", "para_que", "como", "projeto", "exemplo", "referencia", "tests"},
                )
                self.assertTrue(all(conteudo for conteudo in conceito.values()))

    def test_calculadora_xor_atualiza_com_os_valores(self):
        self.tela.xor_a_var.set("3")
        self.tela.xor_b_var.set("1")

        self.tela._atualizar_xor()

        self.assertIn("3 XOR 1 = 2", self.tela._xor_var.get())
        self.assertIn("há uma jogada", self.tela._xor_var.get())

        self.tela.xor_a_var.set("4")
        self.tela.xor_b_var.set("4")
        self.tela._atualizar_xor()
        self.assertIn("4 XOR 4 = 0", self.tela._xor_var.get())
        self.assertIn("desfavorável", self.tela._xor_var.get())

    def test_demonstracao_chama_buscas_reais_e_desenha_sucessores(self):
        self.tela.pilha_a_var.set("1")
        self.tela.pilha_b_var.set("1")
        self.tela.profundidade_var.set("1")
        self.tela.executar_demonstracao()

        limite = time.monotonic() + 5
        while str(self.tela._botao_executar["state"]) == "disabled" and time.monotonic() < limite:
            self.janela.update()
            time.sleep(0.01)
        self.janela.update()

        self.assertEqual(str(self.tela._botao_executar["state"]), "normal")
        self.assertIn("Minimax:", self.tela._resultado_var.get())
        self.assertIn("Alpha-Beta:", self.tela._resultado_var.get())
        self.assertIn("nós", self.tela._resultado_var.get())
        self.assertIn("MAX joga agora", self.tela._guia_var.get())
        self.assertIn("O sucessor exibido é", self.tela._guia_var.get())
        self.assertIn("diferença exibida é global", self.tela._guia_var.get())
        self.assertIn("não uma garantia de vitória", self.tela._guia_var.get())
        self.assertGreater(len(self.tela._arvore.find_all()), 0)

    def test_textos_da_demonstracao_adaptam_a_largura_disponivel(self):
        identificador_aba = next(
            identificador
            for identificador in self.tela._abas.tabs()
            if self.tela._abas.tab(identificador, "text") == "Demonstração interativa"
        )
        aba = self.tela.nametowidget(identificador_aba)
        aba.event_generate("<Configure>", width=640, height=300, when="now")

        resultado = next(
            widget
            for widget in aba.winfo_children()
            if isinstance(widget, ttk.Label)
            and widget.cget("textvariable") == str(self.tela._resultado_var)
        )
        legenda = next(
            widget
            for widget in aba.winfo_children()
            if isinstance(widget, ttk.Label) and widget.cget("text").startswith("Verde:")
        )

        self.assertEqual(resultado.cget("wraplength"), 616)
        self.assertEqual(legenda.cget("wraplength"), 616)


if __name__ == "__main__":
    unittest.main()
