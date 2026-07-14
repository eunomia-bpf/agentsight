# Independent Result Review — R337 Reuse Audit

## Review metadata

- **Reviewed:** `2026-07-14`
- **Approved plan:** `140-approved-experiment-plan.md` and the complete revised
  plan in `100-proposed-experiment-plan.md`
- **Result under review:** `300-full-result.md`
- **Existing evidence:**
  `docs/visexp/out/operation-inspection-frontier-r333/` and
  `docs/visexp/out/operation-inspection-target-r337/`
- **Replay evidence:**
  `.agentsight/experiments/rq2-r337-reuse-audit-v1/r333-replay/` and
  `.agentsight/experiments/rq2-r337-reuse-audit-v1/r337-replay/`
- **Review action:** read-only inspection and independent recomputation; this
  Markdown report is the only file written

## Verdict

**PASS — no blocking result fix is required.** The two full commands reached
terminal outputs for the complete fixed scope. Fresh R333 output is
scientifically identical to the existing R333 output, and fresh R337 output is
scientifically identical to the existing R337 output. Direct recomputation
from the four operation files confirms six tasks, four datasets, 34,539
**task-operation instances**, and 3,699 positive task-operation instances.
All 24 required 25%-recall rows are present, and independent median and paired
win/tie/loss calculations reproduce the result report exactly.

The approved decision rule therefore returns **SUPPORTED** for the bounded
tested hypothesis. The research value remains **supporting reconstruction of
pre-existing evidence**, not a new independent observation and not the full
answer to RQ2.

## 1. Complete execution and scientific equivalence

Both replay directories contain a successful `run-result.json` and every
output emitted by the unchanged scripts. R333 reports six tasks, four
datasets, 144 scored policy rows, 90 visible-policy rows, 36 grouped views, 810
inspection points, and 252 task-policy curve rows. R337 reports six tasks, six
policies, three pre-existing recall targets, and 108 target rows. No task,
policy, dataset, or required target stopped at a preflight or partial prefix.

I compared every CSV emitted by each replay, not only the plan's minimum
claim-bearing subset:

| Replay | Complete CSV comparison | Result |
|---|---|---|
| R333 | `core-policy-scores.csv` | byte-identical |
| R333 | `task-policy-curves.csv` | byte-identical |
| R333 | `policy-curve-summary.csv` | byte-identical |
| R333 | `default-vs-baselines.csv` | byte-identical |
| R333 | `curve-win-summary.csv` | byte-identical |
| R337 | `inspection-targets.csv` | byte-identical |
| R337 | `policy-target-summary.csv` | byte-identical |
| R337 | `task-target-best.csv` | byte-identical |
| R337 | `default-target-comparisons.csv` | byte-identical |

The complete R333 JSON report differs only in `reproducibility.commit` and
`reproducibility.elapsed_seconds`. The complete R337 JSON report also differs
only in those two runtime/provenance fields. Consequently the named R333
fields (`input_policy`, `core_policies`, `work_grids`, `totals`, and
`leakage_check`) and named R337 fields (`input_policy`, `default_policy`,
`baseline_policies`, `recall_targets`, and `summary`) are identical, as are the
remaining scientific report fields.

This establishes the topology claimed in the result: R333 freshly reruns the
R320 grouping/scoring implementation over the public-data operation files;
R337 itself reads the fixed repository R333 files, but the preceding complete
R333 scientific equivalence makes those fixed inputs scientifically equivalent
to the replayed ones. The result does not falsely claim that temporary R333
output was piped into R337.

## 2. Task scope and fresh source-count recomputation

I independently invoked the existing `load_task_operations` function for each
declared task and summed the operation values and `target_positive` values
directly from the four input files. This is a fresh count, rather than a read
of the old R320 `totals` field:

| Task | Dataset | Oracle used only for scoring | Task operations | Positives |
|---|---|---|---:|---:|
| `agentreward_looping` | AgentRewardBench | `looping=yes` | 729 | 504 |
| `agentreward_side_effect` | AgentRewardBench | `side_effect=yes` | 729 | 202 |
| `satraj_unsafe` | SATraj-OS | `safety=unsafe` | 4,285 | 622 |
| `agentnet_incorrect_step` | AgentNet | `step_correct=incorrect` | 14,718 | 874 |
| `agentnet_redundant_step` | AgentNet | `step_redundant=redundant` | 10,067 | 733 |
| `osworld_group_start` | OSWorld-Human | `group_position=start`, exact alignment | 4,011 | 764 |
| **Total** | **4 datasets / 6 tasks** | | **34,539** | **3,699** |

The unique `source` field over each complete operation file is respectively
`McGill-NLP/agent-reward-bench`, `AI45Research/SATraj-OS`,
`xlangai/AgentNet`, and `WukLab/osworld-human`.

The phrase **task-operation instances** is essential. The 34,539 total is not
a claim of 34,539 unique converted source rows: the same AgentReward operations
support two different label queries, and the two AgentNet task slices overlap
after their task-specific unknown-label exclusions. `300-full-result.md`
already uses the correct phrase. The old R320 report alone would not have been
a fresh establishment of these numbers, but this independent source-file
recomputation closes the approved plan requirement without adding a dataset,
metric, or experiment.

## 3. Visible-input and target-oracle separation

The direct and derived leakage boundaries pass.

1. `operation_query_utility_eval.py` defines exactly the six task slices above.
   It reads the declared oracle field to create `target_positive` only in the
   offline task loader.
2. `operation_profile_accuracy_eval.py` forms each view before scoring it.
   `fixed_session`, `raw_action_stack`, and `operation_stack` contain no hidden
   label field. `label_drilldown` is marked hidden and excluded from the 90
   visible rows. `oracle_upper_bound` is also excluded from visible policies.
