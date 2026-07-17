# Blind full-paper read and attack map

## Node metadata

- **Started:** 2026-07-17 15:00:00 -07:00
- **Completed:** 2026-07-17 15:18:00 -07:00
- **Parent:** REVIEW gate, step 0044
- **Objective:** Form an independent AAAI-27 cross-domain assessment from the submitted paper alone, before consulting external sources or earlier review artifacts.
- **Target:** `docs/paper/main.pdf` and `docs/paper/main.tex`
- **Mode:** Read-only full-paper review. No paper edits and no Git operations.
- **Venue/domain routing:** AAAI-27 Main Technical Track; genuinely cross-domain systems/AI-agent measurement. I applied the research-taste, systems, AI/ML, and cross-domain review references.
- **Reviewer-context disclosure:** The task instruction necessarily disclosed the exact thesis, the four-RQ order, and the requirement not to shrink either. I did not read earlier reviewer reports, change logs, rebuttals, experiment proposals, or gate artifacts before this assessment.

## Inputs and provenance

I read the complete nine-page PDF, then read the complete 1,005-line LaTeX source to recover details that are difficult to inspect in PDF extraction. I inspected both claim-bearing figures, all four result tables, the abstract, introduction, background/motivation, design, implementation, all four evaluation subsections, limitations, related work, conclusion, and the full bibliography printed on pages 8--9. This is therefore a paper-only attack map, not a judgment influenced by prior internal explanations.

## Paper-only reconstruction

### Problem, stakes, and challenged belief

The paper argues that accumulating agent histories create population questions about quality, safety, and resource consumption that per-run tracing and debugging do not answer. The challenged default is that an execution/span tree plus metadata aggregation is a sufficient observability hierarchy. The paper's exact thesis is clear, repeated, and memorable:

> Agent observability needs profiling, not only debugging.

The stakes are credible on their face: repeated agent executions produce heterogeneous natural-language intent, tool calls, and system effects, but no stable analogue of code identity or a reusable cross-run call hierarchy.

### Simple principle

The best name-free statement of the principle is: treat completed agent activities as weighted records, then project the same records through query-selected semantic fields so that additive effects can be folded across runs without assuming a runtime call stack.

This is simple and potentially durable. It is more than a UI feature because it identifies what must replace both function identity and stack nesting. The paper is strongest when it stays at this level.

### Artifact and causal mechanism

AgentProf implements the principle as:

1. source-specific parsing/adaptation into uniform weighted operations;
2. field derivation using rules, a local model, mappings, or TF-IDF/K-Means;
3. either direct query-time field projection or automatic segmentation by recurrence of visible adjacent actions;
4. folding identical projected stacks while conserving additive measures; and
5. export to pprof, folded stacks, SVG, or JSON.

The causal chain claimed by the paper is:

```text
heterogeneous trajectories without stable code identity
-> uniform operations plus stable semantic fields
-> selectable operation stacks across runs
-> conserved population profiles
-> better responsibility partitioning and problem ranking
```

The first three links are technically explicit. The last link is tested, but the connection from semantic grouping to the motivating decisions remains less direct than the implementation/model connection.

### Claimed contributions and scope

The paper claims three contributions:

- a semantic operation-stack model for cross-run agent profiling;
- an approximately 9.8K-line offline Rust implementation with pluggable attribution and stack construction; and
- evaluation of cross-layer effect joining, semantic partition agreement, problem localization, field/group/boundary accuracy, and fixed-input profile construction.

The scope is not a live universal profiler. AgentSight recordings require an adapter; only declared process/tool scope is tested; several construction results are explicitly development/post-hoc evidence; and the cost result excludes capture, adaptation, and field/tag generation.

## Four RQs and paper-stated answers

The paper contains exactly four explicit paper-level RQs in the required order.

