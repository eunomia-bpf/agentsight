# R344 Multi-Metric Consistency Audit

- overall: `pass`
- metric comparison rows: 50
- support verdicts: 30
- counterpoint verdicts: 16
- mixed/weak verdicts: 4

## Findings

### flat_work_budget_tradeoff

- status: `supports`
- evidence: Against flat summaries, operation-stack query-aware wins AP, budget30 recall/F1, top-5 work, and work-to-first-positive on 6/6 tasks.

### fixed_session_fragmentation_tradeoff

- status: `supports_with_work_counterpoint`
- evidence: Against fixed-session query-aware, operation-stack query-aware wins top-5 precision/recall/F1 and group count on most tasks, while top-5 work and work-to-first-positive remain fixed-session counterpoints.

### query_aware_over_width

- status: `supports`
- evidence: Against width-only operation-stack ranking, query-aware ranking wins AP on 6/6 tasks, budget30 recall/F1 on 5/6 tasks, and work-to-first-positive on 5/6 tasks.

### ndcg_is_not_headline_metric

- status: `counterpoint`
- evidence: nDCG is mixed across structured baselines and loses to flat on 6/6 tasks because flat has one all-task group; the paper should keep AP/work/fragmentation as the primary localization tradeoff and report nDCG as a secondary metric.

### topk_recall_is_fragmentation_sensitive

- status: `counterpoint`
- evidence: Top-5 recall/F1 can favor coarser flat or dataset-native groups, while inspection-budget recall and work metrics expose their higher inspection cost.

## Non-Claims

- R344 does not add a new ranking, dataset, or hidden-label selection procedure.
- R344 does not claim operation-stack dominates every metric or every baseline.
- R344 does not support human productivity, automatic boundary discovery, or a universal selector.
