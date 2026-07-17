# Step 0033 Milestone Review 001 — Blind Full-Paper Read and Attack Map

**Timestamp:** 2026-07-16T17:20:25-07:00
**Parent node:** Step 0033, `REVIEW_GATE`, milestone review 001
**Objective:** Form an independent, paper-only AAAI 2027 review and reject-hypothesis map before consulting author intent, research history, experiment reports, prior reviews, or cycle diffs.

## Inputs and provenance

I read the complete reader-facing paper at `docs/paper/main.tex`, the rendered `docs/paper/main.pdf`, and the complete bibliography in `docs/paper/references.bib`. I inspected every reader-facing section, every table, the architecture source, and the four available result/flame-graph images. The rendered artifact is a nine-page, US-letter, anonymous AAAI-style PDF generated at 2026-07-16 17:17 PDT. I also loaded the review rubric's research-taste, systems, AI/ML, and cross-domain references.

I deliberately did **not** read `docs/user-instruction.md`, `docs/idea-story.md`, Step 0033 plans/results/reviews, prior milestone reviews, or cycle diffs before writing this report. Unavoidable contamination remains: the parent task identified the venue as AAAI 2027, called the contribution cross-domain, and explicitly asked the reviewer to check the new trajectory-MAP presentation, conditional query population, pooled AP, retained Work measures, atomic boundary, and story preservation. I therefore knew which RQ2 details were newly salient, although I did not know their internal provenance or intended defense.

## Review routing and method

The paper makes load-bearing claims in both systems and AI-agent evaluation. I classify it as **genuinely cross-domain, systems-led**: the artifact and abstraction are profiling-system contributions, while the claimed usefulness depends on semantic inference, trajectory grouping, agent-failure localization, and AI-benchmark protocols. I therefore apply both bars rather than selecting the easier one. The apparent target is AAAI 2027; venue-rule verification is deferred to the mandatory external-search phase.

The blind review used four passes over the paper-only artifact:

1. reconstruct the one-sentence principle, challenged belief, mechanism, and causal chain;
2. map the four RQs to claims, constructs, data, baselines, and stated answers;
3. attack novelty, construct validity, causal attribution, generality, and submission presentation;
4. identify load-bearing claims and protocols requiring primary-source verification.

## Paper-only reconstruction

### Problem, stakes, and challenged belief

The paper argues that agent observability has over-indexed on per-run traces and debugging, whereas teams accumulating many trajectories need population-level attribution: which intents consume resources, which workflow categories concentrate failures, and which behavioral patterns produce system effects. The challenged belief is that an execution/span hierarchy is the natural organizing structure for agent observability. The proposed alternative is profiling: select responsibility fields at query time, project heterogeneous activities into an additive hierarchy, and fold recurring responsibility across runs.

The stakes are real if the system can connect semantic intent to additive effects and if the resulting profile materially improves a developer's prioritization decisions. The paper is strongest when it treats profiling as a reusable *method* rather than as a particular visualization.

### Simple principle and mechanism

The durable principle is:

> Agent histories should be aggregated by semantic responsibility, using selectable additive projections, rather than being confined to execution-local trace trees.

The mechanism has two core abstractions and two pluggable algorithms:

- an **operation** is a uniform weighted record spanning prompts, LLM calls, tool events, and source-linked system effects;
- an **operation stack** is an ordered query-time projection of fields whose identical sequences fold with additive weight conservation;
- **intent attribution** derives stable categorical fields through rules, local models, clustering, or source mappings;
- **stack construction** optionally segments visible action sequences using recurrence learned from reference sessions.

The abstraction itself is simple and memorable. The default automatic boundary mechanism is less obviously principled: NPMI, occurrence-weighted one-dimensional two-means, a second cross-action cutoff, and a monotone minimum rule form a multi-part heuristic. The paper states the procedure precisely, but does not yet explain why this exact construction follows uniquely from the central insight or which parts are essential.

### Claimed contributions and scope

The introduction claims exactly three contributions: the semantic operation-stack model, the AgentProf system, and an evaluation. The system is an offline Rust CLI of about 9.8K LOC producing pprof, folded-stack, SVG, and JSON output. Its scope is offline local histories and mapped public operation JSONL, with AgentSight recordings passed through an adapter. Capture and live-agent overhead are excluded.

