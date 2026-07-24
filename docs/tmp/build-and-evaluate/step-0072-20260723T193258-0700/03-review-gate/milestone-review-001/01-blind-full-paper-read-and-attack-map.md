# Blind Full-Paper Read and Attack Map

**Timestamp:** 2026-07-23T20:03:20-07:00  
**Parent:** `step-0072-20260723T193258-0700/03-review-gate/milestone-review-001`  
**Objective:** Form an unprimed, paper-level review and reject-hypothesis map before reading prior reviews, change summaries, experiment reports, or other `docs/tmp` artifacts.

## Inputs and provenance

I read the complete active paper workspace under `docs/paper/`: the 1,063-line `main.tex`, all claim-bearing tables and the architecture source, the complete 1,275-line bibliography, the reproducibility checklist, citation ledger, README, and the compiled `main.pdf`. I visually inspected a contact sheet of all 12 PDF pages and read the PDF text. I also read `docs/idea-story.md` and `docs/user-instruction.md` from first line to last because they define the authorized thesis, four RQs, and author constraints.

I did **not** inspect `docs/tmp`, prior reviews, author rebuttals, current-cycle reports, change summaries, or Git history before writing this report. The unavoidable context is the review request itself, which names the “updated RQ2 matched-information baseline”; I therefore knew such a change existed but did not know its construction or result beyond what the active paper states. I also read the review skill and its four required rubrics before the paper, as required.

## Method and reviewer context

The target is nominally AAAI 2027 Main Track, while the work makes load-bearing systems and AI/ML claims and is also being judged against an MLSys-style bar. I therefore classify it as **genuinely cross-domain**:

- systems contribution: trace reconstruction, semantic-stack abstraction, conservation, pprof interoperability, and construction cost;
- AI/ML contribution: automatic semantic annotation, recurrence segmentation, task/action classification, problem localization, and benchmark protocols;
- joint contribution: a semantic hierarchy is useful only if automatic structure is faithful and the resulting profile changes a real developer decision under acceptable systems cost.

