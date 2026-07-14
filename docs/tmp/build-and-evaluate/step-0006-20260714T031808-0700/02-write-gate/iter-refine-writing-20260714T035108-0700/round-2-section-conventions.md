# Round 2 — Section Conventions

## Node record

- Started: 2026-07-14T04:01:20-07:00
- Completed: 2026-07-14T04:11:06-07:00
- Cycle/gate: Step 0006 / WRITE
- Parent: Round 1 micro structure
- Reviewer: fresh read-only subagent using
  `check-paper-structure-flow`, section-conventions focus
- Entry paper: Round 1 output, eight pages

## Objective and method

Check abstract and Introduction roles, Design requirements, the four-RQ
Evaluation opening and evidence blocks, Related Work grouping, Conclusion, and
the new RQ3 evidence against an eight-page AAAI full-paper structure. Thesis,
claims, RQ meanings, and numbers were read-only.

## Raw findings

### Must-fix

1. The new RQ3 result was absent from the abstract and Introduction.
2. The fixed thesis appeared explicitly only in the Conclusion.
3. Evaluation introduced data before the RQ set, and RQ4 lacked a minimal
   machine environment.
4. Related Work lacked a closest-mechanism profiling-labels/event-query topic.
5. Complete task/phase/action evidence remains a scientific submission blocker
   for RQ3 and cannot be repaired by prose.

### Should-fix

Consider challenge before existing-tool limitation in the Introduction; move
the RQ1 figure source close to its first reference; make the fault-localization
paragraph thematic rather than list-like; and explain cross-layer semantic
field propagation inside the operation model.

## Applied fixes

- Added the exact thesis to the abstract and Introduction insight paragraph.
- Added the same scoped RQ3 boundary result to the abstract and Introduction
  results paragraph, preserving the 287-task-instance scope and all four
  reported values.
- Moved the explicit RQ1--RQ4 set to the first Evaluation paragraph.
- Added the exact RQ4 measurement environment from the admitted Step 0005
  result: 24-core Intel Core Ultra 9 285K, 125 GiB RAM, Linux 6.15.11.
- Moved the RQ1 figure source immediately after the separation result.
- Added one Design sentence explaining how tool-triggered system-effect
  operations inherit semantic fields and fold under responsible intent.
- Added a profiling-label/event-query Related Work topic using already
  verified pprof, flame-graph, and Perfetto citations.
- Recast fault-localization work as a shared per-execution topic, then named
  representative systems and stated the cross-trajectory aggregation
  difference.

The added front-page and Related Work material initially produced nine pages.
To restore the fixed format without deleting evidence, the previously flagged
RQ1 repetition was tightened: all 13,265-operation grouping counts, all 15
families, 7/10 overlap, Spearman value, ranks, six induction tasks, group
counts, variable-depth count, AP values, and inspection-work value remain.

## Rejected or deferred findings

- **Swap Introduction challenge and existing-tools paragraphs:** rejected.
  Both sequences are conventional, and the current problem -> current tools ->
  structural challenge -> insight flow makes the comparison target explicit
  before explaining why it fails. Moving paragraphs would add churn without
  changing comprehension.
- **Process-mining/event-abstraction closest work:** deferred to the REVIEW
  gate's required external literature search. Writing may use existing verified
  sources but must not invent or add unverified citations.
- **Complete RQ3:** deferred to EXPERIMENT, with the honest TODO retained.

## Preservation and build checks

- abstract length: approximately 248 visible words, within 250;
- thesis and four RQs: unchanged;
- numbers: copied from admitted result sources or preserved exactly;
- citation commands: 49 versus 47 at WRITE entry; no citation key removed;
- technical evidence: tightened, not removed;
- compilation after each subsection-sized edit: PASS;
- page count: restored to eight;
- undefined citations/references: none;
- overfull boxes: none.

## Remaining concern and next node

RQ3 remains only partially answered. Continue to Round 3 logic flow; scientific
closure belongs to a later EXPERIMENT gate.
