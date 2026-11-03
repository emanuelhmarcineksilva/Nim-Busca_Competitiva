import unittest

from agentes import (
    agente_aleatorio,
    agente_busca_limitada,
    agente_principal,
    alfa_beta_limitado,
)
from jogo import Estado, Jogada, Jogador, acoes


class TesteAgentes(unittest.TestCase):
    def test_agente_aleatorio_sempre_escolhe_acao_legal(self):
        estados = (
            Estado(1, 2, Jogador.MAX),
            Estado(3, 0, Jogador.MIN),
            Estado(2, 2, Jogador.MAX),
        )

        for estado in estados:
            with self.subTest(estado=estado):
                self.assertIn(agente_aleatorio(estado, seed=7), acoes(estado))

    def test_agente_aleatorio_reproduz_escolha_com_mesma_semente(self):
        estado = Estado(4, 3, Jogador.MAX)

        primeira = agente_aleatorio(estado, seed=123)
        segunda = agente_aleatorio(estado, seed=123)

        self.assertEqual(primeira, segunda)

    def test_agente_aleatorio_retorna_none_no_terminal(self):
        self.assertIsNone(agente_aleatorio(Estado(0, 0), seed=1))

    def test_agente_busca_limitada_retorna_jogada_valor_e_nos(self):
        estado = Estado(1, 2, Jogador.MAX)

        jogada, valor, nos = agente_busca_limitada(estado, profundidade=1)
        valor_esperado, jogada_esperada, nos_esperados = alfa_beta_limitado(
            estado,
            profundidade_maxima=1,
            ordenar=False,
        )

        self.assertIn(jogada, acoes(estado))
        self.assertEqual((jogada, valor, nos), (
            jogada_esperada,
            valor_esperado,
            nos_esperados,
        ))

    def test_agente_busca_limitada_usa_profundidade_e_ordenacao_configuradas(self):
        estado = Estado(3, 1, Jogador.MAX)

        jogada, valor, nos = agente_busca_limitada(
            estado,
            profundidade=2,
            ordenar=True,
        )
        valor_esperado, jogada_esperada, nos_esperados = alfa_beta_limitado(
            estado,
            profundidade_maxima=2,
            ordenar=True,
        )

        self.assertEqual((jogada, valor, nos), (
            jogada_esperada,
            valor_esperado,
            nos_esperados,
        ))

    def test_agente_principal_usa_profundidade_configurada_e_ordenacao(self):
        estado = Estado(3, 1, Jogador.MAX)

        jogada, valor, nos = agente_principal(estado, profundidade=2)
        valor_esperado, jogada_esperada, nos_esperados = alfa_beta_limitado(
            estado,
            profundidade_maxima=2,
            ordenar=True,
        )

        self.assertEqual((jogada, valor, nos), (
            jogada_esperada,
            valor_esperado,
            nos_esperados,
        ))
        self.assertIn(jogada, acoes(estado))

    def test_profundidade_padrao_proposta_do_agente_principal_e_tres(self):
        estado = Estado(1, 2, Jogador.MAX)

        resultado_padrao = agente_principal(estado)
        valor_esperado, jogada_esperada, nos_esperados = alfa_beta_limitado(
            estado,
            profundidade_maxima=3,
            ordenar=True,
        )

        self.assertEqual(resultado_padrao, (
            jogada_esperada,
            valor_esperado,
            nos_esperados,
        ))

    def test_agentes_de_busca_retorna_utilidade_exata_no_terminal(self):
        estado = Estado(0, 0, Jogador.MIN)

        for agente in (agente_busca_limitada, agente_principal):
            with self.subTest(agente=agente.__name__):
                self.assertEqual(agente(estado, profundidade=0), (None, 1, 1))

    def test_agentes_de_busca_rejeitam_profundidade_sem_jogada(self):
        estado = Estado(1, 2, Jogador.MAX)

        for agente in (agente_busca_limitada, agente_principal):
            with self.subTest(agente=agente.__name__):
                with self.assertRaises(ValueError):
                    agente(estado, profundidade=0)


if __name__ == "__main__":
    unittest.main()
