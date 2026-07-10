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
    "water_deep":  (18, 26, 34),
    "water_mid":   (28, 40, 50),
    "water_hl":    (52, 70, 82),
    "cobble_dark": (48, 50, 54),
    "cobble_mid":  (62, 65, 70),
    "canvas":      (52, 46, 40),
    "skin_pale":   (150, 130, 110),
    "frame_gold":  (120, 94, 46),
    "ember":       (120, 40, 24),
    "mosaic_gold": (150, 122, 62),
    "mosaic_blue": (52, 62, 92),
    "mosaic_ivory":(140, 134, 116),
    "terracotta":  (122, 68, 48),
    "cream":       (176, 162, 134),
    "ivy":         (44, 66, 44),
    "ivy_light":   (62, 88, 56),
    "wax":         (188, 176, 148),
    "plaque":      (96, 92, 84),
    "velvet_deep": (52, 20, 26),
    "velvet_mid":  (74, 28, 36),
    "tile_white":  (152, 154, 148),
    "tile_grime":  (108, 108, 96),
    "padding":     (128, 118, 100),
    "padding_dark":(96, 88, 74),
    "chalk":       (196, 196, 188),
    "blood":       (56, 18, 16),
    "blood_dark":  (38, 12, 12),
    "mirror_glass":(64, 74, 84),
    "mirror_hl":   (108, 122, 134),
    "potion_red":  (150, 40, 44),
    "potion_green":(60, 110, 60),
    "organ_pipe":  (150, 140, 120),
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

# --- Variations of the workhorse surfaces ------------------------------------
def stone_wall_cracked(seed=131):
    img = stone_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # a jagged crack running down the whole tile
    cx = rng.randint(8, 24)
    for y in range(S):
        px[cx % S, y] = PAL["mortar"]
        if rng.random() < 0.5:
            px[(cx + 1) % S, y] = shade(PAL["stone_dark"], 0.7)
        cx += rng.choice([-1, 0, 0, 1])
    return img

def stone_wall_mossy(seed=137):
    img = stone_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # damp lower half, moss creeping up in patches
    for x in range(S):
        h = rng.randint(6, 16)
        for y in range(S - h, S):
            r, g, b = px[x, y]
            f = (y - (S - h)) / max(1, h)
            if rng.random() < 0.55 + 0.4 * f:
                mg = PAL["moss"]
                px[x, y] = (int(r * (1 - f * 0.7) + mg[0] * f * 0.7),
                            int(g * (1 - f * 0.7) + mg[1] * f * 0.7),
                            int(b * (1 - f * 0.7) + mg[2] * f * 0.7))
    return img

# --- Mansion fireplace (warm accent) -----------------------------------------
def fireplace(seed=139):
    rng = random.Random(seed)
    img = stone_wall(seed)
    px = img.load()
    # stone mantel
    for x in range(4, 28):
        px[x, 8] = PAL["stone_hl"]
        px[x, 9] = PAL["stone_light"]
    # firebox opening
    for x in range(8, 24):
        for y in range(10, 26):
            arch = abs(x - 16) > 6 and y < 13
            if not arch:
                px[x, y] = PAL["void"]
    # burning logs and flame
    for x in range(10, 22):
        for y in range(20, 26):
            noisy(px, x, y, PAL["ember"] if y > 22 else PAL["flame_deep"], rng, 10)
    for x in range(12, 20):
        for y in range(15, 21):
            d = abs(x - 16) + abs(y - 19)
            if d < 5:
                noisy(px, x, y, PAL["flame"] if d > 2 else PAL["flame_core"], rng, 8)
    # glow spill on surrounding stone
    for x in range(S):
        for y in range(S):
            d2 = (x - 16) ** 2 + (y - 20) ** 2
            if 36 < d2 < 150:
                r, g, b = px[x, y]
                f = (150 - d2) / 150.0 * 0.4
                px[x, y] = (min(255, int(r + 90 * f)), min(255, int(g + 50 * f)), b)
    # hearth stones
    for x in range(6, 26):
        px[x, 26] = PAL["stone_dark"]
        px[x, 27] = PAL["stone_mid"]
    return img

