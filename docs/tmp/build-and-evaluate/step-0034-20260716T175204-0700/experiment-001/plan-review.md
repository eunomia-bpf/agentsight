# Plan Review: RQ3 Cross-Domain Calibration Of Existing Recurrence Scores

## Verdict

The experiment is nonredundant, fits RQ3, and is executable, but the planned
positive-result rule does not use its own uncertainty analysis. That defect can
turn an unstable or practically null point difference into a claimed supported
cross-domain result, so the interpretation rule must be repaired before the
run.

## Blocking defect

### The support rule ignores uncertainty and cannot classify a noisy apparent win as inconclusive

The plan schedules 10,000 paired, session-level bootstrap draws in each target
domain, but then declares a positive result solely from complete-population
point ordering: no lower than label-free in both targets, higher in at least
one, and higher than raw transfer in both. It explicitly says that the
bootstrap intervals do not affect that relation. Thus, arbitrarily small
positive differences qualify even if the paired intervals include substantial
negative effects in either domain. This is incompatible with the admitted
paper story that calibration transfers across domains, rather than merely the
descriptive claim that one fixed finite table contains a favorable ordering.
It also leaves no predeclared path for the common outcome in which all point
relations pass but the evidence does not distinguish improvement from harm.

Before execution, make the paired uncertainty part of mutually exclusive
positive, contradictory, mixed, and inconclusive rules. At minimum, specify the
interval construction and require the candidate-versus-label-free intervals to
support the claimed preservation in both directions and the
candidate-versus-raw intervals to support the claimed normalization benefit in
both directions; intervals spanning claim-relevant signs must lead to
mixed/inconclusive rather than positive. The complete-population B$^3$ values
can remain the primary reported estimates. The current negative and mixed
rules should be made mutually exclusive at the same time, because a win in one
direction and loss or tie in the other currently satisfies both descriptions.

## Review of the remaining required concerns

- **Paper value and one-RQ fit:** This is a genuine RQ3 accuracy experiment. It
  adds a cross-domain calibration test not supplied by the in-domain Step 0030
  fit, and either outcome changes whether percentile calibration should become
  the grouped-reference interface. It does not change the RQ or test an
  independent lifecycle question.
- **Empirical-CDF mathematics:** The occurrence-weighted, right-continuous
  definition using `<=`, followed by the target continuation rule using `>=`,
  is explicit, monotone, and directionally consistent with higher NPMI meaning
  recurrence. Discrete ties are handled deterministically. Unseen pairs remain
  boundaries. This is a valid candidate normalization; no mathematical blocker
  was found.
- **Bidirectional information fairness:** Within each transfer direction, the
  percentile candidate and raw-cutoff comparison receive the same source group
  labels, target visible actions, target unlabeled reference population, and
  scalar-decision budget. The two directions have unequal source-population
  sizes and different reference construction, but they are reported as two
  separate target results rather than pooled, so this does not invalidate the
  comparisons.
- **Target-label separation:** The run-time separation is adequate: target
  CDFs use only visible transitions, predictions are persisted before target
  groups/stages are loaded, and the population and assignment checks cover both
  targets. The plan also honestly records that these datasets and their prior
  outcomes motivated the candidate. Consequently, even a positive result is
  locked, post-hoc mechanism-development evidence on reused populations, not
  untouched target-blind or unseen-family confirmation. The phrase “stronger
  unseen-family result” and the `decisive` role overstate that independence;
  this scope correction is important for reporting but does not require a new
  workload to execute the stated experiment.
- **Baseline and ablation:** Label-free recurrence is a credible operational
  baseline for whether source annotations add target value. Direct raw-cutoff
  transfer is the strongest equal-information mechanism comparison and the
  positive rule correctly requires beating it. Calling it an ablation rather
  than a second main baseline does not invalidate the matrix, provided result
  review audits it as the claim-critical equal-information comparison. The
  per-domain calibrated row is correctly labeled a higher-information upper
  bound.
- **B$^3$ and bootstrap:** Operation-weighted B$^3$ is claim-matched and
  boundary F1 is properly secondary. Session is the right resampling unit, and
  fold/framework stratification preserves the evaluation structure. For exact
  reproducibility, the implementation should recompute pooled B$^3$ from
  resampled per-session sufficient statistics or give duplicated sessions
  replica-unique group identifiers, and the plan should name the interval
  construction. These details are straightforward; only the absent uncertainty
  decision rule above blocks approval.
- **Completion and executability:** The command, real preflight, complete
  populations, planned cells, seed, output paths, correctness checks, recovery
  point, and terminal artifact rule are concrete. Conditional Rust replay is
  predeclared and cannot select the scientific Python outcome. No additional
  baseline, workload, or implementation review is required.

plan status: REVISE

## Round 2 Follow-Up

The sole Round 1 blocker is closed. The revised plan defines empirical
2.5th--97.5th percentile intervals from 10,000 paired, stratified
target-session bootstrap draws and makes them part of the decision rule while
retaining complete-population B$^3$ deltas as the primary estimates. A positive
result now requires nonnegative interval lower bounds against label-free in
both targets and strictly positive lower bounds against raw transfer in both
targets. When the point ordering passes but an interval does not support the
required relation, the result is inconclusive rather than positive.

The interpretation rules are now ordered and mutually exclusive: positive is
tested first, cross-target sign disagreement is mixed, a point-ordering win
without interval support is inconclusive, and only a consistent failure across
both targets is contradictory. This prevents the same bidirectional outcome
from being classified as both mixed and contradictory. In implementation,
“crosses the claim-relevant zero boundary” should include an interval that
touches zero when the corresponding positive rule requires a strictly positive
lower bound; this follows directly from the stated positive predicate and does
not require a plan revision.

The reporting scope is also corrected. The planned role is now supporting RQ3
mechanism/generalization evidence, the target populations are explicitly
described as complete reused populations, and the known-deviation statement
rules out presenting the result as untouched independent confirmation. No
previously approved workload, baseline, metric, information budget, or
execution condition was reopened.

plan status: PASS
