import re, os, sys

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ['index.html', 'en.html']

ok = True
def check(cond, msg):
    global ok
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        ok = False

css = open(os.path.join(D, 'assets', 'site.css'), encoding='utf-8').read()
pages = {f: open(os.path.join(D, f), encoding='utf-8').read() for f in FILES}

# --- cross-page parity: the gotcha that ate the English page before ---
print('== cross-page parity')
def sig(s):
    body = s[s.index('</head>'):]
    return re.findall(r'<(\w+)[^>]*class="([^"]*)"', body)

a, b = sig(pages['index.html']), sig(pages['en.html'])
check(len(a) == len(b), f'same number of classed elements ({len(a)} vs {len(b)})')
check([x[0] for x in a] == [x[0] for x in b], 'same tag sequence')

# The language switcher's .on state is SUPPOSED to differ between pages
# (it marks the current language). Ignore that one class, compare the rest.
strip_on = lambda cl: ' '.join(c for c in cl.split() if c != 'on')
ca = [strip_on(x[1]) for x in a]
cb = [strip_on(x[1]) for x in b]
check(ca == cb, 'same class sequence (ignoring langbar .on state)')

# ...and assert the switcher is actually correct on each page
for f, s in pages.items():
    bar = re.search(r'<span class="langbar">(.*?)</span>', s, re.S)
    check(bar is not None, f'{f}: langbar present')
    if bar:
        on = re.findall(r'<a[^>]*class="on"[^>]*>([^<]+)</a>', bar.group(1))
        want = 'FR' if f == 'index.html' else 'EN'
        check(on == [want], f'{f}: current language marked {want} (got {on})')

for tag in ['section', 'div', 'img', 'figure', 'h2', 'h3', 'h4', 'p', 'li', 'a', 'ul', 'ol']:
    ca = len(re.findall(rf'<{tag}[\s>]', pages['index.html']))
    cb = len(re.findall(rf'<{tag}[\s>]', pages['en.html']))
    check(ca == cb, f'<{tag}> parity {ca} == {cb}')

# --- structural integrity ---
print('== structure')
for f, s in pages.items():
    body = s[s.index('</head>'):]
    check(body.count('<section') == body.count('</section>'),
          f'{f}: section tags balanced ({body.count("<section")})')
    check(s.count('<noscript>') == 1, f'{f}: noscript fallback intact')
    check('opacity:1!important' in s, f'{f}: noscript reveal rule intact')
    check(s.count('assets/site.css') == 1, f'{f}: one stylesheet link')
    check(s.count('assets/site.js') == 1, f'{f}: one script tag')
    check(s.count('<style>') == 1, f'{f}: only the noscript style inline')
    check('id="bureau"' in s and 'id="battue"' in s, f'{f}: bureau split into two sections')
    check(re.search(r'<div class="wrap">\s*</div>', s) is None, f'{f}: no empty .wrap')
    # nav/footer anchors must still resolve
    ids = set(re.findall(r'id="([^"]+)"', s))
    hrefs = {h[1:] for h in re.findall(r'href="(#[^"]+)"', s)}
    missing = hrefs - ids
    check(not missing, f'{f}: all in-page anchors resolve (missing: {missing})')

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
check('ol.sched' not in css, 'dead ol.sched rules removed')
for cls in ['lede-note', 'signoff', 'spaced', 'flush', 'fnote', 'register']:
    check('.' + cls in css, f'.{cls} rule present')

# --- inline style attributes should be gone from the lower half ---
print('== inline styles')
for f, s in pages.items():
    lower = s[s.index('id="bureau"'):]
    inline = re.findall(r'style="([^"]+)"', lower)
    check(not inline, f'{f}: no inline styles below #bureau (found: {inline})')

print('\nRESULT:', 'OK' if ok else 'FAILURES PRESENT')
sys.exit(0 if ok else 1)
