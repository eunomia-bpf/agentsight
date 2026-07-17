# Step 0033 Milestone Review 001 — Source-Grounded Full-Paper Reread

**Timestamp:** 2026-07-16T17:33:02-07:00
**Parent node:** Step 0033, `REVIEW_GATE`, milestone review 001
**Objective:** Reread the complete rendered paper, including every figure and table, after external source verification; determine which blind-review attacks survive and assess the new RQ2 evidence in the context of the whole paper. This phase still excludes author-intent and cycle-history documents.

## Inputs and review independence

I reread all nine rendered pages of `docs/paper/main.pdf`, checked the corresponding complete `docs/paper/main.tex`, and revisited every table and reader-facing figure after completing the source-verification report. I did not yet read `docs/user-instruction.md`, `docs/idea-story.md`, the Step 0033 experiment plan/results/reviews/write report, or the cycle diff. This report is therefore a source-grounded paper assessment, not yet a compliance audit of how the cycle was executed.

The paper remains genuinely cross-domain and systems-led. Its abstraction and implementation must meet a systems bar; its semantic grouping, agent-problem correspondence, label induction, datasets, and ranking protocol must meet an AI/ML evaluation bar. Neither side can be excused by the other.

## Full-paper reconstruction after external verification

The paper's one-sentence thesis is present verbatim in the Abstract, Introduction, and Conclusion:

> Agent observability needs profiling, not only debugging.

The durable challenged belief is not that current tools literally perform no aggregation. Official LangSmith, Datadog, and NeMo documentation disproves such an absolute claim. The defensible and still ambitious belief challenge is that the execution-local trace/call hierarchy should be the sole or authoritative responsibility hierarchy for population-level agent observability. AgentProf proposes that one conserved stream of heterogeneous operations can instead be projected at query time into selectable semantic responsibility hierarchies.

The paper preserves four explicit research questions:

1. **RQ1: Does semantic profiling improve resource attribution?**
2. **RQ2: Does profiler output correspond to real problems?**
3. **RQ3: How accurate are the tags?**
4. **RQ4: What is profiling cost?**

It also preserves three explicit contributions: the semantic operation-stack model, the AgentProf system, and the evaluation. The reader-facing story is therefore coherent at the paper level: additive cross-layer operations supply the substrate; stable semantic fields and operation stacks supply alternative responsibility structures; folding supplies population profiles; RQ1 checks attribution/fidelity, RQ2 checks correspondence to real problems, RQ3 checks learned fields and boundaries, and RQ4 checks offline cost.

## Research-taste assessment

### Principle, depth, and simplicity

The central principle remains simple and potentially durable:

> Aggregate agent histories by semantic responsibility using selectable additive projections, rather than accepting execution location as the only hierarchy.

This is larger than a new failure localizer and more interesting than a visualization feature. The most important conceptual move is separation of the operation substrate from the hierarchy used to interpret it. The same operations can be projected by task, phase, session, or action and weighted by tokens, time, or system effects without rebuilding the history. That is a recognizable profiling principle.

The paper is less simple at the automatic-construction mechanism. The recurrence constructor combines NPMI, occurrence weighting, one-dimensional two-means, an additional cross-action cutoff, and a monotone minimum rule. The paper explains what it does, but the mechanism does not yet have the inevitability of the operation-stack abstraction. This is a broader scientific opportunity rather than a reason to shrink the thesis or discard the current Step 0033 evidence.

### Challenged belief versus strawman risk

The Introduction now acknowledges cross-trace product hierarchies and aggregated latency/cost/evaluation metrics before stating AgentProf's distinction: source-linked additive cross-layer effects exposed as selectable pprof-compatible operation-stack projections. This is materially better than claiming all existing observability is single-trace debugging. The claim is supportable from public documentation.

The paper still needs a stronger eventual answer to the reviewer who says this is novelty by conjunction: products already group traces and prioritize cost/errors; pprof already accepts tags and pseudo-frames; diagnosis systems already localize failures. The current defense is that AgentProf constructs arbitrary ordered projections over conserved, source-linked operations and can change hierarchy without changing the underlying evidence. That is plausible and substantive, but a future closest-alternative comparison would make the principle harder to dismiss as engineering unification.

### Realism and evidence breadth

The paper uses real local Codex and Claude histories, a controlled 20-task source-lineage suite, 15 mapped public families, three public problem-localization datasets, OSWorld-Human group boundaries, CodeTraceBench failures, AgentBoard families, published software-engineering action labels, and a complete construction-cost path. This is a strong real-world evidence strategy. It does not depend on a toy synthetic environment or a self-written microbenchmark as the sole proof.

