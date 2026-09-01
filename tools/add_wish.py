import pathlib
p=pathlib.Path(r'D:\KITTY\src\pet_window.py')
t=p.read_text(encoding='utf-8')
if 'def wish_11_check' not in t:
    insert = '''
    def wish_11_check(self):
        try:
            now=__import__('datetime').datetime.now()
            if (now.hour==11 or now.hour==23) and now.minute==11:
                slot=f"{now.date()}_{now.hour}"
                if self._last_wish_slot != slot:
                    self._last_wish_slot=slot
                    ampm="AM" if now.hour==11 else "PM"
                    self._show_bubble(f"11:11 {ampm} -- make a wish", 7000)
                    self._play_meow("chirp")
                    print(f"11:11 wish {ampm}")
        except: pass
        self.root.after(20000, self.wish_11_check)

'''
    t=t.replace('    def waiting_check(self):', insert+'    def waiting_check(self):')
    # also ensure scheduling
    if 'self.root.after(10000, self.wish_11_check)' not in t:
        t=t.replace('self.root.after(8000, self._check_long_absence)', 'self.root.after(8000, self._check_long_absence)\n        self.root.after(10000, self.wish_11_check)')
    p.write_text(t, encoding='utf-8')
    print('added wish')
else:
    print('already there')
