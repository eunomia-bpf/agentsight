# Experiment Plan: RQ3 Tag Fidelity From Reused Public Traces

## Research Question

- Fixed paper question: **RQ3 — How Accurate Are the Tags?**
- Tested uncertainty: whether current AgentProf backends recover useful task
  and action-class partitions from visible trace text when scored against
  separate native annotations.
- This experiment does not change RQ3 or its positive hypothesis. It tests the
  task/action partition-fidelity components only; the completed Step 0006
  experiment remains the boundary component.

## Paper-Value Admission

- Planned role: decisive evidence for the independently scoreable task/action
  part of RQ3.
- Largest credible positive result: existing AgentProf tag backends recover
  useful task and action-class partitions on heterogeneous real public traces,
  and current AgentProf folds the predicted fields without losing attribution.
- Strongest reject argument: prior R283--R285 results sometimes compared
  adapter constants or fields produced by the same parser, so apparent
  agreement could be self-reconstruction rather than tag fidelity.
- This run isolates native references in scorer-only sidecars and uses only
  predictor text that is available independently of those reference fields.
- If one backend fails, the result bounds that tested backend; it does not
  change the RQ or authorize a weaker paper hypothesis.

## Reused Assets And Minimal New Glue

- Public data and converter: four already-supported sources through
  `script/agent_trace_datasets.py --include-text`.
- Task backend: unchanged target-blind TF-IDF/K-Means implementation in
  `agentpprof/backend/python/cluster_tagger.py`, including its fixed seed and
  existing automatic cluster-count selection.
- Action backend: unchanged `action_verb()` normalization in
  `script/agent_trace_datasets.py`.
- Scoring: unchanged operation-weighted V-measure implementation in
  `script/operation_stack_quality.py`.
- Profiling: current `agentpprof 0.2.37` operation-file path and the folding
  pattern already used by `script/operation_leaveout_eval.py`.
- One thin adapter, `script/operation_tag_accuracy_eval.py`, may only prepare
  IDs and scorer sidecars, invoke the existing backends and scorer, materialize
  `unmatched`, call AgentProf, and summarize outputs. It may not add a learner,
  parser, metric, cutoff, parameter sweep, or experiment protocol.

## Fixed Sources And Cells

Only sources with a potentially independent cell are recovered. The other five
R285 sources were already inspected in Round 1 and have no independently
scoreable task, phase, or action cell; downloading them again adds no evidence.

| Cell | Source prefix | Scorer-only reference | Visible predictor input | Existing backend |
|---|---|---|---|---|
| task/Mind2Web | complete available prefix, up to 100 rows, from `data/train/train_10.json` (currently 9) | native `row.domain` | one `confirmed_task` text per session | TF-IDF/K-Means |
| task/lclan ScienceWorld trajectory mirror | 100 `default/test` rows from `lclan/webshop_expert_trajectories` | native `info.task_name` | one native `question` per session | TF-IDF/K-Means |
| action/AndroidControl | 2 `default/train` rows | native `action.action_type` | corresponding `step_instructions` and non-reference text | `action_verb()` |
| action/GUI-Odyssey | 500 `default/all` rows | native `step.action` | corresponding `step.info` | `action_verb()` |

The lclan mirror's sampled `task_name` values identify ScienceWorld-style
tasks rather than WebShop shopping intents. Reports use the actual repository
and observed task family; the historical converter key `webshop-expert` is
only the command-line adapter name.

Mind2Web action is unavailable: `action_reprs` serializes the gold operation
suffix (for example, `-> CLICK`), while removing that suffix leaves input the
existing `action_verb()` cannot parse. No new parser is introduced. Phase is
unavailable across all nine R285 corpora because the current fields are copied
from action, derived from action, or adapter constants. WebLINX, API-Bank,
AgentTrek, SWE-agent trajectories, and ToolBench likewise have no independent
cell under the current adapters. These provenance conclusions are recorded as
availability results, not executed as empty experiment cells.

Before action prediction, one field-level source audit checks whether
AndroidControl `step_instructions` or GUI-Odyssey `step.info` directly
serializes its structured gold field. Ordinary natural-language action words
such as "click" or "open" are valid visible evidence. A structured copy of the
gold field makes that predeclared cell `unavailable`; it does not trigger a new
parser, replacement dataset, or experiment redesign.

## Reference Isolation And Prediction

For each eligible row the adapter:

