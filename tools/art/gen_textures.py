#!/usr/bin/env python3
"""Project Umbra — generate sample pixel textures (gothic-Victorian style).

Deterministic (seeded). Output: 32x32 PNG tiles + an 8x preview sheet.
"""
import random
from PIL import Image

S = 32  # Barony tile size

# --- Victorian-gothic palette ---------------------------------------------
# Cold, slightly blue-green stone; warm gaslight amber as the single accent.
PAL = {
    "mortar":      (24, 26, 30),
    "stone_dark":  (52, 56, 62),
    "stone_mid":   (68, 73, 80),
    "stone_light": (86, 92, 100),
    "stone_hl":    (108, 115, 122),
    "moss":        (58, 72, 58),
    "floor_dark":  (44, 46, 50),
    "floor_mid":   (58, 61, 66),
    "floor_light": (74, 78, 84),
    "iron":        (38, 36, 40),
    "iron_hl":     (70, 66, 72),
    "brass":       (140, 108, 52),
    "brass_hl":    (196, 158, 84),
    "flame_core":  (255, 232, 160),
    "flame":       (240, 178, 84),
    "flame_deep":  (196, 116, 48),
    "glass_glow":  (255, 214, 130),
    "wood_dark":   (46, 34, 26),
    "wood_mid":    (66, 48, 36),
    "wood_light":  (88, 64, 46),
    "wood_hl":     (110, 82, 58),
    "paper_base":  (36, 48, 42),
    "paper_deep":  (28, 38, 34),
    "paper_motif": (96, 84, 48),
    "void":        (8, 8, 10),
}

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)

def noisy(px, x, y, c, rng, amount=6):
    n = rng.randint(-amount, amount)
    px[x, y] = tuple(max(0, min(255, v + n)) for v in c)

# --- Stone wall: coursed masonry ------------------------------------------
def stone_wall(seed=7):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    courses = [(0, 7), (8, 15), (16, 23), (24, 31)]
    for ci, (y0, y1) in enumerate(courses):
        # stones in a course: variable widths, offset per course
        x = -rng.randint(0, 5) if ci % 2 else 0
        while x < S:
            w = rng.randint(7, 12)
            base = rng.choice([PAL["stone_dark"], PAL["stone_mid"], PAL["stone_mid"], PAL["stone_light"]])
            mossy = rng.random() < 0.18
            for sx in range(max(0, x), min(S, x + w)):
                for sy in range(y0, y1 + 1):
                    edge_l = sx == x
                    edge_t = sy == y0
                    edge_r = sx == x + w - 1
                    edge_b = sy == y1
                    if edge_r or edge_b:  # mortar gap
                        px[sx, sy] = PAL["mortar"]
                    elif edge_l or edge_t:  # top-left catch light
                        noisy(px, sx, sy, shade(base, 1.22), rng, 4)
                    else:
                        c = base
                        if mossy and sy > y0 + (y1 - y0) // 2 and rng.random() < 0.35:
                            c = PAL["moss"]
                        noisy(px, sx, sy, c, rng)
            x += w
    return img

# --- Flagstone floor --------------------------------------------------------
def stone_floor(seed=11):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    # 2x2 large worn slabs with jittered joints
    jx = 16 + rng.randint(-2, 2)
    jy = 16 + rng.randint(-2, 2)
    quads = [(0, 0, jx, jy), (jx, 0, S, jy), (0, jy, jx, S), (jx, jy, S, S)]
    for (x0, y0, x1, y1) in quads:
        base = rng.choice([PAL["floor_dark"], PAL["floor_mid"], PAL["floor_light"]])
        for x in range(x0, x1):
            for y in range(y0, y1):
                if x == x1 - 1 or y == y1 - 1:
                    px[x, y] = PAL["mortar"]
                elif x == x0 or y == y0:
                    noisy(px, x, y, shade(base, 1.12), rng, 4)
                else:
                    noisy(px, x, y, base, rng, 5)
        # cracks
        if rng.random() < 0.75:
            cx, cy = rng.randint(x0 + 2, max(x0 + 3, x1 - 3)), y0 + 2
            for _ in range(rng.randint(4, 9)):
                if x0 <= cx < x1 - 1 and y0 <= cy < y1 - 1:
                    px[cx, cy] = shade(base, 0.6)
                cx += rng.choice([-1, 0, 1])
                cy += 1
    return img

# --- Wall tile with a brass gas lamp ---------------------------------------
def gaslamp_wall(seed=7):
    img = stone_wall(seed)  # same masonry underneath
    px = img.load()
    rng = random.Random(seed + 99)
    cx = 16
    # warm ambient glow on the stones (radial, subtle)
    for x in range(S):
        for y in range(S):
            d2 = (x - cx) ** 2 + (y - 12) ** 2
            if d2 < 130:
                f = (130 - d2) / 130.0 * 0.55
                r, g, b = px[x, y]
                px[x, y] = (min(255, int(r + 90 * f)),
                            min(255, int(g + 60 * f)),
                            min(255, int(b + 10 * f)))
    # iron back-plate and bracket
    for y in range(18, 24):
        for x in range(cx - 1, cx + 2):
            px[x, y] = PAL["iron"] if x != cx else PAL["iron_hl"]
    # brass stem
    for y in range(14, 18):
        px[cx, y] = PAL["brass"]
        px[cx - 1, y] = shade(PAL["brass"], 0.8)
    # glass housing (lantern box)
    for y in range(8, 14):
        for x in range(cx - 3, cx + 4):
            dx, dy = abs(x - cx), abs(y - 11)
            if dx == 3 or y == 8 or y == 13:
                px[x, y] = PAL["brass"] if (x + y) % 2 else PAL["brass_hl"]
            else:
                px[x, y] = PAL["glass_glow"] if dx <= 1 and dy <= 2 else PAL["flame"]
    # flame core
    px[cx, 11] = PAL["flame_core"]
    px[cx, 10] = PAL["flame_core"]
    px[cx, 12] = PAL["flame_deep"]
    # brass finial
    px[cx, 7] = PAL["brass_hl"]
    return img

