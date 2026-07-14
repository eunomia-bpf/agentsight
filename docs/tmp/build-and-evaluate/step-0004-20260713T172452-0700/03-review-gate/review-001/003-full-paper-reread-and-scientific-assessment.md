# Full-Paper Reread and Source-Grounded Scientific Assessment

## Node record

- **Completed:** 2026-07-14T02:04:20-07:00
- **Parent:** `002-external-search-and-source-verification.md`
- **Objective:** reconcile the blind review and current primary-source search with the canonical research record, Step 0004 experiment evidence, and the complete active paper.
- **Inputs and provenance:** `docs/paper/`; `docs/evaluation.md`; `docs/background-related-work.md`; `docs/user-instruction.md`; `docs/idea-story.md`; Step 0004 EXPERIMENT and WRITE reports; earlier RQ1/RQ3/RQ4 experiment ledgers and terminal artifacts cited by those files.
- **Method:** read the internal evidence only after the paper-only attack map and external search were complete; check each RQ's paper claim against the strongest terminal evidence; then reread the full paper and all claim-bearing figures/tables.
- **Paper mutation:** none. REVIEW is read-only for the paper and canonical story files.

## Scientific contract audit

The exact thesis remains both ambitious and worth defending:

> **Agent observability needs profiling, not only debugging.**

The four fixed questions remain appropriate and unchanged:

1. Does semantic profiling improve resource attribution?
2. Does profiler output correspond to real problems?
3. How accurate are the tags?
4. What is the profiling cost?

The current failure is not an undersized thesis. It is that the paper presents stronger completion than the available RQ1/RQ3/RQ4 constructs establish, while its introduction and conclusion have not caught up with the completed RQ2 evidence.

## RQ-by-RQ assessment

### RQ1 — useful mechanism evidence, not yet independent attribution truth

The complete local-history evidence is real and substantial: 325 Codex/Claude trajectories, 183,714 system observations, conserved totals, complete prompt/system-effect coverage, a 1,000-permutation session-preserving association check, and materially different time/token rankings. These results establish that prompt-derived fields partition system effects and retain behavior information beyond session identity.

They do not yet establish independently correct resource responsibility. The mixed-weight outcome is defined using prompt-tag categories while prompt tags are also the intervention that partitions the groups. More unique groups can mechanically reduce mixing. The current evidence therefore supports mechanism, accounting, and non-random association, but an independent responsibility oracle remains necessary for the final RQ1 answer.

### RQ2 — cumulatively answered

The Step 0004 subsection and independent audits accurately represent the strongest cumulative evidence:

- AgentProcessBench: 1,000 trajectories and 8,509 human-labeled assistant steps; equal-family macro AP 0.588 versus 0.556, paired gain 0.0315 with 95% interval [0.0151, 0.0535], matched-refinement `p=0.00995`, and recall at 30% work 43.52% versus 35.85%.
- HINTBench: 536 released test trajectories and 12,877 steps; Work@80 41.57% versus 46.29% raw action. Development labels selected one of 24 fixed field orders; reported test labels remained held out.
- TraceElephant: all 220 real failed executions and 5,960 atomic steps; Work@50 19.55% versus 46.64%, and recall at 20% work 52.57% versus 23.79%. The predeclared Work@80 tested hypothesis remains `VALID / INCONCLUSIVE` in the research record and is not falsely presented as positive.

This is enough for the paper-level positive answer that target-blind semantic profiles correspond to and concentrate independently annotated real problems. Another RQ2 score, cutoff, or benchmark is not justified.

### RQ3 — current paper result has a hard construct mismatch

The active RQ3 text scores mapping-derived `phase` against source-native `action` labels. A coarse phase vocabulary and an action identity vocabulary are different constructs. High agreement need not mean correct phase and low agreement need not mean incorrect tagging. Existing R285 no-map results are often stronger on the same phase/action measure, showing that the metric also rewards retaining the raw action partition rather than deriving a useful semantic phase.

