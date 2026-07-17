# Milestone Review 001 — External Search and Primary-Source Verification

## Node identity

- **Timestamp:** 2026-07-17T07:47:33-0700
- **Parent:** `01-blind-full-paper-read.md`
- **Gate:** REVIEW
- **Search owner:** `research-literature-novelty`
- **Canonical output updated:** `docs/background-related-work.md`
- **Paper mutation policy:** read-only; no manuscript, thesis, RQ, algorithm, or result was changed

## Objective

Attack the current paper's largest blind-review uncertainty with current external evidence: determine whether real products or papers already provide the same cross-run semantic profiling capability, whether AgentProf's strongest novelty sentence remains defensible, and which existing result or new experiment would materially change an AAAI decision. Search was claim-oriented, not keyword-count-oriented.

## Search method

The search covered four branches derived from the blind review:

1. production agent observability products that discover cross-trace patterns and aggregate cost, latency, error, evaluation, or user-defined attributes;
2. academic agent trajectory representations that merge recurring actions, build process profiles, or turn population structure into inspection or repair decisions;
3. traditional profiling, trace correlation, process mining, and event abstraction that threaten novelty of pprof export, hierarchy, or cross-signal linkage;
4. evaluation precedents for problem localization and human inspection.

Only official product documentation, standards, author-hosted/open proceedings, and paper PDFs were used for technical conclusions. Six closest papers were downloaded and read beyond their abstracts: WebGraphEval, Hodoscope, TraceGraph, Agentic AI Process Observability, TraceProbe, and AgentDiagnose. Product capabilities were verified from the current LangSmith, Datadog, NVIDIA, Laminar, and OpenTelemetry documentation. Search results were checked as of 2026-07-17.

## Primary-source capability matrix