1. assigns a non-semantic ID from dataset, session, turn, and source ordinal;
2. places the native reference in a scorer-only sidecar;
3. removes the reference and any direct structured copy from predictor input;
4. retains only the visible input named in the table;
5. joins prediction to reference by ID only after inference.

Task texts are deduplicated by session before clustering so trajectory length
does not affect fitting or automatic cluster selection. The resulting cluster
tag is then broadcast to all operations in that session. Because V-measure is
label-permutation invariant, these two cells test **task partition fidelity**,
not semantic cluster-name identity. The same interpretation applies to action
cells because the fixed primary metric is also label-permutation invariant.

Every operation in an available cell receives either a prediction or the
literal label `unmatched`. `unmatched` remains inside the V-measure counts;
coverage is reported separately and never conditions the primary score.
Prediction collapse is a valid result and never changes eligibility.

## Comparisons And Outcomes

- Proposed: the unchanged backend named for each cell.
- Simple control: one constant predicted tag over the same cell.
- Oracle: the scorer-only native field; it never enters prediction.
- Primary result: a four-cell vector of per-cell operation-weighted V-measure
  and coverage. Task and action cells are not averaged together.
- Correctness check: current AgentProf preserves row count and total operation
  weight for every predicted cell and their union.
- One deterministic complete run; no repeated seeds, tuning, cutoff, model,
  metric, or parameter sweep.

Expected result: useful agreement and high coverage in most available cells,
with exact AgentProf conservation. Alternative result: the current backend
over-partitions task text, action text lacks recoverable signal, or predictions
collapse to `unmatched`. Either is a valid result for the tested backend.

## Recovery And Execution

The exact full recovery commands are:

```bash
python3 script/agent_trace_datasets.py sample mind2web --limit 100 --config default --split train --repo-file data/train/train_10.json --include-text --out .agentsight/experiments/rq3-task-action-v1/inputs
python3 script/agent_trace_datasets.py sample webshop-expert --limit 100 --config default --split test --include-text --out .agentsight/experiments/rq3-task-action-v1/inputs
python3 script/agent_trace_datasets.py sample android-control --limit 2 --config default --split train --include-text --out .agentsight/experiments/rq3-task-action-v1/inputs
python3 script/agent_trace_datasets.py sample gui-odyssey --limit 500 --config default --split all --include-text --out .agentsight/experiments/rq3-task-action-v1/inputs
```

Preflight requests up to ten Mind2Web rows (the current file returns 9) and one
GUI-Odyssey trajectory so
the existing task-clustering and action-normalization paths both run end to end:

```bash
python3 script/agent_trace_datasets.py sample mind2web --limit 10 --config default --split train --repo-file data/train/train_10.json --include-text --out .agentsight/experiments/rq3-task-action-v1/preflight-inputs
python3 script/agent_trace_datasets.py sample gui-odyssey --limit 1 --config default --split all --include-text --out .agentsight/experiments/rq3-task-action-v1/preflight-inputs
python3 script/operation_tag_accuracy_eval.py --mode preflight --input-root .agentsight/experiments/rq3-task-action-v1/preflight-inputs --out-dir .agentsight/experiments/rq3-task-action-v1/preflight --agentpprof-manifest agentpprof/Cargo.toml
```

The full command is:

```bash
python3 script/operation_tag_accuracy_eval.py --mode full --input-root .agentsight/experiments/rq3-task-action-v1/inputs --out-dir .agentsight/experiments/rq3-task-action-v1/full --agentpprof-manifest agentpprof/Cargo.toml
```

Preflight is connectivity evidence only. Full completion requires all four
source attempts to terminate, the source-text leakage audit to finish before
action inference, every available cell plus its constant control to finish
with all rows retained, and each available profile plus the union to conserve
row count and weight. A source API change is recorded and the complete current
same-source prefix is run; it does not cause dataset substitution.

Raw data and machine results remain under `.agentsight/`. The experiment writes
one detailed Markdown report in this loop directory and, after independent
result review, only a compact admitted summary to `docs/evaluation.md`.

## Interpretation Boundaries

- Positive task scores support target-blind partition fidelity, not correct
  human-readable cluster names.
- Positive action scores support action-class partition fidelity for the
  existing normalization path only on independently audited visible text.
- Exact folding is an attribution-correctness check, not tag-accuracy evidence.
- No result from this experiment answers the unavailable phase component or
  replaces Step 0006's independently evaluated boundary component.
- A mixed or negative backend result returns to REVIEW for a materially better
  mechanism decision; it never changes the fixed RQ or paper hypothesis.
