# R305 Cross-View Case-Packet Baseline

R305 compares the same label-hidden case-packet task across flat, fixed-session, and operation-stack views. Top-5 query-aware operation-stack packets inspect a median 9.4% of operations with lift 1.651. Flat packets recover 100.0% recall by inspecting 100.0% of operations, while fixed-session packets inspect 1.6% with lift 1.661. Operation stacks reduce work versus flat by a median ratio of 0.094 and improve lift versus fixed-session by a median ratio of 1.268.

## View Summary

| View | Tasks | Available groups | Selected groups | Work fraction | Recall | Precision | Lift | Lift>=1 tasks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| flat | 6 | 1.0 | 1.0 | 1.0 | 1.0 | 0.1678 | 1.0 | 6 |
| fixed_session | 6 | 285.0 | 5.0 | 0.0163 | 0.0226 | 0.2482 | 1.6615 | 5 |
| operation_stack | 6 | 157.5 | 5.0 | 0.0937 | 0.188 | 0.1991 | 1.6509 | 4 |

## Task-View Scores

| Task | View | Available groups | Work fraction | Recall | Precision | Lift |
|---|---|---:|---:|---:|---:|---:|
| agentreward_looping | flat | 1 | 1.0 | 1.0 | 0.6914 | 1.0 |
| agentreward_looping | fixed_session | 29 | 0.2058 | 0.2381 | 0.8 | 1.1571 |
| agentreward_looping | operation_stack | 40 | 0.4938 | 0.6508 | 0.9111 | 1.3179 |
| agentreward_side_effect | flat | 1 | 1.0 | 1.0 | 0.2771 | 1.0 |
| agentreward_side_effect | fixed_session | 29 | 0.1948 | 0.0 | 0.0 | 0.0 |
| agentreward_side_effect | operation_stack | 40 | 0.1454 | 0.1139 | 0.217 | 0.7831 |
| satraj_unsafe | flat | 1 | 1.0 | 1.0 | 0.1452 | 1.0 |
| satraj_unsafe | fixed_session | 250 | 0.0154 | 0.0579 | 0.5455 | 3.7577 |
| satraj_unsafe | operation_stack | 142 | 0.042 | 0.2621 | 0.9056 | 6.2384 |
| agentnet_incorrect_step | flat | 1 | 1.0 | 1.0 | 0.0594 | 1.0 |
| agentnet_incorrect_step | fixed_session | 835 | 0.0056 | 0.0126 | 0.1341 | 2.259 |
| agentnet_incorrect_step | operation_stack | 289 | 0.0014 | 0.0034 | 0.1429 | 2.4057 |
| agentnet_redundant_step | flat | 1 | 1.0 | 1.0 | 0.0728 | 1.0 |
| agentnet_redundant_step | fixed_session | 549 | 0.0086 | 0.0123 | 0.1034 | 1.4208 |
| agentnet_redundant_step | operation_stack | 260 | 0.0089 | 0.0177 | 0.1444 | 1.9838 |
| osworld_group_start | flat | 1 | 1.0 | 1.0 | 0.1905 | 1.0 |
| osworld_group_start | fixed_session | 320 | 0.0172 | 0.0327 | 0.3623 | 1.9022 |
| osworld_group_start | operation_stack | 173 | 0.4074 | 0.3874 | 0.1812 | 0.951 |

## Claim Scope

- Supports: operation-stack case packets provide a label-hidden middle ground between flat all-task packets and fixed-session fragmentation.
- Narrows: operation stacks do not dominate fixed-session packets on every task; this is an automated proxy, not a human study.
- Integrity: visible packet fields exclude hidden oracle labels; the answer key is separate.
