# AgentProf Literature And Novelty Frontier

## Purpose And Fixed Contract

This file is the concise current literature, novelty, baseline, and source-search
frontier. Detailed searches and completed experiment histories live in the
linked cycle reports. The pre-repair 243-line frontier is preserved at
[`archived-background-related-work-20260713T110014-0700.md`](tmp/cycle-0002-20260712T201943-0700/archived-background-related-work-20260713T110014-0700.md).

The fixed thesis is:

> **Agent observability needs profiling, not only debugging.**

The four fixed questions remain resource attribution, correspondence to real
problems, tag accuracy, and profiling cost. Literature and experiments must
strengthen that positive program. A local negative or inconclusive construction
does not authorize a hierarchy-centered replacement story, a smaller RQ, or a
weaker hypothesis.

Cycle 0003 completed the fixed-RQ2 HINTBench experiment selected by the prior
whole-paper REVIEW. The full official snapshot and all declared cells ran, but
the paired work interval against raw action crossed zero, so the strict result
is `VALID / INCONCLUSIVE` and that population is closed to retuning. The next
whole-paper REVIEW compared all four open RQs and selected one new
highest-paper-value experiment: fixed-RQ2 localization over all 220 official
TraceElephant real failed executions, with decisive-step targets scorer-only
and strong same-information baselines. This is a stronger external evidence
source for the unchanged RQ2, not a new story or a run-level substitute task.

Step 0004 has now completed that TraceElephant experiment over all 220 released
real failures. Independent recalculation confirms the run is valid and complete.
The fixed semantic construction has strong early concentration but a large
final tied tier, so its predeclared 80%-recall work comparison is inconclusive.
The outer audit synthesized this with the earlier positive AgentProcessBench AP
results and HINTBench work curve and accepted a positive cumulative RQ2 answer.
Another RQ2 score or benchmark variant is not the current evidence priority.

Step 0007 then completed the selected RQ1 replay by reusing R114's fixed 20
real Codex tasks, capture/export path, exact-lineage checker, manifest task
categories, and concurrent controls. The scoped lineage path reaches 100.0%
precision and 96.569% recall, rejects all 1,629 controls, and current
`agentpprof 0.2.37` preserves all 1,520 attributed effects and all five
category weights.

Step 0008 then reused four already supported public sources and current
backends for RQ3. Target-blind task clustering reaches V-measure 0.5565 on the
complete nine-session Mind2Web prefix and 0.8151 on 100 ScienceWorld sessions,
both at full coverage versus 0 for a constant control. The current paper now
combines this task-partition evidence with Step 0006's session-held-out human
boundary result. Phase and broad action evidence remain open components of the
fixed RQ3, but another dataset or metric variant is not automatically the next
paper priority.

Step 0010 is a whole-paper AAAI-27 review. Its external search must first test
whether the apparent missing-baseline objection is a reporting gap: the
completed HINTBench and TraceElephant matrices already include native sequence,
independent-step, per-session, flat, width-only, raw-action, and oracle controls.
A simple cumulative synthesis of those existing results has priority over a new
benchmark or human-dependent study.

## Verified Closest-Work Families

### Profilers And Cross-Trace Analysis

