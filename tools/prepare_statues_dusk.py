"""Convert the generated dusk-statues PNG into a site-spec JPEG.

Site image spec (NOTES.md): cap 1600px, JPEG q82, progressive.

Run: python3 tools/prepare_statues_dusk.py <source.png>
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "assets", "statues-dusk.jpg")

src = sys.argv[1]
img = Image.open(src).convert("RGB")
img.thumbnail((1600, 1600), Image.LANCZOS)
img.save(TARGET, "JPEG", quality=82, progressive=True, optimize=True)

out = Image.open(TARGET)
assert out.format == "JPEG", f"unexpected format: {out.format}"
assert max(out.size) <= 1600, f"too large: {out.size}"
print(f"OK {os.path.basename(TARGET)}: {out.size[0]}x{out.size[1]}, {os.path.getsize(TARGET)} bytes")
