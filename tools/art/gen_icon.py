#!/usr/bin/env python3
"""Project Umbra — generate the application icon (pixel gas lamp).

Draws a 32x32 pixel lantern and upscales nearest-neighbor to 256/128/64/48/32.
Deterministic. Output: Umbra_Icon<N>x<N>.png in OUT_DIR (default '.').
"""
import os
import random
from PIL import Image

S = 32
PAL = {
    "bg":         (16, 17, 20),
    "bg_glow":    (46, 40, 28),
    "iron":       (38, 36, 40),
    "iron_hl":    (70, 66, 72),
    "brass":      (140, 108, 52),
    "brass_hl":   (196, 158, 84),
    "flame_core": (255, 232, 160),
    "flame":      (240, 178, 84),
    "flame_deep": (196, 116, 48),
    "glass":      (255, 214, 130),
}

def icon32(seed=5):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["bg"])
    px = img.load()
    cx = 16
    # radial warm glow
    for x in range(S):
        for y in range(S):
            d2 = (x - cx) ** 2 + (y - 14) ** 2
            if d2 < 210:
                f = (210 - d2) / 210.0
                r, g, b = px[x, y]
                px[x, y] = (min(255, int(r + 96 * f)),
                            min(255, int(g + 66 * f)),
                            min(255, int(b + 14 * f)))
    # hanging ring and hook
    for x in range(cx - 2, cx + 3):
        px[x, 2] = PAL["iron_hl"] if x == cx else PAL["iron"]
    px[cx, 3] = PAL["iron"]
    # lantern crown
    for x in range(cx - 4, cx + 5):
        px[x, 5] = PAL["brass_hl"] if x % 3 else PAL["brass"]
    for x in range(cx - 5, cx + 6):
        px[x, 6] = PAL["brass"]
    px[cx, 4] = PAL["brass_hl"]
    # glass body with cage bars
    for y in range(7, 22):
        for x in range(cx - 6, cx + 7):
            dx = abs(x - cx)
            if dx == 6:
                px[x, y] = PAL["brass"] if y % 2 else PAL["brass_hl"]
            elif dx == 3 and y % 5 != 2:
                px[x, y] = PAL["brass"]  # cage bars
            else:
                dy = abs(y - 14)
                if dx <= 1 and dy <= 4:
                    px[x, y] = PAL["glass"]
                elif dx <= 3 and dy <= 6:
                    px[x, y] = PAL["flame"]
                else:
                    px[x, y] = PAL["flame_deep"]
    # flame core
    for y in range(11, 18):
        px[cx, y] = PAL["flame_core"]
    px[cx, 10] = PAL["flame"]
    # base
    for x in range(cx - 5, cx + 6):
        px[x, 22] = PAL["brass"]
    for x in range(cx - 4, cx + 5):
        px[x, 23] = PAL["brass_hl"] if x % 2 else PAL["brass"]
    for x in range(cx - 2, cx + 3):
        px[x, 24] = PAL["iron"]
    # tiny sparks
    for _ in range(6):
        x = cx + rng.randint(-9, 9)
        y = rng.randint(24, 29)
        if img.getpixel((x, y)) == PAL["bg"]:
            px[x, y] = PAL["flame_deep"]
    return img

out = os.environ.get("OUT_DIR", ".")
os.makedirs(out, exist_ok=True)
base = icon32()
for size in (256, 128, 64, 48, 32):
    base.resize((size, size), Image.NEAREST).save(f"{out}/Umbra_Icon{size}x{size}.png")
print("generated Umbra icons: 256/128/64/48/32")
