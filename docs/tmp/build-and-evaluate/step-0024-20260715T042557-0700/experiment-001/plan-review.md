# Independent Experiment-Plan Review

**Decision:** APPROVE
**Must-fix findings:** none

The independent reviewer explicitly used `research-experiment-design`, read the
complete Steps 0020–0023 evidence and current contracts, and performed no edit
or experiment.

## Judgment

`min(global_cutoff, cross_action_cutoff)` is the smallest principled repair,
not heuristic soup. Step 0021 diagnoses a global cutoff that can be too high
for cross-action continuity because its high cluster is identity-dominated.
Step 0023 isolates its only OSWorld regression to 11 new boundaries where the
cross-action cutoff is higher. The `min` rule is the parameter-free least-change
composition of the two already-audited calibrations: it permits the repair only
in the intended lowering direction and preserves current behavior otherwise.
It adds no score, weight, tolerance, learned gate, third threshold, fallback,
exception, or new name.

Decision-set monotonicity is scientifically relevant and correctly scoped.
Because a boundary is `score < cutoff`, the applied cutoff is never above
current for any seen pair. The candidate may recover continuity but cannot add
current-relative fragmentation. This rules out Step 0023's observed failure
mode but does not substitute for accuracy: over-merging remains possible and
the fixed complete-population B-cubed Pareto verdict still decides adoption.

The fixed RQ3 hypothesis, thesis, four RQs, contribution, and story are
preserved. Current recurrence is the main baseline; Steps 0022/0023 are
component diagnostics. The exact Pareto rule, two complete existing
populations, reference/scorer isolation, five commands, terminal coverage,
equivalence/mass, post-hoc boundary, and one-candidate discipline all pass.
