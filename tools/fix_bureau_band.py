"""Replace the #bureau band photo: bougie.jpg -> statues-dusk.jpg.

The subagent that split the register chose assets/bougie.jpg for the new
full-bleed band. That is Alphonse-Réal's portrait from #alphonse, so the
founder's face became a decorative band mid-catalogue and the same photo
appeared twice on the page. Duplicating an image is the exact defect that
was removed from #doing earlier in this pass.

The register is a catalogue of roadside monuments, so the band should be a
monument at a different time of day, not a person. The new photograph is
generated with the same documentary prompt discipline as the rest of the
site's photography (see icon-prompts.txt), and it pays off a line already
in the copy: the mosquito entry says the statue is best seen at dusk when
its shadow reaches the gas station.

Run: python3 tools/fix_bureau_band.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SWAP = {
    "index.html": (
        '<img src="assets/bougie.jpg" alt="Alphonse-Réal Bougie à la lisière du Bosquet Debout" loading="lazy">',
        '<img src="assets/statues-dusk.jpg" alt="Le maringouin pis la mouche à chevreuil au crépuscule, l\'ombre rendue au poste d\'essence" loading="lazy">',
        "Alphonse-Réal regarde les monuments sans jamais confirmer s'il les a vus.",
        "Cinq heures et demie, fin août. L'ombre se rend au poste d'essence, pis le poste d'essence ferme de bonne heure exprès.",
    ),
    "en.html": (
        '<img src="assets/bougie.jpg" alt="Alphonse-Réal Bougie at the edge of the Standing Grove" loading="lazy">',
        '<img src="assets/statues-dusk.jpg" alt="The mosquito and the horsefly at dusk, the shadow reaching the gas station" loading="lazy">',
        "Alphonse-Réal watches the monuments without ever confirming that he has seen them.",
        "Half past five, late August. The shadow reaches the gas station, and the gas station closes early on purpose.",
    ),
}

for name, (old_img, new_img, old_cap, new_cap) in SWAP.items():
    p = os.path.join(ROOT, name)
    s = open(p, encoding="utf-8").read()

    # Idempotent: skip a file already swapped (index.html applied on a prior
    # run that then failed on en.html's caption wording).
    if "assets/statues-dusk.jpg" in s:
        assert s.count("assets/bougie.jpg") == 1, f"{name}: already swapped but bougie count wrong"
        print(f"SKIP {name} (already swapped)")
        continue

    assert s.count("assets/bougie.jpg") == 2, f"{name}: expected 2 bougie refs, got {s.count('assets/bougie.jpg')}"
    assert old_img in s, f"{name}: band img markup not found"
    assert old_cap in s, f"{name}: band caption not found"

    s = s.replace(old_img, new_img)
    s = s.replace(old_cap, new_cap)

    # Assertions: portrait back to single use, band still present and intact.
    assert s.count("assets/bougie.jpg") == 1, f"{name}: bougie should remain once (the #alphonse portrait)"
    assert s.count("assets/statues-dusk.jpg") == 1, f"{name}: new band photo count"
    assert 'alt="Alphonse-Réal Bougie, 89' in s or 'alt="Alphonse-Réal Bougie, 89' in s or "89" in s, f"{name}: portrait alt lost"
    assert s.count('<div class="band rv">') >= 1, f"{name}: band lost"
    assert s.count("<section") == s.count("</section>"), f"{name}: section balance"
    assert s.count("<div") == s.count("</div>"), f"{name}: div balance"

    open(p, "w", encoding="utf-8").write(s)
    print(f"OK {name}")
