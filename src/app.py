import pathlib
import threading
import sys
import os
# Ensure src is on path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from pet_window import PetWindow
from activity import ActivityMonitor
from taskbar import calc_position, get_taskbar_edge, get_taskbar_rect

try:
    import pystray
    from PIL import Image
    HAS_TRAY=True
except: HAS_TRAY=False

def _base():
    if getattr(sys, 'frozen', False):
        return pathlib.Path(sys._MEIPASS)  # type: ignore
    return pathlib.Path(__file__).parent.parent
SPRITE_DIR = _base() / "assets" / "sprites"
MEOW_WAV = _base() / "assets" / "meow.wav"

def main():
    print(f"Sprite dir: {SPRITE_DIR} exists={SPRITE_DIR.exists()}")
    print(f"Taskbar rect={get_taskbar_rect()} edge={get_taskbar_edge()} placement above={calc_position(56,56,'above')} overlay={calc_position(56,56,'overlay')}")
    pet = PetWindow(SPRITE_DIR)

    mon = ActivityMonitor(cpu_thresh=42)
    def on_activity(active, reason, cpu, pcount):
        # Tk is not thread-safe, use after
        def do():
            if active:
                print(f"[activity] {reason} cpu={cpu:.0f}% procs={pcount}")
            pet.set_activity_state(active, reason)
        try:
            pet.root.after(0, do)
        except: pass
    mon.start(on_activity)

    if HAS_TRAY:
        def tray_thread():
            icon_path = SPRITE_DIR / "frame_4.png"
            if icon_path.exists():
                img = Image.open(icon_path).resize((64,64), Image.NEAREST)
            else:
                img = Image.new("RGBA",(64,64),(255,170,0,255))
            def on_show(icon, item): pet.root.after(0, pet.root.deiconify)
            def on_above(icon, item): pet.root.after(0, lambda: pet.set_placement("above"))
            def on_overlay(icon, item): pet.root.after(0, lambda: pet.set_placement("overlay"))
            def on_quit(icon, item):
                icon.stop()
                pet.root.after(0, pet.quit)
            n = pet.kitten_name or "Kitten"
            def on_mute(icon,item): pet.root.after(0, pet.toggle_mute)
            def on_story(icon,item): pet.root.after(0, pet.show_scrapbook)
            def on_luck(icon,item): pet.root.after(0, pet.trigger_luck)
            menu = pystray.Menu(
                pystray.MenuItem("Placement: Above", on_above),
                pystray.MenuItem("Placement: Overlay (ON taskbar)", on_overlay),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(f"Pet {n} <3", lambda icon,item: pet.root.after(0, pet.trigger_pet)),
                pystray.MenuItem("Wish me luck 🍀", on_luck),
                pystray.MenuItem("Our story 📖", on_story),
                pystray.MenuItem("Mute 🔇", on_mute),
                pystray.MenuItem("Quit", on_quit)
            )
            icon = pystray.Icon("Kitty", img, f"{n} - Taskbar Kitten", menu)
            icon.run()
        threading.Thread(target=tray_thread, daemon=True).start()
        print(f"Tray started for {pet.kitten_name or 'Kitten'}.")

    print(f"=== {pet.kitten_name or 'Kitten'} is ready ===")
    print(" - Sound: purr on pet, chirp on wake (tray Mute to toggle)")
    print(f" - Our story: days, pets, apart. Pet count {pet.memory.get('petCount',0)}")
    pet.run()
    mon.stop()
    print("Exited")

if __name__ == "__main__":
    main()
