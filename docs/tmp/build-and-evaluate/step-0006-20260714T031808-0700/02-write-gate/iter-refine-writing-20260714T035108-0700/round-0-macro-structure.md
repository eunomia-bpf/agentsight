# Round 0 — Macro Structure

## Node record

- Started: 2026-07-14T03:51:08-07:00
- Completed: 2026-07-14T03:56:29-07:00
- Cycle/gate: Step 0006 / WRITE
- Parent: RQ3 evidence synchronization
- Reviewer: independent read-only subagent using
  `check-paper-structure-flow`, Level 1
- Entry paper: eight-page AAAI 2027 paper after RQ3 evidence sync

## Objective and method

Review the complete paper for full-paper section order, design versus
implementation separation, architecture placement, explicit two-to-five RQ
organization, balance, and the placement of the new RQ3 evidence. The reviewer
adapted full-paper conventions to the fixed eight-page AAAI format. Thesis,
four RQs, numbers, and scientific meaning were read-only.

## Raw findings

### Must-fix

1. Evaluation lacked a complete RQ1--RQ4 overview before entering the evidence
   blocks.
2. RQ3's boundary result answers only one component of its fixed
   task/phase/action/boundary hypothesis; the other components remain a
   scientific evidence gap.
3. Design included concrete backend syntax and libraries while Implementation
   was only one short paragraph.
4. Evaluation had no limitations block.

### Should-fix

1. Move the architecture figure to the Design overview.
2. Change question-form RQ subsection titles to parallel noun phrases while
   preserving the exact questions in prose.
3. Add shared evaluation setup information.
4. Reduce RQ1 imbalance and use the space for Implementation, Limitations, and
   Related Work.

### Consider

The combined Background and Motivation section is appropriate for eight pages;
a separate Discussion section is optional; the new RQ3 table does not break the
page budget.

## Applied fixes

### Evaluation

- Added the exact four fixed paper-level RQs before the evidence blocks.
- Renamed the four evidence subsections to the parallel noun phrases Resource
  Attribution, Problem Correspondence, Tag Accuracy, and Profiling Cost.
- Added the exact question at the beginning of each RQ block.
- Added a compact Scope and Limitations subsection after RQ4. It states the
  offline evaluation boundary and honestly identifies the remaining matched
  task/phase/action evidence without including negative experiment results.

### Design and Implementation

- Moved the architecture figure immediately after the Design overview and
  four-stage pipeline.
- Kept Design at the interface/property level: pluggable field derivation,
  ordinary operation fields, direct versus induced stack construction, and
  variable-depth grouping.
- Moved regex syntax, local-model mechanism, TF-IDF/K-Means details, mapping
  example, and concrete adjacent-boundary score inputs into Implementation.
- Split Implementation into Input Reconstruction, Field Derivation and
  Boundaries, and Profile Export paragraphs while preserving all mechanisms,
  values, and citations.

## Rejected or deferred findings

- **Complete RQ3 closure:** not writable. The fixed RQ and hypothesis remain
  unchanged, and the paper now explicitly preserves the task/phase/action
  evidence gap for a later EXPERIMENT gate. No result was invented.
- **Shared setup paragraph:** deferred because the four RQs intentionally use
  heterogeneous local trajectories, public benchmark protocols, and cost
  measurements. A generic hardware/setup paragraph would falsely imply a
  common experimental protocol; each RQ retains its specific setup.
- **Compress RQ1 now:** rejected for this round because the reviewer identified
  no redundant technical statement whose removal was safe, the paper remains
  within eight pages, and deleting evidence would violate the nothing-lost
  rule. Later micro/flow rounds may identify specific repetition.
- **Separate Discussion:** not added; the reviewer considered it optional and
  no current content requires another section.

## Preservation and build checks

- exact thesis: unchanged;
- RQ count and meanings: four, unchanged;
- new scientific claims or numbers: none in this round;
- citation commands: 47 before and after;
- technical content: moved, not removed;
- compilation: `make -C docs/paper` PASS after each subsection-sized edit;
- final page count: eight;
- undefined citations/references: none;
- overfull boxes: none.

## Remaining concern and next node

RQ3 is not submission-complete until task, phase, and action identity receive
matched evidence. That is an EXPERIMENT decision, not a writing edit. Continue
to Round 1 micro structure without changing the RQ or story.
