import re, os, collections

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(D, 'index.html'), encoding='utf-8').read()
body = s[s.index('</head>'):]

# split into sections
parts = re.split(r'(<section[^>]*>|</section>|<footer>)', body)
cur, secs = None, collections.OrderedDict()
buf = []
for p in parts:
    m = re.match(r'<section[^>]*id="([^"]+)"[^>]*class="([^"]*)"', p) or \
        re.match(r'<section[^>]*class="([^"]*)"', p)
    if p.startswith('<section'):
        idm = re.search(r'id="([^"]+)"', p)
        clm = re.search(r'class="([^"]*)"', p)
        cur = idm.group(1) if idm else '(noid)'
        secs[cur] = {'class': clm.group(1) if clm else '', 'html': ''}
        buf = []
    elif p == '</section>' and cur:
        secs[cur]['html'] = ''.join(buf)
        cur = None
    elif cur:
        buf.append(p)

print(f'{"section":<14}{"class":<14}{"h2":>3}{"h3":>3}{"h4":>3}{"img":>4}{"row":>4}{"card":>5}{"band":>5}{"inline-style":>13}')
for k, v in secs.items():
    h = v['html']
    print(f'{k:<14}{v["class"]:<14}'
          f'{len(re.findall(r"<h2", h)):>3}{len(re.findall(r"<h3", h)):>3}'
          f'{len(re.findall(r"<h4", h)):>3}{len(re.findall(r"<img", h)):>4}'
          f'{len(re.findall(r"class=.row.", h)):>4}{len(re.findall(r"class=.card.", h)):>5}'
          f'{len(re.findall(r"class=.band", h)):>5}'
          f'{len(re.findall(r"style=", h)):>13}')

print('\n--- inline style attributes in body ---')
for m in re.finditer(r'<(\w+)[^>]*class="([^"]*)"[^>]*style="([^"]+)"', body):
    print(f'  <{m.group(1)} class="{m.group(2)}"  style="{m.group(3)}"')
for m in re.finditer(r'<(\w+)(?![^>]*class=)[^>]*style="([^"]+)"', body):
    print(f'  <{m.group(1)}  style="{m.group(2)}"')

print('\n--- empty / suspicious containers ---')
for m in re.finditer(r'<div class="wrap">\s*</div>', body):
    print('  EMPTY .wrap at char', m.start())

print('\n--- section background alternation (visual rhythm) ---')
for k, v in secs.items():
    tone = 'TINTED' if 'alt' in v['class'] else ('DARK' if 'dark' in v['class'] else ('BUREAU' if 'bureau' in v['class'] else 'paper'))
    print(f'  {k:<14} {tone}')
