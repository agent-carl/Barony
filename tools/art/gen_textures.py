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
    "brick_dark":  (74, 42, 34),
    "brick_mid":   (92, 52, 40),
    "brick_light": (110, 64, 48),
    "bone":        (168, 158, 134),
    "bone_shadow": (118, 110, 92),
    "bone_dark":   (78, 72, 60),
    "book_red":    (94, 40, 38),
    "book_green":  (48, 68, 52),
    "book_blue":   (44, 54, 76),
    "book_brown":  (86, 62, 40),
    "marble_light":(148, 146, 150),
    "marble_dark": (34, 34, 40),
    "dirt_dark":   (40, 32, 26),
    "dirt_mid":    (54, 42, 32),
    "carpet_deep": (74, 26, 30),
    "carpet_mid":  (96, 34, 38),
    "carpet_gold": (140, 110, 60),
    "glass_blue":  (70, 100, 160),
    "glass_red":   (150, 60, 70),
    "glass_gold":  (210, 170, 90),
    "glass_violet":(110, 70, 140),
    "lead":        (30, 30, 34),
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

# --- Victorian brick (sewers, factory cellars) ------------------------------
def brick_wall(seed=53):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    bh = 4  # brick height
    bw = 8  # brick width
    for row in range(S // bh):
        offset = (bw // 2) if row % 2 else 0
        y0 = row * bh
        x = -offset
        while x < S:
            base = rng.choice([PAL["brick_dark"], PAL["brick_mid"], PAL["brick_mid"], PAL["brick_light"]])
            sooty = rng.random() < 0.22  # victorian soot stains
            for sx in range(max(0, x), min(S, x + bw)):
                for sy in range(y0, min(S, y0 + bh)):
                    if sx == x + bw - 1 or sy == y0 + bh - 1:
                        px[sx, sy] = PAL["mortar"]
                    else:
                        c = shade(base, 0.7) if sooty and sy > y0 + 1 else base
                        if sx == x and sy == y0:
                            c = shade(base, 1.2)
                        noisy(px, sx, sy, c, rng, 5)
            x += bw
    return img

# --- Ossuary wall: stacked skulls and femurs (catacombs) --------------------
def bone_wall(seed=61):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["void"])
    px = img.load()
    # background of packed femur ends (rows of small circles)
    for y in range(S):
        for x in range(S):
            noisy(px, x, y, PAL["bone_dark"], rng, 6)
    for row in range(4):
        for col in range(8):
            cx, cy = col * 4 + 2, row * 8 + 2
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if abs(dx) + abs(dy) <= 1:
                        noisy(px, (cx + dx) % S, (cy + dy) % S, PAL["bone_shadow"], rng, 6)
            px[cx, cy] = PAL["bone"]
    # a course of skulls every other row
    for col in range(4):
        for row_y in (8, 24):
            cx = col * 8 + 4 + (2 if row_y == 24 else 0)
            # cranium
            for dx in range(-2, 3):
                for dy in range(-2, 2):
                    if dx * dx + dy * dy <= 5:
                        noisy(px, (cx + dx) % S, (row_y + dy) % S, PAL["bone"], rng, 4)
            # eye sockets + nasal
            px[(cx - 1) % S, row_y] = PAL["void"]
            px[(cx + 1) % S, row_y] = PAL["void"]
            px[cx, (row_y + 1) % S] = PAL["bone_dark"]
            # jaw
            for dx in range(-1, 2):
                noisy(px, (cx + dx) % S, (row_y + 2) % S, PAL["bone_shadow"], rng, 4)
    return img

# --- Library bookshelf (mansion) ---------------------------------------------
def bookshelf(seed=71):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["wood_dark"])
    px = img.load()
    shelf_rows = [(2, 9), (12, 19), (22, 29)]
    for (y0, y1) in shelf_rows:
        # shelf board above/below
        for x in range(S):
            px[x, y0 - 1] = PAL["wood_hl"]
            px[x, y1 + 1] = PAL["wood_mid"]
        x = 1
        while x < S - 1:
            w = rng.randint(2, 4)
            book = rng.choice([PAL["book_red"], PAL["book_green"], PAL["book_blue"], PAL["book_brown"]])
            lean = rng.random() < 0.12
            top_gap = rng.randint(0, 2)
            for sx in range(x, min(S - 1, x + w)):
                for sy in range(y0 + top_gap, y1 + 1):
                    c = book
                    if sx == x:
                        c = shade(book, 1.25)  # spine highlight
                    if lean and sy == y0 + top_gap:
                        continue
                    noisy(px, sx, sy, c, rng, 5)
            # gilded title band
            if w >= 3 and rng.random() < 0.5:
                px[x + 1, y0 + top_gap + 2] = PAL["brass_hl"]
            x += w + (1 if rng.random() < 0.2 else 0)
    return img

