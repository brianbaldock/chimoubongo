"""Verify the SEO layer on every generated page.

Fails closed. Written after the graph-engineering-course lesson that a gate
which parses nothing still prints success: every check here asserts a non-zero
count of things actually inspected, so a regex that stops matching is a
failure rather than a silent pass.

Run: python3 tools/verify_seo.py
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://chimoubongo.com/"

PAGES = {
    "index.html": "fr", "en.html": "en",
    "village.html": "fr", "en-village.html": "en",
    "visiter.html": "fr", "en-visit.html": "en",
    "attractions.html": "fr", "en-attractions.html": "en",
    "hangar.html": "fr", "en-shop.html": "en",
}

errors: list[str] = []
checked = {"pages": 0, "jsonld": 0, "locs": 0, "meta": 0}


def err(msg: str) -> None:
    errors.append(msg)


def meta(html: str, attr: str, value: str) -> str | None:
    m = re.search(
        rf'<meta\s+{attr}="{re.escape(value)}"\s+content="([^"]*)"\s*/?>', html)
    return m.group(1) if m else None


def check_page(name: str, lang: str) -> None:
    html = (ROOT / name).read_text(encoding="utf-8")
    checked["pages"] += 1
    canonical = SITE + ("" if name == "index.html" else name)

    # canonical + robots
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if not m:
        err(f"{name}: no canonical")
    elif m.group(1) != canonical:
        err(f"{name}: canonical {m.group(1)} != {canonical}")

    # NOTE: must not use a bare "index" substring test here -- "noindex"
    # contains "index", which made this check fail open. Match word-boundaried
    # tokens and reject the negative directives explicitly.
    rm = re.search(r'<meta name="robots" content="([^"]*)"', html)
    if not rm:
        err(f"{name}: missing robots meta")
    else:
        directives = {d.strip().lower() for d in rm.group(1).split(",")}
        if "noindex" in directives or "none" in directives:
            err(f"{name}: robots meta blocks indexing: {rm.group(1)}")
        elif "index" not in directives:
            err(f"{name}: robots meta does not declare index: {rm.group(1)}")
        if "nofollow" in directives:
            err(f"{name}: robots meta is nofollow: {rm.group(1)}")

    # description must exist and be a usable length
    desc = meta(html, "name", "description")
    if not desc:
        err(f"{name}: no meta description")
    elif not (50 <= len(desc) <= 200):
        err(f"{name}: description length {len(desc)} outside 50-200")
    else:
        checked["meta"] += 1

    # social tags, absolute image URLs only
    for attr, key in (("property", "og:title"), ("property", "og:description"),
                      ("property", "og:url"), ("property", "og:image"),
                      ("property", "og:type"), ("name", "twitter:card"),
                      ("name", "twitter:image")):
        v = meta(html, attr, key)
        if not v:
            err(f"{name}: missing {key}")
        elif key.endswith("image") and not v.startswith("https://"):
            err(f"{name}: {key} not absolute: {v}")
    ogurl = meta(html, "property", "og:url")
    if ogurl and ogurl != canonical:
        err(f"{name}: og:url {ogurl} != canonical")

    # hreflang must be reciprocal and include x-default
    tags = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html)
    codes = {c for c, _ in tags}
    if not {"fr-CA", "en-CA", "x-default"} <= codes:
        err(f"{name}: hreflang set incomplete: {sorted(codes)}")
    for _c, href in tags:
        if not href.startswith(SITE):
            err(f"{name}: hreflang href not absolute: {href}")

    # og:image must point at a file that exists on disk
    ogimg = meta(html, "property", "og:image")
    if ogimg:
        rel = ogimg[len(SITE):]
        if not (ROOT / rel).is_file():
            err(f"{name}: og:image missing on disk: {rel}")
        elif (ROOT / rel).stat().st_size == 0:
            err(f"{name}: og:image is zero bytes: {rel}")
        else:
            # A social card must actually be near 1.91:1 and under 1MB. A square
            # logo technically "exists on disk" and still previews badly, which
            # is the exact defect this check exists to catch.
            size = (ROOT / rel).stat().st_size
            if size > 1_000_000:
                err(f"{name}: og:image too large for a social card: {rel} "
                    f"({size} bytes)")
            try:
                from PIL import Image
                with Image.open(ROOT / rel) as im:
                    w, h = im.size
                if not (600 <= w <= 2400 and abs((w / h) - 1.91) <= 0.20):
                    err(f"{name}: og:image is not a ~1.91:1 social card: "
                        f"{rel} ({w}x{h})")
            except ImportError:
                # fail closed: an unavailable check is not a passing check
                err(f"{name}: cannot verify og:image dimensions (Pillow missing)")
        # declared dimensions, when present, must match the real file
        for prop, want in (("og:image:width", "1200"), ("og:image:height", "630")):
            got = meta(html, "property", prop)
            if got is not None and got != want:
                err(f"{name}: {prop} is {got}, expected {want}")

    # twitter:image must match og:image; a stale one previews the wrong art
    twimg = meta(html, "name", "twitter:image")
    if twimg != ogimg:
        err(f"{name}: twitter:image ({twimg}) != og:image ({ogimg})")

    # JSON-LD must parse and describe THIS page
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    opens = html.count('type="application/ld+json"')
    if opens != len(blocks):
        err(f"{name}: {opens} ld+json tags but {len(blocks)} parsed bodies")
    if not blocks:
        err(f"{name}: no JSON-LD")
        return
    for raw in blocks:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            err(f"{name}: JSON-LD invalid: {e}")
            continue
        checked["jsonld"] += 1
        types = {n.get("@type") for n in data.get("@graph", [])}
        if not {"WebSite", "WebPage", "BreadcrumbList"} <= types:
            err(f"{name}: JSON-LD types incomplete: {sorted(types)}")
        page_nodes = [n for n in data["@graph"] if n.get("@type") == "WebPage"]
        if not page_nodes:
            err(f"{name}: no WebPage node")
        else:
            if page_nodes[0].get("url") != canonical:
                err(f"{name}: WebPage url != canonical")
            if page_nodes[0].get("inLanguage") != ("fr-CA" if lang == "fr" else "en-CA"):
                err(f"{name}: WebPage inLanguage wrong")
        # never assert a real-world place for an invented town
        if types & {"LocalBusiness", "Place", "TouristAttraction", "Organization"}:
            err(f"{name}: JSON-LD asserts a real-world entity for a fictional town")


def check_sitemap() -> None:
    p = ROOT / "sitemap.xml"
    if not p.is_file():
        err("sitemap.xml missing")
        return
    try:
        root = ET.fromstring(p.read_text(encoding="utf-8"))
    except ET.ParseError as e:
        err(f"sitemap.xml not well-formed: {e}")
        return
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = [e.text for e in root.iter(f"{ns}loc")]
    if len(locs) != len(PAGES):
        err(f"sitemap lists {len(locs)} urls, expected {len(PAGES)}")
    for loc in locs:
        checked["locs"] += 1
        if not loc or not loc.startswith(SITE):
            err(f"sitemap loc not on canonical host: {loc}")
            continue
        rel = loc[len(SITE):] or "index.html"
        if not (ROOT / rel).is_file():
            err(f"sitemap points at nonexistent file: {rel}")
    if checked["locs"] == 0:
        err("sitemap parsed zero <loc> entries")


def check_robots() -> None:
    p = ROOT / "robots.txt"
    if not p.is_file():
        err("robots.txt missing")
        return
    txt = p.read_text(encoding="utf-8")
    if "User-agent: *" not in txt:
        err("robots.txt has no User-agent")
    if f"Sitemap: {SITE}sitemap.xml" not in txt:
        err("robots.txt does not advertise the sitemap")
    if re.search(r"^Disallow:\s*/\s*$", txt, re.M):
        err("robots.txt blocks the whole site")


def main() -> int:
    for name, lang in PAGES.items():
        if not (ROOT / name).is_file():
            err(f"{name}: not built")
            continue
        check_page(name, lang)
    check_sitemap()
    check_robots()

    # fail closed: a run that inspected nothing is not a pass
    if checked["pages"] != len(PAGES):
        err(f"only inspected {checked['pages']}/{len(PAGES)} pages")
    if checked["jsonld"] < len(PAGES):
        err(f"only parsed {checked['jsonld']} JSON-LD blocks")
    if checked["meta"] < len(PAGES):
        err(f"only validated {checked['meta']} descriptions")

    if errors:
        for e in errors:
            print(f"FAIL {e}")
        print(f"\nRESULT: {len(errors)} problem(s)")
        return 1
    print(f"pages {checked['pages']}  json-ld {checked['jsonld']}  "
          f"sitemap urls {checked['locs']}  descriptions {checked['meta']}")
    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
