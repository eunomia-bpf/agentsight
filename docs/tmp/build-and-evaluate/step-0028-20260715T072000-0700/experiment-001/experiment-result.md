# Experiment Result: RQ3 Reference-Calibrated Recurrence

**Status:** **INVALID — NO SCIENTIFIC RESULT**
**Scientific role reached:** none; REAL PREFLIGHT did not execute end to end
**Candidate target metrics:** none

## Tested Hypothesis

Not tested. The planned question was whether a single cutoff fitted from
independently grouped reference trajectories improves the existing Step 0024
action-transition recurrence constructor on both reused complete target
populations. Neither target population reached candidate execution.

## Evidence Produced

- Product implementation and evaluator implementation passed independent
  implementation review with zero must-fix findings.
- Rust checks passed: 44 unit tests, 9 profile CLI tests, 3 standard-trace CLI
  tests, formatting, and Clippy with warnings denied.
- Both real-preflight attempts stopped before candidate construction because
  the new OSWorld adapter did not exactly reuse the established eligibility
  behavior for singleton groups.
- No raw profile, prediction JSONL, target metric, or scientific comparison was
  produced.

The detailed attempt record is [preflight-failures.md](preflight-failures.md).

## Interpretation

The result is invalid, not supported, mixed, contradicted, negative, or
inconclusive. It does not answer RQ3 and does not update belief in the tested
hypothesis. In particular, it cannot authorize changing the recurrence score,
cutoff objective, original thesis, four RQs, contribution, or paper story.

## Required Disposition

Close this experiment after independent result review. Do not run a third
preflight, do not promote the optional calibration mode, and do not edit the
paper from this result. The outer loop must decide whether to retain only the
auditable implementation record, remove the unvalidated candidate code, or
choose a different admitted experiment; that disposition cannot pretend the
preflight count reset.

## Completed Disposition

Independent result review returned PASS with zero must-fix findings and chose
the minimum clean disposition: preserve the Markdown history but remove only
the unvalidated candidate implementation. That removal is complete. The three
candidate-modified tracked Rust/CLI/test files have zero diff against the
experiment-entry `HEAD`, all three untracked evaluator files are absent, and
the restored original test suite passes. The Step 0027 arithmetic correction
and every Step 0028 plan/review/failure/result report are retained.
