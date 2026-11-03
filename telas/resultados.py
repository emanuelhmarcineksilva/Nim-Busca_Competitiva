"""Painel de consulta dos resultados experimentais salvos em CSV."""

import csv
from collections import defaultdict
from pathlib import Path
import tkinter as tk
from tkinter import ttk


PASTA_RESULTADOS = Path(__file__).resolve().parents[1] / "resultados" / "final"
TAMANHO_PAGINA = 200

COLUNAS_RESUMO = (
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
)


def _ler_csv(caminho: Path) -> list[dict[str, str]]:
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_resultados(pasta: Path | str = PASTA_RESULTADOS) -> dict[str, list[dict[str, str]]]:
    """Lê os três CSVs sem modificar ou recalcular os resultados originais."""
    pasta = Path(pasta)
    nomes = {
        "resumo": "resumo.csv",
        "partidas": "partidas.csv",
        "jogadas": "jogadas.csv",
    }
    dados = {}
    for chave, nome in nomes.items():
        caminho = pasta / nome
        if not caminho.is_file():
            raise FileNotFoundError(f"Arquivo de resultados não encontrado: {caminho}")
        dados[chave] = _ler_csv(caminho)
    return dados


def calcular_indicadores_gerais(dados: dict[str, list[dict[str, str]]]) -> dict[str, int]:
    """Calcula contagens gerais diretamente dos registros carregados."""
    partidas = dados["partidas"]
    return {
        "partidas": len(partidas),
        "confrontos": len({partida["confronto"] for partida in partidas}),
        "jogadas": len(dados["jogadas"]),
        "configuracoes": len(
            {linha["configuracao_agente"] for linha in dados["resumo"]}
        ),
        "empates": sum(partida.get("vencedor") == "EMPATE" for partida in partidas),
    }


def obter_estatisticas_profundidade(
    resumo: list[dict[str, str]],
) -> list[dict[str, float | int | str]]:
    """Agrupa as decisões dos confrontos de profundidade com média ponderada."""
    acumulado: dict[int, dict[str, float | int]] = {}
    for linha in resumo:
        if linha["grupo_experimental"] != "profundidade":
            continue
        configuracao = linha["configuracao_agente"]
        profundidade = _extrair_profundidade(configuracao)
        if profundidade is None or linha["decisoes_busca"] == "0":
            continue
        item = acumulado.setdefault(
            profundidade, {"decisoes": 0, "total_nos": 0.0, "maximo": 0}
        )
        decisoes = int(linha["decisoes_busca"])
        item["decisoes"] += decisoes
        item["total_nos"] += float(linha["media_nos_por_decisao"]) * decisoes
        item["maximo"] = max(
            int(item["maximo"]), int(linha["maximo_nos_por_decisao"])
        )
    return [
        {
            "profundidade": profundidade,
            "decisoes": int(item["decisoes"]),
            "media": float(item["total_nos"]) / int(item["decisoes"]),
            "maximo": int(item["maximo"]),
        }
        for profundidade, item in sorted(acumulado.items())
        if item["decisoes"]
    ]


def obter_estatisticas_ordenacao(
    resumo: list[dict[str, str]],
) -> list[dict[str, float | int | str]]:
    """Agrupa decisões de busca por profundidade e estado da ordenação."""
    acumulado: dict[tuple[int, str], dict[str, float | int]] = {}
    for linha in resumo:
        if linha["grupo_experimental"] != "ordenacao":
            continue
        configuracao = linha["configuracao_agente"]
        profundidade = _extrair_profundidade(configuracao)
        if profundidade is None or linha["decisoes_busca"] == "0":
            continue
        ordenacao = (
            "ligada"
            if "; ordenação=ligada" in configuracao
            else "desligada"
        )
        item = acumulado.setdefault(
            (profundidade, ordenacao),
            {"decisoes": 0, "total_nos": 0.0, "maximo": 0},
        )
        decisoes = int(linha["decisoes_busca"])
        item["decisoes"] += decisoes
        item["total_nos"] += float(linha["media_nos_por_decisao"]) * decisoes
        item["maximo"] = max(
            int(item["maximo"]), int(linha["maximo_nos_por_decisao"])
        )
    return [
        {
            "profundidade": profundidade,
            "ordenacao": ordenacao,
            "decisoes": int(item["decisoes"]),
            "media": float(item["total_nos"]) / int(item["decisoes"]),
            "maximo": int(item["maximo"]),
        }
        for (profundidade, ordenacao), item in sorted(acumulado.items())
        if item["decisoes"]
    ]


