# Round 6: Language — Sentence Structure

## Node identity

- **Started:** 2026-07-11 23:48:02 -0700
- **Completed:** 2026-07-12 00:09:40 -0700
- **Cycle/Gate:** `cycle-0001-20260711T164850-0700` / `WRITE_GATE`
- **Parent:** `round-5-consistency.md` (`PASS`)
- **Entry paper:** 9 pages; seven content pages; References begins page 8
- **Entry invariants:** four fixed RQs; three target contributions; 59 citation commands

## Objective and method

A fresh read-only subagent was instructed to invoke `paper-writing-style` on
the complete paper with focus only on sentence structure: independent-clause
semicolons, fragments, long subject--verb separation, weak openings, colons
before unlabeled lists, dangling modifiers, note-like runs, and structurally
ambiguous referents. Numbers, citations, math, RQ meanings, contributions,
implemented/proposed status, and scope-bearing hedges are read-only.

## Findings, decisions, and completion evidence

The first reviewer failed to return after a complete-paper scan and was
interrupted without producing findings. A fresh retry reviewer read the same
skill and complete paper under a bounded output contract. It returned three
Must-fix, ten grouped Should-fix, and two Consider findings.

### Must-fix findings and edits

1. The two Setup data descriptions were label-plus-noun fragments. They now
   use finite verbs: the real trajectories `comprise` 325 trajectories and
   `contain` 183,714 observations; the public trajectories `comprise` 15
   mapping/coverage families plus the separately described held-out families.
2. The RQ dependency paragraph used `they` without a grammatical plural
   antecedent. It now states that the central thesis requires the joint
   RQ2+RQ3+RQ4 result grounded by RQ1, and that the four RQs together provide
   Contribution 3's characterization.
3. RQ4 attached `repeated`, `reporting`, and `followed` ambiguously to one
   release run. It now requires complete runs across scales under repeated cold
   and warm conditions, explicitly assigns metric reporting to those runs, and
   then requires the two budget/outcome comparisons.

### Should-fix findings and edits

- Replaced all independent-clause semicolon splices in the Abstract,
  Introduction, Background, Design, Implementation-facing explanations,
  Evaluation, Related Work, and Conclusion. The two remaining English-source
  semicolons occur only inside explicit parenthetical enumerations, where the
  skill permits them.
- Removed the only prose em-dash pair by making the example parenthetical with
  commas.
- Replaced explanatory colons with causal wording or periods. Retained colons
  only for titles, LaTeX labels, displayed definitions, and explicit labeled or
  numbered lists.
- Converted unlabeled lists into `including`, `comprising`, or explicit
  `(1)`--`(n)` enumerations. This affected lower-layer system effects, the
  traditional profiling pipeline, the formal view tuple, built-in views,
  held-out RQ2 families, and the Conclusion's substrate inventory.
- Replaced the weak `This is distinct` opening with `Diagnostic correspondence
  is distinct`, and made the reusable-scope claim's subject explicit.
- Reconnected the RQ2 and RQ3 unanswered-evidence paragraphs so their required
  tests and reports read as scientific obligations rather than project notes or
  imperative fragments.

### Consider decisions

Both Consider findings were applied. The long Introduction workload sentence
was split so an activity, rather than an ambiguous system/agent, runs for hours
or days. The query-time attribution sentence was split after its list so the
final conjunction cannot be read as another list item.

The initial focused recheck found three weak or ambiguous openings introduced
by mechanical splits. They were repaired by naming the profiler's cross-run
claim, the taxonomy-seeded rule generator, and the debug-build study. The final
recheck returned `PASS` with no fragment, lowercase sentence start, semicolon
splice, prose em dash, disallowed colon, weak referent, or note-like directive
run remaining.

Counting each original English prose or caption sentence once, this round
changed 82 sentences. It changed sentence structure and punctuation only. No
number, citation, RQ meaning, contribution, equation, mechanism status, or
scope-bearing hedge changed.

A fresh `make` and final `pdflatex` pass produced a 9-page PDF with seven
content pages and References beginning on page 8. The paper retains 59 citation
commands and four RQ subsections; the final log has no undefined citation or
reference. The same two pre-existing overfull boxes remain for later local
language/layout repair. The `docs/agentpprof-paper/` submodule was untouched,
and this writing round performed no Git operation.

Round 7 next checks word choice, jargon inflation at the lexical level,
nominalizations, vague referents, stacked hedges, and verbose phrases while
preserving every scientific invariant above.
