from PIL import Image, ImageTk
import pathlib

class SpriteAnimator:
    def __init__(self, sprite_dir):
        self.dir = pathlib.Path(sprite_dir)
        self.TARGET = 56
        self.BIG = 96
        # base 8 frames (sleep/alert etc)
        self.frames = []
        for i in range(8):
            p = self.dir / f"frame_{i}.png"
            if p.exists():
                im = Image.open(p).convert("RGBA")
                self.frames.append(im)
        # also try sheet.png fallback
        if not self.frames:
            sheet = self.dir / "sheet.png"
            if sheet.exists():
                im = Image.open(sheet).convert("RGBA")
                sw,sh = im.size
                n = sw // 56
                for i in range(n):
                    crop = im.crop((i*56,0,(i+1)*56,56))
                    self.frames.append(crop)
        # walk frames 4
        self.walk_frames=[]
        for i in range(4):
            p=self.dir / f"walk_{i}.png"
            if p.exists():
                self.walk_frames.append(Image.open(p).convert("RGBA"))
        # pet frames 3
        self.pet_frames=[]
        for i in range(3):
            p=self.dir / f"pet_{i}.png"
            if p.exists():
                self.pet_frames.append(Image.open(p).convert("RGBA"))
        # ensure sizes
        from PIL import Image as _Img
        def ensure(lst):
            out=[]
            for f in lst:
                if f.size != (self.TARGET, self.TARGET):
                    f=f.resize((self.TARGET,self.TARGET), _Img.NEAREST)
                out.append(f)
            return out
        self.frames=ensure(self.frames)
        self.walk_frames=ensure(self.walk_frames)
        self.pet_frames=ensure(self.pet_frames)

        # build big variants (96px) for rubber-duck mode - scale up with NEAREST to keep pixel crisp
        def make_big(lst):
            return [f.resize((self.BIG,self.BIG), _Img.NEAREST) for f in lst]
        def make_flip(lst):
            return [f.transpose(_Img.FLIP_LEFT_RIGHT) for f in lst]
        self.frames_big=make_big(self.frames) if self.frames else []
        self.walk_big=make_big(self.walk_frames) if self.walk_frames else []
        self.pet_big=make_big(self.pet_frames) if self.pet_frames else []
        self.walk_flipped=make_flip(self.walk_frames) if self.walk_frames else []
        self.walk_big_flipped=make_flip(self.walk_big) if self.walk_big else []

        if not self.frames:
            raise FileNotFoundError(f"No frames found in {self.dir}")

        # real cat repertoire reusing frames
        self.states = {
            "sleeping": ("base", [0,1], 2200),
            "waking":   ("base", [2,3], 180),      # yawn/stretch tail up
            "alert":    ("base", [4,5,6], 320),    # perky ears
            "watching": ("base", [6,4,5], 1100),   # birds
            "blink":    ("base", [7,4], 900),      # slow blink loaf
            "walking":  ("walk", [0,1,2,3], 140),
            "pet":      ("pet",  [0,1,2,1,0], 220), # hearts
            "duck":     ("base", [4,5,4,6], 350),
            # new cat-like idles reusing existing art
            "groom":    ("pet",  [2,2,0,0], 420),   # purring loaf lick (pet_2 = loaf side)
            "loaf":     ("base", [4,7,4], 1400),   # loaf sit, slow blink
            "stretch":  ("base", [2,3,3,2], 280),  # long yawn stretch
            "knead":    ("pet",  [0,1,0,1], 300),  # paw knead hearts
            "play":     ("walk", [3,2,1,0], 110),  # playful pounce variant
        }
        self.state="sleeping"
        self.idx=0
        self.is_big=False
        self.flip_walk=False

    def set_state(self, state, big=False, flip=False):
        if state in self.states:
            if state != self.state:
                self.state=state; self.is_big=big; self.flip_walk=flip; self.idx=0
            else:
                # same state: update big/flip without resetting frame idx (no pop)
                self.is_big=big; self.flip_walk=flip

    def set_walk_direction(self, dir):
        # dir = 1 right, -1 left
        want_flip = (dir < 0)
        if want_flip != self.flip_walk and self.state=="walking":
            self.flip_walk=want_flip
            # don't reset idx so walk stays smooth

    def next_frame(self):
        kind, seq, delay = self.states[self.state]
        if kind=="base":
            lst = self.frames_big if self.is_big else self.frames
        elif kind=="walk":
            if self.flip_walk:
                lst = self.walk_big_flipped if self.is_big else self.walk_flipped
            else:
                lst = self.walk_big if self.is_big else self.walk_frames
            if not lst:
                lst=self.frames_big if self.is_big else self.frames
                seq=[0,1]
        elif kind=="pet":
            lst = self.pet_big if self.is_big else self.pet_frames
            if not lst:
                lst=self.frames
                seq=[4,5,6]
        else:
            lst=self.frames
        pil_img = lst[seq[self.idx % len(seq)]]
        self.idx = (self.idx + 1) % len(seq)
        tk_img = ImageTk.PhotoImage(pil_img)
        size = self.BIG if self.is_big else self.TARGET
        return tk_img, delay, size

    def _to_tk(self, pil_img):
        return ImageTk.PhotoImage(pil_img)

    def get_state(self):
        return self.state
