import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from experimentos import ExecucaoCancelada
from telas.experimentos import TelaExperimentos


class TesteTelaExperimentos(unittest.TestCase):
    def setUp(self):
        try:
            self.janela = tk.Tk()
            self.janela.withdraw()
        except tk.TclError as erro:
            self.skipTest(f"Tk não está disponível: {erro}")
        self.tela = TelaExperimentos(self.janela)
        self.tela.pack(fill="both", expand=True)
        self.janela.update()
        self.assertTrue(self.tela._tabela_resumo.cget("xscrollcommand"))

    def tearDown(self):
        if self.tela._em_execucao:
            self.tela.cancelar_execucao()
            limite = time.monotonic() + 5
            while self.tela._em_execucao and time.monotonic() < limite:
                self.janela.update()
                time.sleep(0.01)
        self.janela.destroy()

    def test_confronto_personalizado_exporta_csvs_em_pasta_isolada(self):
        with tempfile.TemporaryDirectory() as diretorio:
            with patch("telas.experimentos.PASTA_EXECUCOES", Path(diretorio)):
                self.tela.posicoes_var.set("1,1")
                self.tela.repeticoes_var.set("2")
                self.tela.agente_max_var.set("Alpha-Beta limitado")
                self.tela.agente_min_var.set("Aleatório")
                self.tela.semente_var.set("2026")
                self.tela.executar_personalizado()

                limite = time.monotonic() + 5
                while self.tela._em_execucao and time.monotonic() < limite:
                    self.janela.update()
                    time.sleep(0.01)
                self.janela.update()

                self.assertFalse(self.tela._em_execucao)
                self.assertEqual(len(self.tela._ultimo_resultado["partidas"]), 2)
                self.assertEqual(
                    self.tela._ultimo_resultado["partidas"][0]["semente_partida"],
                    2026,
                )
                self.assertEqual(
                    self.tela._ultimo_resultado["partidas"][1]["semente_partida"],
                    2027,
                )
                self.assertEqual(
                    {caminho.name for caminho in self.tela._ultimo_diretorio.iterdir()},
                    {"jogadas.csv", "partidas.csv", "resumo.csv"},
                )
                aleatorias = [
                    jogada
                    for jogada in self.tela._ultimo_resultado["jogadas"]
                    if "Aleatório" in jogada["agente"]
                ]
                self.assertTrue(aleatorias)
                self.assertTrue(all(jogada["nos_visitados"] is None for jogada in aleatorias))

    def test_protocolo_completo_exige_confirmacao(self):
        with patch("telas.experimentos.messagebox.askyesno", return_value=False) as confirmar:
            self.tela.executar_protocolo()

        confirmar.assert_called_once()
        self.assertIn("19.520", confirmar.call_args.args[1])
        self.assertFalse(self.tela._em_execucao)
        self.assertEqual(self.tela._ultimo_resultado, None)

    def test_posicoes_invalidas_nao_iniciam_execucao(self):
        self.tela.posicoes_var.set("0,0")
        with patch("telas.experimentos.messagebox.showerror") as mostrar_erro:
            self.tela.executar_personalizado()

        mostrar_erro.assert_called_once()
        self.assertFalse(self.tela._em_execucao)

    def test_cancelamento_remove_pasta_temporaria_sem_publicar_csvs(self):
        with tempfile.TemporaryDirectory() as diretorio:
            with patch("telas.experimentos.PASTA_EXECUCOES", Path(diretorio)):
                with patch(
                    "telas.experimentos.executar_confronto_personalizado",
                    side_effect=ExecucaoCancelada("cancelada no teste"),
                ):
                    self.tela._iniciar_execucao("personalizado", {}, 1)
                    self.tela.cancelar_execucao()

                    limite = time.monotonic() + 5
                    while self.tela._em_execucao and time.monotonic() < limite:
                        self.janela.update()
                        time.sleep(0.01)
                    self.janela.update()

                self.assertFalse(self.tela._em_execucao)
                self.assertEqual(list(Path(diretorio).iterdir()), [])
                self.assertIn("cancelada", self.tela._resultado_var.get())


if __name__ == "__main__":
    unittest.main()
