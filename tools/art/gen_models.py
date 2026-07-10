#!/usr/bin/env python3
"""Project Umbra — generate voxel models in the engine's slab .vox format.

Format (see src/files.cpp loadVoxel):
    Sint32 sizex, sizey, sizez  (little-endian)
    Uint8 data[sizex*sizey*sizez]   index = x*(sizez*sizey) + y*sizez + z
    Uint8 palette[256][3]           channels 0..63 (engine shifts <<2)
Palette index 255 = empty voxel.

World objects in the engine are these voxel models; map tiles are 2D
textures on 3D geometry (tools/art/gen_textures.py) and inventory icons
are 2D RGBA sprites. This completes the third leg of the art pipeline.

Output: <name>.vox + preview_models.png (isometric render).
"""
import os
import struct
import random
from PIL import Image

EMPTY = 255

# --- palette (from the style guide, full 0-255 range here) --------------------
COLORS = {
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
    "bone":        (168, 158, 134),
    "bone_shadow": (118, 110, 92),
    "void_dark":   (10, 10, 12),
    "wax":         (188, 176, 148),
    "terracotta":  (122, 68, 48),
    "stone_mid":   (68, 73, 80),
    "velvet_deep": (52, 20, 26),
}
PALETTE_ORDER = list(COLORS.keys())
IDX = {name: i for i, name in enumerate(PALETTE_ORDER)}


