# Round 7 — Word Choice

**Started:** 2026-07-12T15:24:00-07:00  
**Completed:** 2026-07-12T15:26:36-07:00  
**Cycle/gate:** cycle 0001 / WRITE  
**Reviewer:** fresh read-only subagent using the complete
`paper-writing-style` skill  
**Paper:** `docs/paper/main.tex`

## Review Scope

The reviewer read the complete project instructions, verbatim user prompt log,
idea story, and paper. It checked word choice, nominalization, vague referents,
compound-term density, redundant hedging, verbose phrases, unnecessary
adverbs, and project-report language. It preserved statistical uses of
“significantly,” all scope-bearing qualifiers, the exact thesis, RQs, numbers,
citations, and negative results. It did not edit, compile, or run Git.

## Findings And Disposition

The pass returned ten Must-fix, twenty Should-fix, and seven Consider findings.
The root applied all 37 findings in subsection-sized edits.

The highest-value change removed internal workflow vocabulary from the paper.
`admitted result`, `pinned script`, `in this run`, `artifact operation`,
`profiling-native condition`, `recursive-positive rule`, `substrate`, and
`comparison assets` were replaced by the actual scientific objects: held-out
experiment, released protocol, implementation behavior, directly recorded
additive change, prespecified hypothesis, and evaluation comparison. This
improves conceptual economy without removing any evidence or mechanism.

Ambiguous objects were also made concrete. Inspection now scatters *evidence*,
the current evaluation verifies retention of declared source fields, separate
timings do not support an end-to-end estimate, and the AgentRx/TELBench test asks
whether projection choice affects localization. The Hodoscope text now says
that its released Table 2 protocol was reproduced and that its end-to-end
density-gap/FPS method beat the tested hierarchical method; it does not imply
that flatness caused the result.

All Consider suggestions were accepted because they removed compound labels
without changing meaning: learned priors became models learned across
trajectories, intent-effect cycles became cycles from intent to system effect,
exploratory accounting became exploratory analysis, the flat-view definition
now uses a manual constructor with one frame, the 30% budget is stated directly,
the Discussion no longer calls semantic recursion “authority,” and the
Conclusion uses a model with two abstractions.

The reviewer found no banned verbose template phrase, empty intensifier,
redundant hedge stack, hardcoded rendered system name, or generic
nominalization requiring removal.

## Preservation And Build Evidence

- The exact thesis remains verbatim three times.
- The three RQs, all numbers, 57 citation commands, confidence intervals,
  qualifiers, and unresolved-result statements are unchanged in meaning.
- `make` completed with exit code 0.
- The PDF remains nine US-Letter pages; Conclusion ends on page 7 and
  References begin on page 7 before continuing on pages 8--9, so all technical
  content remains within the seven-page limit.
- There are no undefined citations/references or fatal LaTeX errors.

## Next Node

Round 8 audits terminology, concept consistency, and claim tone. It must reject
new names and scope drift, preserve the exact thesis, and keep evidence-bearing
hedges while removing apologies or defensive project-report prose.
