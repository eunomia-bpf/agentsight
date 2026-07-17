# Source-informed full-paper review and final verdict

## Node metadata

- **Started:** 2026-07-17 15:47:00 -07:00
- **Completed:** 2026-07-17 16:15:00 -07:00
- **Parent:** REVIEW gate, step 0044
- **Inputs:** complete `docs/paper/main.pdf`, complete `docs/paper/main.tex`, the primary sources recorded in `external-search.md`, and narrowly scoped current evaluation artifacts used only to resolve metric and baseline questions.
- **Venue/domain routing:** AAAI-27 Main Technical Track; cross-domain AI-agent measurement and systems observability.
- **Mode:** independent read-only whole-paper review. No paper edits, canonical-document edits, skill edits, or Git operations.
- **Required invariants:** preserve the exact thesis, **“Agent observability needs profiling, not only debugging.”** Preserve exactly four RQs in this order: attribution, problem correspondence/localization, tag accuracy, and cost. This review does not propose narrowing, replacing, or reordering them.

## Review procedure and independence

I first read the complete nine-page paper without consulting previous review artifacts and wrote `blind-read.md`. I then searched current official documentation and primary research for the closest product, standard, profiling, process-analysis, diagnosis, segmentation, and metric precedents and wrote `external-search.md`. After that search, I reread the complete PDF from abstract through the final reference. Finally, I inspected only the current RQ2 scorer/output and RQ3 scorer needed to resolve two questions raised during review: whether tied scores make AP nonstandard, and what “macro-F1” means operationally. I did not inspect or use hidden author explanations to rescue a claim.

## Executive verdict

**Overall score: 5/10 — Weak Reject, close to the borderline.**
**Confidence: 4/5.**

This is an **incomplete-but-promising** paper with a real, memorable thesis and a simple underlying principle. It is not a shallow feature pile. The central model—turn completed agent activities into weighted operations, derive semantic identity, project selectable stacks, and conservatively fold additive effects across runs—is coherent. RQ2 is already credible, complete-workload evidence using standard MAP. The paper is also unusually transparent about development evidence and cost exclusions.

The present rejection risk is narrower than the blind-read attack: every primitive has prior precedent, and the manuscript omits the closest archival process-centric trajectory paper, so the exact residual novelty is not yet isolated sharply enough for an AAAI reviewer. The evidence also answers different parts of the four RQs with different constructs; the manuscript sometimes lets partition agreement or fixed-input construction carry more conceptual weight than those measurements alone warrant. These are primarily literature and paper-architecture problems, not evidence that the thesis or RQs should be made smaller.

I would not demand another benchmark by default. A careful literature/argument repair plus use of already-computed standard-metric comparisons could move this paper upward. A new experiment is acceptance-changing only under the narrow condition identified below.

## Reconstructed contribution after the second full read

### The challenged belief

The paper challenges the assumption that an execution/span tree and per-run debugging interface provide the right stable hierarchy for an accumulated population of agent histories. Natural-language intent and agent actions do not have stable code identities, and downstream file/process/network effects may not appear inside a runtime trace hierarchy.

### The durable principle

The paper's strongest principle is:

> Completed agent activities should be treated as weighted records whose semantic responsibility fields can be projected into different profiling stacks and folded across runs while conserving additive effects.

This statement is simple, non-obvious, and broader than the current implementation. It preserves the exact thesis **“Agent observability needs profiling, not only debugging.”**

### What is technically implemented

AgentProf provides a pipeline from heterogeneous source histories to uniform operations, pluggable field derivation, direct field projection or recurrence-based stack construction, conservative folding, and pprof/folded-stack/JSON output. The formal view `(predicate, stack, weight)` is a useful interface: it makes selection, identity, hierarchy, and measure explicit and allows the same operation corpus to answer different questions without inventing a single universal semantic tree.