References loaded before review: `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, and `cross-domain-review.md`. Venue ambiguity remains: AAAI rewards broad AI significance, while the implementation/evaluation reads like an MLSys or systems measurement paper. I apply both bars rather than using venue ambiguity to lower either one.

## Paper-only reconstruction

### Problem, stakes, and challenged belief

The paper argues that production teams accumulate many agent trajectories but lack population-level answers about cost, failure, unsafe effects, and wasted effort. Per-run traces preserve execution occurrence, not a reusable cross-run hierarchy of semantic responsibility. The challenged belief is therefore:

> An agent’s native trace tree and local action identifiers are sufficient organizational structures for understanding recurring responsibility across a population.

This is a real and important problem on its face. The memorable thesis is exactly:

> **Agent observability needs profiling, not only debugging.**

The paper’s stakes are broad and durable: attribute measured resources to recurring work, inspect where problems concentrate, and retain drilldown to source evidence.

### Simple principle

In one plain sentence:

> Treat completed agent trajectories as weighted profiling samples, assign recurring semantic responsibilities over their source evidence, and fold equal responsibility paths across runs.

This is simple, potentially deep, and separable from the artifact name. It predicts that (1) changing the additive measure should change which recurring responsibility dominates without changing attribution boundaries, (2) useful semantic identities should concentrate independently defined problems better than occurrence-local identities, (3) automatic constructors should agree with independently annotated task structure, and (4) profile construction should scale predictably.

### Artifact and causal connection

AgentProf retains an ordered source forest of sessions, prompts, LLM calls, tools, and effects; overlays nested semantic intervals; constructs `agent -> semantic operations -> LLM/tool evidence` stacks; stores raw occurrence identities as labels; and emits one pprof protobuf profile with a selected additive weight. An annotation workspace exposes a small `tag/parent/next` contract to Agent, LLM, and rule-based backends. The mechanism has a clear causal connection to the principle: cross-run identity comes from shared semantic frames, evidence retention comes from source leaves/labels, and conservation comes from keeping additive measures on source nodes while only changing the projection.

The paper calls the ordered source tree, semantic annotations, and weighted pprof stack “three explicit objects.” The authorized project story says operation and operation stack are the only core abstractions. This can be reconciled if the source tree and annotation file are implementation representations, but the current wording makes a possible story-level abstraction expansion visible.

### Claimed contributions and scope

1. A semantic operation-stack model for recurring semantic responsibility over source evidence.
2. AgentProf, a backend-neutral offline profiler that emits pprof-compatible profiles.
3. Evaluation across public localization, structure, labeling, case-study, and construction-cost workloads.

The intended scope is population profiling for quality, safety, and cost across heterogeneous agent traces. The paper disclaims universal attribution-interface superiority, causal interpretation of differential profiles, topology accuracy where no gold hierarchy exists, and inclusion of capture/adaptation/annotation cost in RQ4.

## RQ and claim map

| RQ | Paper-level claim/goal | Main evidence | Blind assessment |
|---|---|---|---|
| **RQ1: Does semantic profiling improve resource attribution?** | Shared semantic paths reunite recurring responsibility, conserve mass, and reveal resource-dependent bottlenecks. | Forty-one private long-horizon sessions; three repeated Git-deployment executions; one hierarchy over 489 focused operations and 4.56M reported tokens; SSH diagnosis is 21.47% of count but 46.15% of tokens. | **Partially answered.** It shows multi-resource attribution capability and a useful case, but no matched alternative attribution interface, independent gold responsibility, or decision outcome establishes “improve.” |
| **RQ2: Does profiler output correspond to real problems?** | Target-blind profiles complement local diagnostics, expose population differences, and correspond to independent problem annotations. | Complete AgentProcessBench/HINTBench/TraceElephant ranking; matched local+semantic vs local+raw-evidence; 440-session AgentRewardBench differential case and expert looping labels. | **Correspondence is answered; semantic advantage is not.** Local+AgentProf clearly improves over Local, but is statistically indistinguishable from information-matched raw action. The case study corresponds to looping but does not beat the fixed chain. |
| **RQ3: How accurately do automatic backends recover operation structure?** | Agent and non-LLM backends recover useful literal identities, partitions, and boundaries. | 405 CodeTraceBench trajectories; 287 OSWorld-Human sessions; Mind2Web, ScienceWorld, AgentBoard, and ASE label tasks. | **Positive but fragmented and development-heavy.** Each metric matches its output construct, and several comparisons are strong. However, no untouched population validates the flagship Agent constructor; multiple unrelated backends/constructs are combined into one broad answer. |
| **RQ4: What is the cost of constructing a semantic profile?** | Fixed-mark profile construction is practical and near-linear. | Four public workloads and union, three timing runs, 27,765 operations, 1.16 s and 465.2 MiB. | **Narrowly answered.** Core construction is fast, but the RQ excludes source adaptation and automatic annotation, likely the dominant end-to-end cost. Memory is high for the evaluated scale and lacks deeper scaling stress. |

All four RQs have explicit answers, but RQ1 and RQ4 use narrower operationalizations than their question wording, and RQ3’s answer is an aggregate over heterogeneous constructs rather than one end-to-end automatic profiling pipeline.

## Initial verdict

**Initial paper-only verdict: Reject / major revision, incomplete-but-promising.**

The paper has a real problem, a memorable thesis, a simple mechanism, substantial implementation, unusually broad public-data use, and two population-level cases. It is not complicated-but-shallow: the principle is coherent and the pprof mapping is elegant. But the current evidence does not yet close the paper’s most important causal chain:

`semantic responsibility -> information beyond matched raw evidence -> better problem localization or developer decision`.

The newly visible matched RQ2 comparison is scientifically honest and important. It also removes the strongest empirical basis for claiming that semantic operation identity, rather than retained evidence plus a local diagnostic score, improves localization. The paper can still defend a larger profiling contribution, but it must show a consequence that specifically requires the semantic hierarchy instead of merely showing that the complete packet works.

## Ranked blind findings

### Blocker B1 — Evidence/evaluation: the matched RQ2 baseline explains away semantic-prefix localization gains

**Claim/location.** Abstract and Introduction say the target-blind declared semantic hierarchy improves MAP over raw action on all three workloads; Conclusion says profiles improve localization MAP over raw action on all three. RQ2’s matched table instead compares Local+AgentProf with Local+Raw+Evidence at `.894/.893`, `.517/.518`, and `.326/.324`, with all paired intervals including zero.

**Failed inference.** The reader cannot infer that recursive semantic responsibility improves target ranking once the baseline receives the same source evidence and local score. The clear gain over Local shows that group-level aggregation adds information, but not that AgentProf’s semantic prefix supplies it.

**Missing evidence.** A downstream task in which hierarchy topology or cross-run shared identity is load-bearing under information parity: matched inspection work, cross-run transfer, aggregate responsibility localization, root-cause triage, or an ablation that preserves all evidence while randomizing/flattening only the semantic ancestry.

**Gate and repair.** `EXPERIMENT_GATE`. Preserve the ambitious claim by testing a decision that raw action plus the same evidence cannot express: cross-run responsibility-level inspection, unseen-family transfer of canonical operations, or hierarchy-conditioned drilldown with matched packet size and scorer. Do not simply shrink RQ2 to “profiles complement local scores.”

### Blocker B2 — Submission readiness: the compiled paper violates the AAAI main-text page limit

**Claim/location.** `docs/paper/README.md` says main content ends on page seven and references occupy pages eight and nine. The current `main.pdf` has 12 pages; visual inspection shows main content through page 10, with the two large case-study figures occupying pages 9 and 10 and references on pages 11–12.

**Failed inference.** This is not a format-ready AAAI submission.

**Gate and repair.** `WRITE_GATE`, after evidence priorities are settled. Preserve the full thesis and four RQs, but compress implementation detail, repeated numeric narration, and fragmented RQ3 evidence; move non-load-bearing protocol detail and secondary backend cells to the supplement. Redesign the two figures into readable, information-dense composites rather than removing the population cases.

### Major M1 — Evidence/evaluation: RQ1 demonstrates capability, not improved attribution

**Claim/location.** “Does semantic profiling improve resource attribution?” is answered using a single repeated task whose width changes under count versus tokens.

**Failed inference.** Any grouped view with two additive measures can reveal different percentages. Conservation and resource-switching establish correctness and usefulness, but not improvement over flat, native-tree, raw-action, or per-session attribution. The hierarchy itself is also produced by the evaluated Agent backend, without independent validation on this private population.

**Gate and repair.** `EXPERIMENT_GATE`. Compare responsibility attribution under information parity against native tree, raw action, and session-local projections on repeated real tasks with an independent resource/problem oracle or a registered developer decision. The existing case should remain as qualitative mechanism evidence.

### Major M2 — Evidence/evaluation: RQ3 lacks independent confirmation of the flagship Agent constructor

**Claim/location.** Automatic Agent A2 is developed and scored on the complete CodeTraceBench development population. The paper explicitly calls it development evidence. OSWorld-Human validates recurrence and supervised boundary methods, not A2.

**Failed inference.** Strong in-population B³ gains do not establish that source-only Agent annotation recovers operation structure on unseen agent/task families. The 5,537-to-1,434 canonicalization is source-only and boundary-preserving, but it does not itself validate semantic name equivalence across sessions.

**Gate and repair.** `EXPERIMENT_GATE`. Freeze A2 instructions, model/version, representation repair, canonicalizer, and all stopping rules; run on a complete untouched human-staged or independently grouped family. Report multiple-run stability and annotation cost. Preserve the broad automatic-backend claim through external confirmation rather than narrowing it.

### Major M3 — Evidence/evaluation: RQ4 excludes the likely dominant end-to-end costs

**Claim/location.** RQ4 asks for semantic-profile construction cost but excludes capture, source adaptation, and automatic annotation. The abstract reports only 1.16 s “after marks are fixed.”

**Failed inference.** A reviewer cannot assess whether automatic semantic profiling is practical. Agent workers or a 27B classifier may dominate time, tokens, hardware, and monetary cost by orders of magnitude. Three timing repetitions over five small natural input sizes are insufficient for predictable scaling and tail behavior.

**Gate and repair.** `EXPERIMENT_GATE`. Retain core timing as an ablation, but add complete end-to-end latency/resource/cost for at least the default automatic Agent path and one non-LLM path, including cold/warm distinction and repeated-query savings. Scale to a materially larger public population or explain the maximum realistic corpus size.

### Major M4 — Scientific framing/global logic: the paper’s broad thesis outruns its currently isolated consequences

The thesis spans cost, safety, failure, and wasted work. The strongest isolated quantitative result is structure agreement, while attribution and problem localization do not establish semantic advantage under matched controls. The result section therefore reads as several capable components rather than one end-to-end belief challenge. The repair is not a smaller thesis; it is one decisive cross-domain chain connecting semantic structure to a real population decision under matched information and practical cost.

### Major M5 — Reproducibility: automatic annotation protocols are under-specified

The paper does not identify the Codex Agent model/version, complete fixed instruction, decoding/tool policy, number and independence of runs, merge adjudication, annotation token/time cost, or a durable artifact link. Qwen configurations likewise omit important inference settings. The checklist itself says the number of runs is not stated and several code/parameter items are partial/no.

**Gate and repair.** Mixed `EXPERIMENT_GATE` and `WRITE_GATE`: freeze and disclose exact configurations, prompts, source packets, seeds or determinism conditions, model hashes/versions, run counts, and raw outputs; then summarize them compactly in the paper/supplement.

### Major M6 — Global consistency: headline claims do not foreground the matched negative result

The abstract and conclusion retain the older “improves over raw action on all three” sentence, while the main RQ2 text correctly states no matched semantic-prefix advantage. The two statements refer to different baselines, but a reviewer will reasonably read the headline as the stronger information-matched claim. The abstract’s sentence about “Canonical renaming alone improves HINT” is also difficult to connect to the RQ2 table and distracts from the actual matched conclusion.

**Gate and repair.** `WRITE_GATE` after the next experiment. Name the baseline precisely in every headline and state what semantic ancestry contributes beyond matched evidence if the new evidence supports it.

### Minor findings

- **Mechanism/measurement:** Raw-action grouping has no boundary F1 in the CodeTrace table even though an adjacent action-change boundary appears computable. Explain the construct mismatch or report it.
- **Statistics:** Bootstrap design is described but not justified against accepted benchmark protocols; multiple workloads/backends and development choices create multiplicity/selection concerns.
- **Population validity:** CodeTraceBench includes failed trajectories only; stage agreement may not transfer to successful behavior or non-coding agents.
- **Case-study dependence:** AgentReward sessions are reused across 338 pairs, yielding 7,366 bad vs 3,780 good occurrences. Task-clustered uncertainty helps the looping test, but descriptive flame widths remain pair-occurrence weighted and can visually overrepresent tasks with many combinations.
- **Terminology:** `operation`, semantic operation, annotation leaf, action, evidence frame, and group are mostly distinguishable but impose substantial load. “Backend-neutral recursive annotation workspace” and “semantic operation stack model” are enough; “three explicit objects” can be demoted to implementation representation.
- **Naming:** Figure 2’s caption says `AgentPProf` while the paper and macro say `AgentProf`.
- **Privacy/ethics:** Local agent histories can contain prompts, source code, credentials, and system effects. The paper lacks a privacy/security/data-handling discussion.
- **Artifact scale:** 465.2 MiB RSS for only 27,765 operations is high even if runtime is fast; practical corpus scale is not established.
- **Checklist consistency:** Private real-agent sessions are not described enough to reproduce RQ1, yet the checklist says existing datasets are publicly available and only marks unavailable-data description as partial.

## Claim-bearing figures and tables

- **Figure 1** clearly communicates the workspace contract but does not show the key variable-depth semantic path or conservation invariant. It is architecture-correct but scientifically weak.
- **Figure 2** contains the strongest RQ1 qualitative evidence and shows variable-depth paths, but three full-width flamegraphs are too small for easy reading in the PDF and consume a full page.
- **Figure 3** is the strongest RQ2 population view and correctly labels differences as non-causal. It also consumes nearly a full page and needs a clearer direct mapping from visible frames to the quantitative looping test.
- **Table 1** is the most important scientific table because it contains the matched RQ2 baseline. Its interpretation should dominate the next cycle.
- **Tables 2–4** are useful but currently create a collection-of-benchmarks effect: automatic Agent stages, recurrence boundaries, literal classifiers, and construction cost are not tied together as one end-to-end system claim.

## Load-bearing external verification questions

1. Do current observability tools such as Datadog Patterns and LangSmith Insights already build recursive cross-trace semantic hierarchies with metric rollups close enough to weaken novelty?
2. Do TraceProbe, Graphectory, Hodoscope, TraceGraph, WebGraphEval, and recent localization benchmarks already provide the same-claim cross-run structure or decision consequence?
3. What exact hierarchy/annotations do CodeTraceBench and OSWorld-Human provide, and do B³/boundary F1 validly measure the paper’s claimed semantic responsibility?
4. Are AgentProcessBench, HINTBench, and TraceElephant localizer outputs and target semantics suitable for MAP, and does the paper’s “local score” use comparable information across all workloads?
5. Is pprof capable of the labels, signed samples, filtering, trace linkage, and pseudo-frame behaviors claimed?
6. What evaluation protocols do current agent observability/trajectory-diagnosis papers use for matched information, inspection work, human utility, stability, and cost?
7. Does AAAI-27 officially permit only seven pages of main text plus two references pages, and does the current PDF violate it?
8. What stronger public repeated-task or human-structured datasets can independently test the frozen A2 constructor and end-to-end profiling decision?

## Alternatives and decision

The strongest alternative explanation is:

> The observed localization value comes from adding source evidence, aggregation, and a fixed local diagnostic—not from recursive semantic responsibility.

A second alternative is that automatic stage agreement reflects benchmark-specific segmentation conventions rather than a reusable profiling hierarchy. A third is that attractive flamegraphs are explanatory visualizations of labels produced by a powerful annotator, while the profiling abstraction itself adds little beyond grouping and rollup already available in observability products.

The largest plausible claim worth defending remains ambitious:

> A fixed semantic responsibility hierarchy turns heterogeneous agent traces into conserved, source-drillable population profiles that improve real diagnosis and resource attribution beyond information-matched occurrence-local views.

The decisive experiment is a complete, frozen, information-matched population study where the same source evidence and local scores feed (a) semantic responsibility, (b) raw action, (c) native execution, and (d) session-local projections, and a standard or independently validated decision metric measures cross-run diagnosis/attribution. It should include end-to-end annotation cost and untouched-family transfer.

## Tree/search updates

The attack tree opens four load-bearing branches:

1. **Novelty/status-quo branch:** verify whether commercial and academic tools already provide the claimed semantic hierarchy/rollup.
2. **RQ2 causal branch:** verify benchmark constructs and whether matched raw evidence fully explains the result.
3. **RQ3 validity branch:** verify human-stage/group semantics, metrics, and untouched-family expectations.
4. **RQ4 practicality branch:** verify venue expectations for end-to-end cost and realistic scale.

## Project-memory updates

None. This review is read-only and records findings only. It does not change the thesis, four RQs, paper, `docs/idea-story.md`, `docs/user-instruction.md`, or canonical memory.

## Completion assessment, uncertainty, and next node

The blind-read phase is complete. Confidence is high on the internal claim/evidence mismatches and page-count violation; confidence is provisional on novelty, benchmark validity, and expected baselines until primary-source verification.

**Next node:** mandatory external search and primary-source verification, followed by a complete paper reread.
