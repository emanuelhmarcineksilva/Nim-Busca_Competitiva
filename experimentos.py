"""Execução de partidas e protocolo experimental do Nim de Duas Pilhas."""

import csv
import random
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from agentes import (
    alfa_beta,
    agente_aleatorio,
    agente_busca_limitada,
    agente_principal,
    minimax,
)
from jogo import (
    Estado,
    Jogada,
    Jogador,
    criar_estado_inicial,
    jogador,
    resultado,
    teste_terminal,
    utilidade,
)

Agente = Callable[..., Any]
CallbackProgresso = Callable[[Dict[str, Any]], None]
SEMENTE_MESTRE = 2026
REPETICOES_ALEATORIAS = 10
TAMANHO_PILHAS = 8


class ExecucaoCancelada(Exception):
    """Indica que uma execução experimental foi cancelada entre partidas."""


def _verificar_cancelamento(cancelar: Optional[Callable[[], bool]]) -> None:
    if cancelar is not None and cancelar():
        raise ExecucaoCancelada("A execução foi cancelada antes de iniciar outra partida.")


def _notificar_progresso(
    progresso: Optional[CallbackProgresso],
    concluidas: int,
    total: int,
    confronto: str,
    vitorias: Dict[str, int],
) -> None:
    if progresso is not None:
        progresso(
            {
                "concluidas": concluidas,
                "total": total,
                "restantes": total - concluidas,
                "confronto": confronto,
                "vitorias": dict(vitorias),
            }
        )


def _nome_agente(agente: Agente) -> str:
    return getattr(agente, "__name__", agente.__class__.__name__)


def _solicitar_jogada(
    agente: Agente,
    estado: Estado,
    gerador: random.Random,
) -> Tuple[Jogada, Optional[int], Optional[int]]:
    """Retorna jogada, nós visitados e semente usada, quando aplicável."""
    semente = None
    if agente is agente_aleatorio:
        semente = gerador.getrandbits(64)
        retorno = agente(estado, seed=semente)
    else:
        retorno = agente(estado)

    nos_visitados = None
    if isinstance(retorno, tuple) and len(retorno) == 3:
        primeira, segunda, nos = retorno
        if isinstance(primeira, Jogada) or primeira is None:
            jogada = primeira
        elif isinstance(segunda, Jogada) or segunda is None:
            jogada = segunda
        else:
            raise TypeError("O agente deve retornar uma jogada.")

        if not isinstance(nos, int) or isinstance(nos, bool) or nos < 0:
            raise ValueError("A quantidade de nós retornada pelo agente é inválida.")
        nos_visitados = nos
    else:
        jogada = retorno

    if not isinstance(jogada, Jogada):
        raise ValueError("O agente não retornou uma jogada válida.")
    return jogada, nos_visitados, semente