The algorithmic novelty should not rest on NPMI, one-dimensional clustering, pprof export, or tag-to-frame promotion individually. The potentially novel result is their integration with cross-layer effects and arbitrary additive-measure conservation to enable multiple query-selected population profiles over heterogeneous agent histories.

## AAAI-27 criteria

| Criterion | Assessment | Reason |
|---|---:|---|
| Significance | 7/10 | The population-level observability problem is timely and general. The thesis challenges a real default and could influence how agent histories are analyzed. |
| Novelty | 5/10 | I found no verified prior source with the full combination, but all primitives have strong precedents and the closest archival process-centric work is missing. The paper currently asks the reviewer to infer the residual conjunction. |
| Technical soundness | 6/10 | The operation model, additive conservation, and standard scoring are coherent. Recurrence is a heuristic with development-corpus influence, and the four RQs mix constructs that require careful separation. |
| Empirical support | 6/10 | Complete public RQ2 populations, real cross-layer capture, several public RQ3 protocols, and full cost runs are meaningful. RQ1 resource attribution and RQ4 end-to-end cost remain only partially represented by their current measurements. |
| Clarity | 7/10 | The paper is well organized, visually readable, candid about scope, and explicit about four RQs. The novelty comparison and the meaning of “tag accuracy” remain diffuse. |
| AAAI relevance | 8/10 | It bridges AI agents, evaluation, observability, and systems measurement. AAAI-27 explicitly welcomes integrative cross-field work, so a systems-style artifact is not a relevance problem. |

## Main strengths

1. **A memorable thesis and a simple model.** “Agent observability needs profiling, not only debugging” is a stronger contribution direction than yet another diagnostic dashboard. The selected-stack view explains why there is no single authoritative semantic hierarchy.

2. **A technically clean accounting invariant.** Every additive weight is attached to an operation and conserved during folding. This gives tokens, time, files, process cost, failures, or other additive measures the same algebraic treatment.

3. **A useful separation between fields and views.** Field derivation can improve independently of the profiling model. A user can select different field orders and weights over the same records, which is more principled than hard-coding one universal tree.

4. **RQ2 is already substantive.** The primary comparison scores all target-bearing queries on three complete released workloads using standard per-query AP and workload MAP. Semantic grouping improves over matched raw-action grouping on all three; the local-first analysis correctly positions grouping as a refinement of operation-local evidence rather than a replacement.

5. **Standard metrics, not bespoke success measures.** The current paper uses ordinary B³, AP/MAP, macro-F1 and accuracy, V-measure, exact boundary precision/recall/F1, elapsed time, throughput, and peak RSS. It does not contain token-weighted B³, Recall@20%, a fixed top-3 reader protocol, or a model-reader metric.

6. **Honest limitations.** The paper marks development/post-hoc evidence, declares the process/tool capture scope, and says exactly what RQ4 excludes. That candor improves credibility.

## Main weaknesses and required repairs

### Major 1 — The closest archival neighbor is omitted

**Category:** novelty/literature; **route:** WRITE plus literature update; **new experiment:** no.

The paper must cite and directly distinguish *Process-Centric Analysis of Agentic Software Systems* (Graphectory), OOPSLA 2026, DOI 10.1145/3798271. It builds temporal/semantic graphs over 4,000 SWE-agent and OpenHands trajectories, derives process metrics and shared phase strategies, exposes inefficiencies, and supports online analysis. This is closer than a generic tracing or product-dashboard citation because it also transfers classical software structure to stochastic agent trajectories and analyzes populations of runs.

The distinction is still defensible: Graphectory does not establish source-linked OS effects, arbitrary additive-measure conservation, pprof-compatible output, or multiple query-selected field stacks over one operation corpus. But a top-venue reviewer should not have to discover that distinction independently.

### Major 2 — The residual novelty is distributed instead of falsifiable

**Category:** novelty/global logic; **route:** WRITE; **new experiment:** normally no.