| Source | Verified capability | Direct overlap with AgentProf | Material distinction retained by AgentProf | Threat level |
|---|---|---|---|---:|
| [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | Samples production interactions, summarizes and embeds them, clusters with UMAP/HDBSCAN, assigns each interaction to a topic, builds a topic hierarchy, and aggregates interaction volume, cost, tokens, errors, latency, and online evaluations. Topics can be exported to datasets or annotation queues. | Cross-run semantic grouping, hierarchy, additive metric rollups, failure prioritization. | Operates on selected interactions/spans; no verified cross-layer joining of process/file/network effects to responsible agent actions, no selectable stack projection over one conserved operation corpus, and no conventional profiler output. | **Very high product overlap** |
| [LangSmith Insights](https://docs.langchain.com/langsmith/insights) | Hierarchically categorizes traces, optionally from user-declared categories/attributes, and aggregates error rate, latency, cost, feedback, and extracted attributes per category. | Cross-run semantic categories, hierarchical drill-down, metric aggregation. | Trace/run object is the unit; no verified low-level effect attribution or pprof-style sample projection. | **Very high product overlap** |
| [LangSmith Engine](https://docs.langchain.com/langsmith/engine) | Detects recurring trace-supported issues, diagnoses root causes, proposes fixes, creates evaluators and examples, and can open a code PR. | Establishes a stronger analysis-to-action product precedent than visualization or ranking alone. | It is an issue/fix loop rather than a resource profiler; no conserved multi-resource operation stack is documented. | **High consequence precedent** |
| [Laminar Signals](https://laminar.sh/docs/signals/introduction) | Reads each current or historical trace into a structured event, then supports querying, clustering, backfilling, tracking, and alerting over those events. | Cross-run behavioral categorization and event clustering. | Signal extraction is prompt/schema driven at trace level; no verified cross-layer additive responsibility model or profile format. | **High product overlap** |
| [NVIDIA NeMo Agent Toolkit Profiler](https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/profiler.html) | Instruments supported workflows, records per-invocation tokens and time, performs offline analysis, forecasts usage, and analyzes latency, throughput, bottlenecks, and concurrency. | Uses the word and practice of profiling for agent workflows and aggregates resource/performance measurements. | Requires supported workflow instrumentation and retains workflow/runtime structure; does not verify heterogeneous completed histories with query-time semantic stacks or joined OS effects. | **Closest named profiler** |
| [OpenTelemetry Profiles](https://opentelemetry.io/docs/specs/otel/profiles/) | Defines a pprof-superset profile signal; profile samples can carry direct trace/span links and correlate with logs, metrics, and traces through resource context. Public alpha was announced in 2026. | pprof compatibility, profile--trace linkage, cross-signal correlation. | Correlates code-stack samples with request/resource context; it does not derive agent semantic responsibility units or action-level query-time hierarchies. | **Eliminates component-level novelty** |
| [Hodoscope](https://arxiv.org/abs/2604.11072) | Summarizes actions into behavior-level intent, compares group distributions, ranks distinctive actions for review, discovers a real benchmark vulnerability, reports 6--23x review-effort improvement, and improves some downstream monitors. | Label-free cross-run behavior abstraction, human inspection prioritization, discovery of recurring/atypical agent behavior. | Distributional comparison rather than additive resource attribution; requires comparison groups and does not preserve/fold arbitrary weights. | **Strongest inspection precedent** |
| [WebGraphEval](https://arxiv.org/abs/2510.19205) | Canonicalizes and merges recurring actions from 4,768 WebArena trajectories and six agents into weighted action graphs; propagates reward and reports redundancy, inefficiency, and critical transitions. | Uniform/canonical actions, cross-agent recurrence, weighted population representation, problem/efficiency analysis. | Task-specific action graphs with outcome overlays, not cross-layer effects, selectable field stacks, or pprof output. | **High academic overlap** |
| [TraceGraph](https://arxiv.org/abs/2605.31308) | Pools 7,329 multi-model trajectories into task-specific shared decision landscapes, derives Access/Trap/Repair process profiles, and uses discovered traps in a recovery pipeline that improves official SWE-bench resolved rate on fired subsets. | Recurring cross-run structure, process profiles, problem regions, downstream intervention. | Outcome-informed task graph rather than target-blind additive resource profiler; no heterogeneous effect joining. | **Strongest intervention precedent** |
| [TraceProbe](https://arxiv.org/abs/2607.06184) | Normalizes 2,500 coding-agent trajectories into canonical actions and deterministic effect labels, detects recurring anti-patterns, aligns runs, and reports setting-level process profiles including tokens, duration, failed work, milestones, and resource/process differences. | Canonical operations/effects, resource-aware process profiles, cross-run comparison, recurring behavior. | Coding-specific deterministic diagnostics; no verified system-effect joining, arbitrary additive conservation, selectable stack fields, or profiler-format export. | **Closest current academic neighbor** |
| [Agentic AI Process Observability](https://arxiv.org/abs/2505.20127) | Consolidates repeated agent executions into process event logs and applies process/causal discovery to reveal temporal dependencies and unintended behavioral variability. | Cross-run aggregation, semantic process abstraction, developer observability. | Early workshop study on one calculator setup; not a multi-resource profiler and not a validated generic operation-stack model. | **Important conceptual precedent** |
| [AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/) | Measures trajectory competencies, visualizes semantic action embeddings and state transitions, correlates metrics with human judgments, and uses filtered trajectory data to improve a downstream agent. | Semantic trajectory analysis and analysis-to-intervention evidence. | Web-domain diagnostic/evaluation toolkit rather than additive responsibility profiling. | **High evaluation precedent** |

## What is no longer defensible as independent novelty

The external evidence rejects novelty claims based solely on any of the following components:

- storing traces as fielded or canonical action records;
- merging semantically similar actions across runs;
- deriving flat or hierarchical categories from many traces;
- aggregating tokens, cost, latency, errors, evaluations, or reward by those categories;
- calling cross-run agent analysis “profiling” or producing process profiles;
- exporting weighted stacks in pprof format;
- linking profile samples to traces/spans;
- ranking suspicious or failing behavior for human review;
- claiming that population-level structure can guide a later repair.

The current paper mostly avoids these isolated first-ever claims, but its three-paragraph related-work section does not show the reader that the authors understand how crowded these components have become.

## The surviving large novelty claim

No verified source combines the following into one agent-specific model and evaluated system:

1. a uniform operation record spanning prompts, LLM calls, tools, and source-linked process/file/network effects;
2. exact conservation of arbitrary additive measures over the admitted operation corpus;
3. query-time construction of a hierarchy from a user-selected sequence of semantic fields, independent of runtime call nesting;
4. multiple responsibility/resource projections over the same completed heterogeneous histories;
5. conventional pprof-compatible output plus source lineage back to operations;
6. evidence that the same organization improves independently annotated problem ranking over an information-matched raw-action organization.

This composite is not a retreat to implementation novelty. It is the concrete mechanism behind the fixed thesis:

> **Agent observability needs profiling, not only debugging.**

The thesis remains scientifically interesting because it asks agent observability to treat repeated activities as accountable resource/problem populations, not merely as executions to replay. The correct paper claim is that AgentProf provides the missing **agent semantic responsibility profile**, not that it invented semantic grouping, hierarchical dashboards, cross-run analysis, or profile/trace correlation separately.

## Direct same-claim risk assessment

### Risk 1 — “This is Datadog Patterns or LangSmith Insights exported to pprof”

This is the most likely product-informed reviewer objection. Both products already discover hierarchical topics and aggregate cost/error/latency/evaluation metrics. The rebuttal cannot rely on the file format. It must show that AgentProf's unit is an additive operation/effect with preserved source lineage, that the hierarchy is a selectable responsibility view rather than one generated topic tree, and that system effects beyond instrumented LLM spans can be attributed to agent actions.

The current RQ1 capture/control experiment and operation invariant partially answer this. Figure 1 demonstrates multiple projections, but it does not visually expose source-linked low-level effects. The architecture and related-work prose should make the distinction visible without creating new jargon.

### Risk 2 — “This is process mining or TraceProbe for agents”

Process mining already creates higher-level activities and hierarchical process abstractions from logs. TraceProbe now uses canonical actions/effect labels and the term process profiles while reporting token/duration/failed-work differences across real coding-agent settings. The paper must not claim first cross-run process analysis or first agent profile.

AgentProf remains different in its profiler semantics: arbitrary additive measures, selectable field stacks, exact mass conservation, heterogeneous cross-layer effects, and standard profile tooling. TraceProbe is a particularly important citation because it appeared immediately before the AAAI deadline and uses the closest vocabulary.

### Risk 3 — “The paper ranks problems, but stronger work discovers and fixes them”

Hodoscope reports real unknown-vulnerability discovery and inspection reduction; TraceGraph reports a graph-guided recovery improvement; LangSmith Engine closes the loop to evaluators and code changes. AgentProf's RQ2 standard MAP result is valid but is not automatically a stronger consequence.

This does not invalidate the profiling thesis. A profiler is valuable infrastructure even when it does not repair a program. For AAAI significance, however, the paper should make one concrete decision enabled by cross-run additive responsibility unmistakable. The existing fixed-reader result and local-first analysis are candidates, but neither should be overstated as human productivity or untouched intervention evidence.

## Current paper coverage versus external frontier

The current Introduction correctly acknowledges LangSmith Insights and Datadog Patterns and says some tools already derive hierarchical categories and aggregate metrics. This is an important strength.

The current Related Work is too compressed to establish the remaining boundary. It currently lacks visible discussion of:

- TraceProbe as the closest current “process profile” paper;
- WebGraphEval as a weighted recurring-action graph;
- Hodoscope or TraceGraph as stronger inspection/intervention precedents;
- OpenTelemetry Profiles as prior pprof-compatible trace/profile linkage;
- process mining/event abstraction as prior hierarchical trace segmentation.

This is a WRITE problem, not evidence that the story should be replaced. A concise claim-oriented comparison can fit by compressing generic lists rather than adding a long survey.

## Canonical literature update

`docs/background-related-work.md` was updated to:

1. record the 2026-07-17 source verification date;
2. replace stale pre-Step-0036 RQ2 language with the current standard MAP and local-first evidence;
3. add WebGraphEval;
4. strengthen TraceProbe's capability description from the full paper;
5. add OpenTelemetry Profiles;
6. separate established real-problem concentration from unproven human-inspection/repair consequences;
7. make the remaining RQ2 question about paper-level sufficiency against current closest work rather than another metric on the same targets.

No historical result was deleted. The fixed thesis and four RQs were preserved.

## Implications for the next iteration

The source search does **not** authorize another constructor, score, cutoff, or benchmark merely to produce a larger table. It changes the acceptance question from “are the metrics standard?” to:

> Does AgentProf demonstrate an important decision enabled by cross-layer additive semantic responsibility that trace grouping and local diagnosis do not already provide?

Three candidate routes remain for the full-paper reread and independent review:

1. **WRITE using existing evidence:** foreground the local-first same-signal comparison and sharpen the exact composite novelty against Datadog/LangSmith/TraceProbe/OpenTelemetry Profiles.
2. **Existing-trajectory consequence analysis:** use the already captured 325 histories or existing fixed-reader packets to expose one concrete resource/problem prioritization decision that changes under semantic multi-resource profiles, with no new corpus and no new algorithm.
3. **No new experiment:** if independent reviewers find that RQ1 lineage/conservation plus three-benchmark MAP already clears the AAAI bar, spend the remaining iteration on closest-work positioning, Figure 1 callouts, and a stronger evidence-to-thesis synthesis.

A new product imitation, proprietary-product reproduction, or another custom localization metric is not a high-value route. The next node must reread the paper with this external frontier and decide which route actually changes the verdict.

## Uncertainty

Product documentation verifies advertised capabilities, not an information-matched experimental baseline; no proprietary Datadog/LangSmith implementation can be reproduced from these documents alone. Several 2026 academic sources are preprints rather than accepted main-track papers. These facts reduce their authority as performance baselines but not their force as novelty/capability precedents.

No source found the exact six-part AgentProf composite. Absence from this bounded search is not proof of global firstness; the manuscript should use precise capability language rather than an absolute “first.”

## Completion

The external-search node is complete. It produced a current source-grounded novelty boundary and updated the canonical literature frontier. The next node is a full-paper reread that converts this evidence into a provisional accept/reject assessment and one routeable next action.
