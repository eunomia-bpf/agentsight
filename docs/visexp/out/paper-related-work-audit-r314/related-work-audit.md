# Paper Related Work Audit R314

R314 audits the current related-work and baseline grounding. It does not sync datasets or rerun profilers.

## Summary

- Overall: scoped_related_work_ready.
- Closest-work coverage: pass.
- Novelty delta: pass.
- Baseline grounding: pass.
- Guardrails: pass.
- R313 alignment: pass.
- Position: The paper is grounded against current trace-tree observability systems, classic folded-stack profilers, and public labeled agent-trajectory benchmarks, while preserving the scoped R313 inspectability-tradeoff claim.

## Closest Work Coverage

| Key | Status | Lines | Reason |
|---|---|---|---|
| classic_flamegraph_pprof | pass | 41, 42, 77, 83, 86, 93, 117, 175, 206, 265, 266, 301, ... (119 total) | Classic profilers are the folded-stack/profile lineage and include labels/tag pseudo-frame threats. |
| pprof_tags | pass | 42, 77, 86, 175, 643, 711, 826, 897, 954, 1210 | pprof tags and pseudo stack frames narrow the novelty away from query-time aggregation alone. |
| perfetto_sql | pass | 42, 76, 86, 94, 175, 641, 644, 711, 826, 898, 954, 1210 | Perfetto SQL and derived events narrow the novelty away from generic trace analysis. |
| opentelemetry_genai | pass | 35, 38, 40, 71, 72, 75, 85, 95, 96, 99, 139, 178, ... (29 total) | OpenTelemetry-style GenAI semantic conventions are the trace-schema threat. |
| openinference | pass | 38, 40, 72, 75, 85, 96, 99, 139, 179, 181, 652, 656, ... (20 total) | OpenInference is a current AI-observability semantic convention for spans. |
| langsmith | pass | 36, 73, 85, 86, 97, 126, 178, 653, 738, 826, 898, 1210 | LangSmith is a production LLM observability and evaluation platform. |
| langfuse | pass | 37, 74, 85, 86, 98, 126, 178, 653, 739, 826, 899, 1210 | Langfuse is an open LLM tracing, eval, and prompt-management platform. |
| phoenix | pass | 38, 72, 75, 85, 86, 96, 99, 126, 178, 179, 653, 656, ... (20 total) | Phoenix is an OpenTelemetry/OpenInference-based tracing/eval platform. |
| agentops | pass | 39, 43, 60, 85, 100, 178, 653, 741, 826, 899, 1210 | AgentOps is the closest agent-specific observability taxonomy/tooling threat. |
| public_labeled_trajectories | pass | 13, 16, 27, 28, 29, 31, 32, 33, 34, 43, 50, 53, ... (197 total) | The paper must distinguish itself from benchmarks that provide labeled trajectories. |

## Baseline Grounding

| Key | Status | Lines | Reason |
|---|---|---|---|
| dataset_native_sequence | pass | 83, 86, 87, 124, 179, 358, 564, 571, 594, 621, 832, 860, ... (18 total) | Reviewers will expect a comparison against the benchmark's native sequence view. |
| flat_action_summary | pass | 83, 86, 87, 127, 179, 241, 243, 245, 350, 358, 366, 420, ... (82 total) | Flat counting is the simplest aggregation baseline. |
| fixed_session_stack | pass | 83, 84, 85, 86, 87, 125, 177, 179, 232, 242, 243, 245, ... (117 total) | Fixed session or demo stacks test whether operation stacks add value. |
| fixed_session_span_tree_proxy | pass | 85, 86, 177, 179, 656, 814, 820, 826, 858, 940, 1067, 1140, ... (18 total) | LLM observability systems motivate a span-tree baseline, but current R320 evidence uses fixed-session as the proxy. |
| frontier_counterpoints | pass | 86, 87, 179, 243, 245, 350, 358, 437, 439, 440, 443, 446, ... (63 total) | R313 should preserve counterpoints instead of claiming dominance. |

## R313 Alignment

| Key | Expected text | Status | Lines |
|---|---|---|---|
| tasks | 6 | pass | 3, 6, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, ... (283 total) |
| datasets | 4 | pass | 3, 5, 18, 27, 28, 29, 30, 32, 35, 36, 37, 38, ... (282 total) |
| operations | 34,539 | pass | 241, 532, 619, 777, 814, 819, 821, 822, 825, 829, 832, 879, ... (30 total) |
| positive_operations | 3,699 | pass | 241, 619, 822, 825, 829, 832, 879, 940, 1005, 1133, 1136, 1140, ... (16 total) |
| candidate_points | 162 | pass | 243, 482, 777, 799, 825, 1136, 1181, 1209 |
| operation_stack_on_frontier | 6/6 | pass | 241, 243, 246, 440, 445, 446, 619, 621, 777, 820, 822, 823, ... (34 total) |
| operation_stack_best_lift | 4/6 | pass | 242, 243, 445, 777, 820, 822, 825, 1131, 1132, 1133, 1136, 1204, ... (14 total) |
| operation_stack_best_recall_under_30pct_work | 4/6 | pass | 242, 243, 445, 777, 820, 822, 825, 1131, 1132, 1133, 1136, 1204, ... (14 total) |
| flat_on_frontier | 6/6 | pass | 241, 243, 246, 440, 445, 446, 619, 621, 777, 820, 822, 823, ... (34 total) |
| fixed_session_on_frontier | 6/6 | pass | 241, 243, 246, 440, 445, 446, 619, 621, 777, 820, 822, 823, ... (34 total) |
