# Real preflight — VisualWebArena 512

Timestamp: 2026-07-21T02:16:00-07:00
Decision: admit the unchanged plan to the full run

## Inputs

The preflight used one real same-task pair from the fixed AgentRewardBench
revision. The task was: “List out reviewers, if exist, who mention `disgust`
for the purple product.” The unsuccessful candidate was the published Qwen
2.5-VL-72B trace and the successful base was the published Claude 3.7 Sonnet
trace. Both are `visualwebarena.resized.512`; neither trace was edited.

The exact preflight command was:

```bash
python3 script/agentreward_diff_pprof_eval.py \
  --dataset-root .agentsight/external/agentreward-full \
  --agentpprof agentpprof/target/debug/agentpprof \
  --out-dir .agentsight/experiments/agentreward-diff-pprof-v1/preflight-fixed \
  --case-only
```

## Pipeline checks

- Two trajectories and one bad-good pair were materialized.
- Both operation-count and token-weighted signed pprof files were generated.
- `go tool pprof -top` decoded both files without a custom renderer.
- Stack records contained task, derived subtask, strategy, native action,
  accessible object, and visible result. They did not contain success,
  looping, model, agent, or session labels.
- Outcome labels selected and paired the published trajectories, but stack
  construction itself consumed no outcome field.
- The adapter skipped the actionless terminal observation. Each case trace has
  the three native actions reported by `summary_info.n_steps`; no synthetic
  `action:unknown` frame or artificial token was added.

## User-visible localization

The two traces have the same native-action count and error rate, and the good trace
actually uses more tokens. Those aggregate counters do not tell the user what
went wrong. The differential pprof does:

- The candidate's positive path spends 5,098 tokens inspecting `Reviews (4)`
  on an Elmwood Inn orange-vanilla tea page and encounters a click timeout.
- A second candidate-positive conclusion calls `report_infeasible` after
  reasoning that no reviewer mentions the target term.
- The base-negative paths inspect `Reviews (12)` on the purple V8 +Energy
  product and call `send_msg_to_user` with reviewer Maria A. and the matching
  text.

The ordinary `go tool pprof` filters reproduce this distinction:

```bash
go tool pprof -top -focus='error|repeated|stopped' \
  docs/visexp/out/agentreward-diff-pprof-v1/visualwebarena-512-bad-minus-good.tokens.pb.gz

go tool pprof -top -focus='conclusion' \
  docs/visexp/out/agentreward-diff-pprof-v1/visualwebarena-512-bad-minus-good.tokens.pb.gz
```

Positive values belong to the bad candidate; negative values belong to the
good base. The tool reports the bad error path at `+328` net tokens because the
good trace also has an error-bearing review action, while the child object and
subtask frames separate `Reviews (4)` on the wrong product from `Reviews (12)`
on the correct one.

## Preflight judgment

The preflight does not show that a scalar failure score can classify this pair:
the simple scores tie or prefer the longer successful trace. It does show the
intended product value: the same ordinary pprof query localizes semantically
different work that aggregate counters hide. The exact parser, encoder, and
reader path succeeded, so the unchanged experiment proceeded to every eligible
pair.
