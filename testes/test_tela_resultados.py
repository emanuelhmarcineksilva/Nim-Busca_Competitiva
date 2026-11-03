import tempfile
import tkinter as tk
import unittest

from telas.resultados import (
    PASTA_RESULTADOS,
    carregar_resultados,
    calcular_indicadores_gerais,
    obter_estatisticas_ordenacao,
    obter_estatisticas_profundidade,
    TelaResultados,
)


class TesteTelaResultados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = carregar_resultados()

    def test_csvs_finais_tem_as_quantidades_planejadas(self):
        indicadores = calcular_indicadores_gerais(self.dados)
        self.assertEqual(indicadores["partidas"], 19520)
        self.assertEqual(indicadores["confrontos"], 16)
        self.assertEqual(indicadores["jogadas"], 79447)
        self.assertEqual(indicadores["empates"], 0)
        self.assertEqual(len(self.dados["resumo"]), 32)
        self.assertEqual(len({linha["id_partida"] for linha in self.dados["partidas"]}), 19520)

    def test_agente_sem_busca_permanece_nao_aplicavel(self):
        linhas_aleatorias = [
            linha
            for linha in self.dados["resumo"]
            if linha["configuracao_agente"] == "Agente aleatório"
        ]
        self.assertTrue(linhas_aleatorias)
        for linha in linhas_aleatorias:
            with self.subTest(confronto=linha["confronto"]):
                self.assertEqual(linha["decisoes_busca"], "0")
                self.assertEqual(linha["media_nos_por_decisao"], "N/A")
                self.assertEqual(linha["maximo_nos_por_decisao"], "N/A")

    def test_estatisticas_de_profundidade_e_ordenacao_preservam_decisoes(self):
        profundidades = obter_estatisticas_profundidade(self.dados["resumo"])
        ordenacao = obter_estatisticas_ordenacao(self.dados["resumo"])

        self.assertEqual([linha["profundidade"] for linha in profundidades], [1, 2, 3, 4])
        self.assertEqual(len(ordenacao), 8)
        for linha in profundidades + ordenacao:
            self.assertGreater(linha["decisoes"], 0)
            self.assertGreaterEqual(linha["media"], 0)
            self.assertGreaterEqual(linha["maximo"], linha["media"])

    def test_leitor_sinaliza_csv_ausente(self):
        with tempfile.TemporaryDirectory() as diretorio:
            with self.assertRaises(FileNotFoundError):
                carregar_resultados(diretorio)

    def test_leitor_usa_campos_csv_existentes_sem_modifica_los(self):
        original = PASTA_RESULTADOS / "resumo.csv"
        primeira_linha = original.read_text(encoding="utf-8-sig").splitlines()[0]
        self.assertIn("media_nos_por_decisao", primeira_linha)
        self.assertIn("configuracao_agente", primeira_linha)

    def test_painel_apresenta_confronto_partidas_e_historico(self):
        try:
            janela = tk.Tk()
            janela.withdraw()
        except tk.TclError as erro:
            self.skipTest(f"Tk não está disponível: {erro}")
        try:
            tela = TelaResultados(janela)
            tela.pack(fill="both", expand=True)
            janela.update()

            self.assertEqual(tela._cartoes["Partidas"].get(), "19.520")
            self.assertEqual(len(tela._tabela_resumo.get_children()), 2)
            self.assertGreater(len(tela._tabela_vitorias.get_children()), 0)
            self.assertGreater(len(tela._tabela_partidas.get_children()), 0)
            for tabela in (
                tela._tabela_vitorias,
                tela._tabela_resumo,
                tela._tabela_partidas,
                tela._tabela_jogadas,
            ):
                self.assertTrue(tabela.cget("xscrollcommand"))

            primeira_partida = tela._tabela_partidas.get_children()[0]
            tela._tabela_partidas.selection_set(primeira_partida)
            tela._selecionar_partida()
            self.assertGreater(len(tela._tabela_jogadas.get_children()), 0)
        finally:
            janela.destroy()


if __name__ == "__main__":
    unittest.main()
