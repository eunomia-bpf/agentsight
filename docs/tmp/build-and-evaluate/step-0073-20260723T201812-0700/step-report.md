# Step 0073 Report — Fixed-Instruction RQ3 Follow-On

**Timestamp:** 2026-07-23T20:52:00-07:00
**Status:** complete; transition to recursive RQ3 EXPERIMENT Gate

## Objective

Test whether the current automatic A2 structure result remains stronger than
recurrence on the complete 364-session population annotated after the initial
41-session product collection, without changing the paper's thesis, four RQs,
or story.

## Experiment and result

The scorer filters the already complete A2 and baseline rows by the
manifest-defined follow-on set. It regenerates no annotation, name, recurrence
assignment, or official reference.

| Method | B³ P | B³ R | B³ F1 | Boundary F1 |
|---|---:|---:|---:|---:|
| Current automatic Agent A2 | .910 | .536 | .675 | **.403** |
| Multi-resolution recurrence | .758 | .628 | **.687** | .289 |
| Native source tree | .977 | .270 | .423 | .286 |
| Source-native turn | .993 | .196 | .328 | .252 |

A2 minus recurrence B-cubed F1 is `-.01217`; the 10,000-resample
task-cluster 95% interval is `[-.02727,+.00322]`. The registered positive
hypothesis is therefore inconclusive.

A2 nevertheless has higher exact-boundary F1 in all four frameworks. Its
5,198 predicted occurrences for 2,382 official stages include 1,623
singletons. The combined result diagnoses an over-fragmentation tradeoff:
current A2 detects more real transitions but closes too many short groups on
the broader, shorter follow-on population.

## Verification

- Four serial plan reviews converged to PASS.
- Complete 364-session / 15,116-operation / 14,752-pair run: PASS.
- Exact exclusion of all 41 initial sessions: PASS.
- Independent raw-row subset and metric reconstruction: PASS.
- Independent reproduction of all 10,000 bootstrap draws: PASS to floating
  summation tolerance.
- Fresh full scorer replay: PASS in 0.89 seconds and 86,392 KiB maximum RSS.
- Python compilation and CLI wiring: PASS.
- Whole-paper `iter-review-critique` review: cycle PASS.

## Paper and memory impact

No paper source changes in this cycle. The valid boundary enters
`docs/evaluation.md`; `docs/idea-story.md` records explicitly that it changes
one backend diagnosis, not the thesis, story, four RQs, or research ambition.

ACT*ONOMY is confirmed as mandatory closest-work coverage, but its public
release does not provide compatible CodeTrace operation-boundary predictions.
Recurrence therefore remains the primary same-input numerical baseline for
this experiment.

## Next scientific decision

Complete the already-fixed recursive Qwen3.6-27B source-only backend over all
405 sessions. It asks one interval-wide split/stop question recursively and
therefore directly addresses the observed fragmentation without a gold-driven
contraction rule. Keep ordinary B-cubed primary, boundary F1 secondary, and
report group/singleton statistics.

Retain model-call, token, wall-time, failure, and replay telemetry during the
same run. Analyze those observations only in the subsequent RQ4 experiment,
with fixed-mark replay and label-free recurrence as cost baselines.
