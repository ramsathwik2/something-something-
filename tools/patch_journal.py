import pathlib, re
p=pathlib.Path(r'D:\KITTY\src\pet_window.py')
t=p.read_text(encoding='utf-8')
# fix dont_sleep menu indices 7->8
t=t.replace('self.menu.entryconfig(7, label="Don\'t sleep 30m', 'self.menu.entryconfig(8, label="Don\'t sleep 30m')
t=t.replace('self.menu.entryconfig(7, label=f"Don\'t sleep', 'self.menu.entryconfig(8, label=f"Don\'t sleep')
# ensure mute is 9
t=t.replace('self.menu.entryconfig(8, label=new_lab)', 'self.menu.entryconfig(9, label=new_lab)')
# add journal init scheduling if not present
if 'def show_journal' not in t:
    # add after _is_dont_sleep definition
    journal_code = '''
    # --- Journal for Gayathree (book, never lost) ---
    def _journal_path(self):
        import sys as _sys, os as _os
        if getattr(_sys, 'frozen', False):
            d=pathlib.Path(_os.getenv("APPDATA", str(pathlib.Path.home()))) / "TaskbarKitten"
        else:
            d=pathlib.Path(__file__).parent.parent / "assets"
        d.mkdir(parents=True, exist_ok=True)
        jp=d / "journal.json"
        # migrate old
        old=pathlib.Path(__file__).parent.parent / "assets" / "journal.json"
        if not jp.exists() and old.exists():
            try: jp.write_text(old.read_text(encoding='utf-8'), encoding='utf-8')
            except: pass
        return jp

    def _load_journal(self):
        import json
        try:
            if self._journal_path().exists():
                return json.loads(self._journal_path().read_text(encoding='utf-8'))
        except: pass
        return {}

    def _save_journal(self, data):
        import json, tempfile, os
        p=self._journal_path()
        try:
            # atomic + backup, never lost
            tmp=p.with_suffix('.tmp')
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            # backup previous
            if p.exists():
                try: (p.with_suffix('.bak')).write_text(p.read_text(encoding='utf-8'), encoding='utf-8')
                except: pass
            tmp.replace(p)
        except:
            try: p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            except: pass

    def show_journal(self):
        import datetime, json
        win=tk.Toplevel(self.root)
        win.title("Gayathree's Journal 📖")
        W,H=740,520
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        win.geometry(f"{W}x{H}+{sw//2-W//2}+{sh//2-H//2}")
        win.configure(bg="#FFF8DC")
        win.attributes("-topmost", True)
        # book shadow + pages
        canvas=tk.Canvas(win, width=W, height=H, bg="#FFF8DC", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        def _rr(x1,y1,x2,y2,r, **kw): pts=[x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]; return canvas.create_polygon(pts, smooth=True, **kw)
        _rr(12,12,W-12,H-12,18, fill="#E6D5B8", outline="")
        _rr(8,8,W-8,H-8,18, fill="#FFFCF5", outline="#C9A86A", width=2)
        # spine
        canvas.create_line(W//2, 24, W//2, H-24, fill="#E6D5B8", width=2, dash=(4,4))
        # header
        tk.Label(win, text="Gayathree's Journal  📖", bg="#FFFCF5", fg="#6B4C3B", font=("Segoe UI", 13, "bold")).place(x=W//2, y=28, anchor="n")
        tk.Label(win, text="Madhu will remind you at 9 PM — every day ♡ (right-click to change later)", bg="#FFFCF5", fg="#8B7355", font=("Segoe UI", 7)).place(x=W//2, y=50, anchor="n")
        # left dates list + right editor
        left=tk.Frame(win, bg="#FFFCF5", bd=1, relief="solid")
        left.place(x=22, y=70, width=200, height=H-110)
        tk.Label(left, text="Days", bg="#FFFCF5", fg="#6B4C3B", font=("Segoe UI", 9, "bold")).pack(pady=6)
        lb=tk.Listbox(left, bg="white", fg="#5a3e2b", font=("Segoe UI", 8), bd=0, highlightthickness=0, activestyle="none", selectbackground="#FFDAB9")
        lb.pack(fill="both", expand=True, padx=6, pady=4)
        right=tk.Frame(win, bg="#FFFCF5", bd=1, relief="solid")
        right.place(x=W//2+10, y=70, width=W//2-32, height=H-110)
        today=datetime.date.today().isoformat()
        date_var=tk.StringVar(value=today)
        tk.Label(right, textvariable=date_var, bg="#FFFCF5", fg="#8B7355", font=("Segoe UI", 8, "italic")).pack(pady=4)
        txt=tk.Text(right, bg="white", fg="#3a2a1a", font=("Segoe UI", 10), wrap="word", bd=0, padx=10, pady=8, undo=True)
        txt.pack(fill="both", expand=True, padx=6, pady=4)
        txt.configure(highlightthickness=1, highlightbackground="#E6D5B8")
        data=self._load_journal()
        def load_date(d):
            date_var.set(d)
            txt.delete("1.0", tk.END)
            txt.insert("1.0", data.get(d, ""))
        # populate dates: include today + existing sorted desc
        dates=sorted(set(list(data.keys()) + [today]), reverse=True)
        for d in dates: lb.insert(tk.END, d)
        # select today
        try:
            idx=dates.index(today)
            lb.selection_set(idx); lb.see(idx)
        except: pass
        load_date(today)
        def on_select(e):
            sel=lb.curselection()
            if sel: load_date(lb.get(sel[0]))
        lb.bind("<<ListboxSelect>>", on_select)
        def save():
            d=date_var.get()
            data[d]=txt.get("1.0", tk.END).rstrip()
            self._save_journal(data)
            self._show_bubble(f"Journal saved for {d} ♡", 2800)
        btn=tk.Button(right, text="💾 Save today's page", command=save, bg="#FF8FA3", fg="white", activebackground="#FFA0B5", font=("Segoe UI", 9, "bold"), bd=0, padx=14, pady=6, cursor="hand2")
        btn.pack(pady=6)
        # autosave on close
        def on_close():
            try: save()
            except: pass
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)
        txt.focus_set()

    def check_journal_reminder(self):
        try:
            import datetime
            now=datetime.datetime.now()
            hour=self.memory.get("journal_hour",21)
            minute=self.memory.get("journal_min",0)
            # changeable later via menu, default 21:00
            if now.hour==hour and now.minute==minute and now.second<25:
                today=now.date().isoformat()
                slot=f"{today}_{hour}_{minute}"
                if getattr(self, '_last_journal_slot', None) != slot:
                    self._last_journal_slot=slot
                    # check if already journaled today
                    data=self._load_journal()
                    if not data.get(today, "").strip():
                        self._show_bubble("9 PM — time to journal, Gayathree? 📖", 7000)
                        print("journal reminder 9pm")
                    else:
                        self._show_bubble("Journal done today — proud of you ♡", 4000)
                    # gentle chirp if not muted
                    self._play_meow("chirp")
        except: pass
        self.root.after(25000, self.check_journal_reminder)
'''
    t=t.replace('    def _is_dont_sleep(self):', journal_code + '\n    def _is_dont_sleep(self):')
    # schedule reminder in __init__
    if 'self.root.after(10000, self.wish_11_check)' in t:
        t=t.replace('self.root.after(10000, self.wish_11_check)', 'self.root.after(10000, self.wish_11_check)\n        self.root.after(15000, self.check_journal_reminder)')
    # also need _last_journal_slot init
    t=t.replace('self._last_wish_slot=None', 'self._last_wish_slot=None\n        self._last_journal_slot=None')
    p.write_text(t, encoding='utf-8')
    print('patched journal')
else:
    print('already has journal')
