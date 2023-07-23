import tkinter as tk
from tkinter import BOTH
import sv_ttk

from main_frame import MainFrame

win = tk.Tk()

win.title("SVG Toolkit")
win.geometry("800x600")

MainFrame(win).pack(fill=BOTH)

sv_ttk.set_theme("dark")

win.mainloop()