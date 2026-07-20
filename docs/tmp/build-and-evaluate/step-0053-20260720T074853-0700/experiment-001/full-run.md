# FULL RUN

## Status

**VALID / CONTRADICTED / NOT ADOPTED.** The fixed source-native adjacent-pair
classifier completed every planned trajectory and standard score. It did not
recover the author-verified workflow-stage partition better than the current
multi-resolution recurrence constructor.

This is a result about one flat boundary operator. It is not a result about the
paper thesis, the four fixed RQs, generated subtask names, recursive task depth,
diagnosis quality, or the desired task-semantic hierarchy.

## Commands

```bash
python3 script/rq3_source_native_task_progress_boundary_eval.py infer full \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18182 --workers 4 --timeout-seconds 600 \
  --out .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/full

python3 script/rq3_source_native_task_progress_boundary_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/full \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --out .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/score
```

## Complete Population And Isolation

- 405/405 source-valid trajectories, 251 tasks, 20,866 operations, and 20,461
  adjacent decisions completed;
- all 20,866 operations were retained exactly once;
- the five fixed source layouts contributed 71 MiniSWE, 118 OpenHands native,
  95 OpenHands maximal-history, 28 SWE-agent, and 93 Terminus2 trajectories;
- intent was available on 15,304 operations (73.34%), progress on 10,418
  (49.93%), and a uniquely attributable result on 13,143 (62.99%);
- the model saw only concrete task, native intent, native progress, source
  action, and uniquely attributable result;
- agent, model, session, status, phase, action-kind, human stage, and official
  manifest fields were unavailable to inference;
- Qwen2.5-3B-Instruct Q4_K_M made 20,461 deterministic calls using 33,560,944
  prompt tokens and 122,766 completion tokens; request sizes were 284--6,740
  tokens and wall time was 1,777.42 seconds.

## Prediction Behavior

The fixed policy emitted 19,856 `continue` decisions and 605 boundaries, a
2.9568% boundary rate. These decisions form 1,010 contiguous predicted groups,
versus 2,948 official stages. The candidate therefore under-segments rather
than repeating the earlier near-singleton failure.

## Standard Results

| Method | B-cubed P | B-cubed R | B-cubed F1 | Boundary F1 | Exact-span F1 |
|---|---:|---:|---:|---:|---:|
| source-native adjacent classifier | 0.253830 | 0.948235 | 0.400462 | 0.066074 | 0.012633 |
| multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

The candidate recovered only 104 of 2,543 true adjacent boundaries, with 501
false positives: boundary precision 0.171901 and recall 0.040897. Its high
B-cubed recall is the expected consequence of merging many human stages into
large predicted groups, not evidence of accurate task continuity.

The failure is visible in complete real cases, not only in the pooled metric.
For example, the 142-operation OpenHands `break-filter-js-from-html` trajectory
has 27 official stages but one candidate group; the 275-operation Terminus2
`git-multibranch` trajectory has 24 official stages but one candidate group.

Candidate B-cubed F1 by framework was 0.456258 on OpenHands, 0.350278 on
SWE-agent, 0.239609 on Terminus2, and 0.590726 on mini-SWE-agent. The current
multi-resolution recurrence was higher on every framework: 0.676295, 0.708893,
0.605471, and 0.691523 respectively.

Across 10,000 paired task-cluster bootstrap resamples, candidate minus
multi-resolution recurrence had mean -0.262088 and 95% interval
[-0.286562, -0.236752]; zero resamples were positive. The registered adoption
condition therefore fails decisively.

## Interpretation

The experiment changes the failure diagnosis, not the research goal. Real
per-step thoughts, progress records, actions, and results match the intended
task-semantic evidence contract; system-field grouping alone does not represent
task decomposition. But the tested memoryless adjacent-pair
`continue`/`boundary` policy does not maintain enough task state to determine
when a concrete subtask begins or ends. It strongly over-merges even when
source-native evidence is present. This run does not establish whether that
evidence is generally necessary or sufficient for a stateful constructor.

Therefore:

- do not adopt this classifier;
- do not render its groups as a positive task-semantic flamegraph;
- do not relabel tool, command, path, agent, session, or status stacks as task
  semantics;
- retain the intended main path exactly as `concrete task -> nested subtask ->
  phase/strategy -> semantic action -> operation object -> result`;
- treat system fields as metadata, filters, color, width, or source-linked
  detail only; and
- return the scientific decision to the outer loop rather than tuning another
  local prompt, grammar, cutoff, or post-hoc contraction.

## Raw Artifacts

- fixed inference and atomic session caches:
  `.agentsight/experiments/rq3-source-native-task-progress-boundary-v1/full/`
- standard score, per-operation rows, boundary rows, and bootstrap samples:
  `.agentsight/experiments/rq3-source-native-task-progress-boundary-v1/score/`
- human-readable scorer report:
  `.agentsight/experiments/rq3-source-native-task-progress-boundary-v1/score/report.md`
