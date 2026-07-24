# RQ6 Independent Result Review

**Reviewer:** independent read-only research subagent

**Date:** 2026-07-23

**Verdict:** **PASS**

## Sampling and source integrity

- Every Open-SWE harness/model stratum contains 64 independent task instances:
  256 stratum-specific selections and 255 unique instance IDs across strata.
  The only repeated ID is `pingcap__tidb-lightning-508`, selected in the two
  OpenHands model strata. IdeaTrail contributes 64 independent topics.
- Each formal manifest stratum equals the first 64 hash-ranked entries from
  the retained 256-candidate-per-stratum plan.
- The sample-size change is documented as a pre-analysis amendment after
  acquisition started, not as pre-outcome. Selection uses identifiers only.
- The independent checker rereads 320 rows and reconciles 31,249 Tool calls,
  22,433 path-resolved calls, 10,751 mutation calls, and 22,113 transitions.
  Same-path/same-module/cross-module counts are 8,514/7,639/5,960, with zero
  mismatch.

## Estimator and result audit

An independent E4 implementation reproduced all 320 return counts and medians
with zero mismatch. `A,B,A = 1`; public stratum medians are 2, 2, 2, 3, and 3
strictly intervening path calls. Aggregate cross-module movement is
18.0%--30.0% publicly versus 2.1%--20.2% in the six-case compatible anchor.

The supported claim is narrow: within-attempt path locality and short returns
recur in these public coding/scientific-process strata, with a different
magnitude. E3/E4 are exact; E1 is descriptive; E5/E6 are analogous; E2 and
longitudinal lineage/re-grounding/Skill cells remain N/A. The artifacts make no
population, productivity, long-term-progress, or causal harness/model claim.

## Figure and Nebula boundary

The result figure matches the committed tables and keeps the exact/analogous/N/A
boundary visible. The separate Agent Nebula review is also supported: retain
the directory-colored force-layout skeleton, but strengthen the action-order
focus layer and native-root session continuity. Force-layout coordinates are
explicitly presentation-only and never become an empirical metric.

Final mechanical audit also passed: all recorded hashes matched their current
files and `git diff --check` returned zero.
