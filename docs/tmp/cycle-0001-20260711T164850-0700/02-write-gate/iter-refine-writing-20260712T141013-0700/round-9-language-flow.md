# Round 9 — Language Flow And Polish

**Started:** 2026-07-12T15:42:56-07:00  
**Completed:** 2026-07-12T15:52:18-07:00  
**Cycle/gate:** cycle 0001 / WRITE  
**Reviewer:** fresh read-only subagent using the complete
`paper-writing-style` flow procedure  
**Paper:** `docs/paper/main.tex`

## Review Scope

The reviewer read the complete paper and checked topic and stress position,
old-to-new information order, paragraph transitions, antecedents, and register
consistency. It also read the project instructions and preserved the exact
author-fixed thesis, RQ meanings, evidence, numbers, citations, and negative
results. It did not edit files, compile, run Git, or convert scientific gaps
into prose claims.

## Findings And Disposition

The reviewer returned two Must-fix, ten Should-fix, and three Consider
findings. The root applied both Must-fix findings and all ten Should-fix
findings.

The two Must-fix repairs removed an ambiguous Hodoscope comparison in Related
Work and replaced a positive-sounding unsupported summary with the actual
result: two tested conditions in which the projections do not improve
diagnosis.

The Should-fix repairs give `these questions` an explicit antecedent, introduce
CPU call stacks before operation stacks, lead the central prediction with its
scientific content, place the zero-weight normalization caveat after the
built-in measures, and give the induction process an explicit subject. The RQ
overview is now independently readable. The entropy, failure-localization, and
Hodoscope procedures state their purpose before notation or mechanics. The RQ3
result leads with the result rather than setup.

One Consider finding was applied: Discussion now explains why execution
nesting, behavior similarity, and profiling attribution must remain distinct.
The suggestion to introduce `agent-engineering` was rejected because it would
restore an unnecessary compound term removed in Round 7. The suggestion to
split the third contribution was rejected because the sentence remains
coherent and the split would consume scarce body space without improving its
scientific content.

## Format Repair And Preservation

The flow edits initially moved five Conclusion lines onto page 8. The root
compressed repeated Related Work and Conclusion wording while retaining every
citation family, closest-work distinction, Hodoscope comparison, negative
condition, open evidence requirement, and the broad
cost/regression/safety/failure/waste scope.

- `make` completes with exit code 0.
- The PDF is nine US-Letter pages.
- The complete Conclusion ends on page 7; page 8 begins with `References`.
- Citation-command count remains 57.
- The exact author-fixed thesis remains verbatim in Abstract, Introduction,
  and Conclusion.
- No semicolon appears in the LaTeX prose, and no undefined citation,
  undefined reference, or fatal LaTeX error remains.
- No RQ meaning, quantitative value, uncertainty interval, evidence-bearing
  qualifier, technical mechanism, or contribution was removed.

BibTeX still reports that `sdbl` contains both `volume` and `number`. That is
owned by the next citation round rather than hidden by this language pass.

## Next Node

Round 10 performs full source-level citation verification because the
bibliography is not yet fully annotated. It will verify existence, metadata,
claim support, and missing citations, repair the `sdbl` record, rebuild the
paper, and preserve the page boundary and scientific story.
