"""Insert or rebuild the baked #shop section in both pages, plus nav links.

Reads assets/shop.json (written by tools/bake_shop.py) and emits static
markup: no fetch, no cart JS, no token in the page. Every buy control is a
plain <a> to Fourthwall's hosted checkout, which is the only third-party
contact and it happens only after a deliberate click.

Size choice is a real <select> inside a <form method="get">, so it works with
JavaScript off. The form GETs the Fourthwall checkout endpoint and the select
is named "products", whose value is the variant UUID. That is exactly the
shape /cart/checkout expects, so no script is needed to build the URL.

Copy is written in the town's register, not shop boilerplate. The shop is the
Bureau de tourisme's "hangar à souvenirs", which the #battue section already
refers to, so it is continuous with the fiction rather than bolted on.

Run: python3 tools/build_shop_section.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, "assets", "shop.json"), encoding="utf-8") as f:
    SHOP = json.load(f)

COPY = {
    "fr": {
        "eyebrow": "Le hangar à souvenirs",
        "h2": "Des affaires à rapporter",
        "lede": "Le Bureau vend cinq affaires. C'est pas beaucoup, mais c'est ce qu'y a. "
                "Ginette trouvait que vendre des souvenirs d'une place qui existe pas officiellement, "
                "c'était la chose la plus honnête que le village pouvait faire.",
        "note": "Les prix sont en dollars américains parce que l'imprimeur est aux États. "
                "Le paiement pis l'envoi se font chez Fourthwall, pas ici. "
                "On garde rien sur toi tant que tu cliques pas.",
        "size": "Grandeur",
        "buy": "Acheter",
        "from": "à partir de",
        "cta": "Voir le hangar au complet",
        "nav": "Le hangar",
        "foot": "Le hangar",
    },
    "en": {
        "eyebrow": "The souvenir shed",
        "h2": "Things to take home",
        "lede": "The Bureau sells five things. It is not much, but it is what there is. "
                "Ginette held that selling souvenirs of a place that does not officially exist "
                "was the most honest thing the town could do.",
        "note": "Prices are in US dollars because the printer is in the States. "
                "Payment and shipping happen at Fourthwall, not here. "
                "We keep nothing on you unless you click.",
        "size": "Size",
        "buy": "Buy",
        "from": "from",
        "cta": "See the whole shed",
        "nav": "The shed",
        "foot": "The shed",
    },
}


def money(v, cur):
    return f"${v:.2f}" if cur == "USD" else f"{v:.2f} {cur}"


def build(copy):
    base = SHOP["checkoutBase"]
    cards = []
    for p in SHOP["products"]:
        price = money(p["priceMin"], p["currency"])
        prefix = f'<span class="pfrom">{copy["from"]}</span> ' if p["priceMax"] != p["priceMin"] else ""
        v = p["variants"][0]

        opts = []
        for var in p["variants"]:
            for o in var["options"]:
                if not o["available"]:
                    continue
                label = o["size"] or ""
                if len(p["variants"]) > 1 and var["colour"]:
                    label = f"{label} · {var['colour']}" if label else var["colour"]
                opts.append(f'<option value="{o["id"]}:1">{label} — {money(o["price"], p["currency"])}</option>')

        cards.append(f'''    <div class="good">
      <figure><img src="{v["image"]}" alt="{p["name"]}" loading="lazy" width="900" height="1200"></figure>
      <div class="goodbody">
        <h4>{p["name"]}</h4>
        <p class="price">{prefix}{price}</p>
        <form class="pick" method="get" action="{base}">
          <input type="hidden" name="currency" value="{p["currency"]}">
          <label>
            <span>{copy["size"]}</span>
            <select name="products">
{chr(10).join("              " + o for o in opts)}
            </select>
          </label>
          <button type="submit">{copy["buy"]}</button>
        </form>
      </div>
    </div>''')

    return f'''<section id="shop">
<div class="wrap">
  <div class="sechead rv">
    <p class="eyebrow">{copy["eyebrow"]}</p>
    <h2>{copy["h2"]}</h2>
  </div>

  <p>{copy["lede"]}</p>

  <div class="goods rv">
{chr(10).join(cards)}
  </div>

  <p class="shopnote">{copy["note"]} <a href="https://{SHOP["shopDomain"]}/" rel="noopener">{copy["cta"]} &rarr;</a></p>
</div>
</section>

'''


def replace_shop_section(s, copy):
    """Rebuild the #shop section of a content fragment from the baked catalog.

    Since the 2026-08-14 multi-page split the shop is its own page, so this no
    longer inserts nav or footer links: tools/build_site.py owns all chrome.
    The fragment is the section and nothing else, which is why this replaces
    from '<section id="shop">' to end of string rather than to an anchor.
    """
    assert s.startswith('<section id="shop">'), "fragment must be the shop section"
    out = build(copy)

    assert out.count('<section id="shop">') == 1, "shop section count"
    assert out.count("<section") == out.count("</section>"), "section balance"
    assert out.count("<div") == out.count("</div>"), "div balance"
    assert out.count("<form") == out.count("</form>") == 5, "form count"
    assert out.count("<select") == out.count("</select>") == 5, "select count"
    assert "ptkn_" not in out, "storefront token must never reach the page"
    return out


if __name__ == "__main__":
    for name, copy in COPY.items():
        path = os.path.join(ROOT, "content", name, "shop.html")
        before = open(path, encoding="utf-8").read()
        after = replace_shop_section(before, copy)
        open(path, "w", encoding="utf-8").write(after)
        print(f"OK content/{name}/shop.html: rebuilt #shop "
              f"({'unchanged' if after == before else 'CHANGED, rerun tools/build_site.py'})")
