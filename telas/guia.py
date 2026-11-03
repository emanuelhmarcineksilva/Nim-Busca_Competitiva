"""Guia interativo do TDE2, baseado na implementação e nos dados do projeto."""

import tkinter as tk
from tkinter import ttk

from telas.resultados import (
    PASTA_RESULTADOS,
    carregar_resultados,
    calcular_indicadores_gerais,
    obter_estatisticas_ordenacao,
    obter_estatisticas_profundidade,
)


SECOES = {
    "Visão geral do projeto": (
        "O Nim Lab é um projeto didático do TDE2 sobre busca competitiva. "
        "Ele reúne as regras do Nim de Duas Pilhas, agentes de jogo, experimentos "
        "reprodutíveis e uma interface para estudar os algoritmos.\n\n"
        "Os módulos de regras (`jogo.py`) e de agentes (`agentes.py`) são separados: "
        "a interface e os experimentos chamam essas funções em vez de reescrever "
        "as regras ou a busca.\n\n"
        "O relatório acadêmico continua sendo uma entrega separada. "
        "`DocumentoFinalEntrega.md` é o template da disciplina; esta aba é um guia "
        "de estudo, não o relatório preenchido."
    ),
    "Regras do Nim de Duas Pilhas": (
        "Há duas pilhas de pedras, A e B. Em cada turno, o jogador escolhe uma única "
        "pilha e retira uma ou mais peças dela. Não pode retirar peças de ambas na "
        "mesma jogada.\n\n"
        "É permitido retirar todas as peças de uma pilha porque a regra exige uma "
        "retirada positiva de uma pilha, até a quantidade disponível. Quem retira a "
        "última pedra vence. Quando ambas as pilhas ficam vazias, a partida terminou.\n\n"
        "Exemplo: em (A=2, B=1), retirar duas de A leva a (A=0, B=1), e o turno passa "
        "ao outro jogador."
    ),
    "Formalização do problema": (
        "O estado é s = (a, b, j), em que a e b são quantidades não negativas e j é "
        "MAX ou MIN, o jogador que fará a próxima jogada.\n\n"
        "Estado inicial: as pilhas podem ser configuradas; a interface de partida "
        "permite até oito peças em cada pilha. Ações: retirar k peças de A ou B, "
        "com 1 ≤ k ≤ quantidade daquela pilha.\n\n"
        "Transição: RESULTADO(s, ação) diminui uma pilha e alterna o jogador. Terminal: "
        "a=b=0. Utilidade: +1 se MAX venceu, -1 se MIN venceu. Não há empate nas regras "
        "implementadas.\n\n"
        "O estado terminal registra quem jogaria em seguida; portanto o vencedor é o "
        "oposto desse jogador. A utilidade continua sempre na perspectiva de MAX."
    ),
    "Estados e ações": (
        "A classe Estado é imutável e valida quantidades inteiras não negativas e um "
        "jogador válido. Jogada guarda a pilha e quantas pedras retirar.\n\n"
        "Exemplo: (3, 3, MAX) significa três peças em cada pilha e MAX na vez. "
        "A:1 significa retirar uma peça da pilha A; o resultado é (2, 3, MIN).\n\n"
        "As funções acoes(), resultado(), teste_terminal() e utilidade() em jogo.py "
        "são a fonte única das regras."
    ),
    "Agentes implementados": (
        "Aleatório escolhe uma ação legal usando uma semente recebida. Minimax completo "
        "e Alfa-Beta completo buscam até os estados terminais. Alpha-Beta limitado "
        "aplica um limite de profundidade e usa avaliação heurística nas folhas não "
        "terminais. O agente principal usa profundidade 3 e ordenação ligada.\n\n"
        "A tela Partida permite escolher quem controla MAX e MIN, quem começa e, quando "
        "aplicável, a profundidade. MAX/MIN são papéis; não significam necessariamente "
        "que uma pessoa sempre inicia."
    ),
    "Minimax": (
        "Minimax examina todas as continuações até os terminais. Nos nós de MAX, "
        "escolhe o maior valor; nos nós de MIN, escolhe o menor. A utilidade das folhas "
        "é calculada da perspectiva de MAX.\n\n"
        "A versão minimax() do projeto é pura: não usa poda, ordenação nem heurística. "
        "Desempata pela primeira ação legal encontrada.\n\n"
        "Exemplo: se MAX compara sucessores com valores -1 e +1, prefere +1. Se MIN "
        "está na vez, prefere -1."
    ),
    "Alpha-Beta": (
        "Alfa-Beta mantém dois limites: alpha é o melhor valor que MAX já consegue "
        "garantir; beta é o melhor valor que MIN já consegue garantir. Quando "
        "alpha ≥ beta, as ações restantes daquele nó não podem mudar a escolha e "
        "podem ser ignoradas.\n\n"
        "Com janela inicial infinita e busca completa, o valor permanece igual ao "
        "Minimax. A quantidade de nós pode ser menor; a jogada escolhida pode variar "
        "em caso de empate entre ações ótimas."
    ),
    "Busca limitada e heurística": (
        "A busca limitada para quando atinge o limite de jogadas a partir da raiz. "
        "Terminais continuam recebendo utilidade exata. Uma posição não terminal no "
        "limite recebe uma estimativa de avaliacao_heuristica().\n\n"
        "A heurística atual combina a oportunidade de vitória imediata (peso 0,8) e "
        "a paridade do total (peso 0,2), e converte o sinal para a perspectiva de MAX. "
        "Ela é uma aproximação, não uma garantia de vitória nem de jogo perfeito.\n\n"
        "A profundidade 0 avalia a própria raiz e não escolhe jogada; agentes precisam "
        "de profundidade pelo menos 1."
    ),
    "XOR e estratégia ótima": (
        "XOR é a operação binária exclusiva, escrita a ^ b em Python. No Nim de duas "
        "pilhas, XOR igual a zero ocorre quando as pilhas têm a mesma quantidade.\n\n"
        "Sob jogo perfeito, uma posição com XOR zero é perdedora para quem está na vez. "
        "Se o XOR é diferente de zero, existe uma retirada legal que pode produzir "
        "XOR zero para o próximo jogador.\n\n"
        "Essa é uma propriedade matemática conhecida do Nim, não uma descoberta do "
        "projeto. A propriedade não garante vitória contra qualquer adversário nem "
        "significa que a busca limitada implementa sempre essa estratégia."
    ),
    "Complexidade computacional": (
        "Se b representa o fator de ramificação médio e m a profundidade, a estimativa "
        "didática para Minimax é O(b^m): em cada nível, a busca pode examinar muitos "
        "sucessores. No Nim, b varia por estado e é no máximo a+b ações legais naquele "
        "estado; cada jogada reduz pelo menos uma peça, então a profundidade é finita "
        "e no máximo a+b.\n\n"
        "Alfa-Beta tem o mesmo pior caso assintótico O(b^m). Com ordenação ideal, a "
        "análise clássica pode chegar a O(b^(m/2)); isso é uma propriedade teórica, "
        "não uma promessa para a ordenação simples do projeto.\n\n"
        "A busca recursiva usa espaço proporcional à profundidade e às ações mantidas "
        "em cada nível. Não há memoização: um mesmo estado em ramos diferentes é "
        "contado de novo. Essas expressões são estimativas teóricas, diferentes dos "
        "nós medidos nos CSVs."
    ),
    "Metodologia experimental": (
        "O protocolo usa 80 posições ordenadas (A e B de 0 a 8, exceto 0,0), quatro "
        "combinações de atribuição de agente a MAX/MIN e jogador inicial, e 16 "
        "confrontos. Os confrontos aleatorizados têm dez repetições por combinação; "
        "os demais têm uma.\n\n"
        "A semente mestre aprovada é 2026. A fórmula de partidas aleatorizadas depende "
        "dos índices da posição, combinação de papéis e repetição, e não do confronto; "
        "assim, sementes correspondentes são reutilizadas entre confrontos aleatórios. "
        "O agente aleatório recebe uma nova semente por turno, derivada de um gerador "
        "persistente por partida.\n\n"
        "Custo principal: nós visitados por decisão de busca. Para o aleatório, custo "
        "de busca é N/A, não zero. Os CSVs registram jogadas, partidas e resumo."
    ),
    "Resultados": "",
    "Limitações": (
        "Os resultados descrevem apenas as posições, configurações, sementes e "
        "adversários definidos no protocolo. As 80 posições são ordenadas e incluem "
        "pares simétricos como (2,5) e (5,2), o que gera repetição estrutural.\n\n"
        "Uma taxa alta contra o agente aleatório não prova superioridade geral. A "
        "busca limitada usa estimativa heurística e não tem garantia de jogo perfeito. "
        "Os resultados não incluem intervalos de confiança.\n\n"
        "O protocolo não possui um confronto experimental entre Minimax completo e "
        "Alfa-Beta completo; a comparação de valores e nós pode ser feita para estados "
        "escolhidos na aba Algoritmos. O template de relatório ainda precisa ser "
        "preenchido e revisado como documento acadêmico."
    ),
    "Conclusão": (
        "O projeto demonstra como formalizar um jogo, implementar busca adversarial e "
        "medir decisões com uma unidade de custo explícita. Minimax fornece a referência "
        "completa; Alfa-Beta pode preservar seu valor evitando ramos; a busca limitada "
        "troca completude por custo menor e depende de uma estimativa.\n\n"
        "As conclusões sobre desempenho devem se limitar aos dados observados e às "
        "comparações controladas do protocolo. A estratégia XOR é conhecida e serve "
        "como referência matemática, não como resultado inédito do trabalho.\n\n"
        "Para a entrega, conferir o template DocumentoFinalEntrega.md, a ficha exigida "
        "pela disciplina, a evidência dos testes e os CSVs reais."
    ),
}


