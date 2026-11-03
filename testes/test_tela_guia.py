import tkinter as tk
import unittest

from telas.guia import SECOES, TelaGuia


class TesteTelaGuia(unittest.TestCase):
    def setUp(self):
        try:
            self.janela = tk.Tk()
            self.janela.withdraw()
        except tk.TclError as erro:
            self.skipTest(f"Tk não está disponível: {erro}")
        self.tela = TelaGuia(self.janela)
        self.tela.pack(fill="both", expand=True)
        self.janela.update()

    def tearDown(self):
        self.janela.destroy()

    def test_guia_tem_as_14_secoes_planejadas(self):
        self.assertEqual(len(SECOES), 14)
        self.assertIn("Metodologia experimental", SECOES)
        self.assertIn("Resultados", SECOES)
        self.assertIn("Conclusão", SECOES)

    def test_secao_de_resultados_consulta_os_csvs_finais(self):
        texto = self.tela._texto_resultados()

        self.assertIn("19,520", texto)
        self.assertIn("CSV", texto)
        self.assertIn("N/A", texto)
        self.assertIn("não demonstram superioridade geral", texto)


if __name__ == "__main__":
    unittest.main()
