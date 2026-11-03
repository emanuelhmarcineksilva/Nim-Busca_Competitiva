import unittest

from agentes import agente_aleatorio, agente_busca_limitada
from experimentos import executar_partida
from jogo import Estado, Jogada, Jogador, Pilha, acoes, teste_terminal, utilidade


class TesteExecucaoPartidas(unittest.TestCase):
    def test_partida_completa_entre_agentes_deterministicos(self):
        partida = executar_partida(
            agente_busca_limitada,
            agente_busca_limitada,
            pilha_a=1,
            pilha_b=0,
            seed=10,
        )

        self.assertEqual(partida["vencedor"], Jogador.MAX)
        self.assertTrue(teste_terminal(partida["estado_final"]))
        self.assertEqual(partida["quantidade_jogadas"], 1)

    def test_partida_entre_agente_aleatorio_e_agente_de_busca(self):
        partida = executar_partida(
            agente_aleatorio,
            agente_busca_limitada,
            pilha_a=2,
            pilha_b=1,
            seed=2026,
        )

        self.assertTrue(teste_terminal(partida["estado_final"]))
        self.assertIsNotNone(partida["vencedor"])
        self.assertGreater(partida["quantidade_jogadas"], 0)

    def test_alternancia_correta_de_max_e_min(self):
        partida = executar_partida(
            agente_busca_limitada,
            agente_busca_limitada,
            pilha_a=2,
            pilha_b=1,
            jogador_inicial=Jogador.MIN,
            seed=5,
        )

        jogadores = [registro["jogador"] for registro in partida["historico"]]
        self.assertEqual(jogadores[0], Jogador.MIN)
        for anterior, atual in zip(jogadores, jogadores[1:]):
            self.assertNotEqual(anterior, atual)

    def test_vencedor_corresponde_a_utilidade_terminal(self):
        partida = executar_partida(
            agente_busca_limitada,
            agente_busca_limitada,
            pilha_a=1,
            pilha_b=0,
            seed=2,
        )

        esperado = (
            Jogador.MAX
            if utilidade(partida["estado_final"]) == 1
            else Jogador.MIN
        )
        self.assertEqual(partida["vencedor"], esperado)

    def test_historico_registra_transicoes_e_ordem_das_jogadas(self):
        partida = executar_partida(
            agente_busca_limitada,
            agente_busca_limitada,
            pilha_a=2,
            pilha_b=0,
            seed=1,
        )

        self.assertEqual(partida["quantidade_jogadas"], len(partida["historico"]))
        self.assertEqual(
            partida["historico"][0]["estado_anterior"],
            partida["estado_inicial"],
        )
        for indice, registro in enumerate(partida["historico"]):
            self.assertEqual(registro["numero_jogada"], indice + 1)
            self.assertIn(registro["jogada"], acoes(registro["estado_anterior"]))
            self.assertEqual(
                registro["estado_posterior"].jogador_atual,
                Jogador.MIN
                if registro["jogador"] == Jogador.MAX
                else Jogador.MAX,
            )
            if indice:
                self.assertEqual(
                    registro["estado_anterior"],
                    partida["historico"][indice - 1]["estado_posterior"],
                )

    def test_nos_de_busca_e_nao_aplicavel_para_agente_aleatorio(self):
        partida = executar_partida(
            agente_aleatorio,
            agente_busca_limitada,
            pilha_a=2,
            pilha_b=1,
            seed=44,
        )

        for registro in partida["historico"]:
            if registro["agente"] == "agente_aleatorio":
                self.assertIsNone(registro["nos_visitados"])
                self.assertIsNotNone(registro["semente"])
            else:
                self.assertIsInstance(registro["nos_visitados"], int)
                self.assertGreater(registro["nos_visitados"], 0)
                self.assertIsNone(registro["semente"])

    def test_mesma_semente_reproduz_partida_e_sementes_por_turno(self):
        argumentos = {
            "agente_max": agente_aleatorio,
            "agente_min": agente_aleatorio,
            "pilha_a": 3,
            "pilha_b": 2,
            "seed": 2026,
        }

        primeira = executar_partida(**argumentos)
        segunda = executar_partida(**argumentos)

        self.assertEqual(primeira, segunda)
        self.assertEqual(primeira["semente_inicial"], 2026)
        self.assertTrue(
            all(registro["semente"] is not None for registro in primeira["historico"])
        )

    def test_jogador_inicial_pode_ser_max_ou_min(self):
        for jogador_inicial in (Jogador.MAX, Jogador.MIN):
            with self.subTest(jogador_inicial=jogador_inicial):
                partida = executar_partida(
                    agente_busca_limitada,
                    agente_busca_limitada,
                    pilha_a=1,
                    pilha_b=0,
                    jogador_inicial=jogador_inicial,
                    seed=7,
                )
                self.assertEqual(
                    partida["estado_inicial"],
                    Estado(1, 0, jogador_inicial),
                )
                self.assertEqual(partida["historico"][0]["jogador"], jogador_inicial)
                self.assertEqual(partida["vencedor"], jogador_inicial)

    def test_agentes_configurados_sao_chamados_no_papel_correto(self):
        for jogador_inicial in (Jogador.MAX, Jogador.MIN):
            with self.subTest(jogador_inicial=jogador_inicial):
                def agente_de_max(estado):
                    return acoes(estado)[0]

                def agente_de_min(estado):
                    return acoes(estado)[0]

                partida = executar_partida(
                    agente_de_max,
                    agente_de_min,
                    pilha_a=2,
                    pilha_b=1,
                    jogador_inicial=jogador_inicial,
                    seed=8,
                )

                for registro in partida["historico"]:
                    esperado = (
                        "agente_de_max"
                        if registro["jogador"] == Jogador.MAX
                        else "agente_de_min"
                    )
                    self.assertEqual(registro["agente"], esperado)
                self.assertEqual(
                    partida["historico"][-1]["jogador"],
                    partida["vencedor"],
                )

    def test_nos_registrados_correspondem_ao_retorno_do_agente(self):
        partida = executar_partida(
            agente_busca_limitada,
            agente_busca_limitada,
            pilha_a=2,
            pilha_b=1,
            seed=11,
        )

        for registro in partida["historico"]:
            jogada, _, nos_visitados = agente_busca_limitada(
                registro["estado_anterior"]
            )
            self.assertEqual(registro["jogada"], jogada)
            self.assertEqual(registro["nos_visitados"], nos_visitados)

    def test_sementes_diferentes_podem_produzir_historicos_diferentes(self):
        historicos = set()
        for seed in range(10):
            partida = executar_partida(
                agente_aleatorio,
                agente_aleatorio,
                pilha_a=3,
                pilha_b=2,
                seed=seed,
            )
            historico = tuple(
                (registro["jogada"], registro["estado_posterior"])
                for registro in partida["historico"]
            )
            historicos.add(historico)

        self.assertGreater(len(historicos), 1)

    def test_partida_inicialmente_terminal_nao_registra_jogadas(self):
        partida = executar_partida(
            agente_busca_limitada,
            agente_busca_limitada,
            pilha_a=0,
            pilha_b=0,
            seed=3,
        )

        self.assertEqual(partida["historico"], [])
        self.assertEqual(partida["quantidade_jogadas"], 0)
        self.assertIsNone(partida["vencedor"])

    def test_agente_sem_jogada_em_estado_nao_terminal_gera_erro(self):
        def agente_sem_jogada(estado):
            return None

        with self.assertRaises(ValueError):
            executar_partida(
                agente_sem_jogada,
                agente_busca_limitada,
                pilha_a=1,
                pilha_b=0,
                seed=1,
            )

    def test_jogadas_invalidas_nao_geram_resultado_de_partida(self):
        def agente_max(estado):
            return acoes(estado)[0]

        def agente_min_sem_jogada(estado):
            return None

        with self.assertRaises(ValueError):
            executar_partida(
                agente_max,
                agente_min_sem_jogada,
                pilha_a=1,
                pilha_b=1,
                seed=1,
            )

        def agente_com_jogada_ilegal(estado):
            return Jogada(Pilha.A, estado.pilha_a + 1)

        with self.assertRaises(ValueError):
            executar_partida(
                agente_com_jogada_ilegal,
                agente_busca_limitada,
                pilha_a=1,
                pilha_b=0,
                seed=1,
            )

    def test_retorno_de_agente_com_formato_invalido_gera_erro(self):
        def agente_formato_invalido(estado):
            return ("não é jogada",)

        with self.assertRaises(ValueError):
            executar_partida(
                agente_formato_invalido,
                agente_busca_limitada,
                pilha_a=1,
                pilha_b=0,
                seed=1,
            )


if __name__ == "__main__":
    unittest.main()