class TelaGuia(ttk.Frame):
    """Documentação acessível por navegação interna."""

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent, style="Conteudo.TFrame", padding=(24, 18))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        ttk.Label(
            self,
            text="NIM LAB  /  MATERIAL DE ESTUDO",
            foreground="#2563eb",
            background="#f1f5f9",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self,
            text="Guia do trabalho",
            foreground="#0f172a",
            background="#f1f5f9",
            font=("TkDefaultFont", 22, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))

        principal = ttk.Frame(self)
        principal.grid(row=2, column=0, sticky="nsew")
        principal.columnconfigure(1, weight=1)
        principal.rowconfigure(0, weight=1)
        self._lista = tk.Listbox(principal, width=31, exportselection=False)
        self._lista.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        for titulo in SECOES:
            self._lista.insert("end", titulo)
        self._lista.bind("<<ListboxSelect>>", self._selecionar_secao)
        self._lista.selection_set(0)
        self._lista.activate(0)

        conteudo = ttk.Frame(principal)
        conteudo.grid(row=0, column=1, sticky="nsew")
        conteudo.columnconfigure(0, weight=1)
        conteudo.rowconfigure(1, weight=1)
        self._titulo = ttk.Label(conteudo, text="", font=("TkDefaultFont", 16, "bold"))
        self._titulo.grid(row=0, column=0, sticky="w", pady=(0, 8))
        texto_frame = ttk.Frame(conteudo)
        texto_frame.grid(row=1, column=0, sticky="nsew")
        texto_frame.columnconfigure(0, weight=1)
        texto_frame.rowconfigure(0, weight=1)
        self._texto = tk.Text(
            texto_frame,
            wrap="word",
            padx=14,
            pady=12,
            relief="flat",
            background="#ffffff",
            font=("TkDefaultFont", 10),
        )
        self._texto.grid(row=0, column=0, sticky="nsew")
        barra = ttk.Scrollbar(texto_frame, orient="vertical", command=self._texto.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self._texto.configure(yscrollcommand=barra.set)
        self._mostrar_secao("Visão geral do projeto")

    def _selecionar_secao(self, _evento=None) -> None:
        selecao = self._lista.curselection()
        if selecao:
            self._mostrar_secao(self._lista.get(selecao[0]))

    def _mostrar_secao(self, titulo: str) -> None:
        texto = SECOES[titulo]
        if titulo == "Resultados":
            texto = self._texto_resultados()
        self._titulo.configure(text=titulo)
        self._texto.configure(state="normal")
        self._texto.delete("1.0", "end")
        self._texto.insert("1.0", texto)
        self._texto.configure(state="disabled")
        self._texto.yview_moveto(0)

    @staticmethod
    def _texto_resultados() -> str:
        try:
            dados = carregar_resultados(PASTA_RESULTADOS)
        except (OSError, ValueError) as erro:
            return f"Não foi possível ler os resultados finais: {erro}"

        indicadores = calcular_indicadores_gerais(dados)
        linhas = [
            "Os números abaixo são lidos dos CSVs finais existentes, não são exemplos "
            "ou estimativas.\n",
            f"Partidas registradas: {indicadores['partidas']:,}.",
            f"Confrontos: {indicadores['confrontos']}.",
            f"Jogadas registradas: {indicadores['jogadas']:,}.",
            f"Empates registrados: {indicadores['empates']}.",
            f"Fonte: {PASTA_RESULTADOS}\n",
            "Nós por decisão, agrupados por profundidade nos confrontos correspondentes:",
        ]
        for item in obter_estatisticas_profundidade(dados["resumo"]):
            linhas.append(
                f"• Profundidade {item['profundidade']}: média ponderada "
                f"{item['media']:.2f} nós em {item['decisoes']} decisões; "
                f"máximo observado {item['maximo']}."
            )
        linhas.append("\nOrdenação nos confrontos específicos de ordenação:")
        por_profundidade = {}
        for item in obter_estatisticas_ordenacao(dados["resumo"]):
            por_profundidade.setdefault(item["profundidade"], {})[
                item["ordenacao"]
            ] = item
        for profundidade, pares in sorted(por_profundidade.items()):
            desligada = pares.get("desligada")
            ligada = pares.get("ligada")
            if desligada and ligada:
                linhas.append(
                    f"• d{profundidade}: desligada {desligada['media']:.2f} "
                    f"nós/decisão ({desligada['decisoes']} decisões); ligada "
                    f"{ligada['media']:.2f} ({ligada['decisoes']} decisões)."
                )
        linhas.extend(
            (
                "",
                "A média é ponderada pela quantidade de decisões que realmente "
                "executaram busca. Agente aleatório aparece como N/A para nós. "
                "Diferenças devem ser interpretadas dentro do protocolo: não demonstram "
                "superioridade geral, e posições simétricas foram mantidas.",
            )
        )
        return "\n".join(linhas)


def criar_tela(parent: ttk.Frame) -> TelaGuia:
    """Cria o guia interativo do trabalho."""
    return TelaGuia(parent)
