# Diagnostic Lens Portfolio R345

R345 reuses tracked R335/R341/R344 artifacts to summarize which diagnostic lens helps each real labeled task. It does not fetch, sync, create, relabel, or rerank datasets.

## Verdict

- Overall: pass.
- Tasks: 6 across 4 datasets.
- Diagnostic lenses: 6 over 36 objective rows.
- Actionable task cards: 6/6.
- Best objective views: operation-stack family 11/36; non-operation-stack counterpoints 25/36.
- View diversity: 6/6 tasks need at least three best views across objectives.
- R344 metric surface: 30 support, 16 counterpoints, 4 mixed/weak.

## Lens Summary

| Objective | Lens | Best Views | Default Op-Stack | Interpretation |
|---|---|---|---:|---|
| ranking_fidelity_ap | ranked-stack table | {'dataset_native': 1, 'fixed_session': 2, 'operation_stack': 3} | 3/6 | Operation-stack query-aware is often the AP-faithful ranking view, but fixed-session and dataset-native remain task-specific counterpoints. |
| top5_localization_f1 | hot-stack table | {'dataset_native': 1, 'fixed_session': 1, 'flat': 1, 'operation_stack': 1, 'raw_action_stack': 2} | 1/6 | Hot-group F1 is the most fragmented lens: raw-action, dataset-native, fixed-session, flat, and operation-stack each win at least one task. |
| budget30_recall | budgeted inspection curve | {'dataset_native': 1, 'fixed_session': 1, 'operation_stack': 4} | 3/6 | Budgeted recall mostly favors operation stacks, but a width variant and dataset-native hierarchy win on boundary/safety tasks. |
| first_positive_work | first-positive drilldown | {'fixed_session': 2, 'operation_stack': 3, 'raw_action_stack': 1} | 2/6 | First-positive search is a drilldown counterpoint: fixed-session or raw-action can surface an example earlier even when operation stacks rank better overall. |
| groups_to_50pct | recall-fragmentation curve | {'dataset_native': 2, 'fixed_session': 1, 'raw_action_stack': 3} | 0/6 | Coverage at 50% positives often prefers raw-action or dataset-native groups, exposing mapping/depth tuning needs. |
| total_group_fragmentation | group-fragmentation overview | {'flat': 6} | 0/6 | Flat has the lowest group count by construction, so group count alone is a counterpoint metric, not a localization metric. |

## Task Cards

| Task | Views | Operation-Stack Objectives | Action | Counterpoints |
|---|---:|---|---|---|
| agentreward_looping | 4 | ['budget30_recall', 'ranking_fidelity_ap'] | Keep repeat_signal in the stack, but add prevalence-aware ranking because looping positives are common. | ['fixed_session_lower_work_to_first_positive', 'default_operation_stack_not_best_top5_f1'] |
| agentreward_side_effect | 3 | ['first_positive_work'] | Increase weight on write/input actions or use a deeper side-effect mapping before ranking. | ['raw_action_or_baseline_stack_beats_mapping', 'default_operation_stack_not_best_top5_f1'] |
| satraj_unsafe | 4 | ['top5_localization_f1'] | Use environment + phase + action stack fields; prioritize risky environments and write actions. | ['fixed_session_lower_work_to_first_positive', 'misleading_visible_feature'] |
| agentnet_incorrect_step | 3 | ['budget30_recall', 'first_positive_work', 'ranking_fidelity_ap'] | Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples. | ['raw_action_or_baseline_stack_beats_mapping', 'default_operation_stack_not_best_top5_f1'] |
| agentnet_redundant_step | 3 | ['budget30_recall', 'first_positive_work', 'ranking_fidelity_ap'] | Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples. | ['fixed_session_lower_work_to_first_positive', 'raw_action_or_baseline_stack_beats_mapping', 'default_operation_stack_not_best_top5_f1'] |
| osworld_group_start | 4 | ['budget30_recall'] | Use group-depth or boundary-derived fields for higher recall; action-depth alone fragments starts. | ['fixed_session_lower_work_to_first_positive', 'raw_action_or_baseline_stack_beats_mapping', 'misleading_visible_feature', 'default_operation_stack_not_best_top5_f1'] |

## Scope

R345 supports diagnostic-lens actionability: the profiler exposes which stack fields, rankers, mappings, and drilldowns to tune. It does not support human productivity, automatic boundary discovery, metric dominance, a universal selector, or full trace-ecosystem compatibility.
