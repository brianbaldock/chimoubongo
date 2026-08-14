"""One-shot: lift the baked .goods block out of the pre-split pages into the
new content fragments, so the Fourthwall variant UUIDs are copied from a
verified source instead of retyped by hand.

Run once against a checkout that still has the single-page index.html/en.html.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

HEAD = {
    "fr": """<section id="shop">
<div class="wrap">
  <div class="sechead rv">
    <p class="eyebrow">Le hangar à souvenirs</p>
    <h2>Des affaires à rapporter</h2>
    <p class="dek">Le Bureau vend cinq affaires. C'est pas beaucoup, mais c'est ce qu'y a. Ginette trouvait que vendre des souvenirs d'une place qui existe pas officiellement, c'était la chose la plus honnête que le village pouvait faire.</p>
  </div>
""",
    "en": """<section id="shop">
<div class="wrap">
  <div class="sechead rv">
    <p class="eyebrow">The souvenir shed</p>
    <h2>Things to take home</h2>
    <p class="dek">The Bureau sells five things. It is not much, but it is what there is. Ginette felt that selling souvenirs of a place that does not officially exist was the most honest thing the town could do.</p>
  </div>
""",
}

TAIL = {
    "fr": """
  <p class="shopnote">Les prix sont en dollars américains parce que l'imprimeur est aux États. Le paiement pis l'envoi se font chez Fourthwall, pas ici. On garde rien sur toi tant que tu cliques pas. <a href="https://chimoubongo-shop.fourthwall.com/" rel="noopener">Voir le hangar au complet &rarr;</a></p>
</div>
</section>
""",
    "en": """
  <p class="shopnote">Prices are in US dollars because the printer is in the States. Payment and shipping happen at Fourthwall, not here. Nothing about you is kept until you click. <a href="https://chimoubongo-shop.fourthwall.com/" rel="noopener">See the whole shed &rarr;</a></p>
</div>
</section>
""",
}


def main() -> int:
    for lang, page in (("fr", "index.html"), ("en", "en.html")):
        text = (ROOT / page).read_text(encoding="utf-8")
        match = re.search(r'(<div class="goods rv">.*?\n  </div>)\n', text, re.S)
        if not match:
            print(f"FAIL {page}: no .goods block found (already split?)")
            return 1
        goods = match.group(1)
        assert goods.count('<div class="good">') == 5, f"{page}: expected 5 products"
        out = ROOT / "content" / lang / "shop.html"
        out.write_text(HEAD[lang] + "\n" + goods + "\n" + TAIL[lang], encoding="utf-8")
        print(f"OK {out.relative_to(ROOT)}: 5 products, "
              f"{len(re.findall(r'<option', goods))} variants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
