# Proposed Experiment Plan — R337 Reuse Audit

## Node metadata

- **Proposed:** `2026-07-14T10:51:09-07:00`
- **Parent:** R337 reuse-audit loop
- **Status:** proposed; requires three serial independent reviews
- **Experiment:** one complete replay/audit, not a new benchmark comparison

## Research question and tested hypothesis

**RQ2, verbatim:** Does Profiler Output Correspond to Real Problems?

**Tested hypothesis:** Across R337's six existing public labeled tasks, the
existing `operation_stack:query_aware` profile reaches the already-defined 25%
positive-recall target with lower per-operation inspection work and fewer
inspected groups than the existing `fixed_session:query_aware` organization,
while `raw_action_stack:query_aware` and `flat:width` remain explicit
counterpoints.

This experiment may judge only this tested hypothesis. It does not answer all
of RQ2 and cannot change the RQ, the fixed positive paper hypothesis, the
thesis, or the story.

## Why this is the highest-value simple experiment

The result already exists and directly addresses the current reviewer's
recurrence/fragmentation question. It uses real public labeled traces and
existing tested code. Reuse avoids a new dataset, model, labeling effort,
matched partition, interpolated cardinality, Pareto score, metric sweep, or
agent rerun. A new downstream intervention would have greater ultimate upside
but is a separate research program and is outside this node.

## Fixed inputs

The replay uses the repository's existing public-data operation sources:

- `docs/visexp/out/external-agent-trace-agentreward-r288/agentreward-operations.jsonl`
- `docs/visexp/out/external-agent-trace-satraj-r289/satraj-operations.jsonl`
- `docs/visexp/out/external-agent-trace-agentnet-r291/agentnet-operations.jsonl`
- `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl`

The existing code path is:

1. `script/operation_inspection_frontier_eval.py` imports the existing R320
   grouping/scoring implementation and reconstructs the six task/view
   groupings, visible-policy rankings, and per-task inspection curves directly
   from the four public operation sources.
2. `script/operation_inspection_target_eval.py` reads the existing R333 curves
   and extracts the already-defined 10%, 25%, and 50% fixed-recall points. Only
   the existing 25% point is the tested hypothesis here; 10% and 50% remain
   reported context, not alternative success criteria.

R337 also reads R336 recommendations for descriptive task-card fields. Those
recommendations do not determine work, group counts, target reach, or the
primary comparison, so R336 is not promoted into the causal evidence chain.

## Existing policies and measurements

No view, ranker, target, or measurement is added. The required visible rows are:

- `operation_stack:query_aware` — tested profile;
- `fixed_session:query_aware` — execution/session fragmentation baseline;
- `raw_action_stack:query_aware` — simple action organization counterpoint;
- `flat:width` — one-group compactness and full-work counterpoint.

The measurements retain their existing definitions:

- **positive recall:** cumulative labeled-positive operation mass recovered by
  the already-ranked groups;
- **inspection work:** cumulative operation mass inspected to reach the fixed
  recall point; lower is better;
- **groups inspected:** number of ranked groups traversed to reach that point;
  lower is less fragmented.

No cross-metric aggregate is computed. Work and group count are reported side
by side.

## Hidden-label and source audit

The audit must verify from code and replayed outputs that:

1. the four operation files exist and supply exactly the six declared task
   slices from AgentRewardBench, SATraj-OS, AgentNet, and OSWorld-Human;
2. visible ranking features are limited to the existing `status`,
   `repeat_signal`, `phase`, `action`, and `environment` fields;
3. `script/agent_trace_datasets.py` derives those visible fields from action
   signatures, actions, system/task outcomes, and source metadata rather than
   from the target oracle: `repeat_signal` comes from adjacent action
   signatures; AgentReward `looping`/`side_effect`, SATraj `safety`, AgentNet
   `step_correct`/`step_redundant`, and OSWorld `group_position` remain distinct
   label fields; the public `source` identifier in each operation row is also
   recorded;
4. hidden fields do not enter grouping or ranking and are read only after the
   ordered groups exist to score recall/precision;
5. the replay reconstructs six tasks, four datasets, 34,539 task-operation
   instances, and 3,699 positives before any paper use; and
