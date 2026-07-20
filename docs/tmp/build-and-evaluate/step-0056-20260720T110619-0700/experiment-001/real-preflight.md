# Real Preflight

## Verdict

**PASS.** One complete invariant-triggering trajectory from each source layout
completed exact-request prefix reuse, the causal state intervention, newly
inferred suffix turns, operation materialization, and standard scoring.

## Commands

```bash
python3 script/rq3_stateful_exact_leaf_invariant_eval.py infer preflight \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --original-cache-dir .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full/sessions \
  --llama-url http://127.0.0.1:18182 --workers 4 --timeout-seconds 600 \
  --out .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/preflight

python3 script/rq3_stateful_exact_leaf_invariant_eval.py score \
  --predictions .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/preflight/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/preflight/inference-summary.json \
  --step0054-score-rows .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/score/operation-score-rows.jsonl \
  --step0055-score-rows .agentsight/experiments/rq3-stateful-visible-path-identity-v1/full/operation-score-rows.jsonl \
  --out .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/preflight/score
```

## Coverage And Causal Checks

- five sessions and all five source layouts;
- 87 source-native turns, 104 operations, 99 adjacent pairs, 23 stage
  occurrences, and five task clusters;
- 22 Step 0054 responses reused only for byte-identical requests;
- 65 new model calls after the first state divergence;
- 34 exact same-leaf proposals applied as `stay`, affecting every preflight
  session;
- proposed counts: 35 push, 38 replace, 14 stay;
- applied counts: 27 push, 12 replace, 48 stay;
- no missing operation, invalid transition, reused nonidentical suffix, stack
  truncation, depth cap, or second rule; and
- maximum observed depth 16 with the unchanged prompt and model.

Preflight exact-visible-path B-cubed F1 is 0.677324 versus 0.586310 for the
unmodified policy and 0.685875 for recurrence. The causal mechanism interval is
positive on this five-task screen; candidate-minus-recurrence crosses zero.
These values diagnose the registered pipeline only. The intervention, prompt,
model, metrics, and stop rule remain unchanged for the complete run.
