# Real Preflight

## Verdict

**VALID WIRING; PROCEED TO THE REGISTERED FULL RUN.** The fixed evaluator ran
one complete real trajectory from each source layout, including a Terminus2
response turn containing seven commands. No source join, stack transition,
context, coverage, grammar, cache, or scorer error occurred. The model behavior
is scientifically concerning but is not a wiring failure and will not be used
to tune the frozen prompt.

## Commands

```bash
python3 script/rq3_stateful_native_turn_task_stack_eval.py infer preflight \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18182 --workers 4 --timeout-seconds 600 \
  --out .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/preflight

python3 script/rq3_stateful_native_turn_task_stack_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/preflight/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/preflight/inference-summary.json \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --prior-stateful-assignments .agentsight/experiments/rq3-qwen3b-semantic-task-stack-v2/full/score/operation-assignments.jsonl \
  --out .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/preflight-score
```

## Real Source Coverage

The five trajectories contain 100 operations in 84 native turns:

| Layout | Operations | Turns | Maximum operations in one turn |
|---|---:|---:|---:|
| MiniSWE messages | 20 | 20 | 1 |
| OpenHands native events | 20 | 20 | 1 |
| OpenHands maximal history | 20 | 20 | 1 |
| SWE-agent trajectory elements | 20 | 20 | 1 |
| Terminus2 response episodes | 20 | 4 | 7 |

All 100 operations received exactly one immutable-root-to-active-leaf path.
Inference saw the concrete task, complete active task labels, native
intent/progress, planned source action, and preceding-turn result. It did not
open official stages, baseline assignments, phase/action-kind, agent, model,
session, or status fields. The current turn's result was not visible to its own
transition.

## Fixed-Policy Behavior

The 84 legal transitions were 31 `push`, 38 `replace`, 15 `stay`, and no pure
`pop`, for a new-frame rate of 0.8214. Operation paths had depth 1--21 including
the immutable root. This is less degenerate than Step 0049's 0.9996 new-frame
rate, but it remains strongly over-segmented on this small diagnostic sample.

The clearest failure is the OpenHands maximal-history trajectory: missing
source-native intent and a carried progress list led Qwen to push generic
`phase-1`, `phase-2`, and `phase-3` labels on every turn, reaching depth 21.
These labels violate the semantic intent of the fixed task-frame instruction,
even though they satisfy the output grammar. Other cases produce more concrete
labels but frequently replace same-wording frames, so unique instance identity
still creates excessive groups.

The diagnostic score is ordinary B-cubed F1 0.5849 for the candidate versus
0.7152 for multi-resolution recurrence on these five trajectories. This score
is not an adoption result and did not alter the prompt, grammar, state transform,
population, metric, or interpretation rule. The registered full run is required
to determine whether this behavior persists across all 405 trajectories.

## Artifacts

- inference and per-session resumable caches:
  `.agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/preflight/`
- scorer rows, standard metrics, and bootstrap diagnostic:
  `.agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/preflight-score/`
