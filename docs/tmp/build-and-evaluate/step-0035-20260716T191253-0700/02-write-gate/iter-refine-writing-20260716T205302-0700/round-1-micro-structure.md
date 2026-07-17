# Round 1 — Micro Structure

**Started:** 2026-07-16T21:04:00-07:00

**Completed:** 2026-07-16T21:22:25-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Objective:** Repair paragraph roles, section-local evidence order, and direct
RQ answers after a complete-paper Level-2/Level-3 review, without changing the
fixed thesis, four RQs, algorithm, quantitative evidence, or canonical
submodule.

## Inputs and Review Scope

The independent reviewer read the complete LaTeX source and rendered PDF. It
used `check-paper-structure-flow` at paragraph-role and sentence-flow levels.
The review also incorporated the immediately following metric audit: ordinary
B-cubed and MAP are the reader-facing standard primary metrics; token-weighted
B-cubed and fixed-reader outcomes are supporting analyses rather than new
community-standard metrics.

The reviewer performed no edit and no Git operation.

## Raw Reviewer Findings

### Must-fix

1. The abstract and Introduction did not follow one clean causal chain. They
   previewed profiling as the solution before explaining why conventional
   profiling does not transfer, and placed the existing-tool gap before the
   structural cause.
2. Figure 1 could split the central thesis/model paragraph in the rendered PDF,
   separating the operation-stack definition from its completion.
3. Evaluation tables could render outside the evidence block that introduced
   them. In the prior PDF, RQ2/RQ3 material was interleaved at page boundaries
   and the RQ4 table could appear below later sections.
4. RQ3 still promises literal phase-label accuracy without direct evidence.
   This is a scientific gap, not a writing defect.

### Should-fix

1. Separate the AgentProf mechanism paragraph from the empirical-results
   paragraph in the Introduction.
2. Make each contribution lead with the deliverable or empirical finding and
   point to the responsible section.
3. Make the three Evaluation data classes parallel and bind each class to its
   RQ consumers.
4. Move the HINTBench snapshot detail from the global setup into RQ2.
5. End RQ2 and RQ4 with direct answers containing their headline evidence.
6. Split operation-stack projection semantics from selectable view/weight
   semantics.
7. Replace ambiguous algorithm referents such as `same calibration` and `the
   refinement` with the exact two-means procedure and cross-action cutoff.
8. Separate RQ1 and RQ3 scope limitations.

## Applied Fixes

### Abstract and Introduction

- Reordered the argument to context, developer problem, structural profiling
  mismatch, existing-tool gap, fixed thesis, model, system, evidence, and
  contributions.
- Preserved the exact thesis: **Agent observability needs profiling, not only
  debugging.**
- Split system mechanisms from results so one paragraph no longer performs two
  roles.
- Rewrote the contribution list as model, system, and empirical findings, with
  explicit references to Background/Design, Implementation, and Evaluation.
- Moved Figure 1 after the completed contribution list. The rendered figure no
  longer interrupts the thesis or operation-stack definition.
- Reduced the abstract from 256 to approximately 233 mechanically counted
  words while retaining RQ1--RQ4 headline evidence.

### Evaluation Organization

- Recast the global dataset description as three parallel classes: real
  histories, annotated public trajectories, and public problem-localization
  benchmarks, with RQ ownership stated inline.
- Moved the 629/536/80 HINTBench snapshot explanation into RQ2.
- Clarified ordinary B-cubed as a standard **partition-agreement** metric, not a
  purported standard resource-attribution metric. Token-weighted B-cubed stays
  explicitly secondary.
- Kept MAP as the sole RQ2 reader-facing primary metric over all three complete
  public localization workloads.
- Removed the custom Work-at-recall curve and mixed per-task reader-work table
  from the reader paper. Their complete audited results remain in
  `docs/evaluation.md` and the Step 0033 artifacts. The main paper retains the
  positive rank-hidden reader recall/precision synthesis as one supporting
  sentence.
- Rewrote the RQ2 close to answer the fixed question directly: against the
  matched raw-action view, semantic profiles rank independently annotated
  problems earlier on all three complete benchmarks.
- Rewrote the RQ4 close to repeat 27,765 operations, 1.17 seconds, 464.5 MiB,
  18.2% time, and 1.3% memory.
- Made all four evaluation tables non-floating evidence blocks. The rendered
  two-column reading order now places every table after its RQ protocol and
  before that RQ's closing interpretation.

### Design and Implementation Flow

- Split the operation-stack projection/hierarchy paragraph from the selectable
  view/weight definition.
- Renamed `Field derivation and boundaries` to `Field derivation` because the
  following paragraph independently owns boundary construction.
- Replaced `same calibration` with the repeated two-means procedure and `the
  refinement` with the cross-action cutoff.
- Split RQ1 and RQ3 limitations into separate paragraphs.

## Deferred Scientific Fix

Literal phase-label accuracy remains outside the current evidence while RQ3 is
fixed and explicitly includes phase. This round did not narrow RQ3, alter the
positive hypothesis, reinterpret boundary agreement as label-name accuracy, or
invent evidence. The gap remains an outer EXPERIMENT decision after the writing
cycle.

## Verification

- `make` completes under the official `aaai2027` style.
- Final PDF: 9 letter-size pages; main content ends on page 7 and references
  continue through pages 8--9.
- The log has no undefined citation/reference, LaTeX warning, overfull box, or
  compilation error.
- `git diff --check` passes.
- Entry and current citation sets are identical at 52 unique keys.
- The exact fixed thesis occurs in the abstract, Introduction, and Conclusion.
- The four fixed RQ strings remain unchanged.
- No experimental number was recomputed or changed in this writing round.
- `docs/agentpprof-paper` remains at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c` and clean.

## Next Node

Proceed serially to Round 2, reviewing section conventions and paper-level
role completeness. The phase-label evidence gap remains recorded for the outer
research loop rather than being hidden by prose.
