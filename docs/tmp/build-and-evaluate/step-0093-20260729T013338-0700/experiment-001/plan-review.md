# Independent Plan Review

## Round 1

**Verdict:** BLOCK

The independent reviewer found that the original protocol could misinterpret
retention of repeated task prompts or root labels as stable operation-path
structure:

- all 405 session IDs contain `fields.prompt`, so session-ID tie breaking leaks
  the task oracle into tied rankings;
- 251 tasks collapse to only 45 canonical root labels, while the planned
  `* work` removal did not remove the root position in general;
- the proposed paper wording and uncertainty interval needed a narrower,
  fixed-candidate retrospective interpretation.

## Disposition

Accepted. The plan now:

1. computes permutation-marginalized AP, Top-1, and MRR for exact-score ties and
   gives AUROC ties weight 0.5;
2. adds canonical root-only and canonical root-stripped representations;
3. requires positive task-bootstrap intervals for full versus root-only and for
   root-stripped versus each source-native baseline;
4. repeats generic-work removal after stripping the original root;
5. limits any admissible statement to CodeTrace, repeated prompt exposure, and
   retrospective representational consistency;
6. defines bootstrap intervals as conditional on the fixed candidate library;
7. verifies `fields.agent == prediction.framework` in both prediction files.

No scorer implementation or experiment execution occurred before this
disposition.

## Round 2

**Verdict:** APPROVE

The same reviewer confirmed that all Round 1 blockers were resolved: no
task-bearing ID controls tie order; the tie-aware metric semantics are frozen;
root-only and root-stripped gates isolate non-root structure; generic-work
removal also covers the root-stripped representation; the claim and bootstrap
population are explicitly bounded; and framework equality is checked in both
prediction files.

Implementation and real preflight are authorized under the amended plan.
