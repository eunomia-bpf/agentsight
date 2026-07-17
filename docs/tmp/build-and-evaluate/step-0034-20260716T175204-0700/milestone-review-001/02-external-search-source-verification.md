# External Search and Primary-Source Verification

## Node metadata

- **Started:** 2026-07-16T18:35:00-07:00
- **Completed:** 2026-07-16T19:19:00-07:00
- **Parent:** Step 0034 REVIEW gate, milestone review 001
- **Objective:** Attack every load-bearing novelty, protocol, and operational-value claim identified in the blind read by searching both the AI-agent observability/evaluation community and the systems profiling/process-mining community, opening primary sources, and recording how the evidence changes the reject hypotheses.
- **Target venue:** AAAI-27 Main Technical Track.
- **Paper state:** This node remains read-only with respect to the manuscript, canonical memory, author intent, prior reviews, and Step 0034 artifacts.

## Search protocol and source policy

I searched outward from the blind attack map rather than from the paper's bibliography. I used four inclusion tests:

1. the source implements or evaluates cross-trajectory semantic categorization, hierarchy, aggregation, diagnosis, or profiling;
2. the source implements the same mathematical/system mechanism through labels, pseudo-frames, arbitrary grouping, cross-boundary joins, trace abstraction, or hierarchical process discovery;
3. the source owns a benchmark used in AgentProf and therefore defines its official task, split, metric, or strong baselines; or
4. the source supplies a directly reusable protocol for testing developer informativeness, diagnosis, or intervention.

For products and standards, I opened official documentation. For research claims, I opened the paper PDF, proceedings page, or official project page. Search-result snippets were discovery aids, not evidence. I excluded secondary summaries, vendor blogs that did not document an implemented capability, generic tracing systems without a relevant aggregation/abstraction mechanism, and papers that merely mention agents without a trace-level task. Commercial tools are used to test the paper's status-quo claim, not to establish peer-reviewed scientific novelty. Preview capabilities are explicitly qualified.

## Exact query log

The following queries were issued during this node. Repeated variants were used when titles or current official pages were difficult to locate.

### AI-agent observability, behavior discovery, and profiling

- `site:docs.langchain.com/langsmith/insights hierarchical behavior categories traces cost latency errors`
- `site:docs.datadoghq.com/llm_observability/monitoring/patterns hierarchical patterns traces token cost latency`
- `site:docs.nvidia.com/nemo/agent-toolkit profiler tokens latency bottlenecks concurrency`
- `LLM agent trajectory clustering hierarchical behavior profiles observability paper`
- `OpenTelemetry GenAI semantic conventions agent spans tool calls official specification attributes`
- `OpenInference specification agent tool spans attributes official`
- `Laminar Signals structured events traces official docs signals agent observability`
- `agent observability semantic profiling signals informative traces without LLM judges paper`
- `"Signals: finding the most informative agent traces without LLM judges"`
- `"finding the most informative agent traces" arxiv`
- `"agent traces" "1.52x" informativeness signals paper`
- `"signal-based sampling" agent traces tau-bench`

### Agent benchmarks, failure attribution, and trajectory structure

- `AgentProcessBench official paper process quality tool-using agents evaluation step labels metrics KDD 2026`
- `HINTBench official paper horizon agent intrinsic non-attack trajectory benchmark localization metrics`
- `Seeing the Whole Elephant benchmark failure attribution LLM multi-agent official paper metrics`
- `OSWorld-Human official paper action group annotations task segmentation efficiency`
- `CodeTracer Towards Traceable Agent States CodeTraceBench verified split official paper stage labels failure localization`
- `site:github.com CodeTracer CodeTraceBench agent states verified split`
- `agent trajectory task boundary segmentation action groups benchmark process mining language agents`

### Systems profiling, causal monitoring, and process abstraction

- `site:github.com/google/pprof tagroot tagleaf labels profiling`
- `Pivot Tracing dynamic causal monitoring distributed systems SOSP 2015 primary paper arbitrary aggregation`
- `Perfetto Trace Processor SQL metrics arbitrary grouping official documentation`
- `process mining hierarchical event logs trace clustering task segmentation primary paper`
- `performance profiling arbitrary labels dimensions stacks tagroot tagleaf context-sensitive profiling paper`

