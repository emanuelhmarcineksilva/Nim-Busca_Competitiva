import unittest

from agentes import minimax
from jogo import Estado, Jogada, Jogador, Pilha


class TesteMinimax(unittest.TestCase):
    def test_max_escolhe_a_jogada_de_maior_valor(self):
        valor, jogada, nos = minimax(Estado(1, 2, Jogador.MAX))

        self.assertEqual(valor, 1)
        self.assertEqual(jogada, Jogada(Pilha.B, 1))
        self.assertEqual(nos, 12)

    def test_min_escolhe_a_jogada_de_menor_valor(self):
        valor, jogada, nos = minimax(Estado(1, 2, Jogador.MIN))

        self.assertEqual(valor, -1)
        self.assertEqual(jogada, Jogada(Pilha.B, 1))
        self.assertEqual(nos, 12)

    def test_estado_terminal_retorna_utilidade_e_nenhuma_jogada(self):
        valor, jogada, nos = minimax(Estado(0, 0, Jogador.MAX))

        self.assertEqual(valor, -1)
        self.assertIsNone(jogada)
        self.assertEqual(nos, 1)

    def test_empate_de_valor_escolhe_a_primeira_acao_legal(self):
        valor, jogada, nos = minimax(Estado(1, 1, Jogador.MAX))

        self.assertEqual(valor, -1)
        self.assertEqual(jogada, Jogada(Pilha.A, 1))
        self.assertEqual(nos, 5)


if __name__ == "__main__":
    unittest.main()
