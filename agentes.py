"""Agentes de busca para o Nim de Duas Pilhas."""

import random
from typing import List, Optional, Tuple, Union

from jogo import Estado, Jogada, Jogador, acoes, jogador, resultado, teste_terminal, utilidade


def agente_aleatorio(estado: Estado, seed: Optional[int] = None) -> Optional[Jogada]:
    """Escolhe uma ação legal aleatoriamente; retorna None em estado terminal."""
    jogadas = acoes(estado)
    if not jogadas:
        return None
    return random.Random(seed).choice(jogadas)


def minimax(estado: Estado) -> Tuple[int, Optional[Jogada], int]:
    """Busca todas as continuações e retorna (valor, melhor jogada, nós).

    Um nó visitado é cada estado em que minimax é chamado, incluindo a raiz
    e os estados terminais. Sem memoização, um estado repetido em ramos
    diferentes é contado novamente. Empates de valor mantêm a primeira ação
    na ordem retornada por acoes().
    """
    if teste_terminal(estado):
        return utilidade(estado), None, 1

    melhor_jogada: Optional[Jogada] = None
    melhor_valor: Optional[int] = None
    nos_visitados = 1

    for jogada in acoes(estado):
        estado_seguinte = resultado(estado, jogada)
        valor_seguinte, _, nos_seguinte = minimax(estado_seguinte)
        nos_visitados += nos_seguinte

        if (
            melhor_valor is None
            or (
                jogador(estado) == Jogador.MAX
                and valor_seguinte > melhor_valor
            )
            or (
                jogador(estado) == Jogador.MIN
                and valor_seguinte < melhor_valor
            )
        ):
            melhor_valor = valor_seguinte
            melhor_jogada = jogada

    return melhor_valor, melhor_jogada, nos_visitados


def ordenar_acoes(estado: Estado) -> List[Jogada]:
    """Prioriza jogadas que deixam as duas pilhas com a mesma quantidade."""
    def prioridade(jogada: Jogada) -> bool:
        proximo = resultado(estado, jogada)
        return (proximo.pilha_a ^ proximo.pilha_b) != 0

    return sorted(
        acoes(estado),
        key=prioridade,
    )


def avaliacao_heuristica(estado: Estado) -> float:
    """Estima a posição pela perspectiva de MAX, sem alterar utilidade terminal.

    Ter exatamente uma pilha não vazia significa que o jogador da vez pode
    retirar todas as pedras e vencer imediatamente. Esse sinal recebe peso
    0.8; a paridade total é um sinal aproximado, de peso 0.2.
    """
    if teste_terminal(estado):
        return utilidade(estado)

    existe_vitoria_imediata = (estado.pilha_a == 0) != (estado.pilha_b == 0)
    caracteristica_vitoria = 1.0 if existe_vitoria_imediata else 0.0
    caracteristica_paridade = (
        1.0 if (estado.pilha_a + estado.pilha_b) % 2 == 1 else -1.0
    )
    valor_para_jogador_atual = (
        0.8 * caracteristica_vitoria + 0.2 * caracteristica_paridade
    )

    if jogador(estado) == Jogador.MAX:
        return valor_para_jogador_atual
    return -valor_para_jogador_atual


def alfa_beta_limitado(
    estado: Estado,
    profundidade_maxima: int,
    alpha: float = float("-inf"),
    beta: float = float("inf"),
    ordenar: bool = False,
) -> Tuple[Union[int, float], Optional[Jogada], int]:
    """Alfa-Beta com corte por profundidade e avaliação heurística."""
    if (
        not isinstance(profundidade_maxima, int)
        or isinstance(profundidade_maxima, bool)
        or profundidade_maxima < 0
    ):
        raise ValueError("A profundidade máxima deve ser um inteiro não negativo.")

    def buscar(
        posicao: Estado,
        profundidade: int,
        alpha_atual: float,
        beta_atual: float,
    ) -> Tuple[Union[int, float], Optional[Jogada], int]:
        if teste_terminal(posicao):
            return utilidade(posicao), None, 1
        if profundidade == profundidade_maxima:
            return avaliacao_heuristica(posicao), None, 1

        nos_visitados = 1
        melhor_jogada: Optional[Jogada] = None
        melhor_valor: Optional[Union[int, float]] = None
        jogadas = ordenar_acoes(posicao) if ordenar else acoes(posicao)

        if jogador(posicao) == Jogador.MAX:
            for jogada in jogadas:
                valor_seguinte, _, nos_seguinte = buscar(
                    resultado(posicao, jogada),
                    profundidade + 1,
                    alpha_atual,
                    beta_atual,
                )
                nos_visitados += nos_seguinte
                if melhor_valor is None or valor_seguinte > melhor_valor:
                    melhor_valor = valor_seguinte
                    melhor_jogada = jogada

                alpha_atual = max(alpha_atual, melhor_valor)
                if alpha_atual >= beta_atual:
                    break
        else:
            for jogada in jogadas:
                valor_seguinte, _, nos_seguinte = buscar(
                    resultado(posicao, jogada),
                    profundidade + 1,
                    alpha_atual,
                    beta_atual,
                )
                nos_visitados += nos_seguinte
                if melhor_valor is None or valor_seguinte < melhor_valor:
                    melhor_valor = valor_seguinte
                    melhor_jogada = jogada

                beta_atual = min(beta_atual, melhor_valor)
                if alpha_atual >= beta_atual:
                    break

        return melhor_valor, melhor_jogada, nos_visitados

    return buscar(estado, 0, alpha, beta)


