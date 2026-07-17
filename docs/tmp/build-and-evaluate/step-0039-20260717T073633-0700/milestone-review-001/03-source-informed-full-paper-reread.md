# Milestone Review 001 — Source-Informed Full-Paper Reread

## Node identity

- **Timestamp:** 2026-07-17T07:51:42-0700
- **Parents:** `01-blind-full-paper-read.md` and `02-external-search-primary-source-verification.md`
- **Gate:** REVIEW
- **Venue:** AAAI-27 Main Technical Track
- **Mutation policy:** paper and submodule remained read-only
- **Decision status:** provisional until the independent whole-paper review returns

## Objective

Reread the complete paper after current closest-work verification, compare it against the permanent original story and explicit user instructions, determine which of the blind-review objections survive, and identify the smallest next action that can change the AAAI verdict without changing the thesis, four RQs, contribution scope, or operation-stack model.

## Story and intent audit

The reread compared `docs/paper/main.tex`, the rendered PDF, the complete `docs/idea-story.md`, `docs/user-instruction.md`, and the read-only submodule story.

The current paper preserves all load-bearing invariants:

- exact thesis: **“Agent observability needs profiling, not only debugging.”**
- exactly four RQs in the original order: attribution, problem localization, tag accuracy, and profiling cost;
- exactly two core model objects: operation and operation stack;
- original problem scale: many heterogeneous runs, recurring responsibility, multiple additive measures, and developer questions about cost, failure, safety, and wasted work;
- tracing and profiling are complementary; the paper does not replace the story with a hierarchy-selection paper;
- the submodule remains the story authority and has not been modified.

The current manuscript differs from the original submodule where it should: unsupported historical numbers have been replaced by complete current experiments, the automatic constructor is now cross-session recurrence rather than the old score mixture, and the paper uses the official AAAI-27 format. These are evidence and mechanism corrections, not a new story.

No thesis drift is present in the abstract, introduction, design requirements, contribution list, RQ headings, or conclusion.

## Source-informed thesis assessment

The external search makes the field substantially more crowded than the current three-paragraph related work suggests. Semantic grouping, cross-run categories, cost/error rollups, canonical actions, process profiles, and even trajectory-guided repair all have direct precedents. This removes weak component-level novelty arguments.

It does **not** invalidate the thesis. The paper's strongest defensible contribution is the composite semantic responsibility profile:

1. one fielded operation model spans high-level agent events and source-linked low-level effects;
2. every admitted operation carries conserved additive measures;
3. a selected field order constructs a query-time responsibility stack without runtime nesting;
4. the same corpus can be projected by task, phase, action, session, effect, or resource measure;
5. the result is consumable by standard profiler tooling;
6. independent benchmark targets show that semantic organization can improve problem ranking.

No verified closest source implements and evaluates that whole combination. This is still a simple, non-obvious, durable idea. The paper should defend the whole combination directly rather than imply novelty for any individual ingredient.

## RQ-by-RQ reread

### RQ1 — Does semantic profiling improve resource attribution?

**Current answer: positive within declared scope.**

The 20-task capture suite establishes scoped precision/recall against concurrent controls and lossless passage into AgentProf. The 405-trajectory CodeTraceBench analysis establishes that semantic stage-aligned partitions match independently annotated units of work better than raw action identity, with positive secondary token-weighted directions under all three allocations. Multiple profile measures on the same 325 trajectories expose different bottlenecks.

The main caveat is construct wording: ordinary B-cubed is a standard partition-agreement metric, not a direct causal attribution error. The paper already states that phase-only is statistically indistinguishable from recurrence and therefore makes the correct model-level inference: semantic stages improve over raw identity, not that recurrence is universally best. No new RQ1 constructor is needed.

The source-informed improvement is explanatory: make “source-linked conserved additive responsibility” visibly distinct from Datadog/LangSmith topic-level metric rollups and OpenTelemetry code-profile correlation. The current experiments already supply the evidence.