## RQ2: detailed assessment of the Step 0033 result as presented

### Estimand and primary metric

The evaluation defines one target-bearing trajectory as one query, operations as ranked items, and annotated problem operations as relevant. It computes standard non-interpolated AP for each such query and arithmetic-mean MAP across queries. That is a standard information-retrieval metric and a defensible common estimand across datasets with one or more relevant operations.

The three reported query populations and main results are:

| Workload | Target-bearing trajectory queries | AgentProf MAP | Raw-action MAP | Paired delta and interval |
|---|---:|---:|---:|---:|
| AgentProcessBench | 614 | 0.789 | 0.773 | +0.016, 95% CI [0.005, 0.027] |
| HINTBench | 400 | 0.453 | 0.281 | +0.171, 95% CI [0.155, 0.189] |
| TraceElephant | 220 | 0.230 | 0.121 | +0.109, 95% CI [0.078, 0.141] |

All three paired intervals exclude zero. AgentProcessBench provides a small but consistent improvement; HINTBench and TraceElephant provide substantially larger matched grouping effects. Because the same released scalar signal is used before and after grouping, the comparison isolates semantic redistribution/aggregation rather than claiming that AgentProf independently diagnoses problem content.

### Conditional query population

The protocol subsection and Table 1 disclose the target-bearing query condition, and the table gives 614, 400, and 220. All operations, including those from zero-positive trajectories, are still scored and enter pooled operation AP. Scientifically this is reasonable.

However, the Introduction says “Across three complete public benchmarks with 27,346 labeled steps, trajectory MAP rises ...,” and Table 1's caption says “complete RQ2 workloads.” A fast reader can infer that MAP averages all dataset trajectories rather than the 1,234 target-bearing queries. “Complete” is true of workload ingestion but ambiguous about the MAP denominator. This is a current Step 0033 wording must-fix. The paper should make the two facts adjacent: all operations in each workload were scored, while trajectory MAP averages only target-bearing trajectories.

The fix is precision, not metric replacement. Assigning AP to a no-relevant-item trajectory would conflate problem detection with within-trajectory ranking. The paper already retains those records in pooled AP, which is the better safeguard.

### Pooled operation AP

The paper reports pooled operation AP of 0.692 versus 0.669 on AgentProcessBench, 0.250 versus 0.180 on HINTBench, and 0.078 versus 0.053 on TraceElephant. This is correctly presented as secondary. Pooled AP weights long trajectories more heavily and asks a different question from query-equal MAP, but it retains the zero-positive population as nonrelevant inspection work. Its direction agrees with MAP on all three workloads.

This is the right amount of robustness checking. Adding nDCG, MRR, Recall@K, or more composite metrics would increase surface area without changing the main inference.

### Work measures and reader task

The six-task rank-hidden reader reports median recall +0.081 and precision +0.036, but median work +0.006, where more work is worse. The prose therefore correctly limits the conclusion to improved prioritization under the fixed display budget and explicitly states that it does not establish lower inspection work, human utility, or universal dominance.

The benchmark-level Work results remain useful operational diagnostics:

- HINTBench Work@80 is 41.57% for AgentProf and 46.29% for raw action; only the raw-action interval crosses zero.
- TraceElephant Work@50 is 19.55% for AgentProf and 46.64% for raw action.
- TraceElephant Work@80 requires the full trajectory and its interval crosses zero.

These measures are not universal standard ranking metrics and should remain secondary and benchmark-specific, as they do in the current paper. Their mixed pattern is not a reason to remove RQ2 or weaken the main MAP result. It appropriately defines the boundary of what the present evidence proves.

### Atomic-score boundary

The paper reports that the atomic released score has higher AgentProcessBench AP (0.863 versus AgentProf 0.789) but lower HINTBench and TraceElephant AP (0.411 versus 0.453 and 0.209 versus 0.230). This boundary is scientifically valuable. It prevents the grouping improvement from being misread as universal dominance over every view and reveals that aggregation helps more when problem evidence is distributed or repeated across operations.

The result should not be hidden as “negative.” It is a useful mechanism boundary: AgentProf changes prioritization through grouping; when the released scalar already gives a highly accurate atomic ordering, grouping need not dominate. The paper states this without surrendering the profiling thesis.

### What RQ2 proves and does not prove

The strongest supported RQ2 statement is:

> Holding each workload's released localization/risk signal fixed, semantic operation-stack aggregation improves trajectory-equal problem ranking relative to matched raw-action grouping on all three evaluated public populations, with the largest gains on HINTBench and TraceElephant.

