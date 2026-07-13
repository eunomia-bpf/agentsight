# Round 8 — Terminology And Claim Tone

**Started:** 2026-07-12T15:27:00-07:00  
**Completed:** 2026-07-12T15:42:56-07:00  
**Cycle/gate:** cycle 0001 / WRITE  
**Reviewer:** fresh read-only subagent using complete
`check-terminology-infoflow` and `paper-writing-style` procedures  
**Paper:** `docs/paper/main.tex`

## Concept Inventory And Review Scope

The reviewer read the complete project instructions, verbatim user prompts,
idea story, paper, and canonical design, implementation, evaluation, and
literature frontiers. It built a concept inventory and term-frequency audit,
then checked invented jargon, definition order, synonym drift, overloaded
terms, claim tone, self-attacking prose, and project-report vocabulary. It did
not edit, compile, run Git, or propose experiments as prose fixes.

The inventory confirmed two genuine coined core abstractions:

1. an `operation`, a fielded weighted observation;
2. an `operation stack`, an ordered path used to aggregate a measure.

`stack constructor` and the formal projection parameters are supporting
notation, not additional contributions. `flat`, `source-native`, and semantic
projections are alternatives over the same two abstractions.

## Findings And Applied Fixes

The reviewer returned twelve Must-fix, ten Should-fix, and five Consider
findings. The root applied all 27 groups.

The Introduction now defines semantic axes as task, phase, action-family, or
effect fields and defines responsibility as accounting ownership rather than
causation. It defines an operation stack as an ordered query-time path rather
than conflating it with the full query/measure configuration. The formal Design
now calls $(\varphi,C,w)$ an `operation-stack projection`, uses `projection`
consistently for that object, and states how a derived semantic field may apply
to downstream effects only when the source records the relation.

The Abstract explains the three projection choices in reader language before
using them. Design no longer calls elapsed-to-next-event time an operation
duration. RQ1 lists all four tested projections, calls the flat baseline the
no-tag projection, and removes the one-off `sanitized` and `null p95` terms.
RQ3 uses `dataset-provided action annotations`, not `native annotations`, so it
cannot be confused with a source-native execution hierarchy.

The Hodoscope setup expands farthest-point sampling before `FPS`, states that
the nested hierarchy is fit on four non-iQuest cohorts and applied to iQuest,
and distinguishes benchmark-provided turn grouping from a genuine execution
hierarchy. Calculator-style difference labels were rewritten as direct method
comparisons without changing $+22.0$, $-30.5$, $-11.9$, $+73.3$, their
intervals, or the zero-win result.

Claim tone now leads with what each experiment establishes and which
hypothesis it rejects. Internal phrases such as `boundary`, `deployable`,
`materialize`, `debug study`, and `fresh calls` were replaced with
reader-facing descriptions. Scope-bearing negative evidence remains intact.
Related Work positions the contribution against precedents rather than arguing
with a hypothetical reviewer.

All Consider findings were accepted after source checks. The 35,136 calls are
now identified as uncached llama.cpp tagger calls. The five boundary
configurations are named as two OSWorld-Human variants, AgentNet correctness
and redundancy, and AgentRewardBench looping. Output-tool compatibility is
stated directly without explanatory parentheticals.

## Format Repair And Preservation

The definition fixes initially pushed the Conclusion into page 8. The root
compressed redundant Discussion, Related Work, and Conclusion wording while
preserving all citations, comparisons, negative results, open evidence, and
the broad cost/regression/safety/failure/waste scope. No experiment or
contribution was removed.

- `make` completes with exit code 0.
- The PDF is nine US-Letter pages.
- All technical content, including the complete Conclusion, ends on page 7;
  References begin on page 8.
- The Abstract is exactly 250 words.
- Citation-command count remains 57.
- The exact author-fixed thesis remains verbatim in Abstract, Introduction,
  and Conclusion.
- No rendered semicolon, undefined citation/reference, or fatal LaTeX error
  remains.
- All RQ meanings, numbers, uncertainty intervals, and evidence-bearing
  qualifiers are preserved.

## Next Node

Round 9 performs a full information-flow pass over topic position, old-to-new
threads, paragraph transitions, and register consistency. It may tighten local
transitions but cannot alter scientific meaning or consume the open experiment
gaps through prose.
