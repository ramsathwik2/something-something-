"""Generate README visuals for the GitHub repo.

Creates docs/img/hero.png (static preview) and docs/img/walk.gif (looping
walk cycle) from the real sprite sheets, upscaled with NEAREST to keep the
pixel art crisp. No private/real data is used - only the sprites.

Usage:  py -3 tools/make_preview.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "assets", "sprites")
OUT = os.path.join(ROOT, "docs", "img")


def load(name):
    return Image.open(os.path.join(SPRITES, name)).convert("RGBA")


def upscale(img, scale):
    w, h = img.size
    return img.resize((w * scale, h * scale), Image.NEAREST)


def font(size):
    for name in ("segoeui.ttf", "arial.ttf", "dejavusans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_hero():
    W, H = 1280, 440
    img = Image.new("RGBA", (W, H), "#241c33")

    draw = ImageDraw.Draw(img)
    top = (80, 76, 140)
    bot = (20, 16, 42)
    for y in range(H):
        t = y / H
        c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=c)

    for x, y, r in ((1150, 70, 110), (60, 330, 60), (700, 40, 90), (1230, 160, 40)):
        glow = Image.new("RGBA", (r * 4, r * 4), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for i in range(3, -1, -1):
            alpha = int(14 * (i + 1))
            gd.ellipse(
                [r * 2 - r * (i + 1), r * 2 - r * (i + 1), r * 2 + r * (i + 1), r * 2 + r * (i + 1)],
                fill=(255, 214, 170, alpha),
            )
        img.alpha_composite(glow, (x - r * 2, y - r * 2))

    scale = 5
    cat = upscale(load("frame_4.png"), scale)
    cat_w, cat_h = cat.size
    cat_x = 200
    cat_y = H - 96 - cat_h

    bubble = Image.new("RGBA", (560, 150), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bubble)
    bd.rounded_rectangle([0, 0, 560, 150], radius=26, fill=(255, 248, 240, 255))
    bd.polygon([(150, 150), (180, 150), (150, 165 + 20)], fill=(255, 248, 240, 255))
    f_big = font(34)
    f_small = font(22)
    bd.text((40, 34), "Meow!  I live on your taskbar \u2728", font=f_big, fill=(60, 42, 30))
    bd.text((42, 92), "Gayathree's Journal - kept safe and private", font=f_small, fill=(120, 95, 70))
    img.paste(bubble, (cat_x + cat_w + 24, cat_y + 20), bubble)

    img.paste(cat, (cat_x, cat_y), cat)
    bd2 = ImageDraw.Draw(img)
    f_hero = font(58)
    f_sub = font(26)
    bd2.text((cat_x + cat_w + 24, 190), "Madhu \u00b7 Taskbar Kitten", font=f_hero, fill=(255, 228, 196))
    bd2.text((cat_x + cat_w + 24, 262), "a tiny cat for your taskbar", font=f_sub, fill=(255, 200, 170))

    task_y = H - 84
    bd2.rounded_rectangle([0, task_y, W, H], radius=14, fill=(16, 12, 28))
    bd2.line([(0, task_y + 2), (W, task_y + 2)], fill=(70, 60, 95))
    tray_x = W - 60
    for i in range(4):
        bd2.ellipse([tray_x - i * 28 - 10, task_y + 30, tray_x - i * 28, task_y + 50], fill=(150, 140, 175))
        bd2.rounded_rectangle([tray_x - i * 28 - 13, task_y + 12, tray_x - i * 28 - 7, task_y + 26], fill=(150, 140, 175))
    clock = Image.new("RGBA", (170, 70), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clock)
    cd.rounded_rectangle([0, 0, 170, 70], radius=10, fill=(30, 24, 48, 255))
    cd.text((14, 14), "11:11", font=font(30), fill=(255, 214, 170))
    img.paste(clock, (tray_x - 190, task_y + 8), clock)

    os.makedirs(OUT, exist_ok=True)
    img.convert("RGB").save(os.path.join(OUT, "hero.png"))
    print("wrote docs/img/hero.png", img.size)


def make_walk():
    frames = [upscale(load(f"walk_{i}.png"), 4) for i in range(4)]
    for i, fr in enumerate(frames):
        canvas = Image.new("RGBA", (fr.width, fr.height), (0, 0, 0, 0))
        canvas.alpha_composite(fr)
        frames[i] = canvas
    frames[0].save(
        os.path.join(OUT, "walk.gif"),
        save_all=True,
        append_images=frames[1:],
        duration=220,
        loop=0,
        disposal=2,
        transparency=0,
    )
    print("wrote docs/img/walk.gif", frames[0].size)


if __name__ == "__main__":
    make_hero()
    make_walk()