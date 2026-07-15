# Independent Experiment Plan Review — Round 2

**Completed:** 2026-07-15T06:20:00-07:00  
**Skill:** `research-experiment-design`  
**Mode:** independent and read-only  
**Verdict:** **APPROVE**  
**Must-fix:** none

## Review

The revised plan cleanly separates the Step 0024 threshold-eligibility decision
from the local ordering. Neighboring edges are now ordered only by raw NPMI.
Within a target session, every raw score comes from the same reference model and
transition sample space, so the values are commensurate even when the existing
threshold decisions used different global and cross-action cutoffs.

The one hypothesis, label-independent decision-subset property, same-action
preservation property, fixtures, diagnostics, and Rust/Python equivalence
contract all use the same revised definition. The plan adds no field, window,
normalization, threshold, candidate, dataset, benchmark, or target-label tuning.

## Authorization

Implementation is authorized exactly as revised. Step 0024 threshold decisions
must be computed first. Only an action-changing threshold boundary whose raw
NPMI is no greater than each available immediate neighbor may remain a final
boundary. No candidate metric may be read before implementation review and REAL
PREFLIGHT authorization.
