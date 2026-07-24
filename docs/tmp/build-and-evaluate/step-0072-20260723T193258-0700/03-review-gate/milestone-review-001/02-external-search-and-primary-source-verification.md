# External Search and Primary-Source Verification

**Timestamp:** 2026-07-23T20:07:16-07:00  
**Parent:** `step-0072-20260723T193258-0700/03-review-gate/milestone-review-001`  
**Objective:** Attack the blind review’s novelty, benchmark, baseline, protocol, and practicality hypotheses using primary sources from both agent/AI and systems/observability communities.

## Inputs and provenance

This phase began only after the blind assessment was written to `01-blind-full-paper-read-and-attack-map.md`. Sources include official product/specification documentation, archival paper pages/PDFs, official repositories, and primary arXiv/OpenReview papers where no archival version is available. Search snippets and third-party summaries were used only to discover primary sources and are not treated as evidence below.

The paper’s own bibliography was used as one seed set, but the search was deliberately expanded beyond cited work. In particular, it uncovered ACT*ONOMY and CHIEF, which are not discussed in the paper and materially affect the same-claim attack.

## Search method

### Questions

1. Is recursive cross-run semantic categorization with metric rollups already present in commercial observability?
2. Does adjacent academic work already construct shared semantic behavior profiles, hierarchical task structures, or cross-run decision graphs?
3. What consequence do the strongest adjacent papers demonstrate: visualization only, review effort, attribution accuracy, or actual agent improvement?
4. Do the three RQ2 datasets define MAP as an official task, or is AgentProf introducing a new repurposed retrieval protocol?
5. What exactly do OSWorld-Human “groups” and CodeTraceBench “stages” mean?
6. Does matching raw source evidence matter according to the benchmark literature?
7. Are pprof labels, tag filtering, pseudo-frames, and trace linkage real standard capabilities?
8. What cost, scale, uncertainty, and submission-format bars do official sources establish?

### Representative queries

- `Datadog LLM Observability Patterns hierarchical topics metrics cost tokens`
- `LangSmith Insights hierarchical categories traces aggregated metrics`
- `TraceProbe 2607.06184 canonical actions tokens failed work`
- `Process-Centric Analysis Agentic Software Systems Graphectory`
- `Hodoscope 2604.11072 review effort baseline`
- `TraceGraph 2605.31308 shared decision landscapes recovery`
- `WebGraphEval recurring canonical actions weighted graph`
- `"semantic profiling" AI agents trajectories profiling pprof`
- `How to Interpret Agent Behavior ACTONOMY hierarchical taxonomy profiles`
- `hierarchical failure attribution agent trajectories CHIEF`
- `AgentProcessBench evaluation protocol metrics`
- `HINTBench risk-step localization metrics`
- `TraceElephant evaluation metrics agent step accuracy`
- `CodeTraceBench stage labels`
- `OSWorld-Human grouped actions`
- `google pprof tagroot tagleaf focus labels official`
- `OpenTelemetry Profiles pprof trace link official`
- `AAAI 2027 author kit page limit`

### Source-family coverage and exclusions

| Community/source family | Included primary sources | Why included | Excluded/discovery-only material |
|---|---|---|---|
| Commercial observability | Datadog Patterns; LangSmith Insights; NVIDIA NeMo Agent Toolkit profiler | Current operational status quo for categories, rollups, drilldown, cost, and profiling | Marketing blogs and generic “agent observability” explainers |
| Profiling standards | Google pprof documentation; OpenTelemetry Profiles specification | Verifies standard output, labels, pseudo-frames, filtering, and trace linkage | Secondary pprof tutorials |
| Cross-run agent analysis | Graphectory/OOPSLA; TraceProbe; Hodoscope; TraceGraph; WebGraphEval; ACT*ONOMY | Same problem, same representation, or stronger downstream consequence | Citation-count sites and model summaries |
| Failure attribution | TraceElephant/ACL; MP-Bench; CHIEF | Accepted protocols and hierarchy/observability baselines | Blog summaries |
| RQ2 datasets | AgentProcessBench/KDD; HINTBench; TraceElephant/ACL | Verifies label constructs and official metrics | Third-party benchmark descriptions |
| RQ3 datasets | CodeTracer/CodeTraceBench paper and released dataset description; OSWorld-Human/MLSys and official repository | Verifies what stages/groups mean | Unversioned derivative summaries |
| Venue | AAAI-27 official conference/author-kit materials and repository’s official template | Submission status and formatting expectations | Forum anecdotes |