The rendered claim is also numerically inconsistent: some boundary values are inapplicable, and the figure does not support “seven of nine exceed 0.7 on both metrics.” Therefore the historical 7/9 claim and figure cannot remain as the current RQ3 answer.

This does not authorize narrowing RQ3. A later complete RQ3 experiment still needs the positive fixed hypothesis: a target-blind tagger or mapping should assign accurate and stable task, phase, action, and boundary identities on unseen agents/task families. Existing OSWorld-Human grouped human actions are a promising reusable boundary oracle, but the tracked public operation files do not contain the same free-form text plus independent semantic labels needed to validate every natural-language tagger. Solving that gap now would introduce a new data/ontology program rather than a simple reuse experiment.

### RQ4 — existing timing is real but not a scaling answer

The 76 profile specifications demonstrate that current configurations run, but they use one 34,539-operation union input and therefore do not form a scaling curve. The R160 fixed eight-session clean/cached run demonstrates an executable cold/warm path but is not integrated with the complete public-workload cost result. Hardware, per-workload size, peak RSS, rows per second, output size, and cold/warm end-to-end comparison remain absent from the paper.

RQ4 is the simplest high-value next experiment because its runner, workloads, binary, cache path, and prior timing evidence already exist. It requires measurement consolidation, not a new benchmark, model, ontology, or complex statistical framework.

## Whole-paper consistency findings

### Must fix before starting the next outer experiment

1. Introduction and contribution text still state the superseded four-dataset, 34,539-operation, 9.4%-work, and 45%-group-reduction RQ2 result.
2. Evaluation setup still assigns RQ2 to the four older annotated families instead of distinguishing the current AgentProcessBench/HINTBench/TraceElephant evidence.
3. An RQ1 paragraph calls its six historical tasks “the same six tasks used in RQ2,” which is no longer true.
4. Conclusion restores the old 9.4% and 4/6 statements rather than the current cumulative RQ2 answer.
5. Introduction, RQ3, and conclusion present the invalid 7/9 tag-accuracy result as complete evidence.
6. HINTBench must be described as 536 released **test-split** trajectories rather than as the whole 629-trajectory benchmark.

These are factual synchronization repairs. They must not replace or narrow the thesis, fixed RQs, abstract/intro problem direction, semantic operation-stack model, or AgentProf contribution.

### Submission blockers that do not block the next experiment

Official LangSmith, Datadog, OpenTelemetry, and pprof sources contradict categorical statements that existing systems cannot aggregate tags, metrics, or tag-derived views. Process-Centric Analysis, Hodoscope, process-mining event abstraction, and AgentGraph are also missing close neighbors. The large thesis remains defensible when novelty is stated precisely as the joint capability to derive recurring responsibility fields from heterogeneous agent histories, propagate them to cross-layer additive effects, and materialize alternative query-time profiler hierarchies. A focused literature/novelty writing pass remains mandatory before submission, but it need not delay the reused-asset RQ4 run.

## Taste assessment

- **Principle:** profile recurring semantic responsibility across executions rather than only debug individual execution trees.
- **Belief challenged:** run-local tracing structure and application-supplied metadata are sufficient for population-level attribution.
- **Strongest alternative explanation:** the current gains could arise from ordinary tag aggregation and finer partitioning rather than the operation-stack abstraction unless independent attribution/tag evidence isolates the mechanism.
- **Largest claim worth defending:** one conserved operation layer can attribute multiple additive measures to recurring semantic responsibility across heterogeneous agent histories and expose both resource concentration and real problems.
- **Classification:** simple-but-deep core, incomplete-but-promising evidence. The paper becomes complicated only when tagger/boundary variants are treated as additional core concepts.
- **Terms to keep small:** operations and operation stacks are the core; intent attribution and stack construction are mechanisms; regex, LLM, clustering, induction, pprof, and flamegraph are implementations or alternatives, not separate scientific abstractions.

## Decision and next node

Route to a narrow WRITE correction for stale/invalid factual claims. After independent verification of that correction, close Step 0004 and begin one reused-asset RQ4 experiment. Do not start another RQ2 scheme and do not expand RQ3 into a new labeling infrastructure in this cycle.
