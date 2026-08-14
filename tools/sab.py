"""Sabotage mutations for the SEO gate harness. Scratch copies only.

Kept as a file rather than inline python -c because inline -c trips the host
command guard. Each mutation targets one real SEO defect class.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "village.html"


def sub(pattern, repl, path=P, count=1):
    t = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, t, count=count, flags=re.S)
    if n != count:
        raise SystemExit(f"mutation did not apply: {pattern}")
    path.write_text(new, encoding="utf-8")


def ld_block(t):
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', t, re.S)
    if not m:
        raise SystemExit("no ld+json block")
    return m


def mutate_json(fn):
    t = P.read_text(encoding="utf-8")
    m = ld_block(t)
    data = json.loads(m.group(2))
    fn(data)
    new = t[:m.start(2)] + json.dumps(data, ensure_ascii=False) + t[m.end(2):]
    P.write_text(new, encoding="utf-8")


def main(case):
    if case == "canonical":
        sub(r'<link rel="canonical" href="[^"]+"',
            '<link rel="canonical" href="https://chimoubongo.com/wrong.html"')
    elif case == "noindex":
        sub(r'<meta name="robots" content="[^"]*"',
            '<meta name="robots" content="noindex, nofollow"')
    elif case == "nodesc":
        sub(r'<meta name="description" content="[^"]*">\n', "")
    elif case == "relimg":
        sub(r'<meta property="og:image" content="[^"]*"',
            '<meta property="og:image" content="assets/logo.png"')
    elif case == "badimg":
        sub(r'<meta property="og:image" content="[^"]*"',
            '<meta property="og:image" content="https://chimoubongo.com/assets/nope.png"')
    elif case == "ogurl":
        sub(r'<meta property="og:url" content="[^"]*"',
            '<meta property="og:url" content="https://chimoubongo.com/other.html"')
    elif case == "noxdefault":
        sub(r'<link rel="alternate" hreflang="x-default" href="[^"]+">\n', "")
    elif case == "badjson":
        t = P.read_text(encoding="utf-8")
        m = ld_block(t)
        broken = m.group(2).replace("}", "", 1)
        if broken == m.group(2):
            raise SystemExit("json mutation did not land")
        P.write_text(t[:m.start(2)] + broken + t[m.end(2):], encoding="utf-8")
    elif case == "jsonurl":
        def f(d):
            for n in d["@graph"]:
                if n.get("@type") == "WebPage":
                    n["url"] = "https://chimoubongo.com/drift.html"
        mutate_json(f)
    elif case == "fakeplace":
        def f(d):
            d["@graph"].append({
                "@type": "LocalBusiness", "name": "Chimoubongo",
                "address": {"@type": "PostalAddress", "addressRegion": "QC"},
            })
        mutate_json(f)
    elif case == "ghostloc":
        s = ROOT / "sitemap.xml"
        sub(r"</urlset>",
            "  <url><loc>https://chimoubongo.com/ghost.html</loc></url>\n</urlset>",
            path=s)
    elif case == "badxml":
        s = ROOT / "sitemap.xml"
        s.write_text(s.read_text(encoding="utf-8").replace("</urlset>", ""),
                     encoding="utf-8")
    else:
        raise SystemExit(f"unknown case {case}")


if __name__ == "__main__":
    main(sys.argv[1])