def executar_partida(
    agente_max: Agente,
    agente_min: Agente,
    pilha_a: int = 8,
    pilha_b: int = 8,
    jogador_inicial: Jogador = Jogador.MAX,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Executa uma partida e retorna o resultado e o histórico de jogadas.

    A semente inicial é registrada. Para cada turno do agente aleatório,
    um gerador persistente deriva e registra uma nova semente.
    Nós não aplicáveis, como no agente aleatório, são representados por None.
    """
    if seed is not None and (
        not isinstance(seed, int) or isinstance(seed, bool)
    ):
        raise TypeError("A semente deve ser um inteiro ou None.")

    semente_inicial = (
        seed if seed is not None else random.SystemRandom().getrandbits(64)
    )
    gerador = random.Random(semente_inicial)
    estado = criar_estado_inicial(pilha_a, pilha_b, jogador_inicial)
    estado_inicial = estado
    historico = []

    while not teste_terminal(estado):
        jogador_atual = jogador(estado)
        agente_atual = agente_max if jogador_atual == Jogador.MAX else agente_min
        jogada, nos_visitados, semente = _solicitar_jogada(
            agente_atual,
            estado,
            gerador,
        )
        estado_seguinte = resultado(estado, jogada)

        historico.append(
            {
                "numero_jogada": len(historico) + 1,
                "agente": _nome_agente(agente_atual),
                "jogador": jogador_atual,
                "estado_anterior": estado,
                "jogada": jogada,
                "estado_posterior": estado_seguinte,
                "nos_visitados": nos_visitados,
                "semente": semente,
            }
        )
        estado = estado_seguinte

    vencedor = None
    if historico:
        vencedor = Jogador.MAX if utilidade(estado) == 1 else Jogador.MIN

    return {
        "estado_inicial": estado_inicial,
        "estado_final": estado,
        "agente_max": _nome_agente(agente_max),
        "agente_min": _nome_agente(agente_min),
        "semente_inicial": semente_inicial,
        "vencedor": vencedor,
        "quantidade_jogadas": len(historico),
        "historico": historico,
    }


def gerar_posicoes_iniciais() -> List[Tuple[int, int]]:
    """Gera as 80 posições ordenadas previstas no protocolo."""
    return [
        (pilha_a, pilha_b)
        for pilha_a in range(TAMANHO_PILHAS + 1)
        for pilha_b in range(TAMANHO_PILHAS + 1)
        if (pilha_a, pilha_b) != (0, 0)
    ]


def gerar_combinacoes_papeis() -> List[Dict[str, Any]]:
    """Gera as quatro combinações de agente MAX e jogador inicial."""
    return [
        {
            "indice": 0,
            "agente_a_max": True,
            "jogador_inicial": Jogador.MAX,
        },
        {
            "indice": 1,
            "agente_a_max": True,
            "jogador_inicial": Jogador.MIN,
        },
        {
            "indice": 2,
            "agente_a_max": False,
            "jogador_inicial": Jogador.MAX,
        },
        {
            "indice": 3,
            "agente_a_max": False,
            "jogador_inicial": Jogador.MIN,
        },
    ]


def _configuracao_agente(
    nome: str,
    configuracao: str,
    funcao: Agente,
) -> Dict[str, Any]:
    return {
        "nome": nome,
        "configuracao": configuracao,
        "funcao": funcao,
    }


def _agente_busca(profundidade: int, ordenar: bool) -> Agente:
    return partial(
        agente_busca_limitada,
        profundidade=profundidade,
        ordenar=ordenar,
    )


def _agente_principal(profundidade: int) -> Agente:
    return partial(agente_principal, profundidade=profundidade)


def configurar_confrontos() -> List[Dict[str, Any]]:
    """Retorna as 16 configurações de confronto aprovadas."""
    aleatorio = _configuracao_agente(
        "Aleatório",
        "Agente aleatório",
        agente_aleatorio,
    )
    confrontos = []

    def adicionar(
        grupo: str,
        nome: str,
        agente_a: Dict[str, Any],
        agente_b: Dict[str, Any],
        aleatorizado: bool,
    ) -> None:
        confrontos.append(
            {
                "indice": len(confrontos),
                "grupo": grupo,
                "nome": nome,
                "agente_a": agente_a,
                "agente_b": agente_b,
                "aleatorizado": aleatorizado,
            }
        )

    for profundidade in range(1, 5):
        busca = _configuracao_agente(
            f"Busca limitada d{profundidade}, sem ordenação",
            f"profundidade={profundidade}; ordenação=desligada",
            _agente_busca(profundidade, ordenar=False),
        )
        adicionar(
            "agente_aleatorio",
            f"Aleatório vs busca limitada d{profundidade} sem ordenação",
            aleatorio,
            busca,
            True,
        )

    principal = _configuracao_agente(
        "Agente principal",
        "profundidade=3; ordenação=ligada",
        _agente_principal(3),
    )
    adicionar(
        "agente_aleatorio",
        "Aleatório vs agente principal d3 com ordenação",
        aleatorio,
        principal,
        True,
    )

    for profundidade_a, profundidade_b in (
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 3),
        (2, 4),
        (3, 4),
    ):
        busca_a = _configuracao_agente(
            f"Busca limitada d{profundidade_a}, sem ordenação",
            f"profundidade={profundidade_a}; ordenação=desligada",
            _agente_busca(profundidade_a, ordenar=False),
        )
        busca_b = _configuracao_agente(
            f"Busca limitada d{profundidade_b}, sem ordenação",
            f"profundidade={profundidade_b}; ordenação=desligada",
            _agente_busca(profundidade_b, ordenar=False),
        )
        adicionar(
            "profundidade",
            f"Profundidade d{profundidade_a} vs d{profundidade_b}, sem ordenação",
            busca_a,
            busca_b,
            False,
        )

    for profundidade in range(1, 5):
        sem_ordenacao = _configuracao_agente(
            f"Busca limitada d{profundidade}, sem ordenação",
            f"profundidade={profundidade}; ordenação=desligada",
            _agente_busca(profundidade, ordenar=False),
        )
        com_ordenacao = _configuracao_agente(
            f"Busca limitada d{profundidade}, com ordenação",
            f"profundidade={profundidade}; ordenação=ligada",
            _agente_busca(profundidade, ordenar=True),
        )
        adicionar(
            "ordenacao",
            f"Ordenação d{profundidade}: desligada vs ligada",
            sem_ordenacao,
            com_ordenacao,
            False,
        )

    busca_d1_ordenada = _configuracao_agente(
        "Busca limitada d1, com ordenação",
        "profundidade=1; ordenação=ligada",
        _agente_busca(1, ordenar=True),
    )
    principal_d3 = _configuracao_agente(
        "Agente principal",
        "profundidade=3; ordenação=ligada",
        _agente_principal(3),
    )
    adicionar(
        "comparacao_controlada",
        "Busca d1 ordenada vs agente principal d3 ordenado",
        busca_d1_ordenada,
        principal_d3,
        False,
    )

    return confrontos


def calcular_total_partidas(
    confrontos: Optional[List[Dict[str, Any]]] = None,
    quantidade_posicoes: int = 80,
    repeticoes_aleatorias: int = REPETICOES_ALEATORIAS,
) -> int:
    """Calcula quantas partidas as configurações selecionadas representam."""
    if confrontos is None:
        confrontos = configurar_confrontos()
    total = 0
    for confronto in confrontos:
        repeticoes = repeticoes_aleatorias if confronto["aleatorizado"] else 1
        total += quantidade_posicoes * 4 * repeticoes
    return total


def validar_protocolo_completo(
    confrontos: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """Confirma o número aprovado de confrontos e partidas do protocolo."""
    if confrontos is None:
        confrontos = configurar_confrontos()
    grupos = {}
    for confronto in confrontos:
        grupos[confronto["grupo"]] = grupos.get(confronto["grupo"], 0) + 1

    grupos_esperados = {
        "agente_aleatorio": 5,
        "profundidade": 6,
        "ordenacao": 4,
        "comparacao_controlada": 1,
    }
    total = calcular_total_partidas(confrontos)
    if len(confrontos) != 16 or grupos != grupos_esperados or total != 19_520:
        raise ValueError(
            "A configuração não corresponde ao protocolo aprovado: "
            f"{len(confrontos)} confrontos e {total} partidas."
        )
    return total


def derivar_semente_partida(
    indice_posicao: int,
    indice_combinacao: int,
    indice_repeticao: int,
    semente_mestre: int = SEMENTE_MESTRE,
) -> int:
    """Aplica a fórmula de sementes aprovada, sem depender do confronto."""
    return semente_mestre + (
        (indice_posicao * 4 + indice_combinacao) * REPETICOES_ALEATORIAS
        + indice_repeticao
    )


def _estado_csv(estado: Estado) -> str:
    return f"{estado.pilha_a}|{estado.pilha_b}|{estado.jogador_atual.value}"


def _jogada_csv(jogada: Jogada) -> str:
    return f"{jogada.pilha.value}:{jogada.quantidade}"


def _valor_na_csv(valor: Any) -> Any:
    return "N/A" if valor is None else valor


COLUNAS_JOGADAS = [
    "id_partida",
    "grupo_experimental",
    "confronto",
    "numero_turno",
    "agente",
    "configuracao_agente",
    "jogador",
    "estado_anterior",
    "jogada",
    "estado_posterior",
    "nos_visitados",
    "semente_mestre",
    "semente_partida",
    "semente_turno",
]

COLUNAS_PARTIDAS = [
    "id_partida",
    "grupo_experimental",
    "confronto",
    "configuracao_agente_a",
    "configuracao_agente_b",
    "pilha_a_inicial",
    "pilha_b_inicial",
    "agente_max",
    "agente_min",
    "jogador_inicial",
    "semente_mestre",
    "semente_partida",
    "indice_posicao",
    "indice_combinacao",
    "indice_repeticao",
    "vencedor",
    "agente_vencedor",
    "quantidade_jogadas",
    "resultado_final",
]

COLUNAS_RESUMO = [
    "grupo_experimental",
    "confronto",
    "agente",
    "configuracao_agente",
    "quantidade_partidas",
    "vitorias",
    "derrotas",
    "empates",
    "taxa_vitoria_percentual",
    "decisoes_busca",
    "media_nos_por_decisao",
    "maximo_nos_por_decisao",
]


def exportar_resultados(
    jogadas: List[Dict[str, Any]],
    partidas: List[Dict[str, Any]],
    resumos: List[Dict[str, Any]],
    diretorio: Any,
) -> Dict[str, str]:
    """Grava as três tabelas CSV e retorna seus caminhos."""
    caminho = Path(diretorio)
    caminho.mkdir(parents=True, exist_ok=True)
    tabelas = (
        ("jogadas.csv", COLUNAS_JOGADAS, jogadas),
        ("partidas.csv", COLUNAS_PARTIDAS, partidas),
        ("resumo.csv", COLUNAS_RESUMO, resumos),
    )
    caminhos = {}
    for nome_arquivo, colunas, linhas in tabelas:
        arquivo = caminho / nome_arquivo
        with arquivo.open("w", newline="", encoding="utf-8") as saida:
            escritor = csv.DictWriter(saida, fieldnames=colunas)
            escritor.writeheader()
            escritor.writerows(
                {
                    chave: _valor_na_csv(valor)
                    for chave, valor in linha.items()
                }
                for linha in linhas
            )
        caminhos[nome_arquivo] = str(arquivo)
    return caminhos


def _calcular_resumos(
    confrontos: List[Dict[str, Any]],
    partidas: List[Dict[str, Any]],
    jogadas: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    resumos = []
    for confronto in confrontos:
        partidas_confronto = [
            partida
            for partida in partidas
            if partida["confronto"] == confronto["nome"]
        ]
        configuracoes = (confronto["agente_a"], confronto["agente_b"])
        for configuracao in configuracoes:
            nome_agente = configuracao["nome"]
            vitorias = sum(
                partida["agente_vencedor"] == nome_agente
                for partida in partidas_confronto
            )
            empates = sum(
                partida["agente_vencedor"] is None
                for partida in partidas_confronto
            )
            derrotas = len(partidas_confronto) - vitorias - empates
            decisoes = [
                jogada["nos_visitados"]
                for jogada in jogadas
                if jogada["confronto"] == confronto["nome"]
                and jogada["agente"] == nome_agente
                and jogada["nos_visitados"] is not None
            ]
            resumos.append(
                {
                    "grupo_experimental": confronto["grupo"],
                    "confronto": confronto["nome"],
                    "agente": nome_agente,
                    "configuracao_agente": configuracao["configuracao"],
                    "quantidade_partidas": len(partidas_confronto),
                    "vitorias": vitorias,
                    "derrotas": derrotas,
                    "empates": empates,
                    "taxa_vitoria_percentual": (
                        100 * vitorias / len(partidas_confronto)
                        if partidas_confronto
                        else 0.0
                    ),
                    "decisoes_busca": len(decisoes),
                    "media_nos_por_decisao": (
                        sum(decisoes) / len(decisoes) if decisoes else "N/A"
                    ),
                    "maximo_nos_por_decisao": max(decisoes) if decisoes else "N/A",
                }
            )
    return resumos


def executar_experimentos(
    confrontos: Optional[List[Dict[str, Any]]] = None,
    posicoes: Optional[List[Tuple[int, int]]] = None,
    repeticoes_aleatorias: Optional[int] = None,
    diretorio_resultados: Optional[Any] = None,
    semente_mestre: int = SEMENTE_MESTRE,
    progresso: Optional[CallbackProgresso] = None,
    cancelar: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Executa confrontos selecionados e exporta jogadas, partidas e resumo.

    Sem parâmetros reduzidos, executa o protocolo completo. Para um piloto,
    informe confrontos, posições, repetições e uma pasta de saída separada.
    """
    if not isinstance(semente_mestre, int) or isinstance(semente_mestre, bool):
        raise TypeError("A semente mestre deve ser um inteiro.")

    todos_confrontos = configurar_confrontos()
    if (
        confrontos is None
        and posicoes is None
        and repeticoes_aleatorias is None
    ):
        validar_protocolo_completo(todos_confrontos)
    if confrontos is None:
        confrontos_selecionados = todos_confrontos
    else:
        por_nome = {confronto["nome"]: confronto for confronto in todos_confrontos}
        nomes_selecionados = [confronto.get("nome") for confronto in confrontos]
        if any(nome not in por_nome for nome in nomes_selecionados):
            raise ValueError("Foi selecionada uma configuração de confronto desconhecida.")
        if len(set(nomes_selecionados)) != len(nomes_selecionados):
            raise ValueError("Um confronto não pode ser selecionado mais de uma vez.")
        confrontos_selecionados = [por_nome[nome] for nome in nomes_selecionados]
    if not confrontos_selecionados:
        raise ValueError("É necessário selecionar pelo menos um confronto.")

    posicoes_com_indices = list(enumerate(gerar_posicoes_iniciais()))
    if posicoes is not None:
        if len(set(posicoes)) != len(posicoes):
            raise ValueError("A lista de posições iniciais não pode conter duplicatas.")
        indice_por_posicao = {
            posicao: indice for indice, posicao in posicoes_com_indices
        }
        try:
            posicoes_com_indices = [
                (indice_por_posicao[posicao], posicao) for posicao in posicoes
            ]
        except KeyError as erro:
            raise ValueError(f"Posição inicial inválida: {erro.args[0]}") from erro
    if repeticoes_aleatorias is None:
        repeticoes = REPETICOES_ALEATORIAS
    else:
        if (
            not isinstance(repeticoes_aleatorias, int)
            or isinstance(repeticoes_aleatorias, bool)
            or repeticoes_aleatorias < 1
        ):
            raise ValueError("As repetições aleatórias devem ser um inteiro positivo.")
        repeticoes = repeticoes_aleatorias

    combinacoes = gerar_combinacoes_papeis()
    partidas = []
    jogadas = []
    total_partidas = calcular_total_partidas(
        confrontos_selecionados,
        quantidade_posicoes=len(posicoes_com_indices),
        repeticoes_aleatorias=repeticoes,
    )
    partidas_concluidas = 0
    vitorias_parciais: Dict[str, int] = {}

    for indice_confronto, confronto in enumerate(confrontos_selecionados):
        repeticoes_confronto = repeticoes if confronto["aleatorizado"] else 1
        for indice_posicao, (pilha_a, pilha_b) in posicoes_com_indices:
            for combinacao in combinacoes:
                agente_max_cfg = (
                    confronto["agente_a"]
                    if combinacao["agente_a_max"]
                    else confronto["agente_b"]
                )
                agente_min_cfg = (
                    confronto["agente_b"]
                    if combinacao["agente_a_max"]
                    else confronto["agente_a"]
                )
                for indice_repeticao in range(repeticoes_confronto):
                    _verificar_cancelamento(cancelar)
                    semente_partida = (
                        derivar_semente_partida(
                            indice_posicao,
                            combinacao["indice"],
                            indice_repeticao,
                            semente_mestre,
                        )
                        if confronto["aleatorizado"]
                        else None
                    )
                    partida_id = (
                        f"c{indice_confronto:02d}-p{indice_posicao:02d}"
                        f"-k{combinacao['indice']}-r{indice_repeticao:02d}"
                    )
                    resultado_partida = executar_partida(
                        agente_max_cfg["funcao"],
                        agente_min_cfg["funcao"],
                        pilha_a=pilha_a,
                        pilha_b=pilha_b,
                        jogador_inicial=combinacao["jogador_inicial"],
                        seed=(
                            semente_partida
                            if semente_partida is not None
                            else semente_mestre
                        ),
                    )

                    vencedor = resultado_partida["vencedor"]
                    agente_vencedor = (
                        agente_max_cfg["nome"]
                        if vencedor == Jogador.MAX
                        else agente_min_cfg["nome"]
                        if vencedor == Jogador.MIN
                        else None
                    )
                    partidas.append(
                        {
                            "id_partida": partida_id,
                            "grupo_experimental": confronto["grupo"],
                            "confronto": confronto["nome"],
                            "configuracao_agente_a": confronto["agente_a"]["configuracao"],
                            "configuracao_agente_b": confronto["agente_b"]["configuracao"],
                            "pilha_a_inicial": pilha_a,
                            "pilha_b_inicial": pilha_b,
                            "agente_max": agente_max_cfg["nome"],
                            "agente_min": agente_min_cfg["nome"],
                            "jogador_inicial": combinacao["jogador_inicial"].value,
                            "semente_mestre": semente_mestre,
                            "semente_partida": _valor_na_csv(semente_partida),
                            "indice_posicao": indice_posicao,
                            "indice_combinacao": combinacao["indice"],
                            "indice_repeticao": indice_repeticao,
                            "vencedor": vencedor.value if vencedor else "N/A",
                            "agente_vencedor": agente_vencedor or "N/A",
                            "quantidade_jogadas": resultado_partida["quantidade_jogadas"],
                            "resultado_final": (
                                f"vitoria:{agente_vencedor}"
                                if agente_vencedor
                                else "empate"
                            ),
                        }
                    )

                    for registro in resultado_partida["historico"]:
                        configuracao_jogada = (
                            agente_max_cfg
                            if registro["jogador"] == Jogador.MAX
                            else agente_min_cfg
                        )
                        jogadas.append(
                            {
                                "id_partida": partida_id,
                                "grupo_experimental": confronto["grupo"],
                                "confronto": confronto["nome"],
                                "numero_turno": registro["numero_jogada"],
                                "agente": configuracao_jogada["nome"],
                                "configuracao_agente": configuracao_jogada["configuracao"],
                                "jogador": registro["jogador"].value,
                                "estado_anterior": _estado_csv(registro["estado_anterior"]),
                                "jogada": _jogada_csv(registro["jogada"]),
                                "estado_posterior": _estado_csv(registro["estado_posterior"]),
                                "nos_visitados": registro["nos_visitados"],
                                "semente_mestre": semente_mestre,
                                "semente_partida": _valor_na_csv(semente_partida),
                                "semente_turno": registro["semente"],
                            }
                        )
                    partidas_concluidas += 1
                    if vencedor is not None:
                        nome_vencedor = (
                            agente_max_cfg["nome"]
                            if vencedor == Jogador.MAX
                            else agente_min_cfg["nome"]
                        )
                        vitorias_parciais[nome_vencedor] = (
                            vitorias_parciais.get(nome_vencedor, 0) + 1
                        )
                    _notificar_progresso(
                        progresso,
                        partidas_concluidas,
                        total_partidas,
                        confronto["nome"],
                        vitorias_parciais,
                    )

    _verificar_cancelamento(cancelar)
    resumos = _calcular_resumos(confrontos_selecionados, partidas, jogadas)
    if diretorio_resultados is None:
        diretorio_resultados = Path(__file__).resolve().parent / "resultados"
    caminhos_csv = exportar_resultados(
        jogadas,
        partidas,
        resumos,
        diretorio_resultados,
    )
    return {
        "confrontos": confrontos_selecionados,
        "partidas": partidas,
        "jogadas": jogadas,
        "resumo": resumos,
        "caminhos_csv": caminhos_csv,
    }


def _configuracao_personalizada(
    agente: str,
    profundidade: int,
    ordenar: bool,
) -> Dict[str, Any]:
    if agente == "Aleatório":
        return _configuracao_agente("Aleatório", "Agente aleatório", agente_aleatorio)
    if agente == "Minimax completo":
        return _configuracao_agente(
            "Minimax completo", "busca completa", minimax
        )
    if agente == "Alpha-Beta completo":
        return _configuracao_agente(
            "Alpha-Beta completo", "busca completa", alfa_beta
        )
    if agente == "Alpha-Beta limitado":
        return _configuracao_agente(
            f"Alpha-Beta limitado d{profundidade}, "
            f"ordenação={'ligada' if ordenar else 'desligada'}",
            f"profundidade={profundidade}; "
            f"ordenação={'ligada' if ordenar else 'desligada'}",
            partial(agente_busca_limitada, profundidade=profundidade, ordenar=ordenar),
        )
    if agente == "Agente principal":
        return _configuracao_agente(
            f"Agente principal d{profundidade}, ordenação ligada",
            f"profundidade={profundidade}; ordenação=ligada",
            partial(agente_principal, profundidade=profundidade),
        )
    raise ValueError(f"Agente personalizado desconhecido: {agente}")


def executar_confronto_personalizado(
    agente_max: str,
    agente_min: str,
    posicoes: List[Tuple[int, int]],
    repeticoes: int,
    jogador_inicial: Jogador,
    semente_mestre: int,
    diretorio_resultados: Any,
    profundidade_max: int = 3,
    profundidade_min: int = 3,
    ordenar_max: bool = False,
    ordenar_min: bool = False,
    progresso: Optional[CallbackProgresso] = None,
    cancelar: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Executa um confronto personalizado reutilizando o motor de partidas."""
    if not posicoes:
        raise ValueError("Informe pelo menos uma posição inicial.")
    if len(set(posicoes)) != len(posicoes):
        raise ValueError("As posições iniciais não podem conter duplicatas.")
    for pilha_a, pilha_b in posicoes:
        criar_estado_inicial(pilha_a, pilha_b, jogador_inicial)
        if (pilha_a, pilha_b) == (0, 0):
            raise ValueError("A posição (0, 0) já é terminal e não inicia uma partida.")
    if (
        not isinstance(repeticoes, int)
        or isinstance(repeticoes, bool)
        or repeticoes < 1
    ):
        raise ValueError("A quantidade de repetições deve ser um inteiro positivo.")
    if not isinstance(jogador_inicial, Jogador):
        raise TypeError("O jogador inicial deve ser MAX ou MIN.")
    if not isinstance(semente_mestre, int) or isinstance(semente_mestre, bool):
        raise TypeError("A semente mestre deve ser um inteiro.")
    for lado, nome, profundidade, ordenar in (
        ("MAX", agente_max, profundidade_max, ordenar_max),
        ("MIN", agente_min, profundidade_min, ordenar_min),
    ):
        if nome in {"Alpha-Beta limitado", "Agente principal"} and (
            not isinstance(profundidade, int)
            or isinstance(profundidade, bool)
            or profundidade < 1
        ):
            raise ValueError(f"A profundidade de {lado} deve ser um inteiro positivo.")
        if not isinstance(ordenar, bool):
            raise TypeError(f"A ordenação de {lado} deve ser booleana.")

    max_cfg = _configuracao_personalizada(
        agente_max, profundidade_max, ordenar_max
    )
    min_cfg = _configuracao_personalizada(
        agente_min, profundidade_min, ordenar_min
    )
    max_cfg["nome"] = f"{max_cfg['nome']} (MAX)"
    min_cfg["nome"] = f"{min_cfg['nome']} (MIN)"
    confronto = {
        "indice": 0,
        "grupo": "personalizado",
        "nome": f"Personalizado: {max_cfg['nome']} vs {min_cfg['nome']}",
        "agente_a": max_cfg,
        "agente_b": min_cfg,
        "aleatorizado": agente_max == "Aleatório" or agente_min == "Aleatório",
    }

    partidas: List[Dict[str, Any]] = []
    jogadas: List[Dict[str, Any]] = []
    total_partidas = len(posicoes) * repeticoes
    concluidas = 0
    vitorias: Dict[str, int] = {}
    for indice_posicao, (pilha_a, pilha_b) in enumerate(posicoes):
        for indice_repeticao in range(repeticoes):
            _verificar_cancelamento(cancelar)
            indice_partida = indice_posicao * repeticoes + indice_repeticao
            semente_partida = semente_mestre + indice_partida
            partida_id = f"custom-p{indice_posicao:03d}-r{indice_repeticao:04d}"
            resultado_partida = executar_partida(
                max_cfg["funcao"],
                min_cfg["funcao"],
                pilha_a=pilha_a,
                pilha_b=pilha_b,
                jogador_inicial=jogador_inicial,
                seed=semente_partida,
            )
            vencedor = resultado_partida["vencedor"]
            nome_vencedor = (
                max_cfg["nome"]
                if vencedor == Jogador.MAX
                else min_cfg["nome"]
                if vencedor == Jogador.MIN
                else None
            )
            partidas.append(
                {
                    "id_partida": partida_id,
                    "grupo_experimental": "personalizado",
                    "confronto": confronto["nome"],
                    "configuracao_agente_a": max_cfg["configuracao"],
                    "configuracao_agente_b": min_cfg["configuracao"],
                    "pilha_a_inicial": pilha_a,
                    "pilha_b_inicial": pilha_b,
                    "agente_max": max_cfg["nome"],
                    "agente_min": min_cfg["nome"],
                    "jogador_inicial": jogador_inicial.value,
                    "semente_mestre": semente_mestre,
                    "semente_partida": semente_partida,
                    "indice_posicao": indice_posicao,
                    "indice_combinacao": 0 if jogador_inicial == Jogador.MAX else 1,
                    "indice_repeticao": indice_repeticao,
                    "vencedor": vencedor.value if vencedor else "N/A",
                    "agente_vencedor": nome_vencedor or "N/A",
                    "quantidade_jogadas": resultado_partida["quantidade_jogadas"],
                    "resultado_final": f"vitoria:{nome_vencedor}" if nome_vencedor else "empate",
                }
            )
            for registro in resultado_partida["historico"]:
                configuracao = (
                    max_cfg if registro["jogador"] == Jogador.MAX else min_cfg
                )
                jogadas.append(
                    {
                        "id_partida": partida_id,
                        "grupo_experimental": "personalizado",
                        "confronto": confronto["nome"],
                        "numero_turno": registro["numero_jogada"],
                        "agente": configuracao["nome"],
                        "configuracao_agente": configuracao["configuracao"],
                        "jogador": registro["jogador"].value,
                        "estado_anterior": _estado_csv(registro["estado_anterior"]),
                        "jogada": _jogada_csv(registro["jogada"]),
                        "estado_posterior": _estado_csv(registro["estado_posterior"]),
                        "nos_visitados": registro["nos_visitados"],
                        "semente_mestre": semente_mestre,
                        "semente_partida": semente_partida,
                        "semente_turno": registro["semente"],
                    }
                )
            concluidas += 1
            if nome_vencedor:
                vitorias[nome_vencedor] = vitorias.get(nome_vencedor, 0) + 1
            _notificar_progresso(
                progresso, concluidas, total_partidas, confronto["nome"], vitorias
            )

    _verificar_cancelamento(cancelar)
    resumos = _calcular_resumos([confronto], partidas, jogadas)
    caminhos_csv = exportar_resultados(
        jogadas, partidas, resumos, diretorio_resultados
    )
    return {
        "confrontos": [confronto],
        "partidas": partidas,
        "jogadas": jogadas,
        "resumo": resumos,
        "caminhos_csv": caminhos_csv,
    }
