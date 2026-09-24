import pathlib
import threading
import sys
import os
import ctypes
# Ensure src is on path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from pet_window import PetWindow
from activity import ActivityMonitor
from taskbar import calc_position, get_taskbar_edge, get_taskbar_rect

try:
    import pystray
    from PIL import Image
    HAS_TRAY=True
except Exception:
    HAS_TRAY=False

def _base():
    if getattr(sys, 'frozen', False):
        return pathlib.Path(sys._MEIPASS)  # type: ignore
    return pathlib.Path(__file__).parent.parent
SPRITE_DIR = _base() / "assets" / "sprites"
MEOW_WAV = _base() / "assets" / "meow.wav"

_SINGLE_INSTANCE_MUTEX = "Local\\TaskbarKitten_SingleInstance_Mutex"

def acquire_single_instance():
    """Return handle if we are the only instance, else None."""
    kernel32 = ctypes.windll.kernel32
    # c_int (the default restype) truncates a 64-bit HANDLE on x64
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    handle = kernel32.CreateMutexW(None, False, _SINGLE_INSTANCE_MUTEX)
    if not handle:
        return None
    # ERROR_ALREADY_EXISTS = 183
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(handle)
        return None
    return handle

def main():
    mutex = acquire_single_instance()
    if mutex is None:
        ctypes.windll.user32.MessageBoxW(None,
            "Madhu is already running. Check the system tray.\n\n"
            "If the kitten is stuck, right-click its tray icon and choose Quit, "
            "or end the Kitty process in Task Manager.",
            "Madhu - Already Running", 0x40)
        return

    print(f"Sprite dir: {SPRITE_DIR} exists={SPRITE_DIR.exists()}")
    print(f"Taskbar rect={get_taskbar_rect()} edge={get_taskbar_edge()} placement above={calc_position(56,56,'above')} overlay={calc_position(56,56,'overlay')}")
    pet = PetWindow(SPRITE_DIR)

    mon = ActivityMonitor(cpu_thresh=42)
    def on_activity(active, reason, cpu, pcount):
        # Tk is not thread-safe, marshal onto the UI queue
        pet.post_ui(lambda: (print(f"[activity] {reason} cpu={cpu:.0f}% procs={pcount}") if active else None, pet.set_activity_state(active, reason)))
    mon.start(on_activity)

    if HAS_TRAY:
        state = {"name": pet.kitten_name or "Kitten", "muted": bool(pet.memory.get("is_muted"))}
        def tray_thread():
            icon_path = SPRITE_DIR / "frame_4.png"
            if icon_path.exists():
                img = Image.open(icon_path).resize((64,64), Image.NEAREST)
            else:
                img = Image.new("RGBA",(64,64),(255,170,0,255))
            def on_show(icon, item): pet.post_ui(pet.root.deiconify)
            def on_above(icon, item): pet.post_ui(lambda: pet.set_placement("above"))
            def on_overlay(icon, item): pet.post_ui(lambda: pet.set_placement("overlay"))
            def on_quit(icon, item):
                icon.stop()
                pet.post_ui(pet.quit)
            def on_mute(icon,item): pet.tray_state = state; pet.post_ui(pet.toggle_mute)
            def on_story(icon,item): pet.post_ui(pet.show_scrapbook)
            def on_luck(icon,item): pet.post_ui(pet.trigger_luck)
            def name_text(item): return f"Pet {pet.kitten_name or 'Kitten'} <3"
            def mute_text(item): return ("🔇 Unmute" if pet.memory.get("is_muted") else "🔊 Mute")
            menu = pystray.Menu(
                pystray.MenuItem("Placement: Above", on_above),
                pystray.MenuItem("Placement: Overlay (ON taskbar)", on_overlay),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(name_text, lambda icon,item: pet.post_ui(pet.trigger_pet)),
                pystray.MenuItem("Wish me luck 🍀", on_luck),
                pystray.MenuItem("Our story 📖", on_story),
                pystray.MenuItem(mute_text, on_mute),
                pystray.MenuItem("Quit", on_quit)
            )
            icon = pystray.Icon("Kitty", img, f"{state['name']} - Taskbar Kitten", menu)
            pet.tray_icon = icon
            icon.run()
        threading.Thread(target=tray_thread, daemon=True).start()
        print(f"Tray started for {pet.kitten_name or 'Kitten'}.")

    print(f"=== {pet.kitten_name or 'Kitten'} is ready ===")
    print(" - Sound: purr on pet, chirp on wake (tray Mute to toggle)")
    print(f" - Our story: days, pets, apart. Pet count {pet.memory.get('petCount',0)}")
    if os.environ.get("KITTY_OPEN_JOURNAL") == "1" or "--open-journal" in sys.argv:
        pet.post_ui(pet.show_journal)
    pet.run()
    mon.stop()
    # we never took ownership, so ReleaseMutex was a no-op; close the handle
    # explicitly instead (the kernel would clean it up at exit anyway)
    kernel32 = ctypes.windll.kernel32
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle(mutex)
    print("Exited")

if __name__ == "__main__":
    main()