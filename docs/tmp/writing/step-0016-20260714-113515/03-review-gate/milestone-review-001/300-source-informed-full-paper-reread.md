# Source-Informed Full-Paper Reread: *AgentProf: Semantic Profiling for AI Agents*

## Review-node metadata

- **Phase:** `FULL-PAPER REREAD` after external search and primary-source verification.
- **Started:** 2026-07-14 11:44 PDT.
- **Completed:** 2026-07-14 11:49:32 PDT.
- **Parent:** [200-external-search-and-source-verification.md](200-external-search-and-source-verification.md).
- **Prior blind assessment:** [100-blind-full-paper-read.md](100-blind-full-paper-read.md).
- **Objective:** Reassess the complete paper under source-grounded AAAI, systems, AI/ML, and cross-domain standards; determine the final current state of all four fixed RQs and whether one further experiment is genuinely necessary.
- **Target venue:** AAAI 2027 Main Technical Track.
- **Contribution routing:** cross-domain, systems-primary, with load-bearing AI evaluation and outcome claims.
- **Reviewer references:** `iter-review-critique` plus its research-taste, systems, AI/ML, and cross-domain references.
- **Canonical intent read in full:** `docs/user-instruction.md` and `docs/idea-story.md`.
- **Paper read in full again:** `docs/paper/main.tex`, the complete nine-page `main.pdf`, every included claim-bearing figure, all three result tables, architecture, abstract, introduction, background, design, implementation, four RQ subsections, limitations, related work, conclusion, and rendered references.
- **External evidence read:** the complete 200 report plus the load-bearing primary sources linked below. Recent 2026 arXiv work is treated as preprint evidence, not accepted-venue fact, unless a primary page states acceptance.
- **Prohibited material:** no other `docs/tmp` verdict, experiment proposal, or historical review was read. `docs/evaluation.md` was not read. No Git command was run. Paper, canonical documents, and submodule remained read-only.
- **Writes:** this report only.

## Method and governing constraints

The reread started from the source-informed attack map rather than from a new story. I checked each paper claim against the verified capability boundary, reread every evidence-bearing paragraph and visual, and then audited the result against the author's fixed intent.

The following are constraints, not variables for this review:

1. the thesis remains exactly **“Agent observability needs profiling, not only debugging”**;
2. operations and operation stacks remain the only two core abstractions;
3. the four RQs remain attribution, problem correspondence, tag accuracy, and cost, with their current meaning intact;
4. evidence gaps do not authorize shrinking or replacing the thesis, story, or RQs;
5. if more evidence is required, reuse existing real benchmarks, software, and completed artifacts, and admit exactly one simple complete experiment rather than a new experimental program.

These constraints are compatible with scientific review. They require a stronger test of the original claim rather than a smaller paper.

## Source-grounded principle and challenged belief

The durable principle remains:

> Agent trajectories can be treated as profiling samples: source-linked activities and effects become weighted operations, and query-time operation stacks attribute the same recorded measures to recurring responsibility at the granularity of the decision.

