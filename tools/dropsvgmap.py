"""Remove the hand-drawn SVG map from #map on both pages.

Brian's call, 2026-08-07: the site now ships real baked OpenStreetMap plates
(assets/map-region.jpg and assets/map-detail.jpg) directly above the SVG,
showing the same geography from real survey data. The illustration became
redundant the moment those landed, and having both invites the reader to
compare a decorative drawing against a real map in the same section.

The legend copy underneath it is good writing and carries a real joke about
GPS disagreement, so it is preserved and re-parented into the .note block
where the rest of the section's asides already live.

This supersedes the old NOTES.md rule "The hand-drawn SVG map in #map is
deliberate line art. Do not photo-swap it."

Run: python3 tools/dropsvgmap.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for name in ("index.html", "en.html"):
    p = os.path.join(ROOT, name)
    s = open(p, encoding="utf-8").read()

    assert s.count("<svg") == 1, f"{name}: expected exactly 1 svg, got {s.count('<svg')}"

    start = s.index('<div class="map">')
    end = s.index("</section>", start)
    block = s[start:end]

    # Keep the legend prose, drop the drawing.
    legend = re.search(r'<div class="legend">\s*(.*?)\s*</div>', block, re.S)
    assert legend, f"{name}: legend not found"
    legend_html = legend.group(1).strip()
    assert "GPS" in legend_html, f"{name}: legend text looks wrong"

    # Re-parent the legend as a final paragraph of the existing .note block.
    note_close = s.rindex("</div>", 0, start)
    s = s[:note_close] + f'  <p class="gpsnote">{legend_html}</p>\n  ' + s[note_close:]

    # Recompute offsets after the insert, then excise the whole .map block.
    # The slice runs to </section>, which swallows BOTH the .map closing div
    # and the enclosing .wrap closing div. Put the wrap's closer back.
    start = s.index('<div class="map">')
    end = s.index("</section>", start)
    s = s[:start] + "</div>\n" + s[end:]

    # Assertions.
    assert "<svg" not in s, f"{name}: svg survived"
    assert "</svg>" not in s, f"{name}: svg close survived"
    assert 'class="legend"' not in s, f"{name}: legend div survived"
    assert "GPS" in s, f"{name}: legend prose lost"
    assert s.count("map-region.jpg") == 1, f"{name}: region plate lost"
    assert s.count("map-detail.jpg") == 1, f"{name}: detail plate lost"
    assert s.count("<section") == s.count("</section>"), f"{name}: section balance"
    assert s.count("<div") == s.count("</div>"), f"{name}: div balance"

    open(p, "w", encoding="utf-8").write(s)
    print(f"OK {name}")