### Venue verification

- `site:aaai.org AAAI-27 call for papers reproducibility checklist submission instructions`

## Source verification matrix

### Current agent-observability products and standards

| Primary source opened | Verified capability | Relevance and inclusion decision |
|---|---|---|
| [LangSmith Insights official documentation](https://docs.langchain.com/langsmith/insights) | Automatically analyzes trace collections for common behaviors and failure modes; organizes traces into generated or predefined categories and subcategories; reports category-level error rate, latency, cost, feedback, and attributes; can run on a schedule and compare periods. | **Closest status-quo contradiction; included.** It already implements hierarchical cross-trace semantic categories with aggregate operational metrics. It does not establish source-linked uninstrumented system effects or pprof output, so it narrows rather than eliminates AgentProf's possible delta. |
| [Datadog LLM Observability Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | Clusters production traffic into AI-labeled topics and a parent-child hierarchy, with volume/share/coherence views intended to find evaluation gaps and failure patterns. | **Closest product-level contradiction; included with qualification.** The page labels Patterns as Preview. It still falsifies the categorical statement that current observability supports only individual-run debugging. |
| [Datadog LLM Observability Cost](https://docs.datadoghq.com/llm_observability/monitoring/cost/) | Aggregates estimated LLM cost across traces and custom tags. | **Included as supporting status-quo evidence.** It shows population-level cost profiling exists, although it does not provide AgentProf's arbitrary semantic stack construction. |
| [Laminar Signals official documentation](https://laminar.sh/docs/signals/introduction) | Generates structured per-trace records linked to source spans, supports behavioral categories such as cost/waste, and lets users query, cluster, alert on, or backfill signals over many traces. The motivation explicitly contrasts this with reading traces one by one. | **Strong same-problem evidence; included.** Signals is not a pprof-like additive hierarchy and does not claim low-level OS effects, but it occupies the paper's claimed missing population-analysis layer. |
| [NVIDIA NeMo Agent Toolkit Profiler](https://docs.nvidia.com/nemo/agent-toolkit/1.5/improve-workflows/profiler.html) | Instruments agent workflows, records per-invocation token/time/LLM-call statistics, stores offline profiles, forecasts usage, computes latency/throughput, and analyzes bottlenecks and concurrency across multiple agent frameworks. | **Terminology and scope contradiction; included.** A current agent tool explicitly calls this activity profiling. AgentProf must distinguish semantic responsibility and source-linked effects, not claim that agents lack profiling altogether. |
| [OpenTelemetry GenAI semantic attributes](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) | Defines structured attributes for agents, workflows, sessions, prompts, tools, tokens, and evaluation scores. The live registry notes movement/deprecation of some fields into newer specification locations. | **Included as representation context, not a novelty defeater.** Semantic fields over traces are standardized; OpenTelemetry does not by itself induce categories or operation stacks. The moving specification means exact attribute names should not carry a timeless claim. |
| [OpenInference specification](https://arize-ai.github.io/openinference/spec/) | Defines typed span attributes for LLMs, tools, agents, messages, token counts, and trace hierarchy/context. | **Included as a serious structured-span alternative.** It shows that a fair baseline can expose the same semantic labels in an existing hierarchy before testing whether query-time stacks add value. |

### Systems profiling and trace-query mechanisms

| Primary source opened | Verified capability | Relevance and inclusion decision |
|---|---|---|
| [Google pprof documentation](https://github.com/google/pprof/blob/main/doc/README.md) | Samples may carry string and numeric tags as extra dimensions; tags support filtering and breakdown; `tagroot` and `tagleaf` promote tag values to pseudo stack frames; compatible profiles from multiple programs can be merged. | **Mechanistically closest; included.** AgentProf's field projection, additive sample folding, and semantic pseudo-frames are not a new profiling primitive at the one-label level. Ordered multi-field composition, automatic semantic derivation, and agent adapters may still be engineering contributions, but they require an expressiveness or outcome comparison against pprof labels rather than a citation-only dismissal. |
| [Perfetto Data Explorer](https://perfetto.dev/docs/visualization/data-explorer) and [Trace Summary](https://perfetto.dev/docs/analysis/trace-summary) | Trace data and arbitrary per-event metadata can be filtered, joined, grouped, and aggregated in a visual pipeline or custom SQL; trace-summary metrics support arbitrary SQL, dimensions, `group_by`, and additive aggregations. | **Included as a representation baseline.** The operation-stack computation is expressible as conventional trace-query projection and `GROUP BY`; AgentProf's distinct value must come from the responsibility ontology, source linkage, or user consequence, not from tuple aggregation alone. |
| [Pivot Tracing: Dynamic Causal Monitoring for Distributed Systems](https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems/) | Defines low-overhead cross-component/machine monitoring in which events captured at one point can be selected, filtered, and grouped by context from causally related points using happened-before joins; evaluates heterogeneous Hadoop systems. | **Included as a close causal-attribution ancestor.** It already links low-level effects to higher-level context across boundaries. AgentProf applies a related idea offline to agent semantics, but the broad causal-monitoring principle is not new. |
| [Activity Mining by Global Trace Segmentation](https://www.vdaalst.com/publications/p586.pdf) | Treats low-level event logs as the wrong abstraction, discovers coherent subsequences/high-level activities from global event-class correlations, builds a hierarchy, and projects a log to arbitrary abstraction levels; validates on a real ASML log. | **Closest RQ3 mechanism family; included.** It predates agent-specific recurrent action boundaries and provides a direct process-mining baseline family that the paper does not evaluate or discuss. |
| [Discovering Hierarchical Processes Using Flexible Activity Trees for Event Abstraction](https://arxiv.org/abs/2010.08302) | Discovers multi-level hierarchical processes from logs using activity trees and log abstraction/projection, handles interleaving, and evaluates precision, generalization, and F1 against domain-knowledge, random, and flat alternatives. | **Included as a strong hierarchy baseline.** It makes clear that hierarchy and event abstraction have an established evaluation vocabulary beyond pairwise boundary agreement. |
| [Context-Aware Trace Clustering](https://epubs.siam.org/doi/10.1137/1.9781611972795.35) | Clusters process traces while retaining contextual information beyond raw sequence identity. | **Included as adjacent baseline provenance.** It is less mechanistically direct than segmentation/activity trees, so it is not used alone to reject novelty; it reinforces that raw-action grouping is not the strongest known alternative. |

### Agent diagnosis, triage, and human-grounded utility

| Primary source opened | Verified capability/protocol | Relevance and inclusion decision |
|---|---|---|
| [Signals: Trajectory Sampling and Triage for Agentic Interactions](https://arxiv.org/pdf/2604.00356) | Uses lightweight interaction/execution/environment signals to sample trajectories. In a controlled, blinded study, three expert annotators judged 300 shuffled trajectories from equal-size random, heuristic, and signal samples; signal sampling achieved 82% developer-informative trajectories versus 74% and 54%, with 1.52x efficiency over random. It reports exact confidence intervals, significance tests, agreement, reward-stratified checks, and limitations. | **Decisive protocol analogue; included.** It directly operationalizes the developer-informativeness consequence that AgentProf currently disclaims. It also shows how to control inspection budget and failure-rate composition. AgentProf need not copy this method, but should meet or adapt this evidentiary standard for RQ2/the thesis. |
| [AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/) | Provides trajectory-semantic diagnosis across five competencies, compares against 30 manually annotated trajectories, reports human correlation, and demonstrates downstream data-curation improvement on WebArena. | **Included as independent-human and downstream precedent.** Its small human set is not definitive, but it makes AgentProf's six-task self-reader probe look especially preliminary. |
| [CodeTracer / CodeTraceBench](https://arxiv.org/pdf/2604.11641) | Represents coding-agent execution as a hierarchical trace tree with stage/step labels, evaluates failure-onset localization on verified data with matched budgets and macro precision/recall/F1, compares bare-LLM and ablated variants, and tests reflective replay as a downstream remediation. | **Closest academic mechanism and protocol; included.** AgentProf uses 405 source-valid failed trajectories for post-hoc boundary calibration and B-cubed agreement, but does not compare with the benchmark owner's hierarchy/localization methods or explain why this subset and task answer RQ3. Reflective replay is a stronger consequence test for RQ2. |
| [From Flat Logs to Causal Graphs (CHIEF)](https://arxiv.org/pdf/2602.23701) | Builds a hierarchical causal graph over agent traces, uses task decomposition and counterfactual attribution, and compares against multiple baselines on agent- and step-level failure attribution. The paper reports that hierarchy alone is insufficient without guided causal reasoning. | **Contradictory evidence; included.** It directly challenges the inference that semantic hierarchy by itself yields diagnosis value and motivates a baseline that separates representation from causal reasoning. |
| [TraceElephant: Seeing the Whole Elephant](https://aclanthology.org/2026.acl-long.912.pdf) | Defines reproducible multi-agent failure attribution with agent- and step-level accuracy, compares all-at-once, binary-search, step-by-step, static-agentic, and dynamic counterfactual-replay methods, runs repeated trials, and reports human annotation agreement. | **Official benchmark/protocol source; included.** AgentProf instead converts a released localization signal into group ranking/MAP. That is a new secondary task, not an evaluation against the benchmark's official attribution baselines or exact-accuracy construct. |
| [Understanding Software Engineering Agents: Thought-Action-Result Trajectories](https://www.software-lab.org/publications/ase2025_trajectories.pdf) | Unifies trajectories into thought/action/result units, manually maps action categories, and mines sequential action patterns over agent runs. | **Included because AgentProf cites and reuses the action taxonomy.** It supports the plausibility of the labels but also shows that semantic action abstraction and sequence-pattern mining predate the profiler contribution. |

### Official benchmark-task verification

| Benchmark source opened | Official task and metrics | Consequence for AgentProf |
|---|---|---|
| [AgentProcessBench](https://arxiv.org/pdf/2603.14465) | Labels assistant steps as positive/neutral/negative process quality, with StepAcc and FirstErrAcc; reports a 1,000-trajectory, 8,509-label corpus and agreement/resolution procedures. | AgentProf averages released judge votes and evaluates ranking/MAP over derived groups. This can test a new retrieval view, but it is not the official process-evaluation task and is not compared with process reward models. Its strongest result being the atomic baseline is therefore scientifically important, not an incidental caveat. |
| [HINTBench](https://arxiv.org/abs/2604.13954) (primary OpenReview PDF indexed at `https://openreview.net/pdf?id=YSCiOXc1ij`) | Defines risk detection plus coarse/fine risk-step localization and reports F1/strict-F1 with repeated runs and guard/general models. | AgentProf uses a best-Wilson-prefix grouping score and MAP rather than official localization metrics or model baselines. The transformation is not invalid, but it establishes ranking consistency with an inherited signal, not competitive risk localization. |
| [TraceElephant](https://aclanthology.org/2026.acl-long.912.pdf) | Uses exact agent-level and step-level failure attribution with multiple inference strategies and counterfactual replay. | Same issue: AgentProf evaluates an additional profile-ranking task. Claims must say so and cannot borrow the benchmark's diagnosis meaning without validating the derived task. |
| [OSWorld-Human](https://arxiv.org/abs/2506.16042) | Provides human minimal computer-use trajectories and action-group information to study efficiency/excessive steps. | Human action groups are a plausible boundary reference, but they were designed for trajectory efficiency, not as ground truth for an arbitrary semantic stack hierarchy. Because recurrence was selected after OSWorld inspection, this dataset cannot be the untouched test of the finalized constructor. |
| [CodeTracer / CodeTraceBench](https://arxiv.org/pdf/2604.11641) | Uses verified coding trajectories, hierarchical stage/step states, official run matching, macro localization metrics, ablations, and replay. | AgentProf's post-hoc calibration on a selected failed subset is useful diagnostic evidence, not independent confirmation of RQ3 or competitive failure localization. |

### Venue requirements

The [AAAI-27 Main Technical Track call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/) limits submissions to seven content pages and nine pages total, reserves pages beyond seven for references, warns that reviewers need not read supplementary material, requires a reproducibility checklist, and evaluates significance, novelty, empirical/theoretical soundness, related-work coverage, clarity, and reproducibility. The full-paper deadline is July 28, 2026. The compiled manuscript is nine pages including references/checklist, so gross length is not the problem. The problem is scientific readiness: critical novelty and evaluation evidence must appear in the main body, while the current checklist answers several reproducibility items only partially or negatively.

## What the search establishes

### The challenged belief is materially overstated

The broad belief that agent observability is confined to debugging individual runs is not defensible in July 2026. LangSmith Insights, Datadog Patterns, and Laminar Signals all analyze collections of traces into behavior categories or hierarchies, and LangSmith exposes aggregate error, latency, cost, and feedback at those levels. NVIDIA explicitly provides an agent-workflow profiler. These are not identical to AgentProf, but they already implement the population-level shift that the introduction presents as missing.

The narrower, source-supported gap is: **current agent analytics do not obviously combine locally derived semantic responsibility categories with additive, source-linked low-level system effects in arbitrary ordered projections and export them through a conventional profiler interface without requiring a vendor trace hierarchy.** That narrower gap may be useful. The manuscript does not yet isolate or evaluate it against a same-input alternative.

### The mathematical systems primitive is established, not new by itself

Pprof already treats labels as profile dimensions and can materialize tag values as stack frames. Perfetto already expresses arbitrary dimension selection, joins, grouping, and aggregation over trace data. Pivot Tracing already joins low-level effects to high-level causal context and aggregates across distributed boundaries. Process mining has long transformed low-level logs into discovered hierarchical activities and evaluated abstraction fidelity.

Therefore, `project fields -> make frames -> sum weights` is not a standalone scientific novelty. A defensible contribution must be either:

- a new semantic/causal invariant for agent effects;
- an expressiveness or reliability result that established labeled profilers and trace queries cannot obtain;
- a validated agent-specific constructor that outperforms process-abstraction alternatives; or
- a consequential operational result caused specifically by source-linked semantic profiles.

The current paper does not provide one of these comparisons. Its implementation and dataset integration remain potentially valuable engineering, but the claimed profiling principle is presently an application/synthesis of known primitives.

### The RQ2 protocols do not inherit the official benchmark meaning automatically

AgentProcessBench, HINTBench, and TraceElephant evaluate step classification or failure/risk localization with official accuracy/F1 constructs and substantive model baselines. AgentProf creates a secondary ranking problem using their released signals. This derived task is legitimate if described as such, but a positive MAP difference over raw action cannot be interpreted as competitive diagnosis or proof that profiles correspond to actionable problems. Atomic ranking winning on AgentProcessBench, uncertain work deltas, and omission of official baselines weaken the causal claim further.

Signals, AgentDiagnose, CodeTracer, CHIEF, and TraceElephant demonstrate stronger consequence tests: blinded expert informativeness, human correlation, exact localization, counterfactual reasoning, and replay-based improvement. The absence of an independent developer or downstream decision test is therefore **missing promised evidence** for the thesis and RQ2, not a merely desirable embellishment.

### RQ3 omits the closest abstraction community

Global trace segmentation, flexible activity trees, context-aware trace clustering, and CodeTracer all address low-level-to-high-level trajectory structure. AgentProf's always-cut, action-change, and phase-change controls do not represent that literature. B-cubed agreement with an already inspected dataset and post-hoc CodeTraceBench calibration cannot establish that recurrent transition boundaries are the right general constructor. A fresh, untouched family and a serious process-abstraction/hierarchical baseline are necessary for the fixed RQ3.

## Updated reject hypotheses

### Blockers

1. **B1 — novelty/equivalence:** The paper's broad novelty and status-quo framing are contradicted by current agent analytics and established systems mechanisms. The narrower unique delta is not isolated experimentally. This upgrades blind H1/H7 from a pending concern to a source-grounded blocker.
2. **B2 — causal evidence for the thesis and RQ1/RQ2:** No experiment tests whether source-linked semantic system effects improve independent attribution, diagnosis, or intervention over a same-input hierarchical semantic baseline. RQ1's mixedness remains circular and RQ2 remains a derived ranking probe. Existing work provides feasible, stronger protocols.
3. **B3 — complete fixed RQ3 evidence:** The constructor is neither tested untouched nor compared with the closest hierarchy/segmentation family, while phase accuracy remains unmeasured. This is missing evidence for an explicit RQ, not a request for extra breadth.

### Majors

1. **M1 — benchmark construct validity:** The paper does not clearly separate its new derived ranking tasks from the official task meanings and does not compare with official strong baselines.
2. **M2 — cross-domain chain:** The implementation joins two mature families—semantic trace analysis and systems profiling—but the evaluation does not show that their combination changes a real decision.
3. **M3 — literature coverage:** The paper omits or underdevelops the closest current products, pprof/Perfetto expressiveness, Pivot Tracing, process abstraction, CodeTracer/CHIEF, and human-grounded trajectory triage. Two Related Work paragraphs cannot support an AAAI novelty judgment.
4. **M4 — reproducibility/submission readiness:** The official venue makes critical main-body evidence and reproducibility material decision-relevant, while the checklist and current artifact do not document enough to independently reconstruct all derived tasks.

### Minors

1. Datadog Patterns is Preview and should not be represented as a mature universal baseline.
2. OpenTelemetry GenAI attributes are evolving; exact registry field names should be cited with version/date or treated generically.
3. Commercial tools may be inaccessible for reproducible experiments; a faithful open reimplementation using the same labels, hierarchy, and metrics is acceptable if capability parity is documented.

## Strongest alternative explanation and largest defensible claim

The strongest alternative explanation is that the reported gains come from **adding a benchmark-correlated semantic grouping label to an ordinary aggregate query**, not from a new profiling abstraction. Under this explanation, a labeled trace table, pprof tag frames, Perfetto query, or process-mining hierarchy supplied the same fields would achieve the same ranking, while the flame graph is a rendering choice.

The largest claim defensible from current evidence is narrower than the manuscript's thesis:

> AgentProf is an offline systems integration that converts heterogeneous agent records and source-linked effects into conserved, selectable semantic projections and exports them in profiler-compatible formats; on three derived benchmark-ranking tasks, some semantic groupings rank inherited problem signals earlier than a matched raw-action grouping.

The current evidence does not yet support the general claim that agent observability needs this new profiling abstraction, that attribution is more correct, or that the profiles improve developer diagnosis or intervention.

## Decisive next experiment and search implication

The decisive experiment is a pre-registered, untouched, same-input factorial comparison:

- **representation:** raw trace/tree, existing semantic hierarchy or process-abstraction baseline, and AgentProf operation stacks;
- **evidence:** semantic trace fields alone versus the same fields plus source-linked low-level system effects;
- **budget:** equal trace visibility, labels, ranking signals, inspection budget, and model/human time;
- **task:** identify the correct responsibility/root cause and choose a concrete mitigation on held-out real agent families;
- **outcomes:** diagnosis/intervention accuracy, time or groups inspected, calibration, and preferably replayed improvement or prevented cost/safety effect.

This directly tests the paper's unique combination. Signals supplies a credible blinded informativeness protocol; CodeTracer and TraceElephant supply matched-budget localization and replay precedents; process mining supplies the serious abstraction baselines. A separate untouched RQ3 test must include task, action, literal phase, and boundary tags under the finalized constructor.

No additional search for cosmetic cutoff, metric, or benchmark variants is likely to change the decision. A focused literature/positioning pass is still required before rewriting, but the next scientific route is already identifiable.

## Verdict after external verification

**Reject at the current AAAI-27 bar; route to EXPERIMENT_GATE, not WRITE_GATE or submission.** The blind verdict was weak reject pending novelty search. Primary sources strengthen it to reject because the community belief is partly a strawman, the systems primitive is established, the benchmark evaluations are nonstandard secondary tasks, and the paper does not test the narrower source-linked semantic-effect delta that remains plausibly novel.

Taste classification remains **incomplete-but-promising**, with a present risk of **complicated-but-shallow**: the artifact and dataset breadth are real, but they spread evidence across many derived tasks instead of testing the one consequence that could make the synthesis deep.

## Tree/search updates, uncertainty, and next node

The attack tree now has three verified roots: (1) equivalence to existing semantic analytics and profiling primitives, (2) absence of an independent consequence test for the unique combination, and (3) incomplete/contaminated validation of the semantic constructor. Product capability details may change, and some 2026 papers are recent preprints, so exact maturity is less certain than feature existence. None of the blocker findings depends on one vendor or one preprint: pprof, Perfetto, Pivot Tracing, established process mining, and official benchmark protocols independently support them.

No canonical project-memory update and no manuscript edit was made. The next mandatory node is a fresh full-paper reread with these sources in view, recorded in `03-full-paper-reread-scientific-assessment.md` before any author-intent, prior-review, evaluation-log, or Step 0034 material is consulted.
