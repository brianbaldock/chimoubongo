import re, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def sig(f):
    s = open(os.path.join(D, f), encoding='utf-8').read()
    body = s[s.index('</head>'):]
    return re.findall(r'<(\w+)[^>]*class="([^"]*)"', body)
a, b = sig('index.html'), sig('en.html')
for i, (x, y) in enumerate(zip(a, b)):
    if x != y:
        print(f'index {i}:')
        print(f'  fr: <{x[0]} class="{x[1]}">')
        print(f'  en: <{y[0]} class="{y[1]}">')
        for j in range(max(0, i-2), min(len(a), i+3)):
            print(f'    ctx {j}: fr=<{a[j][0]} "{a[j][1]}">  en=<{b[j][0]} "{b[j][1]}">')
        print()
