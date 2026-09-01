import pathlib, re
p=pathlib.Path(r'D:\KITTY\src\pet_window.py')
t=p.read_text(encoding='utf-8')
# replace _play_meow purr to use wav
old = '''    def _play_meow(self, kind="meow"):
        if self.memory.get("is_muted"):
            print("🔇 muted"); return
        def _do():
            try:
                import winsound, time as _t
                if kind=="purr":
                    # low rumble purr 25-50Hz feel: soft 80-65Hz tremolo, not musical beeps
                    for f in (72,68,65,70,68,65):
                        try: winsound.Beep(f, 70)
                        except: _t.sleep(0.07)
                        _t.sleep(0.025)
                    # tail
                    try: winsound.Beep(60, 90)
                    except: pass
                elif kind=="chirp":
                    winsound.Beep(1350, 70); winsound.Beep(1680, 90)
                else:
                    winsound.Beep(880, 110); winsound.Beep(1046, 140)
            except: pass
            print(f"🔊 {kind}")
        import threading
        threading.Thread(target=_do, daemon=True).start()'''
new = '''    def _play_meow(self, kind="meow"):
        if self.memory.get("is_muted"):
            print("muted"); return
        def _do():
            try:
                import pathlib, winsound
                wav = pathlib.Path(__file__).parent.parent / "assets" / "meow.wav"
                if wav.exists() and kind in ("meow","purr","chirp"):
                    try:
                        winsound.PlaySound(str(wav), winsound.SND_FILENAME | winsound.SND_ASYNC)
                    except:
                        winsound.Beep(880, 110); winsound.Beep(1046, 140)
                else:
                    if kind=="purr":
                        for f in (72,68,65,70,68,65):
                            try: winsound.Beep(f, 70)
                            except: __import__('time').sleep(0.07)
                            __import__('time').sleep(0.025)
                        try: winsound.Beep(60, 90)
                        except: pass
                    elif kind=="chirp":
                        winsound.Beep(1350, 70); winsound.Beep(1680, 90)
                    else:
                        winsound.Beep(880, 110); winsound.Beep(1046, 140)
            except: pass
            print(f"sound {kind}")
        import threading
        threading.Thread(target=_do, daemon=True).start()'''
if old in t:
    t=t.replace(old, new)
    p.write_text(t, encoding='utf-8')
    print('fixed meow to wav')
else:
    print('old not found, trying re')
    # fallback regex
    import re
    t=re.sub(r'    def _play_meow.*?threading\.Thread\(target=_do.*?', new, t, flags=re.DOTALL)
    p.write_text(t, encoding='utf-8')
    print('fallback fixed')
