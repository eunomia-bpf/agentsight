# AgentProcessBench Wilson REAL PREFLIGHT report

**Executed:** 2026-07-13T06:45:10-07:00

**Approved plan:** `experiment-plan.md`, Revision 3

**Implementation review:** PASS, zero must-fix

**Execution status:** **VALID**

**Scientific verdict:** **PREFLIGHT_ONLY**

## Scope and disposition

This run validates the real end-to-end path on the first 10 query IDs in every
family. It cannot support, contradict, or make the approved hypothesis
inconclusive. Its point estimates, intervals, and shuffle values cannot select
a new score, threshold, family, field, or rule.

No paper, submodule, shared skill, thesis, story, RQ, or positive hypothesis was
edited. The only allowed decision is whether the exact FULL command is
executable after independent validity review.

## Exact command and terminal status

```bash
python3 script/agentprocessbench_wilson_eval.py preflight \
  --source docs/visexp/out/agentprocessbench-rq2/source/official-repo \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentprocessbench-rq2-wilson/preflight \
  --query-limit 10 --permutations 200 --bootstraps 1000 \
  --max-bootstrap-attempts 5000 --seed 4204
```

The command exited successfully in approximately five seconds. The machine
summary reports `VALID / PREFLIGHT_ONLY`.

## Real selected data

The official source remained commit
`0a42606b178a8c69d40c5765dc05c342f921e578`. The selected subset contains:

| Family | Tasks | Trajectories | Operations |
|---|---:|---:|---:|
| BFCL | 10 | 50 | 619 |
| GAIA dev | 10 | 50 | 342 |
| HotpotQA | 10 | 50 | 122 |
| tau2 | 10 | 50 | 547 |
| **Total** | **40** | **200** | **1,630** |

All 1,630 operations have 20 released prediction slots. They contain 32,258
non-null votes and 4,909 released harmful votes. The three complete-source
all-null operations belong to GAIA query 19 and therefore are not selected by
the fixed first-10-query preflight. No zero-vote group path occurs in this
subset; the focused tests exercise that approved rule.

## Source/label boundary

The run completed in the approved order:

1. visible source conversion;
2. released-risk loading;
3. five real AgentProf views;
4. family-local group-vote aggregation and point-score materialization;
5. human-label value loading;
6. point, shuffle, and bootstrap scoring.

The pre-label files are:

```text
wilson-group-scores.jsonl       2,127 rows
wilson-operation-scores.jsonl   1,630 rows
wilson-score-report.json
```

They contain operation/group identities, released-vote totals, and scores but
no human label. The separate post-score `labels.jsonl` contains exactly 1,630
rows. The machine audit records `materialized_before_human_labels: true` and
the human-label audit records exact coverage.

## Real AgentProf views

The exact binary was `agentpprof 0.2.37`. It constructed all five views and
conserved exactly 1,630 operations and 57,788,847,116 prior risk units globally
and per AgentProf stack group:

| AgentProf view | AgentProf stack keys | Operations exact | Risk exact |
|---|---:|---|---|
| Flat | 1 | yes | yes |
| Raw action | 99 | yes | yes |
| Semantic | 162 | yes | yes |
| Session | 200 | yes | yes |
| Ungrouped | 1,630 | yes | yes |

The Wilson scorer then applies the approved family-local identity
`(family, AgentProf stack key)`. Consequently, the scoring-group count may be
larger than the globally unique textual AgentProf key count when the same key
appears in multiple families:

| Scored view | Family-local groups | Operations | Available votes | Harmful votes |
|---|---:|---:|---:|---:|
| Flat | 4 | 1,630 | 32,258 | 4,909 |
| Raw action | 115 | 1,630 | 32,258 | 4,909 |
| Semantic | 178 | 1,630 | 32,258 | 4,909 |
| Session | 200 | 1,630 | 32,258 | 4,909 |
| Ungrouped | 1,630 | 1,630 | 32,258 | 4,909 |

Every view reports exact family separation and vote accounting. This planned
split is the same family-stratified unit used by point estimates, shuffles, and
bootstrap before equal-family macro aggregation.

## Historical regression check

The new evaluator reproduced both completed mean-risk preflight effects bit for
bit:

