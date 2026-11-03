"""Interface para confrontos personalizados e o protocolo experimental."""

import queue
import shutil
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from uuid import uuid4

from experimentos import (
    ExecucaoCancelada,
    REPETICOES_ALEATORIAS,
    SEMENTE_MESTRE,
    TAMANHO_PILHAS,
    calcular_total_partidas,
    configurar_confrontos,
    executar_confronto_personalizado,
    executar_experimentos,
    validar_protocolo_completo,
)
from jogo import Jogador


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_EXECUCOES = RAIZ_PROJETO / "resultados" / "execucoes"
AGENTES_DISPONIVEIS = (
    "Aleatório",
    "Minimax completo",
    "Alpha-Beta completo",
    "Alpha-Beta limitado",
    "Agente principal",
)
AGENTES_COM_PROFUNDIDADE = {"Alpha-Beta limitado", "Agente principal"}


def _label_com_wrap_responsivo(parent, **opcoes) -> ttk.Label:
    """Ajusta o texto ao espaço disponível na página."""
    label = ttk.Label(parent, **opcoes)
    if "wraplength" in opcoes:
        parent.bind(
            "<Configure>",
            lambda evento: label.configure(wraplength=max(200, evento.width - 28)),
            add="+",
        )
    return label


class TelaExperimentos(ttk.Frame):
    """Configura e executa partidas sem bloquear o loop do Tk."""

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent, style="Conteudo.TFrame", padding=(24, 18))
        self._fila: queue.Queue = queue.Queue()
        self._cancelamento: threading.Event | None = None
        self._em_execucao = False
        self._inicio_execucao = 0.0
        self._ultimo_resultado: dict | None = None
        self._ultimo_diretorio: Path | None = None
        self._criar_variaveis()
        self._criar_layout()
        self._atualizar_controles_agentes()
        self._atualizar_total_personalizado()

    def _criar_variaveis(self) -> None:
        self.agente_max_var = tk.StringVar(self, "Aleatório")
        self.agente_min_var = tk.StringVar(self, "Alpha-Beta limitado")
        self.profundidade_max_var = tk.StringVar(self, "3")
        self.profundidade_min_var = tk.StringVar(self, "2")
        self.ordenar_max_var = tk.BooleanVar(self, False)
        self.ordenar_min_var = tk.BooleanVar(self, False)
        self.posicoes_var = tk.StringVar(self, "2,3; 4,4")
        self.repeticoes_var = tk.StringVar(self, "5")
        self.semente_var = tk.StringVar(self, str(SEMENTE_MESTRE))
        self.jogador_inicial_var = tk.StringVar(self, Jogador.MAX.value)
        self._total_personalizado_var = tk.StringVar(self, "")
        self._status_var = tk.StringVar(self, "Configure um confronto para começar.")
        self._detalhe_progresso_var = tk.StringVar(self, "")
        self._resultado_var = tk.StringVar(self, "Nenhuma execução concluída nesta sessão.")
        self._local_var = tk.StringVar(self, "")

    def _criar_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        ttk.Label(
            self,
            text="NIM LAB  /  EXECUÇÃO CONTROLADA",
            foreground="#2563eb",
            background="#f1f5f9",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self,
            text="Experimentos",
            foreground="#0f172a",
            background="#f1f5f9",
            font=("TkDefaultFont", 22, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))

        self._abas = ttk.Notebook(self)
        self._abas.grid(row=2, column=0, sticky="nsew")
        self._criar_aba_personalizada()
        self._criar_aba_protocolo()
        self._criar_aba_resultado()

        progresso = ttk.LabelFrame(self, text="Acompanhamento", padding=10)
        progresso.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        progresso.columnconfigure(0, weight=1)
        ttk.Label(progresso, textvariable=self._status_var).grid(
            row=0, column=0, sticky="w"
        )
        self._barra_progresso = ttk.Progressbar(
            progresso, mode="determinate", maximum=1
        )
        self._barra_progresso.grid(row=1, column=0, sticky="ew", pady=6)
        _label_com_wrap_responsivo(
            progresso,
            textvariable=self._detalhe_progresso_var,
            wraplength=760,
            justify="left",
        ).grid(row=2, column=0, sticky="w")
        self._botao_cancelar = ttk.Button(
            progresso,
            text="Cancelar execução",
            command=self.cancelar_execucao,
            state="disabled",
        )
        self._botao_cancelar.grid(row=0, column=1, rowspan=3, padx=(12, 0))

    def _criar_aba_personalizada(self) -> None:
        aba = ttk.Frame(self._abas, padding=14)
        aba.columnconfigure(0, weight=1)
        self._abas.add(aba, text="Confronto personalizado")
        _label_com_wrap_responsivo(
            aba,
            text=(
                "Informe as posições no formato A,B; A,B. MAX e MIN continuam sendo "
                "papéis do jogo; o jogador inicial é configurado separadamente."
            ),
            wraplength=760,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        agentes = ttk.LabelFrame(aba, text="Agentes e opções de busca", padding=10)
        agentes.grid(row=1, column=0, sticky="ew")
        agentes.columnconfigure(1, weight=1)
        agentes.columnconfigure(4, weight=1)
        self._criar_seletor_agente(agentes, "Agente de MAX", self.agente_max_var, 0)
        self._criar_seletor_agente(agentes, "Agente de MIN", self.agente_min_var, 3)
        self.agente_max_var.trace_add("write", self._atualizar_controles_agentes)
        self.agente_min_var.trace_add("write", self._atualizar_controles_agentes)

        controles = ttk.LabelFrame(aba, text="Partidas e reprodutibilidade", padding=10)
        controles.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        controles.columnconfigure(1, weight=1)
        ttk.Label(controles, text="Posições A,B").grid(row=0, column=0, sticky="w")
        posicoes = ttk.Entry(controles, textvariable=self.posicoes_var, width=28)
        posicoes.grid(row=0, column=1, sticky="ew", padx=(8, 18))
        self.posicoes_var.trace_add("write", self._atualizar_total_personalizado)
        ttk.Label(controles, text="Repetições por posição").grid(
            row=0, column=2, sticky="w"
        )
        repeticoes = ttk.Spinbox(
            controles,
            from_=1,
            to=1000,
            textvariable=self.repeticoes_var,
            width=7,
        )
        repeticoes.grid(row=0, column=3, sticky="w", padx=(8, 18))
        self.repeticoes_var.trace_add("write", self._atualizar_total_personalizado)
        ttk.Label(controles, text="Semente mestre").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(controles, textvariable=self.semente_var, width=14).grid(
            row=1, column=1, sticky="w", padx=(8, 18), pady=(8, 0)
        )
        ttk.Label(controles, text="Começa").grid(row=1, column=2, sticky="w", pady=(8, 0))
        ttk.Combobox(
            controles,
            textvariable=self.jogador_inicial_var,
            values=(Jogador.MAX.value, Jogador.MIN.value),
            state="readonly",
            width=8,
        ).grid(row=1, column=3, sticky="w", padx=(8, 18), pady=(8, 0))

        acoes = ttk.Frame(aba)
        acoes.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(acoes, textvariable=self._total_personalizado_var).pack(side="left")
        self._botao_personalizado = ttk.Button(
            acoes,
            text="Executar confronto",
            command=self.executar_personalizado,
        )
        self._botao_personalizado.pack(side="right")

    def _criar_seletor_agente(
        self,
        parent: ttk.LabelFrame,
        titulo: str,
        variavel: tk.StringVar,
        coluna: int,
    ) -> None:
        lado = "max" if coluna == 0 else "min"
        ttk.Label(parent, text=titulo).grid(row=0, column=coluna, sticky="w")
        seletor = ttk.Combobox(
            parent,
            textvariable=variavel,
            values=AGENTES_DISPONIVEIS,
            state="readonly",
            width=23,
        )
        seletor.grid(row=1, column=coluna, sticky="ew", padx=(0, 10))
        setattr(self, f"_{lado}_seletor", seletor)
        ttk.Label(parent, text="Prof.").grid(
            row=0, column=coluna + 1, sticky="w"
        )
        profundidade = ttk.Spinbox(
            parent,
            from_=1,
            to=2 * TAMANHO_PILHAS,
            textvariable=(
                self.profundidade_max_var
                if lado == "max"
                else self.profundidade_min_var
            ),
            width=5,
        )
        profundidade.grid(row=1, column=coluna + 1, sticky="w", padx=(0, 12))
        setattr(self, f"_{lado}_profundidade", profundidade)
        ordenar_var = self.ordenar_max_var if lado == "max" else self.ordenar_min_var
        ordenar = ttk.Checkbutton(
            parent,
            text="Ordenar jogadas",
            variable=ordenar_var,
        )
        ordenar.grid(row=1, column=coluna + 2, sticky="w")
        setattr(self, f"_{lado}_ordenar", ordenar)

    def _criar_aba_protocolo(self) -> None:
        aba = ttk.Frame(self._abas, padding=18)
        aba.columnconfigure(0, weight=1)
        self._abas.add(aba, text="Protocolo completo")
        total = validar_protocolo_completo()
        _label_com_wrap_responsivo(
            aba,
            text="Execução do protocolo experimental aprovado",
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        _label_com_wrap_responsivo(
            aba,
            text=(
                f"Esta opção executa exatamente {total:,} partidas: "
                "16.000 contra agente aleatório, 1.920 de profundidade, "
                "1.280 de ordenação e 320 de comparação controlada. "
                f"A semente mestre permanece fixa em {SEMENTE_MESTRE}. "
                "A configuração não pode ser editada nesta tela."
            ).replace(",", "."),
            wraplength=760,
            justify="left",
        ).grid(row=1, column=0, sticky="w")
        _label_com_wrap_responsivo(
            aba,
            text=(
                "Os arquivos serão publicados numa pasta identificada em "
                "resultados/execucoes/. Os CSVs de resultados/final/ não serão "
                "sobrescritos. O cancelamento é verificado entre partidas; uma "
                "execução cancelada não publica CSVs parciais."
            ),
            wraplength=760,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(12, 18))
        self._botao_protocolo = ttk.Button(
            aba,
            text=f"Executar {total:,} partidas".replace(",", "."),
            command=self.executar_protocolo,
        )
        self._botao_protocolo.grid(row=3, column=0, sticky="w")

    def _criar_aba_resultado(self) -> None:
        aba = ttk.Frame(self._abas, padding=12)
        aba.columnconfigure(0, weight=1)
        aba.rowconfigure(2, weight=1)
        self._abas.add(aba, text="Resultado da execução")
        _label_com_wrap_responsivo(
            aba,
            textvariable=self._resultado_var,
            wraplength=760,
            justify="left",
        ).grid(row=0, column=0, sticky="ew")
        _label_com_wrap_responsivo(
            aba,
            textvariable=self._local_var,
            wraplength=760,
            justify="left",
            foreground="#1e3a8a",
        ).grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self._tabela_resumo = ttk.Treeview(
            aba,
            columns=(
                "agente",
                "partidas",
                "vitorias",
                "derrotas",
                "empates",
                "taxa",
                "decisoes",
                "media",
                "maximo",
            ),
            show="headings",
            height=8,
        )
        for coluna, titulo, largura in (
            ("agente", "Configuração", 270),
            ("partidas", "Partidas", 80),
            ("vitorias", "Vitórias", 80),
            ("derrotas", "Derrotas", 80),
            ("empates", "Empates", 70),
            ("taxa", "Vitória %", 90),
            ("decisoes", "Decisões", 90),
            ("media", "Média nós", 100),
            ("maximo", "Máximo nós", 100),
        ):
            self._tabela_resumo.heading(coluna, text=titulo)
            self._tabela_resumo.column(coluna, width=largura, anchor="center")
        self._tabela_resumo.grid(row=2, column=0, sticky="nsew")
        barra = ttk.Scrollbar(aba, orient="vertical", command=self._tabela_resumo.yview)
        barra_horizontal = ttk.Scrollbar(
            aba, orient="horizontal", command=self._tabela_resumo.xview
        )
        barra.grid(row=2, column=1, sticky="ns")
        self._tabela_resumo.configure(
            yscrollcommand=barra.set,
            xscrollcommand=barra_horizontal.set,
        )
        barra_horizontal.grid(row=3, column=0, sticky="ew")
        self._botao_exportar = ttk.Button(
            aba,
            text="Exportar cópias dos CSVs…",
            command=self.exportar_csvs,
            state="disabled",
        )
        self._botao_exportar.grid(row=4, column=0, sticky="w", pady=(8, 0))

    def _atualizar_controles_agentes(self, *_args) -> None:
        for lado, nome in (
            ("max", self.agente_max_var.get()),
            ("min", self.agente_min_var.get()),
        ):
            habilitado = nome in AGENTES_COM_PROFUNDIDADE
            getattr(self, f"_{lado}_profundidade").configure(
                state="normal" if habilitado else "disabled"
            )
            ordenar = getattr(self, f"_{lado}_ordenar")
            if nome == "Agente principal":
                ordenar.configure(state="disabled")
                (self.ordenar_max_var if lado == "max" else self.ordenar_min_var).set(True)
            else:
                ordenar.configure(state="normal" if nome == "Alpha-Beta limitado" else "disabled")
                if nome != "Alpha-Beta limitado":
                    (self.ordenar_max_var if lado == "max" else self.ordenar_min_var).set(False)

    def _atualizar_total_personalizado(self, *_args) -> None:
        try:
            posicoes = self._ler_posicoes(self.posicoes_var.get())
            repeticoes = int(self.repeticoes_var.get())
            if repeticoes < 1:
                raise ValueError("As repetições precisam ser pelo menos 1.")
            self._total_personalizado_var.set(
                f"Serão executadas {len(posicoes) * repeticoes} partidas."
            )
        except (ValueError, tk.TclError) as erro:
            self._total_personalizado_var.set(f"Parâmetros inválidos: {erro}")

    @staticmethod
    def _ler_posicoes(texto: str) -> list[tuple[int, int]]:
        posicoes = []
        for parte in texto.split(";"):
            campos = parte.strip().split(",")
            if len(campos) != 2:
                raise ValueError("Use o formato A,B; A,B.")
            try:
                a, b = (int(campo.strip()) for campo in campos)
            except ValueError as erro:
                raise ValueError("As pilhas devem ter quantidades inteiras.") from erro
            if not (0 <= a <= TAMANHO_PILHAS and 0 <= b <= TAMANHO_PILHAS):
                raise ValueError(f"Cada pilha deve estar entre 0 e {TAMANHO_PILHAS}.")
            if a + b == 0:
                raise ValueError("A posição (0,0) já é terminal.")
            posicoes.append((a, b))
        if not posicoes:
            raise ValueError("Informe pelo menos uma posição.")
        if len(set(posicoes)) != len(posicoes):
            raise ValueError("Remova posições repetidas.")
        return posicoes

    def executar_personalizado(self) -> None:
        if self._em_execucao:
            return
        try:
            posicoes = self._ler_posicoes(self.posicoes_var.get())
            repeticoes = self._ler_inteiro_positivo(
                self.repeticoes_var.get(), "Repetições", 1000
            )
            seed = int(self.semente_var.get())
            max_depth = self._ler_inteiro_positivo(
                self.profundidade_max_var.get(), "Profundidade de MAX", 16
            )
            min_depth = self._ler_inteiro_positivo(
                self.profundidade_min_var.get(), "Profundidade de MIN", 16
            )
            jogador_inicial = Jogador(self.jogador_inicial_var.get())
        except (ValueError, tk.TclError) as erro:
            messagebox.showerror("Parâmetros inválidos", str(erro), parent=self)
            return
        total = len(posicoes) * repeticoes
        argumentos = {
            "agente_max": self.agente_max_var.get(),
            "agente_min": self.agente_min_var.get(),
            "posicoes": posicoes,
            "repeticoes": repeticoes,
            "jogador_inicial": jogador_inicial,
            "semente_mestre": seed,
            "profundidade_max": max_depth,
            "profundidade_min": min_depth,
            "ordenar_max": self.ordenar_max_var.get(),
            "ordenar_min": self.ordenar_min_var.get(),
        }
        self._iniciar_execucao("personalizado", argumentos, total)

    def executar_protocolo(self) -> None:
        if self._em_execucao:
            return
        total = calcular_total_partidas(configurar_confrontos())
        confirmado = messagebox.askyesno(
            "Confirmar protocolo completo",
            f"A execução vai iniciar {total:,} partidas com a configuração aprovada "
            f"e semente mestre {SEMENTE_MESTRE}. Os arquivos irão para uma pasta nova "
            "em resultados/execucoes/; resultados/final/ não será alterada.\n\n"
            "Deseja continuar?".replace(",", "."),
            parent=self,
        )
        if confirmado:
            self._iniciar_execucao("protocolo", {}, total)

    @staticmethod
    def _ler_inteiro_positivo(texto: str, rotulo: str, maximo: int) -> int:
        valor = int(texto)
        if not 1 <= valor <= maximo:
            raise ValueError(f"{rotulo} deve estar entre 1 e {maximo}.")
        return valor

    def _iniciar_execucao(self, tipo: str, argumentos: dict, total: int) -> None:
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
        self._cancelamento = threading.Event()
        self._em_execucao = True
        self._inicio_execucao = time.monotonic()
        self._barra_progresso.configure(maximum=total, value=0)
        self._detalhe_progresso_var.set("")
        self._status_var.set(f"Preparando {total:,} partidas…".replace(",", "."))
        self._botao_cancelar.configure(state="normal")
        self._botao_personalizado.configure(state="disabled")
        self._botao_protocolo.configure(state="disabled")
        self._botao_exportar.configure(state="disabled")
        self._tabela_resumo.delete(*self._tabela_resumo.get_children())
        self._resultado_var.set("Execução em andamento.")
        self._local_var.set("")
        self._abas.select(2)
        threading.Thread(
            target=self._executar_em_background,
            args=(tipo, argumentos, run_id),
            daemon=True,
        ).start()
        self.after(100, self._processar_fila)

    def _executar_em_background(
        self, tipo: str, argumentos: dict, run_id: str
    ) -> None:
        staging = PASTA_EXECUCOES / f".{run_id}.staging"
        destino = PASTA_EXECUCOES / run_id
        staging_criado = False

        def publicar_progresso(dados: dict) -> None:
            self._fila.put(("progresso", dados))

        try:
            PASTA_EXECUCOES.mkdir(parents=True, exist_ok=True)
            if destino.exists():
                raise FileExistsError(f"A pasta de execução já existe: {destino}")
            staging.mkdir()
            staging_criado = True
            if tipo == "protocolo":
                resultado = executar_experimentos(
                    diretorio_resultados=staging,
                    progresso=publicar_progresso,
                    cancelar=self._cancelamento.is_set,
                )
            else:
                resultado = executar_confronto_personalizado(
                    **argumentos,
                    diretorio_resultados=staging,
                    progresso=publicar_progresso,
                    cancelar=self._cancelamento.is_set,
                )
            if self._cancelamento.is_set():
                raise ExecucaoCancelada("A execução foi cancelada.")
            staging.rename(destino)
            resultado["caminhos_csv"] = {
                nome: str(destino / nome) for nome in resultado["caminhos_csv"]
            }
            self._fila.put(("concluida", (resultado, destino, run_id)))
        except ExecucaoCancelada as erro:
            try:
                if staging_criado and staging.exists():
                    shutil.rmtree(staging)
            except OSError as falha_limpeza:
                self._fila.put(
                    (
                        "erro",
                        RuntimeError(
                            f"{erro} A pasta temporária não pôde ser removida: "
                            f"{falha_limpeza}"
                        ),
                    )
                )
            else:
                self._fila.put(("cancelada", str(erro)))
        except Exception as erro:
            try:
                if staging_criado and staging.exists():
                    shutil.rmtree(staging)
            except OSError as falha_limpeza:
                erro = RuntimeError(
                    f"{erro} A pasta temporária não pôde ser removida: "
                    f"{falha_limpeza}"
                )
            self._fila.put(("erro", erro))

    def _processar_fila(self) -> None:
        evento_terminal = False
        ultimo_progresso = None
        for _ in range(100):
            try:
                tipo, dados = self._fila.get_nowait()
            except queue.Empty:
                break
            if tipo == "progresso":
                ultimo_progresso = dados
            elif tipo == "concluida":
                resultado, destino, run_id = dados
                self._finalizar_execucao(resultado, destino, run_id)
                evento_terminal = True
                break
            elif tipo == "cancelada":
                self._encerrar_execucao()
                self._status_var.set("Execução cancelada; nenhum CSV parcial foi publicado.")
                self._resultado_var.set(f"Cancelada com segurança: {dados}")
                evento_terminal = True
                break
            elif tipo == "erro":
                self._encerrar_execucao()
                self._status_var.set(f"Falha na execução: {dados}")
                self._resultado_var.set("A execução falhou. Nenhum resultado parcial foi publicado.")
                messagebox.showerror("Falha na execução", str(dados), parent=self)
                evento_terminal = True
                break
        if ultimo_progresso is not None and not evento_terminal:
            self._mostrar_progresso(ultimo_progresso)
        if self._em_execucao and not evento_terminal:
            self.after(100, self._processar_fila)

    def _mostrar_progresso(self, dados: dict) -> None:
        concluidas = dados["concluidas"]
        total = dados["total"]
        tempo = time.monotonic() - self._inicio_execucao
        vitorias = ", ".join(
            f"{nome}: {quantidade}"
            for nome, quantidade in sorted(dados["vitorias"].items())
        ) or "ainda sem vencedores"
        self._barra_progresso.configure(maximum=total, value=concluidas)
        self._status_var.set(
            f"{concluidas:,}/{total:,} partidas concluídas · "
            f"{dados['restantes']:,} restantes · {tempo:.1f} s".replace(",", ".")
        )
        self._detalhe_progresso_var.set(
            f"Confronto atual: {dados['confronto']}\n"
            f"Vitórias parciais por configuração: {vitorias}"
        )

    def cancelar_execucao(self) -> None:
        if self._em_execucao and self._cancelamento is not None:
            self._cancelamento.set()
            self._botao_cancelar.configure(state="disabled")
            self._status_var.set("Cancelamento solicitado; aguardando o fim da partida atual.")

    def _finalizar_execucao(
        self, resultado: dict, destino: Path, run_id: str
    ) -> None:
        tempo = time.monotonic() - self._inicio_execucao
        self._encerrar_execucao()
        self._ultimo_resultado = resultado
        self._ultimo_diretorio = destino
        self._popular_resumo(resultado["resumo"])
        total = len(resultado["partidas"])
        self._status_var.set(
            f"Execução concluída · {total:,} partidas · {tempo:.1f} s".replace(",", ".")
        )
        self._resultado_var.set(
            f"Execução {run_id}: {total:,} partidas e "
            f"{len(resultado['jogadas']):,} jogadas registradas.\n"
            f"Semente mestre: {resultado['partidas'][0]['semente_mestre'] if total else 'N/A'}."
            .replace(",", ".")
        )
        self._local_var.set(f"CSVs gerados em: {destino}")
        self._botao_exportar.configure(state="normal")
        self._detalhe_progresso_var.set(
            "Os nós são calculados somente para decisões de busca; N/A permanece não aplicável."
        )
        self._botao_personalizado.configure(state="normal")
        self._botao_protocolo.configure(state="normal")

    def _encerrar_execucao(self) -> None:
        self._em_execucao = False
        self._botao_cancelar.configure(state="disabled")
        self._botao_personalizado.configure(state="normal")
        self._botao_protocolo.configure(state="normal")

    def _popular_resumo(self, resumos: list[dict]) -> None:
        self._tabela_resumo.delete(*self._tabela_resumo.get_children())
        for indice, linha in enumerate(resumos):
            self._tabela_resumo.insert(
                "",
                "end",
                iid=f"resumo-execucao-{indice}",
                values=(
                    linha["configuracao_agente"],
                    linha["quantidade_partidas"],
                    linha["vitorias"],
                    linha["derrotas"],
                    linha["empates"],
                    f"{linha['taxa_vitoria_percentual']:.2f}",
                    linha["decisoes_busca"],
                    _formatar_metrica(linha["media_nos_por_decisao"]),
                    _formatar_metrica(linha["maximo_nos_por_decisao"]),
                ),
            )

    def exportar_csvs(self) -> None:
        if self._ultimo_diretorio is None:
            return
        destino = filedialog.askdirectory(
            title="Escolha a pasta para copiar os três CSVs",
            parent=self,
        )
        if not destino:
            return
        pasta_destino = Path(destino).resolve()
        if pasta_destino == self._ultimo_diretorio.resolve():
            messagebox.showinfo(
                "CSV já exportados",
                "Os três arquivos já estão nessa pasta.",
                parent=self,
            )
            return
        arquivos = ("jogadas.csv", "partidas.csv", "resumo.csv")
        existentes = [nome for nome in arquivos if (pasta_destino / nome).exists()]
        if existentes and not messagebox.askyesno(
            "Confirmar substituição",
            "Os arquivos a seguir já existem e serão substituídos: "
            + ", ".join(existentes),
            parent=self,
        ):
            return
        for nome in arquivos:
            shutil.copy2(self._ultimo_diretorio / nome, pasta_destino / nome)
        messagebox.showinfo(
            "Exportação concluída",
            f"Os três CSVs foram copiados para {pasta_destino}.",
            parent=self,
        )


def _formatar_metrica(valor) -> str:
    if valor == "N/A" or valor is None:
        return "N/A"
    return f"{float(valor):.2f}"


def criar_tela(parent: ttk.Frame) -> TelaExperimentos:
    """Cria a interface dos experimentos."""
    return TelaExperimentos(parent)
