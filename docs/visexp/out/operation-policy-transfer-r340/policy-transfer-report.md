# Operation Policy Transfer Audit R340

R340 selects visible profile policies using only non-target tasks or non-target datasets, then scores the selected policy on the held-out task using already-scored R320/R339 metrics.

## Verdict

- Transfer decisions: 96.
- Exact held-out best selections: 31/96.
- Within-tolerance selections: 62/96.
- Operation-stack selected decisions: 16/96.
- Beats width baseline: 72/96.
- Beats fixed-session baseline: 69/96.

Supported wording: Selecting visible view/ranker policies from non-target tasks gives an auditable transfer signal: it often stays near the best visible held-out policy, but exact best policy selection remains task- and objective-specific.

Scope guardrails:
- does not use target hidden labels for policy selection
- does not prove an automatic universal selector
- does not make operation-stack query-aware the best policy for every objective
- does not replace task-specific actionability cards or fixed-session counterpoints

Must not claim:
- target hidden labels are used to select the transferred policy
- R340 proves an automatic universal selector
- operation-stack query-aware is the best policy for every objective
- task-specific actionability cards or fixed-session counterpoints are unnecessary

## Objective Summary

| Protocol | Objective | Decisions | Exact best | Within tolerance | Median target rank | Operation-stack selected |
|---|---|---:|---:|---:|---:|---:|
| leave_dataset | budget30_operation_recall | 6 | 2 | 2 | 6.0 | 3 |
| leave_dataset | first_positive_work | 6 | 1 | 3 | 2.5 | 4 |
| leave_dataset | groups_to_50pct | 6 | 3 | 6 | 1.5 | 0 |
| leave_dataset | ranking_fidelity_ap | 6 | 0 | 2 | 7.0 | 0 |
| leave_dataset | sequence_budget30_session_recall | 6 | 0 | 1 | 7.0 | 0 |
| leave_dataset | sequence_budget30_session_work | 6 | 6 | 6 | 1.0 | 0 |
| leave_dataset | sequence_top5_session_recall | 6 | 3 | 6 | 2.5 | 0 |
| leave_dataset | top5_localization_f1 | 6 | 0 | 4 | 5.0 | 0 |
| leave_task | budget30_operation_recall | 6 | 3 | 3 | 3.5 | 4 |
| leave_task | first_positive_work | 6 | 1 | 3 | 3.5 | 5 |
| leave_task | groups_to_50pct | 6 | 3 | 6 | 1.5 | 0 |
| leave_task | ranking_fidelity_ap | 6 | 0 | 2 | 7.0 | 0 |
| leave_task | sequence_budget30_session_recall | 6 | 0 | 2 | 6.5 | 0 |
| leave_task | sequence_budget30_session_work | 6 | 6 | 6 | 1.0 | 0 |
| leave_task | sequence_top5_session_recall | 6 | 3 | 6 | 2.5 | 0 |
| leave_task | top5_localization_f1 | 6 | 0 | 4 | 5.0 | 0 |

## Task Cards

| Protocol | Task | Dataset | Exact best | Within tolerance | Dominant selected view | Counterexamples |
|---|---|---|---:|---:|---|---|
| leave_dataset | agentnet_incorrect_step | agentnet | 4 | 7 | flat | sequence_budget30_session_recall->raw_action_stack:width rank 10 |
| leave_dataset | agentnet_redundant_step | agentnet | 5 | 7 | flat | sequence_budget30_session_recall->raw_action_stack:width rank 8 |
| leave_dataset | agentreward_looping | agent-reward-bench | 2 | 4 | flat | ranking_fidelity_ap->dataset_native:query_aware rank 5; budget30_operation_recall->dataset_native:query_aware rank 6; first_positive_work->fixed_session:query_aware rank 3 |
| leave_dataset | agentreward_side_effect | agent-reward-bench | 1 | 3 | flat | ranking_fidelity_ap->dataset_native:query_aware rank 2; top5_localization_f1->flat:query_aware rank 6; budget30_operation_recall->dataset_native:query_aware rank 8 |
| leave_dataset | osworld_group_start | osworld-human | 2 | 5 | flat | ranking_fidelity_ap->dataset_native:query_aware rank 8; budget30_operation_recall->operation_stack:query_aware rank 6; sequence_budget30_session_recall->raw_action_stack:visible_risk rank 6 |
| leave_dataset | satraj_unsafe | satraj-os-safety | 1 | 4 | flat | ranking_fidelity_ap->fixed_session:width rank 15; top5_localization_f1->raw_action_stack:width rank 9; budget30_operation_recall->fixed_session:width rank 12 |
| leave_task | agentnet_incorrect_step | agentnet | 4 | 7 | flat | sequence_budget30_session_recall->raw_action_stack:width rank 10 |
| leave_task | agentnet_redundant_step | agentnet | 5 | 7 | flat | sequence_budget30_session_recall->raw_action_stack:width rank 8 |
| leave_task | agentreward_looping | agent-reward-bench | 3 | 5 | flat | ranking_fidelity_ap->dataset_native:query_aware rank 5; first_positive_work->operation_stack:visible_risk rank 5; sequence_budget30_session_recall->raw_action_stack:query_aware rank 5 |
| leave_task | agentreward_side_effect | agent-reward-bench | 1 | 4 | flat | ranking_fidelity_ap->dataset_native:query_aware rank 2; top5_localization_f1->flat:query_aware rank 6; budget30_operation_recall->dataset_native:query_aware rank 8 |
| leave_task | osworld_group_start | osworld-human | 2 | 5 | flat | ranking_fidelity_ap->dataset_native:query_aware rank 8; budget30_operation_recall->operation_stack:query_aware rank 6; sequence_budget30_session_recall->raw_action_stack:visible_risk rank 6 |
| leave_task | satraj_unsafe | satraj-os-safety | 1 | 4 | flat | ranking_fidelity_ap->fixed_session:width rank 15; top5_localization_f1->raw_action_stack:width rank 9; budget30_operation_recall->fixed_session:width rank 12 |
