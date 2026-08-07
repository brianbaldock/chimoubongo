# Chimoubongo site — working notes

Fictional tourism site for an invented hippie town in the Mauricie, Québec.
Bilingual, static, no build step, no dependencies, no trackers, no cookies.

- **Live:** https://chimoubongo.com
- **Repo:** `brianbaldock/chimoubongo`, branch `main`, GitHub Pages from repo root
- **Local preview:** `python3 -m http.server 8777` from repo root

## Layout

```
index.html      French, canonical, served at /
en.html         English mirror, structurally identical
assets/site.css single stylesheet, shared by both pages
assets/site.js  scroll-reveal, shared by both pages, loaded with defer
assets/*.jpg    photo essay
assets/logo.png nav / hero / footer
tools/          maintenance scripts, not shipped
CNAME           chimoubongo.com
```

Both HTML files keep exactly one inline `<style>`: the `<noscript>` fallback
that force-reveals `.rv` content when JS is off. **That block must stay inline
and must never be merged into `site.css`**, or the scroll reveal is dead on
arrival for everyone.

## Design system

Modeled on tourismeshawinigan.com. Tokens live in `:root` at the top of
`site.css`: ink `#221c15`, paper `#faf7f0`, pine `#2f4230`, clay `#b4552d`,
gold `#c08a2e`. Headings are uppercase Helvetica-stack sans with tight
tracking; body is a Palatino/Iowan serif. Fluid sizing via `clamp()`.

Components: `.hero` (full-bleed), sticky blurred `nav`, `.stats`, `.sechead`
(eyebrow + title), `.band` (full-bleed captioned photo), `.fixedband`
(parallax quote), `.row` (alternating photo + text), `.cards`, `.founder`,
`.poster`, `ol.steps`, `ol.charter`, dark `footer`.

The hand-drawn SVG map in `#map` is deliberate line art. Do not photo-swap it.

## Rules for editing

1. **Always edit both `index.html` and `en.html`.** A greedy regex once ate
   two attractions off the English page and the result still looked fine.
   Write per-block, assert expected counts, verify both files afterward.
2. Style changes go in `assets/site.css` only. There is no second copy now.
3. Run `python3 tools/verify.py` after structural edits. It checks element
   count parity between the pages, noscript integrity, brace balance, and
   that every class used in markup has a CSS rule.
4. Screenshot tools capture without scrolling, so `.rv` content below the fold
   *looks* invisible in a full-page capture. That is the tool, not a bug.
   Verify by scrolling and counting `.rv.in` in the browser console.
5. Images: cap 1600px, JPEG q82, progressive, `loading="lazy"` below the fold.
6. Site copy follows Brian's voice rules: no em dashes, no corporate filler.

## tools/

- `inspect.py` — report structure and duplication across both pages
- `extract.py` — one-shot CSS/JS extraction (already applied, kept for record)
- `verify.py` — parity and integrity checks, run after any structural edit
