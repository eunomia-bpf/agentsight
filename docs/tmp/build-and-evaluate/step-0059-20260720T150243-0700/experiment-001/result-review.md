# Independent Result Review

## Verdict

**APPROVE — zero must-fix after the occurrence-identity correction.** The independent read-only reviewer explicitly
applied `research-experiment-design` and classified the run as valid and
complete, the tested hypothesis as inconclusive, and the result as supporting
mechanism-boundary evidence. The candidate is not adopted; multi-resolution
recurrence remains the incumbent. The paper, story, thesis, and RQs remain
unchanged.

## Independent State Replay

The reviewer replayed all 405 session caches rather than trusting the summary:

- 17,148 ordered source-native transitions and 20,866 unique operations;
- 6,267 proposed stays, 10,753 pushes, and 128 pops;
- 11,677 applied stays, 5,343 pushes, and 128 pops;
- all 5,410 exact duplicate-leaf proposals became identity-preserving stays;
- every one of the 128 pops removed exactly one active leaf;
- every operation's post-transition visible path matches both predictions and
  score rows; and
- 17,057 distinct candidate request hashes have zero overlap with the 17,061
  distinct Step 0056 request hashes, confirming that no response from the old
  grammar was reused.

The reviewer also verified the actual model SHA, all 405 source-archive SHAs,
the label-free target schema, request/state replay, and that scoring occurred
only after candidate inference completed.

## Outer-Audit Correction And Fresh Review

The first result pass correctly replayed inference but trusted the scorer's
session-namespaced visible-path identity. Outer audit then found that this
merged an exact path that disappeared and later recurred, contrary to the
approved definition of one task occurrence as a maximal contiguous equal-path
run.

The scorer was corrected symmetrically for the candidate and Step 0056 without
changing any model assignment. Independent fresh review reconstructed the runs
directly from ordered raw paths:

- candidate: 5,761 occurrences from 5,593 distinct session-local paths plus
  168 non-contiguous revisits;
- Step 0056: 6,264 occurrences from 5,972 distinct paths plus 292 revisits; and
- every scored occurrence is exactly one maximal contiguous run, with group
  count equal to span count.

The earlier path-fold scores and bootstrap values are superseded by the
corrected results below.

## Independently Recomputed Standard Metrics

| Method | B-cubed P | B-cubed R | B-cubed F1 | Boundary F1 | Exact-span F1 |
|---|---:|---:|---:|---:|---:|
| candidate | 0.708301 | 0.613398 | 0.657442 | 0.239777 | 0.040877 |
| Step 0056 | 0.754887 | 0.577432 | 0.654342 | 0.256606 | 0.049501 |
| recurrence | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

The raw population independently reproduces 405 sessions, 2,948 stage
occurrences, and 251 task clusters.

The reviewer independently regenerated both 10,000-resample paired
task-cluster bootstraps and matched every saved raw draw:

- candidate minus recurrence: mean `-0.005515468`, 95% interval
  `[-0.020053233,+0.010075115]`, positive fraction `0.2381`;
- candidate minus Step 0056: mean `+0.003095653`, 95% interval
  `[-0.005868074,+0.012358870]`, positive fraction `0.7445`.

The registered interpretation **inconclusive-not-adopted** is therefore
correct.

## Scientific Boundary

The reviewer confirmed the mechanism diagnosis: only 128 pops versus 5,343
effective pushes, 334/405 sessions without any depth decrease, maximum depth
122, and 1,106 exact phase-like proposals. The fixed 3B policy does not learn
semantic task closure. This result cannot be generalized to reject the
well-nested representation, RQ3, the positive hypothesis, or the profiling
thesis, and it does not belong in the positive paper body.
