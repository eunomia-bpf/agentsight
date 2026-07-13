# RQ2 Revision-1 Experiment Handoff — Plan Review Exhausted

## Context

- **Cycle/gate/loop:** cycle 0001 / EXPERIMENT_GATE / RQ2 revision 1.
- **Timestamp:** 2026-07-11T20:17:18-07:00.
- **Status:** experiment ended before implementation or preflight because Round 5
  remained `REVISE`.
- **Immutable RQ:** Does profiler output correspond to real problems?
- **Conclusion-claim revision:** 1 of at most 2; unchanged during this loop.

## Entry And Scientific Objective

RQ2 revision 0 produced admitted contradictory evidence: flattened, risk-ranked
induced leaves did not consistently beat flat/matched alternatives on AgentRx or
TELBench. That result invalidated the leaf-grouping evidence but did not test or
remove the paper's larger multi-resolution operation-stack contribution.
Revision 1 therefore proposed a stronger, source-grounded mechanism: preserve
the full query-conditioned semantic hierarchy, navigate it coarse-to-fine with a
development-only risk score, identify small failure-containing scopes, and then
improve exact localization or reduce inspection work on fresh Who&When and TRAIL
traces.

## Work Completed

The loop completed a primary-source protocol audit and five serial scientific
plan reviews in the single `plan-review.md`. The plan now specifies:

- 184 Who&When and 148 TRAIL fresh confirmation traces, with AgentRx/TELBench
  used only for development;
- no-answer Who&When primary scoring with exact integer steps, plus compatibility
  rows for the released answer-assisted substring evaluator;
- scrubbed TRAIL primary inputs that remove embedded offline answers, annotator
  solutions, and reference/test patches, with official raw input retained only
  as compatibility;
- exact handling of release anomalies and four zero-gold TRAIL traces;
- proposed, semantic-leaf, flat, fixed-window, fixed-field, native, query-free,
  non-risk, matched-random, published SDBL, whole-session, and oracle comparisons;
- a frozen development-only TF-IDF/logistic risk scorer and identical-score
  structural controls;
- exact operation, selected-content-token, total-token, downstream-quality,
  clustered-bootstrap, subgroup, and full-matrix rules;
- the concrete Rust structural-node/navigation schema, CLI changes, driver,
  tests, checkpoints, and significant-run resource envelope needed before a real
  preflight.

No paper, Rust code, driver, source repository, or submodule was modified by this
revision-1 loop. No preflight or partial experiment was run or interpreted.

## Why The Plan Did Not Pass

Rounds 1–4 found and repaired construct ambiguity, uncharged summaries, missing
mechanism ablations, Who answer leakage/weak scoring, TRAIL offline-answer
leakage, SDBL comparison mismatch, unspecified risk scoring, zero-gold
denominators, underdefined uncertainty and equal-cost rules, missing
implementation steps, and a falsely query-conditioned “query-free” ablation.

Round 5 found one remaining load-bearing defect. The plan's mandatory criteria
could all be satisfied after flattening terminal scopes into an ordered operation
list and partially filling the last scope. Such a result would establish
hierarchy-constrained operation ranking, but not the claimed ability to produce
small navigable failure scopes. Because the fifth review remained `REVISE`, the
experiment skill forbids a sixth round or execution under this plan.

## Scientific Impact

This is not evidence against the immutable RQ or the multi-resolution thesis; it
is an unapproved experimental construct. The paper must not claim that revision 1
ran, passed, or failed empirically. It should preserve the attractive hypothesis
and explicitly mark whole-scope usefulness as unanswered. Revision-0 negative
evidence remains admitted and must stay visible: the hierarchy cannot be defended
using flattened leaf groups.

The next experiment selected by a later full-paper REVIEW should retain the
complete ambitious claim and add a whole-scope evidence block:

1. emit only complete non-overlapping terminal scopes for the scope metric;
2. predeclare a maximum whole-scope operation and token work bound;
3. measure whole-scope failure recall/Hit and scope-size/work AUC without partial
   filling;
4. require superiority over leaf-only, fixed, native, matched-random, and adapted
   EASD scopes where applicable;
5. separately retain atomic-operation and downstream localization curves so the
   paper proves both scope quality and final utility.

## State And Routing

- **Plan-review scope:** complete, five of five rounds, final `REVISE`.
- **Implementation/preflight/full execution:** not started and not authorized.
- **Uncertainty:** whether a bounded whole-scope criterion can be both fair across
  heterogeneous trace lengths and strong enough to distinguish semantic
  hierarchy from shape/risk effects.
- **Revisit evidence:** a WRITE_GATE idea synthesis and blind full-paper REVIEW
  that preserve RQ2, explicitly require whole-scope utility, and select the next
  decisive experiment.
- **Next action:** independent outer audit of this handoff, then WRITE_GATE
  (`iter-refine-ideas` followed by `iter-refine-writing`) and full-paper REVIEW.