Official LangSmith Insights and Datadog Patterns already derive hierarchical cross-trace categories and roll up error, latency, cost, feedback, token, and evaluation signals. NeMo Agent Toolkit already calls its instrumented workflow analysis a profiler. pprof already promotes tags to pseudo-frames and reports additive values. OpenTelemetry Profiles already links profiles to traces/spans. WebGraphEval and Graphectory already build cross-run recurring structures.

AgentProf therefore should not rely on any one of these primitives as its novelty. The paper should make the residual capability comparison explicit and name-free:

> Over one heterogeneous operation corpus, can a system join agent actions to downstream effects, conserve arbitrary additive measures, and expose multiple query-selected semantic stack projections without assuming a runtime call hierarchy?

That conjunction is not a retreat. It is the large paper claim expressed as a testable capability instead of a feature list. The manuscript already contains all components, but the comparison is scattered among the introduction, formal model, related work, and evaluation synthesis.

### Major 3 — RQ1 combines three constructs that should not substitute for one another

**Category:** evidence-to-claim alignment; **route:** WRITE first; **new experiment:** not required by this review.

RQ1 asks about resource attribution. Its evidence has three distinct roles:

- the 20-task controlled capture measures whether effects are joined to the right task under the declared scope;
- conservation checks show that folding does not lose or duplicate attributed weight; and
- human-stage B³ measures agreement between a semantic partition and human stage intervals.

All three are relevant, but B³ is a partition metric, not a direct measure that resource responsibility is correct. The paper partly acknowledges this; the synthesis should make the separation impossible to miss. This is a claim-architecture repair, not a reason to replace RQ1, weaken the thesis, or invent a custom resource metric.

### Major 4 — RQ3 is a family of scoped accuracy results, not one interchangeable property

**Category:** evaluation/global logic; **route:** WRITE; **new experiment:** no automatic requirement.

Literal task labels, literal action labels, task partitions, phase partitions, recurring groups, and adjacent boundaries are different output types with different information boundaries. The paper uses appropriate standard metrics for each, but the heading “How accurate are the tags?” can cause readers to treat them as one production-path accuracy number.

The answer should remain large: AgentProf supports a pluggable semantic field and group-construction interface across all these protocols. The writing should explicitly distinguish literal-label accuracy, partition agreement, and boundary recovery, then state what each result licenses. The 0.498 action macro-F1 is bounded evidence for one adapter, while ordinary B³ of 0.680/0.786 is structural evidence for label-free recurrence; neither is a universal tag-accuracy claim.

### Major 5 — RQ4 answers fixed-input construction cost, not the whole pipeline

**Category:** evidence scope; **route:** WRITE/claim consistency; **new experiment:** not currently acceptance-changing.

The paper reports 1.17 seconds and 464.5 MiB for 27,765 fixed-field operations, with 18.2% time and 1.3% RSS overhead versus raw-action grouping. This is a valid and useful measurement, but it excludes capture, source adaptation, and field/tag generation. The manuscript discloses these exclusions consistently in RQ4 and limitations; the abstract/conclusion should continue to describe the number as profile-construction cost rather than end-to-end agent overhead.

I do not recommend adding an end-to-end run merely for completeness. It would strengthen engineering scope but would not resolve the central novelty question. Preserve RQ4 exactly and keep its answer precise.

### Minor 1 — State the standard metric definitions precisely

**Category:** reproducible reporting; **route:** WRITE; **new experiment:** no.

The current metrics are standard and citable. Two one-sentence definitions would remove avoidable ambiguity:

- RQ2 uses `sklearn.metrics.average_precision_score` per target-bearing trajectory and the arithmetic mean across trajectories. This implementation evaluates tied score thresholds together; the inspected current result records identify scikit-learn 1.4.1.post1. Thus the blind-read tie concern is resolved and no replacement metric is needed.
- RQ3 macro-F1 is the arithmetic mean of the per-class F1 values over the declared class set. The scorer implements exactly that convention.

