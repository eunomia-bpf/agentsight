# AgentProcessBench Wilson implementation report

**Implemented:** 2026-07-13T06:35:58-07:00

**Approved plan:** `experiment-plan.md`, Revision 3

**Outer gate:** EXPERIMENT

**Status:** implementation complete; REAL PREFLIGHT not yet run

## Scope

This node implements only the approved finite-evidence ranking construction.
It does not edit the prior mean-risk experiment, paper, canonical submodule,
shared skills, thesis, story, four RQs, or positive RQ2 hypothesis.

New files:

```text
script/agentprocessbench_wilson_eval.py
script/test_agentprocessbench_wilson_eval.py
```

The new evaluator imports the already-audited AgentProcessBench source loader,
visible-field converter, released-judge loader, real AgentProf invocation,
human-label loader, group-atomic metric, and matched-shuffle constructor from
`script/agentprocessbench_profile_eval.py`. The prior script remains unchanged
and retains its exact completed result.

## Implemented execution order

The top-level run order is:

1. validate the exact preflight/full CLI size;
2. load visible source fields and operation IDs;
3. load the 20 released judge slots without human labels;
4. run real AgentProf for all five views;
5. independently aggregate family-local released votes and materialize all
   point scores;
6. only then load human-label values;
7. score point estimates, matched shuffles, and paired cluster bootstraps;
8. write ordinary machine artifacts and a Markdown report.

The score-before-label boundary is visible in the source and produces three
pre-label artifacts:

```text
wilson-group-scores.jsonl
wilson-operation-scores.jsonl
wilson-score-report.json
```

None contains a human label. `labels.jsonl` is written only after the fixed
construction has been scored.

## Family-local score implementation

Every group identity is exactly:

```text
(family, AgentProf stack key)
```

The implementation rejects assignment-family mismatch and checks that every
view has at least one group in each selected family. For each view it verifies
exact equality with the input totals for:

- operations;
- non-null released votes;
- released harmful votes.

The same logic applies to flat, session, raw, semantic, and ungrouped views.
Flat therefore has four point-estimate groups in FULL, one per family, even
though real AgentProf emits the same textual `flat:all` stack key.

## Score implementation

The scalar and vectorized paths implement the exact approved formula with:

```text
z = 1.959963984540054
```

Inputs with negative counts or harmful votes above available votes fail. A
group with zero available votes receives score zero, remains in all operation
denominators, and is listed in `zero_vote_groups`. All 20 models remain equally
weighted; null predictions supply no vote.

The group score is described only as a Wilson-shaped deterministic finite-
ensemble score. No code or report interprets it as a calibrated human-harm
confidence bound.

## Metrics and controls

The new metric path calls the previously audited complete-tier implementation.
Equal group scores are reduced into one tier, and AP is:

```text
sum_k (Recall_k - Recall_(k-1)) * Precision_k
```

with both quantities measured after opening the full tier. Work-to-50 also
charges the complete crossing tier.

The scorer records only the approved primary and supporting measurements. It
does not reintroduce Wilson-threshold classification accuracy or FirstErrAcc.

Each of 200 matched shuffles reuses the audited within-family, within-raw-leaf
joint `(intent, phase)` permutation. The new scorer recomputes pooled votes and
Wilson scores for every shuffled group. It writes both AP and work effects;
only the predeclared AP empirical p-value participates in the verdict.

## Bootstrap implementation

Each deterministic draw samples 50 query IDs with replacement inside every
family and applies the multiplicity to all five rollouts and their operations.
For every view, the evaluator recomputes:

- group operation counts;
- group harmful-vote totals;
- group available-vote totals;
- group Wilson scores;
- atomic AP, recall-at-30, and work-to-50.

It does not reuse full-population group scores. Families remain separate until
their metric effects are combined with equal weight. A draw with no human
harmful positive in any family is discarded exactly as planned.

## Historical regression output

The evaluator also recomputes the previous raw/semantic mean-risk point
estimates using the unchanged audited scorer. They are stored under
`mean_risk_regression` only to verify equivalence with the completed first run.
They cannot change the new verdict.

## Focused test results

The new test module covers:

1. scalar and vectorized Wilson formula;
2. score zero for no released evidence;
3. rejection of invalid vote counts;
4. separation of identical AgentProf stack keys across families;
5. label-free score artifacts;
6. retention of all-null operations in every view and denominator;
7. complete equal-score tier AP/work behavior;
8. score recomputation under resampling weights;
9. deterministic family-local matched shuffles;
10. mechanical `SUPPORTED`/`INCONCLUSIVE` verdicts;
11. materialization-before-human-label call order.

Exact focused command:

```bash
python3 -m unittest -v script/test_agentprocessbench_wilson_eval.py
```

Result: **8 tests passed**.

Exact joint regression command:

```bash
python3 -m unittest -v \
  script/test_agentprocessbench_profile_eval.py \
  script/test_agentprocessbench_wilson_eval.py
```

Result: **17 tests passed**, including the prior script's real AgentProf test,
risk-unit loss rejection, label sequencing, atomic metrics, shuffle, and
verdict tests.

`py_compile` also completed successfully for both new files. `ruff` is not
installed in the environment; its absence does not affect the scientific run.

## Planned artifact set

REAL PREFLIGHT and FULL will write into distinct ignored directories:

```text
docs/visexp/out/agentprocessbench-rq2-wilson/preflight/
docs/visexp/out/agentprocessbench-rq2-wilson/full/
```

Each directory will contain visible projection, operations, released risks,
real AgentProf profiles and assignments, pre-label group/operation scores,
post-score labels, 200 shuffle effects, compressed bootstrap rows, summary,
and `report.md`. These are ordinary calculation artifacts, not freezes,
attestations, Git gates, or non-Markdown contracts.

## Next action

Before REAL PREFLIGHT, an independent read-only reviewer must apply
`research-experiment-design` and inspect implementation-plan equivalence,
source/label sequencing, family-local aggregation, vote accounting, bootstrap
recomputation, tests, and unchanged prior/paper/submodule state. Any concrete
must-fix is repaired and reviewed again. Zero must-fix authorizes only REAL
PREFLIGHT, not a scientific conclusion.
