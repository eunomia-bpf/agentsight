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
| classic_flamegraph_pprof | pass | 41, 42, 77, 83, 86, 93, 117, 175, 206, 265, 266, 302, ... (129 total) | Classic profilers are the folded-stack/profile lineage and include labels/tag pseudo-frame threats. |
| pprof_tags | pass | 42, 77, 86, 175, 650, 718, 833, 907, 964, 1234 | pprof tags and pseudo stack frames narrow the novelty away from query-time aggregation alone. |
| perfetto_sql | pass | 42, 76, 86, 94, 175, 648, 651, 718, 833, 908, 964, 1234 | Perfetto SQL and derived events narrow the novelty away from generic trace analysis. |
| opentelemetry_genai | pass | 35, 38, 40, 71, 72, 75, 85, 95, 96, 99, 139, 178, ... (29 total) | OpenTelemetry-style GenAI semantic conventions are the trace-schema threat. |
| openinference | pass | 38, 40, 72, 75, 85, 96, 99, 139, 179, 181, 659, 663, ... (20 total) | OpenInference is a current AI-observability semantic convention for spans. |
| langsmith | pass | 36, 73, 85, 86, 97, 126, 178, 660, 745, 833, 908, 1234 | LangSmith is a production LLM observability and evaluation platform. |
| langfuse | pass | 37, 74, 85, 86, 98, 126, 178, 660, 746, 833, 909, 1234 | Langfuse is an open LLM tracing, eval, and prompt-management platform. |
| phoenix | pass | 38, 72, 75, 85, 86, 96, 99, 126, 178, 179, 660, 663, ... (20 total) | Phoenix is an OpenTelemetry/OpenInference-based tracing/eval platform. |
| agentops | pass | 39, 43, 60, 85, 100, 178, 660, 748, 833, 909, 1234 | AgentOps is the closest agent-specific observability taxonomy/tooling threat. |
| public_labeled_trajectories | pass | 13, 16, 27, 28, 29, 31, 32, 33, 34, 43, 50, 53, ... (207 total) | The paper must distinguish itself from benchmarks that provide labeled trajectories. |

## Baseline Grounding

| Key | Status | Lines | Reason |
|---|---|---|---|
| dataset_native_sequence | pass | 83, 86, 87, 124, 179, 363, 569, 576, 601, 628, 839, 870, ... (18 total) | Reviewers will expect a comparison against the benchmark's native sequence view. |
| flat_action_summary | pass | 83, 86, 87, 127, 179, 241, 243, 245, 355, 363, 371, 425, ... (82 total) | Flat counting is the simplest aggregation baseline. |
| fixed_session_stack | pass | 83, 84, 85, 86, 87, 125, 177, 179, 232, 242, 243, 245, ... (117 total) | Fixed session or demo stacks test whether operation stacks add value. |
| fixed_session_span_tree_proxy | pass | 85, 86, 177, 179, 663, 821, 827, 833, 868, 950, 1088, 1161, ... (18 total) | LLM observability systems motivate a span-tree baseline, but current R320 evidence uses fixed-session as the proxy. |
| frontier_counterpoints | pass | 86, 87, 179, 243, 245, 355, 363, 442, 444, 445, 448, 451, ... (63 total) | R313 should preserve counterpoints instead of claiming dominance. |

## R313 Alignment

| Key | Expected text | Status | Lines |
|---|---|---|---|
| tasks | 6 | pass | 3, 6, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, ... (294 total) |
| datasets | 4 | pass | 3, 5, 18, 27, 28, 29, 30, 32, 35, 36, 37, 38, ... (298 total) |
| operations | 34,539 | pass | 241, 537, 626, 784, 821, 826, 828, 829, 832, 836, 839, 889, ... (30 total) |
| positive_operations | 3,699 | pass | 241, 626, 829, 832, 836, 839, 889, 950, 1026, 1154, 1157, 1161, ... (16 total) |
| candidate_points | 162 | pass | 243, 487, 784, 806, 832, 1157, 1205, 1233 |
| operation_stack_on_frontier | 6/6 | pass | 241, 243, 246, 445, 450, 451, 626, 628, 784, 827, 829, 830, ... (34 total) |
| operation_stack_best_lift | 4/6 | pass | 242, 243, 332, 333, 450, 628, 784, 827, 829, 832, 841, 842, ... (26 total) |
| operation_stack_best_recall_under_30pct_work | 4/6 | pass | 242, 243, 332, 333, 450, 628, 784, 827, 829, 832, 841, 842, ... (26 total) |
| flat_on_frontier | 6/6 | pass | 241, 243, 246, 445, 450, 451, 626, 628, 784, 827, 829, 830, ... (34 total) |
| fixed_session_on_frontier | 6/6 | pass | 241, 243, 246, 445, 450, 451, 626, 628, 784, 827, 829, 830, ... (34 total) |
