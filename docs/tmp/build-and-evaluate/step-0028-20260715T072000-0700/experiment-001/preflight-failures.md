# Real-Preflight Failure Record

**Experiment:** RQ3 Reference-Calibrated Recurrence
**Closed:** 2026-07-15T07:56:12-07:00
**Status:** **INVALID — CLOSED AFTER TWO PREFLIGHT ATTEMPTS**

## Scope

Both attempts used the approved OSWorld-Human preflight command and stopped in
the self-authored source adapter before fitting NPMI, fitting a cutoff, invoking
`agentpprof`, writing a prediction, loading a target label for scoring, or
computing a candidate metric. CodeTraceBench preflight and both full runs were
not started.

The exact thesis, four RQs, original AgentProf story, tested hypothesis, product
algorithm, target populations, paper, skills, branch, and read-only paper
submodule did not change in response.

## Attempt 1

**Command:**

```bash
python3 script/rq3_reference_calibrated_recurrence_eval.py \
  --mode preflight \
  --binary agentpprof/target/release/agentpprof \
  --operation-file docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl \
  --out-dir .agentsight/experiments/rq3-reference-calibrated-recurrence-v1/preflight
```

**Observed failure:**

```text
06fe7178-4491-4589-810f-2e2bc9502122: fewer than two actions
```

**Cause found without candidate execution:** the new visible loader read the
broad raw source rather than applying the registered Step 0024 eligibility
condition `group_alignment=exact` before grouping. The attempted repair added
that condition and retained no group value in the visible candidate object.

## Attempt 2

The exact approved command above was rerun once.

**Observed failure:**

```text
06fe7178-4491-4589-810f-2e2bc9502122: fewer than two actions
```

**Cause found without candidate execution:** the adapter still treated a
single-operation exact-alignment session as fatal. The established
`group_sequences` helper instead silently excludes groups with fewer than two
operations after applying the required-field filter. A read-only population
inspection confirmed the authoritative rule:

```text
raw source:                         369 sessions
group_alignment=exact:             320 sessions
exact and at least two operations: 287 sessions
registered eligible operations:    3,978
registered eligible pairs:         3,691
```

Those last three values exactly match Step 0024. No third repair or execution
was attempted.

## Closure Decision

`research-experiment-design` states that a self-authored harness failure spends
a preflight attempt, repairs do not reset the count, and the experiment must be
closed after the second invalid attempt. Therefore:

- the experiment is closed as invalid rather than interpreted as a negative
  algorithm result;
- no OSWorld or CodeTrace target metric exists;
- the approved scientific verdict (`supported`, `mixed`, or `contradicted`)
  is not evaluated;
- no paper claim, RQ answer, story, or hypothesis may change;
- the known adapter eligibility defect is recorded but not rerun inside this
  experiment; and
- the optional product/evaluator implementation remains unpromoted pending
  outer-loop disposition after independent result review.

This closure is about execution discipline only. It provides no evidence for
or against reference calibration of the existing recurrence algorithm.
