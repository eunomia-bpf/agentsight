# External Search And Source Verification

## Search Scope

The root independently searched primary papers, official repositories, and
official product/standard documentation after the blind paper read. The search
covered profiling standards, cross-run commercial analysis, process-centric
agent analysis, latent structure discovery, compositional task benchmarks, and
benchmarks with state-grounded subgoals. No search result was treated as proof
without opening a primary or official source.

## Verified Product And Standard Baselines

1. [LangSmith Insights](https://docs.langchain.com/langsmith/insights) creates
   hierarchical trace categories and aggregates error rate, latency, cost, and
   feedback at category and subcategory levels.
2. [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/)
   clusters production interactions into a topic hierarchy, names topics, and
   exposes volume, share, coherence, cost, token, latency, and error summaries.
3. [NVIDIA NeMo Agent Toolkit Profiler](https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/profiler.html)
   profiles token and latency bottlenecks, including nested tool-call stacks.
4. [OpenTelemetry Profiles](https://opentelemetry.io/docs/specs/otel/profiles/)
   defines pprof-compatible profiles and links samples to trace/span context.
5. pprof label promotion is a direct precedent for rendering tag values as
   pseudo-stack frames.

These sources show that hierarchical cross-run grouping and metric rollups are
not by themselves an open problem. They do not erase AgentProf's larger thesis:
none of these sources demonstrates the same task-responsibility attribution of
arbitrary conserved measures across agent intent and source-linked system
effects. The paper must realize and evaluate that stronger object rather than
claim novelty from field ordering alone.

## Verified Academic Pressure

- [TraceProbe](https://arxiv.org/abs/2607.06184) normalizes 2,500 real coding
  trajectories into a canonical action taxonomy, detects anti-patterns and
  divergent behavior, and reports process cost and failed work.
- [Graphectory](https://arxiv.org/abs/2512.02393) analyzes temporal and semantic
  process relations across 4,000 SWE-agent/OpenHands trajectories and reports
  6.9--23.5% resolution gains from online detection and intervention.
- [Hodoscope](https://arxiv.org/abs/2604.11072) uses cross-group behavioral
  differences to uncover benchmark vulnerabilities and reports 6--23x lower
  review effort than uniform sampling.
- [TraceGraph](https://arxiv.org/abs/2605.31308) builds shared decision
  landscapes and uses historical trap regions to improve SWE-bench resolved
  rate on fired subsets.
- [BPOP](https://arxiv.org/abs/2602.02806) infers latent dependency partial
  orders from noisy linear traces, beats trace-only and process-mining
  baselines, and compiles the inferred graph to reduce context, tokens, and
  runtime.
- [Same Signal, Different Semantics](https://arxiv.org/abs/2605.18332) analyzes
  64,380 SWE-bench runs across 43 frameworks and finds that several behavioral
  signals reverse direction across agent configurations. This directly warns
  against treating globally recurrent low-level actions as stable task
  semantics without task/control context.
- [AgentFlow](https://arxiv.org/abs/2607.01640) recovers typed agent dependency
  graphs from 5,399 agent programs. It is static analysis rather than trajectory
  profiling, but confirms that framework-aware dependency structure is a
  serious neighboring abstraction.

The process literature raises two requirements for AgentProf: compare against
structure-aware alternatives and connect the representation to an inspection,
intervention, cost, safety, or quality decision.

## Verified Public Evaluation Resources

### WorkArena++

[WorkArena++](https://proceedings.neurips.cc/paper_files/paper/2024/hash/0b82662b6c32e887bb252a74d8cb2d5e-Abstract-Datasets_and_Benchmarks_Track.html)
contains 682 realistic knowledge-work tasks and can generate ground-truth
observation/action traces. The [official repository](https://github.com/ServiceNow/workarena)
states that WorkArena++ composes WorkArena atomic tasks into real workflows;
its oracle interface exposes a composite task length and an explicit
`subtask_idx` when executing each atomic subtask. This is materially closer to
task/subtask responsibility than the current flat stage corpora. Running the
live benchmark requires ServiceNow instance access, so source inspection alone
does not authorize a complete trajectory result.

### ToolSandbox

[ToolSandbox](https://github.com/apple/ToolSandbox/blob/main/README.md) defines
task completion through a milestone DAG: nodes are state or interaction
subgoals, directed edges specify prerequisite order, and the official evaluator
finds an optimal milestone-to-trajectory match consistent with a topological
ordering. The repository already contains the complete released trajectory
population and official scenario definitions used in Step 0060. A milestone
DAG is not automatically a nested task stack, but it is an independent
state-grounded reference for completion and dependency.

## Search Implications

The source search strengthens rather than narrows the fixed thesis. The exact
paper-level thesis remains **“Agent observability needs profiling, not only
debugging.”** The source-grounded repair is not another field, threshold, or
prompt. It is to make the profile's responsibility path follow task intent and
subtask control while keeping command, tool, model, session, and status as
evidence.

The simplest promising principle is:

> Task structure should come from task intent and explicit planning or
> delegation events; ordinary tool and system events inherit that structure
> and supply the measured evidence.

This is distinct from both the current field stack and the failed per-operation
open-vocabulary Qwen controllers. It preserves operations and operation stacks
as the two core abstractions and changes only how a task-semantic stack is
constructed.