The story remains ambitious: it proposes a missing profiling layer for agent observability rather than a narrow failure-localization model. The evidence spans real Codex/Claude histories, a fixed 20-task cross-layer lineage suite, 15 public trajectory families, three complete public localization workloads, OSWorld-Human group annotations, CodeTraceBench failures, AgentBoard categories, software-engineering action labels, and construction cost.

## RQ and evidence map

| RQ | Paper-level question | Primary construct and evidence | Stated answer | Blind concern |
|---|---|---|---|---|
| RQ1 | Does semantic profiling improve resource attribution? | Source-lineage precision/recall and control rejection on 20 Codex tasks; weight conservation; mixed-weight ablation on 325 real trajectories; multiple weight/projection views | Source-linked folding is high-fidelity and semantic fields produce more separated, multi-resolution resource views | Mixed-weight is defined by the same prompt categories used to group, so it partly establishes representational refinement by construction rather than decision utility. The 20-task join is mainly evidence for the upstream AgentSight path, not the operation-stack abstraction alone. |
| RQ2 | Does profiler output correspond to real problems? | Trajectory-level MAP on AgentProcessBench, HINTBench, TraceElephant; pooled operation AP; Work@80/Work@50; six-task rank-hidden reader | AgentProf beats matched raw action in MAP on all three complete populations and helps group prioritization, while not claiming universal dominance or reduced work | This is the clearest positive decision-oriented evidence, but the result is conditional on target-bearing queries, uses benchmark-specific released localization scores, and has a small AgentProcess gain. The paper needs source verification for the AP/MAP protocol and a clear defense of score/group causality. |
| RQ3 | How accurate are the tags? | Boundary and B3 F1 on OSWorld-Human; post-hoc CodeTraceBench calibration; V-measure on two partition workloads; macro-F1/accuracy for AgentBoard task family and eight software-engineering actions | Target-blind partitions, declared-label assignment, and held-out grouping are supported | One broad RQ combines four different label objects and protocols. Literal phase labels remain untested despite the positive hypothesis naming phase. The default recurrence rule was selected after earlier corpus inspection; the paper properly labels it development evidence, but abstract prominence risks over-reading it as independent confirmation. |
| RQ4 | What is profiling cost? | Three-run medians on four complete public workloads and their union, up to 27,765 operations | Offline construction is practical and predictable over the tested range: 1.17 s, 464.5 MiB, +18.2% time, +1.3% memory over raw action | Adequate for the tested offline scope, but the linear fit over five naturally correlated input sizes is descriptive rather than a scalability study. |

All four RQs are explicit and evaluation subsections are organized by them. Each has an answer, although RQ3's literal-phase component is explicitly outside current evidence. There are no orphan experiments in the reader-facing organization.

## Initial strengths

1. **Large, memorable thesis.** “Agent observability needs profiling, not only debugging” is simple, non-obvious, and potentially durable across tool and model generations.
2. **Useful abstraction boundary.** Uniform operations plus query-time additive stacks separate data representation from view selection. This is easier to reason about than a taxonomy of type-specific trajectory nodes.
3. **Cross-layer relevance.** Source-linked effects connect AI-agent semantics to actual file/process/network behavior, a stronger systems anchor than LLM-only trace dashboards.
4. **Public and real evidence breadth.** The paper does not rely on a toy synthetic benchmark. It uses real local sessions, complete public populations, and multiple annotation types.
5. **Evidence boundaries are often explicit.** The RQ2 text preserves the atomic-score boundary and says the reader result does not prove lower work, human utility, or universal dominance. RQ3 calls recurrence development evidence and the CodeTraceBench calibration post-hoc.
6. **Standard RQ2 ranking construct is legible.** A trajectory is a query, operations are ranked items, and annotated problem operations are relevant. The table reports MAP and paired intervals; pooled operation AP retains the zero-positive workload as a safeguard.
7. **Additive invariants and ordinary tooling matter.** Weight conservation and pprof-compatible output give the proposed profile more than metaphorical similarity to conventional profiling.

## Blind reject-hypothesis / attack map

### A. Major scientific attack: the claimed belief challenge may exceed the demonstrated comparison

The paper says existing tools do not provide the exact bundle of source-linked, additive, selectable, pprof-compatible operation-stack projections. That bundle may be novel, but novelty-by-conjunction is weaker than demonstrating that trace/debugging abstractions fail at an important recurring decision and that profiling fixes it. Current direct baselines are mostly raw action, session, constant/simple boundary controls, or atomic released scores. There is no end-to-end comparison against a current cross-trace product hierarchy, an agent-diagnosis method, or a strong learned grouping/ranking baseline. If primary sources show that LangSmith Insights, Datadog Patterns, NeMo profiling, or agent-diagnosis systems already aggregate recurring behaviors and costs, the paper must sharpen the *scientific distinction* without shrinking the thesis.

