# Product Port Plan: Optional Reference-Calibrated Recurrence

**Entered:** 2026-07-15
**Input:** independently reviewed Step 0030 `VALID / SUPPORTED` experiment
**Change type:** feature; optional supervised calibration of the existing
operation-stack induction path

## Public Behavior

Keep `--induce-operation-stack` and the Step 0024 label-free two-means
constructor as the default. Add one optional ordinary operation input:

```text
--induce-calibration-operation-file PATH
```

The file contains independently grouped historical operations with exactly one
`session`, `action`, and `group` value per operation. It is used only with a
separate `--induce-reference-operation-file`: the score reference builds the
unchanged action-transition NPMI table, the grouped calibration history selects
one scalar by operation-weighted B-cubed F1, and the scalar is applied to the
target input. Calibration and target session IDs must be disjoint.

## Fixed Semantics

Port exactly the algorithm already tested in Step 0030:

- unchanged NPMI association, adjacent-occurrence weighting, and unseen-pair
  boundary rule;
- candidates below the minimum observed calibration score, at every adjacent
  distinct-score midpoint, and above the maximum;
- one per-operation B-cubed objective over session-qualified reference groups;
  profile resource values do not enter fitting;
- exact ties choose the numerically smallest cutoff;
- one scalar for the entire invocation; and
- unchanged segment construction, motif naming, stack folding, and resource
  mass.

No numeric-cutoff flag, benchmark identity, per-framework rule, second score,
context window, target metric, retry, or new algorithm name is allowed.

## Compatibility And Errors

- Omitting calibration must preserve every Step 0024 boundary decision and
  existing report field.
- Supplying calibration without operation-stack induction or without a
  separate score-reference file is an error.
- Missing/multiple `session`, `action`, or `group` values are errors.
- Calibration/target session overlap is an error.
- A calibration population with no finite score observed in the score
  reference is an error.
- Profile-spec input follows the existing plural operation-file convention.

## Validation

1. focused Rust unit tests for candidate enumeration, selected cutoff,
   operation-weighted B-cubed, changed target boundary, and unchanged omitted-
   calibration path;
2. CLI integration tests for the normal grouped-reference command and the two
   invalid input combinations;
3. complete Rust tests, Clippy, and formatting;
4. replay the complete existing Step 0030 OSWorld and CodeTrace input through
   the release binary and require exact Python/Rust selected cutoffs, all target
   decisions, segments, and pooled metrics; and
5. independent code/diff review with an explicit code-growth and reduction
   pass.

## Repository And Publication Boundary

The user prohibits branch creation or switching during auto research, so this
port stays on the current research branch. It does not create a broad mature-
project PR from the research branch. Git publication is independent of the
scientific result. No paper, global skill, or read-only paper submodule is
changed by the implementation itself.
