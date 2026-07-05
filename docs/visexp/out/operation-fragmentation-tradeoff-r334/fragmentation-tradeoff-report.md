# R334 Fragmentation Tradeoff Audit

R334 reads tracked R320 policy scores and R333 inspection curves to separate group fragmentation from operation-work cost. It does not fetch, sync, create, or relabel a dataset.

## Primary Findings

- Against fixed_session:query_aware, operation_stack:query_aware reduces total groups on 4/6 tasks and positive groups on 4/6 tasks; it reaches 50% positive recall with fewer ranked groups on 5/6 tasks (median delta -31.5 groups).
- At the same 30% inspected-work budget, operation_stack:query_aware inspects fewer groups than fixed_session:query_aware on 5/6 tasks (median delta -54.0 groups) while its median recall delta is 0.0275.
- The fixed-session result is a fragmentation result, not work dominance: operation_stack:query_aware has lower work-to-50%-recall on only 1/6 tasks, lower top-5 work on only 2/6 tasks, and lower work-to-first-positive on only 2/6 tasks.
- Against flat summaries, operation_stack:query_aware reaches 50% positive recall with median work 0.4314 instead of 1.0000, and top-5 work is lower on 6/6 tasks; flat remains a single coarse group, not a fragmentation win.
- Mapping and ranker choices remain mechanisms, not magic defaults: relative to raw_action_stack:query_aware, operation_stack:query_aware lowers work-to-50%-recall on 6/6 tasks; relative to dataset_native:query_aware, it improves 30%-budget recall on 5/6 tasks. Relative to operation_stack:width, query-aware ranking improves AP on 6/6 tasks and budget30 recall on 5/6 tasks, but reaches 50% positives with fewer groups on only 1/6 tasks.

## Non-Claims

- no new datasets, dataset sync, dataset creation, or relabeling
- no human or agent analyst productivity, accuracy, or time-to-answer claim
- no claim that operation stacks minimize every group-count or work metric
- no automatic view selector, universal boundary detector, or label-free deployed ranker
- no full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility claim
- no profiler abstraction beyond operation and operation stack

## Artifacts

- Report: `docs/visexp/out/operation-fragmentation-tradeoff-r334/fragmentation-tradeoff-report.json`
- Default comparisons: `docs/visexp/out/operation-fragmentation-tradeoff-r334/default-fragmentation-comparisons.csv`
- Budget comparisons: `docs/visexp/out/operation-fragmentation-tradeoff-r334/budget-fragmentation-comparisons.csv`
- Fixed-session task cases: `docs/visexp/out/operation-fragmentation-tradeoff-r334/fixed-session-fragmentation-cases.csv`
