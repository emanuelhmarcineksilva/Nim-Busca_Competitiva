"""Inicialização e navegação do aplicativo Nim Lab."""

import tkinter as tk
from tkinter import ttk

from telas import algoritmos, experimentos, guia, partida, resultados
from telas.comum import PaginaRolavel


NAVEGACAO = (
    ("partida", "Partida", "Executar e acompanhar uma partida"),
    ("algoritmos", "Algoritmos", "Explorar os algoritmos de busca"),
    ("experimentos", "Experimentos", "Configurar os confrontos"),
    ("resultados", "Resultados", "Consultar os CSVs reais"),
    ("guia", "Guia do trabalho", "Revisar conceitos e metodologia"),
)

TELAS = {
    "partida": partida.criar_tela,
    "algoritmos": algoritmos.criar_tela,
    "experimentos": experimentos.criar_tela,
    "resultados": resultados.criar_tela,
    "guia": guia.criar_tela,
}


class NimLab(tk.Tk):
    """Janela principal, responsável somente pelo layout e pela navegação."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Nim Lab — Busca Competitiva")
        self.geometry("1180x760")
        self.minsize(760, 500)
        self._botoes: dict[str, ttk.Button] = {}
        self._telas: dict[str, ttk.Frame] = {}
        self._paginas_rolaveis: dict[str, PaginaRolavel] = {}
        self._configurar_estilos()
        self._construir_layout()
        self.mostrar_tela("partida")

    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")

        estilo.configure("Sidebar.TFrame", background="#172554")
        estilo.configure(
            "Marca.TLabel",
            background="#172554",
            foreground="#ffffff",
            font=("TkDefaultFont", 18, "bold"),
        )
        estilo.configure(
            "Submarca.TLabel",
            background="#172554",
            foreground="#bfdbfe",
            font=("TkDefaultFont", 10),
        )
        estilo.configure(
            "Nav.TButton",
            background="#172554",
            foreground="#e2e8f0",
            anchor="w",
            padding=(16, 12),
            borderwidth=0,
            font=("TkDefaultFont", 10),
        )
        estilo.map(
            "Nav.TButton",
            background=[
                ("active", "#1e3a8a"),
                ("!active", "#172554"),
            ],
            foreground=[("active", "#ffffff")],
        )
        estilo.configure(
            "NavAtiva.TButton",
            background="#1e40af",
            foreground="#ffffff",
            anchor="w",
            padding=(16, 12),
            borderwidth=0,
            font=("TkDefaultFont", 10, "bold"),
        )
        estilo.configure("Conteudo.TFrame", background="#f1f5f9")
        estilo.configure(
            "Rodape.TLabel",
            background="#f1f5f9",
            foreground="#64748b",
            padding=(24, 10),
        )

    def _construir_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        layout = ttk.Frame(self)
        layout.grid(row=0, column=0, sticky="nsew")
        layout.columnconfigure(1, weight=1)
        layout.rowconfigure(0, weight=1)

        menu = ttk.Frame(layout, style="Sidebar.TFrame", width=250, padding=(12, 24))
        menu.grid(row=0, column=0, sticky="ns")
        menu.grid_propagate(False)

        ttk.Label(menu, text="NIM LAB", style="Marca.TLabel").pack(
            anchor="w", padx=12
        )
        ttk.Label(
            menu,
            text="TDE2 · Busca Competitiva",
            style="Submarca.TLabel",
        ).pack(anchor="w", padx=12, pady=(4, 28))

        for identificador, titulo, descricao in NAVEGACAO:
            botao = ttk.Button(
                menu,
                text=f"{titulo}\n{descricao}",
                style="Nav.TButton",
                command=lambda chave=identificador: self.mostrar_tela(chave),
            )
            botao.pack(fill="x", pady=3)
            self._botoes[identificador] = botao

        area = ttk.Frame(layout, style="Conteudo.TFrame")
        area.grid(row=0, column=1, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)

        paginas = ttk.Frame(area, style="Conteudo.TFrame")
        paginas.grid(row=0, column=0, sticky="nsew")
        paginas.columnconfigure(0, weight=1)
        paginas.rowconfigure(0, weight=1)

        for identificador, _, _ in NAVEGACAO:
            pagina = PaginaRolavel(paginas)
            pagina.grid(row=0, column=0, sticky="nsew")
            pagina.conteudo.columnconfigure(0, weight=1)
            tela = TELAS[identificador](pagina.conteudo)
            tela.grid(row=0, column=0, sticky="nsew")
            self._telas[identificador] = tela
            self._paginas_rolaveis[identificador] = pagina

        self._status = ttk.Label(
            area,
            text="Nim Lab · interface didática para o TDE2.",
            style="Rodape.TLabel",
            anchor="w",
        )
        self._status.grid(row=1, column=0, sticky="ew")

    def mostrar_tela(self, identificador: str) -> None:
        """Traz a tela selecionada para frente e atualiza o item ativo."""
        if identificador not in self._telas:
            raise ValueError(f"Tela desconhecida: {identificador}")

        self._paginas_rolaveis[identificador].tkraise()
        for chave, botao in self._botoes.items():
            botao.configure(
                style="NavAtiva.TButton" if chave == identificador else "Nav.TButton"
            )

        titulo = next(
            titulo for chave, titulo, _ in NAVEGACAO if chave == identificador
        )
        descricao = next(
            descricao
            for chave, _, descricao in NAVEGACAO
            if chave == identificador
        )
        self._status.configure(text=f"{titulo}  ·  {descricao}")


def iniciar() -> None:
    """Cria a janela principal e inicia o loop de eventos do Tk."""
    aplicativo = NimLab()
    aplicativo.mainloop()


if __name__ == "__main__":
    iniciar()
