# R336 Actionability Selection Audit

R336 reuses tracked R320/R333/R334/R335 artifacts. It treats already-generated
visible profiles as policy choices and asks which policy is best for each
diagnostic objective. Hidden labels are used only for offline scoring.

## Primary Findings

- R336 scores 15 visible policies across 6 tasks and 6 diagnostic objectives without fetching, syncing, creating, or relabeling data.
- Best visible policy depends on the analysis objective: objective best views are budget30_recall: dataset_native=1, fixed_session=1, operation_stack=4; first_positive_work: fixed_session=2, operation_stack=3, raw_action_stack=1; groups_to_50pct: dataset_native=2, fixed_session=1, raw_action_stack=3; ranking_fidelity_ap: dataset_native=1, fixed_session=2, operation_stack=3; top5_localization_f1: dataset_native=1, fixed_session=1, flat=1, operation_stack=1, raw_action_stack=2; total_group_fragmentation: flat=6. This strengthens the design choice to expose view, stack fields, predicates, and rankers as query-time knobs over the same operations.
- operation_stack:query_aware remains a strong default: it is Pareto-frontier on 6/6 tasks, best AP on 3/6 tasks, best 30% budget recall on 3/6 tasks, and lower top-5 work than flat on 6/6 tasks.
- The fixed-session/span-tree proxy remains a real counterpoint: operation stacks improve top-5 recall over fixed-session on 5/6 tasks and reduce total groups on 4/6 tasks, but lower work-to-first-positive on only 2/6 tasks.
- Every task needs more than one best policy across the diagnostic objectives in 6/6 tasks. R336 therefore supports actionable optimization insight, not an automatic universal selector.

## Objective Best Policies

| Objective | Best view counts | operation_stack:query_aware best tasks |
|---|---|---:|
| ranking_fidelity_ap | dataset_native=1, fixed_session=2, operation_stack=3 | 3/6 |
| top5_localization_f1 | dataset_native=1, fixed_session=1, flat=1, operation_stack=1, raw_action_stack=2 | 1/6 |
| budget30_recall | dataset_native=1, fixed_session=1, operation_stack=4 | 3/6 |
| first_positive_work | fixed_session=2, operation_stack=3, raw_action_stack=1 | 2/6 |
| groups_to_50pct | dataset_native=2, fixed_session=1, raw_action_stack=3 | 0/6 |
| total_group_fragmentation | flat=6 | 0/6 |

## Pareto And Baseline Readout

- Pareto-frontier task counts: dataset_native:query_aware=6, fixed_session:query_aware=5, flat:width=6, operation_stack:query_aware=6, operation_stack:width=3, raw_action_stack:query_aware=6.
- Default-vs-baseline readout: budget30_recall_higher_than_flat=6, groups_lower_than_fixed=4, groups_to_50pct_lower_than_fixed=5, top5_recall_higher_than_fixed=5, top5_work_lower_than_flat=6, work_to_first_positive_lower_than_fixed=2.

## Non-Claims

- no new datasets, dataset sync, dataset creation, or relabeling
- no human or agent analyst productivity, accuracy, or time-to-answer claim
- no automatic universal policy selector
- no operation-stack dominance on every metric
- no profiler abstraction beyond operation and operation stack
