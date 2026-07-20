# Real Preflight — Global Task-Semantic Segmentation

## Verdict

**PASS for execution, strong collapse warning for scientific behavior.** One
projected-token-longest complete trajectory from each of the four frameworks
completed source-only reconstruction, whole-trajectory model inference,
grammar validation, exact operation expansion, and the standard scorer. No
trajectory, turn, or operation was truncated.

The four valid responses nevertheless each emitted exactly one segment for the
entire trajectory. They generated variable subtask-path depths from one to six,
but none generated a task-progress boundary. The full run therefore proceeded
unchanged, as registered, to determine whether this was a four-trajectory
screening artifact rather than stopping on smoke behavior.

## Registered Interface Repairs Before The Final Preflight

The first executable attempts exposed interface defects rather than scientific
results:

1. redundant model-generated `start` and `end` values could disagree, so each
   non-final record now emits only `through`; starts and the final end are
   structural;
2. an unbounded `subtasks[]` was interpreted as a sequential plan and exhausted
   one completion budget, so the final fixed interface uses one
   parent-to-child `subtask_path` string;
3. the first 331 completed responses under that old interface all collapsed to
   one segment, so the final prompt explicitly rejects both whole-trajectory
   collapse and per-turn fragmentation; and
4. the parser initially imposed a 96-character limit on each parsed path frame
   despite allowing a 384-character path. That inconsistent parser-only limit
   was removed; no prompt, model, hypothesis, input, baseline, or metric
   changed.

These histories remain in ignored raw attempt directories. The version-2
preflight below is the final admitted prompt/schema version; no further prompt
variant is permitted.

## Commands

```bash
python3 script/rq3_global_task_semantic_segmentation_eval.py infer preflight \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --source-cache-dir .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/full/sessions \
  --turn-assignments .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/predictions.jsonl \
  --llama-url http://127.0.0.1:18183 --workers 1 --timeout-seconds 1200 \
  --out .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/preflight

python3 script/rq3_global_task_semantic_segmentation_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/preflight/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/preflight/inference-summary.json \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --causal-score-rows .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/score/operation-score-rows.jsonl \
  --out .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/preflight/score
```

## Coverage And Diagnostics

- four complete trajectories and all four frameworks;
- 584 source-native turns and 584 operations;
- exact context bounds on the native 32,768-token single-slot server;
- four model calls, 78,362 prompt tokens, and 282 completion tokens;
- every turn and operation covered exactly once;
- four emitted segments total, exactly one per session;
- subtask depths one, two, and six, with mean 2.5; and
- no frame exactly equals a reserved agent/model/session/tool/command/path/status
  word; the qualitative audit already exposes a command primitive (`ls -la`)
  in one semantic-action slot.

The preflight candidate reaches ordinary operation-level B-cubed F1 0.163439,
versus 0.530705 for multi-resolution recurrence and 0.633970 for the causal
online Qwen control. Its boundary and exact-span F1 are both zero because it
predicts no internal boundary. These are preflight diagnostics, not the
registered full-population result.
