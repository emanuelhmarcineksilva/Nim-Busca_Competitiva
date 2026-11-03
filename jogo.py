"""Regras do Nim de Duas Pilhas."""

from dataclasses import dataclass
from enum import Enum
from typing import List


class Jogador(Enum):
    MAX = "MAX"
    MIN = "MIN"


class Pilha(Enum):
    A = "A"
    B = "B"


@dataclass(frozen=True)
class Estado:
    pilha_a: int
    pilha_b: int
    jogador_atual: Jogador = Jogador.MAX

    def __post_init__(self) -> None:
        if not isinstance(self.pilha_a, int) or isinstance(self.pilha_a, bool):
            raise TypeError("A quantidade da pilha A deve ser um inteiro.")
        if not isinstance(self.pilha_b, int) or isinstance(self.pilha_b, bool):
            raise TypeError("A quantidade da pilha B deve ser um inteiro.")
        if self.pilha_a < 0 or self.pilha_b < 0:
            raise ValueError("As quantidades de pedras não podem ser negativas.")
        if not isinstance(self.jogador_atual, Jogador):
            raise TypeError("O jogador atual deve ser MAX ou MIN.")


@dataclass(frozen=True)
class Jogada:
    pilha: Pilha
    quantidade: int

    def __post_init__(self) -> None:
        if not isinstance(self.pilha, Pilha):
            raise TypeError("A pilha deve ser Pilha.A ou Pilha.B.")
        if not isinstance(self.quantidade, int) or isinstance(self.quantidade, bool):
            raise TypeError("A quantidade retirada deve ser um inteiro.")
        if self.quantidade <= 0:
            raise ValueError("A jogada deve retirar pelo menos uma pedra.")


def criar_estado_inicial(
    pilha_a: int = 8,
    pilha_b: int = 8,
    jogador_inicial: Jogador = Jogador.MAX,
) -> Estado:
    """Cria o estado inicial com quantidades configuráveis."""
    return Estado(pilha_a, pilha_b, jogador_inicial)


def jogador(estado: Estado) -> Jogador:
    """Retorna quem deve jogar no estado informado."""
    return estado.jogador_atual


def acoes(estado: Estado) -> List[Jogada]:
    """Retorna todas as retiradas legais disponíveis no estado."""
    jogadas: List[Jogada] = []
    for pilha, quantidade_disponivel in (
        (Pilha.A, estado.pilha_a),
        (Pilha.B, estado.pilha_b),
    ):
        for quantidade in range(1, quantidade_disponivel + 1):
            jogadas.append(Jogada(pilha, quantidade))
    return jogadas


def teste_terminal(estado: Estado) -> bool:
    """Indica se as duas pilhas estão vazias."""
    return estado.pilha_a == 0 and estado.pilha_b == 0


def resultado(estado: Estado, jogada: Jogada) -> Estado:
    """Aplica uma jogada legal e retorna um novo estado."""
    if teste_terminal(estado):
        raise ValueError("Não é possível jogar em um estado terminal.")
    if not isinstance(jogada, Jogada):
        raise TypeError("A jogada deve ser uma instância de Jogada.")

    quantidade_disponivel = (
        estado.pilha_a if jogada.pilha == Pilha.A else estado.pilha_b
    )
    if jogada.quantidade > quantidade_disponivel:
        raise ValueError("A jogada não é legal neste estado.")

    if jogada.pilha == Pilha.A:
        pilha_a = estado.pilha_a - jogada.quantidade
        pilha_b = estado.pilha_b
    else:
        pilha_a = estado.pilha_a
        pilha_b = estado.pilha_b - jogada.quantidade

    proximo_jogador = (
        Jogador.MIN if estado.jogador_atual == Jogador.MAX else Jogador.MAX
    )
    return Estado(pilha_a, pilha_b, proximo_jogador)


def utilidade(estado: Estado) -> int:
    """Retorna +1 ou -1 no terminal, sempre do ponto de vista de MAX."""
    if not teste_terminal(estado):
        raise ValueError("A utilidade só é definida para estados terminais.")

    vencedor = (
        Jogador.MIN
        if estado.jogador_atual == Jogador.MAX
        else Jogador.MAX
    )
    return 1 if vencedor == Jogador.MAX else -1
