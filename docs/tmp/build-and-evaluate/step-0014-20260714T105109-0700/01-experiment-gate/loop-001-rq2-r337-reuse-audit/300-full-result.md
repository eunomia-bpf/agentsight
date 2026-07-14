# FULL RESULT — R337 Reuse Audit

## Node metadata

- **Completed:** `2026-07-14T11:07:13-07:00`
- **Parent:** approved R337 reuse-audit plan and passing REAL PREFLIGHT
- **RQ:** Does Profiler Output Correspond to Real Problems?
- **Experiment:** one complete fixed-input equivalence audit over existing
  public-data evidence
- **Run validity:** VALID
- **Tested-hypothesis verdict:** SUPPORTED, with raw-action counterpoints
- **Research role:** supporting reconstruction of old evidence, not a new
  independent observation

## Complete commands

```bash
python3 script/operation_inspection_frontier_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/r333-replay
python3 script/operation_inspection_target_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/r337-replay
```

Both commands completed successfully. R333 processed all six task slices and
emitted 144 scored policies, 90 visible-policy rows, 36 grouped views, 810
inspection points, and 252 curve rows across four datasets. R337 processed all
six tasks, six existing policies, and the three existing recall targets. No
task, policy, or source stopped at a preflight or partial result.

## Scientific equivalence checks

The fresh R333 replay was compared with the existing R333 result before R337
was interpreted. The following complete scientific CSV files were byte-for-byte
identical:

- `core-policy-scores.csv`
- `task-policy-curves.csv`

The selected R333 report fields were also identical: `input_policy`,
`core_policies`, `work_grids`, `totals`, and `leakage_check`. Runtime, commit,
and other provenance metadata were deliberately excluded from scientific
equality.

After R333 equivalence passed, the fresh R337 replay was compared with the
existing fixed-input R337 result. These complete scientific CSV files were
byte-for-byte identical:

- `inspection-targets.csv`
- `policy-target-summary.csv`
- `default-target-comparisons.csv`

The selected R337 report fields were also identical: `input_policy`,
`default_policy`, `baseline_policies`, `recall_targets`, and `summary`.
Therefore every claim-bearing task row, reach status, work value, group count,
median, and win/tie/loss count used below is reconstructed exactly.

## Public source and label-separation audit

The replay reads the existing operation conversions from four public sources:

| Dataset family | Public source identifier | Target oracle field(s) | Visible-field origin |
|---|---|---|---|
| AgentRewardBench | `McGill-NLP/agent-reward-bench` | `looping`, `side_effect` | actions, adjacent action signatures, task outcome, benchmark metadata |
| SATraj-OS | `AI45Research/SATraj-OS` | `safety` | tool action/target, adjacent action signatures, execution result, environment metadata |
| AgentNet | `xlangai/AgentNet` | `step_correct`, `step_redundant` | action code/target, adjacent action signatures, task-level outcome, domain metadata |
| OSWorld-Human | `WukLab/osworld-human` | `group_position` | single actions, adjacent action signatures, feasibility/action outcome, application metadata |

`script/agent_trace_datasets.py` derives `repeat_signal` from adjacent
action/target signatures rather than from any target oracle. `phase`, `action`,
and `environment` are derived from actions and source metadata. `status` comes
from a separate task/execution outcome. The R333 leakage report confirms that
the visible rank features—`action`, `environment`, `phase`, `repeat_signal`,
and `status`—have zero field-name overlap with hidden target fields. The task
loader creates `target_positive` from each separate oracle only for scoring,
after visible groups and their order exist.

The fixed R320 source report identifies six tasks, four datasets, 34,539
task-operation instances, and 3,699 positives. The complete fresh R333 replay
reconstructed the six tasks, four datasets, all groupings/rankings, and all
claim-bearing inspection curves exactly from those same four operation files.

## Primary 25%-recall result

All four required policies reach the existing 25% positive-recall target on
all six tasks.

| Policy | Tasks reached | Median inspection work | Median groups inspected |
|---|---:|---:|---:|
| `operation_stack:query_aware` | 6/6 | 0.2000 | 16.0 |
| `fixed_session:query_aware` | 6/6 | 0.2495 | 50.0 |
| `raw_action_stack:query_aware` | 6/6 | 0.1993 | 13.0 |
| `flat:width` | 6/6 | 1.0000 | 1.0 |

Relative to fixed-session organization, operation stacks win/tie/lose
per-task inspection work on **4/1/1** tasks and inspected group count on
**5/0/1** tasks. The median paired differences
(`operation_stack - fixed_session`) are `-0.0731` work and `-37.5` groups.
Thus the operation-stack view achieves the tested recurring-versus-execution
comparison: lower typical operation work while traversing substantially fewer
groups than session fragmentation.

Relative to flat, operation stacks use less work on **6/6** tasks, while flat's
single group is necessarily less fragmented on **6/6**. Flat is therefore the
coarse/full-work endpoint rather than a defeated baseline.

Relative to raw action, operation stacks win/tie/lose work on **3/1/2** tasks
and groups on **2/0/4**. Raw action has slightly lower median work and group
count at this target. The replay therefore does not support a universal
semantic advantage or matched-granularity optimum. AgentProcessBench's
separate matched refinement control remains the semantic-specific evidence;
R337 supplies only the recurring-versus-session compactness operating point.

## Decision-rule application

The audit is VALID:

- the real public inputs and exact six task definitions are present;
- the visible/hidden field boundary and visible-field derivation were checked;
- fresh R333 claim-bearing outputs exactly match the old source-derived curves;
- fresh R337 claim-bearing outputs exactly match the old fixed-target rows; and
- all six tasks and all required policies completed.

The tested hypothesis is SUPPORTED because both main policies reach all six
tasks, operation stacks have strictly lower median work and strictly fewer
median groups than fixed-session organization, every paired outcome is
reported, and raw/flat counterpoints remain visible.

## Scientific interpretation and paper effect

The result supports one bounded secondary RQ2 statement: on six existing real
public labeled tasks at the existing 25%-recall point, an operation-stack view
reduces fixed-session fragmentation while retaining lower typical inspection
work; relative to flat it saves work, and relative to raw action it is mixed.
This makes the value of a recurring cross-run view more concrete than the
current table's uncontextualized session/step scores.

This is a current reconstruction of pre-existing evidence. It is not a new
independent test, does not change any previously observed workload verdict,
and does not by itself solve the larger novelty/decision-outcome objection.
It cannot be presented as a Pareto proof, universal dominance, human or agent
analyst productivity, automatic diagnosis, or downstream intervention.

## Contextual boundaries

The existing 10% and 50% rows were replayed because the unchanged R337 script
emits the full fixed target set, but they were not alternative success rules.
At higher recall, the operation-stack policy does not dominate all existing
views. No target, policy, mapping, ranker, or metric was changed after seeing
this outcome.

## Artifacts

- Preflight: `.agentsight/experiments/rq2-r337-reuse-audit-v1/preflight-r337/`
- Full R333 replay:
  `.agentsight/experiments/rq2-r337-reuse-audit-v1/r333-replay/`
- Full R337 replay:
  `.agentsight/experiments/rq2-r337-reuse-audit-v1/r337-replay/`

No new experiment code was written. The paper, story, RQs, shared skills, and
canonical submodule were not changed during this experiment.
