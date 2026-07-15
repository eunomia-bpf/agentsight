# Round 02: Section Conventions

Skill: `check-paper-structure-flow`, section-convention pass
Reviewer mode: independent read-only subagent

## Reviewer Findings

### Must-fix

1. The abstract was shorter than the full-paper convention and did not mirror
   the evaluation method preview in the introduction.
2. Background mixed substrate descriptions with argumentative motivation.
3. RQ4 promised interpretability but planned only performance measurements.
4. Related Work did not name the verified closest work despite correct topic
   grouping.

### Should-fix

The reviewer asked for the overview immediately after design goals, an explicit
G1--G4 to RQ map, RQ-specific baselines, and fewer top-level Design catalogue
subsections.

### Consider

The contribution list could eventually link to sections, and the conclusion
should state the supported thesis only after evidence exists.

## Root Decisions And Applied Fixes

- Expanded the abstract with method and metric previews without adding results,
  and mirrored the evaluation method in the introduction.
- Split neutral Background from an evidence-gap Motivation section.
- Added scale-sensitive navigation, recall, and crowding measures to RQ4.
- Named RECAP, Githru, recent trajectory work, `Will It Survive?`, and CLSA in
  Related Work while leaving exact citations for the citation-verification
  round.
- Moved the walkthrough directly after goals, mapped goals to RQs, grouped the
  visual families under decision-oriented projections and coordinated
  interaction, and made baseline assignments explicit.
- Deferred section references in the contribution list because the skeleton is
  still changing. Retained the evidence-safe conclusion placeholder.

## Meaning And Evidence Check

All additions describe planned methods or verified positioning. No study
outcome was inferred. The RQ4 change strengthens construct validity without
changing the question.

## Verification

`make -C docs/paper` completed successfully and produced a five-page PDF. The
cumulative snapshot diff contains 300 insertions and 126 deletions. Only
underfull-box diagnostics remain; no LaTeX error or unresolved cross-reference
warning remains after the second compiler pass.