def _extrair_profundidade(configuracao: str) -> int | None:
    marcador = "profundidade="
    if marcador not in configuracao:
        return None
    try:
        return int(configuracao.split(marcador, 1)[1].split(";", 1)[0])
    except ValueError:
        return None


class TelaResultados(ttk.Frame):
    """Exibe indicadores, comparações, gráficos e históricos das partidas."""

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent, style="Conteudo.TFrame", padding=(24, 18))
        self._dados: dict[str, list[dict[str, str]]] = {}
        self._partidas_filtradas: list[dict[str, str]] = []
        self._pagina = 0
        self._jogadas_por_partida: dict[str, list[dict[str, str]]] = defaultdict(list)
        self._criar_variaveis()
        self._criar_layout()
        self.carregar()

    def _criar_variaveis(self) -> None:
        self._confronto_var = tk.StringVar(self)
        self._grafico_var = tk.StringVar(self, "Taxa de vitória (%)")
        self._pesquisa_var = tk.StringVar(self)
        self._status_var = tk.StringVar(self, "Carregando CSVs...")
        self._pagina_var = tk.StringVar(self, "")
        self._interpretacao_var = tk.StringVar(self, "")
        self._cartoes = {
            nome: tk.StringVar(self, "—")
            for nome in ("Partidas", "Confrontos", "Jogadas", "Configurações", "Empates")
        }

    def _criar_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        ttk.Label(
            self,
            text="NIM LAB  /  DADOS EXPERIMENTAIS REAIS",
            foreground="#2563eb",
            background="#f1f5f9",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self,
            text="Resultados",
            foreground="#0f172a",
            background="#f1f5f9",
            font=("TkDefaultFont", 22, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))

        self._abas = ttk.Notebook(self)
        self._abas.grid(row=2, column=0, sticky="nsew")
        self._criar_aba_visao_geral()
        self._criar_aba_partidas()
        self._criar_aba_analise()
        ttk.Label(
            self,
            textvariable=self._status_var,
            foreground="#475569",
            background="#f1f5f9",
            anchor="w",
        ).grid(row=3, column=0, sticky="ew", pady=(8, 0))

    def _criar_aba_visao_geral(self) -> None:
        aba = ttk.Frame(self._abas, padding=10)
        aba.columnconfigure(0, weight=1)
        aba.rowconfigure(3, weight=1)
        self._abas.add(aba, text="Visão geral e gráficos")
        cartoes = ttk.Frame(aba)
        cartoes.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for coluna, (nome, variavel) in enumerate(self._cartoes.items()):
            cartoes.columnconfigure(coluna, weight=1)
            caixa = ttk.LabelFrame(cartoes, text=nome, padding=(10, 7))
            caixa.grid(row=0, column=coluna, sticky="ew", padx=(0, 6))
            ttk.Label(
                caixa, textvariable=variavel, font=("TkDefaultFont", 15, "bold")
            ).pack(anchor="w")

        filtros = ttk.Frame(aba)
        filtros.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(filtros, text="Confronto").pack(side="left")
        self._seletor_confronto = ttk.Combobox(
            filtros,
            textvariable=self._confronto_var,
            state="readonly",
            width=54,
        )
        self._seletor_confronto.pack(side="left", padx=(8, 18))
        self._seletor_confronto.bind("<<ComboboxSelected>>", self._selecionar_confronto)
        ttk.Label(filtros, text="Gráfico").pack(side="left")
        self._seletor_grafico = ttk.Combobox(
            filtros,
            textvariable=self._grafico_var,
            values=(
                "Vitórias",
                "Taxa de vitória (%)",
                "Média de nós por decisão",
                "Máximo de nós por decisão",
                "Efeito da profundidade",
                "Efeito da ordenação",
            ),
            state="readonly",
            width=29,
        )
        self._seletor_grafico.pack(side="left", padx=8)
        self._seletor_grafico.bind("<<ComboboxSelected>>", self._atualizar_grafico)
        ttk.Button(filtros, text="Recarregar CSVs", command=self.carregar).pack(
            side="right"
        )

        self._grafico = tk.Canvas(
            aba,
            height=230,
            background="#ffffff",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
        )
        self._grafico.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self._grafico.bind("<Configure>", self._atualizar_grafico)
        self._abas_resumo = ttk.Notebook(aba)
        self._abas_resumo.grid(row=3, column=0, sticky="nsew")
        aba_confronto = ttk.Frame(self._abas_resumo, padding=(2, 4))
        aba_vitorias = ttk.Frame(self._abas_resumo, padding=(2, 4))
        aba_confronto.columnconfigure(0, weight=1)
        aba_confronto.rowconfigure(0, weight=1)
        aba_vitorias.columnconfigure(0, weight=1)
        aba_vitorias.rowconfigure(1, weight=1)
        self._abas_resumo.add(aba_confronto, text="Confronto selecionado")
        self._abas_resumo.add(aba_vitorias, text="Vitórias agregadas")
        ttk.Label(
            aba_vitorias,
            text=(
                "Soma de vitórias e partidas por rótulo de configuração em vários "
                "confrontos. Os contextos diferem; use a aba de confronto para comparar "
                "taxas e custos sem misturá-los."
            ),
            wraplength=950,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self._tabela_vitorias = self._criar_tabela(
            aba_vitorias,
            colunas=(
                ("config", "Configuração", 330),
                ("partidas", "Partidas acumuladas", 150),
                ("vitorias", "Vitórias acumuladas", 150),
            ),
        )
        self._tabela_vitorias.master.grid(row=1, column=0, sticky="nsew")
        self._tabela_resumo = self._criar_tabela(
            aba_confronto,
            colunas=(
                ("agente", "Agente", 110),
                ("config", "Configuração", 230),
                ("partidas", "Partidas", 75),
                ("vitorias", "Vitórias", 75),
                ("derrotas", "Derrotas", 75),
                ("empates", "Empates", 70),
                ("taxa", "Vitória %", 85),
                ("decisoes", "Decisões", 80),
                ("media", "Média nós", 90),
                ("maximo", "Máximo nós", 90),
            ),
        )
        self._tabela_resumo.master.grid(row=0, column=0, sticky="nsew")

    def _criar_aba_partidas(self) -> None:
        aba = ttk.Frame(self._abas, padding=10)
        aba.columnconfigure(0, weight=1)
        aba.rowconfigure(1, weight=1)
        aba.rowconfigure(4, weight=1)
        self._abas.add(aba, text="Partidas e jogadas")
        filtros = ttk.Frame(aba)
        filtros.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(filtros, text="Buscar ID da partida").pack(side="left")
        busca = ttk.Entry(filtros, textvariable=self._pesquisa_var, width=35)
        busca.pack(side="left", padx=8)
        busca.bind("<Return>", self._pesquisar_partida)
        ttk.Button(filtros, text="Buscar", command=self._pesquisar_partida).pack(
            side="left"
        )
        ttk.Button(filtros, text="Limpar", command=self._limpar_pesquisa).pack(
            side="left", padx=6
        )
        self._tabela_partidas = self._criar_tabela(
            aba,
            colunas=(
                ("id", "ID", 150),
                ("inicio", "Pilhas iniciais", 120),
                ("inicia", "Começa", 80),
                ("vencedor", "Vencedor", 180),
                ("jogadas", "Jogadas", 75),
                ("semente", "Semente da partida", 150),
            ),
            altura=9,
        )
        self._tabela_partidas.master.grid(row=1, column=0, sticky="nsew")
        self._tabela_partidas.bind("<<TreeviewSelect>>", self._selecionar_partida)
        navegacao = ttk.Frame(aba)
        navegacao.grid(row=2, column=0, sticky="ew", pady=6)
        ttk.Button(navegacao, text="Página anterior", command=self._pagina_anterior).pack(
            side="left"
        )
        ttk.Label(navegacao, textvariable=self._pagina_var).pack(
            side="left", padx=10
        )
        ttk.Button(navegacao, text="Próxima página", command=self._proxima_pagina).pack(
            side="left"
        )
        ttk.Label(
            aba,
            text="Histórico de jogadas da partida selecionada",
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=3, column=0, sticky="w", pady=(4, 5))
        self._tabela_jogadas = self._criar_tabela(
            aba,
            colunas=(
                ("turno", "Turno", 60),
                ("agente", "Agente", 170),
                ("jogador", "Jogador", 70),
                ("anterior", "Estado anterior", 150),
                ("jogada", "Jogada", 100),
                ("posterior", "Estado posterior", 150),
                ("nos", "Nós visitados", 100),
                ("semente", "Semente aleatória", 150),
            ),
            altura=7,
        )
        self._tabela_jogadas.master.grid(row=4, column=0, sticky="nsew")

    def _criar_aba_analise(self) -> None:
        aba = ttk.Frame(self._abas, padding=18)
        aba.columnconfigure(0, weight=1)
        self._abas.add(aba, text="Interpretação e limites")
        ttk.Label(
            aba,
            text="Leitura responsável dos resultados",
            font=("TkDefaultFont", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))
        ttk.Label(
            aba,
            textvariable=self._interpretacao_var,
            justify="left",
            wraplength=950,
            font=("TkDefaultFont", 10),
        ).grid(row=1, column=0, sticky="nw")
        limites = (
            "Limitações importantes\n\n"
            "• As 80 posições iniciais são ordenadas; (A, B) e (B, A) são simétricas "
            "neste jogo, então há repetição estrutural no protocolo.\n"
            "• Desempenho contra o agente aleatório não demonstra superioridade geral "
            "contra qualquer agente ou estratégia.\n"
            "• O Nim de duas pilhas tem uma estratégia ótima conhecida baseada em XOR; "
            "isso não é uma descoberta inédita deste projeto.\n"
            "• O custo do agente aleatório é N/A, não zero. Médias de nós usam somente "
            "decisões que executaram busca.\n"
            "• Os confrontos são experimentos separados. Os indicadores gerais de "
            "vitórias agregam contextos e não substituem a comparação selecionada.\n"
            "• Os CSVs não contêm uma comparação experimental entre Minimax completo "
            "e Alfa-Beta completo; a aba Algoritmos executa essa comparação para um "
            "estado escolhido.\n"
            "• Intervalos de confiança não são exibidos automaticamente. Taxas de "
            "vitória dependem do protocolo e da amostra observada."
        )
        ttk.Label(
            aba,
            text=limites,
            justify="left",
            wraplength=950,
        ).grid(row=2, column=0, sticky="nw", pady=(20, 0))

    @staticmethod
    def _criar_tabela(
        parent: ttk.Frame,
        colunas: tuple[tuple[str, str, int], ...],
        altura: int = 8,
    ) -> ttk.Treeview:
        recipiente = ttk.Frame(parent)
        recipiente.columnconfigure(0, weight=1)
        recipiente.rowconfigure(0, weight=1)
        tabela = ttk.Treeview(
            recipiente,
            columns=tuple(coluna[0] for coluna in colunas),
            show="headings",
            height=altura,
        )
        for nome, titulo, largura in colunas:
            tabela.heading(nome, text=titulo)
            tabela.column(nome, width=largura, minwidth=45, anchor="center")
        barra = ttk.Scrollbar(recipiente, orient="vertical", command=tabela.yview)
        barra_horizontal = ttk.Scrollbar(
            recipiente, orient="horizontal", command=tabela.xview
        )
        tabela.configure(
            yscrollcommand=barra.set,
            xscrollcommand=barra_horizontal.set,
        )
        tabela.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        barra_horizontal.grid(row=1, column=0, sticky="ew")
        return tabela

    def carregar(self) -> None:
        """Atualiza a tela usando novamente os CSVs existentes."""
        try:
            self._dados = carregar_resultados()
        except (OSError, csv.Error) as erro:
            self._status_var.set(f"Não foi possível carregar os resultados: {erro}")
            self._limpar_tabelas()
            return

        self._jogadas_por_partida = defaultdict(list)
        for jogada in self._dados["jogadas"]:
            self._jogadas_por_partida[jogada["id_partida"]].append(jogada)
        for historico in self._jogadas_por_partida.values():
            historico.sort(key=lambda linha: int(linha["numero_turno"]))

        indicadores = calcular_indicadores_gerais(self._dados)
        for nome, chave in (
            ("Partidas", "partidas"),
            ("Confrontos", "confrontos"),
            ("Jogadas", "jogadas"),
            ("Configurações", "configuracoes"),
            ("Empates", "empates"),
        ):
            self._cartoes[nome].set(f"{indicadores[chave]:,}".replace(",", "."))
        confrontos = sorted({linha["confronto"] for linha in self._dados["resumo"]})
        self._seletor_confronto.configure(values=confrontos)
        if confrontos and self._confronto_var.get() not in confrontos:
            self._confronto_var.set(confrontos[0])
        self._atualizar_resumo()
        self._atualizar_partidas()
        self._atualizar_grafico()
        self._atualizar_interpretacao()
        self._status_var.set(
            f"Fonte: {PASTA_RESULTADOS} · dados carregados dos CSVs originais."
        )

    def _selecionar_confronto(self, _evento=None) -> None:
        self._pagina = 0
        self._atualizar_resumo()
        self._atualizar_partidas()
        self._atualizar_grafico()

    def _atualizar_resumo(self) -> None:
        self._limpar_tabela(self._tabela_resumo)
        confronto = self._confronto_var.get()
        linhas = [
            linha
            for linha in self._dados.get("resumo", [])
            if linha["confronto"] == confronto
        ]
        for indice, linha in enumerate(linhas):
            taxa = _formatar_numero(linha["taxa_vitoria_percentual"], 2)
            media = _formatar_numero(linha["media_nos_por_decisao"], 2)
            self._tabela_resumo.insert(
                "",
                "end",
                iid=f"resumo-{indice}",
                values=(
                    linha["agente"],
                    linha["configuracao_agente"],
                    linha["quantidade_partidas"],
                    linha["vitorias"],
                    linha["derrotas"],
                    linha["empates"],
                    taxa,
                    linha["decisoes_busca"],
                    media,
                    linha["maximo_nos_por_decisao"],
                ),
            )
        acumuladas: dict[str, dict[str, int]] = defaultdict(
            lambda: {"partidas": 0, "vitorias": 0}
        )
        for linha in self._dados["resumo"]:
            item = acumuladas[linha["configuracao_agente"]]
            item["partidas"] += int(linha["quantidade_partidas"])
            item["vitorias"] += int(linha["vitorias"])
        self._limpar_tabela(self._tabela_vitorias)
        for indice, (configuracao, item) in enumerate(
            sorted(acumuladas.items(), key=lambda par: (-par[1]["vitorias"], par[0]))
        ):
            self._tabela_vitorias.insert(
                "",
                "end",
                iid=f"vitoria-{indice}",
                values=(configuracao, item["partidas"], item["vitorias"]),
            )

    def _atualizar_grafico(self, _evento=None) -> None:
        if not self._dados:
            self._grafico.delete("all")
            return
        tipo = self._grafico_var.get()
        if tipo == "Efeito da profundidade":
            stats = obter_estatisticas_profundidade(self._dados["resumo"])
            valores = [(f"d{item['profundidade']}", float(item["media"])) for item in stats]
            subtitulo = "Média ponderada por decisões, nos confrontos do grupo profundidade"
        elif tipo == "Efeito da ordenação":
            stats = obter_estatisticas_ordenacao(self._dados["resumo"])
            valores = [
                (f"d{item['profundidade']} {item['ordenacao']}", float(item["media"]))
                for item in stats
            ]
            subtitulo = "Média de nós por decisão; grupos de ordenação, não taxas de vitória"
        else:
            colunas = {
                "Vitórias": "vitorias",
                "Taxa de vitória (%)": "taxa_vitoria_percentual",
                "Média de nós por decisão": "media_nos_por_decisao",
                "Máximo de nós por decisão": "maximo_nos_por_decisao",
            }
            campo = colunas.get(tipo, "taxa_vitoria_percentual")
            linhas = [
                linha
                for linha in self._dados["resumo"]
                if linha["confronto"] == self._confronto_var.get()
            ]
            valores = [
                (
                    linha["agente"],
                    _para_float(linha.get(campo)),
                )
                for linha in linhas
                if linha.get(campo) not in ("N/A", "")
            ]
            subtitulo = f"{tipo} · somente o confronto selecionado"
        self._desenhar_barras(valores, tipo, subtitulo)

    def _desenhar_barras(
        self,
        valores: list[tuple[str, float]],
        titulo: str,
        subtitulo: str,
    ) -> None:
        canvas = self._grafico
        canvas.delete("all")
        largura = max(canvas.winfo_width(), 760)
        altura = max(canvas.winfo_height(), 230)
        canvas.create_text(
            16, 16, anchor="w", text=titulo, font=("TkDefaultFont", 12, "bold")
        )
        canvas.create_text(
            16, 38, anchor="w", text=subtitulo, fill="#64748b"
        )
        if not valores:
            canvas.create_text(
                largura / 2,
                altura / 2,
                text="Não há decisões de busca aplicáveis para este gráfico.",
                fill="#64748b",
            )
            return
        max_valor = max((valor for _, valor in valores), default=0.0)
        escala = max(max_valor, 1.0)
        margem_esquerda = 190
        fim = largura - 32
        inicio_y = 63
        espacamento = max(28, min(43, (altura - 70) / len(valores)))
        for indice, (rotulo, valor) in enumerate(valores):
            y = inicio_y + indice * espacamento
            comprimento = (fim - margem_esquerda) * max(valor, 0) / escala
            canvas.create_text(
                margem_esquerda - 8,
                y + 9,
                anchor="e",
                text=rotulo[:28],
                font=("TkDefaultFont", 9),
            )
            canvas.create_rectangle(
                margem_esquerda,
                y,
                margem_esquerda + comprimento,
                y + 18,
                fill="#2563eb" if indice % 2 == 0 else "#60a5fa",
                outline="",
            )
            canvas.create_text(
                margem_esquerda + comprimento + 6,
                y + 9,
                anchor="w",
                text=_formatar_numero(str(valor), 2),
                font=("TkDefaultFont", 8),
            )

    def _atualizar_partidas(self) -> None:
        confronto = self._confronto_var.get()
        partidas = [
            linha
            for linha in self._dados.get("partidas", [])
            if linha["confronto"] == confronto
        ]
        termo = self._pesquisa_var.get().strip()
        if termo:
            partidas = [linha for linha in partidas if termo.lower() in linha["id_partida"].lower()]
        self._partidas_filtradas = partidas
        inicio = self._pagina * TAMANHO_PAGINA
        pagina = partidas[inicio : inicio + TAMANHO_PAGINA]
        self._limpar_tabela(self._tabela_partidas)
        for partida in pagina:
            iid = partida["id_partida"]
            self._tabela_partidas.insert(
                "",
                "end",
                iid=iid,
                values=(
                    iid,
                    f"({partida['pilha_a_inicial']}, {partida['pilha_b_inicial']})",
                    partida["jogador_inicial"],
                    f"{partida['vencedor']} · {partida['agente_vencedor']}",
                    partida["quantidade_jogadas"],
                    partida["semente_partida"],
                ),
            )
        total_paginas = max(1, (len(partidas) + TAMANHO_PAGINA - 1) // TAMANHO_PAGINA)
        self._pagina_var.set(
            f"Página {self._pagina + 1} de {total_paginas} · {len(partidas)} partidas neste filtro"
        )
        self._limpar_tabela(self._tabela_jogadas)

    def _pesquisar_partida(self, _evento=None) -> None:
        self._pagina = 0
        self._atualizar_partidas()
        if self._partidas_filtradas:
            self._abas.select(1)

    def _limpar_pesquisa(self) -> None:
        self._pesquisa_var.set("")
        self._pagina = 0
        self._atualizar_partidas()

    def _pagina_anterior(self) -> None:
        if self._pagina > 0:
            self._pagina -= 1
            self._atualizar_partidas()

    def _proxima_pagina(self) -> None:
        if (self._pagina + 1) * TAMANHO_PAGINA < len(self._partidas_filtradas):
            self._pagina += 1
            self._atualizar_partidas()

    def _selecionar_partida(self, _evento=None) -> None:
        selecionada = self._tabela_partidas.selection()
        if not selecionada:
            return
        id_partida = selecionada[0]
        historico = self._jogadas_por_partida.get(id_partida, [])
        self._limpar_tabela(self._tabela_jogadas)
        for indice, jogada in enumerate(historico):
            nos = jogada["nos_visitados"]
            semente = jogada["semente_turno"]
            self._tabela_jogadas.insert(
                "",
                "end",
                iid=f"jogada-{indice}",
                values=(
                    jogada["numero_turno"],
                    jogada["agente"],
                    jogada["jogador"],
                    jogada["estado_anterior"],
                    jogada["jogada"],
                    jogada["estado_posterior"],
                    nos if nos not in ("", "N/A") else "N/A",
                    semente if semente not in ("", "N/A") else "N/A",
                ),
            )

    def _atualizar_interpretacao(self) -> None:
        profundidades = obter_estatisticas_profundidade(self._dados["resumo"])
        ordenacao = obter_estatisticas_ordenacao(self._dados["resumo"])
        linhas = []
        if profundidades:
            menor = min(profundidades, key=lambda item: float(item["media"]))
            maior = max(profundidades, key=lambda item: float(item["media"]))
            linhas.append(
                "Efeito da profundidade: nos dados carregados, a média ponderada variou "
                f"de {float(menor['media']):.2f} nós/decisão em d{menor['profundidade']} "
                f"a {float(maior['media']):.2f} em d{maior['profundidade']}. "
                f"O cálculo considera {menor['decisoes']} e {maior['decisoes']} "
                "decisões, respectivamente, reunidas nos confrontos do grupo."
            )
        if ordenacao:
            pares: dict[int, dict[str, dict]] = defaultdict(dict)
            for item in ordenacao:
                pares[int(item["profundidade"])][str(item["ordenacao"])] = item
            comparaveis = [
                (profundidade, par)
                for profundidade, par in sorted(pares.items())
                if "ligada" in par and "desligada" in par
            ]
            if comparaveis:
                melhorias = sum(
                    float(par["ligada"]["media"]) < float(par["desligada"]["media"])
                    for _, par in comparaveis
                )
                linhas.append(
                    f"Efeito da ordenação: em {melhorias} de {len(comparaveis)} "
                    "profundidades comparáveis, a média de nós observada foi menor "
                    "com ordenação ligada. A tabela e os gráficos mostram as médias "
                    "e quantidades de decisões."
                )
        linhas.append(
            "Vitórias contra o agente aleatório descrevem apenas este adversário e "
            "este protocolo; não demonstram superioridade geral. A seleção de um "
            "confronto mantém cada comparação contextualizada."
        )
        linhas.append(
            "Os CSVs não incluem um confronto entre Minimax completo e Alfa-Beta "
            "completo, então não há comparação experimental agregada entre esses "
            "dois algoritmos. A aba Algoritmos calcula valores e nós para o estado "
            "escolhido na demonstração."
        )
        self._interpretacao_var.set("\n\n".join(linhas))

    def _limpar_tabelas(self) -> None:
        for tabela in (
            self._tabela_resumo,
            self._tabela_vitorias,
            self._tabela_partidas,
            self._tabela_jogadas,
        ):
            self._limpar_tabela(tabela)
        self._grafico.delete("all")

    @staticmethod
    def _limpar_tabela(tabela: ttk.Treeview) -> None:
        tabela.delete(*tabela.get_children())


def _para_float(valor: str | None) -> float:
    if valor in (None, "", "N/A"):
        return 0.0
    return float(valor)


def _formatar_numero(valor: str, casas: int) -> str:
    if valor in ("", "N/A"):
        return "N/A"
    return f"{float(valor):.{casas}f}"


def criar_tela(parent: ttk.Frame) -> TelaResultados:
    """Cria a página alimentada pelos CSVs experimentais."""
    return TelaResultados(parent)
