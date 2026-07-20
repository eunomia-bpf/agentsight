# REAL PREFLIGHT

## Status

**PASS.** The smallest complete trajectory from each of the five public source
layouts completed the actual source adapter, fixed Qwen3B inference, binary
grammar, atomic persistence, prediction materialization, official stage loader,
standard scorer, and paired task-cluster bootstrap path.

This preflight establishes executability only. Its metric values neither alter
the approved prompt nor answer RQ3.

## Commands

```bash
python3 script/rq3_source_native_task_progress_boundary_eval.py infer preflight \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18182 --workers 4 --timeout-seconds 600 \
  --out .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/preflight

python3 script/rq3_source_native_task_progress_boundary_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/preflight \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --out .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/preflight-score
```

## Real Coverage

- 5 complete sessions, one per source layout;
- 100 official operations and 95 adjacent decisions;
- MiniSWE messages, OpenHands native events, OpenHands maximal tool history,
  SWE-agent trajectory elements, and Terminus2 command/response episodes all
  completed their fixed evidence joins;
- source evidence: intent on 60 operations, progress on 40, uniquely
  attributable result on 76;
- 95/95 real Qwen calls completed, request range 368--3,562 tokens;
- all 100 operations were materialized exactly once;
- the inference process opened no official manifest or stage; and
- the separate scorer recovered 24 official stages across the five tasks and
  completed ordinary B-cubed, exact-span, exact-boundary, and 10,000 paired
  task-cluster resamples.

## Observed Policy Behavior

The fixed policy returned 95 `continue` decisions and zero boundaries on these
five trajectories. The resulting candidate equals a one-span-per-session
control on this preflight subset. This is a scientific observation, not a path
failure. No prompt, grammar, model, evidence projection, metric, baseline, or
decision rule changed after observing it. The approved mechanism proceeds
unchanged to the complete population.

## Raw Artifacts

- inference summary:
  `.agentsight/experiments/rq3-source-native-task-progress-boundary-v1/preflight/inference-summary.json`
- predictions and atomic session caches: the same `preflight/` directory;
- scorer report and machine summary:
  `.agentsight/experiments/rq3-source-native-task-progress-boundary-v1/preflight-score/`