- [Domain-specific program profiling](https://doi.org/10.1016/j.scico.2014.02.011)
  turns domain events into developer-chosen hierarchical reports. Domain-level
  events and arbitrary dimensions are not independently novel.
- [pprof](https://github.com/google/pprof/blob/main/doc/README.md) represents
  weighted samples over location hierarchies and supports labels and tag-derived
  pseudo-frames. Weighted stack aggregation and pprof output are infrastructure,
  not the paper's scientific novelty.
- [Flame graphs](https://queue.acm.org/detail.cfm?id=2927301) establish the
  folded-stack visualization lineage.
- [Perfetto Trace Processor](https://perfetto.dev/docs/analysis/trace-processor)
  supports trace ingestion, SQL analysis, derived events, and query-time
  aggregation.
- [Pivot Tracing](https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems/)
  dynamically selects, filters, and groups metrics across causally related
  component events. It makes independent lineage fidelity, not only mass
  conservation, a required RQ1 comparison.
- [Visualizing Distributed Traces in Aggregate](https://arxiv.org/abs/2412.07036)
  groups and visualizes trace collections by services, structure, depth, or
  latency. Cross-run aggregation is not new by itself.
- [Differential Flame Graphs](https://doi.org/10.1109/SANER.2015.7081872)
  provide a published regression-comparison protocol.

The remaining systems opportunity is a validated agent-specific responsibility
record that conserves additive resources across heterogeneous layers and can be
projected into decision-relevant population profiles without discarding the
source execution view.

### Semantic Cross-Run Agent Analysis

- [Hodoscope](https://arxiv.org/abs/2604.11072) summarizes actions into a common
  behavior space, compares cohort distributions, and directs human inspection
  toward distinctive behavior. It prevents any claim that AgentProf first
  enables semantic cross-run comparison or behavior discovery.
- [AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/) embeds
  trajectory actions and exposes semantic and state-transition visualizations.
  Its automatic competency metrics correlate with human judgments, and its
  filtering of a 46k-example trajectory set improves a downstream WebArena
  agent despite retaining only 13% of the data. This establishes a published
  analysis-to-intervention evidence pattern stronger than visualization alone.
- [ARIA](https://arxiv.org/abs/2506.00539) projects actions into intention space
  and aggregates reward over similar behavior.
- [TraceGraph](https://arxiv.org/abs/2605.31308) pools multi-model trajectories
  into shared action-observation decision landscapes, identifies productive
  cores and traps, and uses those regions in a recovery pipeline that raises
  official SWE-bench resolved rate on fired subsets. It is the strongest
  current precedent for connecting population-level trajectory structure to a
  downstream agent improvement, although it remains a May 2026 preprint.
- [AgentGraph](https://ojs.aaai.org/index.php/AAAI/article/view/42393), published
  in the AAAI-26 Demonstration Track, converts agent logs into source-linked
  knowledge graphs and supports failure detection, optimization
  recommendations, perturbation tests, and causal attribution. It is evidence
  of AAAI relevance and a competing trace representation, not a Main-Track
  precedent for AgentProf's exact claim.

The completed Hodoscope experiment reproduced the official iQuest behavior and
found that the tested recursive AgentProf construction did not beat the released
density-gap/FPS bundle. This is a valid mechanism boundary, not a replacement
thesis. Full evidence remains in
[`cycle-0001/.../loop-rq2-02/result-review.md`](tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/result-review.md).

### Standards And Production Observability

- [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai)
  define GenAI spans, events, and metrics.
- [OpenInference](https://arize-ai.github.io/openinference/spec/) defines AI
  workload semantics over OpenTelemetry.
- [Phoenix](https://arize.com/docs/phoenix) combines tracing, evaluation,
  datasets, experiments, and span scoring.
- [Datadog LLM Observability Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/)
  hierarchically clusters production LLM interactions and can scope clustering
  to failed evaluations. Its documented hierarchy reports interaction volume,
  cost, tokens, errors, latency, and online evaluations and exports clusters to
  datasets or annotation queues. Semantic grouping and failure-topic discovery
  are therefore strong product baselines.
- [LangSmith Insights](https://docs.langchain.com/langsmith/insights)
  hierarchically categorizes cross-trace topics and aggregates latency, cost,
  feedback, error, and extracted attributes. Hierarchical cross-run
  categorization and metric rollups are therefore precedents, not AgentProf's
  novelty.
- [AgentTelemetry](https://dl.acm.org/doi/10.1145/3805760.3814931) supplies an
  agent-specific span taxonomy, fault-detection benchmark, and toolkit. Its
  accepted artifact has no released official fault-bearing step/span target,
  so it is a capability and baseline precedent, not the selected localization
  source.

These sources make generic observability, semantic grouping, trace taxonomy, and
fault-detection claims high risk. AgentProf's defensible distinction must be
tested as cross-layer additive responsibility profiling and decision-relevant
aggregation, not asserted from terminology.

### Failure And Problem Localization

- [AgentRx](https://github.com/microsoft/AgentRx) releases manually annotated
  critical failure steps and a diagnosis method across multiple domains.
- [TELBench / DRIFT](https://github.com/NJU-LINK/DRIFT) studies harmful error
  spans in deep-research trajectories.
- [HINTBench](https://arxiv.org/abs/2604.13954) releases raw agent trajectories
  with official risky-step annotations. The current paper-linked snapshot has
  536 test records rather than the paper/README's 629. Cycle 0003 completed this
  full snapshot as `VALID / INCONCLUSIVE`; it is now a closed mechanism boundary,
  not the next source, and may not be retuned.
- [TraceElephant](https://github.com/TraceElephant/TraceElephant) releases 220
  annotated real failed executions across Captain-Agent, Magentic-One, and
  SWE-Agent with responsible-component and decisive-step targets plus full
  input/output, inter-agent, tool, environment, configuration, and architecture
  context. Step 0004 completed this fixed-RQ2 population.
- [Holistic Evaluation and Failure Diagnosis](https://arxiv.org/abs/2605.14865),
  [TrajAD](https://arxiv.org/abs/2602.06443), and
  [AgentFixer](https://arxiv.org/abs/2603.29848) diagnose, localize, or repair
  trajectory failures.

AgentProf cannot claim failure localization in general. RQ2 must instead show
that one plan-defined target-blind profile concentrates independently defined real
problems and reduces inspection at matched recall, budget, or analyst decision
against strong information-equivalent baselines.

## Cycle 0002 Completed RQ2 Branches

The independent raw-artifact audit is
[`990-independent-outer-audit-20260713T105435-0700.md`](tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/990-independent-outer-audit-20260713T105435-0700.md).

| Branch | Evidence-backed edge | Current scientific use |
|---|---|---|
| [CodeTraceBench](tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-codetracebench/result-review.md) | **limits** the tested task-held-out differential construction | Complete real run; valid but mixed/inconclusive. Its missing raw replicate arrays keep it non-load-bearing. |
| [ToolSafe](tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-toolsafe/result-review.md) | **contradicts** the tested cross-family safety construction | Complete valid negative boundary; inspection-work and unsafe-only directions reverse. |
| [AgentNet](tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentnet/full-result-review.md) | **invalidates** dropping the visible target/local leaf | Complete run, but the intended comparison is invalid because the semantic key removes information retained by the raw baseline. |
| [AgentProcessBench mean risk](tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentprocessbench/full-execution-report.md) | **supports** semantic-specific AP concentration and **leaves unresolved** work reduction | Complete valid run; AP interval is positive, but the task-cluster work-to-50 interval crosses zero. |
| [AgentProcessBench Wilson](tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentprocessbench-wilson/full-execution-report.md) | **supports** the same AP signal under an adaptive score and **leaves unresolved** work reduction | Complete valid reused-target evidence; all family point estimates improve, but the work interval still crosses zero. |

The two AgentProcessBench constructions close the same-target score-search
branch. The second is adaptive because target results had already been observed.
A third variant would be target retuning rather than stronger external evidence.

## Current Novelty Map

| Plain statement | Same-claim risk | Current judgment |
|---|---:|---|
| Agent behavior can be stored as weighted fielded observations. | Very high | Necessary infrastructure; not novelty. |
| Fielded observations can be grouped into hierarchical views. | Very high | Profilers, OLAP/trace query systems, pprof labels, and semantic clustering already do this. |
| Agent observability needs profiling, not only debugging. | Medium | The fixed broad position remains valuable if demonstrated on recurring measured behavior and real decisions. |
| A conserved cross-layer record can attribute additive resources to semantic responsibility across runs. | Medium/high | Potential systems contribution; requires independent lineage and attribution truth. |
| A plan-defined semantic profile concentrates real problems and reduces analyst inspection. | High | AgentProcessBench establishes significant target-blind AP concentration; HINTBench and TraceElephant add favorable inspection regions on independent public workloads. High-recall tail efficiency remains mechanism-dependent. |

Two additional close neighbors sharpen this boundary. *Agentic AI Process
Observability* applies process and causal discovery across agent execution logs
(<https://ceur-ws.org/Vol-4087/paper3-Long.pdf>), while AgentDiagnose analyzes
semantic trajectory competencies and validates them against human judgments
(<https://aclanthology.org/2025.emnlp-demos.15/>). AgentProf must distinguish
itself through weighted cross-layer responsibility attribution and query-time
operation stacks, not through cross-run analysis or semantic visualization
alone.

## Open Evidence And Search Frontier

1. **RQ1 — resource attribution.** Step 0007 supplies the current end-to-end
   replay result on R114's fixed real-task suite. Its scope is the declared
   process/tool lineage and R114-compatible AgentSight 0.2.37 capture path; it
   is not arbitrary causal attribution or automatic task inference.
2. **RQ2 — real-problem localization.** The cumulative AgentProcessBench,
   HINTBench, and TraceElephant evidence supplies an evidence-backed positive
   answer for target-blind problem concentration and useful inspection regions.
   The strict TraceElephant 80%-recall construction remains inconclusive and
   bounds only its high-recall tail. Do not reopen AgentProcessBench scoring,
   HINTBench/TraceElephant tuning, the target-dropping AgentNet key, or completed
   negative branches without materially new evidence.
3. **RQ3 — tag accuracy.** Evaluate the actual prompt/intent attribution path
   and approved fixed mappings on held-out agents and task families, including
   coverage, stability, and downstream attribution sensitivity. Step 0008 now
   supplies positive independent task-partition evidence on Mind2Web and
   ScienceWorld; Step 0006 supplies group-boundary evidence. Structured phase
   mapping alone cannot authorize every tag backend, and a new dataset is not
   justified merely to fill the remaining cells.
4. **RQ4 — profiling cost.** Step 0005 supplies the paper-level construction
   answer: current `agentpprof 0.2.37` builds the 27,765-operation semantic
   union in 1.17 s median with 464.49 MiB maximum RSS, while R160 separately
   supports the predecessor shared-cache mechanism. Do not reopen another
   cost/cache variant.

Step 0006 completed the RQ3 human-boundary component, Step 0007 completed the
selected RQ1 exact-lineage replay, and Step 0008 added independent RQ3 task-
partition evidence. The current whole-paper review identifies one lower-cost
candidate before any new experiment: synthesize the already completed RQ2
native, independent-step, session, flat, raw-action, width-only, matched-
permutation, and oracle controls under their existing predeclared metrics. Only
if that complete reuse cannot change the paper-level utility answer should the
next experiment add a new mechanism or source.

## Search Policy And Reopen Conditions

- Prefer official public benchmarks, real systems/software, real trajectories,
  published protocols, and source-native artifacts. Custom scripts are thin
  conversion/evaluation glue.
- One next experiment answers one fixed RQ and tests one hypothesis. REAL
  PREFLIGHT proves contact only; the approved full matrix must finish before
  interpretation.
- Preserve every valid negative, invalid, and inconclusive branch internally.
  Do not insert it into the reader-facing positive story unless it bounds a
  final claim.
- Reopen a completed branch only when a new external source, changed measured
  signal, corrected fairness boundary, or stronger accepted protocol changes
  the scientific question. A different score on the same observed target is not
  a reopen condition.
- Do not treat reviewer objections or literature neighbors as authority to
  change the fixed thesis, four RQs, motivation, contribution scope, or
  positive hypotheses.
