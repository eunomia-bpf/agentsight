# Round 1 — Paragraph Roles and Sentence Flow

**Started:** 2026-07-19T23:51:37-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Objective:** audit paragraph roles and sentence-to-sentence information flow  
**Completed:** 2026-07-19T23:57:25-07:00  
**Status:** complete

## Read-only contract

- Exact thesis: **Agent observability needs profiling, not only debugging.**
- Exact RQs: attribution, problem correspondence, tag accuracy, and cost.
- Claims, numerical evidence, RQ meaning, and the canonical story are read-only.
- The Qwen semantic-stack negative trial remains experiment history and must not
  enter the paper.
- This round may repair only paragraph focus, transitions, referents, and local
  information order.

## Method

A fresh read-only reviewer applies Levels 2 and 3 of
`check-paper-structure-flow` to the complete post-Round-0 paper. Findings are
classified as Must-fix, Should-fix, and Passed. The root makes only minimal
meaning-preserving edits, compiles the paper, and checks the seven-content-page
and nine-total-page limits.

## Independent findings

The fresh reviewer found two must-fix information-flow defects: RQ1 called the
constructor “the RQ3 recurrence constructor,” creating a circular ownership
handoff, and RQ1's final paragraph inventoried tests rather than directly
answering its question. Three should-fix items concerned the referent “The
improvement,” the transition into built-in resource choices, and a one-sentence
OSWorld population paragraph separated from its protocol. All other paragraph
roles and sentence transitions passed, including the compressed synthesis,
scope, and conclusion.

## Fixes

- Changed “The RQ3 recurrence constructor” to “The recurrence constructor.”
- Rewrote the RQ1 closing sentence to answer that scoped joining preserves
  attributed effects, semantic partitions improve B-cubed over raw action, and
  selectable stacks and weights expose distinct views.
- Clarified “This improvement” and the built-in resource-choice transition.
- Joined the OSWorld population sentence to the predictor protocol paragraph.

No claim, number, RQ, citation, result ownership, or scientific qualifier
changed.

## Exit validation

- Official build: 9 pages; complete Conclusion on page 7; pages 8--9 references
  only.
- No undefined citation/reference or overfull box.
- Citation-command count remains 62.
- Exact thesis and four RQs remain unchanged.
- No writing/review Git operation was performed.
