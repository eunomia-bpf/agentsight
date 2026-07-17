# Step 0042 — Minimal AAAI-27 Format Repair

## Node identity

- **Started:** 2026-07-17T14:38:00-07:00
- **Parent:** Step 0041 format REVIEW
- **Gate:** WRITE
- **Scope:** only the five mechanical violations listed in Step 0041.
- **Repository HEAD:** `cfe62570412f90dc024beb34a458e6481404f1aa`
- **Branch:** `research/semantic-flamegraph-artifacts-v2`; this WRITE node does
  not perform Git operations.
- **Read-only submodule:** `docs/agentpprof-paper` at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

## Immutable content

The exact thesis, the four RQs and their order, prose, claims, evidence,
numbers, qualifiers, citations, algorithms, and submodule are immutable. This
node changes only float placement commands, typography sizes, figure placement,
and paper-asset serialization.

## Approved repair

1. Remove `float`; replace `[H]` with ordinary top/bottom placement.
2. Make the wide architecture diagram a two-column figure at native size;
   raise all of its labels to `\small` (9 pt).
3. Raise all result-table text from `\scriptsize` to `\small` (9 pt).
4. Re-render the exact existing flamegraph SVG geometry as paper-specific
   assets. The rendering removes only the redundant in-image title/metadata,
   expands rows, uses 24-unit labels (at least 9 pt at final width), and
   truncates labels to their existing rectangles. It does not change any
   rectangle width, hierarchy, value, ordering, or source data.
5. Remove LaTeX `trim` and `clip`, then rebuild and audit the PDF.

## Required exit evidence

- official forbidden-command search is empty;
- nine pages total, with all technical content ending on page seven;
- US Letter and anonymous submission retained;
- no Type 3 or unembedded fonts;
- no overfull boxes;
- exact thesis and four RQs unchanged;
- submodule remains clean at its entry revision; and
- a fresh independent reviewer returns PASS on format compliance and content
  preservation.

## Current status

The mechanical repair is implemented and locally validated; independent
reviews are still in progress.

- `main.pdf` is nine US-Letter pages; page seven ends with the complete
  Conclusion, and page eight begins with `References`.
- The build log has no overfull box, unresolved citation, or unresolved label.
- All PDF fonts are embedded Type 1; no Type 3 font is present.
- The author-kit forbidden-command search is empty.
- The three paper panels preserve every source flamegraph group's title,
  x-coordinate, width, fill, and stroke exactly: 940 token groups, 865 time
  groups, and 2,051 file groups. Only vertical row layout and visible-label
  truncation change.
- Each panel is embedded at 476 pixels per inch. A 24-unit label in the
  1,200-unit source becomes 60 pixels in the 3,000-pixel paper asset, or 9.08
  pt at that final embedding resolution.
- Searches find no token-weighted B$^3$, Recall@20\%, fixed reader, top-3
  reader, `float`, `[H]`, `\resizebox`, LaTeX crop, `\scriptsize`, or
  `\tiny` in the manuscript or figure source.
- The exact thesis occurs in the Abstract, Introduction, and Conclusion; the
  four RQ headings remain attribution, localization, tag accuracy, and cost in
  that order.
- `git diff --check` passes, and the read-only submodule remains clean at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

Step 0043's two independent read-only reviewers both returned **PASS** with
zero must-fix or should-fix items:

- `docs/tmp/review/step-0043-20260717T150000-0700/format-review.md` verifies the
  official AAAI-27 format, final figure/table readability, and exact
  flamegraph geometry/data preservation; and
- `docs/tmp/review/step-0043-20260717T150000-0700/content-preservation-review.md`
  verifies the exact thesis, four RQs/order, claims, numbers, qualifiers,
  citations, standard-metric boundary, and clean read-only submodule.

The minimal format-only WRITE node is therefore **complete and closed**. The
next outer state is the separately running fresh full-paper scientific REVIEW;
the format PASS does not pre-authorize its verdict or a new experiment.
