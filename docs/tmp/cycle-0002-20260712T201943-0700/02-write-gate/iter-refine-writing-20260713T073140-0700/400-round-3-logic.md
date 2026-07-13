# Round 3 — Logic and Argument Chain

- Reviewer completed: `2026-07-13T08:06:13-07:00`
- Root edits completed: `2026-07-13T08:13:20-07:00`
- Verdict: `REVISE`
- Story verdict: `NO DRIFT`
- Post-round paper SHA-256: `e3e0bb40e1a59757f3b099991095fbdbe3126aad3eb71371e4ef78a33ad71d2d`

## High-level audit

The reviewer read the complete current paper/bibliography, full user and idea history, all WRITE reports, and the rendered eight-page entry PDF. It found a continuous canonical chain:

> population-level quality/safety/cost questions → need for profiling → semantic/cross-run challenge → operations and operation stacks → AgentProf → attribution/localization/tag/cost evaluation

The exact thesis, broad stakes, two-object model, and four fixed RQs remain intact. No idea revision is authorized.

## Presentation-level must-fixes

1. Rendered float order violated evidence-before-interpretation: RQ2’s table appeared after its answer and the RQ3 plot appeared before its setup.
2. Literal “no runtime hierarchy” wording conflicted with the intended distinction between native execution occurrence and reusable cross-run profiling responsibility.
3. “Attribution” moved implicitly between additive accounting, semantic grouping, localization, and causal diagnosis.
4. The native-hierarchy special-case sentence claimed that selecting `dataset` reproduced an episode/step hierarchy.

## Applied fixes

- Repositioned the RQ2 `table*` source immediately after the RQ2 question and before its setup, so the rendered table now appears at the top of page 6 before result interpretation.
- Kept the RQ3 figure as a top float after its source setup; it now appears on page 7 after the RQ3 heading, method, callout, and initial interpretation rather than before the RQ.
- Replaced literal absence claims with the stronger precise distinction: agents may expose spans/event order, but native execution structure does not determine the stable reusable cross-run responsibility hierarchy required for profiling.
- Defined attribution operationally as assigning a conserved additive measure to a declared responsibility path; it does not by itself establish causal diagnosis.
- Described operation stacks as serving the profiling role of code call stacks rather than claiming they recover a runtime call stack.
- Corrected native-hierarchy subsumption: selecting the corresponding ordered native fields, such as episode then step, reproduces that hierarchy.
- Replaced a forward-defined “same six tasks” reference with an explicit pointer to the RQ2 tasks.
- Added a scoped RQ3 `Answer` that reports only its leave-dataset-out mapping result and supervised upper-bound headroom.

## Scientific gaps recorded for REVIEW/EXPERIMENT

These are not prose defects and were deliberately not “fixed” by weakening, qualifying, or deleting claims.

### E1 — RQ1 independence/circularity

The semantic-axis experiment evaluates lower mixing by task categories after adding prompt-category tags. The paper does not yet show that the scoring category is independently sourced from the tag used to create groups. The permutation establishes association under the construction, not independent responsibility correctness. RQ3 uses different public mappings and does not close this local-tag gap.

Required evidence: independently recorded task/category lineage or an equivalent target-blind attribution ground truth.

### E2 — RQ2 ranking target leakage

RQ2 says annotations are hidden from profiler construction, but ranks groups by the fraction of those hidden positives. Thus grouping may be target-blind while inspection order is target-visible. AP, recall, and work values do not yet demonstrate target-blind localization.

Required evidence: an independent visible ranking/weight signal and a complete rerun. The two internal AgentProcessBench constructions do not alter the paper in this writing cycle.

### E3 — RQ2 decision objective

The table supports a tradeoff: operation stacks improve some work/coverage measures while per-session/native lead other measures. The paper lacks a predeclared primary decision objective under which the positive localization claim is judged.

Required evidence: target-blind ranking plus a declared primary localization/inspection criterion.

### E4 — RQ3 mechanism scope

RQ3 evaluates mapping-derived phase fields against native action annotations. It does not validate the local prompt tagger, LLM tagger, arbitrary intent tags, or RQ2’s ranking signal. The `0.7` threshold and interpretation of native actions as semantic-phase ground truth also need source/protocol justification.

Required evidence: complete held-out evaluation for each claimed tag mechanism and downstream sensitivity.

### E5 — RQ4 cold vs. cached cost

The paper defines complete construction as parse/enrich/construct/fold and separately reports end-to-end seconds, uncached tag counts, per-tag p95, and cache behavior. It does not state the batching/concurrency model or aggregate cold-start duration. Capture overhead is also excluded by definition.

Required evidence: complete cold construction, warm repeated query, batching/concurrency, memory/output size, and separately reported capture cost.

### E6 — “Over 90%” derivation

The visible ablation reports 90.4% no-tag mixed weight, 84.4% session-only, and 36.7% prompt-tag. The introduction/conclusion sentence that semantic profiling separates over 90% of cost left mixed by per-session views is not derivable from those visible values without another statistic.

Required action: reconcile the intended statistic with complete source results; do not paraphrase around the mismatch.

### E7 — Dataset cardinality provenance

The paper reports 15 families/47,590 operations overall, four families/13,265 in one RQ1 test, four datasets/34,539 in RQ2, and nine datasets/13,265 in RQ3. The relationship among families, datasets, tasks, and RQ subsets is not explicit.

Required evidence: a source-derived provenance table or equivalent complete setup accounting.

## Additional routed findings

- Existing-tool gap statements remain categorical; Round 5/10 must distinguish cross-layer operations/query-time responsibility rather than deny semantic/cost aggregation.
- Abstract should make population-level profiling explicit.
- Abstract/Conclusion should close RQ4 only after its scope is internally consistent.
- “The AP differences” needs an identified contrast and null from experiment records.
- Different rankings alone do not prove that either identifies a true bottleneck.

## Build and visual verification

`cd docs/paper && make` succeeded after float placement.

- PDF: 9 pages, the AAAI maximum;
- main content and conclusion end on page 7;
- pages 8–9 contain references only;
- Table 1 renders at the top of page 6 before RQ2 interpretation;
- RQ3 heading/setup/callout precede Figure 4, which renders at the top of page 7;
- section references, fonts, anonymity, and bibliography remain valid;
- no unresolved citation/reference or undefined-control-sequence warning.

Compiled pages 6–7 were visually inspected at normal page scale.

## Lock audit

- Thesis unchanged verbatim.
- Exactly four RQs unchanged in order/meaning.
- No number, baseline, metric, dataset, hypothesis, result, evidence status, or citation changed.
- No claim was narrowed to evade a scientific objection.
- No internal negative result or fifth RQ entered the paper.
- No core abstraction added.
- No citation/bibliography deletion.
- No submodule, idea history, user instruction, or shared skill change.
- No Git operation.
