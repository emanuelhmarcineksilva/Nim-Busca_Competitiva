import tkinter as tk
import unittest
from types import SimpleNamespace
from tkinter import ttk

from telas.comum import PaginaRolavel


class TesteRolagemInterface(unittest.TestCase):
    def setUp(self):
        try:
            self.janela = tk.Tk()
            self.janela.geometry("420x280")
        except tk.TclError as erro:
            self.skipTest(f"Tk não está disponível: {erro}")
        self.pagina = PaginaRolavel(self.janela)
        self.pagina.pack(fill="both", expand=True)
        self.janela.update()

    def tearDown(self):
        self.janela.destroy()

    def _evento_no_widget(self, widget, delta=-120):
        return SimpleNamespace(
            delta=delta,
            num=5 if delta < 0 else 4,
            x_root=widget.winfo_rootx() + 5,
            y_root=widget.winfo_rooty() + 5,
        )

    def test_barra_e_roda_do_mouse_percorrem_conteudo_alto(self):
        for numero in range(40):
            ttk.Label(self.pagina.conteudo, text=f"Linha {numero}").pack(anchor="w")
        self.janela.update()

        regiao = self.pagina.canvas.bbox("all")
        self.assertGreater(regiao[3], self.pagina.canvas.winfo_height())

        self.pagina.canvas.yview_moveto(0)
        evento = self._evento_no_widget(self.pagina.conteudo.winfo_children()[0])
        self.assertEqual(self.pagina._rolar_roda(evento), "break")
        self.assertGreater(self.pagina.canvas.yview()[0], 0)

        self.pagina.canvas.yview_moveto(0)
        self.pagina.rolagem.event_generate(
            "<Button-1>",
            x=5,
            y=self.pagina.rolagem.winfo_height() - 4,
        )
        self.pagina.rolagem.event_generate(
            "<ButtonRelease-1>",
            x=5,
            y=self.pagina.rolagem.winfo_height() - 4,
        )
        self.janela.update()
        self.assertGreater(self.pagina.canvas.yview()[0], 0)

    def test_roda_prioriza_texto_interno_e_nao_roda_fora_da_pagina(self):
        texto = tk.Text(self.pagina.conteudo, height=3)
        texto.pack(fill="x")
        texto.insert("1.0", "\n".join(f"Texto {i}" for i in range(40)))
        for numero in range(30):
            ttk.Label(self.pagina.conteudo, text=f"Conteúdo {numero}").pack(anchor="w")
        self.janela.update()

        antes_pagina = self.pagina.canvas.yview()
        antes_texto = texto.yview()
        self.assertEqual(
            self.pagina._rolar_roda(self._evento_no_widget(texto)),
            "break",
        )
        self.assertEqual(self.pagina.canvas.yview(), antes_pagina)
        self.assertGreater(texto.yview()[0], antes_texto[0])

        evento_fora = SimpleNamespace(
            delta=-120,
            num=5,
            x_root=self.janela.winfo_rootx() + self.janela.winfo_width() - 2,
            y_root=self.janela.winfo_rooty() + 5,
        )
        self.assertIsNone(self.pagina._rolar_roda(evento_fora))

    def test_bindings_sao_removidos_sem_erros_ao_fechar(self):
        erros = []
        self.janela.report_callback_exception = lambda *args: erros.append(args)
        self.pagina.destroy()
        self.janela.update()
        self.assertEqual(erros, [])


if __name__ == "__main__":
    unittest.main()
