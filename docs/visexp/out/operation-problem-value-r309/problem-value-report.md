# R309 Operation Problem Value Synthesis

R309 synthesizes existing labeled-task evidence into reviewer-facing problem cards across 4 datasets, 6 tasks, and 34539 task-operations. Operation stacks are more selective than flat packets on all 6 tasks, contain high-lift evidence in 5/6 tasks, and have higher selected recall than fixed-session packets on 5/6 tasks. Fixed sessions remain cheaper on selected work in 4/6 tasks, so the paper claim remains an inspectability tradeoff rather than universal dominance.

## Summary

- Datasets: 4 (agent-reward-bench, agentnet, osworld-human, satraj-os-safety)
- Tasks: 6
- Task operations: 34539
- Operation-stack high-lift coverage: 5/6
- Operation-stack selected work/recall/top lift: 0.0937 / 0.188 / 1.5739

## Problem Cards

| Task | Dataset | Problem | Work | Recall | Lift | High-lift | Counterpoints |
|---|---|---|---:|---:|---:|---|---|
| agentnet_incorrect_step | agentnet | Find incorrect human desktop steps. | 0.0014 | 0.0034 | 2.4057 | true | low_selected_positive_recall |
| agentnet_redundant_step | agentnet | Find redundant human desktop steps. | 0.0089 | 0.0177 | 1.9838 | true | fixed_session_uses_less_selected_work, fixed_session_reaches_first_positive_earlier, low_selected_positive_recall |
| agentreward_looping | agent-reward-bench | Find repetitive web-agent behavior in expert-reviewed trajectories. | 0.4938 | 0.6508 | 1.3179 | false | fixed_session_uses_less_selected_work, fixed_session_reaches_first_positive_earlier, no_operation_stack_high_lift_group |
| agentreward_side_effect | agent-reward-bench | Find side-effectful web-agent trajectories. | 0.1454 | 0.1139 | 0.7831 | true | top5_packet_lift_below_prevalence |
| osworld_group_start | osworld-human | Find human grouped-action segment starts in desktop traces. | 0.4074 | 0.3874 | 0.951 | true | fixed_session_uses_less_selected_work, fixed_session_reaches_first_positive_earlier, top5_packet_lift_below_prevalence |
| satraj_unsafe | satraj-os-safety | Find unsafe desktop computer-use operations. | 0.042 | 0.2621 | 6.2384 | true | fixed_session_uses_less_selected_work, fixed_session_reaches_first_positive_earlier |

## Claim Scope

- Supports: operation stacks provide a configurable, two-abstraction way to inspect real labeled failure, safety, quality, and boundary tasks without collapsing to flat traces or hard-coding session boundaries.
- Narrows: fixed-session packets remain a strong low-work drilldown baseline, and some tasks need better ranking policies or analyst studies.
- Does not support: human accuracy/time improvement, automatic detection, universal dominance over fixed-session baselines, or complete trace-ecosystem compatibility.

## Source Artifacts

- `r298_value_novelty`: `docs/visexp/out/paper-value-novelty-r298/value-novelty-synthesis.json`
- `r300_query_utility`: `docs/visexp/out/operation-query-utility-r300/query-utility-report.json`
- `r302_ranking`: `docs/visexp/out/operation-analyst-ranking-r302/ranking-report.json`
- `r305_case_baseline`: `docs/visexp/out/operation-case-baseline-r305/case-baseline-report.json`
- `r308_analyst_outcome`: `docs/visexp/out/operation-analyst-outcome-r308/analyst-outcome-report.json`
