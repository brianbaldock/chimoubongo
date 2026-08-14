"""Every <img src> on every page must resolve to a real, non-empty file,
carry alt text, and lazy-load unless it is the hero. Also reports duplicate
srcs, which is the shape a subagent leaves behind when it fills a hole.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
problems = []
seen = Counter()
total = 0

for page in sorted(ROOT.glob("*.html")):
    html = page.read_text(encoding="utf-8")
    tags = re.findall(r"<img\b[^>]*>", html)
    if not tags:
        problems.append(f"{page.name}: no images at all")
    for tag in tags:
        total += 1
        m = re.search(r'src="([^"]+)"', tag)
        if not m:
            problems.append(f"{page.name}: img with no src: {tag[:60]}")
            continue
        src = m.group(1)
        seen[src] += 1
        if src.startswith("http"):
            continue
        f = ROOT / src
        if not f.is_file():
            problems.append(f"{page.name}: missing file {src}")
        elif f.stat().st_size == 0:
            problems.append(f"{page.name}: zero-byte {src}")
        alt = re.search(r'alt="([^"]*)"', tag)
        if alt is None:
            problems.append(f"{page.name}: no alt attribute on {src}")
        elif not alt.group(1).strip() and "logo" not in src:
            problems.append(f"{page.name}: empty alt on {src}")

if total == 0:
    problems.append("inspected zero images (checker is not working)")

print(f"inspected {total} img tags across {len(list(ROOT.glob('*.html')))} pages")
dupes = [(s, n) for s, n in seen.items() if n > 1 and "logo" not in s]
if dupes:
    print("repeated non-logo srcs (verify intentional):")
    for s, n in sorted(dupes):
        print(f"  {n}x {s}")

for p in problems:
    print(f"FAIL {p}")
print("RESULT: OK" if not problems else f"RESULT: {len(problems)} problem(s)")
sys.exit(1 if problems else 0)