It does not prove that AgentProf is a stronger content diagnostician than DRIFT, AgentRx, an LLM judge, or benchmark-specific learned models. It does not prove root cause, repair success, or universal human productivity. The current text mostly respects these boundaries.

The strongest alternative explanation remains that the positive result arises from existing released localization signals plus a convenient smoothing/grouping transform, rather than from a general profiling principle. That explanation does not invalidate the matched grouping result, but it motivates a future complementarity test with a fixed strong diagnostic signal or a closest product-style hierarchy. That is a broader next-cycle opportunity, not a Step 0033 rerun requirement.

## Every table and figure: reread audit

### Figure 1: three semantic flame-graph views

The full-width figure demonstrates the model's central affordance: the same 325 real trajectories are displayed under three field/weight choices, with width representing tokens, wall time, or file-operation count. It is conceptually aligned with the paper and helps the reader see that a “profile” is a selectable projection rather than a fixed execution tree.

The current raster labels are small and often truncated; embedded plot titles use the implementation spelling `agentpprof`, while prose uses `AgentProf`. This is a publication-quality weakness, but it predates the scientific content of the new RQ2 analysis and is best handled in a later figure/presentation pass unless necessary for page economy.

### Figure 2: data-flow and algorithm pipeline

The architecture figure is compact and consistent with the text: histories or operation JSONL become uniform operations, fields are derived, stacks are constructed/folded, and profiles are exported. It correctly separates parsing from semantic enrichment and profile export. The paper's current terminology alternates between “field derivation” and “intent attribution” for overlapping functionality; a later terminology pass could use one as the general interface and the other as a specific method.

### RQ1 figure and text

The resource-view evidence covers source lineage, weight conservation, controls, mixed-weight reduction, and multiple selectable measures. The source-lineage and conservation claims are strong engineering invariants. The mixed-weight result remains partly definitional because adding prompt tags necessarily refines groups along prompt categories. The permutation comparison helps show categories are not arbitrary, but it does not independently establish decision utility. RQ2 supplies a separate decision-oriented bridge, but on different public signals. This is a broader RQ1 construct-validity issue rather than a defect in Step 0033.

### Table 1: RQ2 trajectory MAP

The values, query counts, and paired confidence intervals are mutually consistent in the rendered table and surrounding prose. The caption's “complete RQ2 workloads” is the main wording problem because the reported MAP itself is conditional on target-bearing queries. The table otherwise uses an appropriate primary estimand and does not hide the small AgentProcess gain.

### Table 2: rank-hidden reader

All six tasks are shown, and the median summary matches the surrounding prose. Higher work is correctly treated as worse. The paper does not use the reader as proof of human utility. This table gives accessible prioritization evidence without overclaiming.

### Table 3: RQ3 boundary fidelity

The table distinguishes supervised, reference-calibrated, label-free recurrence, and simple controls. Boundary F1 and B3 F1 are standard for boundary detection and partition agreement respectively. The strongest fair default comparison is label-free recurrence (0.680 boundary, 0.786 B3) versus the simple controls (best control boundary 0.645 and B3 0.678); the supervised comparator is clearly labeled and higher at 0.739/0.816. The post-hoc CodeTraceBench calibration is explicitly bounded in prose and limitations.

This table answers whether induced groups resemble human partitions. It does not answer whether those groups improve problem ranking; RQ2 separately addresses that downstream question. Keeping these constructs separate is correct.

### Table 4: construction cost

The table reports complete-workload sizes, medians over three runs, CPU time, wall time, and peak RSS. The largest union has 27,765 operations and completes in 1.17 s with 464.5 MiB peak RSS. The prose correctly calls the slope descriptive and limits the claim to the tested offline range. It is adequate for RQ4; a broad scalability claim would need more independent sizes and hardware.

## Abstract, Introduction, Evaluation, and Conclusion consistency

### Preserved invariants

- The exact thesis is unchanged and repeated consistently.
- The four RQs remain explicit and evaluation is organized by them.
- The three contribution categories remain present.
- RQ2 numerical values in the Introduction match Table 1.
- The evaluation protocol explicitly defines query, items, relevance, AP, MAP, score source, and matched raw-action comparison.
- The pooled AP, Work measures, reader boundary, and atomic-score boundary prevent an inflated universal interpretation.
- The Conclusion remains one sentence and repeats the thesis rather than inventing a new claim.

### Inconsistencies or missed emphasis

