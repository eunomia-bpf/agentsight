# Blind full-paper review: paper-only attack map

**Reviewer/model:** fresh internal Codex subagent. The runtime did not expose
its exact backend model identifier, so that identifier is recorded as unknown
rather than inferred.

## Scope, routing, and contamination

- Target venue: AAAI 2027, inferred from `\usepackage[submission]{aaai2027}`.
- Primary domain: systems-heavy AI-agent observability.
- Review standard: cross-domain. The claimed abstraction/artifact is systems work, while tag generation and the evaluation rely on AI/ML models, agent benchmarks, and annotation protocols.
- References loaded: `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, and `cross-domain-review.md`.
- Read: all active text in `main.tex`, the included TikZ architecture, the three included flamegraph PNGs and companion SVG metadata, `references.bib`, and the compiled `main.bbl`. Inline tables are in `main.tex`.
- Not read: `docs/user-instruction.md`, `docs/idea-story.md`, `docs/evaluation.md`, prior reviews, experiment reports, git state/history, or repository implementation.
- No external search was performed.

Unavoidable contamination:

1. The injected repository instructions identify AgentSight as an eBPF observability framework and describe its architecture. I therefore was not fully blind to the parent artifact.
2. The task path itself contains `agentsight-research-semantic-flamegraph`.
3. `references.bib` contains author-written `VERIFIED`, `REAL`, `ABSTRACT`, and `USED_FOR` comments. I treated none of those as independent verification.
4. `main.tex` contains Chinese translations and inactive earlier-draft comments. I based the assessment on active rendered text.
5. Inspecting companion SVG title metadata exposed values and stack labels not legible in the bitmap; no experiment records or generation scripts were read.

## Paper as perceived by a reviewer

### Problem and stakes

The paper argues that teams accumulate many agent trajectories but cannot readily answer population-level questions about cost concentration, repeated failure locations, and unsafe system effects. Existing execution traces lack:

- shared semantic identity across natural-language runs;
- a reusable semantic responsibility hierarchy analogous to a call stack;
- source-linked aggregation of agent actions and downstream process/file/network effects.

The stakes are credible in the abstract, but the manuscript supplies little paper-internal evidence that production teams actually face this exact abstraction gap, or that current population dashboards cannot answer the motivating questions.

### Challenged belief

The implicit challenged belief is:

> Profiling requires stable code identities and runtime call stacks, so agent observability should remain trace/debug oriented.

A second implied belief is that ordinary metadata grouping is insufficient unless represented as a profiler stack with conserved measures.

This belief challenge is weakly established. The paper itself acknowledges that LangSmith Insights, Datadog Patterns, TraceProbe, Graphectory, Hodoscope, and TraceGraph already provide cross-run semantic grouping, metric rollups, profiles, or recurring structure ([main.tex:137](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:137)). The remaining novelty is defined as the conjunction of source-linked effects, arbitrary additive measures, and selectable field stacks, not a demonstrated conceptual limitation of prior systems.

### Simple principle

The clearest plain-language principle is:

> Convert trajectory events and linked effects into weighted rows, then treat an ordered semantic grouping key as a synthetic stack and fold identical keys.

This is simple and coherent. The concern is that it may be an OLAP/group-by view serialized as pprof rather than a new profiling abstraction. Conservation follows mechanically from summing unchanged weights, not from a new correctness property.

### Mechanism

The mechanism is:

1. Parse Codex/Claude histories or source-adapted operation JSONL.
2. Represent prompts, calls, tools, GUI actions, and system effects as uniform string-field records with nonnegative measures.
3. Derive fields with regex rules, a local LLM, TF-IDF/K-Means, or dataset mappings.
4. Select an ordered field list at query time.
5. Project each operation to that tuple, merge identical tuples, and sum weights.
6. Export pprof, folded stacks, SVG, or JSON.
7. Optionally derive group boundaries using transition NPMI plus weighted one-dimensional \(k=2\) means at coarse and detailed action resolutions.

The causal chain is incomplete:

```text
agent history
→ derived tags/groups
→ synthetic tuple hierarchy
→ folded profile
→ ? better population decision or intervention
```

The evaluation largely stops at partition agreement or per-trajectory localization MAP. It does not show that a developer identifies a population-level bottleneck, unsafe pattern, or cost problem faster or more accurately.

### Claimed contributions versus perceived contribution

Claimed:

1. Semantic operation stack model.
2. AgentProf implementation with pluggable derivation/construction and pprof output.
3. Broad evaluation of joining, partitioning, localization, tagging, and cost.

Perceived:

1. A faceted aggregation schema encoded as profiler stacks.
2. A pprof/export implementation plus adapters.
3. A transition-segmentation heuristic.
4. A broad but fragmented benchmark collection whose experiments do not jointly validate the central population-profiling claim.

“Evaluation” is evidence, not normally a scientific contribution unless the datasets/protocols themselves are new and reusable.

## RQ map and stated answers

| RQ | Paper’s answer | Reviewer assessment |
|---|---|---|
| RQ1: Does semantic profiling improve resource attribution? | Capture/join yields 100% precision and 96.569% recall; recurrence raises B³ F1 from .541 raw-action to .663; folding conserves weights; selectable views expose different rankings. | Not independently answered end to end. Capture uses predeclared categories and mostly evaluates AgentSight joining. Stage-partition agreement is not weighted resource-attribution error. The method is only .009 above phase-only (.663 vs .654), with no uncertainty for that comparison, and CodeTraceBench influenced method selection. |
| RQ2: Does profiler output correspond to real problems? | Semantic grouping beats raw-action MAP on three benchmarks: .789/.452/.230 vs .773/.281/.121. | Benchmark-conditionally positive, but construct validity is weak. AgentProf is supplied benchmark judge/localizer predictions that already encode diagnostic evidence. It then smooths/reranks them. Evaluation is per-trajectory AP, not population-level inspection effort or group-level actionability. Strongest local+semantic evidence is explicitly post hoc. |
| RQ3: How accurate are the tags? | Reports heterogeneous task partitions, phase partitions, task-family labels, action labels, and group boundaries. | No single answer exists. It conflates literal tags, partitions, and boundaries. Production 3B tagging is not evaluated; the 27B task model is evaluation-only, action labeling is standalone, and recurrence evidence is development/post-hoc on both principal corpora. |
| RQ4: What is profiling cost? | Fixed-field construction processes 27,765 operations in 1.17 s at 464.5 MiB RSS, with 18.2% time and 1.3% memory overhead over raw grouping. | The narrow folding kernel is answered. Full profiling cost is unanswered because capture, adaptation, field/tag generation, model inference, and live-agent overhead are excluded. At roughly 16.7 KiB RSS per operation, 27,765 operations is not persuasive scale evidence. |

All four RQs are explicit, but only the narrow version of RQ4 is cleanly answered.

## Strongest reject hypotheses

### Blocker 1 — The evaluation does not validate the population-level profiling claim

The paper motivates cross-run quality, safety, and cost analysis ([main.tex:111](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:111)), but its strongest quantitative experiments are per-trajectory stage segmentation and per-trajectory problem localization.

- RQ1’s B³ evaluation asks whether contiguous operations match human stages inside failed coding trajectories.
- RQ2 treats each trajectory as one AP query ([main.tex:721](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:721)).
- RQ3 evaluates labels or boundaries.
- The only true population views are illustrative flamegraphs with no correctness, decision-quality, or user-effort outcome.

Thus the paper says “profiling, not only debugging” but validates mostly debugging/localization constructs. The decisive missing evidence is a real population-level task in which AgentProf helps a developer discover or prioritize a repeated cost, reliability, or safety problem better than a strong dashboard/query baseline.

Routing: primarily EXPERIMENT_GATE; the framing also needs WRITE_GATE after evidence exists.

### Blocker 2 — The core abstraction may be a renamed multidimensional group-by

The formal view \((\varphi,\sigma,w)\) is filter, ordered grouping key, and aggregate ([main.tex:404](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:404)). The manuscript already acknowledges:

- pprof tag promotion;
- Pivot Tracing’s dynamic selection/grouping;
- metadata aggregation and hierarchical rollups;
- trace-linked profiles;
- recent cross-run process profiles and graphs.

The paper does not identify an invariant, query, or capability that fundamentally requires “operation stacks” rather than existing tagged events plus group-by/rollup. “Conservation” is true by construction whenever weights are copied and summed.

This is the largest novelty risk and requires external verification before a final verdict. If prior systems already support arbitrary attribute projections and trace/profile linkage, the contribution reduces to an adapter/export format plus one segmentation heuristic.

Routing: external novelty verification first; likely WRITE_GATE plus mechanism sharpening, possibly EXPERIMENT_GATE for direct baseline comparison.

### Major 3 — RQ2 measures smoothing of an existing diagnostic signal, not discovery by the profile

AgentProf and raw grouping both receive the same precomputed benchmark judge/localizer predictions ([main.tex:710](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:710)). Profiles then aggregate those scores. This establishes that some grouping can improve rankings over a weak raw-action grouping, not that semantic profiling independently identifies problems.

Problems:

- No strong semantic hierarchy, clustering, trace-query, or closest-system baseline.
- No random-group or size-matched grouping control.
- No group-inspection metric such as groups reviewed before first/most faults.
- No user-time or downstream repair outcome.
- Exact field orders/mappings for AgentProcessBench and TraceElephant are not specified.
- Local+semantic is post hoc; on AgentProcessBench it is indistinguishable from local+raw.
- “Target blind” does not remove the fact that benchmark predictions were expressly generated to predict the targets.

Routing: EXPERIMENT_GATE.

### Major 4 — Recurrence evidence is development evidence on both principal corpora

CodeTraceBench influenced constructor selection ([main.tex:665](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:665)). The OSWorld rule was also designed after inspecting earlier results on that corpus ([main.tex:794](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:794)). Session-held-out folds prevent direct training leakage but not researcher overfitting to the dataset.

Further:

- Multi-resolution beats coarse by only .014 and phase-only by .009.
- OSWorld lacks nonredundant action detail, so it does not independently test the multi-resolution mechanism.
- Label-free boundary F1 is .680 versus .645 for “always boundary,” only a .035 gain, with no uncertainty.
- No untouched dataset evaluates the final recurrence rule.
- No ablation isolates the global cutoff, action-changing cutoff, “either resolution continues” rule, or run-length-compressed naming.

Routing: EXPERIMENT_GATE.

### Major 5 — The evaluated AI backends do not match the implemented production path

The implementation describes a quantized 3B local tagger ([main.tex:488](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:488)), but:

- task-family evaluation uses a distinct evaluation-only 27B model;
- action-tag evaluation uses a standalone adapter not integrated into the CLI;
- the action macro-F1 is only .498;
- majority-class is the only literal-label baseline;
- no cross-model, prompt, calibration, drift, or category breakdown is reported;
- “stable/repeatable tags” are not tested across model versions, paraphrases, time, or domains.

The paper cannot currently claim validated production tag accuracy.

Routing: EXPERIMENT_GATE.

### Major 6 — “Semantic hierarchy” lacks a responsibility semantics

An arbitrary ordered tuple does not automatically form a causal or responsibility hierarchy. Reordering fields changes parent/child relationships without changing evidence. The paper does not define why, for example, `task → phase → action` encodes responsibility rather than merely drill-down dimensions.

Missing invariants include:

- treatment of absent fields and sentinels;
- escaping and collision behavior;
- high-cardinality fields;
- multiple or asynchronous responsible intents;
- effects shared across concurrent tools;
- overlapping spans and nested operations;
- tag drift;
- whether frame order must obey any semantic dependency.

The automatic constructor produces flat contiguous groups whose compressed action sequence becomes one field; it does not itself infer a multilevel hierarchy.

Routing: WRITE_GATE for formal semantics and EXPERIMENT_GATE for causal attribution.

### Major 7 — The “additive resource” story is not sound for elapsed duration

The model requires additive measures, but the `time` profile sums per-operation elapsed durations ([main.tex:410](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:410)). Nested or concurrent prompts, LLM calls, and tools can overlap, so elapsed durations are not generally additive resource consumption. Summing them can exceed wall-clock time and double-count responsibility. The paper acknowledges idle/user wait but not overlap.

Similarly, copied semantic fields establish bookkeeping conservation, not correct causal attribution. A unique “responsible intent” is assumed rather than modeled.

Routing: mechanism repair plus EXPERIMENT_GATE.

### Major 8 — RQ4 omits the likely dominant costs

The reported 1.17 s excludes capture, adaptation, field derivation, and model inference ([main.tex:891](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:891)). These are precisely the distinctive and potentially expensive stages. The current CLI also cannot directly read AgentSight recordings.

The test covers only one high-end machine, three medians, and at most 27,765 operations. There is no cold/warm-cache distinction, output-size scaling, peak memory for raw rows in the table, or million-operation test. “Making population profiling practical” is therefore premature.

Routing: EXPERIMENT_GATE.

## Algorithm and systems-taste assessment

### Inferred complexity

The paper gives no formal complexity.

- Direct field projection and hash folding: expected \(O(nk)\) time for \(n\) operations and \(k\) selected fields, with \(O(uk)\) aggregate-key storage for \(u\) unique stacks, plus input retention if not streaming.
- Coarse recurrence fitting: \(O(N + IM)\) time and \(O(M)\) space for \(N\) reference transitions, \(M\) distinct scored transitions, and \(I\) weighted 2-means iterations. Detailed recurrence roughly duplicates this work.
- Target segmentation: expected \(O(T)\) lookups over \(T\) target transitions.
- Reference-calibrated cutoff: complexity is unclear; naive enumeration and rescoring could be \(O(MN)\).
- TF-IDF/K-Means and LLM inference dominate field derivation but are excluded from RQ4 and lack cost parameters.

### Mechanism taste

The NPMI thresholding is deterministic and reasonably specified, but its rationale is underdeveloped:

- NPMI is unstable for rare transitions; no smoothing or minimum-support rule is stated.
- Two-means assumes a useful two-cluster score structure without showing it.
- Min/max initialization is outlier-sensitive.
- Choosing the smaller cross-action cutoff can only merge relative to the global rule.
- Detailed continuity can only remove coarse boundaries, never add one; richer detail therefore cannot reveal a finer boundary.
- Segment names based on compressed action sequences may become high-cardinality and undermine cross-run folding.
- Reference-corpus selection and distribution drift are unspecified.

Taste verdict: the core is simple but likely shallow; the surrounding terminology, backends, and evaluation matrix make the work appear more complex without producing one deeper falsifiable principle. I would currently classify it as **complicated-but-shallow, with an incomplete-but-promising systems use case**.

Terms that could be merged without loss:

- “operation” → event/row;
- “operation stack” → ordered grouping hierarchy/key;
- “semantic operation stack model” → filtered weighted aggregation view;
- “intent attribution” and “field derivation”;
- “stack construction,” “boundary construction,” and “group-field construction” need clearer separation;
- “recurrence constructor” could be “transition-based segmentation.”

## Figure and text inconsistencies

1. **Architecture omits the claimed novelty.** Figure 1 is essentially `inputs → operations → field derivation → stack/fold → profiles`. It does not show AgentSight’s source-linking relation, predicates/weights, query-time field selection, recurrence, or responsibility semantics. “Rules/model/mapping” also omits explicit clustering. It is too generic to explain why this is not an ordinary ETL/group-by pipeline.

2. **The flamegraph figure is nearly uninterpretable in paper form.** Most upper-frame labels truncate to `k.`, `m.`, `c.`, etc. The caption does not state each graph’s exact field order. The figure demonstrates that an SVG can be produced, not what operational conclusion a developer draws.

3. **The three flamegraphs change several variables simultaneously.** They differ in included operation types, stack fields, and width measure ([main.tex:586](/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/paper/main.tex:586)). Therefore visual differences cannot isolate the effect of changing resource measure.

4. **Population aggregation is visually ambiguous.** The visible hierarchy includes a `session` frame. If this is a unique session identity, it prevents folding below that level across runs; if values such as `review` and `dev` are semantic categories, the field name is misleading.

5. **Duration visualization conflicts with additive-resource language.** The middle graph uses summed elapsed durations, but overlapping/nested operations can double count.

6. **OSWorld counts need an explicit scope bridge.** RQ3 uses 3,978 operations with complete annotations; RQ4 lists 6,010 OSWorld-Human operations. This can be legitimate, but the paper does not explicitly explain the filtering difference.

7. **RQ3’s title is inconsistent with its contents.** “Tag Accuracy” combines literal tag classification, permutation-invariant partitions, and boundary segmentation, which are materially different outputs.

8. **The architecture says AgentSight adapters feed operation JSONL, while implementation says the CLI cannot read AgentSight recordings directly.** This is not a strict contradiction, but the diagram visually integrates a path that remains an external adapter.

9. **Compilation is otherwise clean.** The provided PDF is 9 pages, with no unresolved references/citations in the log; only underfull-box warnings were observed. Venue page-limit compliance was not externally checked.

## Load-bearing claims requiring external verification

1. No prior tool combines source-linked system effects, arbitrary conserved measures, and selectable query-time semantic stacks.
2. Existing tracing/observability systems are inadequate for the stated population questions.
3. Operation stacks add capability beyond pprof tags, OpenTelemetry Profiles, Pivot Tracing, SQL/group-by dashboards, LangSmith Insights, Datadog Patterns, and NeMo profiling.
4. TraceProbe, Graphectory, Hodoscope, and TraceGraph do not already make the same or stronger cross-run claim.
5. AgentSight’s join semantics justify calling matched effects causally “responsible,” especially for async/concurrent work.
6. CodeTraceBench’s 405 reconstructable failures, stage labels, and official operation sequence match the paper’s protocol.
7. The split construction is genuinely target-disjoint and no target feedback influenced final recurrence beyond the admitted development use.
8. AgentProcessBench, HINTBench, and TraceElephant label semantics support the paper’s AP/MAP transformation.
9. The HINTBench 536-test/80-validation snapshot and selection among 24 field orders are official and nonoverlapping.
10. OSWorld-Human’s 287 sessions, 2,042 groups, and group meaning support responsibility attribution rather than only motor-action segmentation.
11. AgentBoard’s nine families and the ASE/TraceView eight-action taxonomy match the prompts and labels used.
12. Qwen3.6-27B identity, release, quantization/configuration, prompt, and deterministic outputs are reproducible.
13. Ordinary B³ and exact boundary F1 are accepted constructs for these stage/group tasks.
14. The reported private 325-history corpus is representative, ethically collected, and not dominated by the authors’ own research workflow.
15. The 20-task capture ground truth and concurrent controls establish more than PID/process-scope isolation.
16. pprof compatibility is semantically valid for arbitrary string-field hierarchies and round-trips all claimed weights.
17. The three recent localization benchmarks and several 2026 arXiv closest works are real and accurately characterized.

## Strongest alternative explanation

The results can be explained without a new profiling principle:

> Any reasonable semantic grouping of temporally correlated agent operations will smooth an existing diagnostic score better than raw action identity; serializing those grouped sums as pprof yields attractive flamegraphs, but does not establish new attribution semantics or population-level decision value.

## Largest defensible opportunity

The most ambitious credible claim is not “agents need profiling” in general, but:

> A single source-linked operation corpus can support multiple conserved cost/effect views, and a learned cross-run hierarchy can make recurring operational problems cheaper to inspect than existing trace/dashboard representations.

That larger claim would be valuable, but it needs:

- a strong existing observability/query baseline;
- an untouched final-method dataset;
- end-to-end capture through tagging and profile construction;
- a real population-level diagnosis task;
- developer effort or decision-quality measurement;
- overlap-aware resource accounting.

## Preliminary paper-only verdict

**Reject / major revision.**

The paper is unusually candid about post-hoc evidence and contains substantial implementation and benchmarking effort. Arithmetic and within-table consistency appear generally careful. However, the central scientific contract is not closed:

- novelty may collapse to multidimensional aggregation plus pprof export;
- the principal population-level value proposition is not evaluated;
- the automatic hierarchy is development-tuned with no untouched confirmation;
- the production tagging path is not the path evaluated;
- cost excludes distinctive stages;
- “hierarchical responsibility” and additive duration lack sound semantics.

Current characterization: **complicated-but-shallow around a potentially useful systems tool, and incomplete-but-promising if the authors can demonstrate a decisive population-level workflow against strong current baselines.**
