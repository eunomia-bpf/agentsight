# Independent Experiment Plan Review — Round 1

**Completed:** 2026-07-15T06:15:00-07:00  
**Skill:** `research-experiment-design`  
**Mode:** independent and read-only  
**Verdict:** **REVISE**

## Must-Fix Finding

The proposed local-continuity comparison used `npmi - applied_cutoff`, but
neighboring edges can use different calibrations. On the retained
CodeTraceBench output, the global cutoff is `0.122991` and the action-changing
applied cutoff is `-0.055739`. Subtracting these different offsets can make an
edge with lower raw NPMI appear to have a higher margin than its neighbor. The
rule was therefore a local minimum of heterogeneous threshold margins, not a
local minimum of recurrence continuity, so its stated scientific rationale was
not valid.

The reviewer requires one bounded repair: retain Step 0024 threshold
eligibility, but compare the existing raw NPMI values for the local-minimum
test. The hypothesis, properties, fixtures, and Rust/Python equivalence contract
must use that same definition. No window, normalization, sweep, second
candidate, or target-label tuning may be added.

## Findings That Pass

- The retained evidence supports the narrower structural diagnosis: mixed-label
  action-pair types cover 91.2% of OSWorld-Human decisions and 99.7% of
  CodeTraceBench decisions, so pair identity alone cannot resolve
  occurrence-level ambiguity.
- Preserving same-action decisions is acceptable as the least-change scope
  inherited from Step 0024. It is not evidence that same-action occurrences
  lack contextual ambiguity.
- The reused complete populations, fixed Step 0024 baseline, two-population
  B-cubed verdict, scorer separation, full coverage, and Rust/Python equivalence
  contract are adequate.
- No additional dataset, benchmark, baseline family, feature, cutoff, sweep, or
  independent confirmation run is required for this post-hoc
  implementation-selection experiment.

## Disposition

The root accepts the must-fix finding. The plan is revised only to separate
threshold eligibility from the commensurate raw-NPMI local ordering, and is
returned for the second and final independent plan review before implementation.
