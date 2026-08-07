"""Bake OpenStreetMap raster tiles into flat images shipped in assets/.

Why bake instead of embedding Leaflet or an iframe:
  * no third-party request from a visitor's browser, so no visitor IP or
    referrer reaches a tile server, and the site keeps its no-tracker promise
  * no CDN dependency, no JS, works offline and from file://
  * the image is stable forever, so the map cannot silently redraw itself

OSM tile usage policy: bulk downloading is discouraged, so this script is a
one-shot bake (a few dozen tiles total, cached on disk) and is NOT run at
build time or on a schedule. Attribution is rendered in the page next to the
map, which the ODbL requires.

Run manually: python3 tools/bake_map.py
"""
import math
import os
import time
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
CACHE = os.path.join(HERE, ".tilecache")

UA = "chimoubongo.com one-shot static map bake (github.com/brianbaldock/chimoubongo)"
TILE = 256

# The coordinates the village gives out: 47 deg 03' N, 72 deg 59' O.
# Chosen with tools/find_empty.py against real OSM data. At z13 this tile is
# 94.2% forest and 0.04% built, so a reader who zooms in finds nothing there,
# which is the point. It also sits west of Route 155 between Grandes-Piles and
# Lac-Edouard, which is what the copy claims.
VILLAGE = (47.05, -72.98)


def lon2x(lon, z):
    return (lon + 180.0) / 360.0 * (2 ** z)


def lat2y(lat, z):
    r = math.radians(lat)
    return (1.0 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2.0 * (2 ** z)


def fetch(z, x, y):
    path = os.path.join(CACHE, "%d_%d_%d.png" % (z, x, y))
    if os.path.exists(path):
        return path
    os.makedirs(CACHE, exist_ok=True)
    url = "https://tile.openstreetmap.org/%d/%d/%d.png" % (z, x, y)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    if body[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("not a png: %s" % url)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(body)
    os.replace(tmp, path)
    time.sleep(0.35)  # be polite to the tile servers
    return path


def bake(name, z, west, south, east, north, out_width, quality=82, aspect=None):
    """Stitch the tile grid covering the bbox, then crop to the exact bbox.

    If ``aspect`` (width/height) is given, the bbox is first expanded
    symmetrically about its centre in whichever axis is short, so the output
    hits that ratio exactly. That matters because the marker overlay is
    positioned in percentages: any object-fit cropping in CSS would slide the
    pin off the coordinates it is supposed to mark.
    """
    fx0, fx1 = lon2x(west, z), lon2x(east, z)
    fy0, fy1 = lat2y(north, z), lat2y(south, z)
    if aspect:
        w, h = (fx1 - fx0), (fy1 - fy0)
        if w / h < aspect:  # too tall, widen
            cx, need = (fx0 + fx1) / 2, h * aspect
            fx0, fx1 = cx - need / 2, cx + need / 2
        else:  # too wide, heighten
            cy, need = (fy0 + fy1) / 2, w / aspect
            fy0, fy1 = cy - need / 2, cy + need / 2
    x0, x1 = int(math.floor(fx0)), int(math.ceil(fx1))
    y0, y1 = int(math.floor(fy0)), int(math.ceil(fy1))
    cols, rows = x1 - x0, y1 - y0
    canvas = Image.new("RGB", (cols * TILE, rows * TILE), (233, 229, 220))
    n = 0
    for xi in range(cols):
        for yi in range(rows):
            canvas.paste(Image.open(fetch(z, x0 + xi, y0 + yi)).convert("RGB"),
                         (xi * TILE, yi * TILE))
            n += 1
    box = (int(round((fx0 - x0) * TILE)), int(round((fy0 - y0) * TILE)),
           int(round((fx1 - x0) * TILE)), int(round((fy1 - y0) * TILE)))
    img = canvas.crop(box)
    w, h = img.size
    img = img.resize((out_width, max(1, int(round(h * out_width / w)))), Image.LANCZOS)
    out = os.path.join(ASSETS, name)
    img.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
    # Marker position as a fraction of the FINAL image, computed from the same
    # (possibly aspect-expanded) bbox used for the crop.
    mx = (lon2x(VILLAGE[1], z) - fx0) / (fx1 - fx0)
    my = (lat2y(VILLAGE[0], z) - fy0) / (fy1 - fy0)
    print("%-16s z=%-3d tiles=%-4d out=%dx%d ratio=%.3f %d bytes  pin left=%.2f%% top=%.2f%%"
          % (name, z, n, img.size[0], img.size[1], img.size[0] / img.size[1],
             os.path.getsize(out), mx * 100, my * 100))
    return img.size, mx, my


def frac(lat, lon, z, west, south, east, north):
    """Where a point falls inside a baked bbox, as 0..1 fractions. For CSS.

    Only valid for a bake with no aspect expansion; prefer the values that
    bake() itself returns.
    """
    fx = (lon2x(lon, z) - lon2x(west, z)) / (lon2x(east, z) - lon2x(west, z))
    fy = (lat2y(lat, z) - lat2y(north, z)) / (lat2y(south, z) - lat2y(north, z))
    return fx, fy


if __name__ == "__main__":
    # Both plates are baked to the same 4:3 ratio so they sit level side by
    # side and the CSS never has to crop them.
    ASPECT = 4 / 3

    # Regional: Shawinigan up the Saint-Maurice corridor to past La Tuque.
    bake("map-region.jpg", z=10, west=-73.85, south=46.45, east=-72.05,
         north=47.70, out_width=1400, aspect=ASPECT)

    # Detail: the claimed coordinates, close enough to show nothing is there.
    bake("map-detail.jpg", z=12, west=-73.28, south=46.90, east=-72.68,
         north=47.20, out_width=1400, aspect=ASPECT)
