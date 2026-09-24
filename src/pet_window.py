import tkinter as tk

import ctypes, pathlib, random, time, json, datetime

import logging
_LOGGER=logging.getLogger("madhu")
if not _LOGGER.handlers:
    _log_dir=pathlib.Path.home()/"TaskbarKitten"
    try: _log_dir.mkdir(parents=True, exist_ok=True)
    except: _log_dir=pathlib.Path.home()
    _h=logging.FileHandler(_log_dir/(__name__.split(".")[-1]+".log"),
                           encoding="utf-8")
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _LOGGER.addHandler(_h)
    _LOGGER.setLevel(logging.INFO)

# --- safe print: a cp1252 console (or a missing/redirected stdout in a
# --windowed exe) must never crash a Tk callback over an emoji print ---
import builtins as _builtins
_orig_print = _builtins.print
def _safe_print(*a, **k):
    try:
        _orig_print(*a, **k)
    except Exception:
        try:
            _msgs=[]
            for _x in a:
                try: _msgs.append(str(_x))
                except Exception: _msgs.append(repr(_x))
            _LOGGER.info(" ".join(_msgs))
        except Exception:
            pass
_builtins.print = _safe_print

from animator import SpriteAnimator

from taskbar import calc_position, get_taskbar_edge, get_taskbar_rect, get_screen_size, get_work_area

import memory as mem

# Best-effort Latin-1 mapping so PDF export keeps accents/emojis readable
_PDF_TRANSLIT={
    "'":"'", "’":"'", "“":"\"", "”":"\"", "–":"-", "—":"-", "…":"...",
    "é":"e","è":"e","ê":"e","ë":"e","á":"a","à":"a","â":"a","ä":"a","ã":"a","å":"a",
    "í":"i","ì":"i","î":"i","ï":"i","ó":"o","ò":"o","ô":"o","ö":"o","õ":"o",
    "ú":"u","ù":"u","û":"u","ü":"u","ñ":"n","ç":"c","Ç":"C","É":"E","À":"A","È":"E","Ü":"U","Ö":"O","Á":"A","Í":"I","Ó":"O","Ú":"U",
    "œ":"oe","æ":"ae","ß":"ss",
    "♥":"*","·":"-","•":"*","✦":"*","★":"*","☆":"*","☑":"[x]","☐":"[ ]","✓":"v",
    "🔥":"*","💖":"*","💌":"*","🐾":"*","📖":"*","📊":"*","😍":"*","😊":"*","😐":"*","😢":"*","😤":"*","🌙":"*","✨":"*","♡":"*","📷":"*","💘":"*","🎄":"*","🎃":"*","🔒":"*","🔍":"*","🗓":"*","💾":"*","📄":"*","✎":"*","🗑":"*","📤":"*","⏰":"*","📝":"*","🔗":"*","🎨":"*","📋":"*","☑":"[x]",
}



PET_W=56

PET_H=56

BIG_W=96

BIG_H=96



