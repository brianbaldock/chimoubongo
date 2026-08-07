import re, os, sys

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = {'index.html': '/tmp/idx.pre.html', 'en.html': '/tmp/en.pre.html'}

ok = True
def check(cond, msg):
    global ok
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        ok = False

for f, pre_path in PRE.items():
    print(f'== {f}')
    pre = open(pre_path, encoding='utf-8').read()
    post = open(os.path.join(D, f), encoding='utf-8').read()

    strip = lambda s: re.sub(r'<style>.*?</style>|<script>.*?</script>|'
                            r'<link rel="stylesheet" href="assets/site.css">|'
                            r'<script src="assets/site.js" defer></script>', '', s, flags=re.S)
    check(strip(pre) == strip(post), 'markup byte-identical outside swapped blocks')

    for tag in ['section', 'div', 'img', 'h2', 'h3', 'p', 'li', 'a']:
        a = len(re.findall(rf'<{tag}[\s>]', pre))
        b = len(re.findall(rf'<{tag}[\s>]', post))
        check(a == b, f'<{tag}> count {a} == {b}')

    check(post.count('<noscript>') == 1, 'noscript fallback present exactly once')
    check('opacity:1!important' in post, 'noscript reveal rule intact')
    check(post.count('assets/site.css') == 1, 'stylesheet linked once')
    check(post.count('assets/site.js') == 1, 'script linked once')

# shared asset sanity
css = open(os.path.join(D, 'assets', 'site.css'), encoding='utf-8').read()
js = open(os.path.join(D, 'assets', 'site.js'), encoding='utf-8').read()
print('== assets')
check('<style' not in css and '</style>' not in css, 'site.css has no tag leakage')
check('<script' not in js and '</script>' not in js, 'site.js has no tag leakage')
check(css.count('{') == css.count('}'), f'site.css braces balanced ({css.count("{")})')
check(':root' in css, 'site.css contains :root tokens')
check('.rv' in css, 'site.css contains reveal rules')
check('IntersectionObserver' in js or 'querySelectorAll' in js, 'site.js contains reveal logic')

# every class used in markup still has a rule somewhere
post = open(os.path.join(D, 'index.html'), encoding='utf-8').read()
body = post[post.index('</head>'):]
used = set()
for m in re.finditer(r'class="([^"]+)"', body):
    used.update(m.group(1).split())
missing = [c for c in sorted(used) if not re.search(r'[.\s,{]' + re.escape(c) + r'[\s,{:.]', css)]
check(not missing, f'all markup classes have CSS rules (missing: {missing})')

print('\nRESULT:', 'OK' if ok else 'FAILURES PRESENT')
sys.exit(0 if ok else 1)
