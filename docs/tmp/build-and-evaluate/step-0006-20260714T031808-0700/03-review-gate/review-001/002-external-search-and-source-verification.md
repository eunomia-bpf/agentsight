# External Search and Source Verification

## Node record

- Completed: 2026-07-14T05:42:39-07:00
- Search purpose: verify closest-work and RQ3 source boundaries, not expand the
  experiment matrix
- Source policy: primary papers, official repositories, and official product or
  profiler documentation

## Closest scientific neighbors

### Agentic AI Process Observability

- Primary paper: <https://ceur-ws.org/Vol-4087/paper3-Long.pdf>
- Preprint: <https://arxiv.org/abs/2505.20127>

This work consolidates agent runs into an event log and applies process and
causal discovery to behavioral variability. It is a closer neighbor than a
generic tracing product because it also reasons across runs. AgentProf must
distinguish weighted cross-layer responsibility profiling and query-time
operation stacks from process-discovery analysis. This is a Related Work and
novelty-positioning task; it does not require a new benchmark.

### AgentDiagnose

- ACL Anthology: <https://aclanthology.org/2025.emnlp-demos.15/>

AgentDiagnose evaluates semantic trajectory competencies and reports
correlation with human judgments. It strengthens the case that semantic
trajectory analysis is an active area, but its focus is diagnosis and
trajectory curation rather than additive cross-run resource/effect profiling.

### Existing aggregation and profiler capabilities

- LangSmith dashboards: <https://docs.langchain.com/langsmith/dashboards>
- Langfuse metrics: <https://langfuse.com/docs/metrics/overview>
- Phoenix tracing: <https://arize.com/docs/phoenix/tracing/tutorial>
- pprof documentation: <https://github.com/google/pprof/blob/main/doc/README.md>

These sources confirm that cross-run dashboards, aggregate metrics, supplied
attributes, and label promotion are not sufficient novelty claims by
themselves. The paper's strongest differentiator is deriving recurring fields,
preserving their connection to measured effects, and exposing alternative
profile hierarchies over those effects.

## RQ3 source boundary

- OSWorld-Human paper: <https://arxiv.org/abs/2506.16042>
- Official repository: <https://github.com/WukLab/osworld-human>

OSWorld-Human supplies manually annotated human reference trajectories and
grouped actions. It is appropriate independent boundary truth for Step 0006.
It is not an unseen agent-family study, and the official repository warns that
the trajectories contain benchmark solutions. The current paper's
session-held-out, boundary-component wording is therefore the correct scope.

## Search conclusion

No source search justifies a smaller thesis or a broader experiment matrix.
The closest-work screen increases the value of one exact-lineage RQ1 replay,
because independent propagation from activity to downstream measured effects
is precisely what separates AgentProf from dashboards and semantic trajectory
visualizers.

