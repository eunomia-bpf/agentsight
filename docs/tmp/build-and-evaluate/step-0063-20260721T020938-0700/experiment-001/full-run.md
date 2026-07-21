# Full run — all consensus same-task pairs

Timestamp: 2026-07-21T02:19:00-07:00
Execution status: complete

## Command and immutable source

```bash
python3 script/agentreward_diff_pprof_eval.py \
  --dataset-root .agentsight/external/agentreward-full \
  --agentpprof agentpprof/target/debug/agentpprof \
  --out-dir .agentsight/experiments/agentreward-diff-pprof-v1/full-fixed
```

The source is the complete cleaned `McGill-NLP/agent-reward-bench` dataset at
revision `b6d17e646009d6cb63d5dd7be78807b680693f61`. Of 1,302 annotated
trajectories, 1,289 have annotator consensus on success. Thirteen conflicting
success labels were excluded, and no required source file was missing.

## Coverage

Canonicalizing only the published VisualWebArena `resized` suffix produced:

- 125 tasks with at least one consensus successful and one consensus
  unsuccessful trajectory;
- 440 real trajectories;
- 338 complete bad-good pairs;
- 7 AssistantBench, 51 VisualWebArena, 46 WebArena, and 21 WorkArena mixed
  tasks;
- 676 signed pprof files: operation-count and token-weighted for every pair.

All 676 files were read back by `go tool pprof -top`. There were zero parser,
profile-generation, or pprof-readback failures. The raw run is under
`.agentsight/experiments/agentreward-diff-pprof-v1/full-fixed/`; the two compact case
profiles are retained under `docs/visexp/out/agentreward-diff-pprof-v1/`.

## Standard evaluation statistics

The positive class for trajectory ROC AUC is unsuccessful. Pairwise accuracy
gives ties half credit and asks whether the unsuccessful member receives the
higher score.

| Trace-visible score | Pairwise accuracy | Trajectory ROC AUC |
|---|---:|---:|
| Step count | 0.7633 | 0.7517 |
| Total tokens | 0.6686 | 0.6987 |
| Error rate | 0.4941 | 0.5068 |
| Exact action-state repetition rate | 0.6657 | 0.6687 |
| Error-or-repeat non-progress rate | 0.6331 | 0.6331 |

Exact action-state repetition rate also obtains ROC AUC 0.7667 against the independent
human looping annotation across 435 trajectories with consensus looping labels.

The benchmark-stratified pairwise repeat-rate accuracies are 0.5833 on
AssistantBench, 0.6225 on VisualWebArena, 0.6840 on WebArena, and 0.7206 on
WorkArena. The corresponding non-progress rates are 0.5000, 0.5882, 0.6493,
and 0.7132.

## Interpretation

The broad run supports two bounded conclusions.

First, the signed pprof mechanism is operationally complete over a varied real
workload: every planned pair yields a standard tool-readable artifact with
positive bad-only/excess paths and negative good-only/excess paths. Second,
exact native-action repetition in an unchanged visible pre-action state is
meaningfully associated with the independently
annotated looping failure mode, so repeated task paths are a useful thing for a
user to inspect.

The run does **not** support selling the derived non-progress rate as a new
failure detector. A simpler step-count baseline is stronger overall, error rate
is near chance, and performance varies substantially by benchmark. More
importantly, the fixed case shows why profile paths remain useful even when all
scalar scores tie: the path names expose wrong-object work and different final
conclusions.

## Additivity and leakage checks

Actionless terminal observations are excluded before profiling. Each native
action enters one explicit task-semantic stack. Operation profiles use
unit weight; token profiles use the trace's reported input-plus-output tokens.
AgentPProf forms the signed value only after independently aggregating candidate
and base stacks. Success and looping annotations are absent from the operation
JSONL and pprof frames and enter only the evaluator.

The converter does not infer whether a conclusion is correct. Both
`report_infeasible` and `send_msg_to_user` are trace-visible conclusion paths;
the sign and child frames let the user compare them without placing the hidden
success oracle in the profile.

## Limitations recorded for review

- AgentRewardBench has outcome/loop labels, not a human gold semantic stack;
  this run cannot report stack-path localization accuracy.
- The broad accuracy/AUC values score trace-level features, not hierarchy or
  localization quality. Broad evidence for the pprof itself is operational
  coverage; localization usefulness remains the source-verified case study.
- Purpose phrases are deterministic and sparse but depend on available
  reasoning. Action-only traces fall back to strategy plus accessible object.
- Exact repetition requires the same native action, full URL, and pre-action
  accessibility-tree hash. It intentionally misses semantically equivalent
  recurrence when identifiers or visible state change.
- The 338 pairs reuse 440 trajectories across 125 tasks; pair statistics are
  descriptive and are not treated as independent significance samples.
- Fallbacks populated all six conceptual fields in this run. These results do
  not demonstrate recovery of arbitrary variable-depth task decompositions.
- Success discrimination is not the product contract. The profile is evidence
  for inspection; it does not automatically pronounce a trace good or bad.
