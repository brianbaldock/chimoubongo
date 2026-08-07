"""Check OSM tile reachability for the Chimoubongo map, and print tile numbers.

Not shipped. Run manually: python3 tools/tilecheck.py
"""
import math
import urllib.request

LAT, LON = 47.35, -72.8167  # the coordinates the village claims


def deg2num(lat, lon, z):
    r = math.radians(lat)
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2.0 * n)
    return x, y


UA = "chimoubongo.com static site build (contact: brianbaldock on github)"

for z in (8, 9, 10, 11, 12):
    x, y = deg2num(LAT, LON, z)
    url = "https://tile.openstreetmap.org/%d/%d/%d.png" % (z, x, y)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
        ok = body[:8] == b"\x89PNG\r\n\x1a\n"
        print("z=%-3d x=%-6d y=%-6d %s bytes=%d png=%s" % (z, x, y, r.status, len(body), ok))
    except Exception as exc:  # noqa: BLE001
        print("z=%-3d x=%-6d y=%-6d FAIL %s" % (z, x, y, exc))
