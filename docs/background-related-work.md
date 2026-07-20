# AgentProf Literature And Novelty Frontier

**Last primary-source verification:** 2026-07-19, Step 0048 literature refresh.

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

RQ1 now has a complete scoped real-Codex lineage result, RQ4 has a complete
current-binary construction-cost result, and RQ3 has positive held-out boundary
and task-partition evidence plus direct declared task/action-label measurements.
Steps 0017--0018 established that the former
information-gain inducer remained below the strongest simple controls. Steps
0020--0024 replace that objective with cross-session action recurrence, diagnose
identity-dominated global calibration on existing CodeTraceBench trajectories,
and adopt one monotone repair: action-changing pairs use
`min(global_cutoff, cross_action_cutoff)`. The final Rust path exactly matches
the fixed evaluator, preserves all 3,691 OSWorld decisions, and raises
CodeTraceBench B-cubed F1 from 0.475 to 0.649 relative to the prior global
constructor. External phase change remains slightly higher on pooled B-cubed
F1 (0.654) but lower on boundary F1 (0.225 versus 0.287). This is post-hoc
implementation-selection evidence on two reused populations, not independent
confirmation or an answer to every RQ3 tag type. The bounded recurrence repair
branch is closed; see the
[`Step 0024 whole-paper review`](tmp/build-and-evaluate/step-0024-20260715T042557-0700/whole-paper-review.md).

The Step 0018 source-grounded whole-paper review disputed the then-current
cumulative positive RQ2 synthesis because its metrics and information sets were
not yet aligned. Step 0036 later re-evaluated the complete AgentProcessBench,
HINTBench, and TraceElephant populations with standard per-query AP/MAP on
information-matched semantic and raw-action organizations. Semantic grouping
improves MAP on all three. Step 0037 reuses those populations for a post-hoc
mechanism analysis: a local-first ranker preserves every strict operation-local
ordering and uses semantic recurrence only for exact ties; it improves over
local-only and semantic-only on all three, and over a matched local-plus-raw
tie-breaker on HINTBench and TraceElephant. These results support problem
ranking, not automatic human-productivity or lower-work claims. Step 0019
separately tests a fixed rank-hidden LLM reader on existing assets and supports
the registered recall and precision comparison on six tasks. It remains bounded
downstream-use evidence inside unchanged RQ2, not a new story.

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
- [NVIDIA NeMo Agent Toolkit Profiler](https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/profiler.html)
  instruments supported agent workflows, aggregates per-invocation token and
  latency data, and reports throughput, bottleneck, and concurrency analyses.
  It is the closest named agent profiler; AgentProf's remaining distinction is
  heterogeneous completed histories plus source-linked conserved agent/system
  effects and selectable pprof-compatible semantic projections.
- [Pivot Tracing](https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems/)
  dynamically selects, filters, and groups metrics across causally related
  component events. It makes independent lineage fidelity, not only mass
  conservation, a required RQ1 comparison.
