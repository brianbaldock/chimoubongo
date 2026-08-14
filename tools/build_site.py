"""Assemble every page of the site from shared chrome + per-page content.

Why a builder: the site went from two long single-page documents to ten pages
(five sections x two languages). Hand-maintaining the head, top bar, nav, the
merch banner and the footer across ten files guarantees drift, and drift in the
nav is exactly the thing a visitor notices. Content still lives in hand-written
fragments under content/<lang>/<page>.html; only the chrome is generated.

Run: python3 tools/build_site.py
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"

# page key -> (fr filename, en filename)
FILES = {
    "home":        ("index.html",       "en.html"),
    "village":     ("village.html",     "en-village.html"),
    "visit":       ("visiter.html",     "en-visit.html"),
    "attractions": ("attractions.html", "en-attractions.html"),
    "shop":        ("hangar.html",      "en-shop.html"),
}

NAV = ["home", "village", "visit", "attractions", "shop"]

LANG = {
    "fr": {
        "code": "fr-CA",
        "og_locale": "fr_CA",
        "og_locale_alt": "en_CA",
        "brand_alt": "Chimoubongo, Québec, Canada",
        "tagline": "Jumelé avec une roche &middot; Fondé en 1971 &middot; Population : Assez",
        "nav": {
            "home": "Le village",
            "village": "L'histoire",
            "visit": "Se rendre",
            "attractions": "Quoi voir",
            "shop": "Le hangar",
        },
        "shopbar": (
            'Le hangar à souvenirs est ouvert. Chandails, hoodies, tasses, autocollants.',
            "Magasiner",
        ),
        "footer_note": "Un village dans les pins de la Mauricie. Apporte un pot. Laisse la montre dans le char.",
        "footer_head": ("Le village", "Le hangar"),
        "footer_shop": "Des affaires à rapporter",
        "footer_shop_ext": "Le hangar au complet",
        "other_lang": "English",
        "bureau": "Bureau de tourisme et des sentiments connexes de Chimoubongo",
    },
    "en": {
        "code": "en-CA",
        "og_locale": "en_CA",
        "og_locale_alt": "fr_CA",
        "brand_alt": "Chimoubongo, Quebec, Canada",
        "tagline": "Twinned with a rock &middot; Established 1971 &middot; Population: Enough",
        "nav": {
            "home": "The town",
            "village": "The story",
            "visit": "Getting here",
            "attractions": "What to see",
            "shop": "The shed",
        },
        "shopbar": (
            "The souvenir shed is open. Shirts, hoodies, mugs, stickers.",
            "Shop",
        ),
        "footer_note": "A town in the Mauricie pines. Bring a jar. Leave the clock in the car.",
        "footer_head": ("The town", "The shed"),
        "footer_shop": "Things to take home",
        "footer_shop_ext": "The whole shed",
        "other_lang": "Français",
        "bureau": "Chimoubongo Bureau of Tourism &amp; Adjacent Feelings",
    },
}

# title / description / og description, per language per page
META = {
    "fr": {
        "home":        ("Chimoubongo, Québec — Population : Assez",
                        "Un p'tit village dans les pins de la Mauricie qui accueille le monde bizarre, fondé en 1971. Apporte un pot. Laisse la montre.",
                        "Un village dans les pins qui a été voté en existence. Tout le monde est bienvenu, surtout le monde bizarre."),
        "village":     ("L'histoire — Chimoubongo",
                        "Comment neuf personnes pis un chien ont voté un village en existence en 1971, le fondateur Alphonse-Réal Bougie, pis les neuf règles de la charte.",
                        "Le Vote, le fondateur, pis les neuf règles écrites au dos d'un horaire d'autobus."),
        "visit":       ("Se rendre — Chimoubongo",
                        "Où c'est en Mauricie, comment s'y rendre à partir de Shawinigan, pis quoi apporter.",
                        "La 155 vers le nord, la pancarte PAS LOIN, pis la fourche de droite."),
        "attractions": ("Quoi voir — Chimoubongo",
                        "Le deuxième plus gros maringouin au monde, le Tableau des Excuses, la Battue des patates, pis quoi faire dans les arbres.",
                        "Deux statues d'insectes, un tableau d'excuses, pis une battue de patates annuelle."),
        "shop":        ("Le hangar à souvenirs — Chimoubongo",
                        "Chandails, hoodies, tasses pis autocollants de Chimoubongo. Expédiés par Fourthwall.",
                        "Des affaires à rapporter d'une place qui existe pas officiellement."),
    },
    "en": {
        "home":        ("Chimoubongo, Québec — Population: Enough",
                        "A small town in the Mauricie pines that welcomes weird people, founded 1971. Bring a jar. Leave the clock.",
                        "A town in the pines that was voted into existence. Everyone is welcome, especially the strange ones."),
        "village":     ("The Story — Chimoubongo",
                        "How nine people and a dog voted a town into existence in 1971, founder Alphonse-Réal Bougie, and the nine rules of the charter.",
                        "The Vote, the founder, and nine rules written on the back of a bus schedule."),
        "visit":       ("Getting Here — Chimoubongo",
                        "Where it is in the Mauricie, how to drive in from Shawinigan, and what to bring.",
                        "Route 155 north, the NOT FAR sign, and the right-hand fork."),
        "attractions": ("What To See — Chimoubongo",
                        "The world's second-largest mosquito, the Apology Board, the Potato Bash, and things to do in the trees.",
                        "Two insect statues, a board of apologies, and an annual potato bash."),
        "shop":        ("The Souvenir Shed — Chimoubongo",
                        "Chimoubongo shirts, hoodies, mugs and stickers. Shipped by Fourthwall.",
                        "Things to take home from a place that does not officially exist."),
    },
}

SITE = "https://chimoubongo.com/"


def css_version() -> str:
    return hashlib.sha256((ROOT / "assets" / "site.css").read_bytes()).hexdigest()[:12]


def json_ld(lang: str, page: str, canonical: str) -> str:
    """Structured data for the page.

    Deliberately limited to WebSite / WebPage / BreadcrumbList. We do NOT emit
    LocalBusiness, Place or geo coordinates: Chimoubongo is invented, and
    asserting a real business at fabricated coordinates in structured data is
    both dishonest and a spam signal. Site-level search understanding and
    breadcrumbs are the honest wins available here.
    """
    L = LANG[lang]
    title, desc, _og = META[lang][page]
    home_file = FILES["home"][0 if lang == "fr" else 1]
    home_url = SITE + ("" if home_file == "index.html" else home_file)

    crumbs = [{"@type": "ListItem", "position": 1,
               "name": L["nav"]["home"], "item": home_url}]
    if page != "home":
        crumbs.append({"@type": "ListItem", "position": 2,
                       "name": L["nav"][page], "item": canonical})

    graph = [
        {"@type": "WebSite", "@id": SITE + "#website", "url": home_url,
         "name": "Chimoubongo", "inLanguage": L["code"],
         "description": META[lang]["home"][1]},
        {"@type": "WebPage", "@id": canonical + "#webpage", "url": canonical,
         "name": title, "description": desc, "inLanguage": L["code"],
         "isPartOf": {"@id": SITE + "#website"},
         "primaryImageOfPage": SITE + "assets/logo.png",
         "breadcrumb": {"@id": canonical + "#breadcrumb"}},
        {"@type": "BreadcrumbList", "@id": canonical + "#breadcrumb",
         "itemListElement": crumbs},
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False, separators=(",", ":"))


def chrome_top(lang: str, page: str, version: str) -> str:
    L = LANG[lang]
    title, desc, og = META[lang][page]
    fr_file, en_file = FILES[page]
    self_file = fr_file if lang == "fr" else en_file
    other_file = en_file if lang == "fr" else fr_file
    canonical = SITE + ("" if self_file == "index.html" else self_file)
    jsonld = json_ld(lang, page, canonical)

    nav_links = "\n".join(
        '  <a class="nl{on}" href="{href}">{label}</a>'.format(
            on=" on" if key == page else "",
            href="./" if FILES[key][0 if lang == "fr" else 1] == "index.html"
                 else FILES[key][0 if lang == "fr" else 1],
            label=L["nav"][key],
        )
        for key in NAV
    )
    shop_href = FILES["shop"][0 if lang == "fr" else 1]
    bar_text, bar_cta = L["shopbar"]

    return f"""<!DOCTYPE html>