# --- Victorian wood panelling (wainscot) ------------------------------------
def wood_panel(seed=23):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["wood_dark"])
    px = img.load()
    # horizontal grain base
    for y in range(S):
        band = rng.choice([PAL["wood_mid"], PAL["wood_mid"], PAL["wood_light"]])
        for x in range(S):
            c = band
            if rng.random() < 0.08:
                c = shade(band, 0.8)  # grain flecks
            noisy(px, x, y, c, rng, 4)
    # raised panel: outer frame, bevel, inner field
    def frame(x0, y0, x1, y1):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                on_edge = x in (x0, x1) or y in (y0, y1)
                inner = x0 + 2 <= x <= x1 - 2 and y0 + 2 <= y <= y1 - 2
                if on_edge:
                    px[x, y] = PAL["wood_dark"]
                elif not inner:  # bevel: light on top-left, dark bottom-right
                    lit = (x == x0 + 1 or y == y0 + 1)
                    px[x, y] = PAL["wood_hl"] if lit else shade(PAL["wood_dark"], 0.85)
    frame(2, 2, 29, 14)   # upper panel
    frame(2, 17, 29, 29)  # lower panel
    # inner field grain
    for (fx0, fy0, fx1, fy1) in [(4, 4, 27, 12), (4, 19, 27, 27)]:
        for x in range(fx0, fx1 + 1):
            for y in range(fy0, fy1 + 1):
                base = PAL["wood_mid"] if (y % 4) else PAL["wood_light"]
                noisy(px, x, y, base, rng, 5)
    return img

# --- Wrought-iron grate over darkness ---------------------------------------
def iron_grate(seed=31):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["void"])
    px = img.load()
    # faint depth behind the bars
    for x in range(S):
        for y in range(S):
            if rng.random() < 0.04:
                px[x, y] = (14, 14, 18)
    # vertical bars every 6px
    for bx in range(2, S, 6):
        for y in range(S):
            px[bx, y] = PAL["iron_hl"] if y % 7 == 3 else PAL["iron"]
            if bx + 1 < S:
                px[bx + 1, y] = shade(PAL["iron"], 0.7)
    # horizontal straps with rivets
    for by in (5, 26):
        for x in range(S):
            px[x, by] = PAL["iron"]
            px[x, by + 1] = shade(PAL["iron"], 0.7)
        for rx in range(4, S, 6):
            px[rx, by] = PAL["iron_hl"]  # rivet catch-light
    return img

# --- Victorian damask wallpaper ---------------------------------------------
def wallpaper(seed=41):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["paper_base"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            base = PAL["paper_base"] if (x + y) % 2 else PAL["paper_deep"]
            noisy(px, x, y, base, rng, 3)
    # damask motif on a 16x16 half-drop repeat
    motif = [
        "....#....",
        "...###...",
        "..#.#.#..",
        ".#..#..#.",
        "....#....",
        ".#.###.#.",
        "..#####..",
        "...###...",
        "....#....",
    ]
    def stamp(cx, cy, dim):
        col = shade(PAL["paper_motif"], 0.75) if dim else PAL["paper_motif"]
        for my, row in enumerate(motif):
            for mx, ch in enumerate(row):
                if ch == '#':
                    x = (cx + mx - len(row) // 2) % S
                    y = (cy + my - len(motif) // 2) % S
                    px[x, y] = col
    stamp(8, 8, False)
    stamp(24, 24, False)
    stamp(24, 8, True)   # half-drop secondary, dimmer
    stamp(8, 24, True)
    return img

# --- Output -----------------------------------------------------------------
import os
out = os.environ.get("OUT_DIR", ".")
os.makedirs(out, exist_ok=True)

tiles = {
    "wall_stone": stone_wall(),
    "floor_flagstone": stone_floor(),
    "wall_gaslamp": gaslamp_wall(),
    "wall_wood_panel": wood_panel(),
    "wall_iron_grate": iron_grate(),
    "wall_wallpaper": wallpaper(),
}
for name, img in tiles.items():
    img.save(f"{out}/{name}.png")

# preview sheet: each tile 3x3 tiled, upscaled 6x, side by side
tile_grid = 3
scale = 6
gap = 8
w = len(tiles) * (S * tile_grid * scale + gap) - gap
h = S * tile_grid * scale
sheet = Image.new("RGB", (w, h), (12, 12, 14))
ox = 0
for name, img in tiles.items():
    tiled = Image.new("RGB", (S * tile_grid, S * tile_grid))
    for i in range(tile_grid):
        for j in range(tile_grid):
            tiled.paste(img, (i * S, j * S))
    big = tiled.resize((S * tile_grid * scale, S * tile_grid * scale), Image.NEAREST)
    sheet.paste(big, (ox, 0))
    ox += S * tile_grid * scale + gap
sheet.save(f"{out}/preview_sheet.png")
print("generated:", ", ".join(tiles.keys()), "+ preview_sheet")
