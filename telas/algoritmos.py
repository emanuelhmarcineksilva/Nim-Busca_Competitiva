"""Ambiente didático interativo para os algoritmos de busca do projeto."""

import queue
import threading
import tkinter as tk
from tkinter import ttk

from agentes import (
    alfa_beta,
    alfa_beta_limitado,
    avaliacao_heuristica,
    minimax,
    ordenar_acoes,
)
from jogo import Estado, Jogador, acoes, resultado, teste_terminal, utilidade


CONCEITOS = {
    "Minimax": {
        "o_que": "Busca competitiva que escolhe a melhor jogada supondo jogo perfeito dos dois lados.",
        "para_que": "Encontrar o resultado garantido em uma árvore finita, sem atalhos heurísticos.",
        "como": "MAX escolhe o maior valor; MIN escolhe o menor. A utilidade terminal é sempre calculada da perspectiva de MAX.",
        "projeto": "A função percorre todos os sucessores até os terminais e desempata pela primeira ação legal.",
        "exemplo": "Em (1, 2, MAX), a busca compara todas as retiradas possíveis e retorna o valor e a primeira jogada ótima.",
        "referencia": "agentes.py → minimax(); jogo.py → acoes(), resultado(), utilidade()",
        "tests": "testes/test_minimax.py; testes/test_alfa_beta.py",
    },
    "Alpha-Beta": {
        "o_que": "Minimax com limites que permitem interromper ramos que não podem mudar a escolha.",
        "para_que": "Manter o valor minimax e reduzir o número de estados visitados.",
        "como": "Alpha acompanha a melhor garantia de MAX; beta acompanha a melhor garantia de MIN.",
        "projeto": "A busca completa chama recursivamente a própria função até estados terminais.",
        "exemplo": "Quando alpha fica maior ou igual a beta, os sucessores restantes daquele nó deixam de ser necessários.",
        "referencia": "agentes.py → alfa_beta()",
        "tests": "testes/test_alfa_beta.py",
    },
    "Poda Alfa-Beta": {
        "o_que": "Corte de uma parte da árvore quando a janela alpha-beta prova que ela não altera a decisão.",
        "para_que": "Evitar trabalho redundante sem alterar o valor da posição.",
        "como": "A condição de corte é alpha >= beta. Ramos não visitados não entram na contagem de nós.",
        "projeto": "A implementação atual faz a condição depois de atualizar alpha em MAX ou beta em MIN.",
        "exemplo": "A demonstração compara os nós reais de Minimax e Alfa-Beta e informa a diferença total; a árvore ilustra apenas a raiz e seus sucessores.",
        "referencia": "agentes.py → alfa_beta()",
        "tests": "testes/test_alfa_beta.py",
    },
    "Ordenação de jogadas": {
        "o_que": "Reordenação dos movimentos antes de expandir a busca.",
        "para_que": "Tentar encontrar cedo uma boa alternativa, permitindo mais podas Alfa-Beta.",
        "como": "O projeto prioriza ações que deixam as pilhas iguais, situação cujo XOR é zero.",
        "projeto": "A ordenação conserva as jogadas legais e é opcional na busca Alfa-Beta.",
        "exemplo": "Em (3, 1), a retirada de duas peças de A leva a (1, 1) e aparece antes quando aplicável.",
        "referencia": "agentes.py → ordenar_acoes(), alfa_beta()",
        "tests": "testes/test_alfa_beta.py",
    },
    "Busca limitada": {
        "o_que": "Busca Alfa-Beta que para após um número configurável de jogadas.",
        "para_que": "Controlar o custo quando explorar a árvore toda fica caro.",
        "como": "Terminais continuam recebendo utilidade exata; posições não terminais no limite usam a heurística.",
        "projeto": "A busca começa na profundidade zero; o agente precisa de limite pelo menos 1 para escolher uma ação.",
        "exemplo": "A demonstração mostra a jogada, avaliação e nós para a profundidade escolhida.",
        "referencia": "agentes.py → alfa_beta_limitado(), agente_busca_limitada()",
        "tests": "testes/test_alfa_beta_limitado.py; testes/test_agentes.py",
    },
    "Heurística": {
        "o_que": "Estimativa de uma posição não terminal usada no corte da busca limitada.",
        "para_que": "Dar uma avaliação aproximada sem continuar até o fim do jogo.",
        "como": "O projeto combina oportunidade de vitória imediata (peso 0,8) e paridade do total (peso 0,2), convertendo o sinal para MAX.",
        "projeto": "A utilidade terminal não é substituída pela heurística.",
        "exemplo": "Altere o estado da demonstração e compare a avaliação limitada com o valor da busca completa.",
        "referencia": "agentes.py → avaliacao_heuristica(), alfa_beta_limitado()",
        "tests": "testes/test_avaliacao.py; testes/test_alfa_beta_limitado.py",
    },
    "XOR e estratégia ótima": {
        "o_que": "A estratégia clássica do Nim de duas pilhas usa o XOR das quantidades.",
        "para_que": "Identificar posições perdedoras sob jogo perfeito e procurar um sucessor com XOR zero.",
        "como": "A XOR B igual a zero significa pilhas iguais e posição desfavorável para quem joga, se o adversário também jogar perfeitamente.",
        "projeto": "É uma propriedade matemática conhecida do Nim; não é uma descoberta do projeto e não garante vitória contra qualquer adversário.",
        "exemplo": "Se (A, B) = (3, 1), então 3 XOR 1 = 2, diferente de zero.",
        "referencia": "agentes.py → ordenar_acoes(); a operação XOR é usada na prioridade",
        "tests": "testes/test_alfa_beta.py",
    },
}


