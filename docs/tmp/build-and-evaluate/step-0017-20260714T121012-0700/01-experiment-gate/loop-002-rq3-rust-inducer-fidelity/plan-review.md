# Experiment Plan Reviews

## Round 1

- Reviewer: independent subagent using `research-experiment-design`
- Verdict: **REVISE**
- Must-fix findings:
  1. Fix the exact complexity penalty, acceptance inequality, tie-breaks, and
     disposition of every legacy gate before looking at labels.
  2. Guarantee that every accepted split creates two distinct reconstructable
     child paths; repeated labels must not make a split invisible.
  3. Add an explicit candidate test/release build and verify the matched runtime
     configuration.
  4. Do not claim that unit-weight OSWorld-Human isolates the benefit of
     resource weighting.
- Resolution: the plan now fixes `ln(n)/(2n)`, removes the legacy acceptance
  gates and score terms, specifies deterministic tie-breaking and unconditional
  child-frame append, adds candidate tests/build/config checks, and narrows only
  the empirical interpretation of this experiment—not the thesis, RQ3, or the
  algorithmic resource-weighting property.

## Round 2

- Reviewer: fresh independent subagent using `research-experiment-design`
- Verdict: **REVISE**
- Must-fix findings:
  1. Replay old and revised paths with their different duplicate-frame
     semantics, consume every decision, match Rust stack mass, and define
     boundaries/partitions from reconstructed final paths.
  2. Define query relevance and tie order exactly, or remove the query tie-break.
- Resolution: the plan now requires method-specific replay and fixes query
  relevance to the existing lowercase substring-coverage function, with exact
  primary-field and cut tie orders. Neither item changes the numeric objective,
  dataset, metrics, thesis, or RQ3.

## Round 3

- Reviewer: fresh independent subagent using `research-experiment-design`
- Verdict: **APPROVE**
- Must-fix findings: none.
- Confirmed: the algorithm and penalty are fixed; old/new replay semantics are
  explicit; no OSWorld-Human label informs the candidate; the complete 287
  session run and commands are executable; and the thesis, two-object model,
  and four RQs remain unchanged.
