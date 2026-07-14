# External Search And Source Verification

## Scope

- Date: `2026-07-14`
- Venue: AAAI-27 Main Technical Track
- Search target: closest production capabilities, semantic trajectory
  analysis, downstream intervention, profiler semantics, and any evidence that
  changes the next experiment after Step 0012

## Venue and format

The official [AAAI-27 Main Track call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
still permits seven content pages and two reference-only pages and evaluates
significance, novelty, soundness, relevance, and clarity. The current PDF
remains legally formatted: Conclusion ends on page 7 and pages 8--9 contain
references only.

## Verified closest capabilities

| Source | Verified capability | Consequence |
|---|---|---|
| [LangSmith Insights](https://docs.langchain.com/langsmith/insights) | Hierarchical cross-trace categories with error, latency, cost, feedback, attributes, and drilldown | Generic recurring semantic hierarchy and metric rollups are existing product capability |
| [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | Production interactions are embedded, clustered, labeled, organized into a topic hierarchy, compared across runs, and scoped to failures or evaluation gaps | Topic hierarchy, recurring failure discovery, and longitudinal pattern comparison are not sufficient novelty |
| [LangSmith Engine](https://docs.langchain.com/langsmith/engine) | Recurring trace-supported issues lead to proposed code/prompt fixes, deployable evaluators, generated offline examples, and optional pull requests | Product competition now reaches diagnosis-to-action rather than stopping at visualization |
| [pprof tags](https://github.com/google/pprof/blob/main/doc/README.md) | Profile samples already support labels, tag filtering, and `tagroot`/`tagleaf` pseudo frames; the source defines profile semantics | pprof compatibility and categorical pseudo frames are infrastructure, and AgentProf must justify its responsibility semantics |

## Verified research precedents

| Work | Primary-source finding | Consequence |
|---|---|---|
| [AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/) | Semantic/state-transition analysis filters trajectories and improves downstream WebArena training efficiency | Published analysis-to-intervention evidence exists |
| [Agent Mentor](https://arxiv.org/abs/2604.10513) | Semantic execution-log features produce corrective system-prompt instructions and repeated-run accuracy improvements across three configurations | Direct semantic-analysis-to-prompt-improvement precedent; closer to the paper's claimed quality impact than visualization alone |
| [TraceGraph](https://arxiv.org/abs/2605.31308) | Shared decision landscapes identify traps and guide a SWE-bench recovery pipeline with higher resolved rate on fired subsets | Strong graph-based population analysis with a measured downstream intervention |
| [AgentRx](https://arxiv.org/abs/2602.02475) | Critical failure-step and category localization over annotated cross-domain trajectories | Strong run-level diagnostic baseline, but not conserved cross-layer aggregate profiling |

## Effect of Step 0012

The new RQ2 table resolves the false impression that only raw-action baselines
were run. It visibly includes the strongest session, per-step, native, and
width references; it also marks TraceElephant's early region descriptive and
limits HINTBench attribution to the complete profile/prefix/scorer pipeline.
This is a real reporting improvement.

It does not resolve the external frontier. Existing products already discover
recurring semantic patterns with cost/latency/error aggregates, and both a
product and research systems now connect trace analysis to fixes or downstream
agent improvement. The remaining accept case must therefore rest on the
conjunction that those systems do not establish: source-linked conserved
system effects, selectable responsibility projections, and a demonstrated
decision or intervention enabled by that profile.

## Routing implication for full reread

Do not add another localization benchmark, score, cutoff, table row, or generic
semantic clustering comparison. If the blind reread confirms that central
utility remains the strongest reject reason, the next experiment should reuse
existing real traces/tasks and current AgentProf to test one profile-guided
decision or intervention against the strongest simple structural view. It
should remain one complete experiment and avoid a new annotation program or
human dependency.