# --- Haunted portrait (mansion) ------------------------------------------------
def portrait_wall(seed=149):
    img = wood_panel(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # gilded frame
    for x in range(9, 23):
        for y in range(5, 25):
            on_frame = x in (9, 10, 21, 22) or y in (5, 6, 23, 24)
            if on_frame:
                px[x, y] = PAL["frame_gold"] if (x + y) % 2 else PAL["brass_hl"]
    # dark canvas
    for x in range(11, 21):
        for y in range(7, 23):
            noisy(px, x, y, PAL["canvas"], rng, 5)
    # pale figure: head and shoulders, eyes that follow
    cx = 16
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                noisy(px, cx + dx, 11 + dy, PAL["skin_pale"], rng, 5)
    px[cx - 1, 11] = PAL["void"]
    px[cx + 1, 11] = PAL["void"]
    for dx in range(-3, 4):
        for dy in range(0, 5):
            if abs(dx) + dy < 6:
                noisy(px, cx + dx, 16 + dy, shade(PAL["canvas"], 0.6), rng, 4)
    return img

# --- Studded wooden door --------------------------------------------------------
def door_wood(seed=151):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["wood_dark"])
    px = img.load()
    # vertical planks
    for x in range(S):
        for y in range(S):
            plank = (x // 5) % 2
            base = PAL["wood_mid"] if plank else PAL["wood_light"]
            if x % 5 == 0:
                base = PAL["wood_dark"]
            noisy(px, x, y, base, rng, 5)
    # iron banding with studs
    for by in (6, 25):
        for x in range(S):
            px[x, by] = PAL["iron"]
            px[x, by + 1] = PAL["iron_hl"] if x % 4 == 2 else shade(PAL["iron"], 0.8)
    # ring handle
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            d2 = dx * dx + dy * dy
            if 2 <= d2 <= 5:
                px[24 + dx, 16 + dy] = PAL["iron_hl"]
    px[24, 14] = PAL["iron"]
    # stone jamb
    for y in range(S):
        for x in (0, 1, 30, 31):
            noisy(px, x, y, PAL["stone_dark"], rng, 5)
    return img

# --- Chapel carved arch ----------------------------------------------------------
def chapel_arch(seed=157):
    img = stone_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # blind lancet arch carved in relief
    cx = 16
    for y in range(6, 28):
        half = 7 if y > 13 else max(1, y - 6)
        for x in (cx - half, cx + half):
            px[x % S, y] = PAL["stone_hl"]
            px[(x + (1 if x < cx else -1)) % S, y] = shade(PAL["stone_dark"], 0.75)
        if y > 13:
            for x in range(cx - half + 2, cx + half - 1):
                noisy(px, x, y, shade(PAL["stone_dark"], 0.85), rng, 4)
    # carved cross inside
    for y in range(16, 24):
        px[cx, y] = PAL["stone_hl"]
    for x in range(cx - 2, cx + 3):
        px[x, 18] = PAL["stone_hl"]
    return img

# --- Cobblestone (courtyards, streets) --------------------------------------------
def floor_cobble(seed=163):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    # rounded stones on a jittered grid
    for gy in range(0, S, 6):
        for gx in range(0, S, 6):
            cx = gx + 3 + rng.randint(-1, 1)
            cy = gy + 3 + rng.randint(-1, 1)
            base = rng.choice([PAL["cobble_dark"], PAL["cobble_mid"], PAL["stone_mid"]])
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx * dx + dy * dy <= 7:
                        c = shade(base, 1.2) if (dx < 0 and dy < 0) else base
                        noisy(px, (cx + dx) % S, (cy + dy) % S, c, rng, 5)
    return img

# --- Chapel mosaic ------------------------------------------------------------------
def floor_mosaic(seed=167):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            if x % 4 == 3 or y % 4 == 3:
                px[x, y] = PAL["mortar"]
                continue
            ring = max(abs(x - 16), abs(y - 16)) // 4
            base = [PAL["mosaic_ivory"], PAL["mosaic_blue"], PAL["mosaic_gold"], PAL["mosaic_blue"]][ring % 4]
            noisy(px, x, y, base, rng, 6)
    return img

# --- Flooded sewer floor ---------------------------------------------------------------
def floor_water(seed=173):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["water_deep"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            base = PAL["water_mid"] if (y * 3 + x) % 9 < 2 else PAL["water_deep"]
            noisy(px, x, y, base, rng, 4)
    # ripple highlights
    for _ in range(6):
        rx, ry, rl = rng.randint(2, 28), rng.randint(2, 29), rng.randint(3, 7)
        for i in range(rl):
            px[(rx + i) % S, ry] = PAL["water_hl"]
    # drowned flagstone peeking through
    for x in range(20, 27):
        for y in range(22, 28):
            noisy(px, x, y, shade(PAL["floor_mid"], 0.6), rng, 4)
    return img

# --- Mansion ceiling beams ----------------------------------------------------------------
def ceiling_beams(seed=179):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), (26, 24, 24))
    px = img.load()
    # plaster field
    for x in range(S):
        for y in range(S):
            noisy(px, x, y, (58, 54, 50), rng, 4)
    # dark oak beams
    for bx in (2, 16, 30):
        for y in range(S):
            for dx in range(-2, 3):
                x = (bx + dx) % S
                c = PAL["wood_dark"] if abs(dx) == 2 else PAL["wood_mid"]
                if dx == -1:
                    c = PAL["wood_light"]
                noisy(px, x, y, c, rng, 4)
    # cross beam
    for x in range(S):
        for dy in range(-2, 3):
            c = PAL["wood_dark"] if abs(dy) == 2 else PAL["wood_mid"]
            noisy(px, x, (16 + dy) % S, c, rng, 4)
    return img

# --- Victorian encaustic tile (very Victorian!) -------------------------------
def floor_encaustic(seed=181):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            if x % 16 == 15 or y % 16 == 15:
                px[x, y] = PAL["mortar"]
                continue
            lx, ly = x % 16, y % 16
            # quarter-diamond four-color pattern
            d = abs(lx - 7.5) + abs(ly - 7.5)
            if d < 4:
                base = PAL["mosaic_blue"]
            elif d < 7:
                base = PAL["cream"]
            elif d < 10:
                base = PAL["terracotta"]
            else:
                base = PAL["cream"] if (lx < 3 or lx > 12) == (ly < 3 or ly > 12) else PAL["marble_dark"]
            noisy(px, x, y, base, rng, 5)
    return img

# --- Sewer wall with cast-iron pipe -------------------------------------------
def wall_pipe(seed=191):
    img = brick_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # horizontal pipe with flanges
    for x in range(S):
        for dy in range(-2, 3):
            y = 20 + dy
            c = PAL["iron"] if abs(dy) == 2 else PAL["iron_hl"] if dy == -1 else shade(PAL["iron"], 0.9)
            noisy(px, x, y, c, rng, 4)
    for fx in (4, 27):
        for dy in range(-3, 4):
            px[fx, 20 + dy] = PAL["iron_hl"] if dy % 2 else PAL["iron"]
    # drip stain under a joint
    for y in range(23, 30):
        noisy(px, 15, y, PAL["moss"], rng, 6)
        if rng.random() < 0.5:
            noisy(px, 16, y, PAL["moss"], rng, 6)
    return img

# --- Chapel votive candles shelf ------------------------------------------------
def wall_candles(seed=193):
    img = stone_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # stone shelf
    for x in range(3, 29):
        px[x, 20] = PAL["stone_hl"]
        px[x, 21] = PAL["stone_light"]
    # candles of varying heights
    x = 5
    while x < 27:
        h = rng.randint(3, 7)
        for y in range(20 - h, 20):
            px[x, y] = PAL["wax"]
            if x + 1 < 27:
                px[x + 1, y] = shade(PAL["wax"], 0.8)
        # flame
        px[x, 20 - h - 1] = PAL["flame_core"]
        px[x, 20 - h - 2] = PAL["flame"]
        # glow on stone behind
        for dx in range(-2, 3):
            for dy in range(-3, 1):
                gx, gy = x + dx, 20 - h - 2 + dy
                if 0 <= gx < S and 0 <= gy < S:
                    r, g, b = px[gx, gy]
                    px[gx, gy] = (min(255, r + 26), min(255, g + 18), b)
        x += rng.randint(3, 5)
    return img

# --- Ivy-grown stone (courtyards) -------------------------------------------------
def wall_ivy(seed=197):
    img = stone_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # several vines climbing with leaves
    for vine in range(4):
        vx = rng.randint(2, 29)
        for y in range(S - 1, rng.randint(2, 12), -1):
            px[vx % S, y] = PAL["ivy"]
            if rng.random() < 0.45:
                lx = vx + rng.choice([-1, 1])
                px[lx % S, y] = PAL["ivy_light"] if rng.random() < 0.5 else PAL["ivy"]
                if rng.random() < 0.3:
                    px[(lx + rng.choice([-1, 1])) % S, y] = PAL["ivy_light"]
            vx += rng.choice([-1, 0, 0, 1])
    return img

# --- Crypt memorial plaques ---------------------------------------------------------
def wall_plaques(seed=199):
    img = stone_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for (x0, y0) in ((3, 4), (18, 4), (3, 18), (18, 18)):
        w, h = 11, 9
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + h):
                edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
                if edge:
                    px[x, y] = shade(PAL["plaque"], 1.25) if (x == x0 or y == y0) else shade(PAL["plaque"], 0.6)
                else:
                    noisy(px, x, y, PAL["plaque"], rng, 4)
        # engraved lines of a name
        for line in range(2):
            ly = y0 + 3 + line * 2
            for x in range(x0 + 2, x0 + w - 2):
                if rng.random() < 0.7:
                    px[x, ly] = shade(PAL["plaque"], 0.55)
    return img

