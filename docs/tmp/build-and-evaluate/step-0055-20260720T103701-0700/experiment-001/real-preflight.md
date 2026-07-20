# Real Preflight

## Verdict

**PASS.** The score-only evaluator joined one complete real trajectory from
each of the five source layouts, reproduced fixed control fields, retained the
complete ordered visible path, and kept adjacent contraction secondary.

## Command

```bash
python3 script/rq3_stateful_visible_path_identity_eval.py preflight \
  --predictions .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full/predictions.jsonl \
  --step0054-score-rows .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/score/operation-score-rows.jsonl \
  --step0054-summary .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/score/summary.json \
  --out .agentsight/experiments/rq3-stateful-visible-path-identity-v1/preflight
```

## Coverage And Checks

- five complete trajectories, one per MiniSWE, SWE-agent, OpenHands native,
  OpenHands maximal-history, and Terminus2 source layout;
- 100 operations, 95 adjacent pairs, 23 verified session-local stage
  occurrences, and five task clusters;
- exact prediction/Step-0054-score-row key equality;
- hidden instance values reproduce the fixed prediction fields;
- every visible path is nonempty, ordered, depth-consistent, and ends in the
  recorded active leaf label;
- session is applied only as the occurrence-score namespace;
- exact global paths are counted without using them as an accuracy target; and
- no transition replay, model call, path tuning, fuzzy match, phase removal,
  depth rule, or system-field stack key occurs.

The preflight exact-visible path B-cubed F1 is 0.621656 versus 0.570217 for
hidden instance and 0.715187 for recurrence. The five-task construct-effect
interval is positive but wide; the visible-minus-recurrence interval crosses
zero. These small-preflight values diagnose wiring only and do not authorize
interpretation. The approved plan therefore proceeds unchanged to the complete
405-trajectory score.
