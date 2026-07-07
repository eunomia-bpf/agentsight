# Round 2a — Insight Attack

**Date:** 2026-07-07

## Strongest attack

"The paper's own related work concedes pprof supports query-time aggregation with tag-derived stacks. What remains is 'intent recognition restores deterministic labels' — NLP classification exists. The contribution collapses to GROUP BY semantic_label with existing machinery."

Supporting evidence: pprof tagroot/tagleaf already injects arbitrary labels as pseudo stack frames. Perfetto SQL does arbitrary query-time aggregation. The paper never compares against pprof-with-tagroot on the same labeled data. Intent recognition is treated as a pluggable engineering component, not a novel mechanism.

## Checklist pattern match

Claims Pattern 1 (Structural mismatch) but the resolution (label + group-by) is obvious. Fails non-obvious test.
