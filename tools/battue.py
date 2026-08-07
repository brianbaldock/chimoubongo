"""Restructure #battue on both pages.

Measured problems this fixes:
  1. #battue was a single 2864px dark slab: one 340px photo, then 2524px of
     unbroken body copy reversed out on ink. Nothing in the upper half runs
     more than ~800px without a full-bleed break.
  2. It was the only section on the page with no .sechead. Upper half has 5,
     lower half had 3 across 4 sections, and the one big feature had none.
  3. Zero full-bleed breakers between y=8378 and y=21462, i.e. 13,000px.

New structure, which mirrors how #story is built:
     sechead -> narrative on paper -> pull quote -> full-bleed band
     -> dark poster reduced to the practical matter (schedule + rules)

Run: python3 tools/battue.py
"""
import re
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(lang):
    if lang == "fr":
        return dict(
            eyebrow="Le grand événement",
            h2="La Battue de patates",
            lede="Le troisième samedi de septembre, le village se réunit dans le "
                 "champ en arrière du bureau de poste pour tenir des patates "
                 "responsables de quelque chose qu'elles ont pas fait. Ça dure "
                 "depuis 1976 pis c'est pris au sérieux.",
            cap="Le champ en arrière du bureau de poste, troisième samedi de "
                "septembre. Les bâtons sont fournis.",
            kicker="L'horaire de la journée",
            h3="Comment ça se passe",
            when="Troisième samedi de septembre · Le champ en arrière du bureau "
                 "de poste · Bâtons fournis",
        )
    return dict(
        eyebrow="The main event",
        h2="The Potato Bash",
        lede="On the third Saturday in September the town gathers in the field "
             "behind the post office to hold a quantity of potatoes responsible "
             "for something they did not do. It has run since 1976 and it is "
             "taken seriously.",
        cap="The field behind the post office, third Saturday in September. "
            "Bats are provided.",
        kicker="The order of the day",
        h3="How it runs",
        when="Third Saturday in September · The field behind the post office · "
             "Bats provided",
    )


def restructure(path, lang):
    s = open(path, encoding="utf-8").read()
    t = build(lang)

    start = s.index('<section id="battue"')
    end = s.index('<div class="cards rv">', start)
    block = s[start:end]

    # Pull the pieces we are keeping out of the old poster body.
    img = re.search(r'<img src="assets/potato\.jpg"[^>]*>', block).group(0)
    alt = re.search(r'alt="([^"]*)"', img).group(1)

    body = block[block.index('<div class="body">'):]
    paras = re.findall(r'^\s*<p>.*?</p>\s*$', body, re.M | re.S)
    assert len(paras) == 4, f"{path}: expected 4 narrative paragraphs, got {len(paras)}"
    pull = re.search(r'<div class="pull rv">.*?</div>', body, re.S).group(0)
    sched = re.search(r'<ul class="sched">.*?</ul>', body, re.S).group(0)
    note = re.search(r'<p class="lede-note">.*?</p>', body, re.S).group(0)

    narrative = "\n\n".join(p.strip() for p in paras)
    # The pull quote belongs after the second paragraph, where the sentence it
    # quotes is introduced. Split there instead of dumping it at the end.
    first_two = "\n\n".join(p.strip() for p in paras[:2])
    last_two = "\n\n".join(p.strip() for p in paras[2:])

    new = f'''<section id="battue" class="alt">
<div class="wrap">
  <div class="sechead rv">
    <p class="eyebrow">{t["eyebrow"]}</p>
    <h2>{t["h2"]}</h2>
    <p class="dek">{t["lede"]}</p>
  </div>

  {first_two}

  {pull}

  {last_two}
</div>

<div class="band rv">
  <img src="assets/potato.jpg" alt="{alt}" loading="lazy">
  <div class="cap"><div class="in"><p>{t["cap"]}</p></div></div>
</div>

<div class="wrap">
  <div class="poster feature rv">
    <div class="body">
    <p class="kicker">{t["kicker"]}</p>
    <h3>{t["h3"]}</h3>
    <p class="when">{t["when"]}</p>

    {sched}

    {note}
  </div>
  </div>

  '''

    s = s[:start] + new + s[end:]

    # Assertions: nothing lost, nothing duplicated.
    assert s.count('assets/potato.jpg') == 1, f"{path}: potato image count"
    assert s.count('class="sched"') == 1, f"{path}: schedule count"
    assert s.count('id="battue"') == 1, f"{path}: battue count"
    assert s.count('<section') == s.count('</section>'), f"{path}: section balance"
    for p in paras:
        core = p.strip()[3:60]
        assert core in s, f"{path}: lost paragraph {core!r}"
    assert 'class="poster feature rv"' in s, f"{path}: poster kept"
    return s


for name, lang in (("index.html", "fr"), ("en.html", "en")):
    p = os.path.join(ROOT, name)
    out = restructure(p, lang)
    open(p, "w", encoding="utf-8").write(out)
    print(f"OK {name}")
