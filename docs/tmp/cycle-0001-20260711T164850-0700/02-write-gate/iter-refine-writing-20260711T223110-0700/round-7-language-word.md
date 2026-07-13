# Round 7: Language — Word Choice

## Node identity

- **Started:** 2026-07-12 00:10:46 -0700
- **Completed:** 2026-07-12 00:20:35 -0700
- **Cycle/Gate:** `cycle-0001-20260711T164850-0700` / `WRITE_GATE`
- **Parent:** `round-6-language-sentence.md` (`PASS`)
- **Entry paper:** 9 pages; seven content pages; References begins page 8
- **Entry invariants:** four fixed RQs; three target contributions; 59 citation commands

## Objective and method

A fresh read-only subagent was instructed to invoke `paper-writing-style` on
the complete current paper with focus on word choice: verbose phrases,
nominalizations, vague referents, stacked hedges, unnecessary adverbs, inflated
compounds that have plain equivalents, and project-report diction. The full
terminology/invented-term audit is reserved for Round 8. Scientific claims,
numbers, citations, RQs, contributions, formal terms, implementation status,
math, and scope-bearing hedges are read-only.

## Findings, decisions, and completion evidence

The reviewer returned three Must-fix, seventeen Should-fix, and one additional
Consider finding. All were applied with the scientific layer held fixed.

### Must-fix changes

- Rewrote the repeated `under ... under which` responsibility definition and
  replaced ambiguous `it` with `the operation`.
- Named the RQ1 permutation test as the subject that treats expanded
  system-effect weights as statistical units.
- Clarified the RQ2 freeze contract: one vocabulary and one navigator are
  shared across outcomes, while each risk function is frozen before target
  labels are exposed.

### Should-fix changes

- Replaced `instantiates ... substrate with` in both Abstract and Introduction
  with the direct `implements ... by producing/turning` construction.
- Replaced avoidable nominalizations in the Introduction and Background,
  including `analysis and evaluation`, `attributes ... by aggregation`, and
  `as distinct from`.
- Replaced vague or project-status wording such as `not straightforward`,
  `missing research question`, `implemented boundary`, `admitted evidence`,
  `submission-ready`, `prerequisite controls`, and `RQ blocks` with direct
  scientific subjects and verbs.
- Made Design prose concrete: operations are represented uniformly; raw
  strings are matched; declared inspection budgets are allocated; all tree
  constructors feed the same navigator; and the central prediction concerns
  the complete method. `Declared inspection budgets` was chosen instead of
  the reviewer's singular `fixed inspection budget` to preserve the formal
  operation and token budgets.
- Replaced heavy RQ4 wording with `capture full profiling cost` and `a scaling
  study of release builds` while preserving every measurement limitation.
- Made the Introduction contribution lead direct (`We target...`) without
  converting incomplete target contributions into achieved claims.

### Consider and recheck

The view list now ends with `a hierarchy based on the dataset's own
annotations`, parallel to the other hierarchy/view types. The first focused
recheck found three edit-induced repetitions (`answers ... from`, consecutive
`result`, and `measurements ... measure`); all were repaired. The final
independent recheck returned `PASS`.

Counting each original English prose sentence once, this round changed 31
sentences. No number, citation, RQ meaning, contribution scope, formal term,
math expression, implementation boundary, or scope-bearing hedge changed.

A fresh `make` and final `pdflatex` pass produced a 9-page PDF with seven
content pages and References beginning on page 8. The source retains 59
citation commands and four RQ subsections; the log contains no undefined
citation or reference. The same two existing overfull boxes remain. The
submodule and protected project-memory changes were untouched, and this round
performed no Git operation.

Round 8 next performs the dedicated terminology, invented-jargon, definition
order, synonym-drift, and claim-tone audit.
