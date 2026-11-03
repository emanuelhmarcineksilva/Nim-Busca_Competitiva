import unittest

from agentes import alfa_beta, minimax, ordenar_acoes
from jogo import Estado, Jogada, Jogador, Pilha, acoes


class TesteAlfaBeta(unittest.TestCase):
    def test_posicao_com_max_jogando(self):
        valor, jogada, _ = alfa_beta(Estado(1, 2, Jogador.MAX))

        self.assertEqual(valor, 1)
        self.assertIn(jogada, acoes(Estado(1, 2, Jogador.MAX)))

    def test_posicao_com_min_jogando(self):
        valor, jogada, _ = alfa_beta(Estado(1, 2, Jogador.MIN))

        self.assertEqual(valor, -1)
        self.assertIn(jogada, acoes(Estado(1, 2, Jogador.MIN)))

    def test_estado_terminal(self):
        valor, jogada, nos = alfa_beta(Estado(0, 0, Jogador.MAX))

        self.assertEqual(valor, -1)
        self.assertIsNone(jogada)
        self.assertEqual(nos, 1)

    def test_valores_iguais_ao_minimax_em_estados_pequenos(self):
        estados_verificados = 0

        for pilha_a in range(4):
            for pilha_b in range(4):
                for jogador_atual in (Jogador.MAX, Jogador.MIN):
                    estado = Estado(pilha_a, pilha_b, jogador_atual)
                    valor_minimax, _, nos_minimax = minimax(estado)
                    valor_alfa_beta, _, nos_alfa_beta = alfa_beta(estado)

                    self.assertEqual(valor_alfa_beta, valor_minimax, estado)
                    self.assertLessEqual(nos_alfa_beta, nos_minimax, estado)
                    estados_verificados += 1

        self.assertEqual(estados_verificados, 32)

    def test_desempate_mantem_primeira_acao_na_ordem_legal(self):
        estado = Estado(1, 1, Jogador.MAX)

        _, jogada, _ = alfa_beta(estado)

        self.assertEqual(jogada, Jogada(Pilha.A, 1))

    def test_ordenacao_prioriza_estado_com_pilhas_iguais(self):
        estado = Estado(3, 1, Jogador.MAX)

        jogadas_ordenadas = ordenar_acoes(estado)
        primeira = jogadas_ordenadas[0]
        estado_resultante = (
            estado.pilha_a - primeira.quantidade
            if primeira.pilha == Pilha.A
            else estado.pilha_a,
            estado.pilha_b - primeira.quantidade
            if primeira.pilha == Pilha.B
            else estado.pilha_b,
        )

        self.assertEqual(estado_resultante[0], estado_resultante[1])
        self.assertCountEqual(jogadas_ordenadas, acoes(estado))

    def test_ordenacao_preserva_valores_e_nao_excede_minimax(self):
        for pilha_a in range(4):
            for pilha_b in range(4):
                for jogador_atual in (Jogador.MAX, Jogador.MIN):
                    estado = Estado(pilha_a, pilha_b, jogador_atual)
                    valor_minimax, _, nos_minimax = minimax(estado)
                    valor_ordenado, _, nos_ordenados = alfa_beta(
                        estado, ordenar=True
                    )

                    self.assertEqual(valor_ordenado, valor_minimax, estado)
                    self.assertLessEqual(nos_ordenados, nos_minimax, estado)


if __name__ == "__main__":
    unittest.main()
