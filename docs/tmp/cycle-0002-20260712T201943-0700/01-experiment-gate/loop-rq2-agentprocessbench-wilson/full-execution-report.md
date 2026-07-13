# AgentProcessBench Wilson FULL execution report

**Executed:** 2026-07-13T06:58:13-07:00

**Approved plan:** `experiment-plan.md`, Revision 3

**REAL PREFLIGHT review:** PASS, zero must-fix

**Execution status:** **VALID**

**Scientific verdict:** **INCONCLUSIVE**

## Verdict scope

This is the only scientific verdict for the second AgentProcessBench ranking
construction. It tests one positive construction hypothesis inside fixed RQ2.
It does not answer all of RQ2 and cannot change the author-fixed thesis,
canonical story, four RQs, or positive RQ2 hypothesis.

`INCONCLUSIVE` is not `CONTRADICTED`. The complete result contains positive
semantic-specific AP evidence, a favorable complete-population work point
estimate in all four families, and a stronger macro work point estimate than
the first construction. However, the predeclared paired work-to-50 interval
still crosses zero. Because the hypothesis and verdict were conjunctive, this
run cannot be called `SUPPORTED`.

The benchmark's human targets were already observed by the project after the
first run. This result therefore has the predeclared role **supporting adaptive
within-benchmark construction evidence**, not a fresh holdout or independent
external confirmation.

No result from this run has been inserted into the paper.

## Exact command and completion

```bash
python3 script/agentprocessbench_wilson_eval.py full \
  --source docs/visexp/out/agentprocessbench-rq2/source/official-repo \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentprocessbench-rq2-wilson/full \
  --permutations 200 --bootstraps 10000 \
  --max-bootstrap-attempts 50000 --seed 4204
```

The command exited successfully after approximately nineteen seconds. It met
every FULL completion condition:

| Item | Required | Observed |
|---|---:|---:|
| Families | 4 | 4 |
| Tasks | 200 | 200 |
| Trajectories | 1,000 | 1,000 |
| Assistant operations | 8,509 | 8,509 |
| Released judge models | 20 | 20 |
| Released prediction slots | 170,180 | 170,180 |
| Non-null released votes | report | 168,382 |
| All-null operations | 3 | 3 |
| Fixed result views | 5 | 5 |
| Matched shuffles | 200 | 200 |
| Valid query-cluster bootstraps | 10,000 | 10,000 |
| Maximum bootstrap attempts | 50,000 | 10,000 examined |

No FULL bootstrap draw lacked a harmful positive in any family, so zero draws
were discarded. All output artifacts use seed 4204.

## Complete source and label boundary

The official source remained commit
`0a42606b178a8c69d40c5765dc05c342f921e578`. Complete operation counts were:

| Family | Tasks | Trajectories | Operations |
|---|---:|---:|---:|
| BFCL | 50 | 250 | 2,590 |
| GAIA dev | 50 | 250 | 1,628 |
| HotpotQA | 50 | 250 | 734 |
| tau2 | 50 | 250 | 3,557 |
| **Total** | **200** | **1,000** | **8,509** |

The visible converter used task text, message roles, tool calls, tool returns,
and step order only. It created the same seven intent tags as the completed
first construction. The released-risk loader then joined exactly 20 official
judge slots to every operation.

Before the human-label loader ran, real AgentProf assignments and all five
family-local point-score views were materialized in:

```text
wilson-group-scores.jsonl
wilson-operation-scores.jsonl
wilson-score-report.json
```

Those files contain no human labels. The separate scorer then loaded exactly
8,509 human labels with complete operation-ID coverage.

## Real AgentProf and family-local vote accounting

The exact binary was `agentpprof 0.2.37`. Every real AgentProf view conserved
exactly 8,509 operations and 290,601,555,244 prior risk units globally and per
stack key:

| AgentProf view | Global stack keys | Operation exact | Risk exact |
|---|---:|---|---|
| Flat | 1 | yes | yes |
| Raw action | 259 | yes | yes |
| Semantic | 419 | yes | yes |
| Session | 1,000 | yes | yes |
| Ungrouped | 8,509 | yes | yes |

The approved scoring identity is `(family, AgentProf stack key)`. It prevents
same-looking keys in different benchmark families from pooling before the
equal-family macro. Every scored view independently conserved all 8,509
operations, 168,382 non-null votes, and 24,634 released harmful votes:

| Scored view | Family-local groups | Operations | Available votes | Harmful votes |
|---|---:|---:|---:|---:|
| Flat | 4 | 8,509 | 168,382 | 24,634 |
| Raw action | 280 | 8,509 | 168,382 | 24,634 |
| Semantic | 459 | 8,509 | 168,382 | 24,634 |
| Session | 1,000 | 8,509 | 168,382 | 24,634 |
| Ungrouped | 8,509 | 8,509 | 168,382 | 24,634 |

### Zero-vote paths

The three predeclared GAIA all-null operations are:

```text
gaia_dev:19:4:2  tool_call → fetch_url
gaia_dev:19:4:4  tool_call → read_file
gaia_dev:19:4:6  final_answer → final
```

They produce four zero-vote score groups:

- one three-operation session group, `session:gaia_dev:19:4`;
- three one-operation ungrouped groups, one for each operation ID.

All four receive the approved score zero. The operations remain in every
denominator and metric. Their raw and semantic groups contain other voted
operations and therefore do not take the zero-vote path.

## Co-primary complete results

The equal-family macro point estimates were:

| View | Macro AP | Recall@30 | Macro work-to-50 |
|---|---:|---:|---:|
| Raw action | 0.556443 | 0.357885 | 0.330628 |
| Semantic | 0.580959 | 0.425245 | 0.302977 |

The predeclared paired effects were:

| Effect | Point estimate | 95% percentile interval | Condition |
|---|---:|---:|---|
| Semantic minus raw AP | +0.024515 | [+0.016472, +0.051486] | favorable |
| Raw minus semantic work-to-50 | +0.027651 | [-0.026809, +0.080506] | crosses zero |

Semantic therefore has a complete-population AP improvement whose paired
interval is entirely positive. Its work-to-50 point estimate saves 2.77% of
all inspected operations on the equal-family macro, but the paired cluster
interval permits both a small adverse and a larger favorable effect.

## Per-family point estimates

All four families have positive AP and work point effects under the fixed
score:

| Family | Raw AP | Semantic AP | Delta AP | Raw work50 | Semantic work50 | Raw − semantic work50 |
|---|---:|---:|---:|---:|---:|---:|
| BFCL | 0.393528 | 0.409251 | +0.015723 | 0.327027 | 0.302703 | +0.024324 |
| GAIA dev | 0.761928 | 0.785689 | +0.023761 | 0.416462 | 0.360565 | +0.055897 |
| HotpotQA | 0.377831 | 0.397434 | +0.019603 | 0.348774 | 0.340599 | +0.008174 |
| tau2 | 0.692486 | 0.731460 | +0.038974 | 0.230250 | 0.208040 | +0.022210 |

These four point directions explain the complete-population result but do not
replace the predeclared task-cluster bootstrap. The uncertainty interval, not a
post-hoc four-family quota, determines the verdict.

## Matched semantic-specificity control

All 200 shuffles jointly permuted `(intent, phase)` only inside each family and
raw `(action, target, repeat_state)` leaf. Every shuffle preserved the observed
pair multiset and semantic subgroup-size multiset.

The observed macro AP effect was 0.024515. Shuffled effects ranged from
0.002754 to 0.019258, with median 0.011335. No shuffled effect equaled or
exceeded observed:

```text
p_shuffle_ap = (1 + 0) / 201 = 0.004975
```