class Vox:
    def __init__(self, sx, sy, sz):
        self.sx, self.sy, self.sz = sx, sy, sz
        self.data = bytearray([EMPTY]) * 0
        self.data = bytearray([EMPTY] * (sx * sy * sz))

    def set(self, x, y, z, color):
        if 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz:
            self.data[x * (self.sz * self.sy) + y * self.sz + z] = IDX[color]

    def get(self, x, y, z):
        if 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz:
            return self.data[x * (self.sz * self.sy) + y * self.sz + z]
        return EMPTY

    def box(self, x0, y0, z0, x1, y1, z1, color):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.set(x, y, z, color)

    def sphere(self, cx, cy, cz, r, color):
        for x in range(cx - r, cx + r + 1):
            for y in range(cy - r, cy + r + 1):
                for z in range(cz - r, cz + r + 1):
                    if (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2 <= r * r + r * 0.5:
                        self.set(x, y, z, color)

    def write(self, path):
        with open(path, "wb") as f:
            f.write(struct.pack("<iii", self.sx, self.sy, self.sz))
            f.write(bytes(self.data))
            pal = bytearray(256 * 3)
            for i, name in enumerate(PALETTE_ORDER):
                r, g, b = COLORS[name]
                pal[i * 3 + 0] = r >> 2
                pal[i * 3 + 1] = g >> 2
                pal[i * 3 + 2] = b >> 2
            f.write(bytes(pal))


def read_check(path):
    """Round-trip check mirroring src/files.cpp loadVoxel."""
    with open(path, "rb") as f:
        sx, sy, sz = struct.unpack("<iii", f.read(12))
        assert sx > 0 and sy > 0 and sz > 0
        data = f.read(sx * sy * sz)
        assert len(data) == sx * sy * sz
        pal = f.read(256 * 3)
        assert len(pal) == 256 * 3
    return sx, sy, sz


# --- models -------------------------------------------------------------------

def model_wall_torch():
    """Wall sconce: iron bracket, wooden shaft, flame head. Z is up-ish in
    model space; the engine orients by entity yaw."""
    v = Vox(8, 8, 18)
    # iron bracket (against the x=0 wall side)
    v.box(0, 3, 4, 1, 4, 6, "iron")
    v.box(1, 3, 5, 3, 4, 6, "iron_hl")
    # wooden shaft, slightly leaning out from the wall
    for i in range(8):
        x = 2 + i // 3
        v.box(x, 3, 6 + i, x + 1, 4, 6 + i, "wood_mid" if i % 2 else "wood_light")
    # binding ring and tarred head (the engine draws fire itself: actTorch
    # spawns billboard flame particles every tick - models stay flameless)
    v.box(4, 3, 13, 5, 4, 13, "iron_hl")
    v.box(4, 3, 14, 5, 4, 15, "void_dark")
    return v


def model_wall_torch_unlit():
    # visually identical stick; "unlit" is a runtime state (no flame
    # particles, no light). Kept as a separate model in case we later
    # want a crumbled/burnt look for long-cold sconces.
    v = model_wall_torch()
    return v


def model_lantern():
    v = Vox(10, 10, 14)
    # base
    v.box(3, 3, 0, 6, 6, 1, "brass")
    # glass body with brass corner posts
    for (x, y) in ((2, 2), (2, 7), (7, 2), (7, 7)):
        v.box(x, y, 2, x, y, 9, "brass")
    for z in range(2, 10):
        for x in range(3, 7):
            v.set(x, 2, z, "glass_glow")
            v.set(x, 7, z, "glass_glow")
        for y in range(3, 7):
            v.set(2, y, z, "glass_glow")
            v.set(7, y, z, "glass_glow")
    # inner flame
    v.box(4, 4, 3, 5, 5, 5, "flame")
    v.box(4, 4, 5, 5, 5, 6, "flame_core")
    # crown and hanging ring
    v.box(2, 2, 10, 7, 7, 10, "brass")
    v.box(4, 4, 11, 5, 5, 11, "brass_hl")
    v.set(4, 4, 12, "iron")
    v.set(5, 5, 12, "iron")
    v.set(4, 4, 13, "iron_hl")
    return v


def model_skull():
    v = Vox(10, 12, 10)
    v.sphere(5, 5, 5, 4, "bone")
    # jaw
    v.box(3, 8, 1, 7, 10, 3, "bone_shadow")
    # eye sockets
    v.box(3, 2, 4, 4, 3, 5, "void_dark")
    v.box(6, 2, 4, 7, 3, 5, "void_dark")
    # nasal
    v.set(5, 2, 3, "void_dark")
    # cheekbones shade
    v.set(2, 4, 4, "bone_shadow")
    v.set(8, 4, 4, "bone_shadow")
    return v


def model_candelabrum():
    v = Vox(14, 6, 16)
    # base
    v.box(5, 2, 0, 9, 4, 0, "brass")
    v.box(6, 2, 1, 8, 4, 1, "brass_hl")
    # stem
    v.box(7, 3, 2, 7, 3, 8, "brass")
    # crossbar
    v.box(2, 3, 9, 12, 3, 9, "brass")
    # three candle cups + candles + flames
    for cx in (2, 7, 12):
        v.set(cx, 3, 10, "brass_hl")
        v.box(cx, 3, 11, cx, 3, 12, "wax")
        v.set(cx, 3, 13, "flame")
        v.set(cx, 3, 14, "flame_core")
    return v


def model_oil_flask():
    v = Vox(8, 8, 12)
    # rounded body with oil
    v.sphere(4, 4, 3, 3, "glass_glow")
    v.sphere(4, 4, 2, 2, "brass")  # oil seen through glass
    # neck
    v.box(3, 3, 6, 4, 4, 8, "glass_glow")
    # cork
    v.box(3, 3, 9, 4, 4, 10, "wood_mid")
    return v


# --- isometric preview ----------------------------------------------------------

def render_iso(v, scale=6):
    """Simple painter's-algorithm isometric render."""
    W = (v.sx + v.sy) * scale + scale * 2
    H = (v.sx + v.sy) * scale // 2 + v.sz * scale + scale * 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    ox = v.sy * scale
    oy = H - scale
    for z in range(v.sz):
        for y in range(v.sy - 1, -1, -1):
            for x in range(v.sx):
                c = v.get(x, y, z)
                if c == EMPTY:
                    continue
                name = PALETTE_ORDER[c]
                base = COLORS[name]
                sx = ox + (x - y) * scale
                sy = oy - (x + y) * scale // 2 - z * scale
                # top face lighter, right face darker
                for dx in range(scale):
                    for dy in range(scale):
                        f = 1.0
                        if dy < scale // 3:
                            f = 1.25
                        elif dx > 2 * scale // 3:
                            f = 0.7
                        col = tuple(max(0, min(255, int(ch * f))) for ch in base)
                        X, Y = sx + dx, sy - dy
                        if 0 <= X < W and 0 <= Y < H:
                            px[X, Y] = (*col, 255)
    return img


out = os.environ.get("OUT_DIR", ".")
os.makedirs(out, exist_ok=True)

models = {
    "wall_torch": model_wall_torch(),
    "wall_torch_unlit": model_wall_torch_unlit(),
    "lantern": model_lantern(),
    "skull": model_skull(),
    "candelabrum": model_candelabrum(),
    "oil_flask": model_oil_flask(),
}
for name, v in models.items():
    path = f"{out}/{name}.vox"
    v.write(path)
    sx, sy, sz = read_check(path)
    assert (sx, sy, sz) == (v.sx, v.sy, v.sz), name

# preview: renders side by side on dark backdrop
renders = [render_iso(v) for v in models.values()]
gap = 12
W = sum(r.width for r in renders) + gap * (len(renders) + 1)
H = max(r.height for r in renders) + gap * 2
sheet = Image.new("RGB", (W, H), (18, 18, 22))
x = gap
for r in renders:
    sheet.paste(r, (x, H - r.height - gap), r)
    x += r.width + gap
sheet.save(f"{out}/preview_models.png")
print("generated models:", ", ".join(models.keys()), "(slab .vox, round-trip checked)")
