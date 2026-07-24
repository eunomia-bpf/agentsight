# Step 0075 Report — RQ4 End-to-End Accounting

**Timestamp:** 2026-07-23T22:42:00-07:00  
**Outer gate:** EXPERIMENT  
**Status:** complete

## Question

Measure the observable offline cost of the adopted automatic A2 path on the
complete CodeTrace population, rather than reporting fixed-mark pprof replay as
if it were first construction.

## Completed experiment

The approved boundary starts from fixed normalized target operations; A2
packet construction additionally reads the released raw archives. The complete
405-session, 17,148-turn, 20,866-operation population runs three times per
deterministic component.

| Component | Median wall time |
|---|---:|
| A2 source-packet construction | 501.64 s |
| A2 deterministic assembly/root repair/name canonicalization | 3.54 s |
| Coarse-action serialization control | 0.10 s |
| Label-free recurrence alternative | 0.49 s |
| A2 operation replay | 1.17 s |
| A2 token replay | 1.17 s |

All three reconstructed populations and adopted A2 files are byte-identical.
All 12 pprof files load in stock `go tool pprof` and conserve exact mass.

The adopted automatic-Agent batches have a 54.36-minute historical
artifact-time workflow envelope. This is not model time and cannot supply
provider usage; those quantities remain unavailable.

## Independent decision

Independent result review reconstructed counts, timing medians, maximum RSS,
hashes, profile totals, and the mtime envelope:

- run validity: **VALID**;
- registered deterministic hypothesis: **SUPPORTED**;
- remaining must-fixes: **zero**.

The review also caught and corrected one method-identity error: the timed
`--stack action` control must pair with coarse-action B-cubed/boundary
`.473242/.267524`, not the separate raw-action-detail score.

## RQ impact

RQ4 now has a component-level deterministic construction answer and a
source-preserving replay answer. It does not yet have an instrumented A2
model/provider inference timer. This bounded gap does not affect RQ1--RQ3 or
the paper story.

## Next outer node

Enter WRITE to replace the paper's fixed-input-only RQ4 paragraph with the
reviewed decomposition. Then audit whether the existing RQ1 case needs a
matched source/native control in prose or figure form; do not open another
benchmark by default.
