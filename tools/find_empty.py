"""Scan candidate coordinates for a spot that is genuinely empty on OSM.

The village's claimed coordinates have to survive a reader zooming in, so the
point must sit in forest, off the 155, but still plausibly between
Grandes-Piles and Lac-Edouard. Prints how many non-background pixels each
candidate tile has: lower means emptier.

Run manually: python3 tools/find_empty.py
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bake_map import fetch, lat2y, lon2x  # noqa: E402

Z = 13
CANDIDATES = [
    (46.95, -72.95), (46.98, -73.05), (47.05, -72.98), (47.10, -73.10),
    (46.92, -73.12), (47.15, -72.95), (46.88, -72.98), (47.02, -73.20),
    (47.20, -73.05), (46.95, -73.25),
]

# OSM forest green and water blue are the "empty" colours.
FOREST = (173, 209, 158)


def emptiness(lat, lon):
    x, y = int(lon2x(lon, Z)), int(lat2y(lat, Z))
    img = Image.open(fetch(Z, x, y)).convert("RGB")
    px = list(img.getdata())
    forest = sum(1 for p in px if abs(p[0] - FOREST[0]) < 14
                 and abs(p[1] - FOREST[1]) < 14 and abs(p[2] - FOREST[2]) < 14)
    water = sum(1 for p in px if p[2] > p[0] + 25 and p[2] > 150)
    # roads and labels render as near-white or grey
    built = sum(1 for p in px if p[0] > 225 and p[1] > 225 and p[2] > 215)
    return len(px), forest, water, built


if __name__ == "__main__":
    rows = []
    for lat, lon in CANDIDATES:
        total, forest, water, built = emptiness(lat, lon)
        rows.append((built / total, lat, lon, forest / total, water / total))
    for built, lat, lon, forest, water in sorted(rows):
        print("%.4f, %.4f  built=%5.2f%%  forest=%5.1f%%  water=%4.1f%%"
              % (lat, lon, built * 100, forest * 100, water * 100))
