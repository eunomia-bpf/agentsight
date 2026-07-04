# Operation View Frontier R313

R313 reads existing R300/R302/R305/R311 artifacts only. It does not sync datasets or rerun profilers.

## Summary

- Tasks: 6 across 4 datasets.
- Operations: 34,539; positives: 3,699.
- Non-oracle candidate points: 162; frontier points: 76.
- Operation-stack on frontier: 6/6.
- Fixed-session on frontier: 6/6.
- Flat on frontier: 6/6.
- Operation-stack best lift: 4/6.
- Operation-stack best recall under 30% work: 4/6.

Interpretation: operation stacks are consistently nondominated, but fixed-session and flat views remain real counterpoints. The paper should claim a configurable inspectability tradeoff, not single-view dominance.

## Task Frontier Rows

| Task | Frontier views | Best lift | Best recall under 30% work | Interpretation |
|---|---|---|---|---|
| agentnet_incorrect_step | fixed_session, flat, operation_stack | operation_stack:case_query_aware:top_5_groups (work 0.0014, recall 0.0034, lift 2.4057) | operation_stack:query_aware:budget_30pct_operations (work 0.3, recall 0.4382, lift 1.4608) | operation-stack, fixed-session, and flat views are all nondominated, so this task needs a configurable view surface rather than a single hierarchy |
| agentnet_redundant_step | fixed_session, flat, operation_stack | operation_stack:case_query_aware:top_5_groups (work 0.0089, recall 0.0177, lift 1.9838) | operation_stack:query_aware:budget_30pct_operations (work 0.3, recall 0.3533, lift 1.1778) | operation-stack, fixed-session, and flat views are all nondominated, so this task needs a configurable view surface rather than a single hierarchy |
| agentreward_looping | fixed_session, flat, operation_stack | operation_stack:query_aware:budget_10pct_operations (work 0.0988, recall 0.1429, lift 1.4464) | operation_stack:query_aware:budget_30pct_operations (work 0.299, recall 0.3988, lift 1.3336) | operation-stack, fixed-session, and flat views are all nondominated, so this task needs a configurable view surface rather than a single hierarchy |
| agentreward_side_effect | fixed_session, flat, operation_stack | fixed_session:width:budget_30pct_operations (work 0.299, recall 1.0, lift 3.344) | fixed_session:width:budget_30pct_operations (work 0.299, recall 1.0, lift 3.344) | operation-stack, fixed-session, and flat views are all nondominated, so this task needs a configurable view surface rather than a single hierarchy |
| osworld_group_start | fixed_session, flat, operation_stack | fixed_session:visible_risk:top_10_groups (work 0.0274, recall 0.055, lift 2.0045) | operation_stack:width:budget_30pct_operations (work 0.2999, recall 0.4241, lift 1.414) | operation-stack, fixed-session, and flat views are all nondominated, so this task needs a configurable view surface rather than a single hierarchy |
| satraj_unsafe | fixed_session, flat, operation_stack | operation_stack:case_query_aware:top_5_groups (work 0.042, recall 0.2621, lift 6.2384) | fixed_session:query_aware:budget_30pct_operations (work 0.2999, recall 0.865, lift 2.8843) | operation-stack, fixed-session, and flat views are all nondominated, so this task needs a configurable view surface rather than a single hierarchy |
