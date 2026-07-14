# External Search And Source Verification

## Search date and scope

- Date: `2026-07-14`
- Target: AAAI-27 Main Technical Track
- Questions: venue legality and fit; same-claim products; closest agent-analysis
  papers; published evaluation standards; whether the blind review's baseline
  objections reflect missing experiments or missing reporting

## Official venue findings

- [AAAI-27 Main Track](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
  permits seven pages of main content and nine pages total, with pages 8--9
  reserved for references. Abstracts are due July 21, full papers July 28, and
  supplementary material/code July 31, all at 11:59 PM UTC-12.
- The official criteria score significance, novelty, empirical/theoretical
  soundness, AAAI relevance, and clarity. Integrative and critical
  contributions are eligible; strong work that opens directions across areas
  is explicitly preferred over narrow incremental gains.
- The current paper is legally formatted at seven content pages plus two
  reference-only pages. Format is no longer a blocker.

## Closest product capabilities

| Source | Verified capability | Consequence for AgentProf |
|---|---|---|
| [LangSmith Insights](https://docs.langchain.com/langsmith/insights) | Hierarchical cross-trace categories and subcategories with frequency, error, latency, cost, feedback, and extracted-attribute aggregates | Generic cross-run semantic hierarchy and metric rollups are not novel |
| [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | LLM/embedding clustering, AI-built topic hierarchy, volume/cost/token/error/latency/eval aggregates, failed-eval scoping, export to datasets/annotation queues | Topic discovery, failure clustering, and aggregate cost are strong product precedents |
| [pprof tags](https://github.com/google/pprof/blob/main/doc/README.md) | Labels plus `tagroot`/`tagleaf` pseudo stack frames at visualization time | Weighted pseudo-frame hierarchy and pprof compatibility are infrastructure, not the scientific novelty |
| [Pivot Tracing](https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems-2/) | Select, filter, and group metrics across causally related components and machines | Source-linked cross-layer grouping also has a strong systems precedent |

These sources validate the blind review's novelty attack. AgentProf must win on
the conjunction of cross-layer source linkage, conserved additive evidence,
selectable semantic responsibility views, and demonstrated decision value; it
cannot claim first semantic cross-run grouping.

## Closest research and evidence standards

| Work | Primary-source finding | Review consequence |
|---|---|---|
| [AgentDiagnose, EMNLP 2025 Demo](https://aclanthology.org/2025.emnlp-demos.15/) | Semantic/state-transition diagnostics correlate with 30 human annotations; filtering 46k trajectories to 6k improves downstream WebArena success | A diagnosis tool can connect analysis to a downstream improvement without a large new model contribution |
| [TraceGraph, May 2026 preprint](https://arxiv.org/abs/2605.31308) | Shared decision landscapes expose traps and drive a recovery pipeline that improves SWE-bench resolved rate on fired subsets | Strongest current analysis-to-intervention precedent; AgentProf needs either comparable downstream consequence or a clearer orthogonal systems contribution |
| [AgentGraph, AAAI-26 Demo](https://ojs.aaai.org/index.php/AAAI/article/view/42393) | Source-linked trace knowledge graph supports failure/optimization analysis and perturbation-based causal attribution | Confirms AAAI interest but also offers a competing graph representation |
| [Agentic AI Process Observability](https://arxiv.org/abs/2505.20127) | Treats agent trajectories as event logs and applies process and causal discovery | Event-log aggregation and process discovery are not empty prior-art spaces |
| [TraceElephant](https://arxiv.org/abs/2604.22708) | Defines full-observability failure attribution with responsible-agent and decisive-step targets over 220 real failures | The existing RQ2 reuse is externally grounded and developer-relevant |
| [AgentProcessBench](https://arxiv.org/abs/2603.14465) | Provides 1,000 trajectories and 8,509 human-labeled tool-use steps with reported 89.1% agreement | The existing RQ2 AP result uses a credible process-quality source |

## Blind-attack disposition after source and artifact checks

### Confirmed

- Cross-trace semantic categorization, topic hierarchies, and aggregate cost,
  latency, error, and evaluation metrics already exist in production products.
- Agent analysis papers increasingly connect a discovered structure to a
  downstream intervention or verified diagnosis outcome.
- `operation stack` must be justified as more than arbitrary ordered group-by;
  pprof itself can promote tags to pseudo frames.

### Partly refuted as a missing-experiment claim

The blind reviewer stated that RQ2 lacked native, independent-step, session,
flat, width-only, matched-cardinality, and oracle comparisons. The completed
raw experiments already contain most of these:

- HINTBench ran native sequence, independent step, session, raw action, exact
  flat identity, and width-only controls. AgentProf's point estimate requires
  less work than every main baseline; paired intervals are decisively favorable
  against native, independent step, and session, while the raw-action interval
  narrowly crosses zero.
- TraceElephant ran source-native, independent-step, session, flat, width-only,
  raw-action, matched semantic permutations, and oracle controls. The admitted
  early-recall region is positive, while the predeclared 80%-recall primary is
  internally retained as inconclusive.
- AgentProcessBench ran flat, raw action, semantic, session, ungrouped-risk,
  and within-raw-leaf matched semantic permutations. The semantic AP gain over
  raw action is significant and not explained by matched refinement size.

The paper currently reports only the raw-action headline in its compact table,
so this is primarily a synthesis/reporting gap. No new benchmark, model, or
human study is needed to test it.

## Minimal route recommended to the full reread

Before admitting a new experiment, produce one cumulative RQ2 baseline
synthesis from the already completed, independently audited artifacts. It
should answer one question: whether semantic profiles add early problem
concentration beyond same-information structural views, while clearly showing
where direct step signals or session views are upper/diagnostic references.

This route reuses real public workloads and published benchmark targets, adds
no data/model/metric, and directly tests a load-bearing AAAI reviewer objection.
If it cannot strengthen the paper-level utility answer, then the next admitted
experiment should connect a profile-derived finding to an executable agent
intervention using existing trajectories and software rather than add another
localization benchmark.

