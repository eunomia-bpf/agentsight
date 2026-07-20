# REAL PREFLIGHT — Compact-JSON V2.2

**Completed:** 2026-07-19T22:20:00-07:00  
**State:** Complete; full restart authorized

After the unbounded-whitespace full attempt and blocked v2.1 proposal, the
approved compact-JSON constraint restarted preflight from empty caches. All
196/196 operations across the same four complete framework trajectories
finished with no invalid JSON, truncation, context overflow, source mismatch,
or missing transition. Constraint version was
direct-gbnf-single-frame-compact-json-v2.2.

Depth ranged from 1 to 4 with mean 2.199. The transition distribution was 27
pushes and 169 sibling replacements, again with new-frame rate 1.0. The model
used 106,039 prompt and 3,048 completion tokens in 16.30 seconds. Stage labels,
manifest, future evidence, current results, weights, and scores remained
unopened.

The prediction SHA-256 is
c958d3d6ed9255f3e0ab3c85feff0dea5500ee755c74d97e0ad3dc1a2819535c.
A second cache-only invocation reproduced it in 1.40 seconds. The new-frame
rate remains a diagnostic rather than a gate; no prompt or semantic transition
was changed. All enforcement and isolation checks pass. Proceed to a fresh
405-trajectory V2.2 run.
