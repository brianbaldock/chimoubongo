# Chimoubongo — lower-half polish worklist

Working file for the section-sharded pass. Survives context compaction.
Delete once the remaining items are shipped.

## Method (decided 2026-08-07)

Measure, do not squint. See NOTES.md "Measure, do not squint" for the exact
console snippets. Vision QA on this project has produced one useful finding in
328 seconds and 50 tool calls, and that finding was already known from
measurement. Full-page screenshots are also the biggest context cost in the
loop, which is what triggered this whole pass.

Subagent shape: one narrow brief per section, up to 3 in parallel
(`delegation.max_concurrent_children: 3`). No handoff chains — a child cannot
spawn a successor here (`max_spawn_depth: 1` forces leaf) and a child's summary
dies with it, so every brief must be self-contained and finishable well inside
50 tool calls.

## Shipped

- `#battue` restructured: was a 2864px dark slab with 2524px of unbroken
  reversed body copy and no section heading. Now story-shaped: head,
  narrative on paper, pull quote, full-bleed band, compact dark panel.
  Dark body 2524px -> 1043px. (671bf1e)
- `ul.sched` row blowout: one row 677px vs ~81px neighbours, caused by a
  `<strong>` direct child of a grid `li` being blockified into its own row.
  Hanging indent instead. Spread 621px -> 50px. (671bf1e)
- `#doing` duplicate photo: `soup.jpg` appeared both as a card figure and as
  the `#visit` full-bleed band, making the card grid ragged.
  Spread 223px -> 27px, one image request saved. (99970c0)
- Register photo column stagger: 518px on odd rows vs 493px on even, because
  the grid is `1.05fr 1fr` while the figure alternates sides.
  Spread 25px -> 0px at 1280/820/390. (523d736, bfe5995)
- Hand-drawn SVG map removed, real OSM plates kept, legend prose preserved as
  `.gpsnote`. `#map` 2278px -> 1588px, 4.2KB off each page. (5c60442)

## Current section measurements (desktop 1280px, post-SVG-removal)

| section | height | % page | bands | images | sechead |
|---|---|---|---|---|---|
| header (hero) | 955 | 4.5 | 0 | 2 | 0 |
| stats strip | 224 | 1.0 | 0 | 0 | 0 |
| `#story` | 2777 | 12.9 | 2 | 1 | 1 |
| `#alphonse` | 1619 | 7.5 | 0 | 1 | 1 |
| `#map` | 1588 | 7.4 | 0 | 2 | 1 |
| `#directions` | 2471 | 11.5 | 1 | 1 | 1 |
| `#doing` | 1012 | 4.7 | 0 | 0 | 1 |
| **`#bureau`** | **4540** | **21.2** | **0** | 5 | 1 |
| `#battue` | 3324 | 15.5 | 1 | 1 | 1 |
| `#rules` | 866 | 4.0 | 0 | 0 | 1 |
| `#visit` | 1539 | 7.2 | 1 | 1 | 1 |
| footer | 427 | 2.0 | 0 | 1 | 0 |

## Open items, ranked

### 1. `#bureau` is the new worst offender
4540px, 21.2% of the page, **zero full-bleed breakers**. This is the same
defect class just fixed in `#battue`, one section earlier. Five numbered
register entries stack with nothing interrupting them. The upper half never
runs more than ~800px without a break.

Likely fix: promote one register entry's photo to a full-bleed band between
entries, or split the register after entry 3 with a band. Do NOT simply add
padding.

Constraint: the register is a numbered catalogue (`counter-increment: reg`).
Any split must keep numbering continuous 01-05 across the break.

### 2. `#doing` has zero images
1012px, six text cards, no photo at all, sitting between two heavy sections.
It is the only content section on the page with no image. It reads as a gap
rather than a rest. Note: it had exactly one photo until the duplicate
`soup.jpg` was removed, so the fix is a *different* photo, not restoring that
one. Available unused-in-this-section assets: `grove.jpg` (used only as the
`#story` fixedband), `bus.jpg`, `road.jpg`.

### 3. `#rules` is visually thin
866px, 4.0%, no image, no band. It carries the nine-rule charter, which is
arguably the emotional core of the site, in the least prominent section on
the page. Dark green background is its only distinction.

### 4. Mobile nav is a horizontal scroll strip
812px of links scrolling inside 375px. Contained (no body overflow) and
pre-existing, so not urgent, but it is a horizontal-scroll nav on phones.

### 5. Em dashes
Three remain: two in the `<title>`/`og:title`, one in an attribution line
(`» — A.-R. Bougie, 2011`). The attribution dash is conventional typography.
Brian's voice rule targets prose filler. Flagged, not auto-fixed.

## Verification gate for every change

1. `python3 tools/verify.py` must print `RESULT: OK`
2. Measure at 1280 / 820 / 390 — the tablet width caught a real specificity
   bug that desktop and mobile both missed
3. Both `index.html` and `en.html`, always
4. Bust the CSS cache before believing a measurement (see NOTES.md)
