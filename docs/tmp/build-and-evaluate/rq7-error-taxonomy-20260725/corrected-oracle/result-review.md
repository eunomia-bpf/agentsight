# Independent result review

## Verdict

Approved for the same-question corrected-oracle reassessment. This is not an
approval of edge-level equivalence or a general exact-conformance claim.

The reviewer independently confirmed:

- 120 unique corrected expected rows, with 24 shifts: 17 A, 7 C, no B or D.
- A 480-row method matrix whose answers/statuses are preserved and whose
  correctness fields exactly match the corrected answers.
- Trajectory A/B/C/D scores of 12/30, 28/30, 30/30, and 30/30; 100/120
  overall.
- Seven of the original nine B+C mismatches dissolve, with no new B+C
  mismatch.
- Per-project B+C scores of 8/10 for agentsight and 10/10 for each other
  project.
- Trajectory minus ProcGrep B+C correct coverage of +0.9667, project-block
  bootstrap interval [0.90, 1.00].
- Wrapped patches now both produce patch-header edges and classify their
  containing invocation as `edit`.
- The frozen-v2 session bridge and immutable-path treatment reproduce the
  prior HEAD compatibility boundary and are appropriate for these fixed
  questions.
- AgentSight B1/B2 are exactly explained by the projection's stale
  accumulated cwd, not by oracle option arity.

## Judgments

Validity: approved for reassessing the same immutable questions; not
edge-equivalence.

Research value: high. The result separates seven oracle-caused B+C rows from
one real projection cwd defect and quantifies substantial action-oracle drift.

Paper impact: the narrow B+C result is 96.7% on this frozen corpus versus
complete ProcGrep abstention, but reporting must also include A at 40.0% and
overall conformance at 83.3%. “Exact” and general conformance claims are not
supported. The six-project bootstrap is corpus-block uncertainty, not
population generalization.

Next experiment: fix projection per-event cwd handling; then cut a
version-consistent v4 freeze with regenerated anchors and questions. Require a
full edge-ledger comparison and all-120 scoring, with adversarial
changing-cwd, failed-call, inline-cd, and wrapped-patch fixtures.