| RQ | Paper question | Paper-only answer | Claim/evidence assessment before search |
|---|---|---|---|
| RQ1 | Does semantic profiling improve resource attribution? | Scoped joining obtains 100.0% precision and 96.6% recall; folding conserves weights; semantic responsibility grouping improves ordinary B³ F1 over raw action; selectable weights expose different rankings. | Partly answered. Capture/join accuracy and conservation test attribution directly. B³ against human stages tests partition agreement rather than correctness of resource responsibility, and phase-only slightly exceeds recurrence (0.654 vs. 0.649). The paper acknowledges this, but the RQ title is broader than its strongest construct. |
| RQ2 | Does profiler output correspond to real problems? | Semantic grouping improves MAP over raw-action grouping on all three complete localization workloads; local-first post-hoc analysis shows semantic grouping can refine tied local evidence. | The most persuasive RQ. It uses complete public populations, independent targets, standard AP/MAP, a matched raw-action baseline, and clustered intervals. The mechanism is clearest on HINTBench and TraceElephant; AgentProcessBench gains only 0.016 in the primary comparison and does not distinguish local tie-breakers. |
| RQ3 | How accurate are the tags? | Reports macro-F1/accuracy for literal task/action tags; V-measure/B³ for partitions; exact boundary precision/recall/F1 for group boundaries. | Answered only as a collection of scoped backend/protocol results, not as one general accuracy statement. The term “tag” covers literal class labels, partitions, phases, and boundaries with very different information boundaries. Several results are strong, but the action backend reaches only 0.498 macro-F1, Mind2Web has nine sessions/49 operations, and the label-free rule was selected after inspecting OSWorld-Human. |
| RQ4 | What is the profiling cost? | Fixed-field parsing, stack construction, folding, and serialization process 27,765 operations in 1.17 s and add 18.2% time/1.3% peak RSS over raw grouping. | Answered for the explicitly narrowed fixed-input construction path. It does not establish end-to-end capture, adaptation, or tag-generation cost, but the paper discloses those exclusions consistently. |

## Standard-metric audit from the paper alone

The paper-facing primary metrics are recognizable standard metrics and are cited at first methodological use:

- ordinary operation-level B³ precision/recall/F1 for partition agreement;
- non-interpolated AP per query and MAP across queries for localization;
- macro-F1 and accuracy for literal multi-class labels;
- V-measure for partition agreement;
- exact adjacent-boundary precision/recall/F1 for segmentation; and
- elapsed time, throughput, and peak RSS for construction cost.

No token-weighted B³, Recall@20%, fixed-top-k reader score, or model-reader score appears in the paper. The 95% Wilson lower bound is an internal group-scoring rule used before standard MAP, not presented as a general metric. Its scientific validity still requires protocol scrutiny, but it does not replace the paper-facing metric.

## Attack map before external search

### Strongest plausible reject argument

**The paper has an important principle, but it has not yet isolated a sufficiently novel and causally supported joint contribution from already-established semantic grouping, cross-trace aggregation, profiling tags, and cross-run agent graphs.** The paper itself concedes that current platforms derive hierarchical categories and roll up metrics, pprof can promote tags to pseudo-frames, OpenTelemetry links profiles and traces, and recent research builds process profiles or recurring graphs. Its residual claim is the conjunction of source-linked heterogeneous effects, conservation of arbitrary additive measures, and query-selectable stacks over one corpus. A skeptical reviewer can interpret that as a useful composition of known mechanisms unless external comparison shows that the combination creates a new capability or falsifiable result unavailable to the closest systems.

### Other load-bearing reject hypotheses

1. **Construct mismatch in RQ1 (evidence/evaluation, major).** Human-stage B³ evaluates structural partition agreement, not whether resource cost is assigned to the correct semantic responsibility. The 20-task capture suite tests system-effect joining but uses predeclared task categories and a declared process/tool scope. The motivating claim spans task intent, workflow, unsafe effects, and cost, while the directly validated cross-layer attribution set is small.

2. **Mechanism-selection and independence risk (technical/evaluation, major).** Label-free recurrence is a heuristic NPMI plus one-dimensional k-means rule with an additional action-change cutoff. CodeTraceBench and OSWorld-Human influenced constructor selection, so its two most visible recurrence results are development/post-hoc evidence. Session-held-out folds prevent direct target leakage but do not create a genuinely untouched corpus after method design.

3. **Weak strongest-baseline story (novelty/evaluation, major).** Raw-action identity is a useful matched control but not obviously the strongest competing scientific position. Phase-only slightly wins on CodeTraceBench. The paper does not numerically compare against a span/metadata hierarchy, a current cross-trace hierarchical grouper, an established changepoint/sequence segmentation method, or a stronger semantic embedding baseline under the same information budget.