Routing if verified: likely a next-cycle **EXPERIMENT_GATE** for a stronger external or method baseline, plus a small **WRITE_GATE** related-work clarification. It should not default to a smaller claim.

### B. Major evidence attack: RQ1's mixed-weight result is partly construct-by-definition

The prompt-tag view reduces groups that contain multiple prompt-tag categories; since the projection itself includes the prompt tag, lower mixing is an expected mathematical consequence of partition refinement. The permutation test says the observed categories are not random, but does not show that the separation helps find cost, risk, or failures. Multi-weight rank differences and the flame graphs are descriptive. RQ2 provides decision evidence, but uses different public labels and ranking signals. A reviewer may conclude that RQ1 proves fidelity and expressiveness, not “improved attribution” in a task-valid sense.

Routing: potentially **WRITE_GATE** if the intended RQ1 answer is fidelity plus resolution; **EXPERIMENT_GATE** if the paper wants the stronger claim that attribution improves developer decisions across source-linked effects.

### C. Major mechanism/evidence attack: automatic construction looks post-hoc and heuristic

The default recurrence inducer combines NPMI, two one-dimensional clusters, two cutoffs, and a special minimum rule. The paper gives one development corpus and a post-hoc calibration corpus, but not a component ablation, robustness analysis, or cross-family prospective test of the final default. The supervised comparator uses annotations unavailable to the default. This weakens the claim that automatic stack construction is a principled general mechanism, even though the operation-stack model itself does not depend on it.

Routing: **EXPERIMENT_GATE** for mechanism-isolating ablation and a genuinely held-out family or prospectively fixed evaluation; preserve the large profiling story.

### D. Major presentation/evidence consistency issue: the abstract omits the new direct RQ2 answer

The abstract foregrounds RQ1, OSWorld/CodeTraceBench RQ3, and cost, but not the three-benchmark trajectory MAP that most directly answers whether profiles correspond to real problems. The introduction does include MAP. For a nine-page AAAI paper, this omission makes the abstract emphasize boundary construction while under-selling the clearest downstream usefulness evidence. This is a writing-only issue if the MAP protocol survives verification.

Routing: **WRITE_GATE**.

### E. Major baseline/protocol question: what exactly earns the RQ2 gains?

The main comparison changes grouping while holding benchmark-specific scalar signals fixed. That is a sound matched comparison, but it means AgentProf's benefit is redistribution of an existing risk/localization signal, not independent problem detection. AgentProcess's atomic score is substantially higher than AgentProf MAP (0.863 versus 0.789), while AgentProf is higher on HINT and TraceElephant. This is an informative boundary, yet it also invites the question: when should aggregation help, and what mechanism predicts those regimes? The current paper reports the boundary but offers little causal explanation.

Routing: at minimum **WRITE_GATE** for a cross-benchmark mechanism explanation; potentially **EXPERIMENT_GATE** for a stratified analysis tied to a pre-specified prediction.

### F. Major novelty risk: adjacent agent observability/profiling work may already cover population grouping

The bibliography itself lists current product hierarchies, NeMo's agent workflow profiler, agent observability standards, and failure-localization systems. Related Work occupies only three compact paragraphs and asserts differences at bundle level. External verification is required before deciding whether the model is a new abstraction, an engineering unification, or a pprof export layer over existing trace attributes.

Routing: current review **external search**, with a possible next-cycle `research-literature-novelty` map if the branch is crowded.

### G. Minor-to-major AI evaluation concern: heterogeneous RQ3 constructs are aggregated under “tag accuracy”

Boundary partitions, unsupervised cluster V-measure, declared-family classification, literal action classification, and untested phase labels are not one accuracy construct. The paper is careful locally, but the positive hypothesis names task, phase, action, and boundaries together. Readers may remember the broad hypothesis rather than its heterogeneous support and explicit phase gap. This is not a reason to remove RQ3 or narrow the four-RQ story; it is a reason to make the evidence-object map more explicit.

Routing: **WRITE_GATE**, unless a direct literal-phase evaluation is strategically valuable.

### H. Minor submission-readiness concerns