# --- Bone-littered floor (catacombs) ---------------------------------------------------
def floor_bones(seed=211):
    img = floor_dirt(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # long bones
    for _ in range(5):
        x, y = rng.randint(2, 24), rng.randint(2, 29)
        l = rng.randint(4, 7)
        horiz = rng.random() < 0.5
        for i in range(l):
            bx, by = (x + i, y) if horiz else (x, y + i)
            px[bx % S, by % S] = PAL["bone"] if 0 < i < l - 1 else PAL["bone_shadow"]
    # a skull
    cx, cy = rng.randint(6, 26), rng.randint(6, 26)
    for dx in range(-2, 3):
        for dy in range(-2, 2):
            if dx * dx + dy * dy <= 4:
                noisy(px, (cx + dx) % S, (cy + dy) % S, PAL["bone"], rng, 5)
    px[(cx - 1) % S, cy] = PAL["void"]
    px[(cx + 1) % S, cy] = PAL["void"]
    return img

# --- Mossy flagstone floor ---------------------------------------------------------------
def floor_moss(seed=223):
    img = stone_floor(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for _ in range(5):
        cx, cy = rng.randint(3, 28), rng.randint(3, 28)
        rr = rng.randint(2, 5)
        for dx in range(-rr, rr + 1):
            for dy in range(-rr, rr + 1):
                if dx * dx + dy * dy <= rr * rr and rng.random() < 0.75:
                    c = PAL["ivy_light"] if rng.random() < 0.3 else PAL["moss"]
                    noisy(px, (cx + dx) % S, (cy + dy) % S, c, rng, 6)
    return img

# --- Stone vault ceiling ---------------------------------------------------------------------
def ceiling_vault(seed=227):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    # radial wedge stones around a center boss
    cx = cy = 16
    import math
    for x in range(S):
        for y in range(S):
            ang = math.atan2(y - cy, x - cx)
            d = math.hypot(x - cx, y - cy)
            wedge = int((ang + math.pi) / (math.pi / 6))
            ring = int(d / 6)
            if int(d) % 6 == 5 or (wedge + ring) % 2 == 0 and int(ang * 12) % 3 == 0:
                base = PAL["mortar"]
            else:
                base = PAL["stone_mid"] if (wedge + ring) % 2 else PAL["stone_dark"]
            noisy(px, x, y, base, rng, 5)
    # central boss
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                px[cx + dx, cy + dy] = PAL["stone_hl"]
    return img

# --- Plank ceiling ------------------------------------------------------------------------------
def ceiling_planks(seed=229):
    img = floor_planks(seed)
    px = img.load()
    # darken overall - ceilings live in shadow
    for x in range(S):
        for y in range(S):
            r, g, b = px[x, y]
            px[x, y] = (int(r * 0.72), int(g * 0.72), int(b * 0.72))
    return img

# --- Velvet drapes (mansion) ----------------------------------------------------
def wall_curtain(seed=269):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["velvet_deep"])
    px = img.load()
    # vertical folds via sine-ish banding
    for x in range(S):
        fold = (x * 3) % 7
        base = PAL["velvet_mid"] if fold in (2, 3) else PAL["velvet_deep"]
        hl = fold == 3
        for y in range(S):
            c = shade(base, 1.18) if hl and y % 5 else base
            noisy(px, x, y, c, rng, 4)
    # brass rod and rings
    for x in range(S):
        px[x, 1] = PAL["brass"] if x % 5 else PAL["brass_hl"]
    # gold tieback cord
    for y in range(18, 23):
        px[26, y] = PAL["carpet_gold"]
        px[27, y] = shade(PAL["carpet_gold"], 0.75)
    return img

# --- Chapel organ pipes ------------------------------------------------------------
def wall_organ(seed=271):
    rng = random.Random(seed)
    img = wood_panel(seed)
    px = img.load()
    # pipes of graded heights over a wooden case
    heights = [10, 14, 18, 22, 18, 14, 10]
    xw = 4
    for i, h in enumerate(heights):
        x0 = 2 + i * xw
        for x in range(x0, x0 + 3):
            for y in range(26 - h, 26):
                c = PAL["organ_pipe"]
                if x == x0:
                    c = shade(c, 1.2)
                elif x == x0 + 2:
                    c = shade(c, 0.7)
                noisy(px, x, y, c, rng, 3)
            # mouth of the pipe
            px[x, 26 - h + 2] = shade(PAL["organ_pipe"], 0.5)
    # case rail
    for x in range(S):
        px[x, 26] = PAL["wood_dark"]
        px[x, 27] = PAL["wood_hl"]
    return img

# --- Apothecary shelf (occult lab) ---------------------------------------------------
def wall_apothecary(seed=277):
    rng = random.Random(seed)
    img = wood_panel(seed)
    px = img.load()
    for (y0, y1) in ((4, 12), (16, 24)):
        for x in range(S):
            px[x, y0 - 1] = PAL["wood_hl"]
            px[x, y1 + 1] = PAL["wood_mid"]
        x = 2
        while x < 29:
            w = rng.randint(2, 3)
            jar = rng.choice([PAL["potion_red"], PAL["potion_green"], PAL["glass_glow"],
                              PAL["mirror_glass"], PAL["book_brown"]])
            h = rng.randint(4, y1 - y0 - 1)
            for sx in range(x, x + w):
                for sy in range(y1 - h, y1 + 1):
                    c = jar if sy > y1 - h + 1 else shade(jar, 1.25)
                    noisy(px, sx, sy, c, rng, 6)
            # cork/lid
            px[x + w // 2, y1 - h] = PAL["wood_dark"]
            # something floating inside the pale jars
            if jar == PAL["mirror_glass"] and h > 5:
                px[x + w // 2, y1 - 2] = PAL["skin_pale"]
            x += w + rng.randint(1, 2)
    return img

# --- Asylum padded cell -----------------------------------------------------------------
def wall_padded(seed=281):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["padding"])
    px = img.load()
    # diamond tufting
    for x in range(S):
        for y in range(S):
            d = (x + y) % 12
            d2 = (x - y) % 12
            if d == 0 or d2 == 0:
                c = PAL["padding_dark"]
            else:
                # bulge shading between seams
                dd = min(d, 12 - d, d2, 12 - d2)
                c = shade(PAL["padding"], 0.95 + dd * 0.035)
            noisy(px, x, y, c, rng, 4)
    # buttons at intersections
    for x in range(0, S, 12):
        for y in range(0, S, 12):
            px[(x) % S, (y) % S] = shade(PAL["padding_dark"], 0.7)
    # grime along the bottom
    for x in range(S):
        for y in range(28, S):
            noisy(px, x, y, PAL["tile_grime"], rng, 6)
    return img

# --- Asylum / morgue glazed tiles ----------------------------------------------------------
def wall_asylum_tiles(seed=283):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            if x % 8 == 7 or y % 8 == 7:
                px[x, y] = PAL["tile_grime"]
                continue
            base = PAL["tile_white"]
            # aged grime creeping from joints and the floor
            if y > 24 or rng.random() < 0.08:
                base = PAL["tile_grime"]
            if x % 8 == 0 and y % 8 == 0:
                base = shade(PAL["tile_white"], 1.15)  # glaze glint
            noisy(px, x, y, base, rng, 5)
    return img

# --- Ritual chalk circle on flagstone -------------------------------------------------------
def floor_ritual(seed=293):
    img = stone_floor(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    import math
    cx = cy = 16
    # double circle
    for r in (11, 13):
        steps = int(2 * math.pi * r * 2)
        for i in range(steps):
            a = i / steps * 2 * math.pi
            x = int(cx + r * math.cos(a))
            y = int(cy + r * math.sin(a))
            if 0 <= x < S and 0 <= y < S and rng.random() < 0.85:
                px[x, y] = PAL["chalk"]
    # inner pentagram-ish star
    pts = [(cx + int(11 * math.cos(a)), cy + int(11 * math.sin(a)))
           for a in [(-90 + i * 144) * math.pi / 180 for i in range(5)]]
    for i in range(5):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % 5]
        steps = max(abs(x1 - x0), abs(y1 - y0)) + 1
        for s in range(steps):
            x = int(x0 + (x1 - x0) * s / steps)
            y = int(y0 + (y1 - y0) * s / steps)
            if 0 <= x < S and 0 <= y < S and rng.random() < 0.9:
                px[x, y] = PAL["chalk"]
    # rune ticks around
    for a in range(0, 360, 30):
        x = int(cx + 15 * math.cos(a * math.pi / 180))
        y = int(cy + 15 * math.sin(a * math.pi / 180))
        if 0 <= x < S and 0 <= y < S:
            px[x, y] = PAL["chalk"]
    return img

# --- Iron grate floor over darkness -----------------------------------------------------------
def floor_grate(seed=307):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["void"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            bar = x % 6 in (0, 1) or y % 6 in (0, 1)
            if bar:
                c = PAL["iron_hl"] if (x % 6 == 0 and y % 3 == 0) else PAL["iron"]
                noisy(px, x, y, c, rng, 4)
            elif rng.random() < 0.03:
                px[x, y] = (14, 14, 18)  # faint depth below
    return img

# --- Bloodstained flagstone ----------------------------------------------------------------------
def floor_blood(seed=311):
    img = stone_floor(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # a dragged smear with droplets
    y = rng.randint(8, 20)
    for x in range(3, 29):
        w = rng.randint(1, 3)
        for dy in range(w):
            r, g, b = px[x, (y + dy) % S]
            c = PAL["blood"] if rng.random() < 0.7 else PAL["blood_dark"]
            px[x, (y + dy) % S] = (min(255, (r + c[0] * 3) // 4), (g + c[1] * 3) // 4, (b + c[2] * 3) // 4)
        y += rng.choice([-1, 0, 0, 1])
    for _ in range(8):
        dx, dy = rng.randint(2, 29), rng.randint(2, 29)
        px[dx, dy] = PAL["blood_dark"]
    return img

# --- Haunted mirror (mansion) ------------------------------------------------------------------------
def wall_mirror(seed=313):
    img = wood_panel(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # ornate oval frame
    import math
    cx, cy, ax, ay = 16, 15, 8, 11
    for x in range(S):
        for y in range(S):
            e = ((x - cx) / ax) ** 2 + ((y - cy) / ay) ** 2
            if 0.75 <= e <= 1.0:
                px[x, y] = PAL["frame_gold"] if (x + y) % 2 else PAL["brass_hl"]
            elif e < 0.75:
                base = PAL["mirror_glass"]
                # diagonal sheen
                if (x - y) % 9 in (0, 1):
                    base = PAL["mirror_hl"]
                noisy(px, x, y, base, rng, 4)
    # a pale smudge that shouldn't be there
    for dx in range(-1, 2):
        for dy in range(-2, 2):
            if abs(dx) + abs(dy) < 3:
                noisy(px, 13 + dx, 13 + dy, PAL["skin_pale"], rng, 12)
    return img

# === Biome depth variations ==================================================

# --- Dungeon: an unlit gas sconce (refillable - idea #3) ----------------------
def gaslamp_unlit(seed=7):
    img = stone_wall(seed)  # same masonry as the lit one
    px = img.load()
    cx = 16
    for y in range(18, 24):
        for x in range(cx - 1, cx + 2):
            px[x, y] = PAL["iron"] if x != cx else PAL["iron_hl"]
    for y in range(14, 18):
        px[cx, y] = shade(PAL["brass"], 0.6)  # tarnished stem
        px[cx - 1, y] = shade(PAL["brass"], 0.5)
    for y in range(8, 14):
        for x in range(cx - 3, cx + 4):
            dx = abs(x - cx)
            if dx == 3 or y == 8 or y == 13:
                px[x, y] = shade(PAL["brass"], 0.55) if (x + y) % 2 else shade(PAL["brass"], 0.7)
            else:
                px[x, y] = shade(PAL["mirror_glass"], 0.5)
    px[cx, 7] = shade(PAL["brass"], 0.6)
    for y in range(3, 7):
        px[cx, y] = shade(PAL["mortar"], 0.7)  # soot streak
    return img

# --- Dungeon: carved frieze course --------------------------------------------
def wall_stone_frieze(seed=379):
    img = stone_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for x in range(S):
        px[x, 12] = PAL["stone_hl"]
        px[x, 19] = PAL["stone_hl"]
    for x in range(0, S, 4):
        px[(x + 1) % S, 14] = PAL["stone_hl"]
        px[(x + 2) % S, 15] = shade(PAL["stone_dark"], 0.7)
        px[(x + 1) % S, 16] = PAL["stone_hl"]
        px[x % S, 15] = PAL["stone_hl"]
        for y in range(13, 19):
            if rng.random() < 0.12:
                px[(x + 3) % S, y] = shade(PAL["stone_dark"], 0.85)
    return img

# --- Dungeon: rubble-strewn floor -----------------------------------------------
def floor_rubble(seed=383):
    img = stone_floor(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for _ in range(10):
        cx, cy = rng.randint(2, 29), rng.randint(2, 29)
        rr = rng.randint(1, 2)
        base = rng.choice([PAL["stone_mid"], PAL["stone_light"], PAL["stone_dark"]])
        for dx in range(-rr, rr + 1):
            for dy in range(-rr, rr + 1):
                if abs(dx) + abs(dy) <= rr:
                    c = shade(base, 1.15) if dy < 0 else shade(base, 0.8)
                    noisy(px, (cx + dx) % S, (cy + dy) % S, c, rng, 5)
    return img

# --- Catacombs: long-bone columns variant ----------------------------------------
def bone_wall_columns(seed=389):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["void"])
    px = img.load()
    for y in range(S):
        for x in range(S):
            noisy(px, x, y, PAL["bone_dark"], rng, 6)
    for col in range(0, S, 8):
        for y in range(0, S, 5):
            for dy in range(1, 4):
                px[(col + 3) % S, (y + dy) % S] = PAL["bone"]
                px[(col + 4) % S, (y + dy) % S] = PAL["bone_shadow"]
            for bx in (2, 5):
                px[(col + bx) % S, y % S] = PAL["bone"]
                px[(col + bx) % S, (y + 4) % S] = PAL["bone_shadow"]
    cx, cy = 16, 16
    for dx in range(-2, 3):
        for dy in range(-2, 2):
            if dx * dx + dy * dy <= 4:
                noisy(px, cx + dx, cy + dy, PAL["bone"], rng, 4)
    px[cx - 1, cy] = PAL["void"]
    px[cx + 1, cy] = PAL["void"]
    return img

# --- Catacombs: coffin niche --------------------------------------------------------
def wall_coffin_niche(seed=397):
    img = stone_wall(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for x in range(7, 25):
        for y in range(6, 26):
            arch_top = 6 + (0 if 10 <= x <= 21 else 3)
            if y >= arch_top:
                px[x, y] = shade(PAL["mortar"], 0.8)
    for x in range(11, 21):
        for y in range(9, 25):
            taper = 0 if y < 14 else (y - 14) // 5
            if 11 + taper <= x <= 20 - taper:
                edge = x in (11 + taper, 20 - taper) or y in (9, 24)
                c = PAL["wood_dark"] if edge else PAL["wood_mid"]
                noisy(px, x, y, c, rng, 4)
    for y in range(12, 19):
        px[15, y] = PAL["wood_hl"]
        px[16, y] = PAL["wood_hl"]
    for x in range(13, 19):
        px[x, 14] = PAL["wood_hl"]
    return img

# --- Sewer: green scum water variant ---------------------------------------------------
def floor_water_scum(seed=401):
    img = floor_water(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for _ in range(7):
        cx, cy = rng.randint(2, 29), rng.randint(2, 29)
        rr = rng.randint(2, 4)
        for dx in range(-rr, rr + 1):
            for dy in range(-rr, rr + 1):
                if dx * dx + dy * dy <= rr * rr and rng.random() < 0.7:
                    noisy(px, (cx + dx) % S, (cy + dy) % S, PAL["ivy"], rng, 8)
    return img

# --- Mansion: bordeaux wallpaper variant --------------------------------------------------
def wallpaper_red(seed=409):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["velvet_deep"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            base = PAL["velvet_mid"] if (x + y) % 2 else PAL["velvet_deep"]
            noisy(px, x, y, base, rng, 3)
    for x in range(0, S, 8):
        for y in range(S):
            px[x, y] = shade(PAL["velvet_mid"], 1.2)
        for y in range(4, S, 8):
            px[(x + 4) % S, y] = PAL["carpet_gold"]
            px[(x + 4) % S, (y + 1) % S] = shade(PAL["carpet_gold"], 0.7)
    return img

# --- Mansion: torn wallpaper over brick ------------------------------------------------------
def wallpaper_torn(seed=419):
    paper = wallpaper(seed)
    brick = brick_wall(seed + 1)
    rng = random.Random(seed + 2)
    px = paper.load()
    bx = brick.load()
    edge = [rng.randint(8, 14)]
    for y in range(1, S):
        edge.append(min(26, max(6, edge[-1] + rng.choice([-2, -1, 0, 1, 2]))))
    for y in range(S):
        for x in range(edge[y], S):
            px[x, y] = bx[x, y]
        if 0 < edge[y] < S:
            px[edge[y] - 1, y] = shade(PAL["paper_base"], 1.5)
    return paper

# --- Mansion: boarded-up window -----------------------------------------------------------------
def wall_window_boarded(seed=421):
    img = wood_panel(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for x in range(8, 24):
        for y in range(5, 25):
            px[x, y] = PAL["void"] if rng.random() < 0.9 else (16, 16, 22)
    for y in (8, 15, 21):
        for x in range(9, 23):
            if rng.random() < 0.3:
                px[x, y] = shade(PAL["mirror_hl"], 0.6)
    for i, by in enumerate((7, 13, 19)):
        for x in range(6, 26):
            yy = by + (x - 6) // (7 + i)
            for t in range(3):
                if 0 <= yy + t < S:
                    c = PAL["wood_light"] if t == 0 else PAL["wood_mid"] if t == 1 else PAL["wood_dark"]
                    noisy(px, x, yy + t, c, rng, 5)
        px[7, by + 1] = PAL["iron_hl"]
        px[24, by + 2] = PAL["iron_hl"]
    return img

# --- Mansion: rotten planks with holes ------------------------------------------------------------
def floor_planks_rotten(seed=431):
    img = floor_planks(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for _ in range(4):
        cx, cy = rng.randint(4, 27), rng.randint(4, 27)
        rr = rng.randint(2, 4)
        for dx in range(-rr, rr + 1):
            for dy in range(-rr, rr + 1):
                d2 = dx * dx + dy * dy
                if d2 <= rr * rr:
                    if d2 <= (rr - 1) ** 2 and rr > 2:
                        px[(cx + dx) % S, (cy + dy) % S] = PAL["void"]
                    else:
                        r, g, b = px[(cx + dx) % S, (cy + dy) % S]
                        px[(cx + dx) % S, (cy + dy) % S] = (int(r * 0.5), int(g * 0.55), int(b * 0.5))
    return img

# --- Mansion: dark landscape painting ----------------------------------------------------------------
def wall_painting(seed=433):
    img = wood_panel(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for x in range(5, 27):
        for y in range(7, 23):
            on_frame = x in (5, 6, 25, 26) or y in (7, 8, 21, 22)
            if on_frame:
                px[x, y] = PAL["frame_gold"] if (x + y) % 2 else PAL["brass_hl"]
    for x in range(7, 25):
        for y in range(9, 21):
            horizon = 15 + (x % 5 == 0)
            c = (30, 34, 44) if y < horizon else (24, 28, 24)
            noisy(px, x, y, c, rng, 4)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if abs(dx) + abs(dy) <= 1:
                px[21 + dx, 11 + dy] = PAL["cream"]  # sickly moon
    for y in range(12, 20):
        px[11, y] = PAL["void"]  # dead tree
    px[10, 12] = PAL["void"]
    px[12, 13] = PAL["void"]
    px[9, 13] = PAL["void"]
    return img

# --- Mansion: blue carpet variant --------------------------------------------------------------------
def floor_carpet_blue(seed=439):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mosaic_blue"])
    px = img.load()
    deep = shade(PAL["mosaic_blue"], 0.75)
    for x in range(S):
        for y in range(S):
            base = PAL["mosaic_blue"] if (x + y) % 2 else deep
            noisy(px, x, y, base, rng, 4)
    for i in range(S):
        for edge in (1, 30):
            px[i, edge] = PAL["cream"] if i % 3 else shade(PAL["cream"], 0.7)
            px[edge, i] = PAL["cream"] if i % 3 else shade(PAL["cream"], 0.7)
    cx = cy = 16
    for d in range(6):
        for t in range(-d, d + 1):
            for (x, y) in ((cx + t, cy + (d - abs(t))), (cx + t, cy - (d - abs(t)))):
                if d in (3, 5):
                    px[x % S, y % S] = PAL["cream"] if (x + y) % 2 else deep
    return img

# --- Chapel: mourning stained glass (cool variant) ------------------------------------------------------
def stained_glass_blue(seed=443):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["lead"])
    px = img.load()
    panes = [PAL["glass_blue"], PAL["mosaic_blue"], PAL["glass_violet"], PAL["mirror_hl"]]
    cx = 16
    for y in range(2, 30):
        half = 10 if y > 10 else max(1, (y - 1))
        for x in range(cx - half, cx + half):
            if (x + y) % 5 == 0 or (x - y) % 5 == 0:
                px[x % S, y] = PAL["lead"]
            else:
                pane = panes[((x + y) // 5 + (x - y) // 5) % len(panes)]
                noisy(px, x % S, y, pane, rng, 6)
    for dy in range(2):
        px[cx, 24 + dy] = PAL["glass_gold"]  # a single candle-glint
    for y in range(S):
        for x in range(S):
            if x < 3 or x > 28 or y < 2 or y > 29:
                noisy(px, x, y, PAL["stone_dark"], rng, 5)
    return img

# --- Chapel: cross mosaic variant --------------------------------------------------------------------------
def floor_mosaic_cross(seed=449):
    rng = random.Random(seed)
    img = Image.new("RGB", (S, S), PAL["mortar"])
    px = img.load()
    for x in range(S):
        for y in range(S):
            if x % 4 == 3 or y % 4 == 3:
                px[x, y] = PAL["mortar"]
                continue
            in_cross = (12 <= x <= 19) or (12 <= y <= 19)
            base = PAL["mosaic_gold"] if in_cross else PAL["mosaic_ivory"]
            if (10 <= x <= 21) and (10 <= y <= 21) and not in_cross:
                base = PAL["mosaic_blue"]
            noisy(px, x, y, base, rng, 6)
    return img

# --- Asylum: blood-spattered glazed tiles ---------------------------------------------------------------------
def wall_asylum_blood(seed=457):
    img = wall_asylum_tiles(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for i in range(14):
        x = 6 + i
        y = 8 + (i * i) // 14
        if 0 <= x < S and 0 <= y < S:
            px[x, y] = PAL["blood"]
            if rng.random() < 0.5:
                px[x, y + 1] = PAL["blood_dark"]
    for _ in range(5):
        dx, dy = rng.randint(4, 24), rng.randint(6, 16)
        for run in range(rng.randint(2, 7)):
            px[dx, min(S - 1, dy + run)] = PAL["blood_dark"] if run else PAL["blood"]
    return img

# --- Asylum: torn padding ------------------------------------------------------------------------------------------
def wall_padded_torn(seed=461):
    img = wall_padded(seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for (gx, gy, gl) in ((8, 6, 9), (20, 14, 7), (13, 22, 6)):
        x, y = gx, gy
        for i in range(gl):
            px[x % S, y % S] = PAL["void"]
            if rng.random() < 0.6:
                px[(x + 1) % S, y % S] = shade(PAL["cream"], 0.9)  # stuffing
            x += rng.choice([0, 1])
            y += 1
    for sx in range(24, 29):
        for i in range(4):
            px[sx, (10 + i + (sx % 2)) % S] = PAL["padding_dark"]  # scratch marks
    return img


# --- Decor / item sprites (RGBA, transparent background) -------------------------------------------
def _sprite():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))

def spr(px, x, y, c):
    px[x, y] = (c[0], c[1], c[2], 255)

def sprite_lantern(seed=233):
    img = _sprite()
    px = img.load()
    cx = 16
    for x in range(cx - 2, cx + 3):
        spr(px, x, 6, PAL["brass"])
    spr(px, cx, 4, PAL["iron_hl"])
    spr(px, cx, 5, PAL["iron"])
    for y in range(7, 22):
        for x in range(cx - 5, cx + 6):
            dx = abs(x - cx)
            if dx == 5 or y in (7, 21):
                spr(px, x, y, PAL["brass"] if (x + y) % 2 else PAL["brass_hl"])
            elif dx == 2 and y % 4 != 1:
                spr(px, x, y, PAL["brass"])
            else:
                dy = abs(y - 14)
                c = PAL["glass_glow"] if dx <= 1 and dy <= 3 else PAL["flame"]
                spr(px, x, y, c)
    for y in range(11, 18):
        spr(px, cx, y, PAL["flame_core"])
    for x in range(cx - 3, cx + 4):
        spr(px, x, 22, PAL["brass_hl"] if x % 2 else PAL["brass"])
    return img

def sprite_torch(seed=239):
    rng = random.Random(seed)
    img = _sprite()
    px = img.load()
    for y in range(14, 28):
        spr(px, 15, y, PAL["wood_mid"])
        spr(px, 16, y, PAL["wood_light"])
        spr(px, 17, y, PAL["wood_dark"])
    for x in range(14, 19):
        spr(px, x, 13, PAL["iron"])
    for dy in range(0, 8):
        w = 3 - dy // 3
        for dx in range(-w, w + 1):
            c = PAL["flame_core"] if abs(dx) < 1 and dy > 2 else PAL["flame"] if dy > 1 else PAL["flame_deep"]
            if rng.random() < 0.9:
                spr(px, 16 + dx, 12 - dy, c)
    return img

def sprite_oil_flask(seed=241):
    img = _sprite()
    px = img.load()
    cx = 16
    spr(px, cx, 8, PAL["wood_dark"])  # cork
    spr(px, cx, 9, PAL["wood_mid"])
    for y in range(10, 13):
        spr(px, cx - 1, y, PAL["glass_glow"])
        spr(px, cx, y, PAL["glass_glow"])
        spr(px, cx + 1, y, PAL["glass_glow"])
    for y in range(13, 24):
        half = 4 if 14 < y < 22 else 3
        for dx in range(-half, half + 1):
            c = PAL["brass"] if y > 16 else PAL["glass_glow"]  # oil below, air above
            if abs(dx) == half:
                c = shade(PAL["glass_glow"], 0.7)
            spr(px, cx + dx, y, c)
    spr(px, cx - 2, 15, (255, 255, 255))  # glint
    return img

def sprite_matchbox(seed=251):
    img = _sprite()
    px = img.load()
    for x in range(9, 24):
        for y in range(14, 22):
            edge = x in (9, 23) or y in (14, 21)
            c = shade(PAL["carpet_deep"], 1.2) if not edge else shade(PAL["carpet_deep"], 0.7)
            spr(px, x, y, c)
    for x in range(11, 22):  # striker strip
        spr(px, x, 20, PAL["marble_dark"])
    # a match leaning out
    for i in range(6):
        spr(px, 20 + i // 2, 13 - i, PAL["cream"])
    spr(px, 23, 7, PAL["ember"])
    return img

def sprite_candelabrum(seed=257):
    img = _sprite()
    px = img.load()
    cx = 16
    for y in range(24, 28):
        for x in range(cx - 3 + (y - 24), cx + 4 - (y - 24)):
            spr(px, x, y, PAL["brass"] if y % 2 else PAL["brass_hl"])
    for y in range(14, 24):
        spr(px, cx, y, PAL["brass"])
    for dx in (-6, 0, 6):  # three arms
        spr(px, cx + dx, 13, PAL["brass_hl"])
        for y in range(10, 13):
            spr(px, cx + dx, y, PAL["wax"])
        spr(px, cx + dx, 9, PAL["flame"])
        spr(px, cx + dx, 8, PAL["flame_core"])
    for x in range(cx - 6, cx + 7):  # crossbar
        spr(px, x, 14, PAL["brass"])
    return img

def sprite_skull(seed=263):
    rng = random.Random(seed)
    img = _sprite()
    px = img.load()
    cx, cy = 16, 17
    for dx in range(-5, 6):
        for dy in range(-5, 4):
            if dx * dx + (dy * 1.2) ** 2 <= 24:
                c = PAL["bone"] if dy < 1 else PAL["bone_shadow"]
                spr(px, cx + dx, cy + dy, shade(c, 1.0 + rng.uniform(-0.06, 0.06)))
    for ex in (-2, 2):  # sockets
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:
                    spr(px, cx + ex + dx, cy - 1 + dy, PAL["void"])
    spr(px, cx, cy + 1, PAL["bone_dark"])  # nasal
    for dx in range(-2, 3):  # teeth
        spr(px, cx + dx, cy + 3, PAL["bone"] if dx % 2 else PAL["bone_shadow"])
    return img

def sprite_camera(seed=317):
    img = _sprite()
    px = img.load()
    # bellows box camera: wooden body, leather bellows, brass lens
    for x in range(8, 15):
        for y in range(11, 21):
            spr(px, x, y, PAL["wood_mid"] if (x + y) % 5 else PAL["wood_dark"])
    for i, x in enumerate(range(15, 21)):  # bellows folds
        for y in range(12, 20):
            spr(px, x, y, PAL["velvet_deep"] if i % 2 else PAL["velvet_mid"])
    for y in range(13, 19):  # lens board
        spr(px, 21, y, PAL["wood_dark"])
    for dy in range(-2, 3):  # brass lens
        for dx in range(0, 3):
            if abs(dy) + dx < 4:
                spr(px, 22 + dx, 16 + dy, PAL["brass"] if dx < 2 else PAL["brass_hl"])
    spr(px, 24, 16, PAL["glass_glow"])  # glint
    spr(px, 11, 10, PAL["brass_hl"])    # shutter knob
    for y in range(21, 26):  # tripod hint
        spr(px, 11, y, PAL["iron"])
        spr(px, 15, y, PAL["iron"])
    return img

def sprite_grimoire(seed=331):
    rng = random.Random(seed)
    img = _sprite()
    px = img.load()
    for x in range(9, 24):
        for y in range(10, 24):
            edge = x in (9, 23) or y in (10, 23)
            c = PAL["velvet_deep"] if not edge else shade(PAL["velvet_deep"], 0.6)
            spr(px, x, y, c)
    for y in range(10, 24):  # spine
        spr(px, 10, y, PAL["iron"])
    # brass corners and clasp
    for (cx, cy) in ((22, 11), (22, 22), (11, 11), (11, 22)):
        spr(px, cx, cy, PAL["brass_hl"])
    for y in range(15, 19):
        spr(px, 23, y, PAL["brass"])
    # embossed eye sigil
    for dx in range(-2, 3):
        spr(px, 16 + dx, 16, PAL["frame_gold"])
    spr(px, 16, 15, PAL["frame_gold"])
    spr(px, 16, 17, PAL["frame_gold"])
    spr(px, 16, 16, PAL["glass_glow"])
    return img

def sprite_key(seed=337):
    img = _sprite()
    px = img.load()
    # ornate bow (ring with trefoil)
    import math
    for a in range(0, 360, 12):
        x = int(11 + 3.5 * math.cos(a * math.pi / 180))
        y = int(12 + 3.5 * math.sin(a * math.pi / 180))
        spr(px, x, y, PAL["brass"])
    for (dx, dy) in ((0, -5), (-4, 3), (4, 3)):
        spr(px, 11 + dx // 2, 12 + dy // 2, PAL["brass_hl"])
    # shaft
    for i in range(10):
        spr(px, 14 + i, 15 + i // 2, PAL["brass"] if i % 2 else PAL["brass_hl"])
    # wards
    spr(px, 23, 21, PAL["brass"])
    spr(px, 23, 22, PAL["brass"])
    spr(px, 21, 22, PAL["brass"])
    return img

def sprite_potion(color_key, seed=347):
    img = _sprite()
    px = img.load()
    cx = 16
    spr(px, cx, 9, PAL["wood_dark"])
    spr(px, cx, 10, PAL["wood_mid"])
    for y in range(11, 14):
        for dx in range(-1, 2):
            spr(px, cx + dx, y, shade(PAL["glass_glow"], 0.8))
    for y in range(14, 23):
        half = 3 if y < 21 else 2
        for dx in range(-half, half + 1):
            liquid = y > 15
            c = PAL[color_key] if liquid else shade(PAL["glass_glow"], 0.8)
            if abs(dx) == half:
                c = shade(c, 0.65)
            spr(px, cx + dx, y, c)
    spr(px, cx - 1, 16, shade(PAL[color_key], 1.5))  # glint
    return img

def sprite_gravestone(seed=353):
    rng = random.Random(seed)
    img = _sprite()
    px = img.load()
    for x in range(10, 23):
        for y in range(10, 27):
            arch = (x - 16) ** 2 // 6 + 10
            if y >= arch:
                edge = x in (10, 22) or y == 26 or y == arch
                c = PAL["stone_light"] if not edge else PAL["stone_dark"]
                spr(px, x, y, shade(c, 1.0 + rng.uniform(-0.08, 0.08)))
    # engraved cross and lines
    for y in range(13, 18):
        spr(px, 16, y, PAL["stone_dark"])
    for x in range(14, 19):
        spr(px, x, 15, PAL["stone_dark"])
    for x in range(13, 20):
        spr(px, x, 20, PAL["stone_dark"])
        if x % 2:
            spr(px, x, 22, PAL["stone_dark"])
    # moss at the base
    for x in range(10, 23):
        if rng.random() < 0.5:
            spr(px, x, 26, PAL["moss"])
    return img

def sprite_urn(seed=359):
    rng = random.Random(seed)
    img = _sprite()
    px = img.load()
    cx = 16
    profile = [2, 3, 4, 5, 5, 5, 4, 4, 3, 3, 2, 3, 4]
    for i, half in enumerate(profile):
        y = 10 + i
        for dx in range(-half, half + 1):
            c = PAL["terracotta"]
            if dx == -half + 1:
                c = shade(c, 1.25)
            elif dx >= half - 1:
                c = shade(c, 0.7)
            spr(px, cx + dx, y, c)
    # lid knob and band
    spr(px, cx, 9, PAL["terracotta"])
    for dx in range(-4, 5):
        spr(px, cx + dx, 14, PAL["frame_gold"])
    return img

def sprite_clock(seed=367):
    rng = random.Random(seed)
    img = _sprite()
    px = img.load()
    # grandfather clock: tall case
    for x in range(11, 22):
        for y in range(3, 29):
            edge = x in (11, 21) or y in (3, 28)
            c = PAL["wood_mid"] if not edge else PAL["wood_dark"]
            spr(px, x, y, shade(c, 1.0 + rng.uniform(-0.05, 0.05)))
    # face
    import math
    for a in range(0, 360, 8):
        x = int(16 + 3.5 * math.cos(a * math.pi / 180))
        y = int(8 + 3.5 * math.sin(a * math.pi / 180))
        spr(px, x, y, PAL["brass_hl"])
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx * dx + dy * dy <= 6:
                spr(px, 16 + dx, 8 + dy, PAL["cream"])
    spr(px, 16, 8, PAL["iron"])
    spr(px, 16, 7, PAL["iron"])      # hand at midnight
    spr(px, 17, 8, PAL["iron"])
    # pendulum window
    for x in range(14, 19):
        for y in range(14, 25):
            spr(px, x, y, shade(PAL["void"], 1.0) if x in (14, 18) else PAL["marble_dark"])
    for y in range(15, 21):
        spr(px, 16, y, PAL["brass"])
    for dx in range(-1, 2):
        spr(px, 16 + dx, 21, PAL["brass_hl"])  # pendulum bob
    return img

# --- Output -----------------------------------------------------------------
import os
out = os.environ.get("OUT_DIR", ".")
os.makedirs(out, exist_ok=True)

tiles = {
    "wall_stone": stone_wall(),
    "wall_stone2": stone_wall(19),          # layout variant for tiling variety
    "wall_stone_cracked": stone_wall_cracked(),
    "wall_stone_mossy": stone_wall_mossy(),
    "wall_gaslamp": gaslamp_wall(),
    "wall_brick": brick_wall(),
    "wall_brick2": brick_wall(59),          # layout variant
    "wall_bone": bone_wall(),
    "wall_wood_panel": wood_panel(),
    "wall_wallpaper": wallpaper(),
    "wall_bookshelf": bookshelf(),
    "wall_bookshelf2": bookshelf(77),       # different books
    "wall_stained_glass": stained_glass(),
    "wall_iron_grate": iron_grate(),
    "wall_fireplace": fireplace(),
    "wall_portrait": portrait_wall(),
    "wall_door_wood": door_wood(),
    "wall_chapel_arch": chapel_arch(),
    "floor_flagstone": stone_floor(),
    "floor_flagstone2": stone_floor(29),    # layout variant
    "floor_planks": floor_planks(),
    "floor_marble": floor_marble(),
    "floor_dirt": floor_dirt(),
    "floor_carpet": floor_carpet(),
    "floor_cobble": floor_cobble(),
    "floor_mosaic": floor_mosaic(),
    "floor_water": floor_water(),
    "ceiling_beams": ceiling_beams(),
    "floor_encaustic": floor_encaustic(),
    "wall_pipe": wall_pipe(),
    "wall_candles": wall_candles(),
    "wall_ivy": wall_ivy(),
    "wall_plaques": wall_plaques(),
    "floor_bones": floor_bones(),
    "floor_moss": floor_moss(),
    "ceiling_vault": ceiling_vault(),
    "ceiling_planks": ceiling_planks(),
    "wall_curtain": wall_curtain(),
    "wall_organ": wall_organ(),
    "wall_apothecary": wall_apothecary(),
    "wall_padded": wall_padded(),
    "wall_asylum_tiles": wall_asylum_tiles(),
    "wall_mirror": wall_mirror(),
    "floor_ritual": floor_ritual(),
    "floor_grate": floor_grate(),
    "floor_blood": floor_blood(),
    "wall_gaslamp_unlit": gaslamp_unlit(),
    "wall_stone_frieze": wall_stone_frieze(),
    "floor_rubble": floor_rubble(),
    "wall_bone_columns": bone_wall_columns(),
    "wall_coffin_niche": wall_coffin_niche(),
    "floor_water_scum": floor_water_scum(),
    "wall_wallpaper_red": wallpaper_red(),
    "wall_wallpaper_torn": wallpaper_torn(),
    "wall_window_boarded": wall_window_boarded(),
    "floor_planks_rotten": floor_planks_rotten(),
    "wall_painting": wall_painting(),
    "floor_carpet_blue": floor_carpet_blue(),
    "wall_stained_glass_blue": stained_glass_blue(),
    "floor_mosaic_cross": floor_mosaic_cross(),
    "wall_asylum_blood": wall_asylum_blood(),
    "wall_padded_torn": wall_padded_torn(),
}
for name, img in tiles.items():
    img.save(f"{out}/{name}.png")

# item / decor sprites (RGBA)
sprites = {
    "sprite_lantern": sprite_lantern(),
    "sprite_torch": sprite_torch(),
    "sprite_oil_flask": sprite_oil_flask(),
    "sprite_matchbox": sprite_matchbox(),
    "sprite_candelabrum": sprite_candelabrum(),
    "sprite_skull": sprite_skull(),
    "sprite_camera": sprite_camera(),
    "sprite_grimoire": sprite_grimoire(),
    "sprite_key": sprite_key(),
    "sprite_potion_red": sprite_potion("potion_red"),
    "sprite_potion_green": sprite_potion("potion_green"),
    "sprite_gravestone": sprite_gravestone(),
    "sprite_urn": sprite_urn(),
    "sprite_clock": sprite_clock(),
}
for name, img in sprites.items():
    img.save(f"{out}/{name}.png")

# sprite preview: dark backdrop, 6x scale, one row
sscale = 6
srow = Image.new("RGB", (7 * (S * sscale + 10) - 10, ((len(sprites) + 6) // 7) * (S * sscale + 10) - 10), (18, 18, 22))
for idx, (name, img) in enumerate(sprites.items()):
    big = img.resize((S * sscale, S * sscale), Image.NEAREST)
    srow.paste(big, ((idx % 7) * (S * sscale + 10), (idx // 7) * (S * sscale + 10)), big)
srow.save(f"{out}/preview_sprites.png")

# preview sheet: each tile 3x3 tiled, upscaled, arranged in a grid
tile_grid = 3
scale = 5
gap = 10
cols = 7
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
