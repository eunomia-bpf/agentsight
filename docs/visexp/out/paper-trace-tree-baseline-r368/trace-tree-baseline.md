# R368 Trace-Tree Baseline Tradeoff Audit

- Status: `pass`.
- Checks: 10/10.
- This is an E2 paper-integration audit over existing R320/R355 hidden-label scoring outputs.
- It does not import real OpenTelemetry/Phoenix/LangSmith/Perfetto traces; fixed-session is the evaluated trace-tree-shaped baseline.

## Baseline Summary

| Policy | Role | AP | Top-5 work | Budget-30 recall | WTFP | Groups |
|---|---|---:|---:|---:|---:|---:|
| `operation_stack:query_aware` | proposed operation/operation-stack view | 0.3117 | 0.0937 | 0.39 | 0.0378 | 157.5 |
| `flat:width` | summary baseline | 0.1678 | 1.0 | 0.0 | 1.0 | 1.0 |
| `fixed_session:query_aware` | trace-tree-shaped baseline | 0.3476 | 0.0163 | 0.3559 | 0.0044 | 285.0 |
| `dataset_native:query_aware` | native hierarchy baseline | 0.3572 | 0.8539 | 0.3377 | 0.0582 | 7.5 |
| `raw_action_stack:query_aware` | action-tree baseline | 0.2744 | 0.1507 | 0.3325 | 0.0374 | 24.5 |

## Checks

| Check | Status | Evidence |
|---|---|---|
| `real_labeled_trace_scale_preserved` | pass | R320 covers 6 tasks / 4 datasets / 34,539 operations / 3,699 positives. |
| `span_tree_scope_is_fixed_session_proxy_not_ecosystem_claim` | pass | Paper text scopes the evaluated trace-tree-shaped baseline to fixed-session drilldown and leaves real ecosystem imports for future work. |
| `operation_stack_vs_fixed_session_fragmentation_tradeoff` | pass | Operation-stack beats fixed-session on top-5 recall/F1 for 5/6 tasks, budget-30 recall for 4/6, group count for 4/6, and median groups 157.5 vs 285.0. |
| `fixed_session_counterpoints_preserved` | pass | Fixed-session remains a counterpoint: it wins top-5 work and first-positive work on 4/6 tasks, with 0.0044 median WTFP. |
| `operation_stack_vs_flat_inspection_work_tradeoff` | pass | Operation-stack improves AP, budget-30 recall, and top-5 work on 6/6 tasks vs flat; median top-5 work is 0.0937 vs flat 1.0. |
| `dataset_native_tradeoff_preserved` | pass | Dataset-native hierarchy has fewer groups and broader top-5 recall, but operation-stack improves AP on 4/6, budget recall on 5/6, and top-5 work on 6/6. |
| `raw_action_stack_is_not_sufficient_baseline` | pass | Raw-action stacks are useful counterpoints but miss task-aware aggregation: operation-stack improves AP/budget recall on at least 4/6 while raw-action keeps some top-5 recall wins. |
| `oracle_depth_confirms_fixed_session_fragmentation_support` | pass | R355 confirms depth-aware support: 20/24 fixed-session unit-recall wins and 22/24 groups-to-50%-positive-unit wins. |
| `core_experiment_structure_remains_e1_e4` | pass | R361/R364/R367 keep this as E2 baseline evidence inside E1-E4, not a fifth core experiment. |
| `two_abstractions_and_no_new_data_policy_preserved` | pass | The audit reads tracked outputs only and preserves operation/operation-stack as the only profiler abstractions. |

## Non-Claims

- not a new profiler run
- not a new dataset, dataset sync, or relabeling step
- not a human or agent analyst study
- not a complete trace-ecosystem compatibility claim
- not a real OpenTelemetry/Phoenix/LangSmith/Perfetto span-tree import
- not metric dominance over every baseline and metric
