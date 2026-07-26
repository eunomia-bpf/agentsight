# Independent Result Review

Date: 2026-07-26

Scope: read-only audit of the final-HEAD RQ1 dormancy/revival and RQ3
turnover/cooling rerun, its `result.md`, and the corresponding numbers in
`docs/paper/main.tex` and `docs/paper/supplement.tex`.

## Findings

- Independently recomputing the project-level and pooled quantities from
  `rq1-revivals.csv`, `rq1-lifecycle-episodes.csv`, and `rq3-windows.csv`
  produced zero discrepancies.  All ten generated CSV/JSON artifacts are
  present.
- The recorded hashes for the script, `projects.json`, `rq1-artifacts.csv`,
  and the six event exports match the inputs.  Identity replay reconciles all
  6/6 projects with the final-HEAD export: 5,746 identities and 181,303 Tool
  actions.
- Every RQ1 table count, proportion, and type-7 median/p90 is correctly
  rounded.  The aggregate values are 11,271/2,285 revival transitions and
  348/41 mutation revivals.
- The main-paper ranges are correct: 8.3--48.3% for the action-gap threshold
  and 0.0--40.0% for the time-gap threshold.  The remaining 11.2% is the
  correct academic-writing-skills project row (13/116), not the aggregate
  lower bound.
- RQ3 has 3,372 primary adjacent-window pairs.  All transition-weighted,
  project-median, sensitivity, lag-1, and lag-8 paper values match the pooled
  CSV rows after one-decimal rounding.
- Neither TeX file retains the superseded extension totals or percentages.
- The RQ meanings, thresholds, pooling/view definitions, qualifiers, and
  conclusion directions are unchanged from the integrated version; the
  paper-side update is numeric only.

No blocker was found.

```text
run status: valid
tested hypothesis: supported
research value: supporting
paper impact: additional RQ1/RQ3 evidence
next paper decision: numeric-only paper update is supported; no result-side repair required
```
