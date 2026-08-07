import re, os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
css = open(os.path.join(D, 'assets', 'site.css'), encoding='utf-8').read()

used = set()
for f in ['index.html', 'en.html']:
    s = open(os.path.join(D, f), encoding='utf-8').read()
    body = s[s.index('</head>'):]
    for m in re.finditer(r'class="([^"]+)"', body):
        used.update(m.group(1).split())
    for m in re.finditer(r'<(\w+)[\s>]', body):
        used.add(m.group(1))

# every class selector defined in css
defined = set(re.findall(r'\.([A-Za-z][\w-]*)', re.sub(r'/\*.*?\*/', '', css, flags=re.S)))
dead = sorted(c for c in defined if c not in used)
print('DEAD class selectors (defined in CSS, never used in markup):')
for c in dead:
    print('  .' + c)

# element selectors that pair with a class, e.g. ol.sched vs ul.sched
print('\nElement-qualified selectors and whether markup matches:')
for m in re.finditer(r'(?m)^([a-z]+)\.([\w-]+)\s*[,{]', css):
    el, cl = m.group(1), m.group(2)
    hit = 0
    for f in ['index.html', 'en.html']:
        s = open(os.path.join(D, f), encoding='utf-8').read()
        hit += len(re.findall(rf'<{el}[^>]*class="[^"]*\b{re.escape(cl)}\b', s))
    flag = 'OK' if hit else '*** NO MATCH (dead)'
    print(f'  {el}.{cl:<12} matches={hit}  {flag}')

# duplicate selector definitions
sel_counts = {}
for m in re.finditer(r'(?m)^([^@\s][^{]*)\{', css):
    sel = ' '.join(m.group(1).split()).rstrip(',')
    sel_counts[sel] = sel_counts.get(sel, 0) + 1
dupes = {k: v for k, v in sel_counts.items() if v > 1}
print('\nDuplicate selector blocks:')
for k, v in sorted(dupes.items()):
    print(f'  {k}  x{v}')
