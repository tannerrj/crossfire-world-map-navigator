# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file, dependency-free web page (`map-navigator.html`) for interactively exploring
the Crossfire world map — a 30×30 grid of tiles named `world_<x>_<y>` with x and y each
ranging 100–129. There is no build step, no linter, no test suite, and no package manager;
everything (CSS, markup, JavaScript) lives in that one HTML file.

The map tile images are deliberately **not** in this repo (`*.png` is gitignored). They are
produced by the Crossfire Atlas rendering pipeline and live alongside the page when deployed.
On this machine the deployed copy with images is `/Users/leaf/website/crossfireatlas-website/world/`.

## Running it

Serve a directory that contains the tile images plus the page:

```sh
cd /Users/leaf/website/crossfireatlas-website/world
python3 -m http.server 8899
# open http://localhost:8899/map-navigator.html
```

Opening the file directly from this repo shows broken images (no tiles here). After editing
`map-navigator.html` in this repo, copy it into the world/ directory to test, and keep the
two copies in sync.

Without the real renders, `tools/generate-placeholder-tiles.py <dir> --detail-pages`
(stdlib-only, ~20s) generates coordinate-labeled placeholder tiles at all four sizes the
page uses, plus stub detail pages; copy `map-navigator.html` into that directory and serve it.

## Architecture

All state and rendering logic is in the inline `<script>` (an IIFE) at the bottom of
`map-navigator.html`:

- **State model**: either `{mode:'overview'}` (full 30×30 grid of `.x5.png` thumbnails) or
  `{mode:'zoom', wx, wy, z}` where `(wx, wy)` is the **top-left tile of the visible window**,
  not the center. The center tile is derived (`centerOf`).
- **`ZOOMS` table** maps each zoom level to a window size and pre-rendered image suffix:
  z1 = 5×5 tiles using `.x4.png` (200px), z2 = 3×3 using `.x3.png` (400px), z3 = 1×1 using
  `.x1.png` (1600px). The tile set also has `.x2.png` (800px) and `.png`/`.small.png`, which
  the page does not use. Adding/changing a zoom level means editing this table plus `MAXZ`.
- **Border behavior**: the window is clamped to the map (`clampW`), never showing void
  beyond the edge. Compass arrows disable via `canMove`; a diagonal is enabled only when
  both of its components can move.
- **URL hash** is the source of truth for shareable state: `#<cx>,<cy>,<z>` (center tile,
  three digits each) or `#world`. `applyHash`/`updateHash` guard against feedback loops
  with the `applyingHash` flag; state changes use `history.replaceState` so navigation
  doesn't pollute browser history.
- **`LANDMARKS`** holds city/region jump targets, extracted from `region` lines in the
  crossfire-maps source (the first non-`world` region in each `world/world_<x>_<y>` map
  file). Do not guess new entries — regenerate the array with
  `tools/extract-landmarks.sh /path/to/crossfire-maps` (local checkout:
  `/Users/leaf/Documents/cf-devel/crossfire-crossfire-maps`). The script emits official
  `longname` values from `regions.reg`; the names currently embedded in the page were
  hand-shortened for the dropdown (e.g. 'Scorn' instead of 'The Kingdom of Scorn').
- **Minimap** is a second 30×30 grid reusing the same `.x5.png` files (browser-cached from
  the overview) with a percent-positioned viewport rectangle overlay.
- The center-tile detail link points to the Atlas per-tile page `world_<x>_<y>.html`,
  which exists in the deployed world/ directory but not in this repo.
