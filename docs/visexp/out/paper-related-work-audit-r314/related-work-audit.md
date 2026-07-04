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
| classic_flamegraph_pprof | pass | 41, 63, 66, 72, 95, 184, 238, 239, 274, 281, 286, 289, ... (119 total) | Classic profilers are the fixed-call-stack baseline for folded stacks. |
| opentelemetry_genai | pass | 35, 38, 40, 65, 73, 74, 77, 117, 210, 565, 594, 624, ... (20 total) | OpenTelemetry-style GenAI semantic conventions are the trace-schema threat. |
| openinference | pass | 38, 40, 65, 74, 77, 117, 565, 594, 669, 752, 844, 1141, ... (13 total) | OpenInference is a current AI-observability semantic convention for spans. |
| langsmith | pass | 36, 65, 66, 75, 104, 565, 595, 670, 752, 844, 1141 | LangSmith is a production LLM observability and evaluation platform. |
| langfuse | pass | 37, 65, 66, 76, 104, 565, 595, 671, 752, 844, 1141 | Langfuse is an open LLM tracing, eval, and prompt-management platform. |
| phoenix | pass | 38, 65, 66, 74, 77, 104, 565, 595, 669, 672, 752, 844, ... (13 total) | Phoenix is an OpenTelemetry/OpenInference-based tracing/eval platform. |
| agentops | pass | 39, 65, 78, 565, 595, 673, 752, 844, 1141 | AgentOps is the closest agent-specific observability taxonomy/tooling threat. |
| public_labeled_trajectories | pass | 13, 16, 27, 28, 29, 31, 32, 33, 34, 48, 51, 63, ... (187 total) | The paper must distinguish itself from benchmarks that provide labeled trajectories. |

## Baseline Grounding

| Key | Status | Lines | Reason |
|---|---|---|---|
| dataset_native_sequence | pass | 63, 102, 157, 894, 1173 | Reviewers will expect a comparison against the benchmark's native sequence view. |
| flat_action_summary | pass | 63, 66, 105, 157, 218, 220, 323, 334, 388, 407, 409, 410, ... (80 total) | Flat counting is the simplest aggregation baseline. |
| fixed_session_stack | pass | 63, 64, 66, 103, 157, 209, 219, 220, 221, 323, 335, 382, ... (107 total) | Fixed session or demo stacks test whether operation stacks add value. |
| fixed_trace_span_tree | pass | 65, 66, 74, 75, 104, 117, 157, 197, 252, 336, 565, 595, ... (19 total) | LLM observability systems motivate a trace-tree baseline. |
| frontier_counterpoints | pass | 66, 220, 323, 407, 409, 410, 413, 416, 503, 525, 530, 555, ... (59 total) | R313 should preserve counterpoints instead of claiming dominance. |

## R313 Alignment

| Key | Expected text | Status | Lines |
|---|---|---|---|
| tasks | 6 | pass | 3, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, ... (268 total) |
| datasets | 4 | pass | 3, 5, 18, 27, 28, 29, 30, 32, 35, 36, 37, 38, ... (275 total) |
| operations | 34,539 | pass | 218, 502, 555, 560, 562, 703, 740, 745, 747, 748, 751, 824, ... (26 total) |
| positive_operations | 3,699 | pass | 218, 562, 748, 751, 1068, 1071, 1136, 1137 |
| candidate_points | 162 | pass | 220, 452, 564, 703, 725, 751, 1071, 1112, 1140 |
| operation_stack_on_frontier | 6/6 | pass | 218, 220, 410, 415, 416, 561, 562, 563, 564, 703, 746, 748, ... (25 total) |
| operation_stack_best_lift | 4/6 | pass | 219, 220, 415, 561, 562, 564, 703, 746, 748, 751, 825, 1066, ... (18 total) |
| operation_stack_best_recall_under_30pct_work | 4/6 | pass | 219, 220, 415, 561, 562, 564, 703, 746, 748, 751, 825, 1066, ... (18 total) |
| flat_on_frontier | 6/6 | pass | 218, 220, 410, 415, 416, 561, 562, 563, 564, 703, 746, 748, ... (25 total) |
| fixed_session_on_frontier | 6/6 | pass | 218, 220, 410, 415, 416, 561, 562, 563, 564, 703, 746, 748, ... (25 total) |
