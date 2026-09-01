import pathlib, re
t=pathlib.Path(r'D:\KITTY\src\pet_window.py').read_text(encoding='utf-8')
m=re.search(r'LUCK_MESSAGES = \[(.*?)\]', t, re.DOTALL)
entries=[l.strip() for l in m.group(1).splitlines() if l.strip().startswith('"')]
print('entries', len(entries))
# show first 2
print(entries[:2])
