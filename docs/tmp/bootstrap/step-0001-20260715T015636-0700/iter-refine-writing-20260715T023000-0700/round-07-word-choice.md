# Round 07: Word Choice

Skill: `paper-writing-style`, word-choice pass
Reviewer mode: independent read-only subagent

## Reviewer Findings

### Must-fix

The reviewer found five semantic word-choice errors: histories cannot exceed
“attention,” RQ3 cannot “improve time,” repositories are not themselves multi-
day, and an artifact cannot be compared directly with data volumes.

### Should-fix

The reviewer identified eleven verbose, imprecise, or project-report phrases,
including “assume commits,” “spatial frame that does not move,” “bound work,”
“literature-level position comparison,” “Our delta,” and “first-of-kind.”

### Consider

Six small intensifier or diction cuts were proposed for ground truth, design,
schema, predictors, scale dimensions, and survival positioning.

## Root Decisions And Applied Fixes

Applied all Must-fix, Should-fix, and Consider replacements. RQ3 now explicitly
targets higher accuracy and lower completion time. Evaluation now uses multi-day
repository histories and compares browser performance across data volumes.
Process and scale nouns now name their actual constructs.

## Meaning And Evidence Check

No metric, evidence layer, association status, hypothesis, or claim boundary
changed. Removing “strong” from RECAP's ground-truth description avoids an
unmeasured comparison while preserving its favorable local-capture tradeoff.

## Verification

`make -C docs/paper` completed successfully and produced a six-page PDF. The
cumulative snapshot diff contains 411 insertions and 158 deletions. Only
underfull-box diagnostics remain.
