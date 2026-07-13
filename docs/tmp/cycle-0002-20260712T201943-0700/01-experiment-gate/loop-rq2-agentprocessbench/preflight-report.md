# AgentProcessBench RQ2 REAL PREFLIGHT report

**Executed:** 2026-07-13T05:40:00-07:00  
**Outer gate:** EXPERIMENT  
**Plan:** `experiment-plan.md`, Revision 3  
**Implementation review:** Round 2 PASS, zero must-fix  
**Execution status:** **VALID**  
**Scientific verdict:** **PREFLIGHT_ONLY**

## Purpose and boundary

This was the predeclared REAL PREFLIGHT, not a smoke test and not a paper-level
result. It exercised the complete source conversion, released-risk loader,
five real AgentProf views, post-profile human-label loader, scorer, 200 matched
shuffles, and 1,000 valid query-cluster bootstrap draws on the fixed first ten
query IDs of every family.

The run may validate or reject the implementation path. It cannot answer RQ2,
change the tested hypothesis, select a different field/metric/threshold, edit
the paper, or authorize a story change. Only the fixed complete-population run
can produce `SUPPORTED`, `CONTRADICTED`, or `INCONCLUSIVE`.

## Exact command

```bash
python3 script/agentprocessbench_profile_eval.py preflight \
  --source docs/visexp/out/agentprocessbench-rq2/source/official-repo \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentprocessbench-rq2/preflight \
  --query-limit 10 --permutations 200 --bootstraps 1000 \
  --max-bootstrap-attempts 5000 --seed 4204
```

The command exited successfully in approximately five seconds.

## Source, risk, and scorer accounting

The program first validated the complete official source before selecting the
preflight tasks:

| Item | Complete release | Preflight selection |
|---|---:|---:|
| Families | 4 | 4 |
| Tasks | 200 | 40 |
| Trajectories | 1,000 | 200 |
| Assistant-step operations | 8,509 | 1,630 |
| Released judge models | 20 | 20 |
| All-null judge steps | 3 | 0 |

The family operation counts were 619 BFCL, 342 GAIA dev, 122 HotpotQA, and
547 tau2. AgentProf's existing prompt clusterer selected seven intent tags over
all 200 task descriptions before the preflight selection.

All 8,509 human-label keys aligned with assistant-message identities. The
visible converter did not access their values. After all fixed profiles passed,
the separate scorer loader read exactly 8,509 global labels and selected the
same 1,630 preflight operation IDs. The same selected set had exactly one
released risk and one profile assignment per operation.

## Five real AgentProf views

The exact binary version was `agentpprof 0.2.37`. All views conserved exactly
1,630 operations and exactly 57,788,847,116 integer risk units globally and per
group:

| View | Groups | Operations exact | Risk exact | Per-group risk exact |
|---|---:|---|---|---|
| Flat | 1 | yes | yes | yes |
| Raw action | 99 | yes | yes | yes |
| Semantic | 162 | yes | yes | yes |
| Session | 200 | yes | yes | yes |
| Ungrouped risk | 1,630 | yes | yes | yes |

No profile view lost, duplicated, or changed an operation or released-risk
unit. The reversible `risk_units + 1` encoding correctly represented zero-risk
operations through AgentProf and subtracted the independently verified group
operation counts afterward.

## Preflight-only measurements

These values demonstrate that the metric and uncertainty paths execute. They
are not a scientific verdict and must not select a revision:

| Measurement | Point estimate | Preflight 95% interval |
|---|---:|---:|
| Semantic minus raw macro AP | +0.031876 | [+0.020244, +0.093052] |
| Raw minus semantic macro work-to-50 | +0.074912 | [+0.012308, +0.143509] |

The matched-shuffle diagnostic used all 200 fixed permutations. Its empirical
`p` was 0.124378 (24 shuffled deltas at least as large as the observed delta),
with exact group-size preservation in every permutation. This small-subset
diagnostic does not meet the full-run `p <= 0.05` support condition, but the
predeclared preflight verdict remains `PREFLIGHT_ONLY`; it does not justify
changing the hypothesis, stack, risk, control, or complete run.

The bootstrap retained exactly 1,000 valid paired draws after examining 1,001
draws and discarding one no-positive four-family draw. Every retained draw
sampled query IDs within family, kept all five rollouts, and recomputed group
mean risks over the resampled multiset.

Per-family outputs are fully present in the ignored machine summary. They show
expected heterogeneity rather than a join failure: semantic AP exceeds raw AP
in all four selected-family subsets; semantic work-to-50 is lower in GAIA dev,
HotpotQA, and tau2 but slightly higher in BFCL. No family value becomes an
additional pass condition or a construction revision.

## Artifacts

The complete ignored output directory is:

```text
docs/visexp/out/agentprocessbench-rq2/preflight/
```

It contains visible projection, released risks, count and risk AgentProf input
files, ten AgentProf profile JSON files, group assignments, post-profile human
labels, 200 shuffle rows, 1,000 compressed bootstrap rows, `summary.json`, and
the generated `report.md`. These are ordinary result artifacts, not contracts,
freezes, seals, manifests, or Git gates.

## Implementation disposition

The REAL PREFLIGHT found no source join, label boundary, risk alignment,
AgentProf assignment, conservation, shuffle, bootstrap, or completion defect.
No implementation or plan change is proposed from the measurements. Subject to
independent read-only preflight review, the next action is the exact Revision 3
FULL command over all 1,000 trajectories and 8,509 operations.

## Git note

The reviewed implementation was committed locally as `5406966b`. The push
attempt failed with the pre-existing remote HTTP 500/large-history problem.
This external Git failure is not an experiment condition and did not affect
the preflight inputs, execution, or disposition.

No paper, canonical submodule, story, RQ, positive hypothesis, or shared skill
was edited in this node.

## Independent REAL PREFLIGHT review

**Reviewed:** 2026-07-13T05:44:00-07:00  
**Required skill:** `research-experiment-design`  
**Verdict:** **PASS**  
**Must-fix before FULL:** **zero**  
**Material should-fix before FULL:** **none**

The reviewer independently recomputed all five AgentProf count and integer-risk
profiles, checked the complete source and selected-operation joins, confirmed
that human-label values load only after profile construction, inspected all 200
matched shuffles for within-raw-leaf size preservation, and counted exactly
1,000 valid bootstrap rows from 1,001 examined attempts. It also reran all nine
focused tests.

The reviewer confirmed that `VALID / PREFLIGHT_ONLY` is the only correct
disposition and that the subset shuffle `p` must not reject or revise the
complete run. The exact Revision 3 FULL command is authorized without an
implementation or plan change.
