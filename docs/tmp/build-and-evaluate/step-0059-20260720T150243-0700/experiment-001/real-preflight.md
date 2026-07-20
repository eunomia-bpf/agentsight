# Real Preflight

## Verdict

**PASS for wiring and full-run admission.** One complete trajectory from each
of the five source layouts passed through the actual Qwen2.5-3B endpoint,
three-transition parser, causal stack application, complete operation
materialization, and the registered standard scorer. No semantic behavior was
tuned after observing this screen.

## Commands

```bash
python3 script/rq3_well_nested_task_stack_eval.py infer preflight \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18181 --workers 5 --timeout-seconds 600 \
  --out .agentsight/experiments/rq3-well-nested-task-stack-v1/preflight

python3 script/rq3_well_nested_task_stack_eval.py score \
  --predictions .agentsight/experiments/rq3-well-nested-task-stack-v1/preflight/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-well-nested-task-stack-v1/preflight/inference-summary.json \
  --step0056-score-rows .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/score/operation-score-rows.jsonl \
  --out .agentsight/experiments/rq3-well-nested-task-stack-v1/preflight/score
```

## Coverage And Isolation

- five complete trajectories, all five source layouts, all four frameworks;
- 84 source-native turns, 100 operations, 95 adjacent pairs, 23 verified stage
  occurrences, and five task clusters;
- one valid transition per turn and one unique assignment per operation;
- 42 proposed pushes and 42 proposed stays; exact identity converted 17
  duplicate-leaf pushes to stays, yielding 25 pushes and 59 stays;
- the grammar exposed no `replace`, target depth, multi-level pop, depth cap,
  contraction, threshold, or alternate prompt; and
- human stages and recurrence assignments remained unopened until the 100
  candidate assignments were complete.

No pop occurred in this five-trajectory screen, so the pop branch is not
behaviorally exercised here. Its parser and application are mechanically
covered by the implementation audit; absence of a sampled model pop is a
diagnostic, not an added gate. The approved plan requires proceeding to all
405 trajectories rather than tuning or stopping on this observation.

## Diagnostic Metrics

The preflight candidate obtains ordinary B-cubed precision/recall/F1 of
`0.699952 / 0.684563 / 0.692172`. The same five trajectories score `0.715187`
for recurrence and `0.702453` for the Step 0056 contiguous-occurrence mechanism
baseline. The
candidate-minus-recurrence interval `[-0.147157, 0.117883]` crosses zero on
only five task clusters. These are wiring diagnostics only and do not change
the fixed controller or full-run obligation.

Depth naturally reaches 11 including the root. Every preflight session is
monotone because no pop was proposed. This records the observed controller
behavior without turning it into a separate pass/fail criterion.
