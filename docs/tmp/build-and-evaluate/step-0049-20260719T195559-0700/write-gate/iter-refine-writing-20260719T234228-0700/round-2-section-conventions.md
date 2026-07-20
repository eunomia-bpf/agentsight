# Round 2 — Section Conventions

**Started:** 2026-07-19T23:57:51-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Objective:** audit venue-appropriate roles of every paper section  
**Completed:** 2026-07-20T00:02:38-07:00  
**Status:** complete

## Contract

The thesis, four RQs, scientific story, claims, evidence, citations, and
positive-only paper boundary are read-only. This round may repair only
section-role violations, local organization, and figure/table placement.

## Method

A fresh read-only reviewer applies the section conventions in
`check-paper-structure-flow` to the complete current paper. It separately
checks abstract, introduction, background/motivation, design, implementation,
the four RQ blocks, scope/limitations, related work, conclusion, and float
placement. The root accepts only minimal meaning-preserving fixes and then
revalidates build, page boundaries, citations, and references.

## Independent findings

The fresh reviewer found two must-fix convention defects. The abstract reported
all 1,629 concurrent controls rejected, while the corresponding Introduction
result omitted that clause. In the rendered PDF, the RQ4 cost table floated
before the RQ4 heading and protocol. The reviewer otherwise passed all
section-role conventions, exact RQ organization, Design/Implementation
separation, scope placement, topic-organized Related Work, and the one-paragraph
Conclusion.

## Fixes and decisions

- Added the already established “reject all 1,629 concurrent-control effects”
  clause to the Introduction result sentence.
- Changed only Table 4's ordinary float placement to `[h]`; visual inspection
  confirms that it now follows the RQ4 protocol and precedes the RQ4 result
  interpretation.
- Did not add optional prose cross-references or an extra Background-to-Design
  transition. Existing section labels and the opening Design mapping are clear,
  and extra text would consume the exact page budget without adding evidence.

## Exit validation

- Official build: 9 pages; complete Conclusion on page 7; pages 8--9 references
  only.
- Visual inspection: Table 4 is inside RQ4 after its protocol.
- No undefined citation/reference or overfull box.
- Citation-command count remains 62.
- Exact thesis, four RQs, claims, and numbers remain unchanged.
- No writing/review Git operation was performed.
