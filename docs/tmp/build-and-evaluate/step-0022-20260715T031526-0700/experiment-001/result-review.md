# Independent Complete-Result Review

**Decision:** PASS
**Run validity:** VALID / COMPLETE
**Scientific verdict:** MIXED
**Evidence role:** supporting post-hoc mechanism boundary
**Must-fix findings:** none
**Optional findings:** none

## Scope And Reconstruction

A fresh read-only result reviewer inspected the approved plan, plan review,
implementation review, all three raw full-run roots, Step 0020 and Step 0021
baselines, current source diffs, paper contract, and authoritative submodule.
The reviewer independently recomputed the primary and diagnostic outcomes from
raw pair decisions and operation assignments rather than trusting report
booleans.

The reconstruction confirms complete coverage and conservation for both
populations. OSWorld-Human contains 287 sessions, 3,978 operations, and 3,691
scored pairs across all five held-out folds. CodeTraceBench contains 405
target-disjoint sessions, 20,866 operations, 20,461 pairs, and 2,948 complete
official stages across four frameworks. Official labels are loaded only after
prediction; Rust receives only visible `session` and `action` fields.

## Recomputed Outcomes

| Population | Current boundary F1 | Candidate boundary F1 | Current B-cubed F1 | Candidate B-cubed F1 | B-cubed delta |
|---|---:|---:|---:|---:|---:|
| OSWorld-Human | 0.679922 | 0.542657 | 0.786170 | 0.742492 | -0.043677 |
| CodeTraceBench | 0.268506 | 0.287106 | 0.475008 | 0.649173 | +0.174165 |

The OSWorld-Human candidate confusion is TP 970, FP 850, FN 785, TN 1,086,
with B-cubed precision/recall 0.734479/0.750682. The CodeTraceBench candidate
confusion is TP 1,297, FP 5,195, FN 1,246, TN 12,723, with B-cubed
precision/recall 0.828579/0.533630. CodeTraceBench improves on all four
frameworks but remains 0.005272 below phase-change in the pooled B-cubed score.

The reviewer confirms 47,303 CodeTraceBench action-changing calibration
occurrences and 38,171 identity occurrences. The OSWorld-Human fold-level
action-change counts are 2,516, 2,395, 1,838, 2,435, and 2,208, with cutoffs
0.280594, 0.283253, 0.297296, 0.295724, and 0.267110. Rust/Python equivalence
passes on every one of 3,691 decisions, 3,978 assignments, 2,107 segments, 42
unique motifs, and 3,978 units of mass, with NPMI/cutoff agreement within
`1e-12`.

## Scientific Decision

The fixed result rule yields **MIXED**: the candidate improves primary B-cubed
F1 on CodeTraceBench and degrades it on OSWorld-Human. Boundary F1 shows the
same population-dependent tradeoff. The result is valid and useful, but the
candidate must not replace the current Step 0020 recurrence implementation.

The reviewer approves restoring only the Step 0022 candidate code and retaining
the raw artifacts and Markdown history. The paper, design, implementation
documentation, RQ3, positive hypothesis, thesis, and AgentProf story must not
change. Result review must not introduce a second candidate; any later
mechanism proposal belongs to a new outer cycle.
