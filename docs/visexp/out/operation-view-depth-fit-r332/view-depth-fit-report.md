# R332 View/Depth Task-Fit Audit

R332 audits whether a fixed hierarchy is enough, using only tracked R320 visible policy scores.
Hidden labels are used here only to score already-generated policies and to identify task-fit regret.

## Primary Findings

- Best visible AP is split across operation_stack, fixed_session, and dataset_native views ({'operation_stack': 3, 'fixed_session': 2, 'dataset_native': 1}); best top-5 F1 spans {'raw_action_stack': 2, 'dataset_native': 1, 'fixed_session': 1, 'flat': 1, 'operation_stack': 1}. No single hierarchy is the best visible choice across tasks and objectives.
- operation_stack:query_aware is the best visible AP policy on 3/6 tasks and best 30% budget-recall policy on 3/6 tasks, but it has large regret on side-effect and safety when another task-specific view is better.
- operation stacks reduce fragmentation relative to fixed-session query-aware on 4/6 tasks (median group ratio 0.5543), while fixed-session remains a first-positive counterpoint.
- Leave-task source selection does not solve view choice universally: selected-equals-best is 0/6 for AP and 0/6 for top-5 F1. This keeps view/depth choice as a task-aware analysis knob rather than a deployed universal selector.
- The supported design implication is to expose view, stack fields, predicates, and rankers as query-time configuration over the same operations; fixed session/span trees remain baselines, not profiler abstractions.

## Best Visible View Counts

| Metric | Best views | operation_stack:query_aware best tasks |
|---|---|---:|
| average_precision | {'operation_stack': 3, 'fixed_session': 2, 'dataset_native': 1} | 3/6 |
| top5_f1 | {'raw_action_stack': 2, 'dataset_native': 1, 'fixed_session': 1, 'flat': 1, 'operation_stack': 1} | 1/6 |
| budget30_recall | {'operation_stack': 4, 'fixed_session': 1, 'dataset_native': 1} | 3/6 |
| work_to_first_positive | {'operation_stack': 3, 'raw_action_stack': 1, 'fixed_session': 2} | 2/6 |

## Leave-Task Source Selection

| Metric | Selected equals best | Selected beats default | Median selected regret | Median default regret |
|---|---:|---:|---:|---:|
| average_precision | 0/6 | 1/6 | 0.0593 | 0.0045 |
| top5_f1 | 0/6 | 5/6 | 0.0106 | 0.0893 |
| budget30_recall | 3/6 | 0/6 | 0.0635 | 0.0635 |
| work_to_first_positive | 1/6 | 3/6 | 0.0318 | 0.0057 |

## Claim Boundary

- Supports: view/depth/ranker choice is an actionable query-time configuration over the same operations.
- Supports: fixed-session is a real baseline and first-positive counterpoint, while operation stacks reduce fragmentation on most tasks.
- Does not support: a universal label-free selector, one default stack for every task, or operation-stack dominance on every metric.
