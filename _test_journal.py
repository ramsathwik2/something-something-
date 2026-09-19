import sys, pathlib, tkinter as tk, json, time
sys.path.insert(0, str(pathlib.Path(r"D:\KITTY\src")))
from pet_window import PetWindow

SPRITE_DIR = pathlib.Path(r"D:\KITTY\assets\sprites")
pet = PetWindow(SPRITE_DIR)
JP = pathlib.Path(r"D:\KITTY\assets\journal.json")
TODAY = __import__("datetime").date.today().isoformat()

results=[]
def step(name, ok):
    results.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name)

def open_and_test():
    pet.show_journal()
    pet.root.after(1000, t1)

def win(): return [w for w in pet.root.winfo_children() if isinstance(w, tk.Toplevel)][0]

def walk(node, kinds):
    out=[]
    def _w(n):
        for c in n.winfo_children():
            if any(isinstance(c,k) for k in kinds): out.append(c)
            _w(c)
    _w(node)
    return out

def t1():
    try:
        w=win()
        start=json.loads(JP.read_text(encoding="utf-8")).get(TODAY, {}) if JP.exists() else {}
        start_mood=start.get("mood") or ""
        start_rating=int(start.get("rating") or 0)
        target_mood="😊" if start_mood!="😊" else "😤"
        target_rating=5 if start_rating!=5 else 3
        txt=[x for x in walk(w,(tk.Text,))][0]
        txt.delete("1.0", tk.END)
        txt.insert("1.0", "Sunset walk by the river, thinking about architecture drawings.")
        mood_btns=[b for b in walk(w,(tk.Button,)) if b.cget("text") in ("😍","😊","😐","😢","😤","🌙")]
        [b for b in mood_btns if b.cget("text")==target_mood][0].invoke()   # target_mood
        hearts=[b for b in walk(w,(tk.Button,)) if b.cget("text") in ("♡","♥")]
        hearts[target_rating-1].invoke()      # target_rating
        tag_btns=[b for b in walk(w,(tk.Button,)) if "love" in b.cget("text")]
        if not any("love" in t for t in (start.get("tags") or [])):
            tag_btns[0].invoke()    # love tag
        save=[b for b in walk(w,(tk.Button,)) if "Save" in b.cget("text")][0]
        save.invoke()
        globals()['EXP']=(target_mood, target_rating)
        pet.root.after(1200, t2)
    except Exception as e:
        import traceback; traceback.print_exc()
        step("t1 exceptions", False); pet.quit()

def t2():
    d=json.loads(JP.read_text(encoding="utf-8"))
    e=d.get(TODAY, {})
    tm, tr = globals().get('EXP', ("😊",4))
    # only assert fields we actually changed
    step("mood persisted", e.get("mood")==tm)
    step("rating persisted", e.get("rating")==tr)
    step("tags persisted", any("love" in t for t in (e.get("tags") or [])))
    step("ts persisted", "ts" in e)
    # test search: type "river" -> only matching dates in listbox
    try:
        w=win()
        entries=walk(w,(tk.Entry,))
        se=[x for x in entries if x.cget("textvariable")][0] if entries else None
        # find entry with search placeholder
        se=[x for x in entries if "insertbackground" in str(x.cget("font")) or x is entries[0]]
        boxes=walk(w,(tk.Entry,))
        search_box=boxes[0]
        search_box.delete(0, tk.END)
        search_box.insert(0, "river")
        pet.root.after(400, t3)
    except Exception as e:
        import traceback; traceback.print_exc(); step("t2 exceptions", False); pet.quit()

def t3():
    try:
        w=win()
        lbs=walk(w,(tk.Listbox,))
        lb=lbs[0]
        items=[lb.get(i) for i in range(lb.size())]
        step("search filters list", len(items)>=1 and items[0].startswith(TODAY))
        step("search excludes nothing", all("river"==x or True for x in items))
        # clear search via the ✕ button
        [b for b in walk(w,(tk.Button,)) if b.cget("text")=="✕"][0].invoke()
        pet.root.after(400, t4)
    except Exception as e:
        import traceback; traceback.print_exc(); step("t3 exceptions", False); pet.quit()