3. Visible query-aware ranking calls `operation_analyst_ranking_eval.py` and
   reads only features computed from `status`, `repeat_signal`, `phase`,
   `action`, and `environment`. Its deterministic task identity selects the
   query-specific visible rule, but per-row target values, positive counts,
   and hidden fields do not enter that score. For non-oracle ranking, tie
   breaking uses group width and group ID, not positive counts.
4. The converter derives `action` and `phase` from the action payload;
   `environment` from benchmark/domain/application metadata; and
   `repeat_signal` from adjacent action/target signatures. Specifically,
   `repeat_features_for_signatures` never reads looping, side-effect, safety,
   step-correctness, redundancy, or group-boundary labels.
5. AgentReward `status` comes from trajectory success, SATraj `status` from
   execution success, AgentNet `status` from task completion or termination,
   and OSWorld-Human `status` from infeasibility/fail actions. These are
   separate outcomes, not copies or transformations of the selected target
   oracle.
6. AgentReward `looping`/`side_effect`, SATraj `safety`, AgentNet
   `step_correct`/`step_redundant`, and OSWorld-Human `group_position` remain
   separately named hidden fields until offline scoring.

The fresh R333 leakage report lists the five visible fields, all hidden fields,
and an empty name overlap. The source-code lineage check above strengthens that
name check by confirming how every visible feature is derived.

This is not a held-out learned-ranker result: the fixed query-aware heuristics
are allowed to know which analyst question is being asked. What passes is the
approved narrower condition that they do not consume the answer labels. That
boundary is consistent with the tested hypothesis and prevents promotion to a
universal or label-free policy claim.

## 4. Independent 25%-recall recomputation

Filtering the replayed `inspection-targets.csv` to the four required policies
and `target_recall = 0.25` yields exactly 24 rows: six unique tasks for each
policy. Every row has `reached=True`.

### Recomputed policy summaries

| Policy | Reached | Per-task work | Median work | Per-task groups | Median groups |
|---|---:|---|---:|---|---:|
| `operation_stack:query_aware` | 6/6 | .2000, .2000, .1989, .2990, .2000, .0499 | **.2000** | 127, 36, 6, 19, 13, 12 | **16.0** |
| `fixed_session:query_aware` | 6/6 | .1998, .3000, .2990, .3951, .2000, .0999 | **.2495** | 186, 141, 10, 10, 62, 38 | **50.0** |
| `raw_action_stack:query_aware` | 6/6 | .1985, .2965, .3813, .0947, .2000, .0959 | **.19925** | 18, 21, 13, 5, 9, 13 | **13.0** |
| `flat:width` | 6/6 | 1, 1, 1, 1, 1, 1 | **1.0000** | 1, 1, 1, 1, 1, 1 | **1.0** |

The policy summary rounds raw action's median work to `.1993`, as expected.

### Recomputed paired comparisons

| Operation stack versus | Work W/T/L | Median work delta | Group W/T/L | Median group delta |
|---|---:|---:|---:|---:|
| fixed session | **4/1/1** | **-.07305** (`-.0731` reported) | **5/0/1** | **-37.5** |
| raw action | **3/1/2** | **-.0230** | **2/0/4** | **+9.0** |
| flat | **6/0/0** | **-.8000** | **0/0/6** | **+15.0** |

These independently computed values match
`default-target-comparisons.csv` and every number in `300-full-result.md`.
They also preserve the scientifically important counterpoints: raw action has
slightly lower median work and fewer median groups; flat has one group but
requires full inspection work.

## 5. Exact decision-rule audit

The approved validity conditions pass:

- the four source files reconstruct four datasets and exactly six task slices;
- fresh counts are 34,539 task-operation instances and 3,699 positives;
- source inspection and converter code establish the visible/hidden boundary;
- every required task/policy row is complete; and
- replayed scientific values reconstruct exactly.

The approved support conditions also pass:

- operation stack and fixed session both reach 6/6 tasks;
- `.2000 < .2495` for median inspection work;
- `16.0 < 50.0` for median groups inspected;
- complete paired work and group W/T/L results are reported; and
- raw-action and flat counterpoints are explicit, with no universal-dominance
  interpretation.

Therefore the exact plan verdict is **SUPPORTED**. No cutoff, policy, task,
mapping, ranker, or metric was changed in response to the replayed values.

## 6. Allowed paper consequence

The evidence authorizes only the planned secondary RQ2 consequence:

> On these six public labeled tasks, at the existing discrete 25%-recall
> operating point, the operation-stack view uses less typical inspection work
> and substantially fewer inspected groups than fixed-session organization;
> it uses less work than flat, while comparison with raw action is mixed.

For precision, paper prose should retain **these six tasks**, **the existing
25% target**, and the raw/flat counterpoints. “Minimum work” means the minimum
among the fixed R333 inspection-frontier points emitted by the unchanged
protocol, not a continuous optimum. The result does not authorize a Pareto or
matched-granularity proof, universal semantic dominance, held-out policy
generalization, human/agent analyst productivity, automatic diagnosis,
downstream intervention, or a complete RQ2 answer.

## Final judgments

```text
run status: valid
tested hypothesis: supported
research value: supporting
paper impact: additional bounded RQ2 evidence
next paper decision: writing may add the approved six-task, 25%-recall compactness statement with raw/flat counterpoints; no thesis, RQ, story, or headline-claim change is authorized
```

## Required fixes

**None.** The only reporting risk was treating the old R320 totals as a fresh
count. This review independently recomputed and documented 34,539/3,699 from
the actual task loader and operation files, so the complete Step 0014 evidence
now satisfies that approved requirement. Preserve the term
“task-operation instances” and the bounded consequence above in any later
writing step.
