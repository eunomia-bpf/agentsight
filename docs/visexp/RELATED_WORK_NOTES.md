# Related Work Notes: Agent Flamegraph And Trace Views

Last updated: 2026-06-15
Completeness: partial web scan

## Existing Span-Duration / Workflow Views

These systems already cover agent traces, span trees, timelines, or
flamegraph-style views. AgentFlame should treat them as baselines, not novelty.

| System | Public reference | Relevant capability | Implication for AgentFlame |
|--------|------------------|---------------------|----------------------------|
| SigNoz + Inkeep | https://signoz.io/blog/inkeep-ai-agent-monitoring/ | Explicit "Flamegraph for Debugging" for multi-agent workflows; each horizontal bar is a span and width is duration; used for sequential/parallel execution, error cascades, tool overhead, and sub-agent boundaries. | Do not claim agent flamegraphs or span-duration workflow debugging as new. |
| OpenSearch Agent Traces | https://docs.opensearch.org/latest/observing-your-data/agent-traces/agent-tracing/ | Agent graph, trace tree view, and Gantt-style timeline over agent spans. | Treat trace tree/timeline/graph as standard baselines. |
| Datadog Trace View | https://docs.datadoghq.com/tracing/trace_explorer/trace_view/ | Waterfall and Flamegraph visualizations with span search and span metadata. | Span flamegraph and span search are prior art. |
| LangSmith | https://www.langchain.com/langsmith/observability | Agent tracing, cost/latency/error monitoring, trajectory monitoring, OpenTelemetry support. | Baseline for agent/LLM/tool trace observability. |
| Langfuse | https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse | Agent observability for LangGraph, OpenAI Agents, Pydantic AI, CrewAI, n8n; industry convergence around OpenTelemetry. | Baseline for production agent tracing and evaluation workflow. |
| Phoenix / OpenInference | https://arize-ai.github.io/openinference/ and https://arize.com/docs/phoenix/integrations/python/agentspec/agentspec-tracing | OpenInference semantic conventions and Agent Spec tracing over agent workflows. | Baseline for portable LLM/agent span conventions. |
| Agentrial | https://github.com/marketplace/actions/agentrial-ci | Trajectory flame graphs across agent trials, plus multi-agent evaluation metrics. | Baseline for trajectory/run comparison, not exact system-effect provenance. |
| Braintrust | https://www.braintrust.dev/articles/agent-observability-tracing-tool-calls-memory | Traces, spans, and sessions for LLM calls, tool invocations, memory retrieval, and evaluation loops. | Baseline for agent trace/eval integration. |

## Defensible AgentFlame Delta

AgentFlame should be framed as semantic effect profiling:

```text
sessionTag;promptTag;llmcall/tool;process*;effect
```

The claimable delta is not the existence of flamegraph-shaped UI. It is the
combination of:

1. local one-word semantic frames for session, prompt, and LLM-call contexts;
2. deterministic lineage from tool calls through shell/child processes to
   file/network effects;
3. folded aggregation across many sessions by semantic task and effect path.

The strongest required experiment is therefore R114: exact semantic-effect
lineage with precision/recall and negative controls.
