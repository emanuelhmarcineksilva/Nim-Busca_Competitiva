import unittest

from agentes import avaliacao_heuristica, minimax
from jogo import Estado, Jogador, teste_terminal


class TesteAvaliacaoHeuristica(unittest.TestCase):
    def test_terminal_preserva_utilidade_exata_de_max(self):
        self.assertEqual(
            avaliacao_heuristica(Estado(0, 0, Jogador.MIN)),
            1,
        )
        self.assertEqual(
            avaliacao_heuristica(Estado(0, 0, Jogador.MAX)),
            -1,
        )

    def test_pilha_unica_identifica_vitoria_imediata_do_jogador_atual(self):
        self.assertAlmostEqual(
            avaliacao_heuristica(Estado(0, 2, Jogador.MAX)),
            0.6,
        )
        self.assertEqual(
            avaliacao_heuristica(Estado(0, 3, Jogador.MIN)),
            -1.0,
        )

    def test_paridade_e_avaliada_do_ponto_de_vista_de_max(self):
        self.assertEqual(
            avaliacao_heuristica(Estado(2, 2, Jogador.MAX)),
            -0.2,
        )
        self.assertEqual(
            avaliacao_heuristica(Estado(2, 2, Jogador.MIN)),
            0.2,
        )

    def test_avaliacao_fica_no_intervalo_da_utilidade(self):
        for pilha_a in range(5):
            for pilha_b in range(5):
                for jogador_atual in (Jogador.MAX, Jogador.MIN):
                    valor = avaliacao_heuristica(
                        Estado(pilha_a, pilha_b, jogador_atual)
                    )
                    self.assertGreaterEqual(valor, -1)
                    self.assertLessEqual(valor, 1)

    def test_compara_estimativa_com_busca_completa_em_estados_pequenos(self):
        estados_verificados = 0
        concordancias = 0

        for pilha_a in range(4):
            for pilha_b in range(4):
                for jogador_atual in (Jogador.MAX, Jogador.MIN):
                    estado = Estado(pilha_a, pilha_b, jogador_atual)
                    if teste_terminal(estado):
                        continue

                    valor_exato, _, _ = minimax(estado)
                    valor_estimado = avaliacao_heuristica(estado)

                    if (valor_estimado > 0) == (valor_exato > 0):
                        concordancias += 1
                    estados_verificados += 1

        self.assertEqual(estados_verificados, 30)
        self.assertEqual(concordancias, 26)


if __name__ == "__main__":
    unittest.main()
