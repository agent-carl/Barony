#!/usr/bin/env python3
"""Project Umbra — animation frames for animated tiles (gaslamp, fireplace,
candles, water). 4 frames each, deterministic; the engine's animatedtiles
system steps through consecutive tile indices.

Output: <name>_f0..f3.png + preview_animations.png (frames side by side).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# reuse palettes and base tiles from the main generator
import gen_textures as G  # noqa: E402  (runs its generation once as a side effect)

from PIL import Image  # noqa: E402
import random  # noqa: E402

S = G.S
PAL = G.PAL
shade = G.shade
noisy = G.noisy


def flame_jitter(img, cx, cy, frame, rng, height=4, width=2, palette=("flame_core", "flame", "flame_deep")):
    """Redraw a small flame around (cx, cy) with per-frame sway."""
    px = img.load()
    sway = (-1, 0, 1, 0)[frame % 4]
    for dy in range(height):
        w = max(0, width - dy // 2)
        for dx in range(-w, w + 1):
            x = cx + dx + (sway if dy > height // 2 else 0)
            y = cy - dy
            if 0 <= x < S and 0 <= y < S:
                key = palette[0] if abs(dx) == 0 and dy > 0 else palette[1] if dy > 0 else palette[2]
                if rng.random() < 0.92:
                    px[x, y] = PAL[key]
    return img


def gaslamp_frames():
    frames = []
    for f in range(4):
        img = G.gaslamp_wall()
        rng = random.Random(1000 + f)
        px = img.load()
        # vary the glass glow slightly and sway the flame core
        flicker = (0, 6, -4, 3)[f]
        for y in range(9, 13):
            for x in range(14, 19):
                r, g, b = px[x, y]
                px[x, y] = (max(0, min(255, r + flicker)),
                            max(0, min(255, g + flicker // 2)), b)
        flame_jitter(img, 16, 12, f, rng, height=3, width=1)
        frames.append(img)
    return frames


def fireplace_frames():
    frames = []
    for f in range(4):
        img = G.fireplace()
        rng = random.Random(2000 + f)
        px = img.load()
        # embers pulse and flames lick at different heights
        pulse = (0, 8, 14, 6)[f]
        for x in range(10, 22):
            for y in range(20, 26):
                r, g, b = px[x, y]
                px[x, y] = (max(0, min(255, r + pulse)), g, b)
        for tongue in range(3):
            tx = 12 + tongue * 3 + (f % 2)
            flame_jitter(img, tx, 19 - (f + tongue) % 3, f + tongue, rng, height=3, width=1)
        frames.append(img)
    return frames


def candles_frames():
    frames = []
    for f in range(4):
        img = G.wall_candles()
        rng = random.Random(3000 + f)
        px = img.load()
        # each candle's flame leans a different way per frame
        for x in range(4, 28):
            for y in range(6, 20):
                p = px[x, y]
                if p[:3] == PAL["flame_core"]:
                    lean = (-1, 0, 1, 0)[(f + x) % 4]
                    if 0 <= x + lean < S:
                        px[x, y] = img.getpixel((x, y))
                        px[x + lean, y] = PAL["flame_core"]
                        if lean != 0:
                            px[x, y] = PAL["flame"]
        frames.append(img)
    return frames


def water_frames():
    frames = []
    for f in range(4):
        img = G.floor_water()
        rng = random.Random(4000 + f)
        px = img.load()
        # drifting ripple highlights
        for _ in range(6):
            rx, ry, rl = rng.randint(2, 26), rng.randint(2, 29), rng.randint(3, 7)
            for i in range(rl):
                px[(rx + i + f) % S, ry] = PAL["water_hl"]
        frames.append(img)
    return frames


out = os.environ.get("OUT_DIR", ".")
os.makedirs(out, exist_ok=True)

anims = {
    "anim_gaslamp": gaslamp_frames(),
    "anim_fireplace": fireplace_frames(),
    "anim_candles": candles_frames(),
    "anim_water": water_frames(),
}
for name, frames in anims.items():
    for i, img in enumerate(frames):
        img.save(f"{out}/{name}_f{i}.png")

# preview: one row per animation, frames left to right, 5x scale
scale = 5
gap = 8
w = 4 * (S * scale + gap) - gap
h = len(anims) * (S * scale + gap) - gap
sheet = Image.new("RGB", (w, h), (12, 12, 14))
for row, (name, frames) in enumerate(anims.items()):
    for col, img in enumerate(frames):
        big = img.resize((S * scale, S * scale), Image.NEAREST)
        sheet.paste(big, (col * (S * scale + gap), row * (S * scale + gap)))
sheet.save(f"{out}/preview_animations.png")
print("generated animations:", ", ".join(anims.keys()))