# --- Stained glass window (chapel; the warm exception) -----------------------
def stained_glass(seed=83):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["lead"])
    px = img.load()
    panes = [PAL["glass_blue"], PAL["glass_red"], PAL["glass_gold"], PAL["glass_violet"]]
    # gothic lancet: pointed arch made of diamond panes
    cx = 16
    for y in range(2, 30):
        half = 10 if y > 10 else max(1, (y - 1))
        for x in range(cx - half, cx + half):
            # lead cames on a diamond lattice
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                px[x % S, y] = PAL["lead"]
            else:
                pane = panes[((x + y) // 6 + (x - y) // 6) % len(panes)]
                glow = 1.25 if abs(x - cx) < 3 and 12 < y < 20 else 1.0
                noisy(px, x % S, y, shade(pane, glow), rng, 6)
    # central golden figure glow
    for y in range(13, 19):
        px[cx, y] = PAL["glass_gold"]
    # stone frame
    for y in range(S):
        for x in range(S):
            if x < 3 or x > 28 or y < 2 or y > 29:
                noisy(px, x, y, PAL["stone_dark"], rng, 5)
    return img

# --- Mansion plank floor ------------------------------------------------------
def floor_planks(seed=91):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["wood_dark"])
    px = img.load()
    ph = 5
    for row in range(S // ph + 1):
        y0 = row * ph
        seam = rng.randint(4, 27)  # butt joint position per row
        base = rng.choice([PAL["wood_mid"], PAL["wood_light"], PAL["wood_mid"]])
        for x in range(S):
            for y in range(y0, min(S, y0 + ph)):
                if y == y0:
                    px[x, y] = PAL["wood_dark"]  # plank gap
                elif x == seam:
                    px[x, y] = PAL["wood_dark"]
                else:
                    c = base
                    if (x * 7 + y * 3 + row) % 13 == 0:
                        c = shade(base, 0.85)  # grain streaks
                    noisy(px, x, y, c, rng, 4)
    return img

# --- Checkered marble (mansion foyer) ----------------------------------------
def floor_marble(seed=97):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["marble_dark"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            check = ((x // 8) + (y // 8)) % 2 == 0
            base = PAL["marble_light"] if check else PAL["marble_dark"]
            c = base
            # veining
            if (x * 3 + y * 5) % 17 == 0:
                c = shade(base, 0.8 if check else 1.6)
            if x % 8 == 0 or y % 8 == 0:
                c = shade(base, 0.7)
            noisy(px, x, y, c, rng, 3)
    return img

# --- Crypt earth floor ---------------------------------------------------------
def floor_dirt(seed=101):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["dirt_dark"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            c = PAL["dirt_mid"] if rng.random() < 0.4 else PAL["dirt_dark"]
            noisy(px, x, y, c, rng, 7)
    # scattered pebbles and a stray bone fleck
    for _ in range(14):
        x, y = rng.randint(0, S - 1), rng.randint(0, S - 1)
        px[x, y] = shade(PAL["stone_mid"], 0.9)
    for _ in range(2):
        x, y = rng.randint(2, S - 3), rng.randint(2, S - 3)
        px[x, y] = PAL["bone_shadow"]
        px[x + 1, y] = PAL["bone_shadow"]
    return img

# --- Mansion carpet runner ------------------------------------------------------
def floor_carpet(seed=107):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["carpet_deep"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            base = PAL["carpet_mid"] if (x + y) % 2 else PAL["carpet_deep"]
            noisy(px, x, y, base, rng, 4)
    # gold border and corner knots
    for i in range(S):
        for edge in (1, 30):
            px[i, edge] = PAL["carpet_gold"] if i % 3 else shade(PAL["carpet_gold"], 0.7)
            px[edge, i] = PAL["carpet_gold"] if i % 3 else shade(PAL["carpet_gold"], 0.7)
    # central diamond medallion
    cx = cy = 16
    for d in range(6):
        for t in range(-d, d + 1):
            for (x, y) in ((cx + t, cy + (d - abs(t))), (cx + t, cy - (d - abs(t)))):
                if d in (3, 5):
                    px[x % S, y % S] = PAL["carpet_gold"] if (x + y) % 2 else PAL["carpet_mid"]
    return img

# --- Output -----------------------------------------------------------------
import os
out = os.environ.get("OUT_DIR", ".")
os.makedirs(out, exist_ok=True)

tiles = {
    "wall_stone": stone_wall(),
    "wall_gaslamp": gaslamp_wall(),
    "wall_brick": brick_wall(),
    "wall_bone": bone_wall(),
    "wall_wood_panel": wood_panel(),
    "wall_wallpaper": wallpaper(),
    "wall_bookshelf": bookshelf(),
    "wall_stained_glass": stained_glass(),
    "wall_iron_grate": iron_grate(),
    "floor_flagstone": stone_floor(),
    "floor_planks": floor_planks(),
    "floor_marble": floor_marble(),
    "floor_dirt": floor_dirt(),
    "floor_carpet": floor_carpet(),
}
for name, img in tiles.items():
    img.save(f"{out}/{name}.png")

# preview sheet: each tile 3x3 tiled, upscaled, arranged in a grid
tile_grid = 3
scale = 5
gap = 10
cols = 5
cell = S * tile_grid * scale
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (cell + gap) - gap, rows * (cell + gap) - gap), (12, 12, 14))
for idx, (name, img) in enumerate(tiles.items()):
    tiled = Image.new("RGB", (S * tile_grid, S * tile_grid))
    for i in range(tile_grid):
        for j in range(tile_grid):
            tiled.paste(img, (i * S, j * S))
    big = tiled.resize((cell, cell), Image.NEAREST)
    sheet.paste(big, ((idx % cols) * (cell + gap), (idx // cols) * (cell + gap)))
sheet.save(f"{out}/preview_sheet.png")
print("generated:", ", ".join(tiles.keys()), "+ preview_sheet")