6. all six 25%-recall task rows and the four required policies are present.

The old `pass` flags, commit strings, and readiness reports are not evidence.
Git cleanliness or hashes are not scientific pass conditions.

## REAL PREFLIGHT

Preflight is deliberately small and cannot authorize a result. It runs the
actual lightweight target-extraction path once:

```bash
python3 script/operation_inspection_target_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/preflight-r337
```

The preflight report must contain six tasks, the existing 25% target, and the
four required policies. It also confirms the four source files and upstream
artifacts are readable and inspects one source row per dataset. Passing this
preflight proves only that the real summarizer and output path execute; it does
not authorize the scientific result.

If preflight fails, repair only an invocation/path issue and repeat preflight.
Do not change a metric, policy, target, task, or hypothesis.

## FULL RUN

The full run is an equivalence audit over fixed inputs, not a directly piped
temporary chain. R333 accepts only an output directory and recomputes the R320
grouping/scoring implementation from the public operations. R337 also accepts
only an output directory and deliberately reads the repository's fixed R333
artifacts. The audit therefore first proves that a fresh R333 replay is
scientifically identical, then treats R337's fixed inputs as equivalent.

The exact full commands are:

```bash
python3 script/operation_inspection_frontier_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/r333-replay
python3 script/operation_inspection_target_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/r337-replay
```

No separate R320 replay is run because R333 already executes the required R320
grouping/scoring functions from the four public sources. The full audit then:

1. compares the complete replayed R333 `core-policy-scores.csv` and
   `task-policy-curves.csv` with the existing files, and compares the selected
   report fields `input_policy`, `core_policies`, `work_grids`, `totals`, and
   `leakage_check` while excluding elapsed time and commit metadata;
2. only after R333 equivalence passes, compares the complete replayed R337
   `inspection-targets.csv`, `policy-target-summary.csv`, and
   `default-target-comparisons.csv` with the existing files, plus the selected
   report fields `input_policy`, `default_policy`, `baseline_policies`,
   `recall_targets`, and `summary` while excluding runtime/provenance metadata;
3. records the source-derivation audit from `script/agent_trace_datasets.py`
   and the distinct public source identifiers in the operation rows; and
4. reconstructs the 25%-recall medians and per-task win/tie/loss counts for
   operation-stack versus fixed-session, raw-action, and flat from the replayed
   task rows.

The replay is complete only when all six tasks and all required policies reach
terminal outputs. It may not stop after a subset or smoke result.

The comparisons use standard `diff` for the scientific CSV files and `jq` to
select the named JSON fields. No custom audit script is created. Only after
fresh R333 equivalence passes may the R337 replay be treated as a reconstruction
of the old fixed-input evidence.

## Decision rule

The audit is **VALID** only if source/task counts, visible/hidden separation,
all six task rows, and all claim-bearing replay values reconstruct exactly.

The tested hypothesis is **SUPPORTED** only if, at the existing 25% recall
target:

- both operation-stack and fixed-session reach all six tasks;
- operation-stack median inspection work is strictly lower than fixed-session;
- operation-stack median groups inspected is strictly lower than fixed-session;
- the per-task work and group win/tie/loss counts are reported; and
- raw-action and flat comparisons are reported without a universal-dominance
  claim.

Otherwise the tested hypothesis is **INCONCLUSIVE** or **CONTRADICTED** as the
reconstructed rows dictate. Failure does not authorize changing RQ2, retuning
the 25% target, or selecting another policy/cutoff.

## Allowed conclusion

If valid and supported, the result may support one secondary RQ2 statement:
on these six public labeled tasks and the existing 25%-recall point, the
operation-stack view occupies a useful recurring-group operating point—less
inspection work than flat and fewer groups than fixed-session, with mixed
raw-action comparisons.

It may not be described as new independent evidence, a matched-granularity
proof, a Pareto optimum, universal semantic dominance, human/agent analyst
productivity, automatic diagnosis, downstream intervention, or the complete
answer to RQ2.

## Outputs

The gate records Markdown reports for plan reviews, preflight, full result,
independent result review, and gate exit. Machine-generated replay artifacts
remain under `.agentsight/experiments/` and are referenced from those reports.
The paper is not edited during EXPERIMENT.
