"""Remove the duplicated soup.jpg card figure from #doing on both pages.

Measured problem: #doing is a six-card grid where three cards measured 503px
and three measured 280px, a 223px raggedness, because exactly one card of the
six carried a photo. That photo was assets/soup.jpg, which already appears as
the full-bleed band at the bottom of #visit, so the page showed the same
image twice and paid for the inconsistency in the grid.

Dropping the figure fixes both at once and removes a redundant image request.
The card keeps its copy; Thursday Soup still gets its full-bleed moment later.

Run: python3 tools/doingcard.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for name in ("index.html", "en.html"):
    p = os.path.join(ROOT, name)
    s = open(p, encoding="utf-8").read()

    before_soup = s.count("assets/soup.jpg")
    assert before_soup == 2, f"{name}: expected 2 soup.jpg refs, got {before_soup}"

    doing_start = s.index('<section id="doing"')
    doing_end = s.index('<section id="bureau"')
    doing = s[doing_start:doing_end]

    fig = re.search(r'\s*<figure class="rv"><img src="assets/soup\.jpg"[^>]*></figure>', doing)
    assert fig, f"{name}: soup figure not found in #doing"

    new_doing = doing.replace(fig.group(0), "")
    s = s[:doing_start] + new_doing + s[doing_end:]

    # Assertions: only the #doing copy went, the band survives, nothing else moved.
    assert s.count("assets/soup.jpg") == 1, f"{name}: soup.jpg should remain once"
    assert 'class="band flush"' in s, f"{name}: visit band lost"
    assert s.count('<div class="card">') == 16, f"{name}: card count changed"
    assert s.count("<section") == s.count("</section>"), f"{name}: section balance"

    open(p, "w", encoding="utf-8").write(s)
    print(f"OK {name}")