<html lang="{L['code']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="assets/logo.png">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="fr-CA" href="{SITE}{'' if fr_file == 'index.html' else fr_file}">
<link rel="alternate" hreflang="en-CA" href="{SITE}{en_file}">
<link rel="alternate" hreflang="x-default" href="{SITE}{'' if fr_file == 'index.html' else fr_file}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Chimoubongo">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="{L['og_locale']}">
<meta property="og:locale:alternate" content="{L['og_locale_alt']}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{og}">
<meta property="og:image" content="{SITE}assets/logo.png">
<meta property="og:image:alt" content="{L['brand_alt']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{og}">
<meta name="twitter:image" content="{SITE}assets/logo.png">
<link rel="stylesheet" href="assets/site.css?v={version}">
<script type="application/ld+json">{jsonld}</script>
<noscript><style>.rv{{opacity:1!important;transform:none!important}}</style></noscript>
<script data-goatcounter="https://chimoubongo.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body>

<div class="topbar"><div class="wrap">
  <span class="tw">{L['tagline']}</span>
  <span class="langbar"><a href="{fr_file if fr_file != 'index.html' else './'}" class="{'on' if lang == 'fr' else ''}">FR</a><a href="{en_file}" class="{'on' if lang == 'en' else ''}">EN</a></span>
