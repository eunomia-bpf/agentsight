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
| classic_flamegraph_pprof | pass | 41, 63, 66, 72, 95, 184, 239, 240, 275, 282, 287, 290, ... (112 total) | Classic profilers are the fixed-call-stack baseline for folded stacks. |
| opentelemetry_genai | pass | 35, 38, 40, 65, 73, 74, 77, 117, 210, 576, 608, 645, ... (19 total) | OpenTelemetry-style GenAI semantic conventions are the trace-schema threat. |
| openinference | pass | 38, 40, 65, 74, 77, 117, 576, 654, 737, 796, 1082, 1148 | OpenInference is a current AI-observability semantic convention for spans. |
| langsmith | pass | 36, 65, 66, 75, 104, 577, 655, 737, 797, 1082 | LangSmith is a production LLM observability and evaluation platform. |
| langfuse | pass | 37, 65, 66, 76, 104, 577, 656, 737, 797, 1082 | Langfuse is an open LLM tracing, eval, and prompt-management platform. |
| phoenix | pass | 38, 65, 66, 74, 77, 104, 577, 654, 657, 737, 797, 1082 | Phoenix is an OpenTelemetry/OpenInference-based tracing/eval platform. |
| agentops | pass | 39, 65, 78, 577, 658, 737, 797, 1082 | AgentOps is the closest agent-specific observability taxonomy/tooling threat. |
| public_labeled_trajectories | pass | 13, 16, 27, 28, 29, 31, 32, 33, 34, 48, 51, 63, ... (188 total) | The paper must distinguish itself from benchmarks that provide labeled trajectories. |

## Baseline Grounding

| Key | Status | Lines | Reason |
|---|---|---|---|
| dataset_native_sequence | pass | 63, 102, 157, 833, 1116 | Reviewers will expect a comparison against the benchmark's native sequence view. |
| flat_action_summary | pass | 63, 66, 105, 157, 218, 220, 324, 335, 389, 406, 408, 409, ... (73 total) | Flat counting is the simplest aggregation baseline. |
| fixed_session_stack | pass | 63, 64, 66, 103, 157, 209, 219, 220, 222, 324, 336, 383, ... (99 total) | Fixed session or demo stacks test whether operation stacks add value. |
| fixed_trace_span_tree | pass | 65, 66, 74, 75, 104, 117, 157, 197, 253, 337, 399, 577, ... (18 total) | LLM observability systems motivate a trace-tree baseline. |
| frontier_counterpoints | pass | 66, 220, 324, 406, 408, 409, 412, 415, 502, 524, 529, 546, ... (53 total) | R313 should preserve counterpoints instead of claiming dominance. |

## R313 Alignment

| Key | Expected text | Status | Lines |
|---|---|---|---|
| tasks | 6 | pass | 3, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, ... (257 total) |
| datasets | 4 | pass | 3, 5, 18, 27, 28, 29, 30, 32, 35, 36, 37, 38, ... (261 total) |
| operations | 34,539 | pass | 218, 501, 546, 688, 725, 730, 732, 733, 736, 740, 785, 835, ... (27 total) |
| positive_operations | 3,699 | pass | 218, 546, 688, 733, 736, 740, 785, 1007, 1010, 1014, 1077, 1078, ... (13 total) |
| candidate_points | 162 | pass | 220, 451, 547, 688, 710, 736, 1010, 1053, 1081 |
| operation_stack_on_frontier | 6/6 | pass | 218, 220, 409, 414, 415, 546, 547, 688, 731, 733, 734, 736, ... (27 total) |
| operation_stack_best_lift | 4/6 | pass | 219, 220, 414, 547, 688, 731, 733, 736, 1005, 1006, 1007, 1010, ... (15 total) |
| operation_stack_best_recall_under_30pct_work | 4/6 | pass | 219, 220, 414, 547, 688, 731, 733, 736, 1005, 1006, 1007, 1010, ... (15 total) |
| flat_on_frontier | 6/6 | pass | 218, 220, 409, 414, 415, 546, 547, 688, 731, 733, 734, 736, ... (27 total) |
| fixed_session_on_frontier | 6/6 | pass | 218, 220, 409, 414, 415, 546, 547, 688, 731, 733, 734, 736, ... (27 total) |
