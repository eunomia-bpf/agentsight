# R333 Inspection-Efficiency Frontier

R333 reruns the R320 local scorer over tracked operation JSONL inputs and emits full top-k / work-budget inspection curves. It does not fetch, sync, or create datasets.

## Primary Findings

- At <=30% inspected-work, operation_stack:query_aware has median recall 0.3900, versus flat:width 0.0000, fixed_session:query_aware 0.3559, dataset_native:query_aware 0.3377, and raw_action_stack:query_aware 0.3325.
- At <=20% inspected-work, operation_stack:query_aware has median recall 0.2763, versus fixed_session:query_aware 0.2422; the <=30% result is the clearer budgeted-recall point.
- Against flat:width, operation_stack:query_aware uses lower top-5 inspected work on 6/6 tasks and has positive recall under the 30% budget where flat has none.
- Against fixed_session:query_aware, operation_stack:query_aware has higher top-5 recall on 5/6 tasks and fewer groups on 4/6 tasks, but lower work-to-first-positive on only 2/6 tasks.
- Query-aware ranking is a real mechanism knob inside the same operation stack: compared with operation_stack:width, it improves AP on 6/6 tasks and budget30 recall on 5/6 tasks.

## Non-Claims

- no new datasets, dataset sync, or self-created evaluation sets
- no human or agent analyst productivity, accuracy, or time-to-answer claim
- no single-view dominance over every metric or task
- no automatic view selector or label-free deployment ranker
- no live eBPF overhead or complete trace-ecosystem compatibility claim
- no profiler abstraction beyond operation and operation stack

## Artifacts

- Report: `docs/visexp/out/operation-inspection-frontier-r333/inspection-frontier-report.json`
- Policy curve summary: `docs/visexp/out/operation-inspection-frontier-r333/policy-curve-summary.csv`
- Task policy curves: `docs/visexp/out/operation-inspection-frontier-r333/task-policy-curves.csv`
- Baseline comparisons: `docs/visexp/out/operation-inspection-frontier-r333/default-vs-baselines.csv`
