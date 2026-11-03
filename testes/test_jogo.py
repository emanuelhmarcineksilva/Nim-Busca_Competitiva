import unittest

from jogo import (
    Estado,
    Jogada,
    Jogador,
    Pilha,
    acoes,
    criar_estado_inicial,
    jogador,
    resultado,
    teste_terminal,
    utilidade,
)


class TesteRegrasNim(unittest.TestCase):
    def test_estado_inicial_configuravel(self):
        estado = criar_estado_inicial(3, 5)

        self.assertEqual(estado, Estado(3, 5, Jogador.MAX))
        self.assertEqual(jogador(estado), Jogador.MAX)

    def test_acoes_geram_todas_as_retiradas_legais(self):
        estado = Estado(3, 2, Jogador.MAX)

        self.assertEqual(
            acoes(estado),
            [
                Jogada(Pilha.A, 1),
                Jogada(Pilha.A, 2),
                Jogada(Pilha.A, 3),
                Jogada(Pilha.B, 1),
                Jogada(Pilha.B, 2),
            ],
        )

    def test_pilha_vazia_nao_tem_acoes(self):
        self.assertEqual(acoes(Estado(0, 2)), [
            Jogada(Pilha.B, 1),
            Jogada(Pilha.B, 2),
        ])

    def test_estado_terminal_nao_tem_acoes(self):
        estado = Estado(0, 0)

        self.assertTrue(teste_terminal(estado))
        self.assertEqual(acoes(estado), [])

    def test_resultado_reduz_somente_a_pilha_escolhida_e_alterna_jogador(self):
        inicial = Estado(3, 2, Jogador.MAX)

        proximo = resultado(inicial, Jogada(Pilha.A, 2))

        self.assertEqual(proximo, Estado(1, 2, Jogador.MIN))
        self.assertEqual(inicial, Estado(3, 2, Jogador.MAX))

    def test_jogada_que_remove_a_ultima_pedra_encerra_a_partida(self):
        proximo = resultado(Estado(1, 0, Jogador.MIN), Jogada(Pilha.A, 1))

        self.assertTrue(teste_terminal(proximo))
        self.assertEqual(proximo.jogador_atual, Jogador.MAX)

    def test_rejeita_jogada_que_excede_a_pilha(self):
        estado = Estado(1, 2)

        with self.assertRaises(ValueError):
            resultado(estado, Jogada(Pilha.A, 2))
        self.assertEqual(estado, Estado(1, 2))

    def test_rejeita_jogada_em_pilha_vazia(self):
        with self.assertRaises(ValueError):
            resultado(Estado(0, 2), Jogada(Pilha.A, 1))

    def test_rejeita_jogada_em_estado_terminal(self):
        with self.assertRaises(ValueError):
            resultado(Estado(0, 0), Jogada(Pilha.A, 1))

    def test_utilidade_e_sempre_calculada_pela_perspectiva_de_max(self):
        self.assertEqual(utilidade(Estado(0, 0, Jogador.MIN)), 1)
        self.assertEqual(utilidade(Estado(0, 0, Jogador.MAX)), -1)

    def test_utilidade_nao_terminal_e_invalida(self):
        with self.assertRaises(ValueError):
            utilidade(Estado(1, 0))

    def test_rejeita_objeto_que_nao_e_uma_jogada(self):
        with self.assertRaises(TypeError):
            resultado(Estado(1, 0), None)

    def test_rejeita_quantidades_negativas_e_jogadas_invalidas(self):
        with self.assertRaises(ValueError):
            Estado(-1, 0)
        with self.assertRaises(ValueError):
            Jogada(Pilha.A, 0)


if __name__ == "__main__":
    unittest.main()
