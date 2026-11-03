import unittest

from agentes import (
    alfa_beta,
    alfa_beta_limitado,
    avaliacao_heuristica,
    minimax,
)
from jogo import Estado, Jogada, Jogador, Pilha, acoes


class TesteAlfaBetaLimitado(unittest.TestCase):
    def test_profundidade_zero_avalia_raiz_nao_terminal(self):
        estado = Estado(2, 2, Jogador.MAX)

        valor, jogada, nos = alfa_beta_limitado(estado, 0)

        self.assertEqual(valor, avaliacao_heuristica(estado))
        self.assertIsNone(jogada)
        self.assertEqual(nos, 1)

    def test_estado_terminal_e_avaliado_exatamente_antes_do_corte(self):
        valor, jogada, nos = alfa_beta_limitado(
            Estado(0, 0, Jogador.MIN),
            0,
        )

        self.assertEqual(valor, 1)
        self.assertIsNone(jogada)
        self.assertEqual(nos, 1)

    def test_estado_terminal_antes_da_profundidade_maxima(self):
        valor, jogada, nos = alfa_beta_limitado(
            Estado(1, 0, Jogador.MAX),
            1,
        )

        self.assertEqual(valor, 1)
        self.assertEqual(jogada, Jogada(Pilha.A, 1))
        self.assertEqual(nos, 2)

    def test_busca_limitada_retorna_uma_acao_legal(self):
        estado = Estado(1, 2, Jogador.MAX)

        _, jogada, _ = alfa_beta_limitado(estado, 1)

        self.assertIn(jogada, acoes(estado))

    def test_profundidade_suficiente_concorda_com_busca_completa(self):
        for pilha_a in range(4):
            for pilha_b in range(4):
                for jogador_atual in (Jogador.MAX, Jogador.MIN):
                    estado = Estado(pilha_a, pilha_b, jogador_atual)
                    valor_completo, _, _ = minimax(estado)
                    valor_limitado, _, _ = alfa_beta_limitado(
                        estado,
                        pilha_a + pilha_b,
                    )

                    self.assertEqual(valor_limitado, valor_completo, estado)

    def test_limite_invalido_e_rejeitado(self):
        for profundidade in (-1, 1.5, True):
            with self.subTest(profundidade=profundidade):
                with self.assertRaises(ValueError):
                    alfa_beta_limitado(Estado(1, 1), profundidade)

    def test_busca_completa_existente_permanece_disponivel(self):
        estado = Estado(2, 3, Jogador.MIN)

        self.assertEqual(alfa_beta(estado)[0], minimax(estado)[0])


if __name__ == "__main__":
    unittest.main()