The Abstract omits the three-benchmark RQ2 MAP result even though it is the paper's most direct evidence that the profiles correspond to real problems. Instead it devotes substantial result space to RQ3 boundary induction and post-hoc calibration. This under-sells the paper's decision-oriented contribution. It is a writing opportunity, not evidence invalidity. Because the manuscript is already over the technical-page allowance, any abstract change should replace lower-value detail rather than add length.

The Introduction's “three complete public benchmarks with 27,346 labeled steps” wording is too easy to conflate with the target-bearing MAP denominator. The evaluation is clearer, but a paper should not require readers to repair a headline's estimand later.

The limitations section covers RQ1 scope and RQ3 evidence boundaries but does not restate the RQ2 conditional query population or dependency on released workload scores. The RQ2 prose itself does so sufficiently for current scientific reading; adding more limitations prose is not required while page pressure remains.

## Submission-readiness audit

The PDF is anonymous, US letter, unencrypted, and has embedded Type 1 fonts. It has nine rendered pages. Under official recent AAAI main-track precedent, technical content should fit in seven pages and later pages should contain references only.

The current page 8 begins with a continuation of the Related Work paragraph, followed by the one-sentence Conclusion, before the References heading. It is therefore not a seven-technical-page plus reference-only-pages manuscript. This is an objective submission-readiness defect visible in the rendered PDF.

The repair must be a WRITE pass using prose or table economy. It must not shrink the thesis, delete an RQ, remove the new MAP evidence, hide the Work/atomic boundary, or use font/spacing/style tricks. The spill is small enough that concise editing should recover it without scientific loss.

## Ranked findings after full-paper reread

### Current Step 0033 must-fixes

1. **[Blocker, WRITE] Restore AAAI technical-page compliance.** Page 8 contains Related Work and Conclusion technical prose. Pull all non-reference content back onto page 7 through meaning-preserving prose/table economy. Do not change the thesis, RQs, contributions, or result boundaries.
2. **[Major precision issue, WRITE] Make the conditional MAP population unambiguous at every headline use.** The Introduction and Table 1 caption should state that all workload operations were scored while trajectory MAP averages target-bearing trajectories. Avoid “complete workloads/populations” directly modifying MAP without this qualifier.

These are repairable writing/presentation defects. The standard metric, numeric direction, matched baseline, pooled safeguard, Work evidence, and atomic boundary do not require a new experiment.

### Broader next-cycle major opportunities, not Step 0033 blockers

1. **Closest alternative / novelty:** compare or contrast more directly with a current cross-trace product-style hierarchy, NeMo call/workflow profiling, or a strong diagnosis method. A high-value experiment would hold a strong diagnostic score fixed and test whether semantic profiling changes cross-run triage.
2. **RQ1 construct validity:** show a consequential resource-attribution decision that semantic projection improves beyond the partly definitional mixed-weight measure.
3. **Automatic-constructor mechanism:** simplify or ablate the recurrence rule and test a prospectively fixed default on a truly held-out family.
4. **Related-work completeness:** include AgentDiagnose and make the trace-category versus operation-responsibility distinction reviewer-proof.
5. **Publication figures:** improve Figure 1 typography and truncation without adding conceptual layers.

These issues can affect eventual AAAI acceptance, but they are not regressions caused by the Step 0033 metric reanalysis and should not be used to keep rerunning the same RQ2 grouping experiment indefinitely.

## Provisional whole-paper verdict before cycle audit

The paper is **incomplete but scientifically promising**. It has a strong, memorable thesis; a simple central abstraction; a real system; and unusually broad real/public evidence. The Step 0033 trajectory-MAP result materially improves RQ2 because it replaces a less standard aggregate with a standard, trajectory-equal ranking estimand and preserves the operational and atomic boundaries.

The paper is not yet submission-ready because of the rendered page spill and the conditional-population headline ambiguity. Beyond those repairable defects, the largest acceptance risk is not the RQ2 metric but the lack of a closest external comparison that demonstrates what source-linked selectable semantic profiling adds beyond already available cross-trace categorization and agent diagnosis.

## Alternatives considered and next node

I reject the alternatives of replacing MAP, adding a broad metric suite, dropping the AgentProcess result because its gain is small, hiding atomic superiority on that workload, or shrinking the profiling thesis to a grouping technique. The evidence is more credible with those boundaries visible.

The next required node is the cycle audit: read user intent, the complete idea history, all Step 0033 plan/result/review/write artifacts, and the current cycle diff. That audit must determine whether the headline ambiguity and page spill were introduced by this cycle, whether the computation is traceable to the approved plan and raw artifacts, and whether any story/RQ/contribution drift occurred.
