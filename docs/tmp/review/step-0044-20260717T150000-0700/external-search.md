# External search and primary-source verification

## Node metadata

- **Started:** 2026-07-17 15:18:00 -07:00
- **Completed:** 2026-07-17 15:47:00 -07:00
- **Parent:** `blind-read.md`, REVIEW gate step 0044
- **Objective:** Attack the paper's novelty, metric choices, baselines, protocols, real-world motivation, and AAAI-27 relevance using current primary and authoritative sources.
- **Mode:** Read-only literature/novelty review. No paper, canonical-document, or Git changes.
- **Coverage boundary:** Agent-observability products and standards; profiling foundations; current cross-run agent-trajectory analysis and diagnosis; standard partition/classification/localization metrics; and official AAAI-27 criteria. The search was considered sufficient when each load-bearing claim had at least one closest same-problem source, one mechanism precedent, and one evaluation precedent or explicit residual uncertainty.

## Name-free claims under attack

I removed project-coined names before comparison.

1. **Model claim:** Heterogeneous agent and system-effect records can be folded across runs under query-selected semantic field hierarchies while conserving user-selected additive measures.
2. **Construction claim:** Recurrence of visible adjacent actions across reference sessions can construct useful group boundaries without target annotations.
3. **Utility claim:** Semantic grouping of agent operations improves the ranking of independently annotated problems over raw-action identity and can refine operation-local evidence.

## Search questions and exact query families

Searches were run on 2026-07-17. Materially different query branches included:

- `site:docs.langchain.com/langsmith/insights hierarchical categories traces metrics`
- `site:docs.datadoghq.com/llm_observability/monitoring/patterns hierarchical categories`
- `site:opentelemetry.io profiles data model trace linkage pprof official specification`
- `site:github.com/google/pprof tagroot tagleaf pseudo frames documentation`
- `What Resolve Rate Hides trajectory structure diagnostics coding agents 2607.06184`
- `WebGraphEval multi-turn trajectory evaluation graph representation`
- `Hodoscope unsupervised monitoring AI misbehaviors 2604.11072`
- `TraceGraph shared decision landscapes 2605.31308`
- `AgentRx diagnosing AI agent failures 2602.02475`
- `process-centric analysis agentic software systems trajectories 2512.02393`
- `agent profiling trajectories semantic cross-run resource cost AI agents paper`
- `site:docs.nvidia.com NeMo Agent Toolkit profiler tokens latency bottleneck concurrency`
- `Bagga Baldwin 1998 B cubed ACL`, `Rosenberg Hirschberg V-measure ACL`, `Ruokolainen 2016 boundary F1`, `Robertson 2008 average precision`, and `macro F1 standard classification definition`
- official AAAI-27 Main Technical Track CFP and submission instructions.

I opened the primary paper/official documentation rather than relying on result snippets. Product blogs, Reddit discussions, generic “agent profiling” work about agent capability routing, and secondary paper-summary sites were excluded from novelty judgments. Current 2026 arXiv papers are retained with non-archival status stated; WebGraphEval is a NeurIPS 2025 workshop paper; Process-Centric Analysis is archival OOPSLA 2026.

## Verified primary-source map

### Observability, aggregation, and profiling precedents

