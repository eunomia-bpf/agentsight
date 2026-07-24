# Fresh full-pass cost and aggregate diagnostics

Timestamp: 2026-07-24T01:26:00-07:00
Condition: frozen AgentReward iteration 0
Status: complete first-pass measurement; not the terminal revised result

## Population and execution

The fixed `gpt-5.6-sol` high-reasoning backend completed all 12 outcome-blind
batches with at most two workers active.  The merged population contains:

- 440 complete sessions;
- 15,338 source trace nodes;
- 7,229 weighted source operations;
- 2,193 generated annotations; and
- 51,904,621 provider-reported trace tokens in the token-width pprof.

The last number is a property of the profiled agent traces.  It is distinct
from the tokens consumed by the annotation backend below.

All 12 batch annotations passed the same AgentPProf validation before merging.
The combined operation and token profiles open successfully, contain all 440
source roots, and conserve exactly 7,229 operations and 51,904,621 trace
tokens.

## Automatic-backend cost

| Quantity | Complete first pass |
|---|---:|
| End-to-end elapsed, fixed two-worker schedule | 3,521.621 s (58.69 min) |
| Summed worker time | 6,661.706 s (111.03 min) |
| Actual input tokens | 12,039,417 |
| Cached input tokens | 10,929,408 |
| Derived uncached input tokens | 1,110,009 |
| Actual output tokens | 312,433 |
| Reasoning output tokens | 56,684 |
| Logical serialized input tokens | 5,006,729 |
| Logical annotation output tokens | 218,586 |

Per session, the fresh pass consumes 27,362 actual input tokens, of which
24,840 are reported cached and 2,523 uncached, plus 710 actual output tokens.
The exact serialized algorithm payload averages 11,379 input and 497 annotation
output tokens per session.  Summed backend work averages 15.14 seconds per
session; the complete two-worker critical path is reported separately above.

Actual provider counters and logical `tiktoken 0.12.0` `o200k_base` payload
counts are both retained because they measure different things.  Actual input
includes the backend's repeated orchestration and cached context.  Logical
input counts the exact fixed instruction, batch request, source-visible trace,
and empty initial annotation once.

## Deterministic profile cost

After annotation, the current release binary merges and materializes the full
440-session population as:

| View | Wall time | Peak RSS | Sample mass | Unique stacks |
|---|---:|---:|---:|---:|
| Operations | 0.26 s | 100.41 MiB | 7,229 | 6,983 |
| Tokens | 0.25 s | 99.25 MiB | 51,904,621 | 6,930 |

This separation is important: deterministic `.pb.gz` construction is
sub-second here, while automatic annotation takes tens of minutes and millions
of tokens.  The paper must not use the former as a proxy for end-to-end
automatic construction.

## Global first-pass diagnostics

The merged first pass has 603 optional semantic tag names:

- 264 names recur across at least two sessions;
- 339 names occur in exactly one session;
- 24 lexical near-name pairs require source-grounded inspection;
- 282 structural intervals receive advisory diagnostics; and
- weighted semantic depth spans two through four operation frames.

Operation mass by semantic depth is 42 at depth two, 7,161 at depth three, and
26 at depth four.  These measurements explain why a second aggregate-aware
pass is necessary: the first pass is complete and valid, but most mass remains
at one common depth and 56.2% of optional names are session-singleton.  Neither
singleton reduction nor greater depth is itself the success criterion.  The
revision backends must reread the implicated source contexts, preserve genuine
distinctions, and improve the fixed user-question answerability or standard
RQ3 scores.

## Next measurement

Iteration 1 processes every structural issue and all supplied singleton or
near-name contexts in deterministic batches.  It records actual and logical
tokens, worker and critical-path time, annotation changes, regenerated global
diagnostics, and profile mass.  Another complete diagnostic pass follows.
Revision stops only after a complete pass accepts no annotation change or an
exact state repeats; no target score, target depth, or outcome label is visible
to the backend.
