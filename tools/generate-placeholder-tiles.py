#!/usr/bin/env python3
"""Generate placeholder world tiles for developing map-navigator.html.

Creates dummy images for every bigworld tile (world_100_100 .. world_129_129)
at the sizes the navigator uses, so the page can be developed and tested
without the real Crossfire Atlas renders:

    world_<x>_<y>.x1.png   1600 x 1600
    world_<x>_<y>.x3.png    400 x 400
    world_<x>_<y>.x4.png    200 x 200
    world_<x>_<y>.x5.png    100 x 100

Each tile shows its coordinates and a color that varies smoothly with
position (with an ocean ring on the outermost tiles), so panning and zoom
continuity are easy to eyeball. Uses only the Python standard library.

Usage:
    tools/generate-placeholder-tiles.py <output-dir> [--detail-pages] [--force]

    --detail-pages  also write a stub world_<x>_<y>.html for every tile
                    (the target of the navigator's "Open tile detail page" link)
    --force         overwrite files that already exist
"""

import struct
import sys
import zlib
from pathlib import Path

MIN, MAX = 100, 129
BASE = 100                      # tiles are drawn on a 100x100 logical canvas
SIZES = {"x1": 1600, "x3": 400, "x4": 200, "x5": 100}

# 5x7 bitmap glyphs for the coordinate labels.
FONT = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["01110", "10001", "00001", "00110", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ",": ["00000", "00000", "00000", "00000", "00110", "00110", "01100"],
}
GLYPH_W, GLYPH_H, TRACKING = 5, 7, 1


def write_png(path, size, rows):
    """Write an 8-bit RGB PNG from a list of `size` bytearrays of 3*size bytes."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data)))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(raw, 3)))
        f.write(chunk(b"IEND", b""))


def tile_color(x, y):
    """A muted, position-dependent color; ocean blue on the border ring."""
    if x in (MIN, MAX) or y in (MIN, MAX):
        return (58, 78, 148)
    fx, fy = (x - MIN) / (MAX - MIN), (y - MIN) / (MAX - MIN)
    r = int(96 + 70 * fx)
    g = int(120 + 60 * (1 - fy))
    b = int(72 + 40 * fx * fy)
    return (r, g, b)


def darken(c, f=0.55):
    return tuple(int(v * f) for v in c)


def draw_base(x, y):
    """Render the 100x100 logical canvas for one tile."""
    bg = tile_color(x, y)
    edge = darken(bg)
    px = [[bg] * BASE for _ in range(BASE)]

    for i in range(BASE):                      # 1px tile border
        px[0][i] = px[BASE - 1][i] = px[i][0] = px[i][BASE - 1] = edge

    label = "%d,%d" % (x, y)
    scale = 2
    w = (len(label) * (GLYPH_W + TRACKING) - TRACKING) * scale
    ox = (BASE - w) // 2
    oy = (BASE - GLYPH_H * scale) // 2
    ink = (255, 255, 245)
    shadow = darken(bg, 0.35)
    for i, ch in enumerate(label):
        gx = ox + i * (GLYPH_W + TRACKING) * scale
        for ry, bits in enumerate(FONT[ch]):
            for rx, bit in enumerate(bits):
                if bit != "1":
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        yy = oy + ry * scale + sy
                        xx = gx + rx * scale + sx
                        px[yy + 1][xx + 1] = shadow
                        px[yy][xx] = ink
    return px


def scaled_rows(base_px, size):
    """Nearest-neighbor upscale of the logical canvas to `size` pixels."""
    k = size // BASE
    rows = []
    for line in base_px:
        row = bytearray()
        for c in line:
            row += bytes(c) * k
        rows.extend([row] * k)
    return rows


DETAIL_STUB = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>%(name)s</title></head>
<body style="background:#1a1611;color:#e8dcc4;font-family:Georgia,serif;text-align:center">
<h1>%(name)s</h1>
<p>Placeholder detail page for development.</p>
<p><img src="%(name)s.x1.png" alt="%(name)s" style="max-width:90vmin"></p>
<p><a href="map-navigator.html#%(x)d,%(y)d,3" style="color:#d4a843">Back to the navigator</a></p>
</body></html>
"""


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = set(a for a in argv[1:] if a.startswith("--"))
    unknown = flags - {"--detail-pages", "--force"}
    if len(args) != 1 or unknown:
        sys.exit(__doc__.strip().split("\n\n")[-1])

    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    force = "--force" in flags

    written = skipped = 0
    for y in range(MIN, MAX + 1):
        for x in range(MIN, MAX + 1):
            name = "world_%d_%d" % (x, y)
            base_px = None
            for sfx, size in SIZES.items():
                path = out / ("%s.%s.png" % (name, sfx))
                if path.exists() and not force:
                    skipped += 1
                    continue
                if base_px is None:
                    base_px = draw_base(x, y)
                write_png(path, size, scaled_rows(base_px, size))
                written += 1
            if "--detail-pages" in flags:
                page = out / (name + ".html")
                if force or not page.exists():
                    page.write_text(DETAIL_STUB % {"name": name, "x": x, "y": y})
        print("row %d done" % y, file=sys.stderr)

    print("wrote %d images, skipped %d existing (use --force to overwrite)"
          % (written, skipped), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
