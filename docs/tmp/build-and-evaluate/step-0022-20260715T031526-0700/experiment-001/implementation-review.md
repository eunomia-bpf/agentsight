# Independent Implementation Review — Cross-Action Calibration

**Final verdict:** PASS
**Role:** fresh read-only implementation auditor using the
`research-experiment-design` evidence-validity standard

## Audited Change

The reviewer checked the approved plan against the Rust runtime, Python
reference evaluator, Rust/Python equivalence evaluator, CodeTraceBench adapter,
and focused tests before any real preflight or full experiment ran.

The core change passes:

- NPMI and both marginals still use every adjacent reference transition;
- only action-changing transition occurrences enter the unchanged deterministic
  occurrence-weighted two-means calibration;
- identical actions are continuous by identity, including an unseen identical-
  action pair;
- unseen cross-action behavior, motif construction, policy/interface, source
  fields, and resource weighting remain unchanged;
- Python and Rust implement the same rule;
- Step 0020 and Step 0021 current-recurrence summaries are the main baselines
  and are validated as complete before use;
- no scorer label can enter either constructor path.

The focused Rust test verifies that a reference with seven transitions uses
exactly five action changes for calibration and excludes two self-transitions;
it also verifies that an unseen same-action target pair is not a boundary. At
review, 42 Rust unit tests, eight profile CLI tests, three trace CLI tests,
Python compilation, and diff checking passed.

## First Review — REPAIR

The reviewer found two bounded surrounding-script defects:

1. the Rust/Python equivalence script still required Step 0020's old absolute
   output totals of 2,656 segments and 44 motifs, which would reject a correctly
   equivalent candidate solely because this experiment intentionally changes
   boundaries;
2. the CodeTraceBench full summary still inherited Step 0021's `decisive` and
   `additional RQ3 evidence` metadata rather than the approved supporting
   post-hoc mechanism-development role.

## Root Repair And Follow-Up

The root removed only the obsolete 2,656/44 gates. Exact per-fold comparison of
all candidate-derived segments and motifs remains, together with fixed 3,691
decisions, 3,978 assignments, and conserved mass. It changed only the full-run
CodeTrace metadata to `supporting` and `post-hoc mechanism-development evidence
only`; preflight remains dependency-only with no paper impact.

The bounded follow-up returns PASS with no remaining must-fix. No algorithm,
input, metric, workload, result rule, or experiment scope changed during the
repair.
