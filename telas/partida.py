"""Tela para configurar, jogar e acompanhar uma partida de Nim."""

import queue
import random
import threading
import tkinter as tk
from functools import partial
from tkinter import messagebox, ttk
from typing import Any, Dict, Optional, Tuple

from agentes import (
    agente_aleatorio,
    agente_busca_limitada,
    agente_principal,
    alfa_beta,
    minimax,
)
from jogo import (
    Estado,
    Jogada,
    Jogador,
    Pilha,
    criar_estado_inicial,
    resultado,
    teste_terminal,
    utilidade,
)


OPCOES_AGENTE = (
    "Humano",
    "Aleatório",
    "Minimax completo",
    "Alpha-Beta completo",
    "Alpha-Beta limitado",
    "Agente principal",
)
AGENTES_COM_PROFUNDIDADE = {
    "Alpha-Beta limitado",
    "Agente principal",
}
MAXIMO_PILHAS = 8
SEMENTE_BITS = 64


class TelaPartida(ttk.Frame):
    """Interface de partida que delega regras e decisões aos módulos existentes."""

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent, style="Conteudo.TFrame", padding=(24, 20))
        self._estado: Optional[Estado] = None
        self._agentes: Dict[Jogador, Dict[str, Any]] = {}
        self._historico = []
        self._gerador = random.Random()
        self._semente_partida: Optional[int] = None
        self._calculo_em_andamento = False
        self._fila_resultado: queue.Queue = queue.Queue()
        self._semente_turno: Optional[int] = None
        self._configuracao_turno: Optional[Dict[str, Any]] = None
        self._estado_calculado: Optional[Estado] = None

        self._criar_variaveis()
        self._criar_componentes()
        self._atualizar_campos_profundidade()
        self._atualizar_visual()

    def _criar_variaveis(self) -> None:
        self.pilha_a_var = tk.StringVar(self, "8")
        self.pilha_b_var = tk.StringVar(self, "8")
        self.jogador_inicial_var = tk.StringVar(self, Jogador.MAX.value)
        self.agente_max_var = tk.StringVar(self, "Humano")
        self.agente_min_var = tk.StringVar(self, "Aleatório")
        self.profundidade_max_var = tk.StringVar(self, "3")
        self.profundidade_min_var = tk.StringVar(self, "3")
        self.semente_var = tk.StringVar(self, "")
        self.pilha_jogada_var = tk.StringVar(self, Pilha.A.value)
        self.quantidade_jogada_var = tk.StringVar(self, "1")
        self._status_var = tk.StringVar(self, "Configure uma partida para começar.")
        self._vez_var = tk.StringVar(self, "Aguardando partida")
        self._ultima_jogada_var = tk.StringVar(self, "")

    def _criar_componentes(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        ttk.Label(
            self,
            text="NIM LAB  /  TDE2",
            foreground="#2563eb",
            background="#f1f5f9",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self,
            text="Partida",
            foreground="#0f172a",
            background="#f1f5f9",
            font=("TkDefaultFont", 22, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(2, 10))

        self._criar_configuracao()
        self._criar_tabuleiro()
        self._criar_controles()
        self._criar_historico()

    def _criar_configuracao(self) -> None:
        configuracao = ttk.LabelFrame(
            self,
            text="Configuração da partida",
            padding=(12, 8),
        )
        configuracao.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        configuracao.columnconfigure(1, weight=1)

        estado_inicial = ttk.Frame(configuracao)
        estado_inicial.grid(row=0, column=0, columnspan=4, sticky="w")
        self._campo_spinbox(estado_inicial, "Pilha A", self.pilha_a_var, 0)
        self._campo_spinbox(estado_inicial, "Pilha B", self.pilha_b_var, 1)
        ttk.Label(estado_inicial, text="Começa").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            estado_inicial,
            textvariable=self.jogador_inicial_var,
            values=(Jogador.MAX.value, Jogador.MIN.value),
            state="readonly",
            width=7,
        ).grid(row=1, column=2, sticky="ew", padx=(0, 8))

        self._campo_agente(
            configuracao,
            "Agente MAX",
            self.agente_max_var,
            self.profundidade_max_var,
            1,
            "max",
        )
        self._campo_agente(
            configuracao,
            "Agente MIN",
            self.agente_min_var,
            self.profundidade_min_var,
            2,
            "min",
        )

        ttk.Label(configuracao, text="Semente (opcional)").grid(row=3, column=0, sticky="w")
        ttk.Entry(configuracao, textvariable=self.semente_var, width=12).grid(
            row=3, column=1, sticky="w"
        )

        ttk.Label(
            configuracao,
            text="Limite didático: 0 a 8 peças por pilha. Profundidade disponível para Alpha-Beta limitado e agente principal.",
            foreground="#64748b",
            wraplength=700,
        ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(5, 0))

        self._botao_iniciar = ttk.Button(
            configuracao,
            text="Iniciar partida",
            command=self.iniciar_partida,
        )
        self._botao_iniciar.grid(row=3, column=3, sticky="e")

    @staticmethod
    def _campo_spinbox(
        parent: ttk.Frame,
        rotulo: str,
        variavel: tk.StringVar,
        coluna: int,
    ) -> ttk.Spinbox:
        ttk.Label(parent, text=rotulo).grid(row=0, column=coluna, sticky="w")
        campo = ttk.Spinbox(
            parent,
            from_=0,
            to=MAXIMO_PILHAS,
            textvariable=variavel,
            width=5,
        )
        campo.grid(row=1, column=coluna, sticky="ew", padx=(0, 8))
        return campo

    def _campo_agente(
        self,
        parent: ttk.LabelFrame,
        rotulo: str,
        agente_var: tk.StringVar,
        profundidade_var: tk.StringVar,
        linha: int,
        lado: str,
    ) -> None:
        ttk.Label(parent, text=rotulo).grid(row=linha, column=0, sticky="w", pady=(6, 0))
        seletor = ttk.Combobox(
            parent,
            textvariable=agente_var,
            values=OPCOES_AGENTE,
            state="readonly",
            width=20,
        )
        seletor.grid(row=linha, column=1, sticky="ew", padx=(6, 12), pady=(6, 0))
        seletor.bind(
            "<<ComboboxSelected>>",
            lambda _evento: self._atualizar_campos_profundidade(),
        )

        ttk.Label(parent, text="Prof.").grid(row=linha, column=2, sticky="w", pady=(6, 0))
        profundidade = ttk.Spinbox(
            parent,
            from_=1,
            to=2 * MAXIMO_PILHAS,
            textvariable=profundidade_var,
            width=4,
        )
        profundidade.grid(row=linha, column=3, sticky="w", padx=(6, 0), pady=(6, 0))
        setattr(self, f"_{lado}_profundidade", profundidade)

    def _atualizar_campos_profundidade(self) -> None:
        for nome, campo in (
            (self.agente_max_var.get(), self._max_profundidade),
            (self.agente_min_var.get(), self._min_profundidade),
        ):
            campo.configure(
                state="normal" if nome in AGENTES_COM_PROFUNDIDADE else "disabled"
            )

    def _criar_tabuleiro(self) -> None:
        quadro = ttk.LabelFrame(self, text="Estado atual", padding=(12, 8))
        quadro.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        quadro.columnconfigure(0, weight=1)
        quadro.rowconfigure(1, weight=1)

        ttk.Label(
            quadro,
            textvariable=self._vez_var,
            font=("TkDefaultFont", 13, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        self._tabuleiro = tk.Canvas(
            quadro,
            height=132,
            background="#ffffff",
            highlightthickness=0,
        )
        self._tabuleiro.grid(row=1, column=0, sticky="ew")
        self._tabuleiro.bind("<Configure>", lambda _evento: self._desenhar_pilhas())

        ttk.Label(
            quadro,
            textvariable=self._ultima_jogada_var,
            foreground="#475569",
        ).grid(row=2, column=0, sticky="w", pady=(5, 0))

    def _criar_controles(self) -> None:
        controles = ttk.LabelFrame(self, text="Jogada", padding=(12, 8))
        controles.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(controles, text="Pilha").pack(side="left")
        self._seletor_pilha = ttk.Combobox(
            controles,
            textvariable=self.pilha_jogada_var,
            values=(Pilha.A.value, Pilha.B.value),
            state="readonly",
            width=6,
        )
        self._seletor_pilha.pack(side="left", padx=(6, 14))
        self._seletor_pilha.bind(
            "<<ComboboxSelected>>",
            lambda _evento: self._atualizar_quantidade_maxima(),
        )

        ttk.Label(controles, text="Retirar").pack(side="left")
        self._seletor_quantidade = ttk.Spinbox(
            controles,
            from_=1,
            to=MAXIMO_PILHAS,
            textvariable=self.quantidade_jogada_var,
            width=5,
        )
        self._seletor_quantidade.pack(side="left", padx=(6, 14))
        self._botao_proxima = ttk.Button(
            controles,
            text="Próxima jogada",
            command=self.proxima_jogada,
            state="disabled",
        )
        self._botao_proxima.pack(side="left")

        ttk.Label(
            controles,
            textvariable=self._status_var,
            foreground="#475569",
            wraplength=600,
        ).pack(side="left", padx=(16, 0), fill="x", expand=True)

    def _criar_historico(self) -> None:
        quadro = ttk.LabelFrame(self, text="Histórico de jogadas", padding=(8, 6))
        quadro.grid(row=5, column=0, sticky="nsew")
        quadro.columnconfigure(0, weight=1)
        quadro.rowconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        colunas = ("turno", "jogador", "agente", "jogada", "nos", "semente")
        self._tabela = ttk.Treeview(
            quadro,
            columns=colunas,
            show="headings",
            height=6,
        )
        titulos = {
            "turno": "Turno",
            "jogador": "MAX/MIN",
            "agente": "Agente",
            "jogada": "Jogada",
            "nos": "Nós visitados",
            "semente": "Semente do turno",
        }
        larguras = {
            "turno": 55,
            "jogador": 75,
            "agente": 190,
            "jogada": 130,
            "nos": 95,
            "semente": 180,
        }
        for coluna in colunas:
            self._tabela.heading(coluna, text=titulos[coluna])
            self._tabela.column(coluna, width=larguras[coluna], anchor="center")

        barra = ttk.Scrollbar(quadro, orient="vertical", command=self._tabela.yview)
        barra_horizontal = ttk.Scrollbar(
            quadro, orient="horizontal", command=self._tabela.xview
        )
        self._tabela.configure(
            yscrollcommand=barra.set,
            xscrollcommand=barra_horizontal.set,
        )
        self._tabela.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        barra_horizontal.grid(row=1, column=0, sticky="ew")

    def iniciar_partida(self) -> None:
        """Valida a configuração e cria um novo estado inicial."""
        try:
            pilha_a = self._ler_inteiro(
                self.pilha_a_var.get(), "Pilha A", 0, MAXIMO_PILHAS
            )
            pilha_b = self._ler_inteiro(
                self.pilha_b_var.get(), "Pilha B", 0, MAXIMO_PILHAS
            )
            if pilha_a == 0 and pilha_b == 0:
                raise ValueError("As duas pilhas não podem começar vazias.")

            semente_texto = self.semente_var.get().strip()
            semente = (
                self._ler_inteiro(semente_texto, "Semente")
                if semente_texto
                else random.SystemRandom().getrandbits(SEMENTE_BITS)
            )
            jogador_inicial = Jogador(self.jogador_inicial_var.get())
            agentes = {
                Jogador.MAX: self._criar_configuracao_agente(
                    self.agente_max_var.get(),
                    self.profundidade_max_var.get(),
                ),
                Jogador.MIN: self._criar_configuracao_agente(
                    self.agente_min_var.get(),
                    self.profundidade_min_var.get(),
                ),
            }
            estado = criar_estado_inicial(
                pilha_a,
                pilha_b,
                jogador_inicial,
            )
        except (TypeError, ValueError, tk.TclError) as erro:
            messagebox.showerror("Configuração inválida", str(erro), parent=self)
            return

        self._estado = estado
        self._agentes = agentes
        self._historico.clear()
        self._semente_partida = semente
        self._gerador = random.Random(semente)
        self._ultima_jogada_var.set("")
        self._status_var.set(
            f"Partida iniciada · semente {semente}. Use Próxima jogada para avançar."
        )
        for item in self._tabela.get_children():
            self._tabela.delete(item)
        self._botao_proxima.configure(state="normal")
        self._atualizar_visual()

    @staticmethod
    def _ler_inteiro(
        texto: str,
        campo: str,
        minimo: Optional[int] = None,
        maximo: Optional[int] = None,
    ) -> int:
        """Converte e valida entrada inteira da configuração."""
        try:
            valor = int(texto)
        except (TypeError, ValueError) as erro:
            raise ValueError(f"{campo} deve ser um número inteiro.") from erro
        if minimo is not None and valor < minimo:
            raise ValueError(f"{campo} não pode ser menor que {minimo}.")
        if maximo is not None and valor > maximo:
            raise ValueError(f"{campo} não pode ser maior que {maximo}.")
        return valor

    def _criar_configuracao_agente(
        self,
        nome: str,
        profundidade_texto: str,
    ) -> Dict[str, Any]:
        if nome not in OPCOES_AGENTE:
            raise ValueError(f"Agente desconhecido: {nome}.")
        profundidade = None
        if nome in AGENTES_COM_PROFUNDIDADE:
            profundidade = self._ler_inteiro(
                profundidade_texto,
                f"Profundidade do {nome}",
                1,
                2 * MAXIMO_PILHAS,
            )
        return {"nome": nome, "profundidade": profundidade}

    def proxima_jogada(self) -> None:
        """Executa uma jogada humana ou inicia o cálculo de uma jogada automática."""
        if self._estado is None or self._calculo_em_andamento:
            return
        if teste_terminal(self._estado):
            self._mostrar_vencedor()
            return

        configuracao = self._agentes[self._estado.jogador_atual]
        if configuracao["nome"] == "Humano":
            self._executar_jogada_humana(configuracao)
        else:
            self._iniciar_calculo_agente(configuracao)

    def _executar_jogada_humana(self, configuracao: Dict[str, Any]) -> None:
        estado = self._estado
        if estado is None:
            return
        try:
            pilha = Pilha(self.pilha_jogada_var.get())
            quantidade = self._ler_inteiro(
                self.quantidade_jogada_var.get(),
                "Quantidade a retirar",
                1,
            )
            jogada = Jogada(pilha, quantidade)
            self._aplicar_jogada(
                jogada,
                None,
                None,
                configuracao["nome"],
                estado.jogador_atual,
                estado,
            )
        except (TypeError, ValueError, tk.TclError) as erro:
            messagebox.showerror("Jogada inválida", str(erro), parent=self)

    def _iniciar_calculo_agente(self, configuracao: Dict[str, Any]) -> None:
        estado = self._estado
        if estado is None:
            return
        semente_turno = (
            self._gerador.getrandbits(SEMENTE_BITS)
            if configuracao["nome"] == "Aleatório"
            else None
        )
        self._semente_turno = semente_turno
        self._configuracao_turno = configuracao
        self._estado_calculado = estado
        self._calculo_em_andamento = True
        self._botao_proxima.configure(state="disabled")
        self._botao_iniciar.configure(state="disabled")
        self._status_var.set(f"{configuracao['nome']} está calculando a jogada…")

        tarefa = threading.Thread(
            target=self._calcular_jogada_em_thread,
            args=(estado, configuracao, semente_turno),
            daemon=True,
        )
        tarefa.start()
        self.after(40, self._verificar_calculo)

    def _calcular_jogada_em_thread(
        self,
        estado: Estado,
        configuracao: Dict[str, Any],
        semente: Optional[int],
    ) -> None:
        try:
            nome = configuracao["nome"]
            if nome == "Aleatório":
                jogada = agente_aleatorio(estado, seed=semente)
                nos = None
            elif nome == "Minimax completo":
                _, jogada, nos = minimax(estado)
            elif nome == "Alpha-Beta completo":
                _, jogada, nos = alfa_beta(estado)
            elif nome == "Alpha-Beta limitado":
                jogada, _, nos = agente_busca_limitada(
                    estado,
                    profundidade=configuracao["profundidade"],
                )
            elif nome == "Agente principal":
                jogada, _, nos = agente_principal(
                    estado,
                    profundidade=configuracao["profundidade"],
                )
            else:
                raise ValueError(f"Agente automático não suportado: {nome}.")
            self._fila_resultado.put((jogada, nos, None))
        except Exception as erro:
            self._fila_resultado.put((None, None, erro))

    def _verificar_calculo(self) -> None:
        try:
            jogada, nos, erro = self._fila_resultado.get_nowait()
        except queue.Empty:
            self.after(40, self._verificar_calculo)
            return

        estado = self._estado_calculado
        configuracao = self._configuracao_turno
        semente = self._semente_turno
        self._calculo_em_andamento = False
        self._botao_iniciar.configure(state="normal")
        if erro is not None:
            self._botao_proxima.configure(state="normal")
            self._status_var.set("O agente não conseguiu concluir a jogada.")
            messagebox.showerror("Erro do agente", str(erro), parent=self)
            self._limpar_calculo_pendente()
            return

        try:
            if estado is None or configuracao is None or self._estado != estado:
                raise RuntimeError("O estado da partida mudou durante a busca.")
            if not isinstance(jogada, Jogada):
                raise ValueError("O agente não retornou uma jogada válida.")
            self._aplicar_jogada(
                jogada,
                nos,
                semente,
                configuracao["nome"],
                estado.jogador_atual,
                estado,
            )
        except (TypeError, ValueError, RuntimeError) as erro_aplicacao:
            self._botao_proxima.configure(state="normal")
            self._status_var.set("A jogada automática não foi aplicada.")
            messagebox.showerror("Jogada inválida", str(erro_aplicacao), parent=self)
        finally:
            self._limpar_calculo_pendente()

    def _limpar_calculo_pendente(self) -> None:
        self._semente_turno = None
        self._configuracao_turno = None
        self._estado_calculado = None

    def _aplicar_jogada(
        self,
        jogada: Jogada,
        nos_visitados: Optional[int],
        semente: Optional[int],
        nome_agente: str,
        jogador: Jogador,
        estado_anterior: Estado,
    ) -> None:
        """Aplica uma ação pelas regras existentes e atualiza o histórico."""
        if self._estado != estado_anterior:
            raise RuntimeError("O estado mudou antes da aplicação da jogada.")
        estado_seguinte = resultado(estado_anterior, jogada)
        registro = {
            "turno": len(self._historico) + 1,
            "jogador": jogador,
            "agente": nome_agente,
            "jogada": jogada,
            "estado_anterior": estado_anterior,
            "estado_posterior": estado_seguinte,
            "nos_visitados": nos_visitados,
            "semente": semente,
        }
        self._historico.append(registro)
        self._estado = estado_seguinte
        self._tabela.insert(
            "",
            "end",
            values=(
                registro["turno"],
                jogador.value,
                nome_agente,
                f"{jogada.pilha.value}: retirar {jogada.quantidade}",
                "N/A" if nos_visitados is None else nos_visitados,
                "N/A" if semente is None else semente,
            ),
        )
        self._ultima_jogada_var.set(
            f"{nome_agente} ({jogador.value}) retirou {jogada.quantidade} "
            f"peça(s) da pilha {jogada.pilha.value}."
        )
        self._atualizar_visual()

        if teste_terminal(estado_seguinte):
            self._mostrar_vencedor()
        else:
            self._status_var.set("Jogada registrada. Avance para o próximo turno.")

    def _mostrar_vencedor(self) -> None:
        if self._estado is None or not teste_terminal(self._estado):
            return
        vencedor = Jogador.MAX if utilidade(self._estado) == 1 else Jogador.MIN
        agente_vencedor = self._agentes[vencedor]["nome"]
        self._vez_var.set(f"Fim de jogo · vencedor: {vencedor.value} ({agente_vencedor})")
        self._status_var.set(
            f"{vencedor.value} venceu em {len(self._historico)} jogada(s)."
        )
        self._botao_proxima.configure(state="disabled")

    def _atualizar_visual(self) -> None:
        if self._estado is None:
            self._vez_var.set("Aguardando partida")
            self._botao_proxima.configure(state="disabled")
            controles_humanos_ativos = False
        elif teste_terminal(self._estado):
            self._mostrar_vencedor()
            controles_humanos_ativos = False
        else:
            jogador_atual = self._estado.jogador_atual
            configuracao = self._agentes.get(jogador_atual)
            nome = configuracao["nome"] if configuracao else jogador_atual.value
            self._vez_var.set(f"Na vez: {jogador_atual.value} · {nome}")
            controles_humanos_ativos = (
                nome == "Humano" and not self._calculo_em_andamento
            )
            self._botao_proxima.configure(
                state="disabled" if self._calculo_em_andamento else "normal"
            )
        self._seletor_pilha.configure(
            state="readonly" if controles_humanos_ativos else "disabled"
        )
        self._seletor_quantidade.configure(
            state="normal" if controles_humanos_ativos else "disabled"
        )
        self._atualizar_quantidade_maxima()
        self._desenhar_pilhas()

    def _atualizar_quantidade_maxima(self) -> None:
        if self._estado is None:
            disponivel = MAXIMO_PILHAS
        elif self.pilha_jogada_var.get() == Pilha.A.value:
            disponivel = self._estado.pilha_a
        else:
            disponivel = self._estado.pilha_b

        self._seletor_quantidade.configure(to=max(1, disponivel))
        if disponivel == 0:
            outra_pilha = (
                Pilha.B
                if self.pilha_jogada_var.get() == Pilha.A.value
                else Pilha.A
            )
            self.pilha_jogada_var.set(outra_pilha.value)
            disponivel = (
                self._estado.pilha_b
                if outra_pilha == Pilha.B and self._estado is not None
                else self._estado.pilha_a
                if self._estado is not None
                else MAXIMO_PILHAS
            )
            self._seletor_quantidade.configure(to=max(1, disponivel))

        try:
            atual = int(self.quantidade_jogada_var.get())
        except (ValueError, tk.TclError):
            atual = 1
        if atual < 1 or atual > max(1, disponivel):
            self.quantidade_jogada_var.set("1")

    def _desenhar_pilhas(self) -> None:
        if not hasattr(self, "_tabuleiro"):
            return
        self._tabuleiro.delete("all")
        largura = max(self._tabuleiro.winfo_width(), 420)
        espacamento = largura / 2
        valores = (
            ("Pilha A", self._estado.pilha_a if self._estado else 8, "#2563eb"),
            ("Pilha B", self._estado.pilha_b if self._estado else 8, "#0f766e"),
        )
        for indice, (nome, quantidade, cor) in enumerate(valores):
            centro_x = espacamento * (indice + 0.5)
            self._tabuleiro.create_text(
                centro_x,
                17,
                text=f"{nome}  ·  {quantidade} peça(s)",
                fill="#0f172a",
                font=("TkDefaultFont", 11, "bold"),
            )
            if quantidade == 0:
                self._tabuleiro.create_text(
                    centro_x,
                    77,
                    text="Vazia",
                    fill="#64748b",
                    font=("TkDefaultFont", 10),
                )
                continue
            diametro = 24
            passo = 34
            inicio_x = centro_x - ((quantidade - 1) * passo) / 2
            for indice_peca in range(quantidade):
                x = inicio_x + indice_peca * passo
                self._tabuleiro.create_oval(
                    x - diametro / 2,
                    52,
                    x + diametro / 2,
                    52 + diametro,
                    fill=cor,
                    outline="#ffffff",
                    width=2,
                )


def criar_tela(parent: ttk.Frame) -> TelaPartida:
    """Cria a página funcional de partida dentro da navegação do aplicativo."""
    return TelaPartida(parent)
