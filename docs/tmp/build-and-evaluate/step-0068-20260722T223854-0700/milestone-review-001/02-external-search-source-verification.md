# 02 — External Search and Source Verification

- **Timestamp:** 2026-07-22T23:02:00-07:00
- **Parent:** `step-0068-20260722T223854-0700/milestone-review-001`
- **Objective:** verify the closest product, profiling-format, process-analysis,
  and benchmark precedents using primary papers, official documentation, or
  official repositories
- **Search boundary:** claim/mechanism proximity, expected baselines,
  contradictory evidence, and accepted evaluation protocols

## Verified sources

The search used the literal query families `OpenTelemetry profiles data model
official`, `google pprof profile.proto tagroot tagleaf`, `LangSmith Insights
hierarchical traces`, `Graphectory agent observability`, `TraceProbe agent
traces`, `Hodoscope AI misbehavior monitoring`, `TraceGraph agent decision
landscapes`, and exact-title searches for AgentProcessBench, HINTBench,
TraceElephant, and CodeTracer. Search-result snippets, secondary summaries,
Reddit discussions, and unrelated trajectory papers were excluded. A source
entered the map only when its official documentation, repository, or primary
paper supported the compared capability.

### Profiling substrate

- [Google pprof repository](https://github.com/google/pprof) defines profiles
  as samples attached to location hierarchies and numeric values, supports
  aggregation and comparison, and consumes `profile.proto`.
- [Official pprof user documentation](https://github.com/google/pprof/blob/main/doc/README.md)
  states that `-tagroot` and `-tagleaf` can turn tag values into pseudo stack
  frames. Therefore “placing semantic labels in a pprof hierarchy” is not by
  itself a novel profiling mechanism.
- [OpenTelemetry Profiles specification](https://opentelemetry.io/docs/specs/otel/profiles/)
  defines profiles as stack traces with associated resource values, builds on
  pprof, and requires correlation with traces where applicable. It is strong
  precedent for AgentProf's standard-output and source-linkage choices, not
  evidence that OpenTelemetry already supplies agent-semantic responsibility.

### Closest product behavior

- [LangSmith Insights official documentation](https://docs.langchain.com/langsmith/insights)
  says Insights automatically analyzes trace populations, produces
  hierarchical categories and subcategories, aggregates error/latency/cost and
  other attributes, and allows predefined top-level categories with generated
  subcategories. It is the closest verified product precedent for cross-run
  semantic hierarchy and metric rollups.

This is a serious novelty comparator, but the initial reviewers stated the
overlap too broadly in calling it the “same mechanism.” The documented unit of
Insights is a trace/thread summary assigned to categories. AgentProf's claimed
unit is a recursively bounded operation span *inside* an ordered session source
tree, with the covered LLM/tool evidence kept in a weighted profile. The paper
must demonstrate why that distinction matters; it cannot merely list four
features and assume the reader accepts it.

### Closest research behavior

- [Graphectory](https://arxiv.org/abs/2512.02393) represents temporal and
  semantic relations as process graphs and studies 4,000 SWE-agent/OpenHands
  trajectories. It establishes large-scale process-centric analysis and
  recurring phase-pattern precedent.
- [TraceProbe](https://arxiv.org/abs/2607.06184) normalizes 2,500 coding-agent
  trajectories into a nine-action taxonomy, identifies anti-patterns, and
  aligns paired runs. It directly challenges any claim that AgentProf is the
  first cross-run trajectory diagnostic.
- [Hodoscope](https://arxiv.org/abs/2604.11072) compares behavior
  distributions across groups and reports 6--23x review-effort reduction while
  discovering real benchmark exploits. It is a particularly strong precedent
  for connecting population analysis to a downstream human decision.
- [TraceGraph](https://arxiv.org/abs/2605.31308) constructs shared decision
  landscapes from pooled trajectories and connects diagnosed trap regions to a
  recovery pipeline that improves resolved rate. It raises the evidence bar:
  analysis can be evaluated by the intervention it enables.

None of these sources combines AgentProf's exact operation-span annotation,
replayable additive resource measure, retained source evidence, and standard
pprof output. Collectively, however, they make “cross-run semantic grouping”
insufficient as the novelty claim.

### Evaluation-source verification

The supposedly unverifiable 2026 benchmarks in one model review are real and
have primary papers:

- [AgentProcessBench](https://arxiv.org/abs/2603.14465): 1,000 trajectories,
  8,509 human-labeled steps, ternary process-quality labels.
- [HINTBench](https://arxiv.org/abs/2604.13954): 629 long-horizon intrinsic-risk
  trajectories with risk-step localization.
- [TraceElephant](https://arxiv.org/abs/2604.22708): full-trace failure
  attribution for multi-agent systems.
- [CodeTracer / CodeTraceBench](https://arxiv.org/abs/2604.11641): hierarchical
  state reconstruction and stage/step supervision for coding failures.

Thus the blanket “unverifiable benchmarks” objection is rejected. The narrower
question—whether each AgentProf backend saw any field containing target labels
or target-derived strings—remains a project-side input audit, not something the
paper citation alone proves.

## Novelty conclusion

The defensible novelty is not:

- hierarchy alone;
- semantic clustering alone;
- pprof tags alone;
- cross-run diagnostics alone; or
- conservation as a mathematical discovery.

The strongest combined claim remains:

> AgentProf turns source-linked operation spans inside heterogeneous agent
> traces into a reusable semantic responsibility stack, then replays different
> additive measures through that same stack in a standard profiler.

This is potentially simple and deep. The missing empirical comparison is
whether that operation-level, multi-resource, source-drillable profile answers
a real population question better than trace-level hierarchical categories,
flat/source-native rollups, or process graphs.

## Baseline and protocol decision

A paid-product end-to-end LangSmith run is not automatically required and may
not expose operation-level output suitable for the paper's standard metrics.
The scientifically necessary comparison is the *capability*, not a brand name:

1. same real trajectory population;
2. same diagnostic question and hidden answer;
3. automatic AgentProf operation profile;
4. a strong trace-level hierarchical categorization/process baseline, plus the
   existing raw/source-native baseline;
5. decision quality or localization under the same evidence budget.

This can reuse current AgentReward/long-horizon data and does not require a new
benchmark or waiting for humans. If the commercial product is runnable and
exportable, it is valuable corroboration; it must not become a blocking
dependency.

## Completion, search-tree update, and uncertainty

**Status: complete.** The closest-work tree now has four branches: profiler
substrate, product hierarchy, research process analysis, and diagnostic
benchmarks. The product/research novelty risk is real, but it supports a
stronger operation-level multi-resource comparison rather than a smaller
paper. Unknowns remain around exportability of commercial product categories
and whether an open approximation will be accepted as a faithful comparator.
