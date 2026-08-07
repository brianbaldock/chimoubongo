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
- `bake_map.py` — one-shot OpenStreetMap tile bake, not run on a schedule
- `battue.py` — one-shot #battue restructure (applied, kept for record)
- `doingcard.py` — one-shot #doing duplicate-photo removal (applied)

## Measure, do not squint

Screenshots are expensive and the aux vision model rubber-stamps "looks
fine" regardless of actual geometry. Nearly everything that makes the page
look amateur is a number you can read out of the DOM:

```js
// section rhythm: heights, share of page, images per section
[...document.querySelectorAll('section')].map(s => ({
  id: s.id, h: Math.round(s.getBoundingClientRect().height),
  imgs: s.querySelectorAll('img').length, chars: s.innerText.length
}))

// grid raggedness: cards in one grid should be within ~30px of each other
[...document.querySelectorAll('#doing .card')]
  .map(c => Math.round(c.getBoundingClientRect().height))
```

Defects found this way that no screenshot would have named precisely:

- `#battue` was a 2864px dark slab with 2524px of unbroken reversed body
  copy, against a ~800px maximum run anywhere in the upper half
- it was the only section on the page with no `.sechead`
- one `ul.sched` row measured 677px against ~81px for its six neighbours
- `#doing` cards measured 503/503/503/280/280/280, a 223px spread

**Local preview caches `site.css` hard.** A CSS change can look like it did
nothing. Confirm before re-debugging:

```js
const r = await fetch('assets/site.css?bust=' + Date.now());
(await r.text()).includes('your-new-declaration')   // is the file right?
[...document.styleSheets].flatMap(s => [...s.cssRules])
  .filter(x => (x.selectorText||'').includes('your-selector'))  // is it live?
```

Bust it with `link.href = 'assets/site.css?b=' + Date.now()`.

**Mobile without a device:** measure in a 390px iframe rather than guessing
from media queries.

```js
const f = document.createElement('iframe');
f.style.cssText = 'position:fixed;left:-9999px;width:390px;height:844px';
f.src = '/?m=' + Date.now(); document.body.appendChild(f);
// then read f.contentDocument, wait ~2s for scroll-reveal
```

## Gotcha: inline children of a grid li

`ul.sched li` was `display:grid` with a `78px 1fr` template. The one entry
containing a `<strong>` lead-in had that `<strong>` blockified into a second
grid row, stretching the row to 677px. Setting `display:inline` on it does
**not** help; a direct child of a grid container is always blockified. Use a
hanging indent (`padding-left` + negative `text-indent`) for lists whose
items may contain arbitrary inline markup.
