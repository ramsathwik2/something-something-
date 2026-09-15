import tkinter as tk

from animator import SpriteAnimator

from taskbar import calc_position, get_taskbar_edge, get_taskbar_rect, get_screen_size

import ctypes, pathlib, random, time, json, datetime

import memory as mem



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

        # memory

        self.memory = mem.load()

        mem.ensure_birth(self.memory)

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

            self.walk_x = int(self.memory["pos_x"])

        else:

            self.walk_x = self._load_pos()

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



        self.menu = tk.Menu(self.root, tearoff=0)

        self.menu.add_command(label="Placement: Above (floating)", command=lambda: self.set_placement("above"))

        self.menu.add_command(label="Placement: Overlay (on taskbar)", command=lambda: self.set_placement("overlay"))

        self.menu.add_separator()

        self.menu.add_command(label="Walk now (bored)", command=self.trigger_walk)

        pet_label = f"Pet {self.kitten_name} <3" if self.kitten_name else "Pet her <3"

        self.menu.add_command(label=pet_label, command=self.trigger_pet)

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
        self.update_position()

        self.animate()

        self.root.after(5000, self.poll_position)

        self.root.after(3000, self.bored_check)

        self.root.after(3000, self.duck_check)

        self.root.after(2200, self.curious_check)

        self.root.after(2500, self.food_check)

        self.root.after(900, self.ask_name_if_needed)

        self.root.after(2000, self.mood_on_startup)

        self.root.after(4000, self.seasonal_check)

        self.root.after(6000, self.waiting_check)

        self.root.after(1800, self.glance_check)

        self.root.after(8000, self._check_long_absence)

        self.root.after(10000, self.wish_11_check)
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

            # side middle (right side, centered vertical)

            x = sw - BIG_W - 12

            y = sh//2 - BIG_H//2

            # ensure not behind maxized windows? keep topmost

            self.root.geometry(f"{BIG_W}x{BIG_H}+{x}+{y}")

            # speech bubble via tooltip window? simple print

            print("🦆 Duck mode: kitten is bigger on side, ready to rubber-duck your code")

        else:

            self.pet_w = PET_W

            self.pet_h = PET_H

            self.animator.set_state("sleeping", big=False)

            self.update_position()

            print("Duck mode off -> back to taskbar")



    def toggle_duck(self):

        self.set_duck(not self.is_duck)



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

            x = int(self.walk_x)

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

            # architecture idle easter egg 3% : blueprint nap hint

            if random.random()<0.03:

                self._show_bubble("📐 *blueprint nap* Zzz", 3000)

            if random.random() < 0.78 and self.animator.idx % 2 == 0:

                pil = self.animator.frames[0] if not self.animator.is_big else self.animator.frames_big[0]

                tk_img = self.animator._to_tk(pil)

                self._tk_img_ref = tk_img

                self.label.configure(image=tk_img)

                self._anim_after = self.root.after(random.randint(1900,3200), self.animate)

                return

        tk_img, delay, size = self.animator.next_frame()

        self._tk_img_ref = tk_img

        self.label.configure(image=tk_img)

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

            self.root.after(1800, lambda: self.animator.set_state("groom", big=False, flip=False) if not self.walk_active else None)

            end_state="play" if is_awake else "sleeping"

            self.root.after(4200, lambda: self.animator.set_state(end_state, big=False, flip=False) if not self.walk_active else None)

        elif r < 0.40:

            print("🐱 loaf & watch birds")

            self.animator.set_state("loaf", big=False, flip=False)

            self.root.after(3600, lambda: self.animator.set_state("watching", big=False, flip=False))

            end_state="play" if is_awake else "sleeping"

            self.root.after(6800, lambda: self.animator.set_state(end_state, big=False, flip=False) if not self.walk_active else None)

        elif r < 0.62:

            print("🐱 grooming")

            self.animator.set_state("groom", big=False, flip=False)

            self._show_bubble("lick lick ✨", 2200)

            self.root.after(3800, lambda: self.animator.set_state("blink", big=False, flip=False))

            end_state="play" if is_awake else "sleeping"

            self.root.after(5200, lambda: self.animator.set_state(end_state, big=False, flip=False) if not self.walk_active else None)

        elif r < 0.78:

            print("🐱 kneading biscuits")

            self.animator.set_state("knead", big=False, flip=False)

            self._show_bubble("knead knead ♡", 2600)

            end_state="play" if is_awake else "sleeping"

            self.root.after(4000, lambda: self.animator.set_state(end_state, big=False, flip=False) if not self.walk_active else None)

        else:

            print("🐱 playful pounce")

            self.animator.set_state("play", big=False, flip=False)

            self.root.after(2200, lambda: self.animator.set_state("watching", big=False, flip=False))

            end_state="play" if is_awake else "sleeping"

            self.root.after(4600, lambda: self.animator.set_state(end_state, big=False, flip=False) if not self.walk_active else None)

        self.last_activity=time.time()-random.randint(2,6) if is_awake else time.time()-random.randint(3,8)



    def _walk_to_spot(self, target_x):

        if self.is_duck or self.walk_active: return

        print(f"🚶 walk to {target_x}")

        try:

            if self._anim_after:

                self.root.after_cancel(self._anim_after); self._anim_after=None

        except: pass

        self.walk_dir = 1 if target_x > (self.walk_x or target_x) else -1

        self.animator.set_state("walking", big=False, flip=(self.walk_dir<0))

        self.walk_active=True

        self._walk_target=target_x

        self._walk_to_step()



    def _walk_to_step(self):

        if not self.walk_active or self.is_duck:

            self.walk_active=False; self._walk_after=None; return

        # clamp target to taskbar

        tr=get_taskbar_rect()

        sw,_=get_screen_size()

        if tr:

            l,_,r,_=tr; min_x=l+2; max_x=r - self.pet_w -2

        else:

            min_x=2; max_x=sw - self.pet_w -2

        self._walk_target=max(min_x, min(max_x, self._walk_target))

        diff = self._walk_target - self.walk_x

        if abs(diff) < 6:

            self.walk_x = self._walk_target

            _, y = calc_position(self.pet_w, self.pet_h, self.placement)

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

        _, y = calc_position(self.pet_w, self.pet_h, self.placement)

        self._walk_bob=(self._walk_bob+1)%4; bob_y=1 if self._walk_bob in (1,2) else 0

        if self._walk_bob==2: bob_y=2

        self.root.geometry(f"{self.pet_w}x{self.pet_h}+{int(self.walk_x)}+{y - bob_y}")

        if self._walk_bob%4==0: self._save_pos()

        self._walk_after=self.root.after(32, self._walk_to_step)



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

            if random.random() < 0.3:

                self.walk_dir *= -1

        self.animator.set_state("walking", big=False, flip=(self.walk_dir<0))

        self.walk_active=True

        sw, _ = get_screen_size()

        self.walk_x = max(8, min(sw - self.pet_w - 8, self.walk_x))

        self._anim_after = self.root.after(10, self.animate)

        self._walk_step()



    def _walk_step(self):

        if not self.walk_active or self.is_duck:

            self.walk_active=False; self._walk_after=None; return

        # walk everywhere: use taskbar rect, not screen 8..sw-8

        tr=get_taskbar_rect()

        sw, _ = get_screen_size()

        if tr:

            l,_,r,_=tr

            min_x=l+2; max_x=r - self.pet_w -2

        else:

            min_x=2; max_x=sw - self.pet_w -2

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

        if self._long_absence_done:

            self._welcome_back()

            return

        if self.is_petting:

            return

        print("💖 petted!")

        self.is_petting=True

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

                self.root.after(160, lambda: self.root.geometry(f"{orig_w}x{orig_h}+{x}+{y+ (pop_h-orig_h)}"))

            except: pass

        bounce()

        self.root.after(2200, self._end_pet)



    def _end_pet(self):

        self.is_petting=False

        if self.is_duck:

            self.animator.set_state("duck", big=True)

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

            sw,_=get_screen_size()

            x=max(8, min(sw - self.pet_w - 8, x))

            _, y = calc_position(self.pet_w, self.pet_h, self.placement)

            self.root.geometry(f"{self.pet_w}x{self.pet_h}+{x}+{y}")

            self.walk_x=x

            self._save_pos()

            self._record_favorite(x)

            self.animator.set_state("watching", big=False, flip=False)

            self.root.after(1200, lambda: self.animator.set_state("sleeping", big=False, flip=False) if not self.walk_active and not self._is_dont_sleep() else None)

            self.last_activity=time.time() - 12

            self.bored_since=time.time()

            if hasattr(self,'_walk_steps'): self._walk_steps=0

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

        "Your effort today is tomorrow s portfolio",

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

        elif not should and self.is_duck:

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

                            self.root.after(4200, lambda: self.animator.set_state("sleeping", big=False, flip=False) if not self.walk_active else None)

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

    # single-word index for fuzzy token matching

    FOOD_SINGLE = {w for w in FOOD_WORDS if " " not in w}



    def _get_fg_process(self):

        try:

            hwnd=ctypes.windll.user32.GetForegroundWindow()

            pid=ctypes.c_ulong()

            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            import psutil

            return psutil.Process(pid.value).name().lower() if pid.value else ""

        except: return ""



    def _lev(self, a,b):

        # tiny Levenshtein for fuzzy typo (biriyani vs biryani)

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

                    if not self.is_duck:

                        self.bored_since=now

                        self.root.after(180, self.trigger_walk)

                    self.root.after(4800, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self.animator.get_state()=="pet" and not self._is_dont_sleep() else None)

        except Exception as e:

            print("food err",e)

        self.root.after(1200, self.food_check)



    def set_activity_state(self, active, reason):

        # background CPU is NOT life - keep chill baseline, just log, don't twitch

        # only update bored timer so not considered idle while PC busy

        if active:

            self.bored_since=time.time()

            # optional: very subtle 4% chance she glances, not hyper wake

            if random.random()<0.04 and not self.is_duck and not self.walk_active and not self.is_petting and self.animator.get_state()=="sleeping":

                self.animator.set_state("watching", big=False, flip=False)

                self.root.after(2800, lambda: self.animator.set_state("sleeping", big=False, flip=False) if not self.walk_active else None)



    # --- gift emotional touches ---

    def ask_name_if_needed(self):

        if self.memory.get("name") or self._name_pending:

            return

        self._name_pending=True

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

            pth=_pl.Path(__file__).parent.parent / "assets" / "sprites" / "frame_4.png"

            if not pth.exists():

                pth=_pl.Path(r"D:\KITTY\assets\sprites\frame_4.png")

            im=Image.open(pth).convert("RGBA").resize((72,72), Image.LANCZOS)

            tk_img=ImageTk.PhotoImage(im)

            dlg._kitten_img=tk_img

        except Exception:

            try:

                tk_img=tk.PhotoImage(file=r"D:\KITTY\assets\sprites\frame_4.png")

                dlg._kitten_img=tk_img

            except Exception:

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



    def _show_bubble(self, text, ms=4000):

        try:

            if getattr(self, "_food_bubble", None) and self._food_bubble and self._food_bubble.winfo_exists():

                try: self._food_bubble.destroy()

                except: pass

            bub=tk.Toplevel(self.root)

            bub.overrideredirect(True); bub.attributes("-topmost", True); bub.configure(bg="#FFF8DC")

            lab=tk.Label(bub, text=text, bg="#FFF8DC", fg="#5a3e2b", font=("Segoe UI",9,"bold"), padx=10, pady=6, bd=1, relief="solid")

            lab.pack()

            bub.update_idletasks()

            bw = bub.winfo_reqwidth(); bh = bub.winfo_reqheight()

            sw,sh = get_screen_size()

            x=self.root.winfo_x()+self.pet_w//2 - bw//2; y=self.root.winfo_y()-bh-6

            x=max(8, min(sw - bw - 8, x))

            y=max(8, y)

            bub.geometry(f"{bw}x{bh}+{x}+{y}")

            self._food_bubble=bub

            self.root.after(ms, lambda: bub.destroy() if bub.winfo_exists() else None)

        except: pass



    def _play_meow(self, kind="meow"):
        if self.memory.get("is_muted"):
            print("muted"); return
        def _do():
            try:
                import pathlib
                import sys as _sys
                base = pathlib.Path(_sys._MEIPASS) if getattr(_sys, 'frozen', False) else pathlib.Path(__file__).parent.parent  # type: ignore
                mp3 = base / "assets" / "cat-purr-meow.mp3"
                if not mp3.exists():
                    mp3 = pathlib.Path(r"F:\edr-cat-purr-meow-8327.mp3")
                # prefer pygame for MP3, fallback to winsound
                played=False
                try:
                    import pygame  # type: ignore
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    pygame.mixer.music.load(str(mp3))
                    pygame.mixer.music.play()
                    played=True
                except: pass
                if not played:
                    try:
                        import winsound
                        winsound.PlaySound(str(mp3), winsound.SND_FILENAME | winsound.SND_ASYNC)
                        played=True
                    except: pass
                if not played:
                    import winsound
                    winsound.Beep(880, 110); winsound.Beep(1046, 140)
            except: pass
            print(f"sound {kind} meow mp3")
        import threading
        threading.Thread(target=_do, daemon=True).start()


    def toggle_mute(self):

        self.memory["is_muted"]=not self.memory.get("is_muted", False); mem.save(self.memory)

        state="muted 🔇" if self.memory["is_muted"] else "sound on 🔊"

        self._show_bubble(state, 2500)

        try:

            new_lab="Unmute 🔊" if self.memory["is_muted"] else "Mute 🔇"

            self.menu.entryconfig(8, label=new_lab)

        except: pass

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

            def trigger(mid, msg):

                if mid not in m:

                    m.append(mid); self.memory["milestones"]=m; mem.save(self.memory)

                    self._show_bubble(msg, 6000)

                    # heart burst: big pet then bounce

                    self.animator.set_state("pet", big=self.is_duck)

                    self._play_meow()

                    # pop size burst

                    try:

                        ow,oh=self.pet_w,self.pet_h

                        pw,ph=int(ow*1.28), int(oh*1.28)

                        x=self.root.winfo_x(); y=self.root.winfo_y()-(ph-oh)

                        self.root.geometry(f"{pw}x{ph}+{x}+{y}")

                        self.root.after(320, lambda: self.root.geometry(f"{ow}x{oh}+{x}+{y+(ph-oh)}"))

                    except: pass

                    self.root.after(5200, lambda: self.animator.set_state("sleeping", big=False, flip=False) if self.animator.get_state()=="pet" else None)

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

                self._show_bubble(f"Missed you! 💌", 5000)

                self.animator.set_state("pet", big=False, flip=False)

                self._play_meow()

                self.root.after(4800, lambda: self.animator.set_state("sleeping", big=False, flip=False))

                # also heart burst

            elif d==1 and not self.walk_active:

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

                self._show_bubble(msg, 5000)

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
                    self._show_bubble(f"11:11 {ampm} -- make a wish", 7000)
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

                print("waiting bubble only - no drift while sleeping")

                self.root.after(6000, lambda: self.animator.set_state("sleeping", big=False, flip=False) if not self._is_dont_sleep() else None)

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

            prev=self.animator.get_state()

            self.animator.set_state("blink", big=self.is_duck)

            self.root.after(ms, lambda: callback())

        except:

            callback()



    def trigger_luck(self):

        idx=self.memory.get("luck_message_index",0)

        msgs=self.LUCK_MESSAGES

        msg=msgs[idx % len(msgs)]

        self.memory["luck_message_index"]=(idx+1)%len(msgs); mem.save(self.memory)

        self._notice_beat(lambda: self._show_bubble(msg, 5000))

        self.animator.set_state("pet", big=self.is_duck)

        # determined supportive bounce

        try:

            ow,oh=self.pet_w,self.pet_h; pw,ph=int(ow*1.22),int(oh*1.22)

            x=self.root.winfo_x(); y=self.root.winfo_y()-(ph-oh)

            self.root.geometry(f"{pw}x{ph}+{x}+{y}")

            self.root.after(260, lambda: self.root.geometry(f"{ow}x{oh}+{x}+{y+(ph-oh)}"))

        except: pass

        self._play_meow()

        self.root.after(4500, lambda: self.animator.set_state("sleeping", big=False, flip=False))

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

                        self.root.after(900, lambda: self.animator.set_state("sleeping", big=False, flip=False) if not self.walk_active else None)

                        print("👀 glance at cursor")

                    elif random.random()<0.06:

                        # glance at clock

                        self._last_glance=time.time()

                        self.animator.set_state("blink", big=False, flip=False)

                        self.root.after(600, lambda: self.animator.set_state("sleeping", big=False, flip=False))

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

                    self.root.after(800, lambda: self.animator.set_state("sleeping", big=False, flip=False) if not self.walk_active else None)

                    self._show_bubble("missed you… ears down 🥺", 5000)

                    print("💤 long absence: missing you state")

        except: pass

        self.root.after(60000, self._check_long_absence)



    def _welcome_back(self):

        if self._long_absence_done:

            self._long_absence_done=False

            # fast ears-up, hop, extra happy

            self._show_bubble("you're back! hop! 💖", 4500)

            self.animator.set_state("waking", big=False, flip=False)

            try:

                ow,oh=self.pet_w,self.pet_h; pw,ph=int(ow*1.25),int(oh*1.25)

                x=self.root.winfo_x(); y=self.root.winfo_y()-(ph-oh)-6

                self.root.geometry(f"{pw}x{ph}+{x}+{y}")

                self.root.after(180, lambda: self.root.geometry(f"{ow}x{oh}+{x}+{y+(ph-oh)+6}"))

                self.root.after(350, lambda: self.root.geometry(f"{pw}x{ph}+{x}+{y}"))

                self.root.after(530, lambda: self.root.geometry(f"{ow}x{oh}+{x}+{y+(ph-oh)+6}"))

            except: pass

            self.root.after(1200, lambda: self.animator.set_state("pet", big=False, flip=False))

            self.root.after(3000, lambda: self.animator.set_state("sleeping", big=False, flip=False))

            self._play_meow()

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

            try: self.menu.entryconfig(7, label="Don't sleep 30m ☕")

            except: pass

            self._show_bubble("Okay, sleepy now Zzz 😴", 3000)

            self.animator.set_state("sleeping", big=False, flip=False)

            print("Don't sleep OFF")

        else:

            self._dont_sleep_until=time.time()+30*60

            try: self.menu.entryconfig(7, label="Don't sleep ✓ (30m)")

            except: pass

            self._show_bubble("I won't sleep for 30m! ☕", 4000)

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

        try: self.menu.entryconfig(7, label=f"Don't sleep ✓ ({left}m)")

        except: pass

        self._dont_sleep_tick_after=self.root.after(60*1000, self._dont_sleep_tick)



    def _dont_sleep_expire(self):

        self._dont_sleep_until=0

        self._dont_sleep_after=None

        try: self.menu.entryconfig(7, label="Don't sleep 30m ☕")

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



    def _save_pos(self):

        try:

            if self.walk_x is not None:

                self._pos_file.write_text(str(int(self.walk_x)))

                # also persist favorite + memory pos

                try:

                    self.memory["pos_x"]=int(self.walk_x)

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

        self._save_pos()

        try: mem.save(self.memory)

        except: pass

        self.root.destroy()



    def run(self):

        self.root.mainloop()

