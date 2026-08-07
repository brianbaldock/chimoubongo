import re, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for f in ['index.html', 'en.html']:
    s = open(os.path.join(D, f), encoding='utf-8').read()
    print(f'== {f}')
    for m in re.finditer(r'<div class="wrap">\s*</div>', s):
        line = s[:m.start()].count('\n') + 1
        print(f'  line {line}: {m.group(0)!r}')
