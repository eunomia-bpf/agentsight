# Round 8 — Terminology, Information Flow, and Claim Tone

- **Timestamp:** 2026-07-14 04:57 -0700
- **Skills:** `check-terminology-infoflow`, `paper-writing-style`
- **Reviewer:** fresh independent subagent, read-only
- **Target:** complete `docs/paper/main.tex`, architecture figure, relevant
  bibliography entries, and RQ3 experiment report
- **Disposition after fixes:** PASS

## Review outcome

The reviewer found no thesis, RQ, number, citation, architecture, or result
drift. It reported two must-fix, eight should-fix, and two consider findings.
The two substantive wording issues were a surface conflict between existing
per-run span trees and the paper's missing-hierarchy argument, and an incorrect
statement that all four RQ3 components share one annotated construct.

## Applied must-fix changes

- Distinguished an execution span tree from the function-call hierarchy that
  automatically supplies profiling attribution. The Abstract, Background, and
  D3 now consistently state that span trees exist but do not encode semantic
  responsibility through function-call nesting.
- Corrected RQ3 so that task, phase, action, and boundary components are each
  evaluated against their corresponding independent annotations rather than
  an incorrectly shared construct.

## Applied should-fix changes

- Split the Abstract's RQ1/RQ2 and RQ3 evidence into separate sentences.
- Replaced `release profiler` and `released profiler` with `\sys` throughout
  visible paper prose.
- Named automatic induction as the subject of its AP/work result.
- Clarified that AgentProcessBench computes operation-weighted AP within each
  family and then reports the equal-family macro average.
- Separated the HINTBench/TraceElephant released step signal from their Wilson
  lower-bound group-ranking rule.
- Defined the AgentProcessBench test as a within-raw-action-group permutation
  of semantic assignments that preserves subgroup sizes.
- Enumerated all three RQ3 simple controls explicitly.
- Replaced `natural input sizes` with `measured input sizes` in RQ4.

## Consider findings

- Applied the wording change from two algorithm `frameworks` that `enrich` the
  model to two pluggable mechanisms that instantiate it.
- Did not add raw-action RSS to the RQ4 table. The existing text reports the
  measured largest-input delta, while another table column would increase
  density without changing the RQ4 answer.

## Scope discipline

All changes explain existing mechanisms or results. No experiment, benchmark,
metric, model, threshold, claim, RQ, thesis, or narrative direction changed.
The RQ2 explanation was compressed after revision to preserve the eight-page
format.

## Verification

- `make -C docs/paper`: PASS
- PDF length: 8 pages
- Undefined citations/references: none
- Overfull boxes: none
- `git diff --check`: PASS
- No Git operation performed
- Canonical paper submodule untouched
