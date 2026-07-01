# Crossfire World Map Navigator

An interactive, single-file web page for exploring the [Crossfire](https://crossfire.real-time.com/)
world map — the 30 × 30 grid of bigworld maps (`world_100_100` through `world_129_129`) as
rendered by the [Crossfire Atlas](https://www.crossfireatlas.net/).

The default view assembles all 900 tile thumbnails into the full world map. Visitors can
click any tile to zoom in, then step across the world with a compass rose or drill down to
a single map at full detail.

## Features

- **World view** — the complete 30×30 world assembled from the `.x5.png` thumbnails.
- **Three zoom levels**, each backed by the pre-rendered image size that matches its scale:

  | Level | Tiles shown | Image set | Tile size |
  |---|---|---|---|
  | Regional | 5 × 5 | `.x4.png` | 200 px |
  | Local | 3 × 3 | `.x3.png` | 400 px |
  | Single map | 1 × 1 | `.x1.png` | 1600 px |

- **Compass rose** with all eight direction arrows plus a center zoom-in button. Arrows
  grey out at the map borders; zoom-in greys out at full detail.
- **Landmark finder** — a dropdown of cities and regions (Scorn, Navar, Brest, Darcap,
  Santo Dominion, Wolfsburg, Azumauindo, and more). Coordinates were extracted from the
  `region` designations in the [crossfire-maps](https://sourceforge.net/p/crossfire/crossfire-maps/)
  source files.
- **Minimap** with a live viewport rectangle; click it to jump anywhere.
- **Coordinate jump** (x/y between 100 and 129), a random-tile button, and a toggle to
  overlay tile coordinates.
- **Shareable URLs** — the hash tracks the view (e.g. `#105,115,2`) and restores on load.
- **Keyboard navigation** — arrow keys or WASD move one tile (Shift jumps a full page),
  `+`/`-` zoom, `Esc` returns to the world view.
- **Deep links** — when zoomed, the center tile links to its Atlas detail page
  (`world_X_Y.html`).

## Deployment

Copy `map-navigator.html` into a directory containing the Crossfire Atlas world tile
images. The map images themselves are **not** part of this repository; they are produced
by the Crossfire Atlas rendering pipeline. The page expects, for every tile from
`world_100_100` to `world_129_129`:

```
world_<x>_<y>.x1.png   1600 × 1600  full detail
world_<x>_<y>.x3.png    400 × 400   local view
world_<x>_<y>.x4.png    200 × 200   regional view
world_<x>_<y>.x5.png    100 × 100   world view and minimap
world_<x>_<y>.html                  per-tile detail page (optional; used by the
                                    "Open tile detail page" link)
```

The page is fully standalone — no external libraries, no build step, and no server-side
code. Any static web server will do.

## Regenerating landmark data

The landmark dropdown data is derived from the map sources, not hand-maintained. When the
world maps change, regenerate the array from a
[crossfire-maps](https://sourceforge.net/p/crossfire/crossfire-maps/) checkout and paste
it over the `LANDMARKS` definition in `map-navigator.html`:

```sh
tools/extract-landmarks.sh /path/to/crossfire-maps
```

For each named region the script picks the region tile closest to the region's centroid
and takes its display name from the `longname` entries in `regions.reg`.

## Local testing

```sh
cd /path/to/atlas/world
python3 -m http.server 8899
# then open http://localhost:8899/map-navigator.html
```

## License

The navigator page is a small standalone work; the Crossfire map data and rendered
images it displays belong to the Crossfire project and carry their own licensing.
