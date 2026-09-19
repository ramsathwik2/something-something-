import sys, pathlib, time, datetime
sys.path.insert(0,'src')
import tkinter as tk
from pet_window import PetWindow
# quick test without full app loop
root=tk.Tk()
root.withdraw()
pw=PetWindow.__new__(PetWindow)
# minimal init for journal
import memory as mem
pw.memory=mem.load()
pw.root=tk.Tk()
pw.root.withdraw()
# need to init required attrs for journal
import pathlib as pl
pw._journal_path = lambda: pl.Path(__file__).parent.parent / "assets" / "journal_test.json"
# monkey patch to avoid real file
orig_load = pw._load_journal if hasattr(pw, '_load_journal') else None
# just test Text creation like in show_journal
win=tk.Toplevel(pw.root)
win.geometry("740x520")
win.configure(bg="#FDF6E3")
# create Text like in journal
paper=tk.Frame(win, bg="white")
paper.pack(fill="both", expand=True, padx=20, pady=20)
txt=tk.Text(paper, bg="white", fg="#3a2a1a", font=("Segoe UI", 11), wrap="word", bd=0, padx=12, pady=10, undo=True, state="normal", takefocus=1)
txt.pack(fill="both", expand=True)
txt.insert("1.0", "test")
txt.focus_set()
win.update()
print("state", txt.cget("state"))
print("editable test insert", end=" ")
try:
    txt.insert(tk.END, " hello")
    print("ok", repr(txt.get("1.0", tk.END)))
except Exception as e:
    print("fail", e)
# check if we can type via event_generate
try:
    txt.event_generate("<KeyPress>", keysym="a")
    print("key event ok")
except Exception as e:
    print("key event fail", e)
win.destroy()
pw.root.destroy()
root.destroy()
print("done")
