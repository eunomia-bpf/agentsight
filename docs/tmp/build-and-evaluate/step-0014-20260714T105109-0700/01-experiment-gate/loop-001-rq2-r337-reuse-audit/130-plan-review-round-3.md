# Plan Review Round 3 — R337 Reuse Audit

## Review metadata

- **Review date:** `2026-07-14`
- **Plan reviewed:** `100-proposed-experiment-plan.md`
- **Prior reviews:** `110-plan-review-round-1.md` and
  `120-plan-review-round-2.md`
- **Review scope:** final independent check of one-RQ/one-hypothesis
  discipline, public inputs, six-task completion, baselines and measurements,
  label leakage, exact execution topology, simplicity, and absence of forbidden
  new experimental variables.
- **Implementation and evidence inspected:**
  `operation_inspection_frontier_eval.py`,
  `operation_inspection_target_eval.py`, `operation_profile_accuracy_eval.py`,
  `operation_query_utility_eval.py`, `operation_analyst_ranking_eval.py`, the
  four relevant converters in `agent_trace_datasets.py`, and the existing R320,
  R333, and R337 JSON/CSV/Markdown outputs.
- **Reviewer action:** this report only. No plan, code, paper, experiment, or
  publication change.

## Verdict

**PASS.** The revised plan is scientifically sufficient and executable for its
explicitly bounded purpose. It should proceed without another planning round
and without adding any dataset, model, annotation, partition, resample, metric,
human study, or custom audit code.

## Final scientific check

### One RQ and one tested hypothesis

The plan preserves RQ2 verbatim: **“Does Profiler Output Correspond to Real
Problems?”** It tests one aggregate operating-point hypothesis at the already
defined 25% positive-recall target: whether the existing
`operation_stack:query_aware` policy reaches all six tasks with lower median
inspection work and fewer median inspected groups than
`fixed_session:query_aware`.

The decision rule cannot answer all of RQ2. It cannot change the RQ, thesis,
story, positive paper hypothesis, policy, or recall target. Positive,
contradictory, and inconclusive outcomes produce different decisions about one
secondary RQ2 statement, so this is decision-relevant supporting evidence
rather than an activity-only replay.

The wording “across six tasks” is made operational by the explicit requirements
that both policies reach all six tasks, that medians satisfy both inequalities,
and that all six paired win/tie/loss results are reported. It therefore does
not silently substitute a pooled operation-level result for task-level
coverage.

### Real public inputs and complete scope

The four fixed operation files identify the declared public sources in their
rows:

- `McGill-NLP/agent-reward-bench`;
- `AI45Research/SATraj-OS`;
- `xlangai/AgentNet`; and
- `WukLab/osworld-human`.

The RQ2 task declaration creates exactly six labeled task slices: AgentReward
looping and side effect, SATraj safety, AgentNet incorrect and redundant step,
and OSWorld human group start. Existing R320 totals provide the expected
34,539 task-operation instances and 3,699 positive instances. Existing R333
outputs contain six tasks, four datasets, all six required visible policies,
and complete task-policy curves. The proposed full replay requires every task
and policy to terminate; a prefix or smoke subset cannot satisfy completion.

This is a legitimate reuse experiment. It neither downloads nor generates a
new dataset, and it makes no new agent/model call or human-label request.

### Baseline and measurement sufficiency

The baseline set is sufficient and no expansion is warranted:

- `fixed_session:query_aware` is the main competing organization because it
  retains the same query-aware ranker while replacing semantic recurring groups
  with execution/session groups;
- `raw_action_stack:query_aware` is the simple action-organization
  counterpoint; and
- `flat:width` exposes the compact one-group/full-inspection endpoint.

The emitted dataset-native and operation-width rows may remain context but do
not become additional success conditions. The plan correctly avoids a minimum
baseline count or a broad baseline collection exercise.

Positive recall, inspected operation mass, and inspected group count retain
their existing definitions. The 25% target is fixed before replay and is the
only hypothesis-bearing point; 10% and 50% are descriptive context. Work and
group count remain separate measurements, so the audit creates no Pareto score,
weighted aggregate, interpolation, matched-cardinality partition, metric
sweep, or post-result cutoff selection.

### Visible information and label leakage

The implementation boundary is adequate for this replay:

1. `operation_profile_accuracy_eval.py` forms profile groups before scoring
   them with `target_positive` and marks label-drilldown/oracle policies hidden.
2. `operation_analyst_ranking_eval.py` computes the query-aware rank from only
   `status`, `repeat_signal`, `phase`, `action`, and `environment` derived
   features. The task identity selects a fixed query-specific rule, but no
   target-positive values enter that rule.
3. AgentReward `repeat_signal`, AgentNet `repeat_signal`, SATraj
   `repeat_signal`, and OSWorld `repeat_signal` are derived from action/target
   signature repetition. They are not copied from looping, safety,
   step-correctness, redundancy, or human-group labels.
4. AgentReward looping/side-effect, SATraj safety, AgentNet
   correctness/redundancy, and OSWorld group-position remain distinct source
   label fields and are converted into `target_positive` only by the offline
   task loader.
5. `status` comes from task success/failure or source execution outcome rather
   than the selected target label. Correlation with a target is permitted;
   direct or derived use of the target oracle is not.

The revised plan explicitly requires this source-lineage check and records the
public source identifiers, closing the field-name-only gap identified in round
1. No relabeling or new leakage detector is needed.

## Final executability and simplicity check

The plan accurately describes the non-piped topology:

1. the preflight executes the real R337 target summarizer and its real fixed
   input/output path once;
2. the full R333 command reconstructs grouping, visible ranking, and inspection
   curves directly from the four public operation files using the existing R320
   implementation;
3. complete R333 scientific CSVs and selected scientific report fields are
   compared with the existing fixed artifacts; and
4. only after that equivalence check, the R337 command reconstructs the fixed
   target summaries and compares all three claim-bearing CSVs and selected
   report fields.

Both scripts expose the stated `--out-dir` interface, and all named output
files are produced by those interfaces. Standard `diff` and field-selecting
`jq` comparisons are enough. Runtime and commit/provenance fields are correctly
excluded from scientific equality. The plan does not pretend that the temporary
R333 directory is consumed by R337, and it does not run a redundant standalone
R320 replay.

The preflight is intentionally only an executability check. Scientific source
reconstruction belongs to the complete R333 run. That division is acceptable
because the two-command full run is local, deterministic, lightweight, and
must finish all six tasks before interpretation.

## Non-blocking implementation note

The inherited R333/R337 scripts contain legacy tracked-clean source checks and
record commit metadata. The plan correctly does not use those fields, old
`pass` booleans, or Git state as scientific evidence or as part of the
hypothesis decision. Their presence in reused code is not a reason to redesign
this experiment; scientific validity comes from public-source reconstruction,
label separation, complete output equivalence, and the fixed comparison rule.

## Execution instruction

Proceed exactly with the approved preflight and full-run commands. Do not add
another review round and do not broaden the experiment. Result review should
report separately:

- run validity and complete six-task reconstruction;
- supported, contradicted, or inconclusive tested hypothesis;
- supporting rather than decisive/new-independent research value; and
- the bounded RQ2 paper consequence permitted by the plan.

