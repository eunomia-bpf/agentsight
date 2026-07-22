# RQ3 Plan Review — Round 2

**Verdict: PASS**

The repaired plan resolves every Round-1 construct-validity blocker and is
executable from the frozen RQ1 artifacts without a new trace extraction.

## Verification of required repairs

- **First/repeat terminology:** the plan now uses `first-observed mutation`
  and `repeat-observed mutation`, explicitly states that the first observation
  is not workspace expansion, and limits “rework” to a non-normative shorthand.
- **Episode unit:** compound file effects are collapsed by
  `(project, worktree_id, artifact_id, event_id)` and retained as operation
  multi-labels. This prevents two effects from one Tool action becoming a
  zero-distance repetition. The frozen corpus has 13,152 raw mutation rows and
  13,150 resulting episodes, so the distinction is both testable and exactly
  reconcilable.
- **CCDF denominator:** the primary distribution now retains all 7,154
  observed identities and reports the zero mass; the conditional CCDF is
  explicitly limited to the 2,219 identities with at least one episode.
- **Birth states:** all four frozen states are named and retained. Small strata
  may be coverage-limited, but their denominators cannot silently disappear.
- **Action-time axis:** the evolution panel uses the frozen native Tool-action
  `event_index`; it expressly rejects mutation ordinal, smoothing, and rolling
  windows. Wall time is secondary rather than a replacement timeline.
- **Operation composition:** rename/delete are multi-label composition among
  repeat episodes, and the plan distinguishes raw rows from collapsed episode
  totals during reconciliation.
- **Claim boundary:** heavy-tail, convergence, thrashing, defect-repair, waste,
  and forgetting/reset claims are prohibited. F6 supports only descriptive
  right-skew, observed upper-tail length, concentration, and changing
  first/repeat-observed mix.
- **Source reconciliation:** sampled episode IDs must resolve to the frozen RQ1
  event JSON, while lineage, delete--recreate identity, and session changes are
  independently checked. The named source files exist alongside the CSVs.
- **Stop rules:** project eligibility, coverage-only handling, cross-case
  minimum, exact denominators/exclusions, all-panel completion, and independent
  result/figure review are now explicit.

## Non-blocking implementation note

In panel 2, implement “cumulative share of mutations” as cumulative share of
**collapsed mutation episodes**, not raw mutation rows or the artifact CSV's
raw `mutations` aggregate. Likewise, if a birth-state stratum is too small for
a curve, print its count and the exclusion reason. These follow directly from
the approved definitions and do not require another plan revision.

The resulting experiment remains correctly scoped: it contributes descriptive
evidence for RQ3's mutation-concentration facet, not a complete answer to the
separate validation-followed revision or module-switching facets.