class TelaAlgoritmos(ttk.Frame):
    """Página com catálogo de conceitos, busca interativa e cálculo de XOR."""

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent, style="Conteudo.TFrame", padding=(24, 18))
        self._fila_busca: queue.Queue = queue.Queue()
        self._criar_variaveis()
        self._criar_layout()
        self._mostrar_conceito("Minimax")
        self._atualizar_xor()

    def _criar_variaveis(self) -> None:
        self.pilha_a_var = tk.StringVar(self, "2")
        self.pilha_b_var = tk.StringVar(self, "3")
        self.jogador_var = tk.StringVar(self, Jogador.MAX.value)
        self.algoritmo_var = tk.StringVar(self, "Alpha-Beta")
        self.profundidade_var = tk.StringVar(self, "2")
        self.xor_a_var = tk.StringVar(self, "3")
        self.xor_b_var = tk.StringVar(self, "1")
        self._resultado_var = tk.StringVar(self, "Configure um estado e execute a demonstração.")
        self._xor_var = tk.StringVar(self, "")
        self._ordenacao_var = tk.StringVar(self, "")

    def _criar_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        ttk.Label(
            self,
            text="NIM LAB  /  TDE2",
            foreground="#2563eb",
            background="#f1f5f9",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self,
            text="Algoritmos",
            foreground="#0f172a",
            background="#f1f5f9",
            font=("TkDefaultFont", 22, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))

        self._abas = ttk.Notebook(self)
        self._abas.grid(row=2, column=0, sticky="nsew")
        self._criar_aba_conceitos()
        self._criar_aba_demonstracao()
        self._criar_aba_xor()

    def _criar_aba_conceitos(self) -> None:
        aba = ttk.Frame(self._abas, padding=12)
        aba.columnconfigure(1, weight=1)
        aba.rowconfigure(0, weight=1)
        self._abas.add(aba, text="Conceitos")

        lista = tk.Listbox(aba, width=25, exportselection=False)
        lista.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        for titulo in CONCEITOS:
            lista.insert("end", titulo)
        lista.bind("<<ListboxSelect>>", self._selecionar_conceito)
        lista.selection_set(0)
        lista.activate(0)
        self._lista_conceitos = lista

        painel = ttk.Frame(aba)
        painel.grid(row=0, column=1, sticky="nsew")
        painel.columnconfigure(0, weight=1)
        painel.rowconfigure(1, weight=1)
        self._titulo_conceito = ttk.Label(
            painel, text="", font=("TkDefaultFont", 16, "bold")
        )
        self._titulo_conceito.grid(row=0, column=0, sticky="w", pady=(0, 8))
        texto_frame = ttk.Frame(painel)
        texto_frame.grid(row=1, column=0, sticky="nsew")
        texto_frame.columnconfigure(0, weight=1)
        texto_frame.rowconfigure(0, weight=1)
        self._texto_conceito = tk.Text(
            texto_frame,
            wrap="word",
            height=16,
            relief="flat",
            padx=12,
            pady=12,
            background="#ffffff",
            font=("TkDefaultFont", 10),
        )
        self._texto_conceito.grid(row=0, column=0, sticky="nsew")
        barra = ttk.Scrollbar(
            texto_frame, orient="vertical", command=self._texto_conceito.yview
        )
        barra.grid(row=0, column=1, sticky="ns")
        self._texto_conceito.configure(yscrollcommand=barra.set)
        self._texto_conceito.configure(state="disabled")

    def _selecionar_conceito(self, _evento=None) -> None:
        selecao = self._lista_conceitos.curselection()
        if selecao:
            self._mostrar_conceito(self._lista_conceitos.get(selecao[0]))

    def _mostrar_conceito(self, titulo: str) -> None:
        conceito = CONCEITOS[titulo]
        self._titulo_conceito.configure(text=titulo)
        linhas = (
            ("O que é", conceito["o_que"]),
            ("Para que serve", conceito["para_que"]),
            ("Como funciona", conceito["como"]),
            ("Neste projeto", conceito["projeto"]),
            ("Exemplo", conceito["exemplo"]),
            ("Código relacionado", conceito["referencia"]),
            ("Testes", conceito["tests"]),
        )
        texto = "\n\n".join(f"{rotulo}\n{conteudo}" for rotulo, conteudo in linhas)
        self._texto_conceito.configure(state="normal")
        self._texto_conceito.delete("1.0", "end")
        self._texto_conceito.insert("1.0", texto)
        self._texto_conceito.configure(state="disabled")

    def _criar_aba_demonstracao(self) -> None:
        aba = ttk.Frame(self._abas, padding=12)
        aba.columnconfigure(0, weight=1)
        aba.rowconfigure(2, weight=1)
        self._abas.add(aba, text="Demonstração interativa")

        controles = ttk.LabelFrame(aba, text="Estado de busca (máximo 4 peças por pilha)", padding=8)
        controles.grid(row=0, column=0, sticky="ew")
        self._campo_spin(controles, "Pilha A", self.pilha_a_var, 0)
        self._campo_spin(controles, "Pilha B", self.pilha_b_var, 1)
        ttk.Label(controles, text="Jogador").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            controles,
            textvariable=self.jogador_var,
            values=(Jogador.MAX.value, Jogador.MIN.value),
            state="readonly",
            width=7,
        ).grid(row=1, column=2, sticky="ew", padx=(0, 8))
        ttk.Label(controles, text="Algoritmo").grid(row=0, column=3, sticky="w")
        self._seletor_algoritmo = ttk.Combobox(
            controles,
            textvariable=self.algoritmo_var,
            values=("Minimax", "Alpha-Beta"),
            state="readonly",
            width=12,
        )
        self._seletor_algoritmo.grid(row=1, column=3, sticky="ew", padx=(0, 8))
        ttk.Label(controles, text="Profundidade").grid(row=0, column=4, sticky="w")
        ttk.Spinbox(
            controles,
            from_=1,
            to=8,
            textvariable=self.profundidade_var,
            width=5,
        ).grid(row=1, column=4, sticky="ew", padx=(0, 8))
        self._botao_executar = ttk.Button(
            controles,
            text="Comparar buscas",
            command=self.executar_demonstracao,
        )
        self._botao_executar.grid(row=1, column=5, sticky="ew", padx=(0, 8))
        ttk.Button(
            controles,
            text="Ver ordenação",
            command=self._mostrar_ordenacao,
        ).grid(row=1, column=6, sticky="ew")

        resultado_label = ttk.Label(
            aba,
            textvariable=self._resultado_var,
            justify="left",
            wraplength=950,
            padding=(4, 8),
        )
        resultado_label.grid(row=1, column=0, sticky="ew")
        aba.bind(
            "<Configure>",
            lambda evento: resultado_label.configure(
                wraplength=max(200, evento.width - 24)
            ),
            add="+",
        )
        self._arvore = tk.Canvas(
            aba,
            height=315,
            background="#ffffff",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
        )
        self._arvore.grid(row=2, column=0, sticky="nsew")
        legenda = ttk.Label(
            aba,
            text="Verde: melhor jogada · Azul: sucessor explorado · Vermelho: total de nós evitados. O vermelho não identifica um ramo específico, pois a busca não fornece esse rastreamento.",
            wraplength=950,
            foreground="#475569",
        )
        legenda.grid(row=3, column=0, sticky="w", pady=(6, 0))
        aba.bind(
            "<Configure>",
            lambda evento: legenda.configure(wraplength=max(200, evento.width - 24)),
            add="+",
        )
        explicacao = ttk.LabelFrame(
            aba, text="Como interpretar esta demonstração", padding=10
        )
        explicacao.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        explicacao.columnconfigure(0, weight=1)
        texto_explicacao = ttk.Label(
            explicacao,
            text=(
                "Estado (A, B, jogador): os dois números são as peças nas pilhas A e B; "
                "MAX/MIN indica quem joga. Uma ação como A:1 retira uma peça da pilha A. "
                "O nó no alto é o estado inicial; os nós abaixo são todos os sucessores "
                "legais imediatos, não a árvore completa. Azul indica sucessor avaliado; "
                "verde marca a melhor ação da busca selecionada; vermelho resume nós "
                "evitados no total, sem apontar um ramo específico.\n\n"
                "Valor exato +1 significa resultado favorável a MAX com jogo perfeito; "
                "-1 favorece MIN. O Nim atual não permite empate, por isso uma busca "
                "completa retorna apenas +1 ou -1. Um valor heurístico é uma estimativa "
                "na profundidade escolhida, não promessa de vitória. Um nó visitado é "
                "uma chamada de busca, incluindo raiz e folhas. Alfa-Beta pode visitar "
                "menos nós que Minimax e ainda preservar o valor, porque ignora trechos "
                "que não mudariam a decisão."
            ),
            wraplength=950,
            justify="left",
        )
        texto_explicacao.grid(row=0, column=0, sticky="ew")
        explicacao.bind(
            "<Configure>",
            lambda evento: texto_explicacao.configure(
                wraplength=max(200, evento.width - 32)
            ),
            add="+",
        )
        self._guia_var = tk.StringVar(
            self,
            "Execute a demonstração para acompanhar um exemplo real gerado pelos algoritmos.",
        )
        ttk.Label(
            explicacao,
            textvariable=self._guia_var,
            wraplength=950,
            justify="left",
            foreground="#1e3a8a",
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self._desenhar_arvore(None, [])

    @staticmethod
    def _campo_spin(
        parent: ttk.LabelFrame,
        titulo: str,
        variavel: tk.StringVar,
        coluna: int,
    ) -> None:
        ttk.Label(parent, text=titulo).grid(row=0, column=coluna, sticky="w")
        ttk.Spinbox(
            parent,
            from_=0,
            to=4,
            textvariable=variavel,
            width=5,
        ).grid(row=1, column=coluna, sticky="ew", padx=(0, 8))

    def executar_demonstracao(self) -> None:
        """Executa buscas reais fora da thread da interface."""
        try:
            pilha_a = self._ler_quantidade(self.pilha_a_var.get(), "Pilha A")
            pilha_b = self._ler_quantidade(self.pilha_b_var.get(), "Pilha B")
            if pilha_a + pilha_b > 8:
                raise ValueError("Para manter a demonstração rápida, use no máximo 8 peças no total.")
            profundidade = self._ler_quantidade(
                self.profundidade_var.get(), "Profundidade", minimo=1, maximo=8
            )
            estado = Estado(pilha_a, pilha_b, Jogador(self.jogador_var.get()))
        except (ValueError, tk.TclError) as erro:
            self._resultado_var.set(str(erro))
            return

        self._botao_executar.configure(state="disabled")
        self._seletor_algoritmo.configure(state="disabled")
        self._resultado_var.set("Executando Minimax, Alpha-Beta e busca limitada…")
        self._arvore.delete("all")
        threading.Thread(
            target=self._calcular_demonstracao,
            args=(estado, profundidade, self.algoritmo_var.get()),
            daemon=True,
        ).start()
        self.after(40, self._verificar_resultado_busca)

    def _calcular_demonstracao(
        self, estado: Estado, profundidade: int, algoritmo: str
    ) -> None:
        try:
            minimax_resultado = minimax(estado)
            alfa_beta_resultado = alfa_beta(estado)
            limitado = alfa_beta_limitado(estado, profundidade)
            heuristica = avaliacao_heuristica(estado)
            sucessores = []
            melhor = minimax_resultado[1] if algoritmo == "Minimax" else alfa_beta_resultado[1]
            for acao in acoes(estado):
                sucessor = resultado(estado, acao)
                valor_sucessor = minimax(sucessor)[0]
                sucessores.append(
                    {
                        "jogada": acao,
                        "estado": sucessor,
                        "valor": valor_sucessor,
                        "melhor": acao == melhor,
                    }
                )
            self._fila_busca.put(
                (
                    estado,
                    profundidade,
                    minimax_resultado,
                    alfa_beta_resultado,
                    limitado,
                    heuristica,
                    sucessores,
                    None,
                )
            )
        except Exception as erro:
            self._fila_busca.put((None, None, None, None, None, None, None, erro))

    def _verificar_resultado_busca(self) -> None:
        try:
            dados = self._fila_busca.get_nowait()
        except queue.Empty:
            self.after(40, self._verificar_resultado_busca)
            return

        self._botao_executar.configure(state="normal")
        self._seletor_algoritmo.configure(state="readonly")
        estado, profundidade, mm, ab, limitado, heuristica, sucessores, erro = dados
        if erro is not None:
            self._resultado_var.set(f"Erro na demonstração: {erro}")
            return

        algoritmo = self.algoritmo_var.get()
        selecionado = mm if algoritmo == "Minimax" else ab
        melhor_jogada = selecionado[1]
        if teste_terminal(estado):
            melhor_texto = "Nenhuma (estado terminal)"
        elif melhor_jogada:
            melhor_texto = f"{melhor_jogada.pilha.value}: retirar {melhor_jogada.quantidade}"
        else:
            melhor_texto = "Nenhuma"
        evitados = mm[2] - ab[2]
        self._resultado_var.set(
            f"Estado {self._texto_estado(estado)} · {algoritmo}: jogada {melhor_texto}, "
            f"valor {selecionado[0]}, nós {selecionado[2]}.  "
            f"Minimax: {mm[2]} nós; Alpha-Beta: {ab[2]} nós; "
            f"valores iguais: {'sim' if mm[0] == ab[0] else 'NÃO'}; "
            f"diferença: {evitados} nó(s) evitado(s).  "
            f"Busca limitada d{profundidade}: jogada {self._texto_jogada(limitado[1])}, "
            f"avaliação {limitado[0]}, {limitado[2]} nós.  "
            f"Heurística do estado: {heuristica}."
        )
        self._desenhar_arvore(estado, sucessores, evitados)
        melhor_sucessor = next(
            (item for item in sucessores if item["jogada"] == melhor_jogada),
            None,
        )
        self._guia_var.set(
            self._explicar_demonstracao(
                estado,
                melhor_jogada,
                selecionado[0],
                mm[0],
                ab[0],
                limitado[0],
                limitado[1],
                melhor_sucessor,
            )
        )

    def _explicar_demonstracao(
        self,
        estado: Estado,
        jogada,
        valor: float,
        valor_minimax: float,
        valor_alfa_beta: float,
        valor_limitado: float,
        jogada_limitada,
        sucessor_escolhido,
    ) -> str:
        resultado_jogada = (
            self._texto_estado(sucessor_escolhido["estado"])
            if sucessor_escolhido
            else "não há sucessor porque o estado já é terminal"
        )
        resultado_limitado = (
            "o estado já é terminal"
            if teste_terminal(estado)
            else f"escolhe {self._texto_jogada(jogada_limitada)}"
        )
        if valor == 1:
            significado = "a busca completa prevê vitória de MAX com jogo perfeito"
        elif valor == -1:
            significado = "a busca completa prevê vitória de MIN com jogo perfeito"
        else:
            significado = "a busca completa retornou valor neutro"
        if not teste_terminal(estado) and int(self.profundidade_var.get()) < (
            estado.pilha_a + estado.pilha_b
        ):
            significado_limitado = (
                f"A busca limitada retorna {valor_limitado}; ramos que alcançam o "
                "limite antes do terminal usam uma estimativa heurística, não uma "
                "garantia de vitória."
            )
        else:
            significado_limitado = (
                f"A busca limitada retorna {valor_limitado}; nesta posição, a "
                "profundidade permite alcançar estados terminais e obter valor exato."
            )
        return (
            f"1. O estado {self._texto_estado(estado)} informa {estado.pilha_a} peça(s) "
            f"em A, {estado.pilha_b} em B; {estado.jogador_atual.value} joga agora.\n"
            f"2. A ação {self._texto_jogada(jogada)} significa retirar "
            f"{jogada.quantidade if jogada else 0} peça(s) da pilha "
            f"{jogada.pilha.value if jogada else '—'}. O sucessor exibido é "
            f"{resultado_jogada}.\n"
            f"3. O valor completo {valor} é sempre da perspectiva de MAX: {significado}. "
            f"Minimax e Alfa-Beta retornaram {valor_minimax} e {valor_alfa_beta}; "
            "igualdade dos valores mostra que a poda preservou a avaliação.\n"
            f"4. Minimax visitou todos os nós da busca completa; Alfa-Beta visitou só "
            f"os necessários após os cortes. A diferença exibida é global, não indica "
            "qual ramo específico foi podado.\n"
            f"5. Busca limitada {resultado_limitado} e retorna {valor_limitado} em "
            f"profundidade {self.profundidade_var.get()}. {significado_limitado}"
        )

    def _mostrar_ordenacao(self) -> None:
        try:
            estado = self._estado_demonstracao()
        except ValueError as erro:
            self._resultado_var.set(str(erro))
            return
        natural = acoes(estado)
        ordenadas = ordenar_acoes(estado)
        self._ordenacao_var.set(
            "Ações em ordem natural: "
            + ", ".join(self._texto_jogada(acao) for acao in natural)
            + "\nAções ordenadas: "
            + ", ".join(self._texto_jogada(acao) for acao in ordenadas)
            + "\nA ordenação muda a sequência de exploração, não remove ações."
        )
        self._resultado_var.set(self._ordenacao_var.get())

    def _estado_demonstracao(self) -> Estado:
        pilha_a = self._ler_quantidade(self.pilha_a_var.get(), "Pilha A")
        pilha_b = self._ler_quantidade(self.pilha_b_var.get(), "Pilha B")
        if pilha_a + pilha_b > 8:
            raise ValueError("Use no máximo 8 peças no total.")
        return Estado(pilha_a, pilha_b, Jogador(self.jogador_var.get()))

    @staticmethod
    def _ler_quantidade(
        texto: str,
        nome: str,
        minimo: int = 0,
        maximo: int = 8,
    ) -> int:
        valor = int(texto)
        if not minimo <= valor <= maximo:
            raise ValueError(f"{nome} deve estar entre {minimo} e {maximo}.")
        return valor

    @staticmethod
    def _texto_estado(estado: Estado) -> str:
        return f"({estado.pilha_a}, {estado.pilha_b}, {estado.jogador_atual.value})"

    @staticmethod
    def _texto_jogada(jogada) -> str:
        return "nenhuma" if jogada is None else f"{jogada.pilha.value}:{jogada.quantidade}"

    def _desenhar_arvore(self, estado, sucessores, nos_evitados: int = 0) -> None:
        self._arvore.delete("all")
        largura = max(self._arvore.winfo_width(), 620)
        centro = largura / 2
        if estado is None:
            self._arvore.create_text(
                centro,
                40,
                text="Execute uma demonstração para ver o estado e seus sucessores.",
                fill="#475569",
                font=("TkDefaultFont", 11),
            )
            return
        self._arvore.create_oval(
            centro - 92, 15, centro + 92, 65, fill="#dbeafe", outline="#2563eb", width=2
        )
        self._arvore.create_text(
            centro, 40, text=self._texto_estado(estado), font=("TkDefaultFont", 10, "bold")
        )
        if not sucessores:
            self._arvore.create_text(
                centro, 105, text=f"Terminal · utilidade MAX = {utilidade(estado)}"
            )
            return

        distancia = largura / (len(sucessores) + 1)
        for indice, item in enumerate(sucessores, start=1):
            x = distancia * indice
            cor = "#dcfce7" if item["melhor"] else "#dbeafe"
            contorno = "#16a34a" if item["melhor"] else "#2563eb"
            self._arvore.create_line(centro, 65, x, 145, fill=contorno, width=2)
            self._arvore.create_oval(
                x - 68, 125, x + 68, 183, fill=cor, outline=contorno, width=2
            )
            jogada = item["jogada"]
            texto = (
                f"{jogada.pilha.value}:{jogada.quantidade}\n"
                f"({item['estado'].pilha_a},{item['estado'].pilha_b},"
                f"{item['estado'].jogador_atual.value})\n"
                f"valor {item['valor']}"
            )
            self._arvore.create_text(
                x, 154, text=texto, font=("TkDefaultFont", 8), justify="center"
            )
        self._arvore.create_text(
            centro,
            225,
            text="Valores dos sucessores calculados com Minimax completo; "
            "o destaque verde indica a jogada selecionada pelo algoritmo.",
            fill="#475569",
            font=("TkDefaultFont", 9),
        )
        self._arvore.create_text(
            centro,
            252,
            text="A poda acontece dentro das subárvores. A diferença de nós é exata, "
            "mas a implementação não fornece rastreamento por ramo.",
            fill="#64748b",
            font=("TkDefaultFont", 9),
        )
        self._arvore.create_rectangle(
            centro - 110,
            276,
            centro - 88,
            298,
            fill="#fee2e2",
            outline="#dc2626",
        )
        self._arvore.create_text(
            centro - 76,
            287,
            anchor="w",
            text=f"{nos_evitados} nó(s) evitado(s) no total",
            fill="#991b1b",
            font=("TkDefaultFont", 9, "bold"),
        )

    def _criar_aba_xor(self) -> None:
        aba = ttk.Frame(self._abas, padding=20)
        aba.columnconfigure(0, weight=1)
        self._abas.add(aba, text="XOR e estratégia")
        ttk.Label(
            aba,
            text="XOR das pilhas",
            font=("TkDefaultFont", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        controles = ttk.Frame(aba)
        controles.grid(row=1, column=0, sticky="w")
        for coluna, (nome, variavel) in enumerate(
            (("A", self.xor_a_var), ("B", self.xor_b_var))
        ):
            ttk.Label(controles, text=f"Pilha {nome}").grid(
                row=0, column=coluna * 2, sticky="w"
            )
            campo = ttk.Spinbox(
                controles,
                from_=0,
                to=MAXIMO_XOR,
                textvariable=variavel,
                width=7,
                command=self._atualizar_xor,
            )
            campo.grid(row=0, column=coluna * 2 + 1, padx=(6, 18))
            campo.bind("<KeyRelease>", lambda _evento: self._atualizar_xor())
        ttk.Label(
            aba,
            textvariable=self._xor_var,
            font=("TkDefaultFont", 13, "bold"),
            justify="left",
            wraplength=850,
        ).grid(row=2, column=0, sticky="nw", pady=20)
        ttk.Label(
            aba,
            text=(
                "No Nim de duas pilhas, XOR igual a zero indica uma posição perdedora "
                "para quem joga, se o adversário também jogar perfeitamente. Se o XOR "
                "for diferente de zero, há uma jogada que pode levar a zero. É uma "
                "propriedade conhecida do jogo, não uma garantia de vitória em qualquer "
                "partida contra um agente imperfeito."
            ),
            wraplength=850,
            justify="left",
        ).grid(row=3, column=0, sticky="nw")

    def _atualizar_xor(self) -> None:
        try:
            a = self._ler_quantidade(self.xor_a_var.get(), "Pilha A")
            b = self._ler_quantidade(self.xor_b_var.get(), "Pilha B")
        except (ValueError, tk.TclError):
            self._xor_var.set("Informe quantidades inteiras entre 0 e 8.")
            return
        xor = a ^ b
        situacao = (
            "desfavorável para quem está na vez"
            if xor == 0
            else "há uma jogada para buscar uma posição com XOR zero"
        )
        self._xor_var.set(f"{a} XOR {b} = {xor}\nPosição {situacao} sob jogo perfeito.")


MAXIMO_XOR = 8


def criar_tela(parent: ttk.Frame) -> TelaAlgoritmos:
    """Cria a página interativa de algoritmos."""
    return TelaAlgoritmos(parent)