def alfa_beta(
    estado: Estado,
    alpha: float = float("-inf"),
    beta: float = float("inf"),
    ordenar: bool = False,
) -> Tuple[int, Optional[Jogada], int]:
    """Busca até os terminais e retorna (valor, melhor jogada, nós visitados).

    Cada chamada recursiva conta um nó, incluindo raiz e terminais. Ramos
    descartados por alpha >= beta não são visitados nem contabilizados.
    Com ordenar=True, examina primeiro jogadas que deixam pilhas iguais.
    """
    if teste_terminal(estado):
        return utilidade(estado), None, 1

    nos_visitados = 1
    melhor_jogada: Optional[Jogada] = None
    melhor_valor: Optional[int] = None
    jogadas = ordenar_acoes(estado) if ordenar else acoes(estado)

    if jogador(estado) == Jogador.MAX:
        for jogada in jogadas:
            estado_seguinte = resultado(estado, jogada)
            valor_seguinte, _, nos_seguinte = alfa_beta(
                estado_seguinte, alpha, beta, ordenar
            )
            nos_visitados += nos_seguinte

            if melhor_valor is None or valor_seguinte > melhor_valor:
                melhor_valor = valor_seguinte
                melhor_jogada = jogada

            alpha = max(alpha, melhor_valor)
            if alpha >= beta:
                break
    else:
        for jogada in jogadas:
            estado_seguinte = resultado(estado, jogada)
            valor_seguinte, _, nos_seguinte = alfa_beta(
                estado_seguinte, alpha, beta, ordenar
            )
            nos_visitados += nos_seguinte

            if melhor_valor is None or valor_seguinte < melhor_valor:
                melhor_valor = valor_seguinte
                melhor_jogada = jogada

            beta = min(beta, melhor_valor)
            if alpha >= beta:
                break

    return melhor_valor, melhor_jogada, nos_visitados


def agente_busca_limitada(
    estado: Estado,
    profundidade: int = 1,
    ordenar: bool = False,
) -> Tuple[Optional[Jogada], Union[int, float], int]:
    """Agente de referência: Alfa-Beta limitado sem ordenação por padrão.

    Estados terminais retornam (None, utilidade, 1). Em estados não terminais,
    a profundidade precisa ser suficiente para selecionar uma jogada.
    """
    valor, jogada, nos_visitados = alfa_beta_limitado(
        estado,
        profundidade,
        ordenar=ordenar,
    )
    if jogada is None and not teste_terminal(estado):
        raise ValueError(
            "A profundidade deve ser pelo menos 1 para escolher uma jogada."
        )
    return jogada, valor, nos_visitados


def agente_principal(
    estado: Estado,
    profundidade: int = 3,
) -> Tuple[Optional[Jogada], Union[int, float], int]:
    """Agente de busca mais robusta, com ordenação ativada por padrão.

    A profundidade padrão 3 é uma proposta inicial e deve ser avaliada nos
    experimentos antes de ser considerada definitiva.
    """
    valor, jogada, nos_visitados = alfa_beta_limitado(
        estado,
        profundidade,
        ordenar=True,
    )
    if jogada is None and not teste_terminal(estado):
        raise ValueError(
            "A profundidade deve ser pelo menos 1 para escolher uma jogada."
        )
    return jogada, valor, nos_visitados
