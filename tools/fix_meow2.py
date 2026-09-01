import pathlib, re
p=pathlib.Path(r'D:\KITTY\src\pet_window.py')
t=p.read_text(encoding='utf-8')
new_def = '''    def _play_meow(self, kind="meow"):
        if self.memory.get("is_muted"):
            print("muted"); return
        def _do():
            try:
                import pathlib, winsound
                wav = pathlib.Path(__file__).parent.parent / "assets" / "meow.wav"
                if wav.exists():
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
# replace old def
t = re.sub(r'    def _play_meow\(self, kind="meow"\):.*?threading\.Thread\(target=_do.*?(?=\n    def toggle_mute)', new_def + '\n\n', t, flags=re.DOTALL)
p.write_text(t, encoding='utf-8')
print('fixed')
