# Independent REAL PREFLIGHT Review — R337 Reuse Audit

## Review metadata

- **Reviewed:** `2026-07-14`
- **Approved plan:** `140-approved-experiment-plan.md` and the revised full
  plan in `100-proposed-experiment-plan.md`
- **Preflight report:** `200-real-preflight.md`
- **Raw preflight directory:**
  `.agentsight/experiments/rq2-r337-reuse-audit-v1/preflight-r337/`
- **Review action:** read-only inspection of the plan, implementation, report,
  public source samples, and generated output files; this report is the only
  file written
- **Git action:** none

## Verdict

**PASS.** The preflight executed the actual R337 inspection-target summarizer
over its real fixed R333/R336 input path and wrote the expected R337 artifacts.
The output contains all six tasks, the existing 25% recall target, and all four
policies required by the approved plan. One operation row from each of the four
public source files is valid JSON and contains the expected visible fields,
public source identifier, and separate target-label fields. No task, policy,
target, metric, model, source, or hypothesis changed.

This is a pass for **executability only**. It is not a scientific result and
does not establish the tested hypothesis, source reconstruction, label
separation, or a paper claim.

## 1. Actual R337 path executed

The reported command matches the approved REAL PREFLIGHT command:

```bash
python3 script/operation_inspection_target_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/preflight-r337
```

The implementation's `main()` loads the fixed R333 inspection report and
curves plus the fixed R336 recommendations, invokes the real target-row,
summary, best-policy, and comparison computations, and writes the requested
output directory. The preflight directory contains all outputs from that path:

- `inspection-target-report.json` and `inspection-target-report.md`;
- `inspection-targets.csv`;
- `policy-target-summary.csv`;
- `task-target-best.csv`;
- `default-target-comparisons.csv`;
- `run-result.json`; and
- the rendered `index.html`.

`run-result.json` records `run_id: R337`, `status: ok`, the exact preflight
output directory, four datasets, six tasks, six existing policies, three
existing recall targets, and 108 target rows. The eight generated files have
one contiguous write timestamp around `2026-07-14T11:02:49-07:00`, consistent
with one completed invocation. The three claim-bearing preflight CSVs are also
byte-identical to the corresponding tracked R337 CSVs; this is an
executability cross-check only, not a substitute for the approved full R333
source replay and equivalence audit.

## 2. Six tasks and existing targets

`inspection-targets.csv` contains exactly these six task names:

1. `agentreward_looping`
2. `agentreward_side_effect`
3. `satraj_unsafe`
4. `agentnet_incorrect_step`
5. `agentnet_redundant_step`
6. `osworld_group_start`

The only target values present are the three pre-existing values `0.10`,
`0.25`, and `0.50`. The approved hypothesis-bearing target `0.25` is therefore
present without adding or selecting a new cutoff after execution.

## 3. Four required policies at 25% recall

At `target_recall = 0.25`, each required policy has six rows covering six
unique tasks:

| Required policy | Rows | Unique tasks |
|---|---:|---:|
| `operation_stack:query_aware` | 6 | 6 |
| `fixed_session:query_aware` | 6 | 6 |
| `raw_action_stack:query_aware` | 6 | 6 |
| `flat:width` | 6 | 6 |

The two additional emitted policies, `dataset_native:query_aware` and
`operation_stack:width`, are the same existing contextual rows named by the
plan and R337 implementation. They do not enlarge the decision rule or create
new baselines.

The report's observed operation-stack values—6/6 tasks reached, median work
`0.2000`, and median 16 groups—are present in the raw summary. They are checked
here only as proof that the real metric path emitted populated rows. They are
not reviewed or authorized as final evidence at preflight.

## 4. Public source-row readability

I independently parsed the first operation row from every fixed public-data
JSONL file. Each row has the repository's `{fields, value}` schema. The nested
`fields` object contains `action`, `phase`, `repeat_signal`, `status`, and the
applicable `environment`, while the target annotations remain separately
named fields:

| Dataset | Public `source` | Visible sample | Separate target fields |
|---|---|---|---|
| AgentRewardBench | `McGill-NLP/agent-reward-bench` | `click`, `navigate`, `none`, `failure`, `webarena` | `looping`, `side_effect` |
| SATraj-OS | `AI45Research/SATraj-OS` | `type`, `input`, `loop-like`, `failure`, `account` | `safety` |
| AgentNet | `xlangai/AgentNet` | `click`, `navigate`, `none`, `failure`, `infeasible` | `step_correct`, `step_redundant` |
| OSWorld-Human | `WukLab/osworld-human` | `click`, `navigate`, `loop-like`, `gold`, `chrome` | `group_position` |

This confirms only that the approved public operation files and expected row
fields are readable. The preflight does not prove how all rows were converted
or whether hidden labels were excluded throughout grouping and ranking; the
approved full source-lineage and replay audit remains responsible for those
questions.

## 5. Scope and phase-boundary audit

The preflight introduced no new dataset, benchmark, model, label, task,
policy, recall target, metric, partition, interpolation, resample, custom
analysis script, or human dependency. It used the existing R337 command and
the approved dedicated output directory. The six-task scope, four required
comparisons, 25% tested point, RQ2, and tested hypothesis are unchanged.

`200-real-preflight.md` explicitly states that its PASS is for executability
only and that source reconstruction, label separation, CSV equivalence, the
tested hypothesis, and any paper claim remain unresolved until the full R333
and R337 replay. That boundary matches the approved plan and the REAL PREFLIGHT
contract.

## Next authorized action

Proceed to the approved complete R333 source replay and fixed-input
equivalence audit, followed by the complete R337 replay and independent result
review. Do not cite this preflight as experimental evidence and do not change
the experiment scope in response to its populated summary values.
