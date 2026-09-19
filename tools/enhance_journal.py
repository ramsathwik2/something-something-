import pathlib
p=pathlib.Path(r'D:\KITTY\src\pet_window.py')
t=p.read_text(encoding='utf-8')
old = '''    def show_journal(self):
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
        txt.focus_set()'''

new = '''    def show_journal(self):
        import datetime, json
        win=tk.Toplevel(self.root)
        win.title("Gayathree\\'s Journal 📖 — Madhu's Keepsake")
        W,H=820,560
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        win.geometry(f"{W}x{H}+{sw//2-W//2}+{sh//2-H//2}")
        win.configure(bg="#FDF6E3")
        win.attributes("-topmost", True)
        # book canvas with warm parchment + soft shadow + linen texture dots
        canvas=tk.Canvas(win, width=W, height=H, bg="#FDF6E3", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        def _rr(x1,y1,x2,y2,r, **kw): pts=[x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]; return canvas.create_polygon(pts, smooth=True, **kw)
        # layered shadow for depth
        _rr(18,18,W-12,H-12,22, fill="#E8DCC8", outline="")
        _rr(14,14,W-14,H-14,20, fill="#E6D5B8", outline="")
        _rr(8,8,W-8,H-8,20, fill="#FFFCF7", outline="#C9A86A", width=2)
        # central spine + stitches
        canvas.create_line(W//2, 28, W//2, H-28, fill="#D8C4A6", width=3)
        for y in range(40, H-40, 18): canvas.create_oval(W//2-1.5, y-1.5, W//2+1.5, y+1.5, fill="#C9A86A", outline="")
        # Madhu paw peek top-right
        try:
            from PIL import Image as _PILImage, ImageTk as _PILTK
            import pathlib as _pl
            pth=_pl.Path(__file__).parent.parent / "assets" / "sprites" / "frame_4.png"
            im=_PILImage.open(pth).convert("RGBA").resize((44,44), _PILImage.LANCZOS)
            tkp=_PILTK.PhotoImage(im)
            win._paw=tkp
            canvas.create_image(W-48, 36, image=tkp)
        except: canvas.create_text(W-48, 36, text="🐾", font=("Segoe UI", 18))
        # header with divider flourishes
        tk.Label(win, text="Gayathree \\'s Journal", bg="#FFFCF7", fg="#6B4C3B", font=("Georgia", 16, "bold")).place(x=W//2, y=22, anchor="n")
        tk.Label(win, text="— a little book Madhu keeps for you —", bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 8, "italic")).place(x=W//2, y=44, anchor="n")
        canvas.create_line(W//2-90, 62, W//2+90, 62, fill="#E6D5B8", width=1)
        canvas.create_text(W//2, 62, text=" ✦ ", fill="#C9A86A", font=("Segoe UI", 7))
        # left page — calendar & streak
        left=tk.Frame(win, bg="#FFFCF7", bd=0)
        left.place(x=22, y=72, width=240, height=H-108)
        tk.Label(left, text="📅  Days with Madhu", bg="#FFFCF7", fg="#6B4C3B", font=("Segoe UI", 9, "bold")).pack(pady=(6,2))
        # streak
        data=self._load_journal()
        filled=len([v for v in data.values() if v.strip()])
        streak=self._journal_streak(data)
        tk.Label(left, text=f"{filled} pages  •  {streak} day streak 🔥", bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 7)).pack()
        lb_frame=tk.Frame(left, bg="#FFFCF7")
        lb_frame.pack(fill="both", expand=True, padx=8, pady=8)
        # subtle paper lines behind list
        lb=tk.Listbox(lb_frame, bg="white", fg="#5a3e2b", font=("Segoe UI", 9), bd=1, relief="solid", highlightthickness=0, activestyle="none", selectbackground="#FFDAB9", selectforeground="#5a3e2b")
        lb.pack(fill="both", expand=True, ipady=4)
        # right page — writing paper with lines
        right=tk.Frame(win, bg="#FFFCF7", bd=1, relief="solid")
        right.place(x=W//2+14, y=72, width=W//2-36, height=H-108)
        today=datetime.date.today().isoformat()
        pretty_today=datetime.datetime.now().strftime("%A, %B %d  —  %Y")
        hdr=tk.Frame(right, bg="#FFFCF7")
        hdr.pack(fill="x", padx=10, pady=(8,2))
        tk.Label(hdr, text=pretty_today, bg="#FFFCF7", fg="#8B7355", font=("Georgia", 9, "italic")).pack(side="left")
        wc_var=tk.StringVar(value="0 words")
        tk.Label(hdr, textvariable=wc_var, bg="#FFFCF7", fg="#C9A86A", font=("Segoe UI", 7)).pack(side="right")
        # paper lines
        paper=tk.Frame(right, bg="white")
        paper.pack(fill="both", expand=True, padx=8, pady=4)
        # canvas for lines behind text
        line_canvas=tk.Canvas(paper, bg="white", highlightthickness=0, bd=0, height=1)
        line_canvas.pack(fill="x")
        # text with paper color and subtle lines via spacing
        txt=tk.Text(paper, bg="white", fg="#3a2a1a", font=("Segoe UI", 11), wrap="word", bd=0, padx=12, pady=10, undo=True, spacing1=4, spacing3=8, insertbackground="#8B4513")
        txt.pack(fill="both", expand=True)
        txt.configure(highlightthickness=1, highlightbackground="#E6D5B8")
        # subtle horizontal rules overlay (via canvas lines behind text is complex, so add tag)
        def update_wc(e=None): 
            words=len(txt.get("1.0", tk.END).split())
            wc_var.set(f"{words} words")
        txt.bind("<KeyRelease>", update_wc)
        date_var=tk.StringVar(value=today)
        # hidden date var for save
        data=self._load_journal()
        def load_date(d):
            date_var.set(d)
            txt.delete("1.0", tk.END)
            txt.insert("1.0", data.get(d, ""))
            update_wc()
            # pretty header per date
            try:
                dt=datetime.datetime.fromisoformat(d)
                pretty=dt.strftime("%A, %B %d  —  %Y")
                # find header label and update
                for w in hdr.winfo_children():
                    if isinstance(w, tk.Label) and "20" in w.cget("text") or "," in w.cget("text"):
                        w.configure(text=pretty)
                        break
            except: pass
        dates=sorted(set(list(data.keys()) + [today]), reverse=True)
        for d in dates:
            mark=" ●" if data.get(d, "").strip() else " ○"
            lb.insert(tk.END, d + mark)
        try:
            idx=dates.index(today)
            lb.selection_set(idx); lb.see(idx)
        except: pass
        load_date(today)
        def on_select(e):
            sel=lb.curselection()
            if sel:
                raw=lb.get(sel[0])
                d=raw.split(" ")[0]
                load_date(d)
        lb.bind("<<ListboxSelect>>", on_select)
        def save():
            d=date_var.get()
            data[d]=txt.get("1.0", tk.END).rstrip()
            # also update list mark
            sel=lb.curselection()
            if sel:
                raw=lb.get(sel[0]); base=raw.split(" ")[0]
                if base==d:
                    mark=" ●" if data[d].strip() else " ○"
                    lb.delete(sel[0]); lb.insert(sel[0], d+mark); lb.selection_set(sel[0])
            # if new date not in list, add
            if d not in dates:
                lb.insert(0, d + (" ●" if data[d].strip() else " ○"))
            self._save_journal(data)
            self._show_bubble(f"Journal saved for {d} ♡", 2800)
            # tiny ink save shimmer
            try:
                btn.configure(bg="#C9A86A")
                win.after(180, lambda: btn.configure(bg="#FF8FA3"))
            except: pass
        btn=tk.Button(right, text="💾  Save this page  — Madhu will keep it forever", command=save, bg="#FF8FA3", fg="white", activebackground="#FFA0B5", font=("Segoe UI", 9, "bold"), bd=0, padx=14, pady=7, cursor="hand2")
        btn.pack(pady=8)
        # also add time changer link
        def change_time():
            import tkinter.simpledialog as sd
            cur=f"{self.memory.get('journal_hour',21):02d}:{self.memory.get('journal_min',0):02d}"
            ans=sd.askstring("Journal reminder", "Remind daily at (HH:MM 24h):", initialvalue=cur, parent=win)
            if ans:
                try:
                    h,m=map(int, ans.strip().split(":"))
                    if 0<=h<24 and 0<=m<60:
                        self.memory["journal_hour"]=h; self.memory["journal_min"]=m
                        import memory as mem; mem.save(self.memory)
                        self._show_bubble(f"Reminder set to {h:02d}:{m:02d} ♡", 3000)
                except: pass
        tk.Label(right, text="⏰  change reminder time", bg="#FFFCF7", fg="#C49A6C", font=("Segoe UI", 7, "underline"), cursor="hand2").pack()
        # bind label click
        for w in right.winfo_children():
            if isinstance(w, tk.Label) and "change reminder" in w.cget("text"):
                w.bind("<Button-1>", lambda e: change_time())
        def on_close():
            try: save()
            except: pass
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)
        txt.focus_set()
        update_wc()'''
if old in t:
    t=t.replace(old, new)
    p.write_text(t, encoding='utf-8')
    print('enhanced journal')
else:
    print('old not found')
