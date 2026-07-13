# Round 5 — Whole-Paper Consistency

**Completed:** 2026-07-12T19:02:00-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** `round-4-abstract-intro-rebuild.md`  
**Reviewer:** fresh read-only subagent using `check-terminology-infoflow`, paper-consistency scope  
**Verdict after fixes:** PASS

## Raw Findings

Must-fix findings were inconsistent completed/planned experiment status, a no-tag
RQ1 baseline mislabeled as flat, and drift among RQ3's 7/9 V-measure, applicable
boundary labels, and 6-of-applicable boundary-F1 result. Should-fix findings
challenged aggregate-to-native-operation drilldown, asked for the supervised
backend's development/evaluation split, separated the local 183,714-unit result
from 15-family public coverage, and scoped “every projection” to RQ1.

## Applied Fixes

- Changed Abstract and Introduction from “evaluate” to “organize evaluation
  around,” and changed Setup to “the complete RQ2/RQ4 experiment” where those
  matrices remain open.
- Replaced `flat` with `no-tag` in the RQ1 answer because the current no-tag view
  still has many stack paths and is not the defined one-frame flat profile.
- Standardized RQ3 everywhere: seven of nine exceed 0.7 V-measure; among seven
  datasets with applicable adjacent-boundary labels, six exceed 0.7 boundary
  F1. The caption, body, and answer now use identical denominators.
- Separated the 325-trajectory/183,714-unit local result from the 15-family
  representation and mapping coverage sentence.
- Scoped “every projection” in Abstract, Introduction, and Conclusion to the
  current RQ1 ablation.
- Verified the implementation's JSON/folded/pprof summaries and found no emitted
  member-ID index that proves aggregate-to-record drilldown. Replaced that
  overclaim throughout with the implemented boundary: input operation records
  retain source identifiers that can be selected into source-native projections
  alongside semantic aggregates.
- Clarified Figure 1's dashed path: it uses profile results together with
  retained source records, rather than an unimplemented profile drilldown API.
- Added the supervised adjacent-boundary backend split: fitting uses a disjoint
  development split of each source family; evaluated-split labels do not enter
  fitting, selection, or folding and appear only during scoring.
- Updated corresponding Chinese comments so they no longer contradict the
  reader-facing English source.

## Consider Finding

The author-kit `AnonymousSubmission2027.tex` remains untouched. It is not the
AgentProf build entrypoint. Renaming or relocating it during WRITE would create
unnecessary template churn; corpus-wide checks should use `docs/paper/main.tex`.

## Preservation And Intent Check

Exact thesis and four exact RQs remain unchanged. No quantitative value changed.
Citation-command count remains 59. Abstract is 204 words and 9 sentences. No
negative intermediate result entered the paper. The fixes remove overclaims and
status contradictions without narrowing the profiling contribution.

## Build Evidence

`make` completed successfully. The log has no undefined citation/reference,
LaTeX error, emergency stop, or overfull box. The output remains 9 letter-size
pages.

## Next Node

Proceed to Round 6 sentence-structure review. Empirical TODOs remain explicit
and require experiments, not prose changes.
