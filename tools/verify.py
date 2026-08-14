import re, os, sys

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# page key -> (fr file, en file). Must match tools/build_site.py.
PAIRS = {
    "home":        ("index.html",       "en.html"),
    "village":     ("village.html",     "en-village.html"),
    "visit":       ("visiter.html",     "en-visit.html"),
    "attractions": ("attractions.html", "en-attractions.html"),
    "shop":        ("hangar.html",      "en-shop.html"),
}
FILES = [f for pair in PAIRS.values() for f in pair]

ok = True
def check(cond, msg):
    global ok
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        ok = False

css = open(os.path.join(D, 'assets', 'site.css'), encoding='utf-8').read()
pages = {}
for f in FILES:
    path = os.path.join(D, f)
    if not os.path.isfile(path):
        check(False, f'{f}: page missing (run tools/build_site.py)')
        continue
    pages[f] = open(path, encoding='utf-8').read()

# Fail closed: every later section assumes all ten pages exist.
if len(pages) != len(FILES):
    print('\nRESULT: FAILURES PRESENT')
    sys.exit(1)

# --- cross-language parity: the gotcha that ate the English page before ---
print('== cross-language parity')
def sig(s):
    body = s[s.index('</head>'):]
    return re.findall(r'<(\w+)[^>]*class="([^"]*)"', body)

# The language switcher's .on state and the nav's current-page .on state are
# SUPPOSED to vary. Ignore that one class, compare everything else.
strip_on = lambda cl: ' '.join(c for c in cl.split() if c != 'on')

for key, (fr, en) in PAIRS.items():
    a, b = sig(pages[fr]), sig(pages[en])
    check(len(a) == len(b), f'{key}: same number of classed elements ({len(a)} vs {len(b)})')
    check([x[0] for x in a] == [x[0] for x in b], f'{key}: same tag sequence')
    check([strip_on(x[1]) for x in a] == [strip_on(x[1]) for x in b],
          f'{key}: same class sequence (ignoring .on state)')
    for tag in ['section', 'div', 'img', 'figure', 'h2', 'h3', 'h4', 'p', 'li', 'a', 'ul', 'ol']:
        ca = len(re.findall(rf'<{tag}[\s>]', pages[fr]))
        cb = len(re.findall(rf'<{tag}[\s>]', pages[en]))
        check(ca == cb, f'{key}: <{tag}> parity {ca} == {cb}')

# --- language switcher correctness on every page ---
print('== language switcher')
for key, (fr, en) in PAIRS.items():
    for f, want in ((fr, 'FR'), (en, 'EN')):
        bar = re.search(r'<span class="langbar">(.*?)</span>\s*</div>', pages[f], re.S)
        check(bar is not None, f'{f}: langbar present')
        if bar:
            on = re.findall(r'<a[^>]*class="on"[^>]*>([^<]+)</a>', bar.group(1))
            check(on == [want], f'{f}: current language marked {want} (got {on})')
    # ...and each page must point at its own translation, not the home page.
    check(f'href="{en}"' in pages[fr], f'{fr}: EN switch targets {en}')
    other = './' if fr == 'index.html' else fr
    check(f'href="{other}"' in pages[en], f'{en}: FR switch targets {other}')

# --- structural integrity ---
print('== structure')
for f, s in pages.items():
    body = s[s.index('</head>'):]
    check(body.count('<section') == body.count('</section>'), f'{f}: section tags balanced')
    check(body.count('<div') == body.count('</div>'), f'{f}: div tags balanced')
    check(s.count('<noscript>') == 1, f'{f}: noscript fallback intact')
    check('opacity:1!important' in s, f'{f}: noscript reveal rule intact')
    check(s.count('assets/site.css') == 1, f'{f}: one stylesheet link')
    check(s.count('assets/site.js') == 1, f'{f}: one script tag')
    check(s.count('<style>') == 1, f'{f}: only the noscript style inline')
    check(s.count('<title>') == 1 and s.count('<h1') <= 1, f'{f}: one title, at most one h1')

