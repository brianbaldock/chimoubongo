"""Lower-half design pass.

Applies the same structural edits to index.html and en.html, keyed on
language-neutral markup anchors so the two pages can never drift.
Every edit asserts its match count.
"""
import re, os, sys

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ['index.html', 'en.html']
report = []


def sub1(pattern, repl, s, label, flags=0, count=1, expect=1):
    s2, n = re.subn(pattern, repl, s, count=count, flags=flags)
    assert n == expect, f'{label}: expected {expect} match, got {n}'
    report.append(f'    {label}: {n}')
    return s2


for f in FILES:
    path = os.path.join(D, f)
    s = open(path, encoding='utf-8').read()
    report.append(f'== {f}')
    before = len(s)

    # ------------------------------------------------------------------
    # 1. Break #bureau into two sections so the 7262px slab gets a
    #    background change partway down, matching upper-half rhythm.
    #    Split point: after the attraction rows close, before the poster.
    # ------------------------------------------------------------------
    s = sub1(
        r'</div>\n\n<div class="poster feature rv">',
        '</div>\n</div>\n</section>\n\n'
        '<section id="battue" class="alt">\n'
        '<div class="wrap">\n'
        '<div class="poster feature rv">',
        s, 'split bureau before poster')

    # ------------------------------------------------------------------
    # 2. Give the attraction rows a numbered register treatment so the
    #    five identical 3:2 rows read as a catalogue, not a repeat.
    # ------------------------------------------------------------------
    s = sub1(r'<div class="rows rv">', '<div class="rows register rv">',
             s, 'rows -> register')

    # ------------------------------------------------------------------
    # 3. Kill inline layout styles. These are the accumulated patches
    #    that make the bottom look hand-repaired. Replace with classes.
    # ------------------------------------------------------------------
    s = sub1(r'<p style="margin-top:22px"><strong>', '<p class="lede-note"><strong>',
             s, 'inline margin-top:22px -> .lede-note')
    s = sub1(r'<p style="margin-top:26px"><em>', '<p class="signoff"><em>',
             s, 'inline margin-top:26px -> .signoff')
    s = sub1(r'<div class="pull" style="margin-top:34px">', '<div class="pull spaced">',
             s, 'inline margin-top:34px -> .spaced')
    s = sub1(r'<div class="band" style="margin-bottom:0">', '<div class="band flush">',
             s, 'inline margin-bottom:0 -> .flush')
    s = sub1(r'<p style="max-width:340px;margin:0">', '<p class="fnote">',
             s, 'footer inline -> .fnote')

    # ------------------------------------------------------------------
    # 4. Remove the two empty <div class="wrap"></div> leftovers.
    # ------------------------------------------------------------------
    s = sub1(r'\n<div class="wrap">\s*</div>', '', s, 'empty .wrap removed',
             count=0, expect=2)

    open(path, 'w', encoding='utf-8').write(s)
    report.append(f'    {before} -> {len(s)} chars')

print('\n'.join(report))
print('OK')