Preprints from 2026 are explicitly treated as non-archival unless an archival venue is verified. Graphectory (PACMPL/OOPSLA), AgentProcessBench (KDD), TraceElephant (ACL), and OSWorld-Human (MLSys 2026 paper header) have stronger publication provenance than the arXiv-only comparisons.

## Verified source findings

### 1. The status quo already supplies much of the paper’s high-level “missing layer”

The [Datadog Patterns documentation](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) states that it summarizes interactions, embeds them, clusters them, generates meaningful topics, builds a parent-child topic hierarchy, attributes each interaction to one topic, rolls up interactions/cost/tokens/errors/latency/evaluations per topic, and drills down to individual interactions. It supports filtering to failures and comparing topic distributions across runs.

The [LangSmith Insights documentation](https://docs.langchain.com/langsmith/insights) likewise says it automatically analyzes traces, constructs top-level categories and subcategories, aggregates errors/latency/cost/feedback/attributes, supports user-defined extracted attributes that influence categorization, and drills down to individual traces. It can ingest external chat histories and reports typical per-1,000-thread model cost.

**Source-supported fact:** recursive/hierarchical cross-trace semantic categorization, metric rollups, and drilldown already exist in major products.

**Reviewer inference:** AgentProf’s novelty cannot rest on “existing tools do not provide hierarchical semantic grouping with aggregate metrics.” The narrower differentiators are: recursively marked *within-trace intervals* rather than one trace/interactions-to-topic assignment; conservation of arbitrary additive source measures; source-call evidence below semantic frames; backend-neutral annotation replay; and standard pprof output. The paper currently states this narrower combination, but it does not experimentally compare against the actual product behavior or show which user decision the combination uniquely enables.

### 2. A previously uncited paper is unusually close to the semantic-profile claim

[ACT*ONOMY, “How to Interpret Agent Behavior”](https://arxiv.org/abs/2605.13625), begins from the same premise: Claude Code and Codex operate for hours or days, raw natural-language traces are hard to interpret at scale, and developers need to diagnose inefficiency/failure and improve oversight. It contributes a three-level hierarchy of 10 actions, 46 subactions, and 120 leaf categories plus an automated, quote-grounded trace-analysis pipeline. Its experiments explicitly compare behavioral profiles across agents and across diverse trajectories and surface failure-mode patterns.

**Source-supported fact:** shared hierarchical semantic vocabulary plus automatic trajectory annotation plus cross-run behavioral profiles predates the current submission as a public May 2026 preprint.

**Reviewer inference:** this is the closest same-claim novelty risk and must be compared directly. AgentProf may remain novel through variable-depth responsibility intervals, additive conservation, task/object/result rather than a fixed action taxonomy, native evidence composition, and pprof interoperability. Without a direct comparison, however, the paper’s broad “semantic profiling for agents” identity is not securely differentiated.

### 3. Strong adjacent work demonstrates downstream consequences beyond profile correspondence

The archival [Graphectory paper](https://doi.org/10.1145/3798271) automatically analyzes 4,000 SWE-agent/OpenHands trajectories, builds temporal/semantic process graphs, reports process-centric metrics, and uses online monitoring/intervention to improve resolution rates by 6.9%–23.5% on problematic instances with near-zero reported overhead.

[Hodoscope](https://arxiv.org/abs/2604.11072) compares group-wise behavior distributions and measures review effort directly: confirmed issues appear within the first four ranked actions across three testbeds, with a reported 6–23× reduction relative to uniform review. It also discovers a previously unknown benchmark vulnerability and shows that discovered behavior descriptions can improve weaker judges.

[TraceGraph](https://arxiv.org/abs/2605.31308) constructs pooled cross-model decision landscapes, identifies trap regions, and demonstrates a downstream recovery policy that raises official SWE-bench resolved rate on fired subsets. [WebGraphEval](https://arxiv.org/abs/2510.19205) canonicalizes and merges recurring actions into weighted cross-agent graphs and analyzes reward, redundancy, efficiency, and decision points. [TraceProbe](https://arxiv.org/abs/2607.06184) canonicalizes actions/effects across 2,500 trajectories and identifies localization/completion/failed-work signals rather than relying only on outcome rate.

**Source-supported fact:** the nearest literature no longer stops at “the representation corresponds to labels.” It tests review effort, failure-attribution accuracy, or an intervention’s official task outcome.

**Reviewer inference:** for AAAI/MLSys acceptance, AgentProf needs at least one matched downstream consequence of its specifically semantic hierarchical representation. RQ2’s current Local+AgentProf improvement over Local is not enough because the information-matched raw-action view is indistinguishable.

### 4. Hierarchical task decomposition is already an explicit failure-attribution mechanism

[CHIEF](https://arxiv.org/abs/2602.23701) transforms flat multi-agent logs into a hierarchical causal graph, decomposes tasks into subtasks, aligns continuous ranges to the trajectory, builds observation/thought/action/result nodes and dependencies, and performs top-down attribution. It compares eight baselines, reports agent/step accuracy, ablates the hierarchy, evaluates several base models, and reports token cost.

**Reviewer inference:** CHIEF is not a population profiler and uses ground-truth/few-shot task exemplars in some configurations, so it does not subsume AgentProf. It does, however, invalidate any novelty language implying that semantic subtask hierarchy over trace intervals is itself new. AgentProf must claim and prove the *profiling* distinction: conserved population aggregation across runs and measures, not simply hierarchy construction.

### 5. The RQ2 benchmark repurposing uses a new protocol, not the benchmarks’ official tasks

[AgentProcessBench](https://arxiv.org/abs/2603.14465) contains 1,000 trajectories and 8,509 human-labeled steps with ternary process-quality labels and evaluates process reward models. [HINTBench](https://arxiv.org/abs/2604.13954) defines trajectory risk detection, coarse risk-step localization, and fine risk-step/type identification; its headline localization metric is Strict-F1/Loc-F1, not MAP. The archival [TraceElephant paper](https://aclanthology.org/2026.acl-long.912.pdf) defines responsible-agent and decisive-step prediction and reports exact agent-level and step-level accuracy (plus a fixed tolerance), averaged over three independent runs.

**Source-supported fact:** none of these primary benchmark protocols defines AgentProf’s “each target-bearing trajectory is a query, rank all operations, report AP/MAP” task as its official main evaluation.

AP/MAP is a standard retrieval metric, and AgentProf cites a primary SIGIR source. The issue is not that MAP is invented. The issue is that the *benchmark task construction* is new: target-bearing trajectories only, zero-positive trajectories excluded from scoring, localizer predictions reinterpreted as local scores, group-level Wilson lower bounds, and a 24-order validation selection for HINT.

**Reviewer inference:** RQ2 should be presented as a new cross-benchmark localization protocol, with construct validation and an explicit explanation of why AP/MAP answers the profiling-inspection question better than each benchmark’s official F1/accuracy. The current sentence “run complete workloads” can mislead readers into assuming official benchmark evaluation. A human-review/work metric, as in Hodoscope, or official accuracy/F1 alongside MAP would make the result much stronger.

### 6. Information matching is scientifically necessary and the current matched baseline is directionally sound

The [TraceElephant paper](https://aclanthology.org/2026.acl-long.912.pdf) shows that full trace inputs and metadata materially affect attribution: removing input/context reduces step-level accuracy, and full traces improve step-level accuracy by up to 76% relative to output-only traces. Its ablation explicitly controls observability fields.

**Reviewer inference:** AgentProf is correct to retain identical source-kind/tool/call/outcome evidence in the raw-action baseline. The updated baseline fixes a real confound rather than over-controlling away the contribution. Because semantic and raw prefixes are statistically indistinguishable on all three workloads, the sound conclusion is that the experiment establishes complementarity to a local diagnostic but not a target-ranking advantage from semantic ancestry. This result should redirect the next experiment toward a hierarchy-dependent decision, not toward weakening the matched baseline.

### 7. OSWorld-Human groups are an efficiency/batching construct, not general semantic responsibility

The archival [OSWorld-Human PDF](https://arxiv.org/pdf/2506.16042) explains that grouped actions are consecutive actions executable from the same visual observation, such as click–type–enter. The purpose is to estimate how many observation/planning/model calls can be reduced. The dataset was built in two passes by two graduate annotators, cross-validated, and replayed successfully in OSWorld. Its official metric is Weighted Efficiency Score (WES), not B³ or semantic-stage fidelity.

**Source-supported fact:** the group boundary means “new visual observation/planning may be required,” not “new semantic task/subtask responsibility begins.”

**Reviewer inference:** boundary F1 and B³ against these groups validly evaluate whether recurrence recovers OSWorld’s batching partitions. They do **not** independently validate the paper’s variable-depth semantic operation hierarchy or stable cross-run operation identity. The current RQ3 wording mostly calls them groups/boundaries, but the abstract and combined RQ3 answer risk treating them as evidence for automatic semantic responsibility.

### 8. CodeTraceBench stages are failure-localization stages, not a gold recursive responsibility tree

The [CodeTracer/CodeTraceBench paper](https://arxiv.org/pdf/2604.11641) constructs hierarchical traces for failure-onset localization, annotates stage- and step-level failure-critical behavior, and reports localization/replay outcomes. Its source describes the benchmark as containing thousands of trajectories across four frameworks/five model backbones and explicitly focuses on where failure becomes critical.

**Reviewer inference:** a contiguous stage partition is a reasonable independent segmentation target for A2, and B³/boundary F1 are legitimate partition/segmentation measures. But a flat stage partition does not validate canonical cross-session semantic identity, recursive depth, or resource-responsibility meaning. The paper needs to separate:

1. boundary/partition agreement with failure-analysis stages;
2. semantic name agreement/cross-run identity;
3. recursive hierarchy quality.

At present, A2’s strongest result validates the first, while canonicalization preserves boundaries but is not externally scored for the second or third.

### 9. The standard-output claim is real but is not by itself a novelty moat

Official [Google pprof documentation](https://github.com/google/pprof/blob/main/doc/README.md) confirms string/numeric sample tags, `tagfocus`/`tagignore`, tag breakdowns, and `tagroot`/`tagleaf` pseudo-frames. The [OpenTelemetry Profiles specification](https://opentelemetry.io/docs/specs/otel/profiles/) defines a pprof-compatible/superset profile signal with resource/scope context and direct trace/span links.

**Reviewer inference:** AgentProf’s use of pprof is technically credible and operationally attractive. However, pprof already provides arbitrary tag-based pseudo-hierarchies, and OTel Profiles provides standardized trace linkage. The scientific novelty must be the method and validated value of deriving/replaying semantic responsibility—not protobuf serialization.

### 10. Current profilers set a higher cost and performance baseline

The official [NVIDIA NeMo Agent Toolkit profiler documentation](https://docs.nvidia.com/nemo/agent-toolkit/1.4/improve-workflows/profiler.html) records per-invocation tokens/time/LLM calls in real time, computes workflow latency/throughput/bottleneck/concurrency metrics, and supports several agent frameworks. Newer documentation reports percentile-based per-call forecasts and critical-path/fan-out signals.

**Reviewer inference:** RQ4’s fixed-mark parser/folder timing is a useful microbenchmark, but it does not compare against a current workflow profiler, measure live instrumentation, or include the automatic annotation that differentiates AgentProf. It therefore cannot support an end-to-end practicality claim at the cross-domain bar.

### 11. The current PDF is not AAAI submission-compliant

The official [AAAI-27 page](https://aaai.org/conference/aaai/aaai-27/) confirms the target and author kit. The repository’s official `AnonymousSubmission2027.tex` says event-specific page limits govern, forbids layout tricks, and recommends cutting text/figures/tables when overlength. The project’s own venue README states seven main-content pages and at most nine total, while the current PDF has 12 pages and main content through page 10.

**Reviewer inference:** regardless of scientific score, submission completion is impossible without a substantial WRITE pass after evidence selection.

## Source verification matrix by load-bearing claim

| Paper claim | Primary-source result | Effect on attack map |
|---|---|---|
| Existing tools lack the profiling abstraction | Datadog/LangSmith already provide automatic hierarchical categories, metric rollups, and drilldown. | Novelty risk **increases**; retain only narrower interval/conservation/evidence/pprof combination. |
| Semantic behavior profiling is new | ACT*ONOMY provides hierarchical taxonomy, automatic quote-grounded annotations, and cross-agent behavioral profiles. | Previously missing closest work; **major novelty risk**. |
| Population structure should help diagnosis | Hodoscope, Graphectory, TraceGraph, CHIEF demonstrate review-effort, accuracy, or intervention gains. | Expected evidence bar **rises** beyond correspondence/MAP-vs-Local. |
| RQ2 uses benchmark-standard evaluation | Original benchmarks use ternary process scoring, localization F1, or exact agent/step accuracy. | MAP is standard but the cross-benchmark protocol is novel and needs validation. |
| Same evidence is a fair control | TraceElephant shows input/context fields materially change attribution accuracy. | Matched raw+evidence baseline is **validated as necessary**. |
| OSWorld groups are operation structure | They are actions executable under one visual observation, designed to reduce model calls. | Supports batching-boundary accuracy only; semantic construct claim **weakens**. |
| CodeTrace stages validate semantic hierarchy | They supervise stage/step failure localization, not recursive responsibility identity. | Supports flat partition/boundary evidence; identity/topology claim remains open. |
| pprof supports claimed output behavior | Official pprof and OTel docs verify labels, pseudo-frames, filtering, and links. | Technical credibility **strengthens**; serialization novelty weakens. |
| 1.16 s proves practical profiling | NeMo already provides real-time per-invocation profiling and richer workflow metrics. | End-to-end comparison/cost remains a major gap. |

## Contradictory and negative evidence

1. **Matched RQ2 parity:** paper’s own matched baseline contradicts semantic-prefix ranking superiority.
2. **Representation sensitivity:** TraceProbe finds file choice too coarse while function/completion behavior works; Hodoscope finds distance-only sampling can be worse than uniform. These sources reinforce that hierarchy/representation is not valuable merely because it is semantic.
3. **OSWorld construct mismatch:** recurrence may score well by discovering same-observation batching, not task responsibility.
4. **Products already roll up semantic categories:** weakens the paper’s claimed gap.
5. **Stronger consequence exists elsewhere:** Graphectory/TraceGraph/Hodoscope show intervention or review-effort outcomes that AgentProf lacks.

## Stronger reviewer-expected baselines and protocols

### RQ1

- Datadog/LangSmith-equivalent hierarchical topic/category grouping on the same trace summaries, if export/API access permits;
- genuine native source-tree and pprof tagroot/tagleaf projections;
- ACT*ONOMY fixed hierarchy;
- raw action, session-local, and randomized/flattened semantic ancestry with all evidence held constant;
- an independent responsibility/resource decision rather than only changing width.

### RQ2

- official benchmark metrics alongside MAP: ternary/process quality for AgentProcessBench, Strict/Loc-F1 for HINTBench, agent/step accuracy for TraceElephant;
- Hodoscope-style inspection work or time-to-first-confirmed-problem;
- CHIEF or official benchmark localizers where applicable;
- matched packet size, same source fields, same local score, same ranker, and semantic ancestry as the only changed variable;
- untouched benchmark-family transfer after freezing the view.

### RQ3

- ACT*ONOMY hierarchy/tagger or another published semantic taxonomy;
- untouched complete family for A2;
- name-identity scoring separated from flat partition/boundary scoring;
- multiple annotation runs and stability, model/version/prompt disclosure;
- OSWorld WES consequence if batching boundaries are retained as evidence.

### RQ4

- end-to-end automatic annotation plus construction;
- NeMo-like per-invocation/live baseline if live profiling is claimed, or explicit offline-only positioning;
- cold/warm and repeated-query cost;
- latency/token/monetary/GPU/CPU/RSS distributions;
- substantially larger realistic input and tail behavior.

## How search changed the attack map

The blind review treated RQ2 evidence weakness as the leading reject argument. That remains true, but external search adds a co-equal novelty problem: ACT*ONOMY plus Datadog/LangSmith already occupy much of the semantic behavior-profile space. The paper’s defensible novelty is now narrower and more technical, while the evidence must be stronger:

> variable-depth recurring responsibility intervals + conserved arbitrary additive measures + source-call evidence + standard profile output, shown to improve a hierarchy-dependent population decision.

This is not a recommendation to shrink the paper. It is a requirement to prove the larger profiling principle at the exact point where the novelty survives.

The search also changes RQ3 interpretation. The reported metrics are standard, but the gold constructs do not jointly validate “semantic operation stacks”: OSWorld groups validate batching under one observation; CodeTrace stages validate failure-analysis segmentation; task/action classifiers validate literal categories. Their heterogeneity is scientifically legitimate only if the paper explicitly treats them as separate necessary edges and adds one end-to-end semantic-profile consequence.

## Sources and artifacts

Primary links are embedded near each finding. The central evidence set is:

- [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/)
- [LangSmith Insights](https://docs.langchain.com/langsmith/insights)
- [ACT*ONOMY](https://arxiv.org/abs/2605.13625)
- [Graphectory](https://doi.org/10.1145/3798271)
- [Hodoscope](https://arxiv.org/abs/2604.11072)
- [TraceGraph](https://arxiv.org/abs/2605.31308)
- [TraceProbe](https://arxiv.org/abs/2607.06184)
- [WebGraphEval](https://arxiv.org/abs/2510.19205)
- [CHIEF](https://arxiv.org/abs/2602.23701)
- [AgentProcessBench](https://arxiv.org/abs/2603.14465)
- [HINTBench](https://arxiv.org/abs/2604.13954)
- [TraceElephant](https://aclanthology.org/2026.acl-long.912.pdf)
- [OSWorld-Human](https://arxiv.org/pdf/2506.16042)
- [CodeTracer/CodeTraceBench](https://arxiv.org/pdf/2604.11641)
- [Google pprof](https://github.com/google/pprof/blob/main/doc/README.md)
- [OpenTelemetry Profiles](https://opentelemetry.io/docs/specs/otel/profiles/)
- [NVIDIA NeMo Agent Toolkit profiler](https://docs.nvidia.com/nemo/agent-toolkit/1.4/improve-workflows/profiler.html)
- [AAAI-27](https://aaai.org/conference/aaai/aaai-27/)

## Paper/claim impact

- The thesis remains important and real.
- The broad product-gap sentence is too strong unless the differentiating combination is made explicit.
- The matched RQ2 result is scientifically sound and should not be weakened or removed; it changes what is authorized.
- RQ3 positive numbers remain real for their individual constructs, but their combined semantic-hierarchy interpretation is too broad.
- RQ4 fixed-mark construction result remains valid but is not end-to-end practicality.
- Related Work is incomplete without ACT*ONOMY and CHIEF and underplays the downstream evidence of Hodoscope/Graphectory/TraceGraph.

## Alternatives and decision

The largest claim worth defending after search is:

> Semantic responsibility stacks are a standard-profile-compatible population abstraction that, under information parity, improve cross-run attribution and diagnosis because they conserve source measures while making recurring responsibility directly inspectable.

The strongest alternative explanation remains:

> Existing category/grouping tools plus source evidence and local diagnostic scores provide the same practical value; pprof is only an output encoding.

The next evidence should isolate the surviving difference, not retreat to “we also emit pprof.”

## Tree/search updates

- **Novelty branch:** opened a mandatory ACT*ONOMY comparison and a direct Datadog/LangSmith capability matrix.
- **RQ2 branch:** confirmed matched evidence is required; opened official-metric and inspection-work validation.
- **RQ3 branch:** split boundary/partition, literal identity, and recursive-topology claims.
- **RQ4 branch:** opened end-to-end annotation cost and NeMo/current-profiler comparison.
- **Literature branch:** CHIEF and ACT*ONOMY justify a targeted `research-literature-novelty` pass in a later outer cycle because the July 2026 literature is moving quickly; this review does not attempt a comprehensive map.

## Project-memory updates

None. This phase is read-only.

## Completion assessment, uncertainty, and next node

Mandatory external search and primary-source verification are complete for every load-bearing RQ and novelty claim. Remaining uncertainty concerns exact product internals (commercial tools do not expose all algorithms), the unpublished/rapidly changing status of several July 2026 preprints, and whether a later dataset release contains a clean untouched A2-compatible hierarchy.

**Next node:** reread the complete active paper and every claim-bearing figure/table against this verified source map, then form the provisional scientific verdict before inspecting current-cycle artifacts.
