import re, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pages = {}
for f in ['index.html', 'en.html']:
    s = open(os.path.join(D, f), encoding='utf-8').read()
    pages[f] = s
    st = re.findall(r'<style>(.*?)</style>', s, re.S)
    sc = re.findall(r'<script>(.*?)</script>', s, re.S)
    head_end = s.index('</head>')
    print(f'{f}: total={len(s)}  style_blocks={len(st)}  script_blocks={len(sc)}')
    for i, x in enumerate(st):
        print(f'   style[{i}] chars={len(x)} lines={x.count(chr(10))}')
    for i, x in enumerate(sc):
        print(f'   script[{i}] chars={len(x)} lines={x.count(chr(10))}')
    print(f'   body chars={len(s) - head_end}')

a, b = pages['index.html'], pages['en.html']
sa = re.findall(r'<style>(.*?)</style>', a, re.S)
sb = re.findall(r'<style>(.*?)</style>', b, re.S)
ja = re.findall(r'<script>(.*?)</script>', a, re.S)
jb = re.findall(r'<script>(.*?)</script>', b, re.S)
print('CSS identical across pages:', sa == sb)
print('JS  identical across pages:', ja == jb)
if sa != sb and len(sa) == len(sb):
    for i, (x, y) in enumerate(zip(sa, sb)):
        print(f'  style[{i}] same={x==y} lens={len(x)},{len(y)}')
if ja != jb and len(ja) == len(jb):
    for i, (x, y) in enumerate(zip(ja, jb)):
        print(f'  script[{i}] same={x==y} lens={len(x)},{len(y)}')

# external refs already present?
print('link rel=stylesheet in index:', len(re.findall(r'<link[^>]+stylesheet', a)))
print('script src= in index:', len(re.findall(r'<script[^>]+src=', a)))
