# Round 1 — Micro Structure

## Node record

- Started: 2026-07-14T03:56:29-07:00
- Completed: 2026-07-14T04:01:20-07:00
- Cycle/gate: Step 0006 / WRITE
- Parent: Round 0 macro structure
- Reviewer: fresh read-only subagent using `check-paper-structure-flow`,
  Levels 2--3
- Entry paper: Round 0 output, eight pages

## Objective and method

Review paragraph roles and internal flow across the complete paper, with
special attention to abstract/introduction correspondence, topic sentences,
one-idea paragraphs, and direct opening/closing answers for all four RQ blocks.
Claims, numbers, thesis, and RQ meanings were read-only.

## Raw findings

### Must-fix

1. RQ1 lacked a final sentence synthesizing its four existing evidence groups
   into a direct answer.
2. RQ3 closed only the boundary component without explicitly marking the full
   RQ as partially unanswered or naming its evidence TODO.
3. The abstract's thousands-to-millions interaction scale was not mirrored by
   the corresponding Introduction background paragraph.

### Should-fix

Improve the transition from the Introduction problem to profiling; split the
two Background challenges; separate Design rationale from pipeline overview;
separate Implementation field derivation from boundary construction; remove
repetition in the RQ3 opening; separate the two limitations; and separate the
two Related Work topic groups.

### Consider

Reorder Stack Construction so the no-user-fields need appears before the
automatic mechanism.

## Applied fixes

- Mirrored `thousands to millions of interactions` in Introduction paragraph
  1 without changing the abstract claim.
- Connected the Introduction problem directly to profiling as the required
  aggregation method.
- Split the two Background challenges into separate paragraphs.
- Split the Design requirement mapping from the four-stage pipeline overview.
- Added a separate Implementation paragraph for Boundary Construction.
- Added a direct RQ1 closing answer that synthesizes the existing separation,
  multi-resolution, multi-weight, and induction evidence.
- Replaced the repetitive RQ3 opening with one exact question and one
  relationship/protocol sentence.
- Added an explicit partial-answer sentence and matched
  task/phase/action evidence TODO at the end of RQ3.
- Split offline scope from the RQ3 evidence boundary in Limitations.
- Split agent observability from fault localization in Related Work.

## Rejected or deferred finding

The Stack Construction consider item was not applied. Its existing first
sentence already states the purpose (building an attribution hierarchy), the
next sentence handles the user-supplied case, and the automatic path follows
as the no-field-list case. Reordering would not materially improve the
why-before-what sequence.

## Preservation and build checks

- thesis: unchanged;
- four RQ meanings: unchanged;
- quantitative values: unchanged;
- citation commands: 47, unchanged from the WRITE entry;
- technical content: none removed;
- compilation after each subsection-sized group: PASS;
- page count: eight;
- undefined citations/references: none;
- overfull boxes: none.

## Remaining concern and next node

RQ3's declared evidence TODO is scientific and remains for the later outer
loop. Continue to Round 2 section conventions.