These are definition/reporting repairs, not requests for code, a new harness, or metric proliferation.

### Minor 2 — Show that existing alternatives were considered without crowding the paper

**Category:** baseline communication; **route:** WRITE or appendix/supplement if space permits; **new experiment:** no.

The current RQ2 artifacts already compute session/flat/source-native and operation-local alternatives on the same trajectories. The paper's table includes the most important operation-local column and matched raw grouping. The remaining alternatives are generally much weaker than semantic grouping; they can be summarized briefly if reviewers might otherwise assume they were omitted. No new benchmark or new scoring protocol is necessary.

## Standard-metric judgment

The user's metric concern is resolved positively for the current paper:

| Paper-facing quantity | Standard status | Fit to construct |
|---|---|---|
| Ordinary operation-level B³ P/R/F1 | Standard and cited | Appropriate for partition agreement; not sufficient alone for resource-attribution correctness. |
| Per-query non-interpolated AP and MAP | Standard and cited | Appropriate for ranking independently annotated target operations early. Current scorer uses a standard tie-aware implementation. |
| Macro-F1 and accuracy | Standard and cited | Appropriate for literal multiclass fields; define macro averaging explicitly. |
| V-measure | Standard and cited | Appropriate when predicted group names are permutation-invariant. |
| Exact boundary P/R/F1 | Standard and cited | Appropriate for adjacent-boundary recovery. |
| Wall time, throughput, peak RSS | Standard systems measurements | Appropriate for the declared fixed-input construction path. |

No paper-facing metric should be replaced with token-weighted B³, Recall@20%, fixed top-k reading, or a model-reader score. Those quantities may be internal diagnostics, but they are absent from this manuscript and are not needed to answer the four RQs.

## Baseline and evidence audit after repository verification

The existing standard-MAP artifact contains the following alternative views on the same complete populations:

| Workload | Semantic | Raw action | Operation-local/atomic | Session | Source-native where available |
|---|---:|---:|---:|---:|---:|
| AgentProcessBench | .789 | .773 | .863 | .448 | n/a |
| HINTBench | .453 | .281 | .411 | .111 | n/a |
| TraceElephant | .230 | .121 | .209 | .059 | .080 |

The paper already reports the operation-local values as “Local” and separately reports local+semantic/local+raw tie refinement. Therefore the strongest readily available alternative is not silently absent. Session and source-native views do not threaten the headline result. This finding reduces, rather than expands, the need for more experimentation.

## Strongest reject and accept arguments

### Skeptical reviewer

The work packages known semantic grouping, pprof tag frames, additive metric aggregation, trace linkage, and recurring cross-run structure into a polished artifact. The recurrence mechanism is development evidence compared mainly with simple controls, the closest archival process-centric paper is missing, RQ1 partly evaluates partition similarity rather than resource responsibility, and the largest cost number excludes the expensive semantic derivation path. The paper is useful, but its irreducible scientific advance is not yet isolated strongly enough.

### Excited reviewer

The paper identifies the wrong abstraction at the heart of agent observability: the runtime tree is neither stable semantic identity nor the only useful population hierarchy. Its `(selection, stack, weight)` view is simple and general, additive conservation makes different resource measures comparable, and complete real benchmark evidence shows semantic organization changes problem ranking. AAAI explicitly accepts integrative contributions, and no prior source combines heterogeneous agent histories, source-linked system effects, arbitrary conserved measures, and multiple query-selected pprof views.

Both readings are reasonable. The revision should make the excited reviewer's capability comparison explicit while answering the skeptical reviewer's closest-work and construct-alignment objections.

## Would a new experiment change acceptance?

**Not by default.** The dominant acceptance blockers are the omitted Graphectory comparison and diffuse isolation of the integrative novelty. Existing RQ2 standard-MAP evidence is already complete and contains strong alternative views. Another dataset, cutoff, fixed-budget metric, smoke run, or bespoke reader protocol would not change my score.

