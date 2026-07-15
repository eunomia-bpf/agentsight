# Independent Implementation Review

**Initial decision:** REPAIR
**Bounded follow-up:** PASS
**Remaining must-fix findings:** none

## Audited Semantics

A fresh read-only reviewer explicitly used `research-experiment-design`, read
the approved Step 0023 plan and complete allowed diff, and ran no metric-bearing
experiment. It confirms:

- NPMI still uses all adjacent reference transitions and unchanged left/right
  marginals;
- the global cutoff is the existing deterministic occurrence-weighted
  two-means over every transition occurrence;
- the cross-action cutoff is the same two-means over action-changing
  occurrences only;
- a same-action target pair applies the global cutoff and an action-changing
  pair applies the cross-action cutoff;
- an unseen pair remains a boundary and motif construction is unchanged;
- Rust receives only unit-weight `session` and `action`, with official
  CodeTraceBench stages and committed scorer summaries read only after
  prediction;
- Python and Rust reports expose both calibration populations, cutoffs, per-pair
  selected population/cutoff, and exact decision/segment/motif/mass checks;
- preflight emits no scientific verdict;
- no parameter, fallback, search, feature, benchmark, name, or second candidate
  was introduced;
- no stale fixed candidate segment/motif total remains.

The focused fixtures include both same-action and action-changing target pairs
and references with two distinct finite cross-action scores. The terminal local
suite passes 41 Rust unit tests, eight profile CLI tests, and three trace CLI
tests. Python compilation, formatting/diff checking, and the release build pass.

## One Repair

The first review found one stale Step 0020 metadata sentence in the OSWorld
summary that claimed local improvement before the complete result. The root
replaced it with neutral semantics: the file records OSWorld's exact
higher/equal/lower B-cubed relation, while the fixed Pareto verdict requires
both complete populations. The bounded reviewer confirms PASS with no remaining
must-fix.

## Decision

The implementation matches the one approved candidate and may enter REAL
PREFLIGHT. Preflight metrics cannot change the implementation, plan, verdict,
or paper story.
