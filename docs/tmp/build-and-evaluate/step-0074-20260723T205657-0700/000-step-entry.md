# Step 0074 Entry — Fixed Recursive RQ3 Backend

**Timestamp:** 2026-07-23T20:56:57-07:00

**Parent:** Step 0073 outer audit

**Outer gate:** EXPERIMENT

**RQ:** RQ3 — How accurately do automatic backends recover operation
structure?

## Objective

Complete the already implemented and real-preflighted source-only recursive
split/stop backend over all 405 CodeTrace sessions. This is the single
mechanism selected by the Step 0073 whole-paper review because it directly
tests whether interval-wide context and an explicit STOP decision reduce the
fragmentation diagnosed in current A2.

## Fixed experiment authority

The complete approved algorithm, input boundary, workload, baselines, standard
metrics, decision rule, failure policy, and product replay protocol remain in:

- `docs/tmp/build-and-evaluate/step-0066-20260722T004313-0700/experiment-001/experiment-plan.md`;
- its eleven serial historical plan reviews;
- `real-preflight.md`;
- `implementation-review.md`; and
- the Step 0066 report through Node 0066-E10.

Step 0074 does not reopen that scientific plan. It resumes the interrupted
complete run under algorithm identity
`recursive-operation-segmentation-v4`, fixed local Qwen3.6-27B Q4_K_M,
temperature zero, seed `20260722`, one 32,768-token llama.cpp slot, and the
same source-only projections. Official stages, recurrence assignments, prior
candidate names, and scores remain unavailable until all 405 predictions are
complete.

## Current starting state

- The current branch is `research/semantic-flamegraph-artifacts-v2`; it is not
  changed.
- Step 0073 is committed and pushed at `1559529f`.
- 256 nonempty session caches from the fixed complete run are valid under the
  exact current inference identity.
- Three zero-byte files left by a prior interrupted write are invalid JSON and
  contain no scientific output. Only those three files were removed.
- The fixed server is healthy on `127.0.0.1:18185`.
- Full inference is resumed over the complete sorted 405-session population.

## Tested hypothesis

The fixed recursive candidate should avoid one-span and turn-singleton
degeneracy and improve ordinary operation-level B-cubed F1 over
multi-resolution recurrence on the complete CodeTrace population, with a
task-cluster 95% interval wholly above zero. Exact adjacent-boundary F1,
precision/recall, group counts, singleton fraction, per-framework results, and
depth/leaf statistics diagnose the mechanism but do not replace the primary
decision.

One backend result changes one tested answer, not the paper thesis, story, or
four RQs.

## RQ4 telemetry boundary

The run retains model request counts, input/output tokens, call-level elapsed
time, failures, retries, source adaptation time, and pprof construction
telemetry. These observations do not participate in the RQ3 decision. They
will be analyzed in a separate RQ4 experiment against:

1. fixed-mark AgentPProf replay; and
2. label-free recurrence end to end on the same source operations.

## Next node

Complete all 405 predictions, materialize exactly one complete-population and
one fixed long-horizon pprof, then open the official stages once for scoring
and independent result review.
