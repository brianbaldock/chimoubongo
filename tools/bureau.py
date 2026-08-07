"""Split the #bureau attraction register around one full-bleed photo band.

The original single .rows.register was 4540px at 1280px and carried all five
entries uninterrupted. This intentionally makes two register containers so the
band remains a full-width sibling of the constrained .wrap. The second register
starts its CSS counter at 3; see assets/site.css for the continuation rule.

Run once from the repo root: python3 tools/bureau.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ("index.html", "en.html")
PHOTOS = ("mosquito.jpg", "statues.jpg", "board.jpg", "cairn.jpg", "bus.jpg")

BAND = {
    "index.html": {
        "alt": "Alphonse-Réal Bougie à la lisière du Bosquet Debout",
        "cap": "Alphonse-Réal regarde les monuments sans jamais confirmer s'il les a vus.",
    },
    "en.html": {
        "alt": "Alphonse-Réal Bougie at the edge of the Standing Grove",
        "cap": "Alphonse-Réal watches the monuments without ever confirming that he has seen them.",
    },
}


def split_bureau(path):
    text = open(path, encoding="utf-8").read()
    section_start = text.index('<section id="bureau"')
    section_end = text.index("</section>", section_start) + len("</section>")
    section = text[section_start:section_end]

    # A completed run is intentionally idempotent: assert its exact shape and
    # leave it alone rather than attempting a second structural rewrite.
    if section.count('<div class="rows register') == 2:
        assert section.count('<div class="rows register continued rv">') == 1, f"{path}: invalid continuation"
        assert section.count('<div class="row">') == 5, f"{path}: completed register lost a row"
        assert section.count('<div class="band rv">') == 1, f"{path}: completed bureau band count"
        assert not text.startswith('>', section_end), f"{path}: malformed bureau section close"
        return text

    assert section.count('<div class="rows register rv">') == 1, f"{path}: expected one original register"
    assert section.count('<div class="row">') == 5, f"{path}: expected five register rows"
    assert 'class="band' not in section, f"{path}: bureau already has a band"
    assert section.count('assets/bougie.jpg') == 0, f"{path}: band image already in bureau"
    for photo in PHOTOS:
        assert section.count(f'assets/{photo}') == 1, f"{path}: {photo} count changed before edit"

    register_open = '  <div class="rows register rv">\n'
    register_start = section.index(register_open)
    rows_start = register_start + len(register_open)
    rows_close = section.index('</div>\n</div>\n</section>', rows_start)
    rows_html = section[rows_start:rows_close]
    # The first source row begins at column zero; the remaining four have two
    # spaces. Match only those two deliberate outer-row forms, not inner divs.
    starts = [m.start() for m in re.finditer(r'^(?:  )?<div class="row">$', rows_html, re.M)]
    assert len(starts) == 5, f"{path}: could not locate five whole rows"
    rows = [rows_html[start: starts[i + 1] if i + 1 < len(starts) else len(rows_html)] for i, start in enumerate(starts)]
    assert all(row.count('<div class="row">') == 1 for row in rows), f"{path}: row extraction failed"

    before = section[:register_start]
    after = section[rows_close + len('</div>\n</div>\n</section>'):]
    band = BAND[os.path.basename(path)]
    rebuilt = (
        before
        + register_open
        + ''.join(rows[:3])
        + '''</div>
</div>

<div class="band rv">
  <img src="assets/bougie.jpg" alt="{alt}" loading="lazy">
  <div class="cap"><div class="in"><p>{cap}</p></div></div>
</div>

<div class="wrap">
  <div class="rows register continued rv">
'''.format(**band)
        + ''.join(rows[3:])
        + '</div>\n</div>\n</section>'
        + after
    )
    output = text[:section_start] + rebuilt + text[section_end:]

    # Explicit loss/duplication and structural checks. The English page lost
    # entries to a greedy edit once; no whole-page regex replacement is used.
    changed = output[section_start:output.index("</section>", section_start) + len("</section>")]
    assert changed.count('<div class="rows register') == 2, f"{path}: expected two register chunks"
    assert changed.count('<div class="rows register continued rv">') == 1, f"{path}: continuation missing"
    assert changed.count('<div class="row">') == 5, f"{path}: row count changed"
    assert changed.count('<div class="band rv">') == 1, f"{path}: band count wrong"
    assert changed.count('assets/bougie.jpg') == 1, f"{path}: band image count wrong"
    for photo in PHOTOS:
        assert changed.count(f'assets/{photo}') == 1, f"{path}: {photo} lost or duplicated"
    for row in rows:
        heading = re.search(r'<h3>(.*?)</h3>', row, re.S).group(1)
        assert heading in changed, f"{path}: lost entry {heading!r}"
        # Every original row's substantive first paragraph survives verbatim.
        first_p = re.search(r'<p(?: class="[^"]+")?>(.*?)</p>', row, re.S).group(1)
        assert first_p in changed, f"{path}: lost body copy for {heading!r}"
    assert output.count('<section') == output.count('</section>'), f"{path}: section balance"
    assert output.count('<div') == output.count('</div>'), f"{path}: div balance"
    assert output.count('id="bureau"') == 1, f"{path}: bureau id count"
    return output


for name in PAGES:
    path = os.path.join(ROOT, name)
    rendered = split_bureau(path)
    open(path, "w", encoding="utf-8").write(rendered)
    print(f"OK {name}")