There is only one plausible acceptance-changing experimental branch: if the existing RQ2 trajectories expose an information-matched published phase/process representation that can be evaluated by the same standard MAP scorer without implementing a new product or collecting new data, that comparison could test the strongest low-complexity alternative to learned recurrence. It should be admitted only if such fields already exist naturally and the result can change the paper-level conclusion. Otherwise, close the branch and repair the literature/evidence synthesis.

I do **not** recommend a mandatory RQ4 end-to-end run, a user study, a new benchmark, or reimplementation of LangSmith, Datadog, NeMo, or Graphectory for this submission snapshot.

## Thesis, RQ, and story-integrity audit

- The paper states and supports the exact thesis **“Agent observability needs profiling, not only debugging.”** This review does not replace it with a smaller “recurring behavior” or “better grouping” thesis.
- The paper contains exactly four RQs in the required order: attribution, problem correspondence/localization, tag accuracy, and cost. None should be removed, narrowed, reordered, or converted into a recurrence-only paper.
- The current operation-stack design is consistent with the thesis: execution location, semantic responsibility, and decision-oriented aggregation are different structures, and no one tree is presumed authoritative.
- The review recommendations strengthen the claim by identifying the exact conjunction prior systems do not demonstrate. They do not respond to mixed evidence by shrinking the hypothesis.
- Negative development history need not be narrated in the paper. Scoped limitations and post-hoc labels that affect scientific interpretation should remain, because removing them would make the evidence less credible rather than the story stronger.

## Presentation and completeness

- The architecture figure accurately shows the source-to-operation-to-field/stack-to-profile path.
- Tables are legible and captions explain comparison direction and standard metrics.
- The flame-graph examples support multi-measure projection at an aggregate level, although their internal labels are too small for fine-grained visual evidence.
- The paper is internally consistent on the major reported numbers in this review pass.
- Bibliography coverage is broad for current 2025–2026 work except for the material Graphectory omission.
- The nine-page submission snapshot appears within the AAAI main-text/reference format shape; final format compliance is outside this scientific review.

## Final must-fix list

1. **Cite and distinguish OOPSLA 2026 Graphectory.** This is the only clear current-literature blocker.
2. **State the residual integrative capability in one place** against product hierarchies, NeMo, pprof/OTel, Graphectory, and WebGraphEval; do not claim any individual primitive as new.
3. **Separate the three roles of RQ1 evidence**—effect lineage, additive conservation, and partition agreement—so B³ does not stand in for resource-responsibility correctness.
4. **Separate RQ3 output types and scopes** while preserving the full tag/group/boundary question and standard metrics.
5. **Keep RQ4's 1.17-second claim explicitly fixed-input construction cost** and do not imply it covers capture or tag generation.
6. **Define AP implementation/tie behavior and macro-F1 averaging in one sentence each.** No new metric or experiment is required.

## Gate disposition

**REVIEW result: major revisions required before acceptance confidence.** Route the next work to the WRITE/literature path first. Do not change the thesis, the original four RQs/order, or the operation-stack story. Do not launch another experiment unless the bounded existing-trajectory phase/process-baseline branch is both naturally available and capable of changing the paper-level conclusion.

## Search/tree and project-memory disposition

- **Search tree:** Close metric, product, profiling-foundation, current diagnosis, and general-baseline branches. Retain only the bounded existing-data process/phase-baseline question if the root agent judges it decision-relevant.
- **Project memory:** Record Graphectory as closest archival work and the name-free residual capability comparison. Record that standard metrics pass and no bespoke metric should enter the paper.
- **Skill evolution:** No skill modification is justified by this single review. The review process correctly forced whole-paper reading, external primary-source search, second full read, and construct-versus-metric separation.
- **Completion:** Independent AAAI-27 full-paper REVIEW snapshot complete.