### RQ2 — Does profiler output correspond to real problems?

**Current answer: positive against the information-matched raw-action organization, with stronger post-hoc mechanism support.**

Standard per-query AP/MAP is the correct primary metric for ranking multiple independently annotated target operations. AgentProf improves MAP over raw action on all three complete workloads. The local-first analysis is scientifically important because it preserves every strict operation-local diagnostic ordering and only uses semantic recurrence for exact ties; it improves over local-only and semantic-only on all three and over a matched local-plus-raw refinement on HINTBench and TraceElephant.

The paper's current Table 2 exposes only the weaker raw-action comparison. The local-first result remains prose and is explicitly post-hoc. The fixed-reader result, which improves selected-positive recall on 5/6 tasks and precision on 4/6 versus fixed session, is absent from the manuscript. Recall@20%, which improves over raw action on all three complete workloads, is also omitted because it is a project-specific budget protocol rather than the primary standard metric.

Closest work raises the bar: Hodoscope demonstrates real issue discovery and inspection reduction; TraceGraph demonstrates a downstream recovery improvement; LangSmith Engine proposes fixes. AgentProf need not become a repair system, but the reader must see what profiling changes beyond a grouping visualization. The local-first and fixed-reader results already address part of this question and should be considered before authorizing a new experiment.

### RQ3 — How accurate are the tags?

**Current answer: positive for the declared literal and structural constructs.**

The subsection now correctly separates literal task/action labels from permutation-invariant task/phase/group partitions and exact boundaries. Macro-F1/accuracy, V-measure, ordinary B-cubed, and exact boundary F1 are standard or standard-form metrics aligned to those constructs. OSWorld-Human is the strongest integrated result because predicted groups are folded through the actual operation-stack path.

The risk is presentation coherence, not missing metric validity. The subsection spans supervised boundaries, label-free recurrence, reference calibration, TF-IDF/K-Means partitions, and Qwen label classification. These should be presented as validations of the three declared field-derivation modes—rules/mappings, unsupervised structure, and model tagger—rather than as one universal tagger. Adding ARI, NMI, or another metric would not repair this presentation problem.

No additional taxonomy or constructor experiment is admitted by this reread.

### RQ4 — What is the profiling cost?

**Current answer: positive for offline profile construction.**

The complete fixed-input experiment reports median time, peak RSS, throughput, scaling, hardware, and semantic-versus-raw differences. It is sufficient for the stated construction boundary. Capture, source adaptation, and model/rule field generation are explicitly excluded.

The permanent idea history also mentions cached repeated queries. That historical mechanism is not needed to interpret the current RQ4 heading, and the paper does not claim end-to-end tagging or capture overhead. Reopening a cache variant would not change the current AAAI verdict. The scope label should remain precise.

## Metric audit after source reread

The standard-metric objection does not survive:

- AP/MAP is the primary RQ2 ranking metric;
- macro-F1 and accuracy evaluate literal multiclass tags;
- V-measure and ordinary B-cubed evaluate partitions;
- exact adjacent-boundary precision/recall/F1 evaluates structural transitions;
- wall time, throughput, peak RSS, and scale curves evaluate construction cost.

Token-weighted B-cubed and Recall@20% are correctly secondary adaptations/protocols. Their status must remain explicit. There is no scientific reason to replace the current primary metrics or create a composite score.

## Algorithm assessment

AgentProf's core contribution does not require a complicated learning algorithm. The operation-stack model is the scientific abstraction. The current automatic constructor has one understandable principle: transitions that recur coherently across other sessions continue the same operation; weak or unseen transitions create a boundary. NPMI and deterministic two-means instantiate that principle.

The earlier recursive information-gain path was weaker because field purity is not the same property as temporal operation continuity. Adding features, weights, or thresholds would recreate heuristic soup. The current recurrence constructor plus the local-first ranking rule is simpler and better aligned with the paper:

