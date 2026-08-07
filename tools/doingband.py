"""Add one unique full-bleed creek photo to #doing on both pages.

A band keeps all six text cards in the same plain-card grid. The photograph is
not reused elsewhere: putting an image on only one card previously created a
223px height spread, and the old soup image was already the #visit band.

Run: python3 tools/doingband.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COPY = {
    "index.html": {
        "alt": "La crique dans le vieux pin blanc, avec le petit pont de bois",
        "caption": "La crique est frette même quand le village dit que non. Le pont tient, mais il aime pas être pressé.",
    },
    "en.html": {
        "alt": "The creek in the old white pines, with its small wooden footbridge",
        "caption": "The creek is cold even when the town says it is not. The bridge holds, but it does not like being hurried.",
    },
}

for name, copy in COPY.items():
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    start = text.index('<section id="doing"')
    end = text.index('<section id="bureau"', start)
    doing = text[start:end]

    # This script is deliberately one-shot: preserve the existing six-card
    # grid and insert a direct child of #doing after its constrained .wrap.
    assert doing.count('<div class="card">') == 6, f"{name}: expected six #doing cards"
    assert 'assets/creek.jpg' not in doing, f"{name}: creek band already present"
    assert '<img' not in doing, f"{name}: #doing must start without a photo"
    assert doing.endswith('</div>\n</section>\n\n'), f"{name}: unexpected #doing ending"

    band = f'''\n<div class="band rv">
  <img src="assets/creek.jpg" alt="{copy["alt"]}" loading="lazy">
  <div class="cap"><div class="in"><p>{copy["caption"]}</p></div></div>
</div>
'''
    updated_doing = doing[:-len('</div>\n</section>\n\n')] + '</div>\n' + band + '</section>\n\n'
    updated = text[:start] + updated_doing + text[end:]

    # Assertions: both languages get exactly one unique band, and only the
    # bounded #doing block changes shape.
    changed = updated[start:updated.index('<section id="bureau"', start)]
    assert changed.count('assets/creek.jpg') == 1, f"{name}: creek image count"
    assert changed.count('<div class="card">') == 6, f"{name}: card count changed"
    assert changed.count('<div class="band rv">') == 1, f"{name}: band count"
    assert '<div class="wrap">' in changed and '</div>\n\n<div class="band rv">' in changed, f"{name}: band placement"
    assert updated.count('<section') == updated.count('</section>'), f"{name}: section balance"
    assert updated.count('<div') == updated.count('</div>'), f"{name}: div balance"

    path.write_text(updated, encoding="utf-8")
    print(f"OK {name}")
