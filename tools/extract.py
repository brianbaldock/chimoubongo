import re, os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ['index.html', 'en.html']

src = {f: open(os.path.join(D, f), encoding='utf-8').read() for f in FILES}

styles = {f: re.findall(r'<style>(.*?)</style>', s, re.S) for f, s in src.items()}
scripts = {f: re.findall(r'<script>(.*?)</script>', s, re.S) for f, s in src.items()}

assert styles['index.html'] == styles['en.html'], 'style blocks diverge'
assert scripts['index.html'] == scripts['en.html'], 'script blocks diverge'
assert len(styles['index.html']) == 2, 'expected exactly 2 style blocks'
assert len(scripts['index.html']) == 1, 'expected exactly 1 script block'

main_css, noscript_css = styles['index.html']
main_js, = scripts['index.html']

# The second block is the <noscript> reveal fallback. It MUST stay inline and
# MUST NOT be merged into the always-on stylesheet, or scroll reveal dies.
NOSCRIPT_LINE = '<noscript><style>' + noscript_css + '</style></noscript>'
assert 'opacity:1!important' in noscript_css, 'unexpected second style block'
for f in FILES:
    assert NOSCRIPT_LINE in src[f], f'{f}: noscript fallback not in expected form'

css_out = main_css.strip() + '\n'
js_out = main_js.strip() + '\n'

open(os.path.join(D, 'assets', 'site.css'), 'w', encoding='utf-8').write(css_out)
open(os.path.join(D, 'assets', 'site.js'), 'w', encoding='utf-8').write(js_out)
print(f'wrote assets/site.css  {len(css_out)} chars')
print(f'wrote assets/site.js   {len(js_out)} chars')

LINK = '<link rel="stylesheet" href="assets/site.css">'
SCRIPT = '<script src="assets/site.js" defer></script>'

for f in FILES:
    s = src[f]

    # Only the FIRST style block moves out. Anchor on the exact text so the
    # noscript block can never be the one matched.
    first = '<style>' + main_css + '</style>'
    assert s.count(first) == 1, f'{f}: main style block not uniquely found'
    s = s.replace(first, LINK, 1)

    inline_js = '<script>' + main_js + '</script>'
    assert s.count(inline_js) == 1, f'{f}: inline script not uniquely found'
    s = s.replace(inline_js, SCRIPT, 1)

    # postconditions
    assert s.count('<style>') == 1, f'{f}: expected exactly 1 remaining <style> (noscript)'
    assert NOSCRIPT_LINE in s, f'{f}: noscript fallback lost'
    assert re.search(r'<script(?![^>]*src=)', s) is None, f'{f}: leftover inline script'
    assert s.count(LINK) == 1 and s.count(SCRIPT) == 1, f'{f}: tag count wrong'

    open(os.path.join(D, f), 'w', encoding='utf-8').write(s)
    print(f'{f}: {len(src[f])} -> {len(s)} chars ({s.count(chr(10))+1} lines)')

print('OK')
