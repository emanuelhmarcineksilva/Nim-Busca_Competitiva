"""Componentes compartilhados pelas páginas do aplicativo."""

import tkinter as tk
from tkinter import ttk


class PaginaRolavel(ttk.Frame):
    """Viewport vertical para uma página inteira, com roda do mouse."""

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(
            self,
            background="#f1f5f9",
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.rolagem = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.rolagem.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.rolagem.set)
        self.conteudo = ttk.Frame(self.canvas, style="Conteudo.TFrame")
        self._janela = self.canvas.create_window(
            (0, 0), window=self.conteudo, anchor="nw"
        )
        self.conteudo.bind("<Configure>", self._atualizar_regiao)
        self.canvas.bind("<Configure>", self._ajustar_largura)
        self._wheel_tag = f"PaginaRolavel_{id(self)}"
        self.bind_class(self._wheel_tag, "<MouseWheel>", self._rolar_roda)
        self.bind_class(self._wheel_tag, "<Button-4>", self._rolar_linux)
        self.bind_class(self._wheel_tag, "<Button-5>", self._rolar_linux)
        self.bind("<Destroy>", self._remover_bindings, add="+")

    def _atualizar_regiao(self, _evento=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._aplicar_bindtag(self.conteudo)

    def _aplicar_bindtag(self, widget: tk.Misc) -> None:
        bindtags = widget.bindtags()
        if self._wheel_tag not in bindtags:
            widget.bindtags((bindtags[0], self._wheel_tag, *bindtags[1:]))
        for filho in widget.winfo_children():
            self._aplicar_bindtag(filho)

    def _ajustar_largura(self, evento: tk.Event) -> None:
        self.canvas.itemconfigure(self._janela, width=evento.width)

    def _evento_dentro_da_pagina(self, evento: tk.Event) -> bool:
        widget = self.winfo_containing(evento.x_root, evento.y_root)
        while widget is not None:
            if widget == self.conteudo:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _rolar_roda(self, evento: tk.Event) -> str | None:
        if not self._evento_dentro_da_pagina(evento):
            return None
        if evento.delta:
            unidades = -1 if evento.delta > 0 else 1
            return self._rolar_widget_interno(evento, unidades)
        return None

    def _rolar_linux(self, evento: tk.Event) -> str | None:
        if not self._evento_dentro_da_pagina(evento):
            return None
        return self._rolar_widget_interno(evento, -1 if evento.num == 4 else 1)

    def _rolar_widget_interno(self, evento: tk.Event, unidades: int) -> str:
        widget = self.winfo_containing(evento.x_root, evento.y_root)
        while widget is not None and widget != self.conteudo:
            if isinstance(widget, (tk.Canvas, tk.Listbox, tk.Text, ttk.Treeview)):
                inicio, fim = widget.yview()
                pode_rolar = fim < 1 if unidades > 0 else inicio > 0
                if pode_rolar:
                    widget.yview_scroll(unidades, "units")
                    return "break"
            widget = getattr(widget, "master", None)
        self.canvas.yview_scroll(unidades, "units")
        return "break"

    def _remover_bindings(self, evento: tk.Event) -> None:
        if evento.widget != self:
            return
        for sequencia in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.unbind_class(self._wheel_tag, sequencia)


def criar_pagina(
    parent: ttk.Frame,
    titulo: str,
    resumo: str,
    origem: str,
) -> ttk.Frame:
    """Cria o layout-base de uma página ainda sem funcionalidades."""
    pagina = ttk.Frame(parent, style="Conteudo.TFrame", padding=(40, 36))
    pagina.columnconfigure(0, weight=1)

    ttk.Label(
        pagina,
        text="NIM LAB  /  TDE2",
        background="#f1f5f9",
        foreground="#2563eb",
        font=("TkDefaultFont", 10, "bold"),
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(
        pagina,
        text=titulo,
        background="#f1f5f9",
        foreground="#0f172a",
        font=("TkDefaultFont", 24, "bold"),
    ).grid(row=1, column=0, sticky="w", pady=(10, 8))
    ttk.Label(
        pagina,
        text=resumo,
        background="#f1f5f9",
        foreground="#475569",
        font=("TkDefaultFont", 11),
        wraplength=760,
        justify="left",
    ).grid(row=2, column=0, sticky="w")

    cartao = ttk.Frame(pagina, padding=24, relief="solid", borderwidth=1)
    cartao.grid(row=3, column=0, sticky="new", pady=(32, 0))
    cartao.columnconfigure(0, weight=1)
    ttk.Label(
        cartao,
        text="Estrutura pronta para a próxima etapa",
        font=("TkDefaultFont", 13, "bold"),
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(
        cartao,
        text=(
            "Esta página ainda não executa ações nem apresenta resultados. "
            "A integração usará os módulos existentes, sem duplicar regras "
            "ou algoritmos."
        ),
        wraplength=700,
        justify="left",
    ).grid(row=1, column=0, sticky="w", pady=(10, 16))
    ttk.Separator(cartao).grid(row=2, column=0, sticky="ew", pady=(0, 12))
    ttk.Label(
        cartao,
        text=f"Origem prevista: {origem}",
        foreground="#475569",
    ).grid(row=3, column=0, sticky="w")

    return pagina