class PetWindow:

    def __init__(self, sprite_dir):

        self.root = tk.Tk()

        self.root.overrideredirect(True)

        self.root.attributes("-topmost", True)

        self.root.attributes("-transparentcolor", "#FF00FF")

        self.root.configure(bg="#FF00FF")

        # surface any unhandled Tk-callback error (the "left panel went black"
        # bug and friends died invisibly before this because no reporter existed)
        def _tk_crash(*exc_info):
            _LOGGER.error("unhandled Tk callback error: %s",
                          " / ".join(str(x) for x in exc_info[:2]))
            try:
                self._show_bubble("Madhu wiggled — check the log for details", 4000)
            except Exception:
                pass
        self.root.report_callback_exception=_tk_crash

        # memory

        self.memory = mem.load()

        mem.ensure_birth(self.memory)

        if not self.memory.get("lastSeen"):
            # only stamp a presence timestamp on a genuinely new profile; on a
            # re-run we keep the PREVIOUS exit time so "longest time apart" and
            # the "missed you" greeting can actually tally a multi-day absence.
            self.memory["lastSeen"]=datetime.datetime.now().isoformat()

        mem.save(self.memory)

        # position

        # writable pos file (AppData for exe)
        import sys as _sys, os as _os
        if getattr(_sys, 'frozen', False):
            _d = pathlib.Path(_os.getenv("APPDATA", str(pathlib.Path.home()))) / "TaskbarKitten"
            _d.mkdir(parents=True, exist_ok=True)
            self._pos_file = _d / "kitten_pos.txt"
        else:
            self._pos_file = pathlib.Path(__file__).parent.parent / "assets" / "kitten_pos.txt"

        # migrate from memory if exists

        if self.memory.get("pos_x") is not None:

            self.walk_x = int(self._clamp_x(self.memory["pos_x"]))

        else:

            self.walk_x = self._clamp_x(self._load_pos())

        self.walk_dir = 1

        self.root.geometry(f"{PET_W}x{PET_H}+0+0")

        self.kitten_name = self.memory.get("name") or "Madhu"

        self._name_pending = False

        try: self.root.title(self.kitten_name)

        except: pass

        self.animator = SpriteAnimator(sprite_dir)

        self.label = tk.Label(self.root, bg="#FF00FF", bd=0)

        self.label.pack(fill="both", expand=True)

        self.label.bind("<Button-1>", self.on_click)

        self.label.bind("<Button-3>", self.on_right_click)

        self.root.bind("<Button-3>", self.on_right_click)

        self.label.bind("<Enter>", lambda e: self.on_hover(True))

        self.label.bind("<Leave>", lambda e: self.on_hover(False))

        self.label.bind("<B1-Motion>", self.on_drag)



        self.placement = "above"

        self.edge = get_taskbar_edge()

        self._tk_img_ref = None

        self.pet_w = PET_W

        self.pet_h = PET_H

        self.is_duck = False

        self.duck_side = "right"

        self.walk_active = False

        self.bored_since = time.time()

        self.is_petting = False

        self.last_activity = time.time()

        self._modal_open = False

        self._startup_greeted = False

        self._ui_queue = []

        self._last_sound_ts = 0

        self._journal_read_error = False

        self._unlock_fails = 0



        self.menu = tk.Menu(self.root, tearoff=0)

        self.menu.add_command(label="Placement: Above (floating)", command=lambda: self.set_placement("above"))

        self.menu.add_command(label="Placement: Overlay (on taskbar)", command=lambda: self.set_placement("overlay"))

        self.menu.add_separator()

        self.menu.add_command(label="Walk now (bored)", command=self.trigger_walk)

        pet_label = f"Pet {self.kitten_name} <3" if self.kitten_name else "Pet her <3"

        self.menu.add_command(label=pet_label, command=self.trigger_pet)

        self.menu.add_command(label="Gayathree's Journal 📖", command=self.show_journal)

        self.menu.add_command(label="Wish me luck 🍀", command=self.trigger_luck)

        self.menu.add_command(label="Our story 📖", command=self.show_scrapbook)

        self.menu.add_command(label="Don't sleep 30m ☕", command=self.toggle_dont_sleep)

        mute_lab = "Unmute 🔊" if self.memory.get("is_muted") else "Mute 🔇"

        self.menu.add_command(label=mute_lab, command=self.toggle_mute)

        self.menu.add_command(label="Duck mode (coding)", command=self.toggle_duck)

        self.menu.add_separator()

        n = self.kitten_name or "kitten"

        self.menu.add_command(label="Quit", command=self.quit)



        # subtle shadow grounding (solid taskbar anchor) - add 1px darker bottom edge via frame

        try:

            self.shadow = tk.Frame(self.root, bg="#D0C8C0", height=2)

            self.shadow.place(relx=0.18, rely=0.96, relwidth=0.64)

            self.shadow.lower(self.label)

        except: pass

        self._anim_after=None

        self._last_input_ts = time.time()

        self._last_curious = 0

        self._last_food = 0

        self._bored_threshold = random.randint(32,48)

        try:

            self._food_bubble = None

            self._bubble_after = None

        except: pass

        self._breath_phase=0.0
        self._walk_bob=0
        self._last_glance=0
        self._long_absence_done=False
        self._dont_sleep_until=0
        self._dont_sleep_after=None
        self._walk_after=None
        self._dont_sleep_tick_after=None
        self._last_wish_slot=None
        self._last_journal_slot=None
        self.update_position()

        self.animate()

        self.root.after(5000, self.poll_position)

        self.root.after(3000, self.bored_check)

        self.root.after(3000, self.duck_check)

        self.root.after(2200, self.curious_check)

        self.root.after(2500, self.food_check)
        self.root.after(2800, self.arch_check)

        self.root.after(900, self.ask_name_if_needed)

        self.root.after(2000, self.mood_on_startup)

        self.root.after(4000, self.seasonal_check)

        self.root.after(6000, self.waiting_check)

        self.root.after(1800, self.glance_check)

        self.root.after(8000, self._check_long_absence)

        self.root.after(10000, self.wish_11_check)
        self.root.after(15000, self.check_journal_reminder)

        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self.root.after(300, self._drain_ui)
    def post_ui(self, fn):
        try:
            self._ui_queue.append(fn)
        except Exception:
            pass

    def _drain_ui(self):
        try:
            q=self._ui_queue
            self._ui_queue=[]
            for fn in q:
                try: fn()
                except Exception as _e: _LOGGER.error("ui cb: %s", _e)
        except Exception as _e:
            _LOGGER.error("drain ui: %s", _e)
        try:
            self.root.after(300, self._drain_ui)
        except Exception:
            pass

    def _base_dir(self):
        import sys as _sys
        if getattr(_sys, 'frozen', False):
            return pathlib.Path(getattr(_sys, '_MEIPASS', pathlib.Path(__file__).parent.parent))
        return pathlib.Path(__file__).parent.parent

    def _ready_for_transition(self):
        return not self.walk_active and not self.is_petting and not self.is_duck and not self._modal_open

    def _restore_geom(self, w, h, dx=0, dy=0):
        try:
            x=self.root.winfo_x(); y=self.root.winfo_y()
            self.root.geometry(f"{w}x{h}+{x+dx}+{y+dy}")
        except Exception:
            pass

    def set_placement(self, mode):

        if self.is_duck:

            self.set_duck(False)

        self.placement = mode

        print(f"Placement -> {mode}")

        self.update_position()



    def set_duck(self, enable):

        self.is_duck = enable

        if enable:

            self.walk_active=False

            self.animator.set_state("duck", big=True)

            self.pet_w = BIG_W

            self.pet_h = BIG_H

            sw,sh = get_screen_size()

            x = sw - BIG_W - 12

            y = sh//2 - BIG_H//2

            self.root.geometry(f"{BIG_W}x{BIG_H}+{x}+{y}")

            _LOGGER.info("duck mode enabled")



    def toggle_duck(self):

        # manual duck must NOT be auto-tucked by duck_check; only the user
        # (or the OFF toggle) may end it
        self._duck_manual = not self.is_duck
        self.set_duck(not self.is_duck, source="manual")



    def _is_fullscreen(self):

        try:

            fg = ctypes.windll.user32.GetForegroundWindow()

            if not fg: return False

            sw,sh = get_screen_size()

            r = ctypes.wintypes.RECT()

            ctypes.windll.user32.GetWindowRect(fg, ctypes.byref(r))

            return (r.right-r.left)==sw and (r.bottom-r.top)==sh

        except: return False



    def update_position(self):

        if self.is_duck:

            return

        if self.walk_active:

            return

        self.edge = get_taskbar_edge()

        # fullscreen tuck: don't overlay maximised video/game

        tuck = 6 if self._is_fullscreen() else 0

        if self.walk_x is not None:

            x = int(self._clamp_x(self.walk_x))

            if x != self.walk_x:

                self.walk_x = x

            _, y = calc_position(self.pet_w, self.pet_h, self.placement)

            y += tuck

            self.root.geometry(f"{self.pet_w}x{self.pet_h}+{x}+{y}")

        else:

            x,y = calc_position(self.pet_w, self.pet_h, self.placement)

            y += tuck

            self.root.geometry(f"{self.pet_w}x{self.pet_h}+{x}+{y}")

        # debounce save already in _save_pos (pos_x)

        self._save_pos()

        # don't call lift() here; animate/walk will lift when needed



    def poll_position(self):

        if not self.is_duck and not self.walk_active:

            self.update_position()

        self.root.after(5000, self.poll_position)



    # --- animation loop --- with randomized ranges + breathing bob

    def animate(self):

        state = self.animator.get_state()

        # Don't Sleep: never stay in sleeping, nudge to lively states

        if self._is_dont_sleep() and state == "sleeping" and not self.is_duck and not self.walk_active and not self.is_petting:

            # redirect sleep to playful instead

            self.animator.set_state(random.choice(["play","groom","watching","knead","loaf"]), big=False, flip=False)

            state = self.animator.get_state()

        if state == "sleeping" and not self.is_duck and not self.walk_active and not self.is_petting:

            # architecture idle easter egg 3% : blueprint nap hint (90s cooldown)

            if random.random()<0.03 and time.time()-getattr(self,"_last_nap_bubble",0)>90:

                self._last_nap_bubble=time.time()

                self._show_bubble("📐 *blueprint nap* Zzz", 3000)

        try:

            tk_img, delay, size = self.animator.next_frame()

            self._tk_img_ref = tk_img

            self.label.configure(image=tk_img)

        except Exception as _e:

            _LOGGER.error("animate tick: %s", _e)

            # don't kill the flywheel on one bad frame

            try:
                if self._anim_after:
                    self.root.after_cancel(self._anim_after)
            except Exception: pass
            self._anim_after=None

            self._anim_after = self.root.after(600, self.animate)

            return

        if size != self.pet_w:

            pass

        if state=="sleeping":

            delay = random.randint(2000,3200)

        elif state=="watching":

            delay = random.randint(900,1500)

        elif state in ("loaf","groom"):

            delay = random.randint(900,1400)

        elif state=="stretch":

            delay = random.randint(260,340)

        elif state=="knead":

            delay = random.randint(280,380)

        elif state=="play":

            delay = random.randint(110,160)

        elif state=="walking":

            delay = random.randint(120,165)

        elif state=="pet":

            delay = random.randint(190,260)

        elif state=="duck":

            delay = random.randint(320,420)

        self._anim_after = self.root.after(delay, self.animate)



    # --- bored -> real cat life ---

    def bored_check(self):

        idle = time.time() - self.last_activity

        if not self.is_duck and not self.walk_active and not self.is_petting:

            cur=self.animator.get_state()

            allowed=("sleeping","watching","blink","loaf","groom","knead","play","stretch")

            # Don't Sleep: allow any idle to trigger walk, not just sleep

            if self._is_dont_sleep():

                allowed=("sleeping","watching","blink","loaf","groom","knead","play","stretch")

            if idle > self._bored_threshold and cur in allowed:

                self._cat_idle_choice()

                # Don't Sleep walks more often

                self._bored_threshold = random.randint(12,18) if self._is_dont_sleep() else random.randint(18,28)

        self.root.after(3000, self.bored_check)



    def _choose_sleep_spot(self):

        sw,_=get_screen_size()

        fav=self.memory.get("favorite_spots",[])

        if fav:

            from collections import Counter

            fav_x=Counter(fav).most_common(1)[0][0]

        else:

            fav_x=sw-80

        # 55% random roam spot, 45% drift home to fav

        if hasattr(self,'_roam_count'): self._roam_count+=1

        else: self._roam_count=0

        if self._roam_count>=3 or random.random()<0.45:

            self._roam_count=0

            return int(fav_x), True

        else:

            # random spot away from fav, 80..sw-80

            rx=random.randint(40, sw-120)

            # avoid fav proximity

            if abs(rx - fav_x) < 120:

                rx = max(40, min(sw-120, rx + random.choice([-160,160])))

            return int(rx), False



    def _nap_at(self, x, home=False):

        _, y = calc_position(self.pet_w, self.pet_h, self.placement)

        self.walk_x=x; self.root.geometry(f"{self.pet_w}x{self.pet_h}+{x}+{y}"); self._save_pos()

        if home: print(f"🏠 nap home fav {x}")

        else: print(f"😴 nap roaming {x}")



    def _cat_idle_choice(self):

        is_awake=self._is_dont_sleep()

        walk_prob=0.45 if is_awake else 0.28

        if random.random() < walk_prob:

            if random.random()<0.55:

                tx,_=self._choose_sleep_spot()

                self._walk_to_spot(tx)

            else:

                self.trigger_walk()

            self.last_activity=time.time()-random.randint(2,6) if is_awake else time.time()-random.randint(3,8)

            return

        r=random.random()

        if r < 0.22:

            print("🐱 stretch & yawn")

            self._notice_beat(lambda: self.animator.set_state("stretch", big=False, flip=False), ms=220)

            self.root.after(1800, lambda: self.animator.set_state("groom", big=False, flip=False) if self._ready_for_transition() else None)

            end_state="play" if is_awake else "sleeping"

            self.root.after(4200, lambda: self.animator.set_state(end_state, big=False, flip=False) if self._ready_for_transition() else None)

        elif r < 0.40:

            print("🐱 loaf & watch birds")

            self.animator.set_state("loaf", big=False, flip=False)

            self.root.after(3600, lambda: self.animator.set_state("watching", big=False, flip=False) if self._ready_for_transition() else None)

            end_state="play" if is_awake else "sleeping"

            self.root.after(6800, lambda: self.animator.set_state(end_state, big=False, flip=False) if self._ready_for_transition() else None)

        elif r < 0.62:

            print("🐱 grooming")

            self.animator.set_state("groom", big=False, flip=False)

            self._show_bubble("lick lick ✨", 2200)

            self.root.after(3800, lambda: self.animator.set_state("blink", big=False, flip=False) if self._ready_for_transition() else None)

            end_state="play" if is_awake else "sleeping"

            self.root.after(5200, lambda: self.animator.set_state(end_state, big=False, flip=False) if self._ready_for_transition() else None)

        elif r < 0.78:

            print("🐱 kneading biscuits")

            self.animator.set_state("knead", big=False, flip=False)

            self._show_bubble("knead knead ♡", 2600)

            end_state="play" if is_awake else "sleeping"

            self.root.after(4000, lambda: self.animator.set_state(end_state, big=False, flip=False) if self._ready_for_transition() else None)

        else:

            print("🐱 playful pounce")

            self.animator.set_state("play", big=False, flip=False)

            self.root.after(2200, lambda: self.animator.set_state("watching", big=False, flip=False) if self._ready_for_transition() else None)

            end_state="play" if is_awake else "sleeping"

            self.root.after(4600, lambda: self.animator.set_state(end_state, big=False, flip=False) if self._ready_for_transition() else None)

        self.last_activity=time.time()-random.randint(2,6) if is_awake else time.time()-random.randint(3,8)



    def _walk_to_spot(self, target_x):

        if self.is_duck or self.walk_active: return

        _LOGGER.info("walk to %s", target_x)

        if self.walk_x is None:

            x0,_=calc_position(self.pet_w, self.pet_h, self.placement)

            self.walk_x=self._clamp_x(x0)

        try:

            if self._anim_after:

                self.root.after_cancel(self._anim_after); self._anim_after=None

        except: pass

        self.walk_dir = 1 if target_x > (self.walk_x or target_x) else -1

        self.animator.set_state("walking", big=False, flip=(self.walk_dir<0))

        self.walk_active=True

        self._walk_steps=0; self._walk_bounces=0

        self._walk_target=target_x

        self._walk_bob=0

        # keep the animation flywheel alive (spot-walk must show real walk frames)

        self._anim_after = self.root.after(10, self.animate)

        self._walk_to_step()



    def _walk_to_step(self):

        if not self.walk_active or self.is_duck:

            self.walk_active=False; self._walk_after=None; return

        # guard: fresh installs have no walk_x yet -> normalize once

        if self.walk_x is None:

            x0,_=calc_position(self.pet_w, self.pet_h, self.placement)

            self.walk_x=self._clamp_x(x0)

            if self.walk_x is None: self.walk_x=x0

        # clamp target into the shared taskbar lane

        min_x, max_x = self._lane_bounds()

        self._walk_target = max(min_x, min(max_x, int(self._walk_target)))

        diff = self._walk_target - self.walk_x

        if abs(diff) < 6:

            self.walk_x = self._walk_target

            _, y = calc_position(self.pet_w, self.pet_h, self.placement)

            y += 6 if self._is_fullscreen() else 0

            self.root.geometry(f"{self.pet_w}x{self.pet_h}+{int(self.walk_x)}+{y}")

            self._save_pos()

            self.walk_active=False; self._walk_after=None

            print(f"arrived nap spot {int(self.walk_x)}")

            end_state="play" if self._is_dont_sleep() else "sleeping"

            self.animator.set_state(end_state, big=False, flip=False)

            self.bored_since=time.time(); self.last_activity=time.time()

            return

        step = max(2, min(4, abs(diff)//18 + 2))

        self.walk_x += step if diff>0 else -step

        if self.walk_x < min_x: self.walk_x=min_x

        if self.walk_x > max_x: self.walk_x=max_x

        tuck=6 if self._is_fullscreen() else 0

        _, y = calc_position(self.pet_w, self.pet_h, self.placement)

        self._walk_bob=(self._walk_bob+1)%4; bob_y=1 if self._walk_bob in (1,2) else 0

        if self._walk_bob==2: bob_y=2

        self.root.geometry(f"{self.pet_w}x{self.pet_h}+{int(self.walk_x)}+{y + tuck - bob_y}")

        if self._walk_bob%4==0: self._save_pos()

        self._walk_after=self.root.after(32, self._walk_to_step)



    def _lane_bounds(self):
        """Return (min_x, max_x) of the walk lane.

        Uses the work area (screen minus taskbar) instead of the raw
        Shell_TrayWnd rect: on an auto-hide taskbar get_taskbar_rect() returns
        an off-screen sliver, and on a right/left (vertical) taskbar it yields
        min_x > max_x -- which glued the pet off-screen forever. The work area
        follows auto-hide and vertical taskbars correctly."""
        try:
            wa=get_work_area()
            l,_,r,_=wa
            if r - l <= self.pet_w + 4:
                raise ValueError("degenerate work area")
            a=int(l)+2
            b=int(r)-self.pet_w-2
            if b < a:
                a,b = b,a
            return a, b
        except Exception:
            try:
                sw,_=get_screen_size()
                a,b=2, sw-self.pet_w-2
                if b < a:
                    a,b = b,a
                return a, max(2, b)
            except Exception:
                return 2, 2000000

    def _clamp_x(self, x):
        """Clamp x into the walk lane shared by trigger_walk/_walk_step/_walk_to_step. None-safe."""
        if x is None:
            return None
        try:
            a,b=self._lane_bounds()
            if b < a:
                a,b = b,a
            return max(a, min(b, int(x)))
        except:
            return int(x)


    def trigger_walk(self):

        if self.is_duck or self.walk_active:

            return

        print("😺 bored... gonna walk!")

        try:

            if self._anim_after:

                self.root.after_cancel(self._anim_after)

                self._anim_after=None

        except: pass

        if self.walk_x is None:

            x,y = calc_position(self.pet_w, self.pet_h, self.placement)

            self.walk_x = x

            self.walk_dir = random.choice([-1,1])

        else:

            # pick a fresh heading each walk - no random U-turn retraces
            self.walk_dir = random.choice([-1,1])

        self.animator.set_state("walking", big=False, flip=(self.walk_dir<0))

        self.walk_active=True

        self.walk_x = self._clamp_x(self.walk_x)

        self._walk_steps=0; self._walk_bounces=0

        self._walk_bob=0

        self._anim_after = self.root.after(10, self.animate)

        self._walk_step()



    def _walk_step(self):

        if not self.walk_active or self.is_duck:

            self.walk_active=False; self._walk_after=None; return

        # walk everywhere: use the shared taskbar lane (not screen 8..sw-8)

        min_x, max_x = self._lane_bounds()

        prev_dir = self.walk_dir

        new_x = self.walk_x + self.walk_dir*4

        bounced=False

        if new_x < min_x:

            new_x=min_x; self.walk_dir=1; bounced=True

        if new_x > max_x:

            new_x=max_x; self.walk_dir=-1; bounced=True

        if self.walk_dir != prev_dir:

            self.animator.set_walk_direction(self.walk_dir)

        self.walk_x = new_x

        _, task_y = calc_position(self.pet_w, self.pet_h, self.placement)

        task_y += 6 if self._is_fullscreen() else 0

        self._walk_bob = (self._walk_bob+1)%4; bob_y=1 if self._walk_bob in (1,2) else 0

        if self._walk_bob==2: bob_y=2

        self.root.geometry(f"{self.pet_w}x{self.pet_h}+{int(self.walk_x)}+{task_y - bob_y}")

        if not hasattr(self, '_walk_steps'): self._walk_steps=0

        if not hasattr(self,'_walk_bounces'): self._walk_bounces=0

        self._walk_steps+=1

        if bounced: self._walk_bounces+=1

        # walk until she has bounced once and roamed at least 1.5x screen (~400 steps) or 2 bounces

        if (self._walk_bounces>=2 and self._walk_steps>60) or self._walk_steps > random.randint(320, 520):

            self._walk_steps=0; self._walk_bounces=0; self.walk_active=False; self._walk_after=None

            self._save_pos()

            print(f"walk done across {int(self.walk_x)}")

            end_state="play" if self._is_dont_sleep() else "sleeping"

            self.animator.set_state(end_state, big=False, flip=False)

            self.bored_since=time.time(); self.last_activity=time.time()

            return

        if self._walk_bob%4==0: self._save_pos()

        self._walk_after=self.root.after(35, self._walk_step)



    # --- pet reaction ---

    def on_click(self, e):

        self.trigger_pet()



    def trigger_pet(self):

        if self._long_absence_done and not self.is_petting:

            self._welcome_back()

            return

        if self.is_petting:

            return

        print("💖 petted!")

        self.is_petting=True

        # pause any in-progress walk so pet animation owns the screen (no sliding hearts)

        if self.walk_active:

            self.walk_active=False

            self._walk_target=None

            if hasattr(self,'_walk_steps'): self._walk_steps=0

            if hasattr(self,'_walk_bounces'): self._walk_bounces=0

            try:

                if self._walk_after:

                    self.root.after_cancel(self._walk_after); self._walk_after=None

            except: pass

        self.last_activity=time.time()

        try:

            self.memory["petCount"]=self.memory.get("petCount",0)+1

            self.memory["lastPet"]=datetime.datetime.now().isoformat()

            self.memory["lastSeen"]=self.memory["lastPet"]

            mem.save(self.memory)

            self._check_milestones()

        except: pass

        prev_was_duck=self.is_duck

        self._play_meow("purr")

        self._notice_beat(lambda: self.animator.set_state("pet", big=prev_was_duck), ms=220)

        orig_w, orig_h = self.pet_w, self.pet_h

        def bounce():

            try:

                pop_w, pop_h = int(orig_w*1.18), int(orig_h*1.18)

                x = self.root.winfo_x()

                y = self.root.winfo_y() - (pop_h-orig_h)

                self.root.geometry(f"{pop_w}x{pop_h}+{x}+{y}")

                self.root.after(160, lambda: self._restore_geom(orig_w, orig_h, 0, (pop_h-orig_h)))

            except: pass

        bounce()

        self.root.after(2200, self._end_pet)



    def _end_pet(self):

        self.is_petting=False

        if self.is_duck:

            self.animator.set_state("duck", big=True)

        else:

            if self._is_dont_sleep():

                self.animator.set_state("play", big=False, flip=False)

            else:

                self.animator.set_state("sleeping", big=False)

            # little purr stay

            self.bored_since=time.time()



    def on_hover(self, entered):

        if entered and not self.is_petting and not self.walk_active and not self.is_duck:

            # subtle ear twitch hint

            pass



    def on_drag(self, e):

        if self.is_duck:

            return

        try:

            self.walk_active=False

            if self._walk_after:

                try: self.root.after_cancel(self._walk_after)

                except: pass

                self._walk_after=None

            if hasattr(self,'_walk_target'): self._walk_target=None

            x = e.x_root - self.pet_w//2 if hasattr(e,'x_root') else self.root.winfo_x() + e.x - self.pet_w//2

            min_x, max_x = self._lane_bounds()

            x=max(min_x, min(max_x, x))

            _, y = calc_position(self.pet_w, self.pet_h, self.placement)

            self.root.geometry(f"{self.pet_w}x{self.pet_h}+{x}+{y}")

            self.walk_x=x

            self._save_pos()

            self._record_favorite(x)

            self.animator.set_state("watching", big=False, flip=False)

            self.root.after(1200, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

            self.last_activity=time.time() - 12

            self.bored_since=time.time()

            if hasattr(self,'_walk_steps'): self._walk_steps=0

            if hasattr(self,'_walk_bounces'): self._walk_bounces=0

        except Exception as e:

            print("drag err",e)



    def on_right_click(self, e):

        try:

            self.menu.tk_popup(e.x_root, e.y_root)

        finally:

            self.menu.grab_release()



    CODING_PROCS = {"code.exe","pycharm64.exe","idea64.exe","devenv.exe","sublime_text.exe","atom.exe","cursor.exe","opencode.exe"}

    ARCH_PROCS = {"acad.exe","revit.exe","rhino.exe","rhinoceros.exe","sketchup.exe","archicad.exe","lumion.exe","twinmotion.exe","vray.exe","v-ray.exe","enscape.exe"}

    RENDER_PROCS = {"lumion.exe","twinmotion.exe","vray.exe","v-ray.exe","enscape.exe"}

    LUCK_MESSAGES = [

        "You got this - Madhu believes in you!",

        "One line at a time, you are building something beautiful",

        "Take a breath, you have solved harder problems before",

        "Go make that model shine - I am right here watching",

        "Architecture is patience - your lines will find their place",

        "Blueprint by blueprint, you are closer",

        "Trust your eye, it has gotten you this far",

        "Small details make great buildings - keep going",

        "Every great model started with a sketch - keep sketching",

        "Your persistence is the strongest foundation",

        "The best designs take time - yours is coming together",

        "You have the vision - now let it unfold",

        "One more wall and the space comes alive",

        "Your creativity is your superpower today",

        "Breathe, adjust that scale, you have got this",

        "The site will thank you for this care",

        "You are not stuck, you are refining",

        "That section will click any second now",

        "Keep the pencil moving - magic happens there",

        "Your hard work is already showing",

        "You make complex feel simple - keep it up",

        "The rendering will be worth the wait",

        "Light, shadow, you understand it - trust it",

        "Your studio hours are paying off",

        "This is not a block, it is a pause before clarity",

        "You have solved tougher sections before",

        "The model is lucky to have you",

        "Keep going, Madhu is purring for you",

        "You are building more than a model - you are building skill",

        "The next line could be the one",

        "Your dedication is beautiful to watch",

        "You are exactly where you need to be",

        "Take a sip, stretch, then nail that detail",

        "The plan is coming together, keep it up",

        "Your eye for proportion is spot on",

        "You handle pressure like a pro",

        "That facade is going to be stunning",

        "Your ideas deserve to be built - keep building",

        "The hard part is almost behind you",

        "You are turning stress into structure",

        "Keep that scale handy - you have got precision",

        "The journey is the design - enjoy this part",

        "Your focus is your strength today",

        "You are making your future self proud",

        "One more extrude and you will see it",

        "The client will love what you are making",

        "Your lines have intent - trust them",

        "You are crafting space, not just drawings",

        "The sun study will be perfect - keep tweaking",

        "Your model has good bones - keep fleshing it",

        "You are closer than you think",

        "That courtyard will feel amazing",

        "Your patience is architectural",

        "You are doing amazing, keep the momentum",

        "The details you add matter",

        "Your vision is clear - follow it",

        "Take it one floor at a time",

        "You are learning with every line",

        "The building is taking shape because of you",

        "Your effort today is tomorrow's portfolio",

        "You have got the eye - now trust the hand",

        "The massing is strong - refine it",

        "Your ideas are worth the effort",

        "Keep that trace paper rolling",

        "You are not behind, you are building",

        "The section is speaking - listen",

        "Your work ethic is inspiring",

        "You make the studio brighter",

        "That texture will pop - keep it",

        "You are in flow, stay there",

        "The next save will feel great",

        "Your draft is already better than yesterday",

        "You are allowed to take a break - keep going",

        "The light you design will guide someone",

        "Your precision will pay off",

        "You are the architect of your own success",

        "Keep that cursor moving - you have got this",

        "The hardest line is the first - you did it",

        "Your model is breathing - keep it alive",

        "You are making progress, even if slow",

        "The plan needs your touch - give it",

        "Your style is emerging - trust it",

        "You are handling this like a designer",

        "The elevation will be worth it",

        "Your hands know what to do",

        "The site deserves your vision",

        "You are building confidence with every click",

        "That stair will be elegant - keep refining",

        "Your concept is strong - detail it",

        "You are not alone - Madhu is here",

        "The render is almost ready - patience",

        "Your lines are confident today",

        "Keep that passion lit",

        "The building will stand because you stood by it",

        "You are making your professors proud",

        "Your future office will thank you",

        "The next undo is not needed - trust it",

        "You are designing with heart",

        "The mass will balance - you will see",

        "Your work is valid and valuable",

        "Take a breath, the deadline will bend",

        "You are more prepared than you feel",

        "The model is your story - tell it",

        "Your skill is growing with every hour",

        "That roof will be iconic",

        "You are pushing through - respect that",

        "The drawing deserves your care - give it",

        "You are exactly the architect for this job",

        "The viewport is your playground - play",

        "Your ideas are not too big - build them",

        "You are making the complex clear",

        "The next layer will bring it together",

        "Your draft is your power",

        "You are not stuck - you are thinking",

        "The building is lucky to be yours",

        "You are doing the work - that is winning",

        "Keep that lineweight consistent - you have got it",

        "The studio believes in you",

        "Your vision will become shelter",

        "You are shaping space and future",

        "That corner detail will be loved",

        "You are allowed to be proud now",

        "The plan is patient - be patient with it",

        "Your hands are steady - trust them",

        "You are making it happen",

        "The design will thank you later",

        "Your focus is your magic",

        "You are not lost - you are exploring",

        "The model will render beautifully",

        "Your effort is the blueprint for success",

        "You are building at your own perfect pace",

        "That material choice is chef kiss",

        "Your persistence will be remembered",

        "The building is becoming real because of you",

        "You are doing enough and you are enough",

        "Keep that layer on - you need it",

        "Your eye will catch the right proportion",

        "You are the reason this project moves",

        "The next orbit will show you the answer",

        "Your design has heart - keep it",

        "You are making your mark",

        "The toughest part is the thinking - you did",

        "Your lines are your language",

        "You are designing courage",

        "The site is waiting for your idea",

        "Your work matters - keep sharing it",

        "You are not behind - you are thorough",

        "The rendering will sing - keep composing",

        "Your model is your meditation",

        "You are building resilience too",

    ]



    def detect_duck_source(self):

        try:

            hwnd=ctypes.windll.user32.GetForegroundWindow()

            length=ctypes.windll.user32.GetWindowTextLengthW(hwnd)

            buff=ctypes.create_unicode_buffer(length+1)

            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length+1)

            title=(buff.value or "").lower()

            fg_proc=self._get_fg_process()

            # strict proc + title fallback for variants like Code - Insiders

            if fg_proc in self.CODING_PROCS:

                return True, "code", False

            if fg_proc in self.ARCH_PROCS:

                return True, "architecture", fg_proc in self.RENDER_PROCS

            coding_titles=["visual studio code","code - insiders","pycharm","intellij idea","sublime text","visual studio","opencode"]

            arch_titles=["autocad","revit","rhino","sketchup","archicad","lumion","twinmotion","v-ray","enscape"]

            if any(k in title for k in coding_titles):

                return True, "code", False

            if any(k in title for k in arch_titles):

                return True, "architecture", any(r in title for r in ("lumion","twinmotion","v-ray"))

        except: pass

        return False, None, False



    def _render_cpu_high(self):

        try:

            import psutil

            for p in psutil.process_iter(['name','cpu_percent']):

                n=(p.info['name'] or "").lower()

                if n in self.RENDER_PROCS:

                    # psutil needs interval call

                    try:

                        cpu=psutil.Process(p.pid).cpu_percent(interval=0.1)

                    except: cpu=0

                    if cpu > 20: return True

        except: pass

        return False



    def _show_duck_explainer_once(self):

        if not self.memory.get("has_seen_duck_explainer"):

            self.memory["has_seen_duck_explainer"]=True; mem.save(self.memory)

            self._show_bubble("This is rubber ducking — explaining it out loud (even to a cat) often helps you solve it. 🦆", 7000)

            print("duck explainer shown")



    def set_duck(self, enable, source="code"):

        was=self.is_duck

        self.is_duck=enable

        if not enable:
            self._duck_manual=False

        if enable:

            self.walk_active=False

            self.memory["duck_trigger_source"]=source; mem.save(self.memory)

            self._play_meow("chirp")

            self.animator.set_state("duck", big=True)

            self.pet_w=BIG_W; self.pet_h=BIG_H

            sw,sh=get_screen_size()

            x=sw-BIG_W-12; y=sh//2-BIG_H//2

            self._notice_beat(lambda: self.root.geometry(f"{BIG_W}x{BIG_H}+{x}+{y}"))

            if not self.memory.get("has_seen_duck_explainer"):

                self.root.after(600, self._show_duck_explainer_once)

            print(f"🦆 Duck ON source={source}")

        else:

            self.pet_w=PET_W; self.pet_h=PET_H

            if self._is_dont_sleep():

                self.animator.set_state("play", big=False, flip=False)

            else:

                self.animator.set_state("sleeping", big=False)

            self.update_position()

            print("Duck OFF")

        # warm welcome back after long absence handled elsewhere



    def duck_check(self):

        should, source, is_render = self.detect_duck_source()

        # render tools: stay while CPU high, but tuck second CPU drops / proc closes

        if is_render and self.is_duck and source=="architecture":

            if self._render_cpu_high():

                self.last_activity=time.time()

                self.root.after(1200, self.duck_check); return

            # CPU dropped or proc closed -> tuck immediately

            print("Render done -> tuck")

            self.set_duck(False)

            self.root.after(1200, self.duck_check); return

        if should and not self.is_duck and not self.is_petting and not self.walk_active:

            self._notice_beat(lambda: self.set_duck(True, source=source))

            self.last_activity=time.time()

        elif not should and self.is_duck and not self.is_petting and not getattr(self, "_duck_manual", False):

            # tuck the second you close the tool (was 14s)

            print("Duck tuck immediate")

            self.set_duck(False)

        self.root.after(3000, self.duck_check)



    # --- curious: when you're doing something, she comes to watch ---

    def _get_last_input_idle(self):

        try:

            class LASTINPUTINFO(ctypes.Structure):

                _fields_=[("cbSize", ctypes.c_uint),("dwTime", ctypes.c_uint)]

            lii=LASTINPUTINFO(); lii.cbSize=ctypes.sizeof(LASTINPUTINFO)

            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):

                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime

                return millis/1000.0

        except: pass

        return 9999



    def curious_check(self):

        try:

            idle = self._get_last_input_idle()

            # you were idle >14s and now just became active (idle <1.2s)

            if not self.is_duck and not self.walk_active and not self.is_petting:

                now=time.time()

                if idle < 1.2 and (now - self._last_input_ts) > 16:

                    # you just returned to PC after idle, 35% chance curious

                    if random.random()<0.35 and now - self._last_curious > 35:

                        self._last_curious=now

                        self.last_activity=now

                        print("👀 curious: you are doing something, kitten comes!")

                        # come watch: short walk toward center or just watching head tilt

                        if random.random()<0.6:

                            self.animator.set_state("watching", big=False, flip=False)

                            self.root.after(4200, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

                        else:

                            # little curious trot

                            old_dir=self.walk_dir

                            # trot toward middle a bit

                            sw,_=get_screen_size()

                            target = sw//2

                            self.walk_dir = 1 if (target - (self.walk_x or target))>0 else -1

                            self.trigger_walk()

                            # keep dir toward target for this walk

                            self.walk_dir = 1 if target>self.walk_x else -1

                            self.animator.set_walk_direction(self.walk_dir)

                # track when user was last idle

                if idle > 14:

                    self._last_input_ts = now

        except Exception as e:

            print("curious err",e)

        self.root.after(2200, self.curious_check)



    # --- food Google easter egg --- 120 pantry + variants

    FOOD_WORDS = {

        # Indian + variants (biryani/biriyani/briyani etc.)

        "biryani","biriyani","briyani","biriani","biriyani","dosa","idli","samosa","pani puri","pav bhaji","vada pav","butter chicken","paneer","dal","roti","naan","paratha","chole","rajma","sambar","rasam","upma","poha","kathi roll","chicken tikka","tandoori","laddoo","laddu","jalebi","gulab jamun","rasgulla","kheer","halwa","pulao","khichdi","bhatura","chole bhature","vada","uttapam","appam","puttu","aviyal","thorans","curry","masala","chutney","pickle","pakora","bhaji","kachori","thepla","dhokla","khaman","undhiyu","bhel puri","sev puri","misal","thali","litti","sattu","momo","chowmein","hakka","manchurian","idly","vadai","payasam",

        # Western + global

        "pizza","burger","pasta","sushi","ramen","taco","burrito","nachos","quesadilla","steak","fries","hot dog","sandwich","bagel","croissant","donut","doughnut","pancake","waffle","brownie","cookie","cake","cupcake","ice cream","gelato","pie","lasagna","risotto","paella","gyros","kebab","shawarma","falafel","hummus","dim sum","dumpling","pho","pad thai","currywurst","pretzel","chocolate","popcorn","bbq","barbecue","salad","soup","omelette","fried chicken","nuggets","wings","milkshake","smoothie","noodles","fried rice",

    }

    FOOD_WORDS = {w.strip().lower() for w in FOOD_WORDS if w.strip()}
    FOOD_SINGLE = {w for w in FOOD_WORDS if " " not in w}

    # architecture search triggers motivational quote on any browser
    ARCH_SEARCH_WORDS = {
        "architecture","architect","autocad","revit","rhino","sketchup","archicad","lumion","twinmotion","vray","v-ray","enscape","blueprint","floor plan","elevation","section","facade","render","3d model","bim","parametric","studio","studio project","site plan","masterplan"
    }
    ARCH_SEARCH_WORDS = {w.strip().lower() for w in ARCH_SEARCH_WORDS if w.strip()}



    def _get_fg_process(self):

        try:

            hwnd=ctypes.windll.user32.GetForegroundWindow()

            pid=ctypes.c_ulong()

            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            import psutil

            return psutil.Process(pid.value).name().lower() if pid.value else ""

        except: return ""



    def _is_arch_search(self):
        try:
            hwnd=ctypes.windll.user32.GetForegroundWindow()
            length=ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff=ctypes.create_unicode_buffer(length+1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length+1)
            title=(buff.value or "").lower()
            if not title: return False, ""
            for w in self.ARCH_SEARCH_WORDS:
                if w in title:
                    return True, w
            return False, ""
        except: return False, ""

    def _lev(self, a,b):

        if a==b: return 0

        if abs(len(a)-len(b))>2: return 99

        # quick DP for short strings

        prev=list(range(len(b)+1))

        for i,ca in enumerate(a,1):

            cur=[i]+[0]*len(b)

            for j,cb in enumerate(b,1):

                cur[j]= min(prev[j]+1, cur[j-1]+1, prev[j-1]+(0 if ca==cb else 1))

            prev=cur

        return prev[-1]



    def _is_food_google(self):

        try:

            hwnd=ctypes.windll.user32.GetForegroundWindow()

            length=ctypes.windll.user32.GetWindowTextLengthW(hwnd)

            buff=ctypes.create_unicode_buffer(length+1)

            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length+1)

            title=(buff.value or "").lower()

            if not title: return False, ""

            # 1) exact substring (handles "pani puri" etc)

            for w in self.FOOD_WORDS:

                if w in title:

                    return True, w

            # 2) fuzzy token match for typos like biriyani/biryani

            import re

            tokens=re.findall(r"[a-z]+", title)

            for tok in tokens:

                if len(tok)<4: continue

                for w in self.FOOD_SINGLE:

                    if self._lev(tok, w) <= 1:  # 1 typo tolerance

                        return True, w

                    # 2 for longer words like biryani/biriyani distance 1

                    if len(w)>=7 and self._lev(tok, w)==2 and tok[:2]==w[:2]:

                        return True, w

            return False, ""

        except: return False, ""



    def _show_food_bubble(self, word):

        try:

            if self._food_bubble:

                try: self._food_bubble.destroy()

                except: pass

            bub=tk.Toplevel(self.root)

            bub.overrideredirect(True); bub.attributes("-topmost", True); bub.configure(bg="#FFF8DC")

            lab=tk.Label(bub, text=f"gimme {word} 🍕😋", bg="#FFF8DC", fg="#8B4513", font=("Segoe UI", 9, "bold"), padx=8, pady=4, bd=1, relief="solid")

            lab.pack()

            bub.update_idletasks()

            bw=bub.winfo_reqwidth(); bh=bub.winfo_reqheight()

            sw,sh=get_screen_size()

            x=self.root.winfo_x()+self.pet_w//2 - bw//2; y=self.root.winfo_y()-bh-6

            x=max(8, min(sw - bw - 8, x))

            y=max(8, y)

            bub.geometry(f"{bw}x{bh}+{x}+{y}")

            self._food_bubble=bub

            self.root.after(4000, lambda: bub.destroy() if bub.winfo_exists() else None)

        except: pass



    def food_check(self):

        try:

            now=time.time()

            # spam guard: 25s debounce + store last word so same title doesn't loop every 3s

            if now - self._last_food > 22:

                is_food, word = self._is_food_google()

                if is_food and word != getattr(self,'_last_food_word',None):

                    self._last_food=now; self._last_food_word=word

                    self.last_activity=now

                    print(f"🍕 always hungry: '{word}' -> come! proc={self._get_fg_process()}")

                    if self._walk_after:

                        try: self.root.after_cancel(self._walk_after)

                        except: pass

                        self._walk_after=None

                    try:

                        if self._anim_after:

                            self.root.after_cancel(self._anim_after); self._anim_after=None

                    except: pass

                    self.is_petting=False; self.walk_active=False

                    self.animator.set_state("pet", big=self.is_duck)

                    self._show_food_bubble(word)

                    # always keep the animation flywheel alive (duck mode has no trigger_walk)

                    self._anim_after=self.root.after(10, self.animate)

                    if not self.is_duck:

                        self.bored_since=now

                        self.root.after(180, self.trigger_walk)

                    self.root.after(4800, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self.animator.get_state()=="pet" and not self._is_dont_sleep() and not self.is_duck else None)

        except Exception as e:

            print("food err",e)

        self.root.after(1200, self.food_check)

    def arch_check(self):
        try:
            now=time.time()
            if now - getattr(self,'_last_arch',0) > 35:
                is_arch, word = self._is_arch_search()
                if is_arch and word != getattr(self,'_last_arch_word',None):
                    self._last_arch=now; self._last_arch_word=word
                    print(f"arch google '{word}' -> motivational quote")
                    try: idx=int(self.memory.get("luck_message_index",0) or 0)
                    except: idx=0
                    msg=self.LUCK_MESSAGES[idx % len(self.LUCK_MESSAGES)]
                    self.memory["luck_message_index"]=(idx+1)%len(self.LUCK_MESSAGES); mem.save(self.memory)
                    self._show_bubble(msg, 6000)
                    if not self.is_duck and not self.walk_active and not self.is_petting:
                        self.animator.set_state("watching", big=False, flip=False)
                        self.root.after(3200, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)
        except Exception as e:
            print("arch err",e)
        self.root.after(1600, self.arch_check)



    def set_activity_state(self, active, reason):

        # background CPU is NOT life - keep chill baseline, just log, don't twitch

        # only update bored timer so not considered idle while PC busy

        if active:

            self.bored_since=time.time()

            # optional: very subtle 4% chance she glances, not hyper wake

            if random.random()<0.04 and not self.is_duck and not self.walk_active and not self.is_petting and self.animator.get_state()=="sleeping":

                self.animator.set_state("watching", big=False, flip=False)

                self.root.after(2800, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)



    # --- gift emotional touches ---

    def ask_name_if_needed(self):

        if self.memory.get("name") or self._name_pending:

            return

        self._name_pending=True

        self._modal_open=True

        # beautiful gift-style dialog: soft parchment #FFF8DC, rounded card via Canvas, shadow

        dlg=tk.Toplevel(self.root)

        dlg.overrideredirect(True)

        dlg.attributes("-topmost", True)

        dlg.configure(bg="#FFF8DC")

        dlg.title("What's my name?")

        W,H=360,410

        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()

        dlg.geometry(f"{W}x{H}+{sw//2-W//2}+{sh//2-H//2}")

        # gift parchment container with rounded card effect via Canvas + shadow

        canvas=tk.Canvas(dlg, width=W, height=H, bg="#FFF8DC", highlightthickness=0, bd=0)

        canvas.pack(fill="both", expand=True)

        def _round_rect(x1,y1,x2,y2,r, **kw):

            pts=[x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]

            return canvas.create_polygon(pts, smooth=True, **kw)

        # shadow - soft drop shadow for gift card

        _round_rect(12,16,W-12,H-8,20, fill="#E6D5B8", outline="")

        # main rounded card

        _round_rect(8,8,W-16,H-12,20, fill="white", outline="#FFDAB9", width=2)

        # card frame for widgets (white bg sitting on canvas parchment #FFF8DC)

        card=tk.Frame(dlg, bg="white", bd=0)

        card.place(x=16, y=16, width=W-32, height=H-28)

        # allow dragging borderless window

        def _start_drag(e):

            dlg._drag_x=e.x; dlg._drag_y=e.y

        def _do_drag(e):

            try:

                x=dlg.winfo_x()+e.x-dlg._drag_x; y=dlg.winfo_y()+e.y-dlg._drag_y; dlg.geometry(f"+{x}+{y}")

            except: pass

        card.bind("<Button-1>", _start_drag); card.bind("<B1-Motion>", _do_drag)

        canvas.bind("<Button-1>", _start_drag); canvas.bind("<B1-Motion>", _do_drag)

        # cat sprite image top center (load D:\KITTY\assets\sprites\frame_4.png resize 72x72)

        tk_img=None

        try:

            from PIL import Image, ImageTk

            import pathlib as _pl

            pth=self._base_dir()/ "assets" / "sprites" / "frame_4.png"

            if not pth.exists():

                pth=_pl.Path(__file__).parent.parent / "assets" / "sprites" / "frame_4.png"

            im=Image.open(pth).convert("RGBA").resize((72,72), Image.LANCZOS)

            tk_img=ImageTk.PhotoImage(im)

            dlg._kitten_img=tk_img

        except Exception:

            if pth.exists():

                try:

                    tk_img=tk.PhotoImage(file=str(pth))

                    dlg._kitten_img=tk_img

                except Exception:

                    tk_img=None

            else:

                tk_img=None

        if tk_img is not None:

            icon_lab=tk.Label(card, image=tk_img, bg="white", bd=0)

            icon_lab.pack(pady=(14,6))

            icon_lab.bind("<Button-1>", _start_drag); icon_lab.bind("<B1-Motion>", _do_drag)

        else:

            tk.Label(card, text="🐱", bg="white", fg="#FF8FA3", font=("Segoe UI", 28)).pack(pady=(10,4))

        # title "Meet your kitten ✨" in Segoe UI 13 bold #8B4513

        title_lab=tk.Label(card, text="Meet your kitten ✨", bg="white", fg="#8B4513", font=("Segoe UI", 13, "bold"))

        title_lab.pack(pady=(2,2))

        title_lab.bind("<Button-1>", _start_drag); title_lab.bind("<B1-Motion>", _do_drag)

        # subtitle "She's been waiting for you — what will you call her?" 9 italic

        sub_lab=tk.Label(card, text="She's been waiting for you — what will you call her?", bg="white", fg="#8B4513", font=("Segoe UI", 9, "italic"), wraplength=300, justify="center")

        sub_lab.pack(pady=(0,16))

        sub_lab.bind("<Button-1>", _start_drag); sub_lab.bind("<B1-Motion>", _do_drag)

        tk.Frame(card, bg="#FFF0E6", height=1).pack(fill="x", padx=24, pady=(0,16))

        var=tk.StringVar(value=self.memory.get("name") or "Madhu")

        # Entry with rounded border effect (Frame bg #FFDAB9)

        entry_wrap=tk.Frame(card, bg="#FFDAB9", bd=0)

        entry_wrap.pack(fill="x", padx=28, pady=4)

        ent=tk.Entry(entry_wrap, textvariable=var, font=("Segoe UI", 11), justify="center", bg="white", fg="#5a3e2b", relief="flat", bd=0, insertbackground="#8B4513")

        ent.pack(fill="x", padx=2, pady=2, ipady=6)

        ent.select_range(0, tk.END); ent.focus_set()

        tk.Label(card, text="You can always change it later ♡", bg="white", fg="#C49A6C", font=("Segoe UI", 7)).pack(pady=(6,10))

        def confirm():

            name=var.get().strip() or "Madhu"

            self.kitten_name=name

            self.memory["name"]=name

            mem.save(self.memory)

            try:
                self.menu.entryconfig(4, label=f"Pet {name} <3")
            except: pass
            try:
                self.root.title(name)
            except: pass
            # also update tray icon title/menu if exists
            try:
                if hasattr(self, "tray_icon") and self.tray_icon:
                    self.tray_icon.title = f"{name} - Taskbar Kitten"
                    # tray menu will update next time via app.py callback, but force refresh
                    try:
                        self.tray_icon.update_menu()
                    except: pass
            except: pass
            print(f"Named kitten {name}")
            try:
                dlg.destroy()
            except: pass
            self._show_bubble(f"Hi, I'm {name}! <3", 5000)
            self._name_pending=False
            self._modal_open=False

        # pink button #FF8FA3 hover, paw emoji, shadow

        btn_shadow=tk.Frame(card, bg="#E6D5B8")

        btn_shadow.pack(pady=(8,4))

        btn=tk.Button(btn_shadow, text="🐾 That's my name ♡", command=confirm, bg="#FF8FA3", fg="white", activebackground="#FFA0B5", activeforeground="white", font=("Segoe UI", 10, "bold"), bd=0, padx=22, pady=7, relief="flat", cursor="hand2")

        btn.pack(padx=1, pady=1)

        def _on_enter(e):

            btn.configure(bg="#FF9AAE")

        def _on_leave(e):

            btn.configure(bg="#FF8FA3")

        btn.bind("<Enter>", _on_enter); btn.bind("<Leave>", _on_leave)

        # close X subtle

        close_lab=tk.Label(card, text="✕", bg="white", fg="#C49A6C", font=("Segoe UI", 8), cursor="hand2")

        close_lab.place(x=W-32-18, y=6, width=16, height=16)

        close_lab.bind("<Button-1>", lambda e: confirm())

        dlg.bind("<Return>", lambda e: confirm())

        dlg.bind("<Escape>", lambda e: confirm())

        try:

            dlg.protocol("WM_DELETE_WINDOW", confirm)

        except: pass

        try:

            dlg.grab_set()

        except: pass

        # gift pop fade-in + shadow

        try:

            dlg.attributes("-alpha", 0.0)

            def _fade(a=0.0):

                if a>=1.0:

                    try: dlg.attributes("-alpha", 1.0)

                    except: pass

                    return

                try: dlg.attributes("-alpha", a)

                except: pass

                dlg.after(16, lambda: _fade(a+0.12))

            _fade()

        except: pass



    def _show_bubble(self, text, ms=4000, priority=0):

        try:

            cur=getattr(self, "_bubble_prio", None)

            if cur is not None and cur > priority and self._food_bubble is not None and self._food_bubble.winfo_exists():

                return

            if getattr(self, "_food_bubble", None) and self._food_bubble and self._food_bubble.winfo_exists():

                try: self._food_bubble.destroy()

                except: pass

            bub=tk.Toplevel(self.root)

            bub.overrideredirect(True); bub.attributes("-topmost", True); bub.configure(bg="#FFF8DC")

            lab=tk.Label(bub, text=text, bg="#FFF8DC", fg="#5a3e2b", font=("Segoe UI",9,"bold"), padx=10, pady=6, bd=1, relief="solid", wraplength=280, justify="center")

            lab.pack()

            bub.update_idletasks()

            bw = bub.winfo_reqwidth(); bh = bub.winfo_reqheight()

            sw,sh = get_screen_size()

            x=self.root.winfo_x()+self.pet_w//2 - bw//2; y=self.root.winfo_y()-bh-6

            x=max(8, min(sw - bw - 8, x))

            y=max(8, y)

            bub.geometry(f"{bw}x{bh}+{x}+{y}")

            self._food_bubble=bub

            self._bubble_prio=priority

            if getattr(self, "_bubble_after", None):

                try: self.root.after_cancel(self._bubble_after)

                except: pass

                self._bubble_after=None

            self._bubble_after=self.root.after(ms, self._destroy_bubble)

        except: pass

    def _destroy_bubble(self):

        try:
            b=getattr(self,"_food_bubble",None)
            if b is not None and b.winfo_exists(): b.destroy()
        except Exception:
            pass
        self._food_bubble=None
        self._bubble_after=None
        self._bubble_prio=None



    def _play_meow(self, kind="meow"):
        try:
            if self.memory.get("is_muted"):
                return
            now=time.time()
            if now - getattr(self, "_last_sound_ts", 0) < 1.0:
                return
            self._last_sound_ts=now
            wav = self._base_dir() / "assets" / "meow.wav"
            if not wav.exists():
                _LOGGER.warning("meow.wav not bundled; sound disabled")
                return
            # winsound plays WAV natively (MP3 is not supported by PlaySound)
            import winsound
            winsound.PlaySound(str(wav), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as _e:
            _LOGGER.error("sound err: %s", _e)


    def toggle_mute(self):

        self.memory["is_muted"]=not self.memory.get("is_muted", False); mem.save(self.memory)

        state="muted 🔇" if self.memory["is_muted"] else "sound on 🔊"

        self._show_bubble(state, 2500)

        try:

            new_lab="Unmute 🔊" if self.memory["is_muted"] else "Mute 🔇"

            self.menu.entryconfig(9, label=new_lab)

        except: pass

        try:

            ts=getattr(self, "tray_state", None)

            if ts is not None: ts["muted"]=bool(self.memory.get("is_muted"))

            if getattr(self, "tray_icon", None) and self.tray_icon:

                self.tray_icon.update_menu()

        except Exception:

            pass

        print(f"mute toggle -> {state}")



    def _update_longest_apart(self):

        try:

            last=self.memory.get("lastSeen") or self.memory.get("lastPet") or self.memory.get("birth")

            if last:

                hrs=(datetime.datetime.now() - datetime.datetime.fromisoformat(last)).total_seconds()/3600

                if hrs > self.memory.get("longestApartHours",0) and hrs < 720:

                    self.memory["longestApartHours"]=round(hrs,1); mem.save(self.memory)

        except: pass



    def _check_milestones(self):

        try:

            c=self.memory.get("petCount",0)

            m=self.memory.get("milestones",[])

            fired_msgs=[]

            def trigger(mid, msg):

                if mid not in m:

                    m.append(mid); self.memory["milestones"]=m; mem.save(self.memory)

                    fired_msgs.append(msg)

            name=self.kitten_name or "kitten"

            if c==1: trigger("pet1", f"First pet! {name} loves you ♡")

            if c==10: trigger("pet10", f"10 pets already? Lucky {name} 🥰")

            if c==100: trigger("pet100", f"100 pets! {name} is so loved 💖")

            if c==500: trigger("pet500", f"500 pets! You're {name}'s favorite human ✨")

            # anniversary milestones

            birth=self.memory.get("birth")

            if birth:

                days=mem.days_since(birth)

                if days>=7 and "week1" not in m: trigger("week1", f"1 week together! {name} missed you ♡")

                if days>=30 and "month1" not in m: trigger("month1", f"1 month with {name}! 💌")

            if fired_msgs and not self.is_duck:

                self.animator.set_state("pet", big=False)

                self._play_meow()

                self._show_bubble("; ".join(fired_msgs), 6000, priority=1)

                # pop size burst (single, not per milestone)

                try:

                    ow,oh=self.pet_w,self.pet_h

                    pw,ph=int(ow*1.28), int(oh*1.28)

                    x=self.root.winfo_x(); y=self.root.winfo_y()-(ph-oh)

                    self.root.geometry(f"{pw}x{ph}+{x}+{y}")

                    self.root.after(320, lambda: self._restore_geom(ow,oh,0,(ph-oh)))

                except: pass

                self.root.after(5200, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self.animator.get_state()=="pet" and not self._is_dont_sleep() else None)

        except Exception as e:

            print("milestone err",e)



    def mood_on_startup(self):

        try:

            # days since last pet -> extra affectionate greeting

            last=self.memory.get("lastPet")

            d=mem.days_since(last) if last else 999

            hour=datetime.datetime.now().hour

            # time-of-day: night sleepier

            if 22 <= hour or hour < 6:

                # night: curled tighter, slower

                self.animator.set_state("sleeping", big=False, flip=False)

                print("🌙 night mode: sleepier")

            # long absence greeting

            if d >= 3 and not self.walk_active:

                print(f"🥺 missed you for {d} days -> big greeting")

                self._startup_greeted=True

                self._show_bubble(f"Missed you! 💌", 5000)

                self.animator.set_state("pet", big=self.is_duck)

                self._play_meow()

                self.root.after(4800, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

                # also heart burst

            elif d==1 and not self.walk_active:

                self._startup_greeted=True

                self._show_bubble(f"Hi again ♡", 3200)

        except: pass



    def seasonal_check(self):

        try:

            now=datetime.datetime.now()

            m,d=now.month, now.day

            msg=None

            if m==12 and 20 <= d <= 26: msg="Merry Christmas! 🎄"

            elif m==2 and 13 <= d <= 15: msg="Happy Valentine's! 💘"

            elif m==10 and 30 <= d <= 31: msg="Spooky meow 🎃"

            # her birthday hardcoded? ask later

            if msg and random.random()<0.15:

                key="season_{0}_{1}".format(now.year, msg)

                if self.memory.get(key) != msg and self._ready_for_transition():

                    self.memory[key]=msg; mem.save(self.memory)

                    self._show_bubble(msg, 5000, priority=1)

        except: pass

        self.root.after(3600*1000, self.seasonal_check)




    def wish_11_check(self):
        try:
            now=__import__('datetime').datetime.now()
            if (now.hour==11 or now.hour==23) and now.minute==11:
                slot=f"{now.date()}_{now.hour}"
                if self._last_wish_slot != slot:
                    self._last_wish_slot=slot
                    ampm="AM" if now.hour==11 else "PM"
                    self._show_bubble(f"11:11 {ampm} -- make a wish", 7000, priority=1)
                    self._play_meow("chirp")
                    print(f"11:11 wish {ampm}")
        except: pass
        self.root.after(20000, self.wish_11_check)

    def waiting_check(self):

        try:

            # quiet waiting state during long absences: sit by edge looking toward Start

            idle = time.time() - self.last_activity

            if idle > 180 and not self.is_duck and not self.walk_active and not self.is_petting and self.animator.get_state()=="sleeping":

                # 120s true idle -> waiting by left edge looking to Start button

                sw,_=get_screen_size()

                # drift to favorite spot if exists, else edge 12px

                fav=self.memory.get("favorite_spots",[])

                if fav:

                    # most common fav

                    from collections import Counter

                    target=Counter(fav).most_common(1)[0][0]

                    x = max(12, min(sw-80, int(target)))

                else:

                    x=14

                # fix drift: don't teleport while sleeping, just bubble + watch
                self.animator.set_state("watching", big=False, flip=False)

                self._show_bubble("waiting for you…", 3800)

                self.last_activity=time.time()

                print("waiting bubble only - no drift while sleeping")

                self.root.after(6000, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

        except: pass

        self.root.after(45000, self.waiting_check)



    def _record_favorite(self, x):

        try:

            spots=self.memory.get("favorite_spots",[])

            spots.append(int(x))

            if len(spots)>60: spots=spots[-60:]

            self.memory["favorite_spots"]=spots

            self.memory["pos_x"]=int(x)

            mem.save(self.memory)

        except: pass



    # --- living animation helpers ---

    def _notice_beat(self, callback, ms=280):

        # ear flick / eye crack before major transition

        try:

            if getattr(self, "_notice_after", None):

                try: self.root.after_cancel(self._notice_after)

                except: pass

            self.animator.set_state("blink", big=self.is_duck)

            self._notice_after=self.root.after(ms, lambda: callback())

        except:

            callback()



    def trigger_luck(self):

        # pause any in-progress walk so the support-bounce doesn't fight the walk

        if self.walk_active:

            self.walk_active=False

            self._walk_target=None

            if hasattr(self,'_walk_steps'): self._walk_steps=0

            if hasattr(self,'_walk_bounces'): self._walk_bounces=0

            try:

                if self._walk_after:

                    self.root.after_cancel(self._walk_after); self._walk_after=None

            except: pass

        try: idx=int(self.memory.get("luck_message_index",0) or 0)

        except: idx=0

        msgs=self.LUCK_MESSAGES

        msg=msgs[idx % len(msgs)]

        self.memory["luck_message_index"]=(idx+1)%len(msgs); mem.save(self.memory)

        self._notice_beat(lambda: self._show_bubble(msg, 5000, priority=1))

        self.animator.set_state("pet", big=self.is_duck)

        # determined supportive bounce

        try:

            ow,oh=self.pet_w,self.pet_h; pw,ph=int(ow*1.22),int(oh*1.22)

            x=self.root.winfo_x(); y=self.root.winfo_y()-(ph-oh)

            self.root.geometry(f"{pw}x{ph}+{x}+{y}")

            self.root.after(260, lambda: self._restore_geom(ow,oh,0,(ph-oh)))

        except: pass

        self._play_meow()

        self.root.after(4500, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

        print(f"Wish me luck: {msg}")



    def glance_check(self):

        try:

            if not self.is_duck and not self.walk_active and not self.is_petting and self.animator.get_state() in ("sleeping","watching"):

                if time.time()-self._last_glance > random.randint(18,35):

                    # mouse proximity

                    pt=ctypes.wintypes.POINT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))

                    kx=self.root.winfo_x()+self.pet_w//2; ky=self.root.winfo_y()+self.pet_h//2

                    dx=pt.x - kx; dy=pt.y - ky

                    dist=(dx*dx+dy*dy)**0.5

                    # glance toward cursor if near (<280px) or clock (taskbar right) rarely

                    if dist<320 and random.random()<0.45:

                        self._last_glance=time.time()

                        # brief eye/head glance: quick blink/watch

                        self.animator.set_state("watching", big=False, flip=(dx<0))

                        self.root.after(900, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

                        print("👀 glance at cursor")

                    elif random.random()<0.06:

                        # glance at clock

                        self._last_glance=time.time()

                        self.animator.set_state("blink", big=False, flip=False)

                        self.root.after(600, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

        except: pass

        self.root.after(1700, self.glance_check)



    def _check_long_absence(self):

        try:

            last=self.memory.get("lastSeen") or self.memory.get("lastPet")

            hrs=mem.hours_since(last)

            idle_h=self._get_last_input_idle()/3600

            if hrs>=2 or idle_h>=2:

                if not self._long_absence_done and self.animator.get_state()=="sleeping" and not self.is_duck and not self.walk_active:

                    self._long_absence_done=True

                    self.animator.set_state("blink", big=False, flip=False)

                    self.root.after(800, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

                    if not getattr(self, "_startup_greeted", False):

                        self._show_bubble("missed you… ears down 🥺", 5000)

                    print("💤 long absence: missing you state")

        except: pass

        self.root.after(60000, self._check_long_absence)



    def _welcome_back(self):

        if self._long_absence_done:

            self._long_absence_done=False

            # fast ears-up, hop, extra happy

            self._show_bubble("you're back! hop! 💖", 4500)

            if not self.is_duck:

                self.animator.set_state("waking", big=False, flip=False)

                try:

                    ow,oh=self.pet_w,self.pet_h; pw,ph=int(ow*1.25),int(oh*1.25)

                    x=self.root.winfo_x(); y=self.root.winfo_y()-(ph-oh)-6

                    self.root.geometry(f"{pw}x{ph}+{x}+{y}")

                    self.root.after(180, lambda: self._restore_geom(ow,oh,0,(ph-oh)+6))

                    self.root.after(350, lambda: self._restore_geom(pw,ph,0,-(ph-oh)-6))

                    self.root.after(530, lambda: self._restore_geom(ow,oh,0,(ph-oh)+6))

                except: pass

                self.root.after(1200, lambda: self.animator.set_state("pet", big=False, flip=False) if not self.is_duck else None)

                self.root.after(3000, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self._ready_for_transition() and not self._is_dont_sleep() else None)

                self._play_meow()

                self._startup_greeted=True

            print("welcome back hop!")



    def show_scrapbook(self):

        self._update_longest_apart()

        n=self.kitten_name or "Madhu"

        birth=self.memory.get("birth")

        try:

            bd=datetime.datetime.fromisoformat(birth) if birth else datetime.datetime.now()

            days=(datetime.datetime.now()-bd).days

            first=bd.strftime("%b %d, %Y")

        except:

            days=0; first="today"

        pets=self.memory.get("petCount",0)

        longest=self.memory.get("longestApartHours",0)

        fav=self.memory.get("favorite_spots",[])

        fav_str = f"{int(sum(fav)/len(fav))}px" if fav else "still exploring"

        # warm popup

        win=tk.Toplevel(self.root)

        win.title(f"Our story with {n} 📖")

        win.geometry(f"360x320+{self.root.winfo_screenwidth()//2-180}+{self.root.winfo_screenheight()//2-160}")

        win.configure(bg="#FFF8DC")

        win.attributes("-topmost", True)

        tk.Label(win, text=f"Our story with {n} 📖", bg="#FFF8DC", fg="#8B4513", font=("Segoe UI",13,"bold")).pack(pady=12)

        tk.Label(win, text=f"First met: {first}  •  {days} days together", bg="#FFF8DC", fg="#5a3e2b", font=("Segoe UI",9)).pack()

        tk.Label(win, text=f"Times petted: {pets}  •  Hearts given: {pets} 💖", bg="#FFF8DC", fg="#5a3e2b", font=("Segoe UI",10)).pack(pady=6)

        tk.Label(win, text=f"Longest time apart: {longest}h", bg="#FFF8DC", fg="#5a3e2b", font=("Segoe UI",9)).pack()

        tk.Label(win, text=f"Favorite spot: {fav_str} on the taskbar", bg="#FFF8DC", fg="#5a3e2b", font=("Segoe UI",9)).pack()

        tk.Label(win, text=f"Milestones: {', '.join(self.memory.get('milestones',[])) or 'just beginning…'}", bg="#FFF8DC", fg="#8B4513", font=("Segoe UI",8), wraplength=320, justify="center").pack(pady=8)

        tk.Label(win, text="She remembers where she sleeps, and misses you when you're away. ♡", bg="#FFF8DC", fg="#8B4513", font=("Segoe UI",9,"italic"), wraplength=320, justify="center").pack(pady=10)

        tk.Button(win, text="♡ close", command=win.destroy, bg="#FFB6C1", fg="#5a3e2b", bd=0, padx=12, pady=4).pack(pady=8)




    # --- Journal for Gayathree (book, never lost) ---
    def _journal_path(self):
        import sys as _sys, os as _os
        if getattr(_sys, 'frozen', False):
            d=pathlib.Path(_os.getenv("APPDATA", str(pathlib.Path.home()))) / "TaskbarKitten"
        else:
            d=pathlib.Path(__file__).parent.parent / "assets"
        d.mkdir(parents=True, exist_ok=True)
        jp=d / "journal.json"
        if not getattr(self, "_journal_migrated", False):
            self._journal_migrated=True
            self._migrate_legacy_journal(jp, d/"journal_photos")
        return jp

    def _migrate_legacy_journal(self, jp, photos_dir):
        """Fold the dev-tree assets/journal.json (+ photos) into the active store
        exactly once. Existing active entries always win on conflict."""
        import json
        old=pathlib.Path(__file__).parent.parent / "assets" / "journal.json"
        if not old.exists():
            self._merge_legacy_photos(photos_dir)
            return
        changed=False
        try:
            old_data=json.loads(old.read_text(encoding='utf-8'))
        except Exception:
            old_data={}
        new_data={}
        if jp.exists():
            try:
                new_data=json.loads(jp.read_text(encoding='utf-8'))
            except Exception:
                new_data={}
        elif old_data:
            try:
                jp.write_text(json.dumps(old_data, ensure_ascii=False, indent=2), encoding='utf-8')
            except Exception:
                pass
            self._merge_legacy_photos(photos_dir)
            return
        if jp.exists() and old_data:
            for k,v in old_data.items():
                if k not in new_data:
                    new_data[k]=v; changed=True
                elif v and isinstance(v, dict) and isinstance(new_data[k], dict):
                    # keep the richer side field-by-field, never drop old fields
                    merged=dict(new_data[k])
                    for fk,fv in v.items():
                        merged.setdefault(fk, fv)
                    if merged!=new_data[k]:
                        new_data[k]=merged; changed=True
            if changed:
                self._save_journal(new_data)
        self._merge_legacy_photos(photos_dir)

    def _merge_legacy_photos(self, photos_dir):
        old_dir=pathlib.Path(__file__).parent.parent / "assets" / "journal_photos"
        if not old_dir.exists():
            return
        try:
            old_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        try:
            photos_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            for f in old_dir.iterdir():
                if not f.is_file():
                    continue
                dest=photos_dir/f.name
                if not dest.exists():
                    try: shutil.copy2(f, dest)
                    except Exception: pass
        except Exception as _e:
            _LOGGER.error("photos migration: %s", _e)

    # ---- password lock + encryption (Fernet via cryptography) ----
    def _journal_lock_path(self):
        return self._journal_path().with_suffix(".lock")

    def _journal_enc_path(self):
        return self._journal_path().with_suffix(".enc")

    def _journal_locked(self):
        return self._journal_lock_path().exists()

    def _journal_unlock(self, password):
        import hashlib, hmac, json
        try:
            lock=self._journal_lock_path().read_text(encoding="utf-8")
            data=json.loads(lock)
            salt=bytes.fromhex(data["salt"])
            want=bytes.fromhex(data["check"])
            key=hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
            if not hmac.compare_digest(key, want):
                return False
            self._journal_key=self._journal_key_from_key(key)
            self._journal_unlocked=True
            return True
        except: return False

    def _journal_key_from_key(self, key):
        import base64
        return base64.urlsafe_b64encode(key)

    def _journal_encrypt(self, data):
        from cryptography.fernet import Fernet
        f=Fernet(self._journal_key)
        import json
        return f.encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _journal_decrypt(self, blob):
        from cryptography.fernet import Fernet
        f=Fernet(self._journal_key)
        import json
        return json.loads(f.decrypt(blob).decode("utf-8"))

    def _journal_set_password(self, password):
        import hashlib, json, base64, secrets
        if len(password)<6:
            return False
        salt=secrets.token_bytes(16)
        key=hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
        lock=self._journal_lock_path()
        enc=self._journal_enc_path()
        jp=self._journal_path()
        data=self._load_journal()
        if lock.exists():
            # changing password while unlocked: read existing enc/plaintext before relocking
            if getattr(self, "_journal_key", None) and enc.exists():
                try: data=self._journal_decrypt(enc.read_bytes())
                except Exception as _e:
                    _LOGGER.error("relock: could not decrypt existing journal; abort: %s", _e)
                    return False
            else:
                return False
        key_b64=base64.urlsafe_b64encode(key)
        from cryptography.fernet import Fernet
        f=Fernet(key_b64)
        blob=f.encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        # atomic enc write BEFORE the lock file appears
        import tempfile, os
        tmp=pathlib.Path(str(enc)+".tmp")
        try:
            tmp.write_bytes(blob)
            tmp.replace(enc)
        except Exception as _e:
            _LOGGER.error("relock: enc write failed: %s", _e)
            return False
        lock.write_text(json.dumps({"salt":salt.hex(),"check":key.hex()}), encoding="utf-8")
        # remove plaintext + temps
        for p in (jp, jp.with_suffix(".bak"), jp.with_suffix(".tmp")):
            try:
                if p.exists(): p.unlink()
            except Exception:
                pass
        # cache key for this session without prompting again
        self._journal_key=key_b64
        self._journal_unlocked=True
        return True

    def _journal_remove_password(self):
        """Unlock the journal. Returns True only when the plaintext made it to
        disk AND round-tripped; never deletes the encrypted copies otherwise.
        (The old code removed .lock/.enc/.enc.bak even when decryption failed,
        which permanently destroyed the book. Do NOT regress to that.)"""
        import json
        enc=self._journal_enc_path()
        jp=self._journal_path()
        if not (enc.exists() and getattr(self, "_journal_key", None)):
            return False
        try:
            data=self._journal_decrypt(enc.read_bytes())
            text=json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            # write plaintext directly (must bypass _save_journal: still locked here)
            tmp=jp.with_suffix('.tmp')
            tmp.write_text(text, encoding='utf-8')
            tmp.replace(jp)
            # round-trip verify BEFORE touching any encrypted copy
            verify=json.loads(jp.read_text(encoding='utf-8'))
            if not isinstance(verify, dict):
                raise ValueError("plaintext round-trip produced a non-dict")
            # now it is safe to drop the lock + encrypted copies
            for p in (self._journal_lock_path(), enc, pathlib.Path(str(enc)+".bak")):
                try:
                    if p.exists(): p.unlink()
                except Exception:
                    pass
        except Exception as _e:
            _LOGGER.error("unlock/remove-password aborted (nothing deleted): %s", _e)
            return False
        self._journal_key=None
        self._journal_unlocked=False
        return True

    def _load_journal(self):
        import json
        try:
            if self._journal_locked():
                if getattr(self, "_journal_key", None) and self._journal_enc_path().exists():
                    try:
                        return self._journal_decrypt(self._journal_enc_path().read_bytes())
                    except Exception as _e:
                        # try the .enc.bak safety copy before giving up
                        encbak=pathlib.Path(str(self._journal_enc_path())+".bak")
                        if encbak.exists():
                            try: return self._journal_decrypt(encbak.read_bytes())
                            except Exception: pass
                        _LOGGER.error("journal enc decrypt failed: %s", _e)
                        return {}
                return {}
            if self._journal_path().exists():
                try:
                    return json.loads(self._journal_path().read_text(encoding='utf-8'))
                except Exception:
                    # corrupt plaintext: recover from backup, quarantine, and stop autosaving
                    bak=self._journal_path().with_suffix('.bak')
                    if bak.exists():
                        try:
                            recovered=json.loads(bak.read_text(encoding='utf-8'))
                            # repair main atomically (was a plain write before)
                            jptmp=self._journal_path().with_suffix('.tmp')
                            jptmp.write_text(json.dumps(recovered, ensure_ascii=False, indent=2), encoding='utf-8')
                            jptmp.replace(self._journal_path())
                            return recovered
                        except Exception:
                            pass
                    try:
                        self._journal_path().rename(pathlib.Path(str(self._journal_path())+".corrupt."+str(int(time.time()))))
                    except Exception:
                        pass
                    self._journal_read_error=True
                    _LOGGER.error("journal plaintext corrupt; quarantined + marked read-error")
                    return {}
        except Exception as _e:
            _LOGGER.error("journal load failed: %s", _e)
        return {}

    def _save_journal(self, data):
        import json
        if getattr(self, "_journal_read_error", False):
            _LOGGER.error("journal save skipped: previous load was corrupt (recovered/quarantined)")
            return
        if self._journal_locked():
            if not getattr(self, "_journal_key", None):
                _LOGGER.error("journal save skipped: locked but no session key")
                return
            try:
                enc=self._journal_enc_path()
                blob=self._journal_encrypt(data)
                tmp=pathlib.Path(str(enc)+".tmp")
                tmp.write_bytes(blob)
                if enc.exists():
                    try:
                        pathlib.Path(str(enc)+".bak").write_bytes(enc.read_bytes())
                    except Exception:
                        pass
                tmp.replace(enc)
            except Exception as _e:
                _LOGGER.error("journal enc save failed: %s", _e)
            return
        p=self._journal_path()
        try:
            # atomic + backup, never lost
            tmp=p.with_suffix('.tmp')
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
            # rotate .bak ONLY when the current main parses as valid JSON; a
            # corrupt main must never clobber the one good backup
            if p.exists():
                try:
                    prev=p.read_text(encoding='utf-8')
                    json.loads(prev)
                    (p.with_suffix('.bak')).write_text(prev, encoding='utf-8', newline='\n')
                except Exception:
                    pass
            tmp.replace(p)
        except Exception as _e:
            # no non-atomic fallback write here: that could corrupt the file it
            # was meant to preserve
            _LOGGER.error("journal save failed (journal untouched): %s", _e)
            try:
                if tmp.exists(): tmp.unlink()
            except Exception:
                pass

    def _entry_text(self, e):
        s=self._entry_seq(e)
        if s is not None: return s[0] or ""
        return e if isinstance(e, str) else (e or {}).get("text", "")

    def _entry_fmt(self, e):
        if isinstance(e, str): return []
        s=self._entry_seq(e)
        if s is not None: return []
        return list((e or {}).get("fmt", []) or [])

    def _capture_fmt(self, txt):
        """Read the Text widget's tags into a compact, persistable list.
        fmt entries -> (start_char, end_char, kind) where kind is
        'b','i','u','h','c:RRGGBB','l:url'. Char offsets are flat character
        positions in the plain text."""
        if txt is None: return []
        out=[]
        def flat(idx):
            return len(txt.get("1.0", idx))
        # dump text with tags
        try:
            queue={}
            for key, val, idx in txt.dump("1.0", tk.END, tag=True):
                if key in ("tagstart","tagon"): queue[val]=idx
                elif key in ("tagend","tagoff") and val in queue:
                    out.append((flat(queue[val]), flat(idx), val))
                    queue.pop(val, None)
        except: pass
        mapped=[]
        for s,e,t in out:
            if t in ("bold","italic","underline","heading"):
                mapped.append((s,e,{"bold":"b","italic":"i","underline":"u","heading":"h"}[t]))
            elif t=="todo_done":
                mapped.append((s,e,"td"))
            elif t.startswith("color_"):
                mapped.append((s,e,"c:"+t.replace("color_","")))
            elif t.startswith("link_"):
                url=txt._links.get(t,"")
                if url: mapped.append((s,e,"l:"+url))
        mapped.sort(key=lambda x:(x[0],x[1]))
        return mapped

    def _apply_fmt(self, txt, fmt):
        """Re-apply persisted formatting to a freshly-loaded Text widget."""
        if not fmt: return
        def to_idx(sought):
            # off is a *character* offset (txt.get counts only text; embedded
            # images occupy an index but not a char), so translate by walking
            # the widget dump instead of using the naive "chars" index math.
            if sought<=0:
                return "1.0"
            acc=0
            try:
                for item in txt.dump("1.0", tk.END):
                    kind, val, idx = item
                    if kind=="text":
                        n=len(val)
                        if acc==sought:
                            return idx
                        if acc < sought <= acc+n:
                            return txt.index(f"{idx}+{sought-acc}c")
                        acc+=n
                return txt.index(tk.END)
            except Exception:
                try: return txt.index(f"1.0 + {sought} chars")
                except Exception: return "1.0"
        for s,e,kind in fmt:
            if not kind: continue
            try:
                si=to_idx(s); ei=to_idx(e)
            except: continue
            if kind=="b": txt.tag_add("bold", si, ei)
            elif kind=="i": txt.tag_add("italic", si, ei)
            elif kind=="u": txt.tag_add("underline", si, ei)
            elif kind=="h": txt.tag_add("heading", si, ei)
            elif kind=="td":
                try:
                    if txt.get(si, f"{si}+1c")=="☑": si=to_idx(s+2)
                except: pass
                txt.tag_add("todo_done", si, ei)
            elif kind.startswith("c:"):
                hexc=kind[2:]
                t=f"color_{hexc}"
                txt.tag_configure(t, foreground="#"+hexc)
                txt.tag_add(t, si, ei)
            elif kind.startswith("l:"):
                url=kind[2:]
                t=f"link_{len(txt.tag_names())}"
                txt.tag_configure(t, foreground="#0066CC", underline=True)
                txt.tag_add(t, si, ei)
                if not hasattr(txt, "_links"): txt._links={}
                txt._links[t]=url
                txt.tag_bind(t, "<Button-1>", lambda e, u=url: self._open_link(u))

    def _entry_seq(self, e):
        """Return the 6 legacy fields when e is a list/tuple (old format)."""
        if isinstance(e, (list, tuple)) and len(e) >= 6:
            return e
        return None

    def _entry_mood(self, e):
        s=self._entry_seq(e)
        if s is not None: return s[1] or ""
        return "" if isinstance(e, str) else (e or {}).get("mood", "")

    def _entry_rating(self, e):
        s=self._entry_seq(e)
        if s is not None: return int(s[2] or 0)
        return 0 if isinstance(e, str) else int((e or {}).get("rating", 0) or 0)

    def _entry_tags(self, e):
        s=self._entry_seq(e)
        if s is not None: return list(s[3] or [])
        return [] if isinstance(e, str) else list((e or {}).get("tags", []) or [])

    def _entry_photos(self, e):
        s=self._entry_seq(e)
        if s is not None: return list(s[4] or [])
        return [] if isinstance(e, str) else list((e or {}).get("photos", []) or [])

    def _entry_populated(self, e):
        s=self._entry_seq(e)
        if s is not None: return bool(s[0] or s[1] or s[2] or s[3] or s[4])
        if isinstance(e, str): return bool(e.strip())
        return bool((e or {}).get("text","").strip() or (e or {}).get("mood") or int((e or {}).get("rating",0) or 0) or (e or {}).get("tags") or (e or {}).get("photos"))

    def _journal_photos_dir(self):
        d=self._journal_path().parent/"journal_photos"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _attach_photos(self, date_key):
        """Pick one or more photos; copy them into Madhu's book folder. Returns names."""
        import tkinter.filedialog as fd, datetime
        top=None
        was_top=False
        try:
            for w in self.root.winfo_children():
                if isinstance(w, tk.Toplevel) and w.title().startswith("Gayathree"):
                    top=w; break
            if top is not None:
                try: was_top=bool(top.attributes("-topmost"))
                except: was_top=False
                if was_top: top.attributes("-topmost", False)
            files=fd.askopenfilenames(initialdir=str(pathlib.Path.home() / "Pictures"),
                                      title="Pick a photo for Madhu's book",
                                      filetypes=[("Images","*.png *.jpg *.jpeg *.gif *.bmp"),("All files","*.*")])
            if top is not None and was_top:
                try: top.attributes("-topmost", True)
                except: pass
        except:
            if top is not None and was_top:
                try: top.attributes("-topmost", True)
                except: pass
            return []
        if not files: return []
        from PIL import Image
        added=[]
        for f in list(files)[:6]:
            try:
                im=Image.open(f)
                im.thumbnail((460,460), Image.LANCZOS)
                name=datetime.datetime.now().strftime("%H%M%S_%f")+"_"+str(pathlib.Path(f).stem)[:30].replace(" ","_").replace(".","_")+".png"
                dest=self._journal_photos_dir()/name
                im.convert("RGB").save(dest, "PNG")
                added.append(dest.name)
            except: pass
        return added

    def _journal_streak(self, data):
        import datetime
        try:
            written=sorted((d for d,v in data.items() if self._entry_text(v).strip()), reverse=True)
            if not written: return 0
            today=datetime.date.today().isoformat()
            # if today is unwritten but yesterday has a page, the streak is
            # still alive (pending); old code read a hard 0 until the save
            start=today if today in written else (datetime.date.today()-datetime.timedelta(days=1)).isoformat()
            streak=0
            cur=datetime.date.fromisoformat(start)
            for _ in range(max(1, len(written)+2)):
                if cur.isoformat() in written:
                    streak+=1
                    cur-=datetime.timedelta(days=1)
                else:
                    break
            return streak
        except: return 0

    def show_journal(self):
        import datetime, json
        jw=getattr(self, "_journal_win", None)
        if jw is not None:
            try:
                if jw.winfo_exists():
                    jw.deiconify(); jw.lift(); jw.focus_force(); return
            except: pass
        # ---- password gate ----
        if self._journal_locked() and not getattr(self, "_journal_key", None):
            gate=tk.Toplevel(self.root)
            gate.title("Madhu's Journal 🔒")
            gw,gh=360,210
            gate.geometry(f"{gw}x{gh}+{gate.winfo_screenwidth()//2-gw//2}+{max(0,gate.winfo_screenheight()//2-gh//2)}")
            gate.configure(bg="#FDF6E3")
            gate.attributes("-topmost", True)
            tk.Label(gate, text="🔒  Madhu guards this book", bg="#FDF6E3", fg="#6B4C3B", font=("Georgia", 13, "bold")).pack(pady=(18,2))
            tk.Label(gate, text="whisper the password, Gayathree", bg="#FDF6E3", fg="#8B7355", font=("Segoe UI", 9, "italic")).pack()
            pw_var=tk.StringVar()
            pw=tk.Entry(gate, textvariable=pw_var, show="●", bg="white", fg="#3a2a1a", font=("Segoe UI", 11), justify="center", width=20)
            pw.pack(pady=14, ipady=3)
            status=tk.Label(gate, text="", bg="#FDF6E3", fg="#a05a5a", font=("Segoe UI", 8))
            status.pack()
            def go(_=None):
                if self._journal_unlock(pw_var.get()):
                    self._unlock_fails=0
                    gate.destroy()
                    self._open_journal(win_from=self.root)
                else:
                    self._unlock_fails+=1
                    if self._unlock_fails>=5:
                        status.configure(text="too many tries… closing ♡")
                        gate.after(600, gate.destroy)
                        return
                    status.configure(text=f"wrong password — {5-self._unlock_fails} tries left ♡")
                    pw.delete(0, tk.END)
            pw.bind("<Return>", go)
            tk.Button(gate, text="Unlock ♡", command=go, bg="#FF8FA3", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=18, pady=5, cursor="hand2").pack(pady=6)
            gate.focus_force(); pw.focus_set()
            return
        self._open_journal(win_from=self.root)

    def _open_journal(self, win_from=None):
        import datetime, json
        win=tk.Toplevel(self.root)
        self._journal_win=win
        self._journal_applied_date=None
        win.title("Gayathree\'s Journal 📖 — Madhu's Keepsake")
        # clamp to the logical screen: a hardcoded 860x600 could clip the Save/
        # tools rows on 125%+ scaled or small panels (bottom of the window DOA)
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        W=min(860, max(640, sw-60))
        H=min(600, max(360, sh-80))
        win.geometry(f"{W}x{H}+{sw//2-W//2}+{max(0,sh//2-H//2)}")
        win.configure(bg="#FDF6E3")
        win.attributes("-topmost", True)
        # book canvas with warm parchment + soft shadow + linen texture dots
        canvas=tk.Canvas(win, width=W, height=H, bg="#FDF6E3", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        # --- responsive book re-layout ---
        _redraw_job={"id":None}
        _decodata={"paw":None}
        _frames_ok={"ok":False}
        def _redecorate(cw, ch):
            cw=max(cw, 280); ch=max(ch, 200)   # degenerate sizes -> rounded-rect errors
            canvas.delete("deco")
            dark = getattr(self, "_journal_dark_cur", False)
            if dark:
                bevel, step, page, spine, dots, gold = "#342b1f", "#382f22", "#2e261c", "#4a3c2e", "#c9b796", "#e8c474"
            else:
                bevel, step, page, spine, dots, gold = "#E8DCC8", "#E6D5B8", "#FFFCF7", "#D8C4A6", "#C9A86A", "#C9A86A"
            def _rr(x1,y1,x2,y2,r, **kw): pts=[x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]; return canvas.create_polygon(pts, smooth=True, **kw)
            _rr(18,18,cw-12,ch-12,22, fill=bevel, outline="", tags="deco")
            _rr(14,14,cw-14,ch-14,20, fill=step, outline="", tags="deco")
            inner=_rr(8,8,cw-8,ch-8,20, fill=page, outline=gold, width=2, tags="deco")
            canvas.create_line(cw//2, 28, cw//2, ch-28, fill=spine, width=3, tags="deco")
            for y in range(40, ch-40, 18): canvas.create_oval(cw//2-1.5, y-1.5, cw//2+1.5, y+1.5, fill=dots, outline="", tags="deco")
            canvas.create_line(cw//2-90, 62, cw//2+90, 62, fill=step, width=1, tags="deco")
            canvas.create_text(cw//2, 62, text=" ✦ ", fill=gold, font=("Segoe UI", 7), tags="deco")
            paw=_decodata.get("paw")
            if paw is not None: canvas.create_image(cw-48, 36, image=paw, tags="deco")
            return inner
        def _relayout(cw, ch):
            if not _frames_ok["ok"]:
                return
            cw=max(cw, 320); ch=max(ch, 220)
            page_w=max(248, cw//2 - 38)   # both pages grow equally (book symmetry)
            ph=max(40, ch-108)            # never <=0: a negative height collapses
                                          # the frame to a 1px black/dark sliver
            # place-managed widgets do NOT repaint when the parent resizes: they
            # keep a stale (pure-black) backing store. place_forget + place every
            # relayout so Tk invalidates and redraws the whole subtree.
            try:
                left.place_forget(); left.place(x=22, y=72, width=page_w, height=ph)
                right.place_forget(); right.place(x=cw//2+16, y=72, width=cw//2-38, height=ph)
                # header labels are placed once at open but never re-centered: move
                # them too (re-place forces a repaint and keeps them centered)
                _win_labels[0].place_forget(); _win_labels[0].place(x=cw//2, y=22, anchor="n")
                _win_labels[1].place_forget(); _win_labels[1].place(x=cw//2, y=44, anchor="n")
                win.update_idletasks()
            except Exception:
                pass
        def _apply_redraw(cw, ch):
            # guard: an exception here used to die invisibly inside the after()
            # lambda, leaving the left panel at a stale/black geometry forever
            try:
                _redecorate(cw, ch)
                _relayout(cw, ch)
            except Exception as _e:
                _LOGGER.error("journal re-layout failed: %s", _e)
        def _schedule_redraw(e=None):
            if _redraw_job["id"]:
                try: win.after_cancel(_redraw_job["id"])
                except: pass
            cw=win.winfo_width(); ch=win.winfo_height()
            if cw<=1 or ch<=1: cw,ch=W,H
            _redraw_job["id"]=win.after(80, lambda: _apply_redraw(cw,ch))
        win.bind("<Configure>", _schedule_redraw)
        # --- initial decorations ---
        try:
            from PIL import Image as _PILImage, ImageTk as _PILTK
            import pathlib as _pl
            pth=self._base_dir()/ "assets" / "sprites" / "frame_4.png"
            if not pth.exists():
                pth=_pl.Path(__file__).parent.parent / "assets" / "sprites" / "frame_4.png"
            im=_PILImage.open(pth).convert("RGBA").resize((44,44), _PILImage.LANCZOS)
            tkp=_PILTK.PhotoImage(im)
            _decodata["paw"]=tkp; win._paw=tkp
        except: pass
        _redecorate(W,H)
        # header with divider flourishes (stored for relayout)
        _win_labels=[tk.Label(win, text="Gayathree \'s Journal", bg="#FFFCF7", fg="#6B4C3B", font=("Georgia", 16, "bold")),
                     tk.Label(win, text="— a little book Madhu keeps for you —", bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 8, "italic"))]
        _win_labels[0].place(x=W//2, y=22, anchor="n")
        _win_labels[1].place(x=W//2, y=44, anchor="n")
        # left page — calendar & streak
        left=tk.Frame(win, bg="#FFFCF7", bd=0)
        left.place(x=22, y=72, width=248, height=H-108)
        tk.Label(left, text="📅  Days with Madhu", bg="#FFFCF7", fg="#6B4C3B", font=("Segoe UI", 9, "bold")).pack(pady=(6,2))
        # streak
        data=self._load_journal()
        if getattr(self, "_journal_read_error", False):
            # a previous load found the file corrupt and quarantined it: tell the
            # user exactly once, then clear the flag so this fresh book can save
            # again (saves were previously silently voided for the whole session)
            self._journal_read_error=False
            self._journal_read_error_shown=True
            try:
                import tkinter.messagebox as _mb
                _mb.showwarning(
                    "Madhu found a problem in your book",
                    "A previous journal file was damaged, so Madhu parked it as a "
                    "'.corrupt' file and opened a fresh book. Your old words are "
                    "still on disk.\n\nNothing has been deleted.", parent=win)
            except Exception:
                pass
        filled=len([v for v in data.values() if self._entry_populated(v)])
        streak=self._journal_streak(data)
        tk.Label(left, text=f"{filled} pages  •  {streak} day streak 🔥", bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 7)).pack()
        # search box
        search_var=tk.StringVar()
        search_frame=tk.Frame(left, bg="#FFFCF7")
        search_frame.pack(fill="x", padx=8, pady=(6,0))
        tk.Label(search_frame, text="🔍", bg="#FFFCF7", fg="#C9A86A", font=("Segoe UI", 9)).pack(side="left")
        search_entry=tk.Entry(search_frame, textvariable=search_var, bg="white", fg="#5a3e2b",
                              insertbackground="#6B4C3B", font=("Segoe UI", 9), relief="solid", bd=1, highlightthickness=0)
        search_entry.pack(side="left", fill="x", expand=True, padx=(4,0), ipady=2)
        def clear_search():
            search_var.set("")
            _full_refresh("")
        tk.Button(search_frame, text="✕", command=clear_search, bd=0, bg="#FFFCF7", fg="#C9A86A",
                  activebackground="#FFDAB9", font=("Segoe UI", 8), cursor="hand2").pack(side="left", padx=(3,0))
        lb_frame=tk.Frame(left, bg="#FFFCF7")
        lb_frame.pack(fill="both", expand=True, padx=8, pady=8)
        # subtle paper lines behind list
        lb=tk.Listbox(lb_frame, bg="white", fg="#5a3e2b", font=("Segoe UI", 9), bd=1, relief="solid", highlightthickness=0, activestyle="none", selectbackground="#FFDAB9", selectforeground="#5a3e2b")
        lb.pack(fill="both", expand=True, ipady=4)
        # stats button
        tk.Button(left, text="📊  Calendar & Madhu's insights",
                  command=lambda: self._show_stats(win, data, dark=getattr(self,"_journal_dark_cur",False),
                                                   on_day=lambda ds: _goto_date(ds)),
                  bg="#EFE3CF", fg="#6B4C3B", activebackground="#E6D5B8", font=("Segoe UI", 8, "bold"),
                  bd=0, padx=6, pady=4, cursor="hand2").pack(side="bottom", padx=8, pady=(0,8))
        # right page — writing paper with lines
        right=tk.Frame(win, bg="#FFFCF7", bd=1, relief="solid")
        right.place(x=W//2+16, y=72, width=W//2-38, height=H-108)
        _frames_ok["ok"]=True
        today=datetime.date.today().isoformat()
        date_var=tk.StringVar(value=today)
        pretty_today=datetime.datetime.now().strftime("%A, %B %d  —  %Y")
        hdr=tk.Frame(right, bg="#FFFCF7")
        hdr.pack(fill="x", padx=10, pady=(7,2))
        date_label=tk.Label(hdr, text=pretty_today, bg="#FFFCF7", fg="#8B7355", font=("Georgia", 9, "italic"))
        date_label.pack(side="left")
        wc_var=tk.StringVar(value="0 words")
        wc_lbl=tk.Label(hdr, textvariable=wc_var, bg="#FFFCF7", fg="#C9A86A", font=("Segoe UI", 7))
        wc_lbl.pack(side="right")
        # dark mode toggle
        dark_var=tk.BooleanVar(value=False)
        def toggle_dark():
            dark_var.set(not dark_var.get())
            self._journal_dark_cur = dark_var.get()
            dark_tbtn.config(text="☀️" if dark_var.get() else "🌙")
            self._apply_journal_theme(win, dark_var.get())
            _schedule_redraw()
        dark_tbtn=tk.Button(hdr, text="🌙", command=toggle_dark, bd=0, bg="#FFFCF7", fg="#6B4C3B",
                            activebackground="#FFDAB9", font=("Segoe UI", 8), cursor="hand2")
        dark_tbtn.pack(side="right", padx=(6,0))
        # ---- MOOD row: how's your heart ----
        mood_bar=tk.Frame(right, bg="#FFFCF7")
        mood_bar.pack(fill="x", padx=10)
        tk.Label(mood_bar, text="How's your heart today?", bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 8)).pack(side="left")
        mood_var=tk.StringVar(value="")
        mood_btns={}
        for m in ["😍","😊","😐","😢","😤","🌙"]:
            b=tk.Button(mood_bar, text=m, width=2, bd=0, bg="#FFFCF7", fg="#6B4C3B",
                        activebackground="#FFDAB9", font=("Segoe UI", 10), cursor="hand2",
                        command=lambda m=m: (self._pick_mood(m, mood_var, mood_btns), _autosave()))
            b.pack(side="left", padx=1)
            mood_btns[m]=b
        # hearts rating
        tk.Label(mood_bar, text="   ♡", bg="#FFFCF7", fg="#C9A86A", font=("Segoe UI", 8)).pack(side="left")
        rating_var=tk.IntVar(value=0)
        heart_btns=[]
        def draw_hearts():
            r=rating_var.get()
            darknow=getattr(self, "_journal_dark_cur", False)
            for i,b in enumerate(heart_btns):
                b.configure(text="♥" if i<r else "♡",
                            fg="#FF8FA3" if i<r else ("#e8c474" if darknow else "#C9A86A"))
        def set_rating(i):
            rating_var.set(i if rating_var.get()!=i else 0)
            draw_hearts()
            _autosave()
        for i in range(1,6):
            b=tk.Button(mood_bar, text="♡", width=1, bd=0, bg="#FFFCF7", fg="#C9A86A",
                        activebackground="#FFDAB9", font=("Segoe UI", 10), cursor="hand2",
                        command=lambda i=i: set_rating(i))
            b.pack(side="left", padx=0)
            heart_btns.append(b)
        # ---- TAGS row ----
        tag_bar=tk.Frame(right, bg="#FFFCF7")
        tag_bar.pack(fill="x", padx=10, pady=(3,2))
        tk.Label(tag_bar, text="tags:", bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 8)).pack(side="left")
        tags_selected=set()
        tag_btns={}
        tag_defs=[("❤️ love","#FFD2DC"),("🏡 us","#FFE2C2"),("📚 study","#EAD9B0"),("💭 thoughts","#DDD3C8"),("🌙 dreams","#CBDBEA"),("✨ today","#F0D9B4")]
        def refresh_tags():
            for t,b in tag_btns.items():
                on=t in tags_selected
                base_bg="#382f22" if dark_var.get() else "#FFFCF7"
                base_fg="#c9b796" if dark_var.get() else "#6B4C3B"
                b.configure(bg="#FF8FA3" if t=="love" and on else ("#C9A86A" if t!="love" and on else base_bg),
                            fg="white" if on else base_fg)
        def toggle_tag(t):
            if t in tags_selected: tags_selected.discard(t)
            else: tags_selected.add(t)
            refresh_tags()
            _autosave()
        for t,c in tag_defs:
            b=tk.Button(tag_bar, text=t, bd=0, bg="#FFFCF7", fg="#6B4C3B",
                        activebackground="#FFDAB9", font=("Segoe UI", 7), cursor="hand2",
                        command=lambda t=t: toggle_tag(t))
            b.pack(side="left", padx=1, pady=1)
            tag_btns[t]=b
        # separator
        tk.Frame(right, bg="#E6D5B8", height=1).pack(fill="x", padx=8)
        # formatting toolbar
        fmt_bar=tk.Frame(right, bg="#FFFCF7", height=34)
        fmt_bar.pack(fill="x", padx=8, pady=(3,1))
        fmt_buttons = [
            ("B", "bold", "bold"), ("I", "italic", "italic"), ("U", "underline", "underline"),
            ("🎨", "color", "color"), ("🔗", "link", "link"), ("📝", "h1", "heading"),
            ("📋", "list", "bullet"), ("☑", "todo", "todo"),
        ]
        fmt_btns={}
        for label, tag, cmd in fmt_buttons:
            btn=tk.Button(fmt_bar, text=label, width=3, bg="#FFFCF7", fg="#6B4C3B",
                          activebackground="#FFDAB9", activeforeground="#6B4C3B",
                          bd=0, font=("Segoe UI", 9), cursor="hand2",
                          command=lambda t=cmd: (self._apply_format(txt, t), txt.focus_force(), refresh_fmt_buttons()))
            btn.pack(side="left", padx=2, pady=2)
            fmt_btns[cmd]=btn
        def refresh_fmt_buttons():
            try:
                if txt.tag_ranges("sel"):
                    start=txt.index("sel.first")
                    tags=set(txt.tag_names(start))
                    cur_line=txt.get(start+" linestart", start+" lineend")
                else:
                    tags=set(txt.tag_names("insert"))
                    cur_line=txt.get("insert linestart", "insert lineend")
            except: return
            darknow=getattr(self, "_journal_dark_cur", False)
            hot="#4e3a24" if darknow else "#FFDAB9"
            base="#2e261c" if darknow else "#FFFCF7"
            for cmd,b in fmt_btns.items():
                on=False
                if cmd=="bold": on="bold" in tags
                elif cmd=="italic": on="italic" in tags
                elif cmd=="underline": on="underline" in tags
                elif cmd=="heading": on="heading" in tags
                elif cmd=="color": on=any(t.startswith("color_") for t in tags)
                elif cmd=="link": on=any(t.startswith("link_") for t in tags)
                elif cmd=="bullet": on=cur_line.startswith("• ")
                elif cmd=="todo": on=cur_line.startswith("☑ ") or cur_line.startswith("☐ ")
                b.configure(relief="sunken" if on else "flat", bg=hot if on else base)
        tk.Frame(right, bg="#E6D5B8", height=1).pack(fill="x", padx=8)
        # ---- buttons anchored bottom (packed BEFORE the expanding text area) ----
        btnrow=tk.Frame(right, bg="#FFFCF7")
        btnrow.pack(side="bottom", fill="x", padx=8, pady=(2,1))
        toolrow=tk.Frame(right, bg="#FFFCF7")
        toolrow.pack(side="bottom", fill="x", padx=8, pady=(0,4))
        photo_bar=tk.Frame(right, bg="#FFFCF7")
        photo_bar.pack(side="bottom", fill="x", padx=8, pady=(0,2))
        _photo_imgs=[]
        def photo_strip(d):
            for ch in photo_bar.winfo_children(): ch.destroy()
            del _photo_imgs[:]
            e=data.get(d, "")
            names=self._entry_photos(e)
            phd=self._journal_photos_dir()
            if names:
                tk.Label(photo_bar, text="📷 ", bg="#FFFCF7", fg="#C9A86A", font=("Segoe UI", 8)).pack(side="left")
            for n in names[:5]:
                p=phd/n
                if not p.exists(): continue
                try:
                    from PIL import Image as PI, ImageTk as PT
                    im=PI.open(p); im.thumbnail((44,44), PI.LANCZOS)
                    tkp=PT.PhotoImage(im)
                    _photo_imgs.append(tkp)
                    tk.Label(photo_bar, image=tkp, bd=1, relief="solid", bg="#FFFCF7").pack(side="left", padx=1)
                except: pass
        paper=tk.Frame(right, bg="white")
        paper.pack(fill="both", expand=True, padx=8, pady=4)
        txt=tk.Text(paper, bg="white", fg="#3a2a1a", font=("Segoe UI", 11), wrap="word", bd=0, padx=12, pady=10, undo=True, state="normal", takefocus=1)
        txt._links={}
        txt.pack(fill="both", expand=True)
        txt.configure(highlightthickness=1, highlightbackground="#E6D5B8")
        txt.focus_force()
        # rich text tags
        txt.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        txt.tag_configure("italic", font=("Segoe UI", 11, "italic"))
        txt.tag_configure("underline", underline=True)
        txt.tag_configure("heading", font=("Georgia", 14, "bold"), foreground="#6B4C3B")
        txt.tag_configure("todo_done", foreground="#8B7355", overstrike=True)

        def render_inline_photos():
            """Embed the page's photos at the end of the editor (re-entrant)."""
            if not hasattr(txt, "_inline_imgs"): txt._inline_imgs=[]
            # remove old inline images together with the stray newline after each
            for key, val, idx in txt.dump("1.0", tk.END):
                if key=="image":
                    try:
                        if txt.get(idx, f"{idx}+1c")=="\n": txt.delete(idx, f"{idx}+1c")
                        else: txt.delete(idx)
                    except: pass
            del txt._inline_imgs[:]
            dd=date_var.get()
            phd=self._journal_photos_dir()
            names=[n for n in self._entry_photos(data.get(dd)) if (phd/n).exists()]
            # (removed here: aggressive "\n\n\n"->"\n\n" collapsing silently ate
            #  the user's deliberate blank lines on every date switch)
            if not names:
                return
            # start the photo block on its own line
            if txt.get("1.0", "end-1c") and txt.get("end-2c", "end-1c") != "\n":
                txt.insert(tk.END, "\n")
            for n in names:
                try:
                    from PIL import Image as PI, ImageTk as PT
                    im=PI.open(phd/n); im.thumbnail((180,180), PI.LANCZOS)
                    tkp=PT.PhotoImage(im)
                    txt._inline_imgs.append(tkp)
                    txt.image_create(tk.END, image=tkp)
                    txt.insert(tk.END, "\n")
                except: pass

        # ---- load a date into the editor ----
        auto_after=None
        def _autosave(silent=True):
            nonlocal auto_after
            try:
                if auto_after: win.after_cancel(auto_after)
            except: pass
            auto_after=win.after(900, lambda: _save(silent=silent))
        def _flush():
            """Persist pending edits in the editor before switching dates."""
            nonlocal auto_after
            try:
                if auto_after: win.after_cancel(auto_after); auto_after=None
            except: pass
            d=date_var.get()
            stored=data.get(d, "")
            cur_text=txt.get("1.0", tk.END).rstrip()
            dirty=bool(cur_text.strip() or mood_var.get() or rating_var.get() or tags_selected or self._entry_photos(stored))
            if dirty or self._entry_populated(stored):
                try: _save(silent=True)
                except: pass
        def update_wc(e=None):
            words=len(txt.get("1.0", tk.END).split())
            wc_var.set(f"{words} words")
            refresh_fmt_buttons()
            if e: _autosave()
        txt.bind("<KeyRelease>", update_wc)
        txt.bind("<<Selection>>", lambda e: refresh_fmt_buttons())
        txt.bind("<Control-y>", lambda e: (txt.edit_redo(), update_wc(e)) and None)
        txt.bind("<Control-z>", lambda e: (txt.edit_undo(), update_wc(e)) and None)

        def _apply_entry(d):
            e=data.get(d, "")
            if isinstance(e, str): e={"text":e}
            if self._entry_seq(e) is not None:
                s=self._entry_seq(e)
                e={"text":s[0] or "", "mood":s[1] or "", "rating":int(s[2] or 0),
                   "tags":list(s[3] or []), "photos":list(s[4] or []), "ts":s[5] if len(s)>5 else None}
            mood_var.set(self._entry_mood(e))
            rating_var.set(self._entry_rating(e))
            tags_selected.clear()
            tags_selected.update(self._entry_tags(e))
            refresh_tags(); draw_hearts()
            # repaint mood button highlight to match current entry (theme-aware)
            m_sel="#4a2a2c" if dark_var.get() else "#FFD2DC"
            m_base="#2e261c" if dark_var.get() else "#FFFCF7"
            for mb_name, mb in mood_btns.items():
                try: mb.configure(bg=m_sel if mb_name==mood_var.get() else m_base)
                except: pass
            txt.delete("1.0", tk.END)
            txt.insert("1.0", self._entry_text(e))
            txt.edit_reset()
            if not hasattr(txt, "_links"): txt._links={}
            txt._links={}
            self._apply_fmt(txt, self._entry_fmt(e))
            render_inline_photos()
            photo_strip(d)
            update_wc()
            refresh_fmt_buttons()

        def _save(silent=False):
            d=date_var.get()
            cur=data.get(d)
            if isinstance(cur, str): cur={"text": cur}
            else: cur=dict(cur or {})
            cur["text"]=txt.get("1.0", tk.END).rstrip()
            cur["fmt"]=self._capture_fmt(txt)
            cur["mood"]=mood_var.get()
            cur["rating"]=int(rating_var.get())
            cur["tags"]=sorted(tags_selected)
            cur["ts"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            data[d]=cur
            # refresh list entry (only when its text changed; no forced jump)
            if not search_var.get().strip():
                for i in range(lb.size()):
                    if lb.get(i).split(" ")[0]==d:
                        mark=" ●" if self._entry_populated(cur) else " ○"
                        mood=self._entry_mood(cur)
                        new=f"{d}{' '+mood if mood else ''}{mark}"
                        if lb.get(i)!=new:
                            lb.delete(i); lb.insert(i, new)
                        sel=lb.curselection()
                        if not sel or sel[0]!=i:
                            lb.selection_clear(0, tk.END); lb.selection_set(i)
                        break
                else:
                    lb.insert(0, d + " ●")
            self._save_journal(data)
            if not silent:
                self._show_bubble(f"Saved {d} — kept forever in Madhu's book ♡", 2800)
                try:
                    btn.configure(bg="#C9A86A")
                    win.after(180, lambda: btn.configure(bg="#FF8FA3"))
                except: pass

        def load_date(d):
            if d==date_var.get() and d==getattr(self, '_journal_applied_date', None):
                # same page already applied: don't wipe unsaved editor edits
                return
            _flush()
            date_var.set(d)
            self._journal_applied_date=d
            _apply_entry(d)
            try:
                dt=datetime.datetime.fromisoformat(d)
                date_label.configure(text=dt.strftime("%A, %B %d  —  %Y"))
            except: pass

        def _goto_date(d):
            """Called when a calendar day is clicked in the stats window."""
            if d not in data:
                data[d]={}
            _full_refresh()
            load_date(d)
            try:
                idx=lb.size()
                for i in range(lb.size()):
                    if lb.get(i).split(" ")[0]==d: idx=i; break
                if idx<lb.size():
                    lb.selection_clear(0, tk.END); lb.selection_set(idx); lb.see(idx)
            except: pass

        def _refresh_list(needle=None):
            lb.delete(0, tk.END)
            needle=(needle or "").strip().lower()
            for d in sorted(set(list(data.keys()) + [today]), reverse=True):
                e=data.get(d, "")
                if needle:
                    hay=" ".join([d, self._entry_text(e), self._entry_mood(e), " ".join(self._entry_tags(e))]).lower()
                    if needle not in hay: continue
                mark=" ●" if self._entry_populated(e) else " ○"
                mood=self._entry_mood(e)
                lb.insert(tk.END, (f"{d} {mood}" if mood else d) + mark)
            return lb.size()

        def _full_refresh(needle=None):
            n=_refresh_list(needle)
            # select the best match: exact today, else first result, else keep current date
            target=date_var.get()
            idx=lb.size()
            for i in range(n):
                if lb.get(i).split(" ")[0]==target: idx=i; break
            if idx==lb.size():
                for i in range(n):
                    if lb.get(i).split(" ")[0]==date_var.get(): idx=i; break
            if n>0 and idx==lb.size(): idx=0
            if n>0:
                lb.selection_clear(0, tk.END); lb.selection_set(idx); lb.see(idx)

        def on_search(*_):
            needle=search_var.get().strip() or None
            if needle and len(needle)<200: _full_refresh(needle)
            else: _full_refresh()
        search_var.trace_add("write", on_search)

        dates=sorted(set(list(data.keys()) + [today]), reverse=True)
        for d in dates:
            e=data.get(d, "")
            mark=" ●" if self._entry_populated(e) else " ○"
            mood=self._entry_mood(e)
            lb.insert(tk.END, (f"{d} {mood}" if mood else d) + mark)
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

        # ---- buttons: Save on row 1, tools on row 2 ----
        btn=tk.Button(btnrow, text="💾  Save for Madhu", command=lambda: _save(silent=False), bg="#FF8FA3", fg="white", activebackground="#FFA0B5", font=("Segoe UI", 9, "bold"), bd=0, padx=14, pady=7, cursor="hand2")
        btn.pack(side="left", padx=2)
        def backdate():
            import tkinter.simpledialog as sd
            _flush()
            d=date_var.get()
            ans=sd.askstring("Backdate entry", "Change this entry's date\n(YYYY-MM-DD):", initialvalue=d, parent=win)
            if ans:
                ans=ans.strip()
                try:
                    datetime.date.fromisoformat(ans)
                except:
                    self._show_bubble("Hmm, that date is a bit silly — try YYYY-MM-DD 🐾", 3000); return
                if ans==d: return
                import tkinter.messagebox as mb
                existing=data.get(ans)
                if self._entry_populated(existing):
                    ans2=mb.askyesno("Wait, that page has memories", f"There's already an entry on {ans}.\nMove today's page there anyway?\n(The {ans} page will be replaced.)", parent=win)
                    if not ans2: return
                # move current entry to new date
                cur=data.pop(d, {})
                if isinstance(cur, str): cur={"text": cur}
                else: cur=dict(cur or {})
                date_var.set(ans)
                data[ans]=cur
                # full list refresh
                lb.delete(0, tk.END)
                for dd in sorted(set(list(data.keys())+[ans]), reverse=True):
                    e=data.get(dd,"")
                    mark=" ●" if self._entry_populated(e) else " ○"
                    mo=self._entry_mood(e)
                    lb.insert(tk.END, (f"{dd} {mo}" if mo else dd)+mark)
                load_date(ans)
                self._save_journal(data)
                self._show_bubble(f"Moved to {ans} ♡", 2800)
        bk=tk.Button(toolrow, text="✎  backdate", command=backdate, bg="#EFE3CF", fg="#8B7355", activebackground="#E6D5B8", font=("Segoe UI", 8), bd=0, padx=8, pady=5, cursor="hand2")
        bk.pack(side="left", padx=2)
        def new_page():
            import tkinter.simpledialog as sd
            _flush()
            # propose today if free, else the next free day ahead
            proposal=today
            if self._entry_populated(data.get(today)):
                dd=datetime.date.today()
                for i in range(1,31):
                    cand=(dd+datetime.timedelta(days=i)).isoformat()
                    if not self._entry_populated(data.get(cand)):
                        proposal=cand; break
            ans=sd.askstring("New page 📄", "Create a page for date\n(YYYY-MM-DD):", initialvalue=proposal, parent=win)
            if not ans: return
            ans=ans.strip()
            try: datetime.date.fromisoformat(ans)
            except:
                self._show_bubble("Hmm, that date is a bit silly — try YYYY-MM-DD 🐾", 3000); return
            if not self._entry_populated(data.get(ans)) and ans in data:
                pass
            if ans not in data: data[ans]={}
            date_var.set(ans)
            load_date(ans)
            _full_refresh()
            self._save_journal(data)
            self._show_bubble(f"Fresh page open for {ans} ✨", 2800)
            txt.focus_set()
        tk.Button(toolrow, text="📄  new page", command=new_page, bg="#EFE3CF", fg="#8B7355", activebackground="#E6D5B8", font=("Segoe UI", 8), bd=0, padx=8, pady=5, cursor="hand2").pack(side="left", padx=2)
        def del_page():
            import tkinter.messagebox as mb
            _flush()
            d=date_var.get()
            if not self._entry_populated(data.get(d)):
                self._show_bubble("That page is already empty, love", 2500); return
            if not mb.askyesno("Delete page 🗑", f"Delete the page for {d} forever?\nMadhu won't keep it anymore…", parent=win):
                return
            data.pop(d, None)
            self._save_journal(data)
            _full_refresh()
            # go to today or first remaining page
            if today in data: load_date(today)
            elif data:
                load_date(sorted(data.keys())[-1])
            else:
                date_var.set(today); load_date(today)
            self._show_bubble("Page gone — new memories ready to be written ♡", 3000)
        tk.Button(toolrow, text="🗑  delete page", command=del_page, bg="#F3E3E0", fg="#a05a5a", activebackground="#E8D3CF", font=("Segoe UI", 8), bd=0, padx=8, pady=5, cursor="hand2").pack(side="left", padx=2)
        tk.Button(toolrow, text="📤  export", command=lambda: self._export_journal(win, data, date_var.get()),
                  bg="#EFE3CF", fg="#8B7355", activebackground="#E6D5B8", font=("Segoe UI", 8), bd=0, padx=8, pady=5, cursor="hand2").pack(side="left", padx=2)
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
        tk.Button(toolrow, text="⏰ reminder", command=change_time, bg="#EFE3CF", fg="#8B7355", activebackground="#E6D5B8", font=("Segoe UI", 8), bd=0, padx=8, pady=5, cursor="hand2").pack(side="left", padx=2)
        def manage_lock():
            import tkinter.simpledialog as sd, tkinter.messagebox as mb
            if self._journal_locked():
                if mb.askyesno("Remove password?", "Turn off the lock? Existing entries stay safe.", parent=win):
                    if self._journal_remove_password():
                        try: self._save_journal(data)
                        except: pass
                        self._show_bubble("Lock removed — Madhu's book is open", 3000)
                    else:
                        mb.showerror("Couldn't remove the lock",
                                     "Madhu couldn't read the locked book just now, so she kept it "
                                     "locked rather than risk losing anything. Try again in a moment.\n"
                                     "No data was deleted.", parent=win)
            else:
                pw1=sd.askstring("Protect journal 🔒", "Set a password\n(so Madhu's book stays private):", show="●", parent=win)
                if pw1:
                    pw2=sd.askstring("Protect journal 🔒", "Repeat the password:", show="●", parent=win)
                    if pw1!=pw2:
                        self._show_bubble("Passwords don't match ♡", 3000); return
                    if self._journal_set_password(pw1):
                        self._show_bubble("Journal locked — only you can read it 🔒", 4000)
                    else:
                        self._show_bubble("Need at least 6 characters, love", 3000)
        tk.Button(toolrow, text="🔒  lock", command=manage_lock, bg="#EFE3CF", fg="#8B7355", activebackground="#E6D5B8", font=("Segoe UI", 8), bd=0, padx=8, pady=5, cursor="hand2").pack(side="left", padx=2)
        miscrow=tk.Frame(right, bg="#FFFCF7")
        miscrow.pack(side="bottom", fill="x", padx=8, pady=(0,2))
        def add_photo():
            _flush()
            d=date_var.get()
            names=self._attach_photos(d)
            if names:
                cur=data.get(d)
                if isinstance(cur,str): cur={"text":cur}
                cur=dict(cur or {})
                cur["photos"]=list(cur.get("photos",[]))+names
                data[d]=cur
                self._save_journal(data)
                photo_strip(d)
                render_inline_photos()
                self._show_bubble(f"{len(names)} photo{'s' if len(names)>1 else ''} tucked into the page ♡", 3500)
        tk.Button(miscrow, text="📷  photo", command=add_photo, bg="#EFE3CF", fg="#8B7355", activebackground="#E6D5B8", font=("Segoe UI", 8), bd=0, padx=8, pady=5, cursor="hand2").pack(side="left", padx=2)
        def photo_delete():
            import tkinter.messagebox as mb
            _flush()
            d=date_var.get()
            cur=data.get(d)
            known=self._entry_photos(cur)
            if not known:
                self._show_bubble("No photos on this page yet, love", 2500); return
            if mb.askyesno("Remove photos 📷", "Remove all photos from this page?\n(Madhu keeps copies in the book folder.)", parent=win):
                raw=data.get(d)
                cur={"text": raw} if isinstance(raw, str) else dict(raw or {})
                cur["photos"]=[]
                data[d]=cur
                self._save_journal(data)
                photo_strip(d)
                render_inline_photos()
                self._show_bubble("Photos cleared from the page ♡", 2500)
        tk.Button(miscrow, text="✕ photos", command=photo_delete, bg="#F3E3E0", fg="#a05a5a", activebackground="#E8D3CF", font=("Segoe UI", 8), bd=0, padx=8, pady=5, cursor="hand2").pack(side="left", padx=2)
        def on_close():
            nonlocal auto_after
            try:
                if auto_after:
                    try: win.after_cancel(auto_after)
                    except: pass
                    auto_after=None
                _save(silent=True)
            except Exception as _e:
                _LOGGER.error("journal close save failed: %s", _e)
                try:
                    import tkinter.messagebox as _mb
                    _mb.showerror("Madhu couldn't save your page",
                                  "Your last few words may not have been kept. "
                                  "Please copy the page text before closing, love.",
                                  parent=win)
                except Exception:
                    pass
            self._journal_win=None
            win.destroy()
        self._journal_on_close=on_close
        win.protocol("WM_DELETE_WINDOW", on_close)
        txt.focus_set()
        update_wc()
        # restore the theme used last time this journal was open in the session:
        # without this the book re-draws dark ("black panel") onto light widgets,
        # or light onto a dark window
        if getattr(self, "_journal_dark_cur", False):
            dark_var.set(True)
            dark_tbtn.config(text="☀️")
            try: self._apply_journal_theme(win, True)
            except Exception as _e: _LOGGER.error("journal theme restore: %s", _e)
            _schedule_redraw()

    def _pick_mood(self, m, mood_var, mood_btns):
        darknow = getattr(self, "_journal_dark_cur", False)
        sel="#4a2a2c" if darknow else "#FFD2DC"
        base="#2e261c" if darknow else "#FFFCF7"
        for k,b in mood_btns.items():
            b.configure(bg=sel if k==m and mood_var.get()!=m else base)
        if mood_var.get()==m: mood_var.set("")
        else: mood_var.set(m)
        # also show mood char in the header date label area is complex; keep simple
        rtxt=mood_var.get()
        # gentle bubble if a mood picked
        if rtxt:
            self._show_bubble(f"Madhu notes your mood: {rtxt}", 2000)

    def _show_stats(self, parent, data, dark=False, on_day=None):
        """Theme-styled calendar + statistics dashboard"""
        import datetime, calendar
        sw_existing=getattr(self, "_stats_win", None)
        if sw_existing is not None:
            try:
                if sw_existing.winfo_exists():
                    sw_existing.deiconify(); sw_existing.lift(); sw_existing.focus_force(); return
            except: pass
        win=tk.Toplevel(parent)
        self._stats_win=win
        win.title("Madhu's Insights 📊")
        W,H=640,600
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        win.geometry(f"{W}x{H}+{sw//2-W//2}+{max(0,sh//2-H//2)}")
        win.configure(bg="#FDF6E3")
        canvas=tk.Canvas(win, width=W, height=H, bg="#FDF6E3", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        def _rr(x1,y1,x2,y2,r,**kw): pts=[x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1]; return canvas.create_polygon(pts,smooth=True,**kw)
        dbevel="#342b1f" if dark else "#E8DCC8"
        dfill="#2e261c" if dark else "#FFFCF7"
        dout="#e8c474" if dark else "#C9A86A"
        _rr(6,6,W-6,H-6,18, fill=dbevel, outline="")
        _rr(2,2,W-2,H-2,14, fill=dfill, outline=dout, width=2)
        tk.Label(win, text="📊  Madhu's little insights", bg="#FFFCF7", fg="#6B4C3B", font=("Georgia", 14, "bold")).place(x=W//2, y=14, anchor="n")
        tk.Label(win, text="— what your pages whisper —", bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 8, "italic")).place(x=W//2, y=38, anchor="n")
        # lifetime stats row
        dates=[d for d,v in data.items() if self._entry_populated(v)]
        total=len(dates)
        words=sum(len(self._entry_text(v).split()) for v in data.values())
        streak=self._journal_streak(data)
        # entries with mood
        moods=[self._entry_mood(v) for v in data.values() if self._entry_mood(v)]
        from collections import Counter
        mc=Counter(moods)
        top_mood=mc.most_common(1)[0][0] if mc else "—"
        ages=0
        if dates:
            try:
                first=min(datetime.date.fromisoformat(d) for d in dates)
                ages=(datetime.date.today()-first).days
            except: pass
        stats_frame=tk.Frame(win, bg="#FFFCF7")
        stats_frame.place(x=20, y=56, width=W-40, height=64)
        labels=[("pages", str(total)), ("words", str(words)), ("🔥 streak", f"{streak}d"), ("moods", str(len(mc))), ("top mood", top_mood), ("oldest", f"{ages}d ago" if ages else "—")]
        col=0
        for name,val in labels:
            f=tk.Frame(stats_frame, bg="#FFFCF7", bd=0)
            f.place(relx=col/len(labels), rely=0, relwidth=1/len(labels), relheight=1)
            tk.Label(f, text=val, bg="#FFFCF7", fg="#6B4C3B", font=("Georgia", 16, "bold")).pack(anchor="center")
            tk.Label(f, text=name, bg="#FFFCF7", fg="#C9A86A", font=("Segoe UI", 8)).pack(anchor="center")
            col+=1
        # real month calendar — navigable, day numbers visible, written days highlighted
        cal_frame=tk.Frame(win, bg="#FFFCF7")
        cal_frame.place(x=20, y=128, width=W-40, height=230)
        today=datetime.date.today()
        state={"ym":(today.year, today.month)}
        mood_by_date={ds:self._entry_mood(v) for ds,v in data.items()}
        # header: month title + prev/next
        cal_title_bar=tk.Frame(cal_frame, bg="#FFFCF7")
        cal_title_bar.pack(fill="x", pady=(0,2))
        month_lbl=tk.Label(cal_title_bar, text="", bg="#FFFCF7", fg="#6B4C3B", font=("Georgia", 11, "bold"))
        month_lbl.pack(side="left")
        def _shift(delta):
            y,m=state["ym"]
            nm=m+delta
            state["ym"]=(y-1 if nm<1 else y+1 if nm>12 else y, (nm-1)%12+1)
            render_month()
        for txt,delta in (("◀",-1),("▶",1)):
            tk.Button(cal_title_bar, text=txt, bg="#F0D9B4", fg="#5a3e2b", bd=0, relief="flat",
                      activebackground="#EAD9B0", font=("Segoe UI", 8), width=2,
                      cursor="hand2", command=lambda de=delta: _shift(de)).pack(side="right", padx=2)
        week_labels=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        whdr=tk.Frame(cal_frame, bg="#FFFCF7")
        whdr.pack(fill="x")
        for wl in week_labels:
            tk.Label(whdr, text=wl, bg="#FFFCF7", fg="#C9A86A", font=("Segoe UI", 8, "bold"), width=8).pack(side="left", expand=True)
        grid=tk.Frame(cal_frame, bg="#FFFCF7")
        grid.pack(fill="both", expand=True)
        for cc in range(7): grid.columnconfigure(cc, weight=1)
        for rr in range(6): grid.rowconfigure(rr, weight=1)
        def render_month():
            for c in grid.winfo_children(): c.destroy()
            y,m=state["ym"]
            month_lbl.configure(text=f"🗓  {datetime.date(y,m,1).strftime('%B %Y')}")
            first=datetime.date(y,m,1)
            start=first - datetime.timedelta(days=first.weekday())
            for r in range(6):
                for c in range(7):
                    d=start+datetime.timedelta(weeks=r, days=c)
                    ds=d.isoformat()
                    e=data.get(ds)
                    has=self._entry_populated(e) if e else False
                    in_month=d.year==y and d.month==m
                    is_today=(d==today)
                    c_today="#4a2a2c" if dark else "#FFD2DC"
                    c_has="#443620" if dark else "#F0D9B4"
                    c_none="#2e261c" if dark else "#FFFCF7"
                    ring="#e8c474" if dark else "#E8A0B5"
                    bg=c_today if is_today else (c_has if has else c_none)
                    fg="#e8c474" if not in_month else ("#f0e2c4" if (has or is_today) else "#c9b796")
                    cell=tk.Frame(grid, bg=bg, bd=0,
                                  relief="flat",
                                  highlightthickness=2 if is_today else 0,
                                  highlightbackground=ring)
                    cell.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                    tk.Button(cell, text=str(d.day), bg=bg, fg=fg,
                              font=("Segoe UI", 9, "bold" if has else "normal"),
                              activebackground=("#4e3a24" if dark else "#FFDAB9"), bd=0, relief="flat", cursor="hand2",
                              command=lambda ds=ds: (win.destroy(), on_day(ds) if on_day else None)
                              ).pack(side="top", fill="both", expand=True)
                    if has and mood_by_date.get(ds):
                        tk.Label(cell, text=mood_by_date[ds], bg=bg, fg=("#e8c474" if dark else "#8B7355"),
                                 font=("Segoe UI", 8)).pack(side="bottom")
        render_month()
        # mood trend: mini bar by month for last 6 months
        trend_frame=tk.Frame(win, bg="#FFFCF7")
        trend_frame.place(x=20, y=366, width=W-40, height=190)
        tk.Label(trend_frame, text="📈  entries per week (last 12)  —  hearts = your rating", bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 8)).pack(anchor="w")
        tc=tk.Canvas(trend_frame, bg="#FFFCF7", highlightthickness=0)
        tc.pack(fill="both", expand=True, pady=4)
        # count entries per week
        monday=datetime.date.fromordinal(today.toordinal() - today.weekday() - 7*11)
        weekly=[]
        for r in range(12):
            wstart=monday + datetime.timedelta(weeks=r)
            cnt=sum(1 for i in range(7) if self._entry_populated(data.get((wstart+datetime.timedelta(days=i)).isoformat())))
            avg=0
            rr=[self._entry_rating(data.get((wstart+datetime.timedelta(days=i)).isoformat())) if self._entry_populated(data.get((wstart+datetime.timedelta(days=i)).isoformat())) else 0 for i in range(7)]
            avg=sum(rr)/7 if rr else 0
            weekly.append((cnt,avg))
        mx=max([x[0] for x in weekly]+[1])
        bar_w=30; gap=13; left0=15; baseline=120
        bar_muted="#4a3c2e" if dark else "#F3E9D8"
        bar_fill="#8a5a42" if dark else "#E6A88F"
        lab_gold="#e8c474" if dark else "#C9A86A"
        for i,(cnt,avg) in enumerate(weekly):
            x=left0+i*(bar_w+gap)
            h=int(cnt/mx*90) if mx else 0
            tc.create_rectangle(x, baseline-h, x+bar_w, baseline, fill=bar_fill if cnt else bar_muted, outline="")
            if avg:
                tc.create_text(x+bar_w//2, baseline-h-8, text="♥"*max(1,round(avg)), fill="#FF8FA3", font=("Segoe UI", 6))
            tc.create_text(x+bar_w//2, baseline+10, text=f"w{i}", fill=lab_gold, font=("Segoe UI", 6))
        # tag breakdown
        tag_counts=Counter()
        for v in data.values():
            if not isinstance(v,str):
                for t in (self._entry_tags(v)): tag_counts[t]+=1
        if tag_counts:
            tk.Label(trend_frame, text="  top tags:  " + "  ·  ".join(f"{t} ×{n}" for t,n in tag_counts.most_common(4)), bg="#FFFCF7", fg="#8B7355", font=("Segoe UI", 7)).pack(side="bottom", anchor="w", pady=2)
        tk.Button(win, text="Close ♡", command=win.destroy, bg="#FF8FA3", fg="white",
                  activebackground="#FFA0B5", font=("Segoe UI", 9, "bold"), bd=0, padx=18, pady=5, cursor="hand2").place(x=W//2-40, y=H-40)
        win.attributes("-topmost", True)
        win.transient(parent)
        if dark:
            self._apply_journal_theme(win, True)

    def _apply_journal_theme(self, win, dark):
        """Warm night-parchment dark mode — cocoa + gold, not cold navy."""
        if dark:
            # warm chocolate dark palette
            map_bg={ "#FFFCF7":"#2e261c", "white":"#342b1f", "#FDF6E3":"#1e1810",
                     "#EFE3CF":"#382f22", "#FFD2DC":"#4a2a2c", "#FFDAB9":"#4e3a24",
                     "#E6D5B8":"#4a3c2e", "#F3E3E0":"#3a2820", "#F0D9B4":"#443620",
                     "#E8D3CF":"#3a2820", "#DDD3C8":"#4a3c2e", "#CBDBEA":"#2c3038",
                     "#EAD9B0":"#3e3424" }
            map_fg={ "#6B4C3B":"#f0e2c4", "#8B7355":"#c9b796", "#5a3e2b":"#f0e2c4",
                     "#3a2a1a":"#f5ecda", "#C9A86A":"#e8c474", "#C49A6C":"#e8c474",
                     "#a05a5a":"#d4848a" }
            txt_bg="#342b1f"; txt_fg="#f5ecda"; hl_bg="#4a3c2e"
        else:
            # original warm parchment light
            map_bg={ "#2e261c":"#FFFCF7", "#342b1f":"white", "#1e1810":"#FDF6E3",
                     "#382f22":"#EFE3CF", "#4a2a2c":"#FFD2DC", "#4e3a24":"#FFDAB9",
                     "#4a3c2e":"#E6D5B8", "#3a2820":"#F3E3E0", "#443620":"#F0D9B4",
                     "#2c3038":"#CBDBEA", "#3e3424":"#EAD9B0" }
            map_fg={ "#f0e2c4":"#6B4C3B", "#c9b796":"#8B7355", "#f5ecda":"#3a2a1a",
                     "#e8c474":"#C9A86A", "#d4848a":"#a05a5a" }
            txt_bg="white"; txt_fg="#3a2a1a"; hl_bg="#E6D5B8"
        # Toplevel + canvas backdrop
        win.configure(bg="#1e1810" if dark else "#FDF6E3")
        for cc in [w for w in win.winfo_children() if isinstance(w, tk.Canvas)]:
            cc.configure(bg="#1e1810" if dark else "#FDF6E3")
        memo=set()
        def relabel(node):
            if id(node) in memo: return
            memo.add(id(node))
            for w in node.winfo_children():
                if isinstance(w, tk.Widget):
                    try:
                        cur_bg=str(w.cget("bg"))
                        cur_bg=cur_bg if cur_bg.startswith("#") else cur_bg
                        nb=map_bg.get(cur_bg)
                        if nb: w.configure(bg=nb)
                        cur_fg=str(w.cget("fg"))
                        if cur_fg.startswith("#"):
                            nf=map_fg.get(cur_fg) or map_bg.get(cur_fg)
                            if nf: w.configure(fg=nf)
                        try:
                            ab=str(w.cget("activebackground"))
                            if ab.startswith("#") and ab in map_bg:
                                w.configure(activebackground=map_bg[ab])
                        except: pass
                        try:
                            af=str(w.cget("activeforeground"))
                            if af.startswith("#") and af in map_fg:
                                w.configure(activeforeground=map_fg[af])
                        except: pass
                        if isinstance(w, tk.Text):
                            w.configure(bg=txt_bg, fg=txt_fg, highlightbackground=hl_bg,
                                        insertbackground=("#e8c474" if dark else "#6B4C3B"),
                                        selectbackground=("#4a2a2c" if dark else "#FFDAB9"),
                                        selectforeground=(txt_fg if dark else "#3a2a1a"),
                                        inactiveselectbackground=("#4a2a2c" if dark else "#FFDAB9"))
                            for t in w.tag_names():
                                try:
                                    opts={}
                                    if t=="heading": opts={"foreground":"#f0e2c4" if dark else "#6B4C3B"}
                                    if t=="todo_done": opts={"foreground":"#a89a82" if dark else "#8B7355", "overstrike":True}
                                    if t.startswith("link_"): opts={"foreground":"#8ab4f8" if dark else "#0066CC", "underline":True}
                                    if opts: w.tag_configure(t, **opts)
                                except: pass
                        elif isinstance(w, tk.Entry):
                            try:
                                w.configure(insertbackground=("#e8c474" if dark else "#6B4C3B"),
                                            selectbackground=("#4a2a2c" if dark else "#FFDAB9"),
                                            selectforeground=(txt_fg if dark else "#3a2a1a"))
                            except: pass
                        elif isinstance(w, tk.Listbox):
                            try:
                                w.configure(selectbackground=("#4a2a2c" if dark else "#FFDAB9"),
                                            selectforeground=("#f0e2c4" if dark else "#5a3e2b"))
                            except: pass
                    except: pass
                relabel(w)
        relabel(win)

    def _export_journal(self, parent, data, only_today=""):
        """Backup entries as plain text + a simple PDF (no external deps)."""
        import datetime, os
        def ask(ext):
            import tkinter.filedialog as fd
            return fd.asksaveasfilename(parent=parent, defaultextension="." + ext,
                                        initialdir=str(pathlib.Path.home() / "Desktop"),
                                        initialfile=f"Madhu_Journal_{datetime.date.today()}.{ext}",
                                        filetypes=[(ext.upper() + " file", "*." + ext)])
        m=tk.Menu(parent, tearoff=0, bg="#FFFCF7", fg="#6B4C3B", activebackground="#FFDAB9")
        def alltxt():
            dest=ask("txt")
            if dest:
                self._journal_write_txt(data, pathlib.Path(dest))
                self._show_bubble("Backup saved: " + os.path.basename(str(dest)), 3500)
        def allpdf():
            dest=ask("pdf")
            if dest:
                self._journal_write_pdf(data, pathlib.Path(dest))
                self._show_bubble("PDF book saved ♡", 3500)
        def todaytxt():
            dest=ask("txt")
            if dest:
                self._journal_write_txt(data, pathlib.Path(dest), only_today)
                self._show_bubble("Today exported ♡", 2500)
        def todaypdf():
            dest=ask("pdf")
            if dest:
                self._journal_write_pdf(data, pathlib.Path(dest), only_today)
                self._show_bubble("Today's PDF saved ♡", 2500)
        m.add_command(label="Export ALL - text file (.txt)", command=alltxt)
        m.add_command(label="Export ALL - PDF book (.pdf)", command=allpdf)
        m.add_separator()
        m.add_command(label="Export today only - text (.txt)", command=todaytxt)
        m.add_command(label="Export today only - PDF (.pdf)", command=todaypdf)
        try:
            m.post(parent.winfo_pointerx(), parent.winfo_pointery())
        except:
            pass

    def _journal_lines(self, data, today_only=""):
        keys=sorted(data.keys())
        if today_only: keys=[today_only]
        for d in keys:
            e=data.get(d, "")
            txt=self._entry_text(e)
            if today_only and not txt.strip(): continue
            mood=self._entry_mood(e)
            rating=self._entry_rating(e)
            tags=self._entry_tags(e)
            yield f"-- {d} --"
            meta=[]
            if mood: meta.append(f"mood {mood}")
            if rating: meta.append("hearts " + "♥"*rating)
            if tags: meta.append("tags: " + ", ".join(tags))
            if meta: yield "   " + "   ".join(meta)
            yield "   " + (txt.strip().replace("\n", "\n   ") if txt.strip() else "(no words)")
            yield ""

    def _journal_write_txt(self, data, path, only_today=""):
        import datetime
        with open(path, "w", encoding="utf-8") as f:
            f.write("Gayathree's Journal - kept by Madhu ♡\n")
            f.write("exported " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "\n" + "="*40 + "\n\n")
            for l in self._journal_lines(data, only_today): f.write(l + "\n")
        return path

    def _journal_write_pdf(self, data, path, only_today=""):
        import datetime
        def esc(t):
            r=[]
            for c in t:
                # replacement strings can be multi-char ("..." "[x]" "oe" "ss");
                # escape each replacement char individually (ord() of a multi-
                # char string used to raise TypeError and kill the whole export)
                for cc in _PDF_TRANSLIT.get(c, c):
                    o=ord(cc)
                    r.append(hex(o)[2:].rjust(2,"0") if 32 <= o <= 255 else "20")
            return "".join(r)
        pages=[]
        cur=["BT /F1 14 Tf 60 750 Td <" + esc("Gayathree's Journal - kept by Madhu") + "> Tj ET",
             "BT /F1 9 Tf 60 736 Td <" + esc("exported " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M')) + "> Tj ET"]
        y=712
        exit_lines=0
        def flush():
            nonlocal cur, exit_lines
            stream="\n".join(cur).encode("latin-1")
            pages.append(stream)
            cur=[]
            exit_lines=0
        for l in self._journal_lines(data, only_today):
            if y<45:
                flush(); y=712
            cur.append("BT /F1 10 Tf 60 " + str(y) + " Td <" + esc(l) + "> Tj ET")
            y-=14
            exit_lines+=1
            if exit_lines>=46:
                flush(); y=712
        flush()
        n=len(pages)
        if n==0: return path
        font_no=3+2*n
        objs=[]
        objs.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        kids=" ".join(f"{3+2*i} 0 R" for i in range(n))
        objs.append(f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {n} >>\nendobj\n")
        for i,stream in enumerate(pages):
            P=3+2*i
            objs.append(f"{P} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_no} 0 R >> >> /Contents {P+1} 0 R >>\nendobj\n")
            objs.append(f"{P+1} 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream\nendobj\n")
        objs.append(f"{font_no} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
        out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offs=[0]
        for o in objs:
            offs.append(len(out))
            out+= o if isinstance(o, bytes) else o.encode("latin-1")
        xref=len(out)
        count=len(objs)+1
        out+=f"xref\n0 {count}\n0000000000 65535 f \n".encode()
        for o in offs[1:]:
            out+=("%010d 00000 n \n" % o).encode()
        out+=f"trailer\n<< /Size {count} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
        path.write_bytes(bytes(out))
        return path

    def check_journal_reminder(self):
        try:
            import datetime
            now=datetime.datetime.now()
            hour=self.memory.get("journal_hour",21)
            minute=self.memory.get("journal_min",0)
            # changeable later via menu, default 21:00
            if now.hour==hour and now.minute==minute:
                today=now.date().isoformat()
                slot=f"{today}_{hour}_{minute}"
                if getattr(self, '_last_journal_slot', None) != slot:
                    # Windows strftime has no %-I; use manual 12-hour math
                    twelve=(now.hour % 12) or 12
                    data=self._load_journal()
                    if getattr(self, "_journal_read_error", False):
                        # reminder-time load: never void saves silently
                        self._journal_read_error=False
                    try:
                        if not self._entry_text(data.get(today)).strip():
                            msg=(f"{twelve} {now.strftime('%p')} — time to journal, Gayathree? 📖"
                                 if hour==21 else
                                 f"{hour:02d}:{minute:02d} — time to journal, Gayathree? 📖")
                            self._show_bubble(msg, 7000, priority=1)
                            print("journal reminder")
                        else:
                            self._show_bubble("Journal done today — proud of you ♡", 4000)
                        # gentle chirp if not muted
                        self._play_meow("chirp")
                    finally:
                        # latch only AFTER the work, so a failure can retry today
                        self._last_journal_slot=slot
        except: pass
        self.root.after(25000, self.check_journal_reminder)

    # --- Rich Text Formatting Methods ---
    def _apply_format(self, txt, tag):
        """Apply formatting tag to selected text"""
        if tag == "bullet":
            self._toggle_bullet(txt); return
        if tag == "todo":
            self._toggle_todo(txt); return
        try:
            if not txt.tag_ranges("sel"):
                return
            if tag in ("bold", "italic", "underline"):
                if tag in txt.tag_names("sel.first"):
                    txt.tag_remove(tag, "sel.first", "sel.last")
                else:
                    txt.tag_add(tag, "sel.first", "sel.last")
            elif tag == "color":
                self._pick_color(txt)
            elif tag == "link":
                self._add_link(txt)
            elif tag == "heading":
                self._toggle_tag(txt, "heading")
        except: pass

    def _pick_color(self, txt):
        try:
            import tkinter.colorchooser as cc
            color = cc.askcolor(title="Choose text color", parent=txt.winfo_toplevel())
            if color[1]:
                tag_name = f"color_{color[1].replace('#','')}"
                txt.tag_configure(tag_name, foreground=color[1])
                if tag_name in txt.tag_names("sel.first"):
                    txt.tag_remove(tag_name, "sel.first", "sel.last")
                else:
                    txt.tag_add(tag_name, "sel.first", "sel.last")
        except: pass

    def _add_link(self, txt):
        import tkinter.simpledialog as sd
        url = sd.askstring("Add Link", "Enter URL:", parent=txt.winfo_toplevel())
        if url:
            tag_name = f"link_{len(txt.tag_names())}"
            txt.tag_configure(tag_name, foreground="#0066CC", underline=True)
            txt.tag_add(tag_name, "sel.first", "sel.last")
            if not hasattr(txt, "_links"): txt._links={}
            txt._links[tag_name]=url
            # store URL in tag data
            txt.tag_bind(tag_name, "<Button-1>", lambda e: self._open_link(url))

    def _open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    def _toggle_tag(self, txt, tag):
        if tag in txt.tag_names("sel.first"):
            txt.tag_remove(tag, "sel.first", "sel.last")
        else:
            txt.tag_add(tag, "sel.first", "sel.last")

    def _toggle_bullet(self, txt):
        try:
            line_start = txt.index("insert linestart")
            line_end = txt.index("insert lineend")
            line_text = txt.get(line_start, line_end)
            if line_text.startswith("• "):
                txt.delete(line_start, f"{line_start}+2c")
            else:
                txt.insert(line_start, "• ")
        except: pass

    def _toggle_todo(self, txt):
        try:
            line_start = txt.index("insert linestart")
            line_end = txt.index("insert lineend")
            line_text = txt.get(line_start, line_end)
            if line_text.startswith("☐ "):
                txt.delete(line_start, line_end)
                txt.insert(line_start, "☑ " + line_text[2:])
                txt.tag_add("todo_done", f"{line_start}+2c", f"{line_start}+{len('☑ ')+len(line_text[2:])}c")
            elif line_text.startswith("☑ "):
                txt.delete(line_start, line_end)
                txt.insert(line_start, "☐ " + line_text[2:])
                txt.tag_remove("todo_done", f"{line_start}+2c", f"{line_start} lineend")
            else:
                txt.insert(line_start, "☐ ")
                txt.tag_remove("todo_done", line_start, f"{line_start} lineend")
        except: pass

    def _is_dont_sleep(self):
        return time.time() < self._dont_sleep_until

    def toggle_dont_sleep(self):

        if self._is_dont_sleep():

            self._dont_sleep_until=0

            for aid in (self._dont_sleep_after, getattr(self,'_dont_sleep_tick_after',None)):

                if aid:

                    try: self.root.after_cancel(aid)

                    except: pass

            self._dont_sleep_after=None; self._dont_sleep_tick_after=None

            try: self.menu.entryconfig(8, label="Don't sleep 30m ☕")

            except: pass

            self._show_bubble("Okay, sleepy now Zzz 😴", 3000)

            self.animator.set_state("sleeping", big=False, flip=False)

            print("Don't sleep OFF")

        else:

            self._dont_sleep_until=time.time()+30*60

            try: self.menu.entryconfig(8, label="Don't sleep ✓ (30m)")

            except: pass

            self._show_bubble("I won't sleep for 30m! ☕", 4000)

            if not self.is_duck:

                self.animator.set_state("play", big=False, flip=False)

            self._play_meow("chirp")

            print("Don't sleep ON 30m")

            if self._dont_sleep_after:

                try: self.root.after_cancel(self._dont_sleep_after)

                except: pass

            if getattr(self,'_dont_sleep_tick_after',None):

                try: self.root.after_cancel(self._dont_sleep_tick_after)

                except: pass

            self._dont_sleep_after=self.root.after(30*60*1000, self._dont_sleep_expire)

            self._dont_sleep_tick()

            self.root.after(600, self.trigger_walk)



    def _dont_sleep_tick(self):

        if not self._is_dont_sleep():

            return

        left=int((self._dont_sleep_until - time.time())/60)

        left=max(0, left)

        try: self.menu.entryconfig(8, label=f"Don't sleep ✓ ({left}m)")

        except: pass

        self._dont_sleep_tick_after=self.root.after(60*1000, self._dont_sleep_tick)



    def _dont_sleep_expire(self):

        self._dont_sleep_until=0

        self._dont_sleep_after=None

        try: self.menu.entryconfig(8, label="Don't sleep 30m ☕")

        except: pass

        self._show_bubble("Okay, sleepy now Zzz 😴", 3500)

        self.animator.set_state("sleeping", big=False, flip=False)

        print("Don't sleep auto OFF after 30m")



    def _maybe_sleep(self):

        if not self.is_petting and not self.walk_active and not self.is_duck:

            if self._is_dont_sleep():

                self.animator.set_state(random.choice(["groom","play","watching","knead"]), big=False, flip=False)

            else:

                self.animator.set_state("sleeping", big=False)



    def _load_pos(self):

        try:

            if self._pos_file.exists():

                x=int(self._pos_file.read_text().strip())

                print(f"remembered pos {x}")

                return x

        except: pass

        return None



    def _save_pos(self, force=False):

        try:

            if self.walk_x is not None:

                cur_x=int(self.walk_x)

                # dirty-flag: poll_position runs every 5s; only write when the
                # pet actually moved (was ~20 GB/yr of pointless disk churn)
                if not force and cur_x == getattr(self, "_last_saved_x", None):
                    return

                self._last_saved_x=cur_x

                self._pos_file.write_text(str(cur_x))

                # also persist favorite + memory pos

                try:

                    self.memory["pos_x"]=cur_x

                    mem.save(self.memory)

                except: pass

        except: pass



    def quit(self):

        try:

            for aid in (self._anim_after, self._walk_after, self._dont_sleep_after, getattr(self,'_dont_sleep_tick_after',None)):

                if aid:

                    try: self.root.after_cancel(aid)

                    except: pass

        except: pass

        self._save_pos(force=True)

        if getattr(self, '_journal_win', None) is not None and getattr(self, '_journal_on_close', None):
            # do NOT swallow: a silent failure here loses the page being typed
            try: self._journal_on_close()
            except Exception as _e: _LOGGER.error("final journal save failed: %s", _e)

        try:
            # persist when she left, so the next launch can greet/measure absence
            self.memory["lastSeen"]=datetime.datetime.now().isoformat()
            mem.save(self.memory)
        except: pass

        self.root.destroy()



    def run(self):

        self.root.mainloop()

