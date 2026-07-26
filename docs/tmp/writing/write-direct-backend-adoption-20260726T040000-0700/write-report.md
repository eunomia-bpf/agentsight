# WRITE Report: Direct Backend Adoption

Status: **COMPLETE**

## Main issues

The paper still described the evaluated CodeTrace backend as a fixed binary
recursive policy and reported the prior A2 artifact as the current RQ3 result.
That left the abstract, introduction, design, RQ3 table/prose, and RQ4 cost
accounting inconsistent with the complete direct multi-level run in Step 0087.
The prior A2 reconstruction and cost values also needed explicit historical
attribution once the direct backend became current.

## Revision strategy

- Replaced the evaluated recursive-policy paragraph with the direct
  source-only complete-packet protocol, including free per-branch depth, one
  ordinary format retry, and unchanged deterministic downstream repair and
  canonicalization.
- Recast the complete CodeTrace run as independent direct-backend workers under
  one fixed source-only instruction, with stages, outcomes, recurrence
  assignments, and scores unavailable before materialization.
- Replaced the current RQ3 row and prose with the Step-0087 direct-backend
  result while retaining the prior 0.704/0.394 result as explicitly historical.
- Added the complete 405-trajectory direct-annotation token and active-wall
  cost beside the existing per-population annotation-cost reporting.
- Updated the bilingual Chinese `%` comments alongside every changed passage.
- Left the thesis, four RQ titles, citation commands/keys, and all unrelated
  content unchanged.

## Changed-number reconciliation

All changed or newly added values below were checked against
`step-0087-20260726T023000-0700/experiment-001/results.md` and
`cost-record.md`.

| Location / meaning | Before | After |
|---|---:|---:|
| Abstract: current CodeTrace B$^3$ F1 | 0.704 | 0.764 |
| Introduction results: current CodeTrace B$^3$ F1 | 0.704 | 0.764 |
| RQ3 table: current method B$^3$ precision | 0.839 | 0.793 |
| RQ3 table: current method B$^3$ recall | 0.607 | 0.736 |
| RQ3 table: current method B$^3$ F1 | 0.704 | 0.764 |
| RQ3 table: current method boundary F1 | 0.394 | 0.480 |
| RQ3 prose: direct minus recurrence B$^3$ F1 | 0.0414 | 0.101 |
| RQ3 prose: direct-minus-recurrence 95% interval | [0.0214, 0.0606] | [0.087, 0.116] |
| RQ3 prose: comparison formerly reported against raw action | 0.163 | replaced by direct-minus-prior-Agent 0.059 |
| RQ3 prose: direct-minus-prior-Agent 95% interval | absent | [0.048, 0.073] |
| RQ3 prose: current boundary F1 | 0.394 | 0.480 |
| RQ3 summary: current CodeTrace B$^3$/boundary F1 | 0.704 / 0.394 | 0.764 / 0.480 |
| RQ4: complete direct-run input tokens | absent | 12,050,384 |
| RQ4: complete direct-run output tokens | absent | 231,886 |
| RQ4: complete direct-run active backend wall | absent | 2,215.858 s |

The prior Agent artifact's 0.704 B$^3$ F1 and 0.394 boundary F1 remain in one
explicitly historical continuity sentence. Historical A2 replay/cost values
remain numerically unchanged and are now labeled as belonging to the prior
artifact, including 506.35 s, 1.17 s, 501.64 s, 3.54 s, and the 54.36-minute
artifact-time envelope. The direct marks continue to report exact conservation
of 20,866 operations and 494,862,929 provider-reported tokens.

## Validation

- Build command:
  `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=/tmp/agentprof-direct-write-eA57jU main.tex`
- Result: exit code 0; PDF produced successfully (12 pages).
- Final log: no undefined citations, undefined references, multiply defined
  labels, rerun requests, or overfull boxes.
- Exact thesis count: 3.
- RQ headings preserved exactly:
  - `RQ1: Does Semantic Profiling Improve Resource Attribution?`
  - `RQ2: Does Profiler Output Correspond to Real Problems?`
  - `RQ3: How Accurate Are the Tags?`
  - `RQ4: What Is the Profiling Cost?`
- No citation command or citation key was edited.
- No Git command was run.

## Remaining TODOs or risks

None for this scoped task. Existing underfull-box typography warnings remain
non-fatal and predate the requested evidence update; the task explicitly made
information completeness, rather than page count, the constraint.