- recurrence proposes reusable structural responsibility;
- operation-local evidence remains authoritative when it is discriminative;
- semantic grouping refines exact local ties;
- additive folding remains independent of both decisions.

This is sufficient algorithmic content for a systems-and-AI abstraction paper if the paper demonstrates significance. Another constructor variant on OSWorld-Human or CodeTraceBench would not improve the verdict.

## Updated reviewer scorecard

| Dimension | Provisional score | Source-informed judgment |
|---|---:|---|
| Problem significance | 7/10 | Population profiling for agents is important and the thesis is memorable. |
| Novelty | 5.5/10 | Component novelty is crowded; the exact cross-layer additive responsibility composite survives. |
| Technical quality | 6/10 | The two-object model and invariants are principled; the automatic constructor is intentionally simple and post-hoc selected. |
| Empirical evidence | 6/10 | Broad real/public populations and standard metrics; strongest consequence and baseline evidence is not yet prominent. |
| Clarity | 7/10 | Compact, coherent thesis and RQ organization; related work and RQ3 synthesis are too compressed. |
| Reproducibility | 7/10 | Versions, populations, protocols, scope, and complete runs are largely explicit. |

**Provisional overall:** 5/10, weak reject / borderline, with a plausible path to weak accept through one focused evidence-and-writing cycle. This is not evidence that the idea should shrink. It means the current paper does not yet force a reviewer to distinguish AgentProf from semantic trace analytics plus a pprof exporter.

## Surviving must-fix issues

1. **Exact novelty boundary must be visible in the paper.** TraceProbe, WebGraphEval, Hodoscope/TraceGraph, process mining, and OpenTelemetry Profiles are too close to omit. The related-work section should compare claims, not expand into a survey.
2. **RQ2's strongest same-signal result must become reviewer-visible.** The local-first versus local-only, semantic-only, and local-plus-raw comparison directly answers the weak-baseline objection. Keeping it only in dense prose makes Table 2 look weaker than the complete evidence.
3. **The profiling decision must be concrete.** The paper should connect the multi-resource flame graph and/or fixed-reader result to one explicit developer choice that per-run tracing does not answer. This may be a WRITE task using existing evidence; a new experiment is conditional, not automatic.
4. **RQ3 must read as validation of pluggable modes, not unrelated mini-results.** One framing sentence and a compact synthesis can solve this without changing results.
5. **Figure 1 needs existing-data callouts.** At print scale it shows the abstraction but not the surprising decision; call out the time-versus-token rank reversal already measured.

## Provisional routing decision

The preferred next transition is **REVIEW → WRITE using existing evidence**, not another constructor or metric experiment. A minimal write cycle can:

1. add the closest current academic/standards boundary;
2. promote the local-first comparison into a compact table or more legible result block;
3. include the existing fixed-reader group-prioritization result only within its measured scope;
4. annotate Figure 1 with the already measured cross-resource rank reversal;
5. preserve the exact thesis, four RQs, original design/background, all verified numbers, and AAAI page limit.

If the independent reviewer concludes that a direct matched decision baseline is still fatal, admit exactly one existing-trajectory experiment rather than a new corpus or algorithm:

> Extend the existing R315 fixed-reader protocol with a matched raw-action packet built from the already tracked six-task/34,539-operation artifacts, keep the same rank-hidden reader and fixed top-three budget, and compare selected-positive precision/recall across semantic, raw-action, and fixed-session views.

That conditional experiment tests one RQ2 hypothesis, reuses real public trajectories and the existing hidden key, changes no RQ or constructor, and directly answers the strongest product-informed objection. It should not be run merely because more experiments look safer; the independent review must show that it changes the accept/reject judgment.

## Uncertainty and next node

The current review is not independent of prior project history. A separate reviewer is now reading the whole paper and external frontier under the explicit cross-domain AAAI rubric. Its must-fix list will determine whether the preferred WRITE route is sufficient or whether the matched existing-trajectory reader extension is necessary.

No paper change is authorized until that review returns and the cycle-change audit records the final route.
