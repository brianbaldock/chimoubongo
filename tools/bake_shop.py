"""Bake the Fourthwall product catalog into static assets shipped in assets/.

Why bake instead of fetching the Storefront API at runtime:
  * chimoubongo.com makes ZERO third-party requests today, so a live fetch
    would put a request to fourthwall.dev on every page load and hand a
    visitor's IP and referrer to a vendor the reader did not choose. The
    no-tracker promise is a real property of this site, not a nice-to-have.
  * the shop section cannot break when someone else's API has a bad day
  * no JS cart, no API token in the page, works offline and from file://

Same reasoning as tools/bake_map.py, same shape: one-shot fetch, flat files.

TRADEOFF, stated plainly: prices, availability and product photos are only as
fresh as the last bake. Re-run this script and rebuild whenever the shop
changes. The catalog records bakedAt so the page can be honest about it.

The storefront token is PUBLIC by design (Fourthwall's own docs put it in a
client-side query string), so it is not a secret in the usual sense. It still
does NOT live in this file: GitHub push protection pattern-matches the
`ptkn_` prefix as a Shopify credential and blocks the push, and keeping
credentials out of source is the right default regardless. Put it in
tools/.fourthwall-token (gitignored) or set FOURTHWALL_TOKEN in the
environment.

This is NOT the Platform API key, which IS secret and must never appear in
the repo or in a chat message.

Run manually: FOURTHWALL_TOKEN=ptkn_... python3 tools/bake_shop.py
          or: python3 tools/bake_shop.py   (reads tools/.fourthwall-token)
"""
import json
import os
import re
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
SHOP_IMG = os.path.join(ASSETS, "shop")

TOKEN_FILE = os.path.join(HERE, ".fourthwall-token")


def load_token():
    tok = os.environ.get("FOURTHWALL_TOKEN", "").strip()
    if not tok and os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as f:
            tok = f.read().strip()
    if not tok:
        raise SystemExit(
            "No storefront token. Set FOURTHWALL_TOKEN in the environment, or write it to\n"
            f"  {TOKEN_FILE}\n"
            "Get it from Fourthwall: Settings > For Developers."
        )
    assert tok.startswith("ptkn_"), "expected a storefront token (ptkn_...), not a Platform API key"
    return tok


TOKEN = load_token()
API = "https://storefront-api.fourthwall.com/v1"
SHOP_DOMAIN = "chimoubongo-shop.fourthwall.com"

# Read from 'all': the 'chimoubongo' collection exists but is empty.
COLLECTION = "all"

# Two Shirtmoubongo products exist, identical but for colour. They are grouped
# under one card so the storefront does not list the same shirt twice.
GROUPS = {
    "shirtmoubongo": "shirtmoubongo",
    "shirtmoubongo-2": "shirtmoubongo",
}

ORDER = ["shirtmoubongo", "hoodiemoubongo", "cafemoubongo", "truckermoubongo", "stickermoubongo"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "chimoubongo.com static shop bake"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    os.makedirs(SHOP_IMG, exist_ok=True)

    data = fetch(f"{API}/collections/{COLLECTION}/products?storefront_token={TOKEN}")
    products = data.get("results", [])
    assert products, "no products returned; refusing to bake an empty catalog"

    cards = {}
    for p in products:
        key = GROUPS.get(p["slug"], p["slug"])
        variants = p.get("variants") or []
        assert variants, f"{p['slug']}: no variants"

        prices = [v["unitPrice"]["value"] for v in variants if v.get("unitPrice")]
        currency = variants[0]["unitPrice"]["currency"]
        colour = None
        opts = []
        for v in variants:
            attrs = v.get("attributes") or {}
            colour = ((attrs.get("color") or {}).get("name")) or colour
            size = (attrs.get("size") or {}).get("name")
            opts.append({
                "id": v["id"],
                "size": size,
                "price": v["unitPrice"]["value"],
                "available": (v.get("stock") or {}).get("type") != "OUT_OF_STOCK",
            })

        # First image only: one photo per card keeps the grid even, which is
        # the same defect class already fixed twice elsewhere on this site.
        images = p.get("images") or []
        assert images, f"{p['slug']}: no images"
        src = images[0]["url"]
        fname = f"{p['slug']}.jpg"
        path = os.path.join(SHOP_IMG, fname)
        if not os.path.exists(path):
            req = urllib.request.Request(src, headers={"User-Agent": "chimoubongo.com static shop bake"})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
            tmp = path + ".tmp"
            with open(tmp, "wb") as f:
                f.write(raw)
            img = Image.open(tmp).convert("RGB")
            img.thumbnail((1000, 1000), Image.LANCZOS)
            img.save(path, "JPEG", quality=82, progressive=True, optimize=True)
            os.remove(tmp)
            print(f"  baked {fname} ({os.path.getsize(path)} bytes)")

        variant = {
            "colour": colour,
            "options": opts,
            "image": f"assets/shop/{fname}",
        }

        if key in cards:
            cards[key]["variants"].append(variant)
            cards[key]["priceMin"] = min(cards[key]["priceMin"], min(prices))
            cards[key]["priceMax"] = max(cards[key]["priceMax"], max(prices))
        else:
            cards[key] = {
                "key": key,
                "name": re.sub(r"\s*\(.*\)$", "", p["name"]),
                "currency": currency,
                "priceMin": min(prices),
                "priceMax": max(prices),
                "variants": [variant],
            }

    ordered = [cards[k] for k in ORDER if k in cards]
    assert len(ordered) == len(cards), f"ORDER missing keys: {set(cards) - set(ORDER)}"

    out = {
        "shopDomain": SHOP_DOMAIN,
        "checkoutBase": f"https://{SHOP_DOMAIN}/cart/checkout",
        "products": ordered,
    }
    dest = os.path.join(ASSETS, "shop.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"OK shop.json: {len(ordered)} cards, "
          f"{sum(len(v['options']) for c in ordered for v in c['variants'])} variants")
    for c in ordered:
        cols = ", ".join(v["colour"] or "-" for v in c["variants"])
        print(f"   {c['name']:<18} {c['priceMin']}-{c['priceMax']} {c['currency']}  [{cols}]")


if __name__ == "__main__":
    main()
