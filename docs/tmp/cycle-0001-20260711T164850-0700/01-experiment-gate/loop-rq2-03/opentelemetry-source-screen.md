# Source Screen: Exgentic OpenTelemetry Agent Traces

**Timestamp:** 2026-07-12T06:16:00-07:00  
**Status:** rejected before experiment planning  
**Reason:** actual release lacks the source-native parent-child hierarchy and
independent benchmark outcome required by the paper

## Source

- Dataset: `Exgentic/agent-llm-traces`
- Hugging Face revision: `70036b93a04e61b0ea2706a68b962f4f26774587`
- Access: public, ungated
- Full download: all 39 parquet shards plus card metadata, 939MB locally
- License: CDLA Permissive 2.0

This screen used the entire 1,781-row release, not a sample.

## What Passes

- 1,781 real agent traces across six benchmarks and five harnesses.
- 38,052 LLM-call records.
- Every LLM-call record has input/output token counts; the release also carries
  start/end timestamps and status.
- AppWorld includes both `tool_calling` (188 traces) and
  `tool_calling_with_shortlisting` (82 traces).
- Parsing the first user content recovers exact task text. Within equal models,
  base and shortlisting have 59 exact task-text intersections: 57 Gemini and 2
  DeepSeek tasks.

These facts make the source attractive for token-regression analysis.

## Actual Schema Versus Dataset Card

The card documents a span structure containing `parent_span_id`. The actual
parquet schema does not contain that field. Every released span has:

```text
span_id, name, kind, start_time, end_time, attributes,
resource_attributes, status, type, harness, benchmark,
models, session_id, trace_id
```

No parent edge is present. All 38,052 records have `type = llm_call`. Tool calls,
results, and definitions appear only inside serialized input/output message
attributes, not as independently parented tool spans.

The source can reconstruct chronological LLM-call sequence and message content,
but not the genuine OpenTelemetry `trajectory -> agent/span -> LLM/tool` tree
required by the full-paper review. Treating list order or embedded tool messages
as the released parent-child trace would recreate the same turn-position proxy
problem already exposed by Hodoscope.

## Matching And Outcome Limits

The top-level schema has no task ID, benchmark reward, success field, or known
intervention outcome. Exact AppWorld task text can be recovered from prompts,
but:

- base and shortlisting coverage is incomplete and model-dependent;
- there is no released benchmark outcome to verify task success;
- the dataset does not identify a ground-truth changed component at operation
  level;
- span status describes LLM API success/failure, not benchmark decision quality.

The shortlisting configuration is a real harness variant and token counts are a
direct additive measure, but the release alone cannot determine which hierarchy
supports a better benchmark decision. More importantly, it cannot supply the
genuine source-native tree demanded by the central belief comparison.

## Decision

| Requirement | Verdict |
|---|---|
| Fully public complete release | PASS |
| Direct per-call additive token/time measures | PASS |
| Some exact same-task framework cells | PASS (59 AppWorld tasks) |
| Genuine released parent-child agent/tool hierarchy | **FAIL** |
| Independent benchmark outcome/changed component | **FAIL** |

Do not plan the RQ2 experiment on this release. The dataset card's intended
OpenTelemetry semantics are not a substitute for fields absent from the actual
parquet. No adapter should invent parent edges to rescue it.

## Research Consequence

Two serious public candidates now fail for complementary reasons:

- tau-bench preserves the conversation/tool hierarchy and final task reward but
  lacks operation-linked decision evidence and has truncated episodes;
- Exgentic preserves additive LLM measures but omits the released parent-child
  hierarchy and benchmark outcome.

The next source search should require all properties in one release before any
experiment plan is reviewed. A promising route is an official trace corpus or
real instrumented benchmark run that exports both native OpenTelemetry parent
edges and benchmark-native outcomes. Generating that evidence with AgentSight
over a real published benchmark may be necessary, but such a run must be planned
as the real experiment rather than replaced by a toy adapter.