# --- no inline style attributes anywhere ---
print('== inline styles')
for f, s in pages.items():
    inline = re.findall(r'style="([^"]+)"', s[s.index('</head>'):])
    check(not inline, f'{f}: no inline styles (found: {inline})')

# --- every link resolves: in-page anchors AND page-to-page hrefs ---
print('== links')
on_disk = set(os.listdir(D))
for f, s in pages.items():
    ids = set(re.findall(r'id="([^"]+)"', s))
    hrefs = re.findall(r'href="([^"]+)"', s)
    anchors = {h[1:] for h in hrefs if h.startswith('#')}
    check(not (anchors - ids), f'{f}: in-page anchors resolve (missing: {anchors - ids})')
    local = [h for h in hrefs
             if not h.startswith(('#', 'http', 'mailto:', './'))
             and h.endswith('.html')]
    broken = [h for h in local if h.split('#')[0] not in on_disk]
    check(not broken, f'{f}: local page links resolve (broken: {broken})')

# --- the whole point of the site: merch must be reachable from every page ---
print('== merch reachability')
for key, (fr, en) in PAIRS.items():
    for f, shop in ((fr, PAIRS['shop'][0]), (en, PAIRS['shop'][1])):
        s = pages[f]
        bar = re.search(r'<aside class="shopbar">.*?</aside>', s, re.S)
        check(bar is not None, f'{f}: merch banner present')
        if bar:
            check(f'href="{shop}"' in bar.group(0),
                  f'{f}: merch banner links to {shop}')
            text = re.sub(r'<[^>]+>', ' ', bar.group(0))
            check(len(text.split()) >= 4, f'{f}: merch banner has real copy')
        check(f'href="{shop}"' in s.split('<footer')[1] if '<footer' in s else False,
              f'{f}: footer links to {shop}')
        nav = re.search(r'<nav>.*?</nav>', s, re.S)
        check(nav is not None and f'href="{shop}"' in nav.group(0),
              f'{f}: nav links to {shop}')

# --- checkout forms live on the shop pages and NOWHERE else -------------
# Duplicated Fourthwall variant UUIDs across pages is how a price or a size
# silently goes stale on one page only.
print('== checkout containment')
for f, s in pages.items():
    forms = s.count('<form')
    if f in PAIRS['shop']:
        check(forms == 5, f'{f}: five checkout forms (got {forms})')
        check(s.count('fourthwall.com/cart/checkout') == 5, f'{f}: five checkout actions')
        check('ptkn_' not in s, f'{f}: no storefront token in markup')
    else:
        check(forms == 0, f'{f}: no checkout forms outside the shop page (got {forms})')

# --- page weight: the reason for the split ------------------------------
# Before the split each page was ~7000 words of body copy in one scroll.
# This is a real gate, not a vanity metric: if a page creeps back over the
# ceiling the split has been undone by accretion.
print('== page weight')
CEILING = 1800
for f, s in pages.items():
    body = re.sub(r'<[^>]+>', ' ', s[s.index('</head>'):])
    words = len(body.split())
    check(words <= CEILING, f'{f}: {words} words (ceiling {CEILING})')

# --- CSS coverage ---
print('== css')
used = set()
for s in pages.values():
    body = s[s.index('</head>'):]
    for m in re.finditer(r'class="([^"]+)"', body):
        used.update(m.group(1).split())
missing = [c for c in sorted(used) if not re.search(r'[.\s,{]' + re.escape(c) + r'[\s,{:.]', css)]
check(not missing, f'every markup class has a CSS rule (missing: {missing})')
check(css.count('{') == css.count('}'), f'braces balanced ({css.count("{")})')
for cls in ['shopbar', 'sb-cta', 'tease', 'lede-note', 'signoff', 'spaced', 'flush', 'fnote', 'register']:
    check('.' + cls in css, f'.{cls} rule present')

print('\nRESULT:', 'OK' if ok else 'FAILURES PRESENT')
sys.exit(0 if ok else 1)