- [Activity Mining by Global Trace Segmentation](https://www.vdaalst.com/publications/p586.pdf)
  and [Flexible Activity Trees](https://arxiv.org/abs/2010.08302) discover
  higher-level activities and hierarchical abstractions from low-level event
  logs. They are serious RQ3 mechanism/baseline precedents; always-cut,
  action-change, and phase-change controls do not represent this family.
- [Grosz and Sidner's discourse model](https://aclanthology.org/J86-3001/)
  represents the dynamically active, open-ended purposes of discourse as a
  stack of focus spaces: a subordinate purpose pushes, while returning to a
  dominating purpose can pop one or more spaces. This is the closest conceptual
  precedent for an incrementally maintained semantic task stack. Push/pop and
  variable-depth intention stacks are therefore not independently novel; the
  AgentProf opportunity is to infer such a stack from real agent histories with
  a small local model, attach conserved operation weights and effects to its
  active path, and fold recurring paths across runs.
- [Hierarchical event abstraction](https://doi.org/10.1109/ICPM53251.2021.9576868)
  formalizes multiple activity-instance levels over event logs. It reinforces
  that hierarchy construction is an established problem while leaving a direct
  semantic task-stack backend and its agent-profiling consequences open.
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

- [Bouzenia and Pradel's ASE 2025 trajectory
  study](https://arxiv.org/abs/2506.18824) analyzes 120 real AutoCodeRover,
  OpenHands, and RepairAgent trajectories and releases a shared action
  annotation framework. Its categories combine known-tool mappings with manual
  resolution of remaining actions. Together with the [TraceView companion
  guide](https://arxiv.org/abs/2606.22110), it supplies Step 0032's published
  targets and declared operational definitions and prevents novelty claims
  based only on defining a software-agent action taxonomy.
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
- [WebGraphEval](https://arxiv.org/abs/2510.19205), a NeurIPS 2025 workshop
  paper, canonicalizes actions from 4,768 WebArena trajectories across six
  agents, merges recurring behavior into weighted action graphs, and overlays
  reward propagation and success-weighted transition statistics. It prevents a
  claim that AgentProf first creates a weighted cross-agent representation of
  recurring actions or first uses it to expose redundancy, inefficiency, and
  critical decisions. It does not join low-level system effects, conserve
  arbitrary additive measures, provide selectable field hierarchies, or export
  conventional profiler data.
- [Agent Mentor](https://arxiv.org/abs/2604.10513) analyzes semantic features in
  execution logs, derives corrective system-prompt instructions, and reports
  repeated-run accuracy improvements across three agent configurations. It is
  direct precedent for a semantic trajectory analysis-to-intervention loop,
  though its target is prompt ambiguity rather than conserved system effects.
- [AgentGraph](https://ojs.aaai.org/index.php/AAAI/article/view/42393), published
  in the AAAI-26 Demonstration Track, converts agent logs into source-linked
  knowledge graphs and supports failure detection, optimization
  recommendations, perturbation tests, and causal attribution. It is evidence
  of AAAI relevance and a competing trace representation, not a Main-Track
  precedent for AgentProf's exact claim.
- [TraceProbe](https://arxiv.org/abs/2607.06184) normalizes 2,500 coding-agent
  trajectories from five SWE-bench Verified production settings into canonical
  actions and deterministic effect labels, then reports recurring anti-patterns,
  reference-scoped divergence, milestones, tokens, duration, failed work, and
  setting-level process profiles. This July 2026 preprint is the closest current
  academic terminology/capability neighbor: it prevents novelty claims based on
  canonical agent actions, cross-run process profiles, or resource-aware
  trajectory comparison alone. It remains coding-specific and does not join
  system effects across observability layers, expose query-time semantic stacks,
  conserve arbitrary additive measures, or emit pprof-compatible profiles.
- [Process-Centric Analysis of Agentic Software Systems](https://doi.org/10.1145/3798271),
  published at OOPSLA 2026, encodes temporal and semantic relations in
  Graphectory graphs over 4,000 SWE-agent and OpenHands trajectories, derives
  process-centric metrics and strategies, and uses them for online monitoring
  and intervention. It is the closest archival process-centric comparison.
  AgentProf's residual distinction is the conjunction of source-linked agent
  and operating-system effects, conservation of arbitrary additive measures,
  and query-selected pprof operation stacks over one heterogeneous corpus.
- [AgentLens](https://arxiv.org/abs/2605.12925) evaluates 2,614 OpenHands
  trajectories and labels exploration, implementation, verification, and
  orchestration from trajectory history rather than tool identity alone. Its
  1,815-trajectory subset shows that successful outcomes can hide recurrent
  process defects. This is a strong context-sensitive RQ3 and downstream-process
  precedent, but its promised dataset/SDK repository was still unavailable on
  2026-07-19.
- [ProcBench](https://arxiv.org/abs/2605.20251) evaluates process defects and
  control preservation on 200 annotated AndroidBench, TerminalBench, and
  SWE-bench Verified trajectories. It further establishes process-level
  evaluation beyond final success, while using an annotation ontology and
  calibrated scorecards rather than conserved population profiles.
- [CodeTracer / CodeTraceBench](https://arxiv.org/abs/2604.11641) reconstructs
  hierarchical state-transition traces and supports failure localization and
  replay with author-annotated stages. It is both the source for Step 0024's
  reused 405-trajectory implementation-selection population and a closest trace
  representation; AgentProf's claim is cross-trajectory aggregate profiling,
  not first hierarchical state reconstruction.
- [CHIEF](https://arxiv.org/abs/2602.23701) combines hierarchical agent traces
  with counterfactual reasoning and reports that hierarchy alone is
  insufficient for failure attribution. [Signals](https://arxiv.org/abs/2604.00356)
  uses blinded expert judgments and matched sample budgets to measure whether
  selected trajectories are developer-informative. Together they motivate a
  consequential same-input comparison rather than another visualization or
  grouping-only metric.

The completed Hodoscope experiment reproduced the official iQuest behavior and
found that the tested recursive AgentProf construction did not beat the released
density-gap/FPS bundle. This is a valid mechanism boundary, not a replacement
thesis. Full evidence remains in
[`cycle-0001/.../loop-rq2-02/result-review.md`](tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/result-review.md).

### Standards And Production Observability

- [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai)
  define GenAI spans, events, and metrics.
- [OpenTelemetry Profiles](https://opentelemetry.io/docs/specs/otel/profiles/)
  entered public alpha in 2026. Its pprof-superset format can link profile
  samples to trace/span IDs and correlate profiles with logs, metrics, and
  traces through shared resource context. Therefore neither pprof compatibility
  nor profile--trace linkage is independently novel. The remaining distinction
  is deriving an agent-level semantic responsibility hierarchy over joined
  effects and completed heterogeneous histories, rather than linking code-stack
  samples to request context.
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
- [Laminar Signals](https://laminar.sh/docs/signals/introduction) derives
  structured trace-linked events and supports querying, clustering, alerting,
  and backfilling them across trajectories. It is same-problem evidence, while
  leaving source-linked low-level effects and conventional profiler export as
  possible AgentProf distinctions that still require a same-input test.
- [LangSmith Engine](https://docs.langchain.com/langsmith/engine) turns
  recurring trace-supported issues into proposed code or prompt fixes,
  deployable evaluators, offline examples, and optional pull requests. It is a
  product-level diagnosis-to-action competitor, not merely another trace UI.
- [AgentTelemetry](https://dl.acm.org/doi/10.1145/3805760.3814931) supplies an
  agent-specific span taxonomy, fault-detection benchmark, and toolkit. Its
  accepted artifact has no released official fault-bearing step/span target,
  so it is a capability and baseline precedent, not the selected localization
  source.

These sources make generic observability, semantic grouping, trace taxonomy, and
fault-detection claims high risk. AgentProf's defensible distinction must be
tested as cross-layer additive responsibility profiling and decision-relevant
aggregation, not asserted from terminology.

For partition fidelity, [B-cubed](https://aclanthology.org/C98-1012/) is an
established per-item external clustering measure; a later formal comparison
finds it satisfies the stated clustering-quality constraints
(<https://doi.org/10.1007/s10791-008-9066-8>). Exact boundary
precision/recall/F1 is the complementary discrete-transition measure used by
the current RQ3 experiments. These standard metrics should remain primary and
secondary respectively; adding ARI, NMI, or a custom aggregate would not repair
an information or construct-validity defect.

### Failure And Problem Localization

- [AgentRx](https://arxiv.org/abs/2602.02475) releases 115 manually annotated
  failed trajectories across three domains. Its LLM judge consumes a structured
  constraint-validation log to localize the critical failure step and category.
  This is direct protocol precedent for a fixed LLM making a diagnostic choice
  from trajectory-derived evidence, but not a same-input profiler baseline.
- [MP-Bench](https://arxiv.org/abs/2603.25001) releases 289 failed multi-agent
  executions from 121 configurations with three independent expert annotations
  per instance. Only 16.2% of annotated failure steps have three-expert
  consensus, and the paper evaluates graded responsibility rankings with
  standard nDCG@5 and nDCG@full under linear and exponential gains. This is the
  strongest current RQ2 protocol for ambiguous failure responsibility. Its
  public artifact contains annotations and upstream-log links, but no reusable
  target-blind prediction output; gold-derived group scoring would not be a new
  end-to-end localization experiment.
- [AgentLocate](https://arxiv.org/abs/2607.07989) jointly identifies a
  responsible agent and earliest decisive step and evaluates agent-level and
  tolerance-aware step localization on Who\&When and Aegis-Bench. It is a
  direct localization competitor and possible future fixed-signal input, but
  no official runnable artifact was found in the bounded 2026-07-19 search.
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

For fixed-reader evaluation, [Shi et
al.](https://aclanthology.org/2025.ijcnlp-long.18/) show position bias across
list-wise and pairwise LLM judging. A reader experiment must therefore hide the
existing query-aware rank and ordinal identifiers, use identical presentation
and budgets across matched views, and retain the original rank as a separate
control rather than prompt evidence.

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
| A plan-defined semantic profile concentrates independently annotated real problems. | High | Standard per-query AP/MAP improves over matched raw-action organization on all three complete public workloads; the post-hoc local-first analysis isolates additional semantic value on HINTBench and TraceElephant. Hodoscope, Datadog Patterns, LangSmith Insights, WebGraphEval, TraceGraph, TraceProbe, MP-Bench, and AgentLocate make generic cross-run discovery or failure localization non-novel. AgentProf's distinct question is whether a conserved selectable responsibility view improves matched organization of the same evidence. |
| Semantic profiling reduces human inspection or improves repair outcomes. | Very high | The fixed-reader result is bounded supporting evidence, while Hodoscope and TraceGraph provide stronger published inspection/intervention precedents. AgentProf should not imply this consequence without a direct matched test; the larger profiling thesis does not depend on claiming it prematurely. |

Two additional close neighbors sharpen this boundary. *Agentic AI Process
Observability* applies process and causal discovery across agent execution logs
(<https://ceur-ws.org/Vol-4087/paper3-Long.pdf>), while AgentDiagnose analyzes
semantic trajectory competencies and validates them against human judgments
(<https://aclanthology.org/2025.emnlp-demos.15/>). AgentProf must distinguish
itself through weighted cross-layer responsibility attribution and query-time
operation stacks, not through cross-run analysis or semantic visualization
alone.

## Open Evidence And Search Frontier

1. **RQ1 — resource attribution.** Step 0007 supplies source-lineage and
   lossless-folding evidence on R114's fixed real-task suite. Its scope is the
   declared process/tool lineage and R114-compatible AgentSight 0.2.37 capture
   path; it is not arbitrary causal attribution or automatic task inference.
   R170 mixedness is conditional on prompt tags that also define the reference
   categories, so the next highest-value candidate is a same-input comparison
   with an independently defined responsibility outcome, reusing the completed
   real trajectories before seeking a new external asset.
2. **RQ2 — real-problem localization.** Step 0036 establishes positive standard
   MAP differences over matched raw-action organization on all three complete
   public populations. Step 0037's post-hoc local-first analysis preserves
   operation-local evidence and shows that semantic recurrence is useful as a
   tie refinement, but it is not untouched confirmation. Do not reopen the same
   score, cutoff, or observed benchmark branches. Step 0019 completes one
   different downstream decision over all 18 R315 packets: the fixed reader
   improves selected-positive recall on 5/6 tasks and precision on 4/6 versus
   the matched fixed-session packet. Flat remains a lower bound and visible
   order a control; the result does not establish human productivity or
   universally lower work. The remaining paper-level question is whether the
   current standard-MAP and fixed-reader evidence is sufficient against modern
   product and academic cross-trace analysis; another custom metric on the same
   targets is not useful. MP-Bench supplies a stronger multi-perspective
   protocol: graded expert consensus with nDCG@5/full. Reopen RQ2 for that
   protocol only when a published target-blind localizer output or simple fixed
   external scorer can be applied to all 289 logs. Using expert annotations to
   score or rank semantic groups would leak the evaluation target and is not an
   admitted experiment.
3. **RQ3 — tag accuracy.** Evaluate the actual prompt/intent attribution path
   and approved fixed mappings on held-out agents and task families, including
   coverage, stability, and downstream attribution sensitivity. Step 0008 now
   supplies positive independent task-partition evidence on Mind2Web and
   ScienceWorld; Step 0006 supplies group-boundary evidence. Steps 0020--0024
   establish the current recurrence constructor on OSWorld and reused
   CodeTraceBench trajectories, with the complete external phase-change
   tradeoff and post-hoc boundary above. Do not retune either observed
   population. Structured phase mapping alone cannot authorize every tag
   backend. Step 0031 now supplies a different literal-label measurement on the
   complete released [AgentBoard](https://proceedings.neurips.cc/paper_files/paper/2024/hash/877b40688e330a0e2a3fc24084208dfa-Abstract-Datasets_and_Benchmarks_Track.html)
   goal population: the fixed Qwen3.6-27B path reaches 0.695 macro-F1 and 0.733
   accuracy across nine declared families, versus majority 0.044 and 0.248,
   with exact three-run stability. Step 0032 adds all 2,737 published action
   labels from 120 ASE software-engineering trajectories: the same fixed backend
   reaches 0.498 macro-F1 versus 0.061 majority, with a +0.437 whole-trajectory
   bootstrap effect [0.380, 0.494] and exact two-run stability. These results
   support the named backend under declared task and action label sets, not
   literal phase identity, unknown labels, or uniform cross-framework accuracy.
   No next constructor experiment is admitted merely to fill another evidence
   cell. Step 0034's bounded source screen identifies a different calibration
   question on the already-complete trajectories: AAAI-22 provides precedent
   for transferring a threshold-related quantity using score-distribution
   shape, while ACL-23 and EMNLP-24 establish limited-label calibration and
   rank-scale comparability. The complete bidirectional test finds that an
   empirical-percentile cutoff beats direct raw-cutoff transfer but remains
   below the current label-free constructor on both OSWorld-Human and
   CodeTraceBench. Thus scale mismatch is real, while desired grouping
   semantics remain domain dependent under this scalar interface. This closes
   the tested transfer mechanism without claiming novelty for quantiles,
   reopening target-specific recurrence tuning, or changing RQ3.
4. **RQ4 — profiling cost.** Step 0005 supplies the paper-level construction
   answer: current `agentpprof 0.2.37` builds the 27,765-operation semantic
   union in 1.17 s median with 464.49 MiB maximum RSS, while R160 separately
   supports the predecessor shared-cache mechanism. Do not reopen another
   cost/cache variant.

The current source screen finds direct precedent for the fixed-reader decision
in AgentRx and AgentDiagnose and accepted evidence that order must be hidden.
No official tool consumes the R315 packet format, so Step 0019 used one thin
collection/scoring adapter. Raw action remains a strong paper-level
counterpoint; because R315 has no matched raw-action packet, the positive Step
0019 result supports only operation-stack versus execution-local prioritization,
not universal view dominance.

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
