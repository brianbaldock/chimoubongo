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

- Hand-drawn SVG map removed, real OSM plates kept, legend prose preserved as
  `.gpsnote`. `#map` 2278px -> 1588px, 4.2KB off each page. (5c60442)
- `#rules` charter strengthened, CSS only: 3 narrow columns -> 2 wide, larger
  reading size, `01`-`09` numerals in lighter gold. 866px -> 1257px desktop.
  Contrast 8.74:1 body, 6.77:1 numerals. Charter text untouched. (076d2c9)
- `#doing` given a full-bleed creek band, keeping all six cards text-only so
  the grid stays even. Card spread 0px at all three widths. (3a9db53, be7adc2)
- `#bureau` register split after entry 03 with a full-bleed band between two
  `.wrap` siblings. Counter continuity preserved via
  `.rows.register.continued{counter-reset:reg 3}` so numbering runs 01-05
  across the break. (c28194b)
- `#bureau` band photo corrected: the shard had used the founder's portrait,
  duplicating it on the page. Now a dusk shot of the two statues, which pays
  off the copy's own line about the shadow reaching the gas station. (3d55339)

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

### 1. Mobile nav is a horizontal scroll strip
812px of links scrolling inside 375px. Contained (no body overflow) and
pre-existing, so not urgent, but it is a horizontal-scroll nav on phones.

### 2. Em dashes
Three remain: two in the `<title>`/`og:title`, one in an attribution line
(`» — A.-R. Bougie, 2011`). The attribution dash is conventional typography.
Brian's voice rule targets prose filler. Flagged, not auto-fixed.

### 3. Pre-existing intentional image reuse
`road.jpg` appears twice (hero + `#directions` band) and `bus.jpg` twice
(a `#doing` card + its `#bureau` register entry). Both predate this pass and
read as deliberate callbacks rather than defects. Left alone; noted so a
future duplicate-scan does not "fix" them.

## Lesson: what the parallel shard pass actually cost

Three subagents on one worktree produced good structural work and two bad
judgement calls, both traceable to the same root cause: **every real photo
was already used, and neither agent would accept "no good option exists" as
an answer** even though both briefs explicitly permitted it.

- The `#bureau` agent duplicated `bougie.jpg`, putting the founder's portrait
  in as a decorative band. That is the same duplicate-image defect this pass
  had already removed from `#doing`.
- The `#doing` agent generated a new photo and reported it only as a "new
  asset" without saying it was synthetic.

The second turned out to be *fine* — `icon-prompts.txt` shows the site's
photography was always generated with documentary prompts — but the summary
did not say so, and a parent that trusted the summary would not have known.

Rules that follow from this:

1. **Verify subagent image choices specifically.** Scan for duplicate `src`
   values after any shard that adds imagery. A child optimising for "fill
   the hole" will reuse or invent rather than report a blocker.
2. **Child summaries are self-reports.** Both agents reported success and
   both were structurally correct; the defects were only visible by reading
   the actual markup and asset provenance.
3. **Shared worktree is a real hazard.** Task 2 had its commit overlaid by a
   concurrent one and needed a follow-up commit to restore its change. Work
   landed correctly, but sequencing luck was involved.

## Verification gate for every change

1. `python3 tools/verify.py` must print `RESULT: OK`
2. Measure at 1280 / 820 / 390 — the tablet width caught a real specificity
   bug that desktop and mobile both missed
3. Both `index.html` and `en.html`, always
4. Bust the CSS cache before believing a measurement (see NOTES.md)
5. Scan for duplicate image `src` values; check new assets over HTTP for a
   200 and a plausible byte count (`loading="lazy"` makes offscreen iframe
   checks report false negatives)