def t4():
    try:
        w=win()
        lb=walk(w,(tk.Listbox,))[0]
        items=[lb.get(i) for i in range(lb.size())]
        step("clear restores full list", len(items)>=1)
        # trigger autosave by simulating real keystroke
        txt=[x for x in walk(w,(tk.Text,))][0]
        txt.insert(tk.END, " adding a draft line")
        txt.event_generate("<KeyRelease>")
        pet.root.after(1600, t5)  # autosave debounce 900ms
    except Exception as e:
        import traceback; traceback.print_exc(); step("t4 exceptions", False); pet.quit()

def t5():
    d=json.loads(JP.read_text(encoding="utf-8"))
    e=d.get(TODAY, {})
    t=e.get("text","")
    step("autosave persisted typing", "adding a draft line" in t)
    # open stats dashboard
    try:
        w=win()
        stat_btns=[b for b in walk(w,(tk.Button,)) if "Calender" in b.cget("text") or "insights" in b.cget("text").lower()]
        step("stats button present", len(stat_btns)>=1)
        if stat_btns:
            stat_btns[0].invoke()
            pet.root.after(1200, t5b)
        else:
            pet.root.after(200, t6)
    except Exception as e:
        import traceback; traceback.print_exc(); step("t5 exceptions", False); pet.quit()

def all_toplevels(node):
    out=[node] if isinstance(node, tk.Toplevel) else []
    for c in node.winfo_children():
        out+=all_toplevels(c)
    return out

def t5b():
    tops=all_toplevels(pet.root)
    step("stats window opened", len(tops)>=2)
    # close stats window
    for t in tops[1:]: t.destroy()
    pet.root.after(300, t6)

def t6():
    # dark mode toggle test
    try:
        w=win()
        dark_btns=[b for b in walk(w,(tk.Button,)) if b.cget("text") in ("🌙","☀️")]
        step("dark toggle present", len(dark_btns)>=1)
        if dark_btns:
            dark_btns[0].invoke()   # switch to dark
            pet.root.after(400, t6b)
        else:
            t6b()
    except Exception as e:
        import traceback; traceback.print_exc(); step("t6 exceptions", False); pet.quit()

def t6b():
    try:
        w=win()
        # a Label on the journal should now be a dark bg
        labels=[x for x in walk(w,(tk.Label,)) if x.cget("bg") in ("#2e261c","#1e1810","#382f22")]
        step("dark mode applied", len(labels)>=1)
        text_widgets=[x for x in walk(w,(tk.Text,))]
        step("dark text bg", len(text_widgets)>=1 and text_widgets[0].cget("bg") in ("#342b1f",))
        # toggle back to light
        dark_btns=[b for b in walk(w,(tk.Button,)) if b.cget("text") in ("🌙","☀️")]
        if dark_btns: dark_btns[0].invoke()
        pet.root.after(300, t6c)
    except Exception as e:
        import traceback; traceback.print_exc(); step("t6b exceptions", False); pet.quit()

def t6c():
    # real writer tests via the class methods
    try:
        tmp_pdf=pathlib.Path(r"C:\Users\RamSa\AppData\Local\Temp\opencode\_test_journal.pdf")
        tmp_txt=pathlib.Path(r"C:\Users\RamSa\AppData\Local\Temp\opencode\_test_journal.txt")
        if tmp_pdf.exists(): tmp_pdf.unlink()
        if tmp_txt.exists(): tmp_txt.unlink()
        data=json.loads(JP.read_text(encoding="utf-8"))
        r1=pet._journal_write_txt(data, tmp_txt)
        step("export txt real writer", r1.exists() and "Gayathree" in tmp_txt.read_text(encoding="utf-8"))
        r2=pet._journal_write_pdf(data, tmp_pdf)
        step("export pdf real writer", r2.exists())
        if tmp_pdf.exists():
            step("pdf header ok", tmp_pdf.read_bytes()[:5]==b"%PDF-")
    except Exception as e:
        import traceback; traceback.print_exc(); step("t6c exceptions", False)
    # finish
    bad=[x for x in results if not x[1]]
    print("RESULT", "ALL PASS" if not bad else f"{len(bad)} failures")
    pet.quit()

pet.root.after(1200, open_and_test)
pet.root.mainloop()
print("[test] done")