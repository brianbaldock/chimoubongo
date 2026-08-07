"""Regression checks for the #doing full-bleed creek band.

Run: python3 tools/test_doingband.py
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

for name in ("index.html", "en.html"):
    text = (ROOT / name).read_text(encoding="utf-8")
    start = text.index('<section id="doing"')
    end = text.index('<section id="bureau"', start)
    doing = text[start:end]

    assert doing.count('assets/creek.jpg') == 1, f"{name}: #doing needs one unique creek photo"
    assert doing.count('<div class="card">') == 6, f"{name}: expected six #doing cards"
    assert doing.count('<div class="band rv">') == 1, f"{name}: #doing needs one full-bleed band"
    assert re.search(
        r'</div>\s*<div class="band rv">\s*<img src="assets/creek\.jpg"',
        doing,
    ), f"{name}: creek band must be a sibling of the constrained .wrap"
    assert text.count('<section') == text.count('</section>'), f"{name}: section balance"
    assert text.count('<div') == text.count('</div>'), f"{name}: div balance"

image = ROOT / "assets" / "creek.jpg"
assert image.is_file(), "assets/creek.jpg is missing"
assert image.stat().st_size > 0, "assets/creek.jpg is empty"

print("OK doing full-bleed creek band")
