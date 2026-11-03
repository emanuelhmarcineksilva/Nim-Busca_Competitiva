import csv
import tempfile
import threading
import unittest
from pathlib import Path

from experimentos import (
    ExecucaoCancelada,
    REPETICOES_ALEATORIAS,
    SEMENTE_MESTRE,
    calcular_total_partidas,
    configurar_confrontos,
    derivar_semente_partida,
    executar_experimentos,
    gerar_combinacoes_papeis,
    gerar_posicoes_iniciais,
    validar_protocolo_completo,
)
from jogo import Jogador


class TesteProtocoloExperimentos(unittest.TestCase):
    def test_sao_geradas_as_80_posicoes_ordenadas(self):
        posicoes = gerar_posicoes_iniciais()

        self.assertEqual(len(posicoes), 80)
        self.assertNotIn((0, 0), posicoes)
        self.assertEqual(len(set(posicoes)), 80)
        self.assertIn((3, 5), posicoes)
        self.assertIn((5, 3), posicoes)
        self.assertEqual(posicoes[0], (0, 1))

    def test_sao_geradas_quatro_combinacoes_de_papeis(self):
        combinacoes = gerar_combinacoes_papeis()

        self.assertEqual(len(combinacoes), 4)
        self.assertEqual(
            [
                (c["agente_a_max"], c["jogador_inicial"])
                for c in combinacoes
            ],
            [
                (True, Jogador.MAX),
                (True, Jogador.MIN),
                (False, Jogador.MAX),
                (False, Jogador.MIN),
            ],
        )

    def test_configuracao_tem_16_confrontos_com_distribuicao_aprovada(self):
        confrontos = configurar_confrontos()
        grupos = {}
        for confronto in confrontos:
            grupos[confronto["grupo"]] = grupos.get(confronto["grupo"], 0) + 1

        self.assertEqual(len(confrontos), 16)
        self.assertEqual(
            grupos,
            {
                "agente_aleatorio": 5,
                "profundidade": 6,
                "ordenacao": 4,
                "comparacao_controlada": 1,
            },
        )

    def test_protocolo_completo_planeja_19520_partidas(self):
        confrontos = configurar_confrontos()

        self.assertEqual(
            calcular_total_partidas(confrontos),
            19_520,
        )
        self.assertEqual(validar_protocolo_completo(confrontos), 19_520)
        total_por_grupo = {}
        for confronto in confrontos:
            repeticoes = REPETICOES_ALEATORIAS if confronto["aleatorizado"] else 1
            total_por_grupo[confronto["grupo"]] = (
                total_por_grupo.get(confronto["grupo"], 0) + 80 * 4 * repeticoes
            )
        self.assertEqual(
            total_por_grupo,
            {
                "agente_aleatorio": 16_000,
                "profundidade": 1_920,
                "ordenacao": 1_280,
                "comparacao_controlada": 320,
            },
        )

    def test_semente_segue_formula_aprovada(self):
        self.assertEqual(derivar_semente_partida(0, 0, 0), 2026)
        self.assertEqual(derivar_semente_partida(1, 2, 4), 2090)

    def test_piloto_gera_csvs_consistentes_e_reproduziveis(self):
        todos = configurar_confrontos()
        confrontos = [todos[0], todos[4], todos[5]]
        posicoes = [(0, 1), (1, 0)]

        with tempfile.TemporaryDirectory() as primeiro_dir, tempfile.TemporaryDirectory() as segundo_dir:
            primeiro = executar_experimentos(
                confrontos=confrontos,
                posicoes=posicoes,
                repeticoes_aleatorias=2,
                diretorio_resultados=primeiro_dir,
            )
            segundo = executar_experimentos(
                confrontos=confrontos,
                posicoes=posicoes,
                repeticoes_aleatorias=2,
                diretorio_resultados=segundo_dir,
            )

            self.assertEqual(len(primeiro["partidas"]), 40)
            self.assertEqual(len(primeiro["partidas"]), len(segundo["partidas"]))
            self.assertEqual(len(primeiro["jogadas"]), len(segundo["jogadas"]))
            self.assertEqual(primeiro["partidas"], segundo["partidas"])
            self.assertEqual(primeiro["jogadas"], segundo["jogadas"])

            for nome in ("jogadas.csv", "partidas.csv", "resumo.csv"):
                arquivo_a = Path(primeiro_dir) / nome
                arquivo_b = Path(segundo_dir) / nome
                self.assertTrue(arquivo_a.is_file())
                self.assertEqual(arquivo_a.read_bytes(), arquivo_b.read_bytes())

            with (Path(primeiro_dir) / "partidas.csv").open(
                newline="", encoding="utf-8"
            ) as arquivo:
                partidas_csv = list(csv.DictReader(arquivo))
            with (Path(primeiro_dir) / "jogadas.csv").open(
                newline="", encoding="utf-8"
            ) as arquivo:
                jogadas_csv = list(csv.DictReader(arquivo))
            with (Path(primeiro_dir) / "resumo.csv").open(
                newline="", encoding="utf-8"
            ) as arquivo:
                resumo_csv = list(csv.DictReader(arquivo))

            self.assertEqual(len(partidas_csv), 40)
            self.assertEqual(len({linha["id_partida"] for linha in partidas_csv}), 40)
            self.assertEqual(len(jogadas_csv), len(primeiro["jogadas"]))
            self.assertEqual(len(resumo_csv), 6)
            self._validar_registros_piloto(partidas_csv, jogadas_csv)
            self._validar_resumos(primeiro["resumo"], primeiro["jogadas"])
            self.assertEqual(
                resumo_csv,
                [
                    {chave: str(valor) for chave, valor in resumo.items()}
                    for resumo in primeiro["resumo"]
                ],
            )

    def test_sementes_sao_reutilizadas_entre_confrontos_aleatorizados(self):
        confrontos = configurar_confrontos()
        com_aleatorio = [confrontos[0], confrontos[1]]

        with tempfile.TemporaryDirectory() as diretorio:
            resultado_piloto = executar_experimentos(
                confrontos=com_aleatorio,
                posicoes=[(0, 1)],
                repeticoes_aleatorias=2,
                diretorio_resultados=diretorio,
            )
        por_confronto = {}
        for partida in resultado_piloto["partidas"]:
            chave = (
                partida["indice_posicao"],
                partida["indice_combinacao"],
                partida["indice_repeticao"],
            )
            por_confronto.setdefault(partida["confronto"], {})[chave] = int(
                partida["semente_partida"]
            )

        primeira, segunda = por_confronto.values()
        self.assertEqual(primeira, segunda)
        for (indice_posicao, indice_combinacao, indice_repeticao), semente in primeira.items():
            esperado = SEMENTE_MESTRE + (
                (indice_posicao * 4 + indice_combinacao) * 10
                + indice_repeticao
            )
            self.assertEqual(semente, esperado)

    def test_nomes_e_configuracoes_dos_agentes_sao_preservados(self):
        confrontos = configurar_confrontos()
        aleatorio_vs_busca_d1 = confrontos[0]
        with tempfile.TemporaryDirectory() as diretorio:
            piloto = executar_experimentos(
                confrontos=[aleatorio_vs_busca_d1],
                posicoes=[(1, 0)],
                repeticoes_aleatorias=1,
                diretorio_resultados=diretorio,
            )

        for partida in piloto["partidas"]:
            if partida["indice_combinacao"] in (0, 1):
                self.assertEqual(partida["agente_max"], "Aleatório")
                self.assertIn("Busca limitada d1", partida["agente_min"])
            else:
                self.assertIn("Busca limitada d1", partida["agente_max"])
                self.assertEqual(partida["agente_min"], "Aleatório")

    def test_cancelamento_entre_partidas_nao_exporta_csv_parcial(self):
        eventos = []
        cancelamento = threading.Event()

        with tempfile.TemporaryDirectory() as diretorio:
            with self.assertRaises(ExecucaoCancelada):
                executar_experimentos(
                    confrontos=[configurar_confrontos()[0]],
                    posicoes=[(1, 0)],
                    repeticoes_aleatorias=2,
                    diretorio_resultados=diretorio,
                    progresso=lambda evento: (
                        eventos.append(evento),
                        cancelamento.set(),
                    ),
                    cancelar=cancelamento.is_set,
                )

            self.assertEqual(len(eventos), 1)
            self.assertEqual(eventos[0]["concluidas"], 1)
            self.assertEqual(eventos[0]["restantes"], 7)
            self.assertEqual(list(Path(diretorio).iterdir()), [])

    @staticmethod
    def _validar_registros_piloto(partidas_csv, jogadas_csv):
        jogadas_por_partida = {}
        for jogada in jogadas_csv:
            jogadas_por_partida.setdefault(jogada["id_partida"], []).append(jogada)
            if jogada["agente"] == "Aleatório":
                assert jogada["nos_visitados"] == "N/A"

        for partida in partidas_csv:
            jogadas = jogadas_por_partida.get(partida["id_partida"], [])
            assert len(jogadas) == int(partida["quantidade_jogadas"])
            for numero, jogada in enumerate(jogadas, start=1):
                assert int(jogada["numero_turno"]) == numero
                assert jogada["jogador"] in ("MAX", "MIN")
                a, b, jogador_atual = jogada["estado_anterior"].split("|")
                pilha, quantidade = jogada["jogada"].split(":")
                esperado_a = int(a) - int(quantidade) if pilha == "A" else int(a)
                esperado_b = int(b) - int(quantidade) if pilha == "B" else int(b)
                assert jogada["jogador"] == jogador_atual
                assert f"{esperado_a}|{esperado_b}|" in jogada["estado_posterior"]
                if numero > 1:
                    assert (
                        jogadas[numero - 2]["estado_posterior"]
                        == jogada["estado_anterior"]
                    )
            assert partida["vencedor"] in ("MAX", "MIN")
            assert partida["agente_vencedor"] != "N/A"
            assert jogadas[-1]["jogador"] == partida["vencedor"]
            assert jogadas[-1]["estado_posterior"].startswith("0|0|")

    @staticmethod
    def _validar_resumos(resumos, jogadas):
        for resumo in resumos:
            agente = resumo["agente"]
            confronto = resumo["confronto"]
            nos = [
                jogada["nos_visitados"]
                for jogada in jogadas
                if jogada["agente"] == agente
                and jogada["confronto"] == confronto
                and jogada["nos_visitados"] is not None
            ]
            assert resumo["vitorias"] + resumo["derrotas"] + resumo["empates"] == resumo["quantidade_partidas"]
            assert resumo["taxa_vitoria_percentual"] == (
                100 * resumo["vitorias"] / resumo["quantidade_partidas"]
            )
            assert resumo["decisoes_busca"] == len(nos)
            if nos:
                assert resumo["media_nos_por_decisao"] == sum(nos) / len(nos)
                assert resumo["maximo_nos_por_decisao"] == max(nos)
            else:
                assert resumo["media_nos_por_decisao"] == "N/A"
                assert resumo["maximo_nos_por_decisao"] == "N/A"


if __name__ == "__main__":
    unittest.main()