| Effect | Prior preflight | New regression path | Exact |
|---|---:|---:|---|
| Semantic minus raw AP | 0.03187583496787827 | 0.03187583496787827 | yes |
| Raw minus semantic work-to-50 | 0.07491179497942685 | 0.07491179497942685 | yes |

This verifies reuse of the prior converter, assignments, labels, and atomic
metric. It is an implementation check, not a new result.

## Diagnostic preflight measurements

The approved Wilson-shaped score produced these subset diagnostics:

| View | Macro AP | Recall@30 | Work-to-50 |
|---|---:|---:|---:|
| Raw action | 0.535818 | 0.315052 | 0.402106 |
| Semantic | 0.566985 | 0.455010 | 0.312750 |

The paired diagnostic effects were:

| Effect | Point | Preflight 95% interval |
|---|---:|---:|
| Semantic minus raw AP | +0.031167 | [+0.020932, +0.097383] |
| Raw minus semantic work-to-50 | +0.089356 | [+0.012519, +0.136999] |

All 200 matched shuffles completed with exact size preservation. Twenty had AP
effect at least the observed subset effect, giving
`p_shuffle_ap = 21/201 = 0.104478`. Work-effect shuffles ranged from 0.006314
to 0.097291 and are supporting diagnostics only.

The paired query-cluster bootstrap retained 1,000 valid draws after examining
1,001 and discarding one draw with a family lacking a harmful positive. It
recomputed family-local scores in every draw. Completion is exact.

None of these values answers the hypothesis because the run is deliberately
limited to a non-random first-10-query subset. In particular, the preflight
shuffle p-value is not a reason to change the score or plan.

## Artifact set

The complete ignored artifact directory is:

```text
docs/visexp/out/agentprocessbench-rq2-wilson/preflight/
```

It contains 24 files: visible projection and operation input; released risks;
ten real AgentProf count/risk profiles; assignments; pre-label group and
operation scores; score/profile audits; post-score labels; 200 shuffle rows;
1,000 compressed bootstrap rows plus header; summary; and generated Markdown
report.

These are ordinary calculation artifacts. They are not a freeze, manifest,
attestation, Git gate, or scientific verdict.

## Validity decision before independent review

The run satisfies every preflight completion condition:

- four families, 40 tasks, 200 trajectories, and 1,630 operations;
- real AgentProf for all five views;
- family-local score and vote accounting for every view;
- point scores materialized before human-label values;
- 200 exact matched shuffles;
- 1,000 valid cluster-bootstrap draws within 5,000 attempts;
- bit-exact prior mean-risk regression;
- terminal `VALID / PREFLIGHT_ONLY` status.

An independent reviewer must recalculate these facts and inspect the raw
artifacts. A `PASS` authorizes the exact FULL run without plan revision. Any
must-fix repairs only validity; it cannot tune the scientific construction.

## Independent REAL PREFLIGHT review

**Reviewed:** 2026-07-13T06:55:15-07:00

**Required skill:** `research-experiment-design`

**Reviewer mode:** independent, artifact-level, and read-only

**Verdict:** **PASS**

**Must-fix:** **zero**

The reviewer independently recalculated every requested artifact rather than
trusting `summary.json`. It confirmed:

- exact 40-task, 200-trajectory, 1,630-operation source selection and family
  counts;
- 32,600 released slots, 32,258 non-null votes, and 4,909 harmful votes;
- operation and risk-unit conservation for all five real AgentProf views;
- exact 4/115/178/200/1,630 family-local score groups;
- every group Wilson score and operation-score join;
- flat-per-family identity and absence of cross-family pooling;
- no human labels in pre-score artifacts and exact official coverage for all
  1,630 selected labels;
- bit-exact prior mean-risk regression and every atomic point metric;
- all 200 shuffle rows and size preservation, including 20 effects at least
  observed and `p = 21/201`;
- all 1,000 bootstrap rows, with attempt 460 the sole discarded draw, exact
  query multiplicities across all five rollouts, per-draw score recomputation,
  and exact reported intervals;
- focused 8/8 tests, including the zero-vote rule; no zero-vote group occurs in
  this selected subset;
- mechanical `VALID / PREFLIGHT_ONLY` status.

The reviewer did not edit files, use Git, touch the paper/submodule, or run the
FULL command. It explicitly rejected using any preflight value for tuning.

**Disposition:** the exact approved FULL command may proceed without plan
revision.
