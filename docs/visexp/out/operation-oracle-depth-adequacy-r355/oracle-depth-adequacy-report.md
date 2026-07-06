# R355 Oracle-Depth Adequacy Audit

R355 extends R339 below session scope. It reuses tracked labeled operation JSONL and scores visible-ranked groups only after ranking.

## Summary

- Overall: `pass`.
- Tasks / datasets: 6 / 4.
- Accuracy unit-depth rows: 24.
- Subtask-eligible rows: 16.
- True subtask oracle rows: 5.
- Unit depths: `agentnet_step, agentreward_turn, operation, osworld_human_group, positive_run, satraj_step, session`.
- Default policy: `operation_stack:query_aware`.
- Median top-5 oracle-unit work across depths: 0.1307.
- Median budget-30 positive oracle-unit recall across depths: 0.4342.
- Median budget-30 positive-run recall: 0.4908.
- Median groups to 50% positive oracle units: 27.5.

## Paired Checks

| Check | Rows |
|---|---:|
| top5_unit_work_lt_flat_rows | 24/24 |
| budget30_unit_recall_gt_fixed_rows | 20/24 |
| budget30_unit_f1_gt_fixed_rows | 18/24 |
| groups_to_50pct_units_lt_fixed_rows | 22/24 |
| positive_units_per_group_lt_raw_rows | 24/24 |
| depth_gap_lt_fixed_rows | 0/24 |

## Task-Depth Cards

| Task | Depth | Best policy | OS budget-30 unit recall | OS groups to 50% units | Action |
|---|---|---|---:|---:|---|
| agentreward_looping | session | operation_stack:query_aware | 0.5294 | 2 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentreward_looping | operation | operation_stack:query_aware | 0.3988 | 3 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentreward_looping | positive_run | operation_stack:query_aware | 0.5513 | 2 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentreward_looping | agentreward_turn | operation_stack:query_aware | 0.4008 | 3 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentreward_side_effect | session | operation_stack:width | 1.0000 | 1 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentreward_side_effect | operation | raw_action_stack:query_aware | 0.3812 | 17 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentreward_side_effect | positive_run | operation_stack:width | 1.0000 | 1 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentreward_side_effect | agentreward_turn | raw_action_stack:query_aware | 0.8000 | 10 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| satraj_unsafe | session | dataset_native:query_aware | 1.0000 | 13 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| satraj_unsafe | operation | dataset_native:query_aware | 0.8376 | 38 | Preserve baseline counterpoint; operation-stack is an explanation view here. |
| satraj_unsafe | positive_run | dataset_native:query_aware | 1.0000 | 13 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| satraj_unsafe | satraj_step | dataset_native:query_aware | 0.8376 | 38 | Preserve baseline counterpoint; operation-stack is an explanation view here. |
| agentnet_incorrect_step | session | raw_action_stack:query_aware | 0.4084 | 186 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentnet_incorrect_step | operation | operation_stack:query_aware | 0.4382 | 186 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentnet_incorrect_step | positive_run | operation_stack:query_aware | 0.4302 | 186 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentnet_incorrect_step | agentnet_step | operation_stack:query_aware | 0.4382 | 186 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentnet_redundant_step | session | raw_action_stack:query_aware | 0.3539 | 157 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentnet_redundant_step | operation | operation_stack:query_aware | 0.3533 | 157 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentnet_redundant_step | positive_run | operation_stack:query_aware | 0.3535 | 157 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| agentnet_redundant_step | agentnet_step | operation_stack:query_aware | 0.3533 | 157 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| osworld_group_start | session | raw_action_stack:query_aware | 0.4180 | 11 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |
| osworld_group_start | operation | operation_stack:width | 0.2971 | 62 | Raw action has higher unit recall; use operation-stack to reduce broad action groups. |
| osworld_group_start | positive_run | operation_stack:width | 0.2971 | 62 | Raw action has higher unit recall; use operation-stack to reduce broad action groups. |
| osworld_group_start | osworld_human_group | raw_action_stack:query_aware | 0.5000 | 3 | Operation-stack improves oracle-unit recall over fixed-session for this depth. |

## Claim Boundary

On existing labeled traces, the profiler can be evaluated at the oracle depth provided by each dataset. Operation-stack rankings give a measurable depth-aware triage surface across session, operation/step, positive-run, and OSWorld human-group units, while preserving explicit baseline and oracle-depth counterpoints.

Counterpoints:
- session-level AgentRewardBench labels do not prove latent subtask boundaries
- positive-run units are a cross-dataset proxy, not human intent annotations
- AgentNet/SATraj step units are often operation-equivalent controls
- OSWorld human_group is the strongest true subtask oracle and remains boundary-field sensitive
- ScaleCUA history_depth is context-only in this tracked sample and excluded from accuracy claims