| Source | Verified capability | Threat or distinction |
|---|---|---|
| [LangSmith Insights official documentation](https://docs.langchain.com/langsmith/insights) | Automatically groups traces into top-level categories and subcategories, aggregates error/latency/cost/feedback/attributes, and exposes underlying traces. The current service samples at most 1,000 traces per report. | High same-problem and partial same-mechanism overlap. It already performs hierarchical cross-trace semantic grouping and metric rollup. It does not document arbitrary additive-measure conservation, source-linked process/file/network effects, or multiple pprof-compatible query-time stacks over one operation corpus. |
| [Datadog Patterns official documentation](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | Summarizes interactions, embeds them, clusters with UMAP/HDBSCAN, builds an AI-generated topic hierarchy, rolls up cost/tokens/errors/latency/evaluations, and supports diagnosis and prioritization. A run processes up to 10,000 records. | High same-problem and partial same-mechanism overlap. It directly weakens any claim that hierarchical semantic aggregation is absent from products. The paper accurately acknowledges this. The residual distinction is operation-level heterogeneous effects, conservative folding, selectable stacks, and local/offline export. |
| [NVIDIA NeMo Agent Toolkit profiler official documentation](https://docs.nvidia.com/nemo/agent-toolkit/1.5/improve-workflows/profiler.html) | Instruments workflows; records per-invocation tokens, times, LLM/tool calls; performs offline analysis, bottleneck/latency/concurrency analysis, forecasting, and hierarchical prediction tries keyed by function path/call index. | Serious same-problem profiling precedent. It profiles instrumented code/workflow identity rather than deriving reusable semantic responsibility from heterogeneous completed histories. The paper cites NeMo but should make this distinction concrete because “agent profiler” is no longer an empty category. |
| [OpenTelemetry Profiles specification](https://opentelemetry.io/docs/specs/otel/profiles/) | Defines a pprof-superset profile signal, generalized attributes, shared resource context, and optional links from profile samples to trace/span IDs. | Establishes pprof compatibility and profile–trace linkage. It does not itself construct semantic categories or cross-run responsibility hierarchies. |
| [Google pprof documentation](https://github.com/google/pprof/blob/main/doc/README.md) | Reports tag values and additive sample-value breakdowns; `tagroot` and `tagleaf` promote tags to pseudo stack frames. | Establishes tag-to-frame projection and additive profile display. AgentProf cannot claim either primitive alone as novel. Its defensible axis is deriving/combining semantic fields over agent histories and system effects, with arbitrary field order and multiple views. |
| [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/) | Standardizes names across traces, metrics, logs, profiles, and resources; current GenAI conventions include agent/tool operations. | Shows that stable application-supplied identifiers and fields can be standardized. It does not solve stable semantic identity for uninstrumented natural-language histories, which preserves the paper's stated gap. |

### Cross-run trajectory analysis and diagnosis

| Source and status | Verified contribution | Same-claim assessment |
|---|---|---|
| [Process-Centric Analysis of Agentic Software Systems](https://arxiv.org/abs/2512.02393), OOPSLA 2026, DOI 10.1145/3798271 | Encodes temporal and semantic relations in agent trajectories as graphs, defines process-centric metrics and phase-flow analyses, aggregates shared strategies over 4,000 SWE-agent/OpenHands trajectories, detects inefficiencies, and supports online monitoring. | **Closest omitted archival work.** Same problem and substantial same-representation/analysis overlap. It does not conserve arbitrary resource measures, connect OS effects, export profiles, or offer query-selected field stacks. The omission is a submission-level novelty risk because a reviewer can reasonably see both papers as transferring classical software structure to stochastic agent trajectories. |
| [TraceProbe / What Resolve Rate Hides](https://arxiv.org/abs/2607.06184), arXiv 2026 | Canonicalizes heterogeneous coding-agent actions into a nine-type taxonomy with deterministic effect labels, detects anti-patterns, aligns runs, and prioritizes inspection over 2,500 trajectories. | Same problem and normalization/diagnosis precedent, but coding-only and not a conserved multi-measure profiling model. The paper cites it and distinguishes population profiles from diagnostic anti-patterns. |
| [WebGraphEval](https://arxiv.org/abs/2510.19205), NeurIPS 2025 workshop | Canonically encodes web actions, merges recurring behavior into a weighted cross-agent graph, propagates rewards, and identifies inefficiency/critical decisions over thousands of trajectories. | Strong same-mechanism precedent for recurring cross-run weighted structure. It is outcome/evaluation-oriented and web-specific, not source-linked multi-measure profiling. The paper cites it. |
| [Hodoscope](https://arxiv.org/abs/2604.11072), arXiv 2026 | Compares cross-group behavior distributions, surfaces anomalous action patterns, discovers a new benchmark vulnerability, recovers known exploits, and estimates a 6--23x reduction in human review effort. | Stronger evidence than AgentProf for an analysis-to-human-decision consequence, but a different anomaly-discovery objective. It raises the bar for claims about unsafe behavior and practical inspection value. The paper cites it but does not experimentally claim the same outcome. |
| [TraceGraph](https://arxiv.org/abs/2605.31308), arXiv 2026 | Pools trajectories into shared action-observation landscapes, identifies productive/trap regions, and uses them in a recovery intervention that improves resolved rate. | Stronger analysis-to-intervention evidence, but outcome-informed and task-specific rather than target-blind profiling. The paper cites it and correctly treats it as an analysis-to-decision precedent. |
| [AgentRx](https://arxiv.org/abs/2602.02475), arXiv 2026 | Synthesizes constraints, validates them stepwise, and uses the evidence log to localize a critical failure step/category on 115 annotated failures. | Strong diagnosis/localization comparator, but per-failure and LLM-judge based, not cross-run resource profiling. The paper cites it. |
| [AgentSight](https://arxiv.org/abs/2508.02736), arXiv/workshop lineage | Correlates high-level agent intent with low-level system behavior using eBPF and demonstrates security/performance case studies. | Supplies rather than duplicates AgentProf's cross-layer capture. AgentProf's system-effect novelty depends on its aggregation model, not the underlying join. |

### Metrics and protocols

| Metric | Primary/authoritative verification | Assessment |
|---|---|---|
| B³ precision/recall/F1 | [Bagga and Baldwin 1998, ACL Anthology](https://aclanthology.org/C98-1012/) | A standard item-level partition/coreference measure. The paper explicitly uses ordinary per-operation B³ and does not apply token weighting. Appropriate for group-partition agreement, but it does not by itself measure resource-attribution correctness. |
| V-measure | [Rosenberg and Hirschberg 2007, ACL Anthology](https://aclanthology.org/D07-1043/) | A standard entropy-based external clustering measure. Appropriate for partition-valued outputs where literal cluster names are irrelevant. |
| Exact boundary precision/recall/F1 | [Ruokolainen et al. 2016, Computational Linguistics](https://doi.org/10.1162/COLI_a_00243) | Published segmentation protocol reporting boundary precision, recall, and F1. Appropriate for exact adjacent boundary decisions. |
| AP/MAP | [Robertson 2008, SIGIR, DOI 10.1145/1390334.1390453](https://doi.org/10.1145/1390334.1390453) | Standard ranking metric. Appropriate for “inspect relevant target operations early” when every query has a target. The paper still needs an unambiguous definition of how tied group scores enter AP, because a stable ordering of tied items can change AP. |
| Macro-F1/accuracy | [Lewis et al. 2004 RCV1](https://jmlr.org/papers/v5/lewis04a.html) is a real large-scale text-classification precedent; [Sokolova and Lapalme 2009](https://doi.org/10.1016/j.ipm.2009.03.002) systematically analyzes classification measures. | Standard metrics and preferable to a bespoke score. However, “macro-F1” has more than one formula in the literature; the paper should state that it is the arithmetic mean of per-class F1 (if that is what the code computes), not merely name the metric. This is a reporting fix, not a new experiment. |

The paper passes the user's central metric requirement: its headline results use standard, citable metrics. I found no token-weighted B³, Recall@20%, top-3 reader, or model-reader metric. The remaining issues are metric-to-construct alignment and precise tie/averaging definitions, not replacement with another custom metric.

## Claim-oriented novelty judgment

| Name-free claim | Same-claim risk | Reasoned judgment |
|---|---|---|
| Query-selected semantic stacks conserve and aggregate multiple additive effects over heterogeneous agent histories | **Medium** | Every primitive has precedent: product hierarchies and rollups, pprof tag frames, OTel linked profiles, and instrumented workflow profilers. I found no single verified source that combines uninstrumented/local agent histories, source-linked process/file/network effects, arbitrary additive-measure conservation, and multiple query-selected semantic stacks in one operation corpus. This can support an integrative AAAI contribution if the conjunction is stated as a capability with consequences, not as a list of features. |
| Label-free adjacent-action recurrence constructs useful boundaries | **High as an algorithmic novelty claim; medium as a pluggable implementation mechanism** | NPMI, k-means, recurring transitions, and phase/action segmentation are known components. The paper wisely does not present a new learning-algorithm theorem. Its scientific value is empirical utility inside the larger model. Post-hoc corpus influence prevents treating it as independently validated general induction. |
| Semantic grouping improves independent problem ranking over raw identity | **Medium** | Cross-run structures already expose failure patterns and critical regions, but the paper's matched three-benchmark MAP comparison is a distinct quantitative result. The threat is not that the result is already published; it is that raw action may be too weak a competing position and that group-score ties need protocol clarity. |

## Contradictory and negative evidence

1. Current LangSmith and Datadog documentation directly contradicts any broad statement that existing tools lack cross-trace semantic hierarchies or metric rollups. The manuscript now avoids that error and explicitly credits those capabilities.
2. NeMo's official profiler contradicts any claim that “profiling” has not been applied to agent workflows. The remaining belief challenge must be about what supplies identity and hierarchy across heterogeneous completed histories, not the word “profiling.”
3. pprof's official tag promotion shows that tag-derived pseudo-frames are established. Novelty cannot rest on converting a string field to a stack frame.
4. Graphectory shows an archival, process-centric transfer of software graph structure to agent trajectories, including aggregate phase flow and online monitoring. Its absence from the bibliography is the most material literature omission.
5. Hodoscope and TraceGraph provide stronger end consequences (reduced human review and improved recovery). They do not invalidate AgentProf's profiling thesis, but they show why “corresponds to annotated problems” is evidence of correspondence, not yet evidence of improved debugging or repair.

## Baseline and experiment implications

### Competing scientific positions

| Competing position | Existing evidence in the paper | What a fair result would mean |
|---|---|---|
| Raw action identity is enough | Numerical baseline in RQ1/RQ2 | AgentProf consistently wins, so raw identity alone is rejected on the named populations. |
| Dataset/application phase fields are enough | Phase-only baseline in RQ1 slightly exceeds recurrence; phase-change control is weaker on OSWorld-Human | The paper already reports a mixed answer, correctly showing that no one semantic view dominates. This supports selectable stacks more than it supports recurrence. |
| Operation-local diagnostic evidence is enough | Local-only and matched local+raw/local+semantic analysis in RQ2 | Semantic tie refinement helps substantially on two workloads and not distinguishably on AgentProcessBench. This is a credible mechanism result, although adaptive/post-hoc. |
| Product-style hierarchical clustering already solves the problem | Citation-only because products do not expose an equivalent runnable protocol over these operation sets | Needs precise capability distinction, not an unfair reimplementation. No mandatory product reimplementation follows from the search. |
| Process/graph analysis already supplies sufficient cross-run structure | Graphectory, WebGraphEval, TraceProbe, Hodoscope, TraceGraph as citation precedents | If their representation can express the same conserved multi-effect query projections, novelty narrows materially; the primary sources do not establish that equivalence. A name-free comparison is required in writing. |

### Could a new experiment change paper-level acceptance?

**Possibly, but no new experiment is automatically required by this search.** The dominant blocker is the omitted archival closest work and unclear isolation of the integrative novelty, both WRITE/literature repairs. Existing RQ2 evidence is already the right kind of standard-metric, complete-workload evidence. A new experiment becomes acceptance-changing only if the authors cannot establish from mechanisms and existing artifacts that the same operation corpus supports a capability unavailable to the strongest phase/process-graph alternative.

If the existing trajectories and current adapters already expose a directly comparable **phase-only or published process-structure view on the three RQ2 workloads**, recomputing standard MAP with no new data could be decisive: it would test the strongest low-complexity semantic alternative rather than merely raw action. This should be admitted only after checking availability and information parity. It is not a blanket demand to implement LangSmith, Datadog, Graphectory, or another new benchmark.

No additional RQ4 run is presently acceptance-changing: the paper scopes fixed-input construction cost clearly, and full-path cost would support engineering completeness more than the central scientific distinction.

## Accepted-protocol and external-asset handoff by RQ

| RQ | Published/official anchor already used | Remaining implication |
|---|---|---|
| RQ1 attribution | AgentSight cross-layer capture; ordinary B³ partition evaluation; real Codex suite | Preserve exact RQ. Explain which evidence tests effect lineage, weight conservation, and semantic responsibility separately. Do not let B³ stand in for all resource-attribution correctness. |
| RQ2 localization | Three released localization benchmarks; standard per-query AP/MAP; Wilson interval for proportions | Preserve complete workload scoring. Define AP tie handling. Only add an existing-trajectory phase/process baseline if it is naturally available and information-matched. |
| RQ3 tag accuracy | RCV1/classification precedent, V-measure, B³, exact boundary F1, public annotated trajectories | Keep standard metrics; define macro-F1 convention. Present supervised, label-free, literal-label, and partition protocols as distinct scoped answers rather than interchangeable “tag accuracy.” |
| RQ4 cost | Standard elapsed time/throughput/RSS on public workload union | Existing protocol is sufficient for the scoped fixed-input path. Do not inflate it into end-to-end live overhead. |

## How the search changed the attack map

- **Narrowed the generic novelty objection:** No verified prior source combines the entire operation/effect/conservation/query-stack capability. The contribution can be defensible as an integrative result, which AAAI-27 explicitly recognizes.
- **Strengthened one concrete novelty objection:** OOPSLA 2026 Process-Centric Analysis/Graphectory is a closer archival neighbor than the paper currently discusses and must be included.
- **Strengthened the practical-evidence comparison:** Hodoscope and TraceGraph demonstrate downstream review/intervention consequences; AgentProf must avoid implying it has shown those outcomes.
- **Reduced the case for a reflexive new experiment:** Standard metrics and complete RQ2 populations are already present. The next action is full-paper reread and a literature/argument repair unless an available phase/process baseline would directly change the central conclusion.

## Search/tree and project-memory disposition

- **Search-tree update:** Close product/standard, profiling-foundation, metric, and core closest-work branches. Retain one bounded residual branch: whether an information-matched published process/phase view can be evaluated on existing RQ2 trajectories without implementing a new system.
- **Project-memory update:** None. Closest-work and baseline findings are REVIEW evidence for root-agent disposition; this node does not alter thesis, RQs, or canonical story.
- **Completion assessment:** Targeted current-literature coverage sufficient for a final whole-paper verdict.
- **Residual uncertainty:** Commercial implementations are only verifiable through public documentation; several 2026 closest papers are non-archival; AP tie implementation and available RQ2 phase fields require repository inspection rather than more web search.
- **Next node:** Reread the entire paper and all claim-bearing figures/tables, then inspect only the current RQ2 evaluation implementation/provenance needed to resolve tie handling and baseline availability.
