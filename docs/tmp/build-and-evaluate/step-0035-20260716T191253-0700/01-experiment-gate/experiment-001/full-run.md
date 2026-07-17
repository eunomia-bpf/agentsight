# Full Run: CodeTraceBench Stage And Token Attribution

**Started:** 2026-07-16T20:32:37-07:00

**Completed:** 2026-07-16T20:35:44-07:00

**State:** `EXPERIMENT_GATE / COMPLETE FULL RUN`

**Run status:** `VALID`

**Tested hypothesis:** `SUPPORTED`

## Executed Population

The approved deterministic command ran once over the complete pre-existing
source-valid CodeTraceBench target. It did not run an agent, tune the recurrence
constructor, inspect target stages during construction, or select a new subset.

```bash
python3 script/rq1_codetracebench_token_attribution_eval.py \
  --mode full \
  --output .agentsight/experiments/rq1-codetracebench-token-attribution-v1/full
```

The completed run contains 405 failed trajectories, 20,866 operations, 2,948
official human stage intervals, and 251 benchmark tasks. It covers all six
released source forms used by the existing target: 118 OpenHands-native, 95
OpenHands-SWE-raw, 47 mini-SWE-native, 24 mini-SWE-raw, 28 SWE-agent, and 93
Terminus2 trajectories. This is the full 405/468 pre-existing source-valid
target, not every failed trajectory in the release.

## Primary Standard Metric

Ordinary operation-level B-cubed is the predeclared standard partition metric.
Every operation has unit weight. The main comparison uses exactly the same
operations and official stages for the unchanged Step 0024 recurrence stack and
the contiguous source-native raw-action-key view.

| View | B-cubed precision | B-cubed recall | B-cubed F1 |
|---|---:|---:|---:|
| recurrence | 0.828579 | 0.533630 | **0.649173** |
| raw-action-key change | 0.891296 | 0.388437 | **0.541070** |
| action-kind change | 0.947623 | 0.315368 | 0.473242 |
| phase change | 0.685564 | 0.626030 | **0.654445** |
| one session block | 0.173563 | 1.000000 | 0.295788 |
| one operation per block | 1.000000 | 0.141282 | 0.247585 |

The predeclared recurrence-minus-raw-action-key effect is `+0.108103` B-cubed
F1. A paired task-cluster bootstrap over all 251 benchmark tasks with 10,000
resamples and seed `20260716` gives a 95% interval of
`[+0.087091, +0.129132]`; every resampled delta is positive. The ordinary
effect is also positive in each framework: OpenHands `+0.01435`, SWE-agent
`+0.27136`, Terminus2 `+0.25309`, and mini-SWE-agent `+0.14739`.

## Resource-Weighted Secondary Analysis

The source adapter maps 17,148 operation-producing provider responses and
494,862,929 provider-reported tokens to the official operations. This total is
the mapped operation-producing response mass, not the complete cost of every
released trajectory: abandoned earlier SWE-agent attempts and calls that
produce no official operation remain outside the official stage population.

Of those responses, 1,426 produce multiple official operations. They cover
5,144 operations and 35,680,479 tokens, or 7.21% of mapped mass. The
predeclared token-weighted B-cubed sensitivity therefore assigns a shared
response's mass equally, entirely to its first operation, or entirely to its
last operation.

| Allocation | recurrence minus raw-action-key B-cubed F1 |
|---|---:|
| equal | +0.084574 |
| all to first operation | +0.075910 |
| all to last operation | +0.075671 |

Under equal allocation, recurrence reaches 0.651214 token-weighted B-cubed F1
and raw-action-key reaches 0.566640. The direction remains positive under both
extreme allocations. This is a resource-sensitive extension of the standard
partition result, not a community-standard token-attribution metric and not a
replacement for the ordinary B-cubed primary outcome.

## Validity Checks

- All 405 sessions and 20,866 unique `(session, step_id)` operations join once
  to a source usage record, unchanged Step 0024 assignment, and official stage.
- Provider prompt, completion, and total mass are conserved exactly under equal
  allocation: 487,332,028 prompt, 7,530,901 completion, and 494,862,929 total
  tokens.
- Existing recurrence, phase, action-kind, session, and singleton ordinary
  B-cubed values reproduce Step 0024 within `1e-14`, below the `1e-12` bound.
- Target stages and resource weights are loaded only for scoring; neither can
  affect recurrence construction.
- Every planned view, token component, framework breakdown, allocation
  sensitivity, selection audit, and 10,000 bootstrap resamples completed.

## Mechanism Boundary

Phase-only has a slightly higher pooled point estimate than recurrence:
`0.654445` versus `0.649173` ordinary B-cubed F1. A descriptive paired
task-cluster bootstrap for recurrence minus phase gives a 95% interval of
`[-0.017778, +0.008234]`. The direction varies by framework, and token-weighted
point estimates differ by only about 0.0004--0.0011. The experiment therefore
does not establish that either semantic view reliably dominates the other.

This boundary does not contradict H-RQ1. The registered comparison is
recurrence versus the matched raw-action-key view. It means that this RQ1 run
supports semantic stage-aligned attribution over raw action identity, not the
dominance of recurrence over every semantic hierarchy. Recurrence's additional
algorithmic value remains supported separately by the OSWorld-Human RQ3
comparison, where it substantially exceeds phase-only boundary and B-cubed F1.

## Run Artifacts

Machine-readable outputs are under
`.agentsight/experiments/rq1-codetracebench-token-attribution-v1/full/`:

- `operation-usage.jsonl`: one joined usage and assignment record per operation;
- `per-session.jsonl`: per-session sufficient statistics;
- `framework-metrics.json`: framework breakdowns;
- `summary.json`: population, metrics, bootstrap, sensitivity, and validity;
- `report.md`: generated short-form result.
