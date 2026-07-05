# R337 Inspection-Target Cost Audit

R337 reuses tracked R333 inspection curves and R336 actionability recommendations.
It computes the minimum visible inspection point needed to reach fixed positive-recall targets.
Hidden labels are used only through the already-scored R333 curves.

## Primary Findings

- At the 25% positive-recall target, operation_stack:query_aware reaches 6/6 tasks with median inspected work 0.2000 and median 16.0 groups. Flat reaches the same target only by inspecting median work 1.0000.
- At the same 25% target, fixed_session:query_aware also reaches 6/6 tasks but needs median 50.0 groups versus 16.0 for operation stacks; default has fewer groups on 5/6 tasks.
- At the 10% early-recall target, operation_stack:query_aware and fixed_session:query_aware both reach 6/6 tasks with about 10% work, but operation stacks use median 12.5 groups versus 37.5; default has fewer groups on 5/6 tasks.
- Compared with flat at the 25% target, operation_stack:query_aware has lower target work on 6/6 tasks, keeping the flat summary as a complete but expensive baseline.
- The 50% target is an explicit counterpoint: operation_stack:query_aware reaches 5/6 tasks and the best-work policies are dataset_native:query_aware=1, operation_stack:width=4, raw_action_stack:query_aware=1. This supports configurable stack/ranker choices rather than a universal default.

## Target Summary

| Policy | Target | Tasks reached | Median work | Median groups |
|---|---:|---:|---:|---:|
| fixed_session:query_aware | 0.1 | 6/6 | 0.0998 | 37.5 |
| fixed_session:query_aware | 0.25 | 6/6 | 0.2495 | 50.0 |
| fixed_session:query_aware | 0.5 | 6/6 | 0.4996 | 89.5 |
| flat:width | 0.1 | 6/6 | 1.0 | 1.0 |
| flat:width | 0.25 | 6/6 | 1.0 | 1.0 |
| flat:width | 0.5 | 6/6 | 1.0 | 1.0 |
| operation_stack:query_aware | 0.1 | 6/6 | 0.0988 | 12.5 |
| operation_stack:query_aware | 0.25 | 6/6 | 0.2 | 16.0 |
| operation_stack:query_aware | 0.5 | 5/6 | 0.4993 | 60.0 |

## Non-Claims

- no new datasets, dataset sync, dataset creation, or relabeling
- no human or agent analyst productivity, accuracy, or time-to-answer claim
- no automatic universal policy selector
- no operation-stack dominance on every recall target or task
- no live eBPF overhead or trace-ecosystem compatibility claim
- no profiler abstraction beyond operation and operation stack
