# Round 08: Terminology And Claim Tone

Skills: `check-terminology-infoflow` and `paper-writing-style` claim-tone rules
Reviewer mode: independent read-only subagent

## Reviewer Findings

### Must-fix

1. Several implementation and evaluation sentences still used completed-work
   tense although every RQ remains unanswered.
2. Verification action and vendor/model/session identity needed formal
   definitions and explicit non-authorship scope.
3. Eligibility, candidate ambiguity, event-side unmatched, and Git-side
   unmatched states were conflated.
4. Current-tree survival was described as recorded rather than derived.
5. RQ2 drifted among behavior, structure, predictors, agents, sessions,
   vendors, and model labels.
6. RQ4 promised interpretability from days to months rather than operationally
   defined navigation over tested ranges.
7. Endpoint survival was incorrectly described as validating an association.

### Should-fix

The reviewer found provenance/lineage drift, defensive core/supporting-view
disclaimers, undefined touch language, BOOTSTRAP vocabulary in paper prose, and
inconsistent Git-baseline labels.

### Consider

The RQ titles could expose their constructs, and negative novelty disclaimers
could become positive scope statements.

## Root Decisions And Applied Fixes

- Converted all remaining planned implementation and evaluation actions to
  future tense and made the third contribution an evaluation plan.
- Defined verification action as a recorded check, not verified code. Defined
  vendor, recorded model label, and native session identifier as source-
  configuration fields rather than people or Git authors.
- Defined association eligibility, multiple ambiguous candidates, no matched
  Git change, and Git-side unmatched changes separately. Defined endpoint
  survival as a current-tree endpoint rather than time-to-event survival.
- Recast RQ2 around replication across held-out sessions, vendors, and recorded
  model labels. Recast RQ4 around responsive, accurate navigation over tested
  ranges.
- Replaced provenance with path/line lineage or attribution as appropriate.
  Replaced touch with recorded path reference and standardized the RQ3 baseline
  as a strong reproducible Git-only visualization baseline.
- Reframed related-work disclaimers as positive scope and separated endpoint
  survival outcomes from RQ1 association/lineage validation.

## Meaning And Evidence Check

The refinements narrow tone to current BOOTSTRAP status and make constructs
operational. They preserve the central three-layer thesis and do not remove any
requested gallery family. No result, implementation completion, authorship,
causality, correctness, or generality claim was added.

## Verification

`make -C docs/paper` completed successfully and produced a six-page PDF. The
cumulative snapshot diff contains 431 insertions and 163 deletions. Targeted
searches found no remaining provenance, touch, unsupported duration-
interpretability, inconsistent Git-baseline, present-tense evaluation, or
survival-as-validation wording.
