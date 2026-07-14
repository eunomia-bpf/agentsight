# Iterative Writing Round 0: Macro Structure

## Node

- Started: 2026-07-14T06:32:00-07:00
- Completed: 2026-07-14T06:41:00-07:00
- Cycle/gate: Step 0007 / WRITE
- Parent: root scientific disposition
- Objective: verify complete-paper macro structure after RQ1 source-lineage
  integration
- Entry paper SHA-256:
  `d91f2b03562993fb21a0732442a2b24c8d1e5130d058145847919f3e8b6693f7`
- Exit paper SHA-256:
  `75c78815cd29d2c695df844d9221bd24fc85802cb0c8727c8bb994f7b05298dc`

## Files and method

The independent read-only reviewer invoked `check-paper-structure-flow` in
Level-1 macro scope and read the complete `docs/paper/main.tex`,
`docs/user-instruction.md`, `docs/idea-story.md`, and Step 0007 scientific
disposition. The root applied accepted changes subsection by subsection and
compiled the complete paper.

## Raw findings

### Must-fix

1. The Evaluation opening said it “answers” all four questions although the
   RQ3 block explicitly establishes only its group-boundary component.
2. Design and Implementation advertised the automatic TF-IDF boundary backend,
   while RQ3 evaluates a supplied supervised boundary field and explicitly
   excludes that automatic backend.

### Should-fix

1. Clarify the AgentSight-to-AgentProf boundary exposed by the new RQ1 result.
2. Signpost RQ1's four evidence threads and move its problem-density AP/work
   material to RQ2.
3. Split the overloaded Design `Algorithms` subsection into requirement-aligned
   subsections.
4. Update the Introduction's evaluation contribution to include the new
   20-task lineage experiment and boundary evidence.

### Consider

1. Further separate Background from Motivation and move D1--D3 into Design.
2. Add a Discussion section if page balance permits.

## Applied fixes

- Replaced “answers four fixed paper-level questions” with “is organized by
  four fixed paper-level questions.” The four RQ texts and meanings are
  unchanged; RQ3 remains explicitly partial in its own evidence block and Scope.
- Documented that mappings or boundary predictors can supply an ordinary group
  field for direct projection, while the TF-IDF backend remains the automatic
  mode used only when neither fields nor groups are supplied. Implementation
  now states the same interface distinction. This aligns the evaluated field
  integration without claiming the supervised predictor is built into
  AgentProf.
- Updated Figure 2's caption and description: AgentSight supplies scoped
  cross-layer effects; AgentProf owns field derivation, stack construction,
  folding, and export. No new abstraction was introduced.
- Added RQ1 paragraph signposts for source lineage, semantic separation,
  granularity/weights, automatic exploration, and the cumulative answer.
- Moved the six-task AP/inspection result from RQ1 to RQ2 rather than deleting
  it. All values and technical content remain present: AP 0.276 versus 0.312
  and 65.3\% of flat inspection work.
- Reorganized Design into `Operations and Operation Stacks`, `Intent
  Attribution`, and `Stack Construction`, using existing content.
- Updated the evaluation contribution to mirror source lineage, 325 real
  trajectories, 15 public families, and three complete problem benchmarks.

## Rejected or deferred findings

- The combined Background and Motivation section remains. Its current
  subsections already separate neutral background, challenges, and explicit
  D1--D3 requirements; moving requirements would churn the restored canonical
  spine without improving the 7-page content budget.
- No Discussion section was added. The reviewer found the current section order
  sound and classified Discussion as optional; Scope and Limitations already
  carries the necessary scope statements.
- Missing RQ3 task/phase/action evidence is a scientific evidence need, not a
  writing-round authorization to change the fixed RQ or invent results. The
  paper now avoids the false global “answers” promise and retains the honest
  component-level answer.

## Preservation checks

- Four explicit RQs remain present with identical wording and meaning.
- Exact thesis sentence remains present three times.
- `\cite{}` command count remains 52.
- All pre-existing quantitative values remain in the paper; the RQ1 AP/work
  numbers were moved, not changed or removed.
- The new Step 0007 values remain unchanged.
- No core abstraction beyond operations and operation stacks was added.
- No Git command was run by the writing skill or reviewer.

## Compilation

- Command: `make` in `docs/paper/`
- Result: success
- PDF: 9 pages total, comprising 7 content pages and 2 reference pages
- Undefined citations/references: none
- Fatal LaTeX errors: none
- Exit PDF SHA-256:
  `2c03305c7db84c067785f16a368c38173f4df417beb4348b31d0687eb6e6dc31`

## Memory/tree and next node

No thesis, RQ, contribution, or story change occurred, so `docs/idea-story.md`
needs no Narrative Evolution entry. The next serial node is Round 1, complete
paper micro structure.
