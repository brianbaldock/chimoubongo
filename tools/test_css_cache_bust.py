"""Prevent stale CSS after a GitHub Pages deploy.

The stylesheet query value is the first 12 characters of its SHA-256, so a CSS
edit cannot ship while browsers are still allowed to reuse the previous file.
Run: python3 tools/test_css_cache_bust.py
"""
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "assets" / "site.css").read_bytes()
version = hashlib.sha256(css).hexdigest()[:12]
expected = f"assets/site.css?v={version}"

for page in ("index.html", "en.html"):
    text = (ROOT / page).read_text(encoding="utf-8")
    match = re.search(r'<link rel="stylesheet" href="([^"]+)">', text)
    assert match, f"{page}: stylesheet link missing"
    assert match.group(1) == expected, (
        f"{page}: stale stylesheet version {match.group(1)!r}; expected {expected!r}"
    )

print(f"OK both pages cache-bust CSS with {version}")