</div></div>

<nav><div class="wrap">
  <a class="brand" href="{'./' if lang == 'fr' else 'en.html'}">
    <img src="assets/logo.png" alt="{L['brand_alt']}">
    <span>Chimoubongo</span>
  </a>
{nav_links}
</div></nav>

<aside class="shopbar"><div class="wrap">
  <span class="sb-text">{bar_text}</span>
  <a class="sb-cta" href="{shop_href}">{bar_cta} <span class="ar">&rarr;</span></a>
</div></aside>
"""


def chrome_bottom(lang: str) -> str:
    L = LANG[lang]
    i = 0 if lang == "fr" else 1
    town_head, shed_head = L["footer_head"]
    town_links = "\n".join(
        f'          <li><a href="{FILES[k][i] if FILES[k][i] != "index.html" else "./"}">{L["nav"][k]}</a></li>'
        for k in ("home", "village", "visit", "attractions")
    )
    return f"""
<footer>
  <div class="wrap">
    <div class="cols">
      <div>
        <img class="fmark" src="assets/logo.png" alt="Chimoubongo">
        <p class="fnote">{L['footer_note']}</p>
      </div>
      <div>
        <h5>{town_head}</h5>
        <ul>
{town_links}
          <li><a href="{FILES['home'][1 - i] if FILES['home'][1 - i] != 'index.html' else './'}">{L['other_lang']}</a></li>
        </ul>
      </div>
      <div>
        <h5>{shed_head}</h5>
        <ul>
          <li><a href="{FILES['shop'][i]}">{L['footer_shop']}</a></li>
          <li><a href="https://chimoubongo-shop.fourthwall.com/" rel="noopener">{L['footer_shop_ext']}</a></li>
        </ul>
      </div>
    </div>
    <div class="base">
      <span>{L['bureau']}</span>
      <span><a href="https://chimoubongo.com">chimoubongo.com</a></span>
    </div>
  </div>
</footer>

<script src="assets/site.js" defer></script>
</body>
</html>
"""


def page_url(page: str, lang: str) -> str:
    name = FILES[page][0 if lang == "fr" else 1]
    return SITE + ("" if name == "index.html" else name)


def build_sitemap() -> str:
    """Sitemap with reciprocal hreflang alternates on every URL entry.

    Generated from FILES so it cannot list a page that does not exist, which is
    the usual way a hand-written sitemap rots.
    """
    urls = []
    for page in FILES:
        for lang in ("fr", "en"):
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{LANG[o]["code"]}" '
                f'href="{page_url(page, o)}"/>'
                for o in ("fr", "en")
            )
            alts += ('\n    <xhtml:link rel="alternate" hreflang="x-default" '
                     f'href="{page_url(page, "fr")}"/>')
            prio = "1.0" if page == "home" else ("0.9" if page == "shop" else "0.8")
            urls.append(
                f"  <url>\n    <loc>{page_url(page, lang)}</loc>{alts}\n"
                f"    <changefreq>monthly</changefreq>\n"
                f"    <priority>{prio}</priority>\n  </url>"
            )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(urls) + "\n</urlset>\n")


def build_robots() -> str:
    return ("User-agent: *\n"
            "Allow: /\n"
            "\n"
            f"Sitemap: {SITE}sitemap.xml\n")


def build() -> list[str]:
    version = css_version()
    written = []
    for page, (fr_file, en_file) in FILES.items():
        for lang, name in (("fr", fr_file), ("en", en_file)):
            fragment = (CONTENT / lang / f"{page}.html").read_text(encoding="utf-8")
            html = chrome_top(lang, page, version) + fragment.rstrip() + "\n" + chrome_bottom(lang)
            (ROOT / name).write_text(html, encoding="utf-8")
            written.append(name)
    (ROOT / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (ROOT / "robots.txt").write_text(build_robots(), encoding="utf-8")
    written += ["sitemap.xml", "robots.txt"]
    return written


if __name__ == "__main__":
    out = build()
    pages = [n for n in out if n.endswith(".html")]
    print(f"built {len(pages)} pages at css v{css_version()}:")
    for name in pages:
        n = len(re.findall(r"\S+", (ROOT / name).read_text(encoding="utf-8")))
        print(f"  {name:22} {n:5} tokens")
    for name in out:
        if not name.endswith(".html"):
            print(f"  seo: {name}")
