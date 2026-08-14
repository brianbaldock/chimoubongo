"""Regression checks for the baked Fourthwall product art and markup.

Run: python3 tools/test_shop_assets.py
"""
import json
from pathlib import Path
from typing import cast
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAPER2 = (242, 237, 225)
EXPECTED = {
    "cafemoubongo.jpg",
    "hoodiemoubongo.jpg",
    "shirtmoubongo-2.jpg",
    "shirtmoubongo.jpg",
    "stickermoubongo.jpg",
    "truckermoubongo.jpg",
}

shop = json.loads((ROOT / "assets" / "shop.json").read_text(encoding="utf-8"))
assert len(shop["products"]) == 5

for name in EXPECTED:
    path = ROOT / "assets" / "shop" / name
    assert path.is_file(), f"missing baked product art: {name}"
    with Image.open(path) as image:
        assert image.format == "JPEG", f"{name}: expected JPEG, got {image.format}"
        assert image.size == (900, 1200), f"{name}: expected 900x1200, got {image.size}"
        corner = cast(tuple[int, int, int], image.convert("RGB").getpixel((0, 0)))
        assert max(abs(a - b) for a, b in zip(corner, PAPER2)) <= 4, (
            f"{name}: transparent source did not flatten onto --paper2: {corner}"
        )

for page in ("hangar.html", "en-shop.html"):
    text = (ROOT / page).read_text(encoding="utf-8")
    start = text.index('<section id="shop">')
    end = text.index('</section>', start)
    section = text[start:end]
    assert section.count('<div class="good">') == 5, f"{page}: expected five cards"
    assert section.count('width="900" height="1200"') == 5, f"{page}: stale image dimensions"
    assert "ptkn_" not in section, f"{page}: token leaked into markup"
    assert section.count("<form") == section.count("</form>") == 5, f"{page}: checkout forms"

print("OK shop product art is 3:4, paper-composited, and static")