The result therefore passes the fixed semantic-specificity condition. The AP
gain is not explained by matched refinement granularity alone under this
control.

Supporting shuffled work effects ranged from -0.008997 to +0.031330, with
median +0.015835. The observed +0.027651 work effect is toward the high end of
that distribution, but the plan did not make a second shuffle p-value a pass
condition.

## Supporting frontier and historical regression

Semantic improves macro recall at 30% inspection from 0.357885 to 0.425245.
Session grouping reaches AP 0.614636 and work-to-50 0.271273; the ungrouped
released-vote reference reaches AP 0.777081 and work-to-50 0.194498. These
reference views show remaining local-signal headroom but do not add verdict
conditions.

The historical mean-risk regression reproduced the entire first complete
construction exactly. Its two effects are bit-for-bit identical:

| Historical effect | Prior FULL | New regression path | Exact |
|---|---:|---:|---|
| Semantic minus raw AP | 0.03152190141708722 | 0.03152190141708722 | yes |
| Raw minus semantic work50 | 0.016320057727768567 | 0.016320057727768567 | yes |

The Wilson-shaped construction increases the favorable work point estimate
from 0.016320 to 0.027651 and makes HotpotQA favorable, while retaining a
semantic-specific AP gain. That mechanism-level improvement is real at the
complete-population point estimate, but it is not sufficient to move the
cluster interval entirely above zero.

## Paired bootstrap completion

All 10,000 requested paired query-cluster draws were valid; the evaluator
examined exactly 10,000 and discarded zero. Each draw sampled 50 task IDs with
replacement inside every family, kept all five rollouts together, and
recomputed group vote totals, Wilson scores, and complete-tier metrics for raw
and semantic views before equal-family aggregation.

The compressed artifact contains one header and all 10,000 effect rows. Fewer
than 10,000 valid rows would have made the run incomplete; that path did not
occur.

## Mechanical verdict

The approved plan requires all three conditions for `SUPPORTED`:

1. semantic-minus-raw AP interval lower bound above zero: **yes**;
2. raw-minus-semantic work-to-50 interval lower bound above zero: **no**;
3. matched-shuffle AP `p <= 0.05`: **yes**.

The plan assigns `CONTRADICTED` only if either complete paired interval is
entirely adverse. Neither is adverse. Therefore the only plan-consistent
verdict is **INCONCLUSIVE**.

## Artifact set

The complete ignored output is under:

```text
docs/visexp/out/agentprocessbench-rq2-wilson/full/
```

It contains 24 files: visible projection and operations; released risks; ten
real AgentProf count/risk profiles; assignments; pre-label family-local group
and operation scores; score/profile audits; post-score labels; 200 shuffle
rows; 10,000 compressed bootstrap rows plus header; summary; and generated
Markdown report.

These are ordinary calculation artifacts, not a freeze, manifest, attestation,
Git gate, or replacement for this Markdown report.

## Research disposition

This complete result remains in research history alongside the first complete
AgentProcessBench construction. It does not authorize a paper edit because the
predeclared conjunctive construction is not supported. It also does not
authorize narrowing RQ2, weakening the positive hypothesis, changing the
thesis/story, or inserting negative-result prose into the paper.

The plan predeclared this as the second and final target-reused
AgentProcessBench score construction. Therefore:

- do not design a third ranking variant on these already observed human labels;
- preserve both complete results and their positive AP/work point evidence;
- return to the outer WRITE/REVIEW decision after independent result review;
- use REVIEW to select a fresh external source or a different evidence
  mechanism for fixed RQ2, without narrowing the claim;
- keep `docs/paper/` and `docs/agentpprof-paper/` unchanged in this node.

An independent reviewer must now recalculate the complete source joins, scores,
zero-vote mappings, point metrics, all 200 shuffles, all 10,000 bootstrap rows,
intervals, and mechanical verdict. Only then may the outer experiment record
be updated.
