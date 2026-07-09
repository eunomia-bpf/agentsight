# Round 0 — Macro Structure

**Date:** 2026-07-08

## Findings
- All sections present and correctly ordered ✓
- No \paragraph or \textbf run-in headers ✓
- Eval heavy (~3p vs 1.5p target) — Should-fix
- Implementation thin (~0.3p) — Consider
- Design missing: folding algorithm, mapping rule example, pipeline overview — Must-fix (user-flagged)

## Changes
- §3 opening: Added 5-stage pipeline description (parse → label → filter → project → fold)
- §3.2: Added formal folding definition (projection to frame sequence + merge + sum weights)
- §3.3: Added concrete mapping rule example + pluggable backend extensibility note
- Eval trimming and Implementation expansion deferred to later rounds
