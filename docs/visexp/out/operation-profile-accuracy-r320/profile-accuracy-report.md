# R320 Profile Accuracy and Actionability

R320 scores profiler outputs as ranked localization results on existing public labeled agent traces.
It does not fetch, sync, or create datasets; hidden labels are used only after ranking.

## Primary Findings

- Operation-stack query-aware profiling inspects median 9.37% of operations in top-5 groups, versus 100.00% for flat summaries.
- Against fixed-session query-aware drilldown, operation stacks improve top-5 recall on 5/6 tasks and reduce group fragmentation from median 285.0 to 157.5 groups.
- Mapping/tagging matters but is task-sensitive: operation stacks beat the raw action/status stack on top-5 F1 in 2/6 tasks.
- Query-aware visible ranking improves AP over width-only operation-stack ranking on 6/6 tasks; top-5 F1 and work still expose calibration and prevalence counterexamples.
- The Pareto analysis keeps operation stacks on the non-oracle frontier for 6/6 tasks; flat and fixed-session remain useful counterpoints rather than defeated baselines.

## Primary Accuracy Table

| Policy | Hidden? | AP | nDCG | P@5 | R@5 | F1@5 | Work@5 | Recall@30% | WTFP | Groups |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flat:width | False | 0.1678 | 1.0 | 0.1678 | 1.0 | 0.2868 | 1.0 | 0.0 | 1.0 | 1.0 |
| fixed_session:query_aware | False | 0.3476 | 0.7642 | 0.2555 | 0.0233 | 0.0427 | 0.0163 | 0.3559 | 0.0044 | 285.0 |
| dataset_native:query_aware | False | 0.3572 | 0.7445 | 0.1712 | 0.8665 | 0.2822 | 0.8539 | 0.3377 | 0.0582 | 7.5 |
| raw_action_stack:query_aware | False | 0.2744 | 0.5012 | 0.2513 | 0.2442 | 0.2195 | 0.1507 | 0.3325 | 0.0374 | 24.5 |
| operation_stack:width | False | 0.161 | 0.9364 | 0.1398 | 0.4746 | 0.2147 | 0.5424 | 0.3372 | 0.1694 | 157.5 |
| operation_stack:query_aware | False | 0.3117 | 0.5487 | 0.1991 | 0.188 | 0.1981 | 0.0937 | 0.39 | 0.0378 | 157.5 |
| operation_stack:oracle_upper_bound | True | 0.5993 | 0.6372 | 0.8984 | 0.3004 | 0.4029 | 0.0441 | 0.564 | 0.0122 | 157.5 |
| label_drilldown:oracle_upper_bound | True | 1.0 | 1.0 | 1.0 | 0.6703 | 0.7972 | 0.115 | 1.0 | 0.0377 | 86.5 |

## Actionable Optimization Insights

| Task | Best visible policy | Stack/ranker diagnosis | Optimization action |
|---|---|---|---|
| agentreward_looping | dataset_native:query_aware | fixed_session finds the first positive with less work; use it as drilldown; phase/repeat/environment mapping improves top-5 localization over raw action/status; query-aware visible ranking improves AP over flamegraph-width ranking; flat summary finds prevalent positives only by inspecting the whole task | Keep repeat_signal in the stack, but add prevalence-aware ranking because looping positives are common. |
| agentreward_side_effect | fixed_session:width | raw action/status beats the current mapped stack; tune stack depth for this query; query-aware visible ranking improves AP over flamegraph-width ranking; oracle upper bound leaves substantial ranker headroom; flat summary finds prevalent positives only by inspecting the whole task | Increase weight on write/input actions or use a deeper side-effect mapping before ranking. |
| satraj_unsafe | operation_stack:query_aware | operation_stack is the best visible top-5 F1 policy for this task; phase/repeat/environment mapping improves top-5 localization over raw action/status; query-aware visible ranking improves AP over flamegraph-width ranking; oracle upper bound leaves substantial ranker headroom; flat summary finds prevalent positives only by inspecting the whole task | Use environment + phase + action stack fields; prioritize risky environments and write actions. |
| agentnet_incorrect_step | raw_action_stack:width | mapping and raw action stack are close; ranker choice matters more than fields; flat summary finds prevalent positives only by inspecting the whole task | Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples. |
| agentnet_redundant_step | raw_action_stack:width | fixed_session finds the first positive with less work; use it as drilldown; raw action/status beats the current mapped stack; tune stack depth for this query; flat summary finds prevalent positives only by inspecting the whole task | Use desktop environment + phase + repeat/action fields, then drill into fixed sessions for examples. |
| osworld_group_start | flat:width | fixed_session finds the first positive with less work; use it as drilldown; mapping and raw action stack are close; ranker choice matters more than fields; oracle upper bound leaves substantial ranker headroom; flat summary finds prevalent positives only by inspecting the whole task | Use group-depth or boundary-derived fields for higher recall; action-depth alone fragments starts. |

## Claim Boundary

- Supports: profiler fidelity/localization, ranking quality, work tradeoffs, fragmentation reduction, and actionability on six real oracle-backed tasks from four public trace families.
- Supports as broader context: the repository already has 15 source conversions; R320 uses the four oracle-rich families as the main accuracy line.
- Does not support: human productivity, human or agent analyst time-to-answer, automatic discovery of all intent boundaries, or full trace-platform ecosystem compatibility.