4. **Heterogeneous RQ3 evidence (global logic/evaluation, major).** RQ3 combines deterministic mappings, unsupervised partitions, an LLM classifier, a standalone action adapter, supervised boundary prediction, and label-free recurrence. These demonstrate interface breadth, but they do not establish one coherent accuracy property of AgentProf's production path. The strongest supervised result requires annotations; the default label-free result is development evidence.

5. **Decision consequence remains indirect (cross-domain evidence, major).** RQ2 shows ranking correspondence to independently annotated problems, which is valuable, but the paper does not show a developer actually finds, diagnoses, or fixes a problem faster or more accurately because of the aggregate profile. This is not automatically a demand for a new user study; it is a missing causal edge that might instead be repaired by a sharper external precedent and evidence synthesis.

6. **Full-path cost is unmeasured (evidence, minor-to-major depending on claim).** The 1.17 s headline covers only fixed-field profile construction. Local LLM tag generation, source adaptation, capture, and live overhead are excluded. The paper is transparent, so this is not a soundness flaw, but the abstract/conclusion phrase “practical complement” is broader than RQ4 alone proves.

### Largest writing-only gap

The paper's differentiator is distributed across the introduction, formal view, related work, and evidence synthesis rather than made explicit as one falsifiable capability comparison. RQ3 reads as a metric-rich backend catalogue. These are writing/argument-architecture issues only if external search confirms novelty; prose cannot repair substantive overlap.

### Global consistency and presentation

- Thesis, four RQs, high-level mechanism, and scoped limitations are internally consistent.
- The abstract and conclusion correctly use ordinary B³ and standard MAP rather than bespoke inspection-budget metrics.
- The architecture figure is legible and accurately represents the implementation boundary.
- The flame graphs establish that multiple measures can be projected over one corpus, but their internal labels are too small to support fine-grained visual conclusions; the text uses only aggregate top-category comparisons.
- Tables are readable and captions identify metrics and comparison direction.
- I found no paper-internal number contradiction in this blind read.

## Initial paper-only verdict

**Score: 5/10, borderline Weak Reject. Confidence: 4/5.**

This is **incomplete-but-promising**, not complicated-but-shallow. The exact thesis is significant and the operation-stack model is simple enough to be memorable. RQ2 is meaningful, public, and standard-metric based. The present acceptance risk is that the novelty is a conjunction of known observability/profiling features and that the central mechanism's cleanest evidence is post-hoc or compared mainly with raw action. The paper needs source-grounded novelty isolation and a stronger evidence-to-construct explanation; whether it needs another experiment cannot be decided before checking the closest work and accepted protocols.

## Load-bearing external questions

The next search node must verify:

1. whether LangSmith Insights, Datadog Patterns, OpenTelemetry Profiles, and NeMo already provide the claimed hierarchical cross-trace aggregation and profile linkage;
2. whether TraceProbe, WebGraphEval, Hodoscope, TraceGraph, AgentRx, and CodeTracer make same-claim or same-mechanism contributions;
3. what published profile/trace systems already support tag-to-frame promotion, selectable projections, and conserved additive measures;
4. which standard sequence/segmentation or clustering baselines are reviewer-expected for the recurrence mechanism;
5. whether AP/MAP, B³, V-measure, macro-F1, and exact boundary F1 are used consistently with their defining sources; and
6. whether there is primary evidence that population-level analysis is distinct from per-run debugging and useful for agent reliability decisions.

## Search/tree and project-memory disposition

- **Search-tree update:** Open six branches: observability products/standards; cross-run agent analysis; diagnosis/localization; profiling foundations; segmentation/partition metrics; AAAI relevance and evaluation norms.
- **Project-memory update:** None. Blind-review findings are provisional evidence, not author intent and not canonical state.
- **Completion assessment:** Blind read and attack map complete.
- **Uncertainty:** High around 2026 same-claim work and commercial feature scope; moderate around whether the absence of a direct human-decision result is fatal at AAAI.
- **Next node:** External primary-source search and verification, followed by a complete paper reread.