The broad belief “agent observability only has per-run traces and no cross-run semantic aggregation” is not sustainable after source verification. Official [LangSmith Insights](https://docs.langchain.com/langsmith/insights) documentation already describes automatic categories and subcategories across traces with aggregated error, latency, cost, feedback, and extracted attributes. Official [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) documentation describes embedding-based hierarchical topics over production interactions and explicitly recommends scoping them to failed evaluations to prioritize fixes instead of debugging trace by trace.

The actual challenged belief is narrower but still important and fully consistent with the authorized thesis:

> Generic trace/category analytics are sufficient for profiling responsibility even when the consequential evidence spans agent intent, tools, processes, files, networks, and multiple selectable additive measures.

AgentProf may challenge this belief by providing source-linked cross-layer responsibility, conserved measures, and reusable projections over the same evidence. The paper represents that combination, but it has not yet shown the consequential decision that requires it.

## Source-informed provisional AAAI verdict

**Provisional recommendation: 3/10, Reject in the current form (confidence 4/5).** This is not a final cycle verdict and does not authorize a story change.

The problem remains significant, the two-object model remains simple and memorable, and the 20-task lineage result plus exact folding are credible scoped systems evidence. External search weakens the novelty of projection, hierarchy, aggregation, and pprof export in isolation, but it does not show that another system already supplies AgentProf's complete source-linked cross-layer combination. H1 is therefore not fatal.

The rejection turns on H2. AAAI evaluates substantive AI significance and empirical soundness, and its official [AAAI-27 review criteria](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/) prefer work that opens meaningful new territory beyond incremental capability. Once generic category trees and grouped metrics are removed from the novelty claim, the paper must demonstrate what source-linked semantic profiling enables. Current RQ2 primarily groups an already-produced diagnostic signal, and the closest trajectory-analysis work increasingly closes the loop to triage efficiency, attribution, repair, or task outcome. The paper therefore lacks the final causal edge from profile to consequential decision.

The work remains **incomplete-but-promising**, not complicated-but-shallow. It can become simple-but-deep if one outcome test shows that recurring semantic responsibility is a better decision index than direct or execution-local views under equal information and action budgets.

## H1 and H2 after source verification

| Hypothesis | Blind status | Source-informed status | Reason for change | Paper consequence |
|---|---|---|---|---|
| **H1: the core is renamed `GROUP BY`/label promotion** | Blocker candidate. | **Major, not fatal.** Generic projection and hierarchy are not novel; AgentProf's full cross-layer combination remains plausibly distinct. | Official [pprof documentation](https://github.com/google/pprof/blob/main/doc/README.md) confirms sample tags, tag breakdown, and `tagroot`/`tagleaf` pseudo-frames. Official [PerfettoSQL](https://perfetto.dev/docs/analysis/perfetto-sql-getting-started) and [trace-metric](https://perfetto.dev/docs/analysis/metrics) documentation confirms arbitrary event arguments, reusable SQL aggregation, and derived metrics. LangSmith and Datadog already create cross-run semantic hierarchies with aggregate metrics. | Projection, folding, pprof compatibility, and semantic categories cannot carry novelty alone. The paper must center the source-linked intent-to-system-effect responsibility combination and prove a decision that needs it. No thesis or RQ change is required. |
| **H2: RQ2 organizes an external diagnostic signal rather than showing profile decision value** | Blocker candidate. | **Confirmed blocker for AAAI readiness.** | [HINTBench](https://arxiv.org/abs/2604.13954) defines risk-step localization as a benchmark task; its released localization result is already diagnostic inference. [TraceElephant](https://arxiv.org/abs/2604.22708) defines failure attribution as identifying a responsible component and decisive step. AgentProf groups these released outputs, so the system does not produce the load-bearing diagnosis. The paper's own Table 1 is also mixed at the prospective operating points. | RQ2 currently supports target-blind concentration of existing risk evidence, not the strongest claim that a profile improves a real diagnosis, mitigation, optimization, or resource decision. Writing alone cannot close this edge. |

### Closest-work pressure on H2

The closest work does not subsume AgentProf's cross-layer resource model, but it raises the expected consequence bar:

- [Signals](https://arxiv.org/abs/2604.00356) reports a controlled annotation-triage outcome rather than only score concentration.
- [TraceGraph](https://arxiv.org/abs/2605.31308) turns shared cross-trajectory structure into a recovery pipeline and reports official task-outcome change.
- [Agent Mentor](https://arxiv.org/abs/2604.10513) converts recurring semantic trajectory features into corrective instructions and measures later performance.
- [HarnessFix](https://arxiv.org/abs/2606.06324) consolidates recurring trajectory diagnoses into harness repairs and evaluates held-out task outcomes.

These are recent preprints, so they do not automatically defeat novelty. They do make a reviewer demand more than visualization or concentration from a 2027 AAAI submission.

## Final current status of the four fixed RQs

“Final current status” here means the strongest answer supported by the current paper and verified sources. It does not change any RQ.

| Fixed RQ | Current paper evidence | Source-informed current answer | Submission status |
|---|---|---|---|
| **RQ1 — Does semantic profiling improve resource attribution?** | The fixed R114 suite recovers 1,520/1,574 in-scope effects at 100% precision and 96.569% recall, rejects all 1,629 concurrent controls, and AgentProf preserves all 1,520 selected effects and five manifest-category masses. The 325-trajectory ablation shows prompt-tag-conditioned separation, multiple weights, depths, and automatic induction. | **Scoped positive, but only partially answers the broad wording.** Source lineage and mass preservation are strong bounded evidence. Multiple views are real. The 90.4%→36.7% separation is conditional on the same prompt categories used to define mixing, and external sources show that generic tag projection/grouping is established. What remains distinctive is the source-linked cross-layer responsibility combination. | **Partial but not the next blocker.** Preserve the positive scoped answer; do not run another lineage or projection variant now. |
| **RQ2 — Does profiler output correspond to real problems?** | AgentProcessBench AP improves 0.556→0.588 against raw action but loses to session/per-step AP; HINT Work@80 improves descriptively against raw but its paired interval crosses zero; TraceElephant wins at descriptive Work@50 but requires full work at the prospective Work@80 point. All use released judge/localization outputs as the step signal. | **Narrow concentration claim positive; consequential decision claim unanswered.** The profiles sometimes concentrate independently held-out targets, but most diagnostic inference is already in the released signal. The evidence does not show that cross-run semantic profiling improves attribution, validation, remediation, or optimization under an equal action budget. | **Blocker.** This is the only additional experiment justified by current paper-decision value. |
| **RQ3 — How accurate are the tags?** | A pre-specified supervised boundary predictor reaches 0.739 boundary F1 and 0.816 B-cubed partition F1 on session-held-out OSWorld-Human; TF-IDF/K-Means reports task-partition V-measure on nine Mind2Web and 100 ScienceWorld sessions. | **Partial positive.** Boundary and task-partition components have held-out evidence. The result does not evaluate the built-in Rust inducer, the local 3B tags used in RQ1, literal label meaning, phase/action accuracy, or unseen family transfer. No source result removes that internal mechanism/evidence mismatch. | **Partial, but secondary.** A broad tagger matrix would fragment the evidence program and is not justified before RQ2. Keep the exact limitations visible. |
| **RQ4 — What is the profiling cost?** | Current `agentpprof 0.2.37` processes the 27,765-operation union in 1.17 s and 464.5 MiB RSS, with +18.2% time and +1.3% memory over the raw-action path. A predecessor-only eight-session result shows cached reconstruction avoiding repeated model calls. | **Answered for scoped offline construction cost.** The result supports practical, predictable construction over the tested range. It does not establish current-binary cold tag derivation or live capture cost, but the paper explicitly scopes those out and distinguishes predecessor timing. | **Scoped answered.** Clarify end-to-end exclusions in writing; no cost experiment has higher decision value than the RQ2 blocker. |

A full empirical paper ordinarily needs all four RQs answered. RQ1 and RQ4 provide credible bounded answers, RQ3 provides incomplete component evidence, and RQ2 remains the acceptance-determining gap. The paper's current sentence “Together, the complete workloads answer RQ2 positively” is stronger than this evidence state.

## Full-paper causal-chain reassessment

The paper's intended chain remains:

```text
many heterogeneous agent trajectories
→ execution structure is not the only cross-run responsibility index
→ source-linked operations + derived fields + operation stacks
→ conserved, selectable recurring responsibility profiles
→ better quality/safety/cost diagnosis or control
```

The first edge is real and externally grounded by production tools that already invest in cross-trace pattern discovery. The second and third edges are partially supported by the AgentSight lineage suite, AgentProf folding, and heterogeneous mappings. The fourth edge is demonstrated only as organization/concentration of existing signals. The last edge is absent.

This gap cannot be solved by adding another abstraction, hierarchy, ranker, dataset family, operating point, or visualization. It requires one bounded decision and one accepted outcome.

## Strongest source-grounded reject argument

> Existing systems already provide label promotion, arbitrary trace aggregation, and cross-run semantic hierarchies with aggregate metrics; after those established capabilities are removed from the novelty claim, AgentProf's plausible distinction is source-linked cross-layer responsibility. Yet its problem-localization evidence consumes released judge/localization outputs that already encode the diagnosis and shows mixed gains at the prospective operating points. The paper therefore does not demonstrate a new AI-relevant decision enabled by its unique systems mechanism.

The strongest evidence is the conjunction of:

1. official pprof, Perfetto, LangSmith, and Datadog capabilities;
2. HINTBench and TraceElephant's primary definitions of localization/attribution as the benchmark task;
3. Table 1's session/per-step superiority on AgentProcessBench, non-significant HINT raw comparison, and TraceElephant failure at Work@80; and
4. recent trajectory systems that measure triage efficiency, repair, counterfactual validation, or official task outcome.

This is a blocker in **evidence/evaluation and cross-domain causal closure**, not authorization to weaken the thesis.

## Largest scientific gap

The largest scientific gap is **the missing causal connection from the source-linked semantic profile to a consequential, equally budgeted decision**.

The paper shows that fields can be projected, weights conserved, and diagnostic outputs concentrated. It does not show that the recurring semantic responsibility selected by AgentProf is a better place to inspect, replay, validate, repair, optimize, or constrain than the best equally informed direct/execution-local alternative. Without this edge, the systems contribution and AI consequence remain adjacent rather than joint.

## Largest writing-only gap

The largest writing-only gap is **source-informed novelty and claim calibration across the Introduction, RQ2 conclusion, and Related Work**.

- The current Introduction first acknowledges cross-trace hierarchical products and then still contrasts existing tools mainly as per-execution span trees. The precise gap should be the missing source-linked cross-layer responsibility combination, not semantic aggregation itself.
- Related Work cites LangSmith Insights and Datadog Patterns but does not explain how much of hierarchy, metrics, and failure prioritization they already cover.
- The paper omits the closest actionability direction represented by Signals, TraceGraph, Agent Mentor, and HarnessFix.
- The RQ2 conclusion declares a positive complete answer even though the paper itself reports non-significance and a prospective operating-point loss.

These are repairable without changing the thesis, story, two-object model, or four RQs. They are not a substitute for the missing experiment.

## Largest claim the current evidence almost supports

The largest faithful claim worth defending is:

> A single source-linked semantic profile can make recurring agent responsibility accountable across intent, tools, and downstream system effects, preserve additive evidence, and guide the same cross-run diagnosis or resource decision under multiple selectable views.

Current evidence supports source linkage, conservation, selectable views, and partial problem concentration. It almost—but does not yet—support “guide the decision.” This larger claim preserves the original quality, safety, and cost ambition rather than narrowing AgentProf to a pprof exporter or a benchmark ranker.

## Is another experiment genuinely necessary?

**Yes. One experiment is necessary.** A writing-only pass cannot distinguish AgentProf from established semantic grouping or show that a profile improves a consequential decision. RQ2/H2 is a scientific evidence blocker, while additional RQ1, RQ3, or RQ4 variants have lower paper-decision value.

### The single admitted experiment: one-probe TraceElephant counterfactual attribution

Reuse the existing complete TraceElephant mapping, all 220 failed traces, the current frozen AgentProf fields/profile/ranker, the already used released localization signal, and TraceElephant's official runnable environments. Do not introduce a new dataset, model, tagger, hierarchy, ranker, cutoff, or scoring framework.

For each failed trace, allow exactly **one** counterfactual replay/probe:

- AgentProf chooses the top recurring semantic group and the highest existing localization-signal step inside that group as the single candidate to probe.
- The equally informed control chooses the globally highest localization-signal step directly, without semantic grouping.
- Both use the same official TraceElephant counterfactual re-execution procedure and the same one-probe budget.
- Score the official **decisive-step attribution accuracy** over all 220 failures.

This is one experiment, one fixed RQ2 hypothesis, one action budget, one real public benchmark, and one accepted outcome. It directly tests whether the profile contributes decision value beyond the external localization signal. A positive complete result would materially weaken H2 and connect AgentProf's cross-run profile to a developer-facing attribution decision. A null or negative result would show that the current paper is not AAAI-ready; it would not authorize changing the thesis or RQ.

This has higher paper-decision value than the existing R315 packet because it produces a complete public-benchmark outcome from current mapped traces and an official replay protocol, rather than remaining protocol-level preparation that still requires recruitment or a new evaluation apparatus.

## Paper/claim impact and provisional routing

- **Do not change:** thesis, problem importance, two abstractions, four RQs, or the broad quality/safety/cost program.
- **Preserve:** RQ1 lineage/conservation result, RQ3 scoped component evidence, RQ4 cost result, and all material limitations.
- **After evidence exists:** a WRITE gate should precisely position generic grouping versus AgentProf's cross-layer responsibility and rewrite the RQ2 answer to match the one outcome result. It must not hide current comparator outcomes that remain material.
- **Provisional routing:** `EXPERIMENT_GATE` for the single TraceElephant test above. No other experiment is justified by this reread.

## Alternatives considered and decision

No alternative experiment is admitted. Projection/export comparisons would only reconfirm already verified equivalence; another AP/Work cutoff sweep would repeat the proxy construct; a broad tagger matrix would not solve H2; and a new product integration or large human study would violate the reuse/simple constraint. The chosen test uses a benchmark and dynamic protocol already present in the paper's evidence neighborhood and isolates the sole missing edge.

## Tree/search updates, project-memory updates, and completion

- **H1:** changed from blocker candidate to major-not-fatal; generic expression is prior art, cross-layer combination remains plausible.
- **H2/H5:** merged into the strongest acceptance blocker: no demonstrated downstream decision value beyond an existing localization signal.
- **H3:** remains major/partial but is not the next evidence branch.
- **H4:** bounded RQ1 evidence partially closes source-to-profile fidelity; no new lineage variant is needed now.
- **H6/H7:** remain limitations, not current paper-decision branches.
- **Search update:** primary sources now ground the novelty boundary, benchmark construct, AAAI bar, and closest actionability precedent. A comprehensive novelty map is still outside this targeted review.
- **Project-memory updates:** none. Canonical documents were read but not modified.
- **Paper/code/test updates:** none.
- **Completion assessment:** complete for the requested source-informed full-paper reread. The provisional verdict, four final current RQ states, H1/H2 changes, strongest reject argument, largest scientific and writing gaps, largest nearly supported claim, and exactly one experiment decision are recorded.
- **Residual uncertainty:** whether the existing TraceElephant adapter/profile output already exposes the candidate-to-replay handoff; whether official environments reproduce all 220 traces without drift; and whether recent closest preprints will be accepted. These affect execution logistics or novelty confidence, not the decision that one outcome test is required.
- **Next node:** the outer orchestrator should independently audit this report and, if it accepts the provisional routing, admit only the one-probe TraceElephant experiment above.
