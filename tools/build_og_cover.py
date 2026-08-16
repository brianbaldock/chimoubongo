#!/usr/bin/env python3
"""Bake assets/og-cover.jpg: a 1200x630 social card from the square logo.

The square logo.png (900x900, 1.1MB PNG) previews badly as an og:image: platforms
crop or letterbox it, and it is the only un-optimized asset on the site. This
composites it onto the site's --paper2 colour with the wordmark and tagline.
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAPER2 = (242, 237, 225)
INK = (34, 28, 21)
W, H = 1200, 630

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_CANDIDATES_R = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def pick(cands, size):
    for c in cands:
        if pathlib.Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def main():
    logo = Image.open(ROOT / "assets" / "logo.png").convert("RGBA")
    card = Image.new("RGB", (W, H), PAPER2)

    box = 470
    logo_r = logo.resize((box, box), Image.LANCZOS)
    card.paste(logo_r, (70, (H - box) // 2), logo_r)

    d = ImageDraw.Draw(card)
    x = 70 + box + 60
    d.text((x, 250), "Chimoubongo", font=pick(FONT_CANDIDATES, 66), fill=INK)
    d.text((x, 335), "Quebec, Canada", font=pick(FONT_CANDIDATES_R, 34), fill=INK)
    d.line([(x, 315), (x + 400, 315)], fill=INK, width=2)

    out = ROOT / "assets" / "og-cover.jpg"
    card.save(out, "JPEG", quality=86, optimize=True, progressive=True)
    print(f"wrote {out.relative_to(ROOT)} {card.size} {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