- The main flame-graph figure visually demonstrates selectable views, but many labels are truncated and the embedded titles say `agentpprof`, not the paper's `AgentProf`; it resembles raw tool output more than a publication figure.
- Figure 1 consumes a full wide band on page 2 while the paper lacks a compact end-to-end quantitative overview figure.
- The “Evaluation” item in the contribution list is evidence volume rather than a scientific contribution; the two conceptual contributions are clearer.
- The limitations section covers RQ1 and RQ3 boundaries but does not explicitly restate RQ2's target-bearing-query condition and benchmark-signal dependence.
- The paper uses a single hardware point and three timing repetitions; acceptable for current offline-scope wording, but not for a broad scalability claim.

## Load-bearing external-verification checklist

The next phase must verify the following from primary or official sources:

1. whether non-interpolated AP per target-bearing query and arithmetic-mean MAP are a standard and correctly described ranking protocol, including tie behavior and zero-relevant-query handling;
2. whether pooled operation AP is a scientifically meaningful safeguard for the excluded zero-positive trajectories;
3. what HINTBench, TraceElephant, and AgentProcessBench officially label, and whether AgentProf's query/item/relevance mapping preserves their constructs;
4. whether LangSmith Insights and Datadog Patterns already create cross-trace semantic hierarchies and aggregate cost/evaluation values;
5. whether NeMo Agent Toolkit's profiler already performs population-level workflow/resource aggregation and how its hierarchy differs;
6. whether AgentRx, TELBench/DRIFT, AgentTelemetry, CodeTracer, AgentAtlas, TrajAD, or adjacent diagnosis work provides a stronger expected localization baseline or challenges the “debugging only” premise;
7. current AAAI 2027 page, anonymity, reproducibility, and citation rules;
8. whether NPMI and B3 are accurately cited and applied to the claimed constructs.

## Paper/claim impact

The paper-only evidence supports an **incomplete-but-promising** assessment, not a rejection of the central direction. The simple abstraction and large thesis are stronger than the particular automatic constructor. The most credible current paper-level claim is that selectable semantic projections over additive, source-linked operations form a useful profiling layer and improve matched raw-action problem ranking on three public populations. The largest defensible future claim is that population-level semantic responsibility is a general observability abstraction that exposes recurring cost and failure concentrations missed by execution-local trees. Credibility of that larger claim requires a stronger direct comparison to existing cross-trace/diagnosis alternatives and a clearer mechanism explanation for when grouping improves decisions.

The strongest alternative explanation is that the gains come from benchmark-specific scalar localization signals plus a convenient semantic grouping transform, not from a general new profiling principle. External search and rereading must attack that explanation directly.

## Alternatives and decision

I do not recommend shrinking the thesis, deleting RQ2, or replacing the profiling story with a narrow grouping paper. The current decision is to keep the attack map open and proceed to mandatory external search. A likely high-value repair path is to strengthen the causal/evaluative bridge from additive semantic profiles to developer decisions, while simplifying rather than adding terminology.

Terms that may be mergeable without losing explanatory power are “intent attribution” and “field derivation” when they refer to the same interface, and “semantic operation stack model” versus ordinary “operation-stack projection” in some explanatory passages. The two core abstractions themselves should remain distinct.

## Tree, search, and memory implications

- **Search branch 1:** standard ranking protocol and zero-positive handling.
- **Search branch 2:** current cross-trace product hierarchies and workflow profilers.
- **Search branch 3:** agent failure localization and diagnosis baselines.
- **Search branch 4:** evidence that production agent teams need cross-run profiling rather than only tracing.
- **Search branch 5:** AAAI 2027 formal readiness.
- **Potential future experiment branch:** matched comparison or stratified mechanism analysis explaining when semantic aggregation beats atomic/raw views.

No project-memory update is authorized during this read-only review. The final cycle audit should decide whether any repeated workflow issue warrants a root-agent proposal.

## Completion assessment, uncertainty, and next node

**Blind-read completion:** complete. The full paper, rendered layout, figures/tables, and bibliography were reviewed without consulting internal cycle documents.
**Initial paper-only verdict:** promising cross-domain paper with a strong principle and broad real evidence, but with major open questions about closest-work distinction, RQ1 construct validity, automatic-constructor generality, and the causal interpretation of RQ2 gains.
**Uncertainty:** novelty and protocol judgments remain provisional until primary-source verification; the parent-task contamination makes the RQ2 inspection less blind than ideal.
**Next node:** external search and primary-source verification, followed only then by a complete full-paper reread.
