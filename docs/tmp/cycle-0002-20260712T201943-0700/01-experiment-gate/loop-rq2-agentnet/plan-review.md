# Serial plan review: AgentNet cross-platform RQ2 experiment

The same independent subagent reviews revisions serially. Every round explicitly
applies `research-experiment-design`, reads the complete source report and
current plan, remains read-only, and returns `PASS` or `REVISE`. The root owns
all dispositions and plan edits.

## Round 1 — REVISE

**Reviewed:** Revision 1  
**Disposition:** accept all four must-fix categories; preserve the RQ, complete
population, cross-platform transfer, and positive hypothesis.

### Reviewer findings

1. The one scientific object needed sharper population wording, an explicit
   combined-label truth table, a complete risk-model feature/mapping list, an
   Ubuntu-development provenance statement, and a supporting-evidence role
   rather than an entire-RQ verdict.
2. Choosing the strongest grouped baseline inside each target bootstrap draw
   was a composite oracle and could choose different comparators by metric. The
   comparison needed fixed baselines.
3. Operation-work metrics require predicted-problem density/mean risk as the
   primary group score. Additive mass is a different per-group-opening objective
   and cannot break density ties. AgentProf's unsigned operation value also
   cannot silently represent arbitrary floating-point risk.
4. The plan needed a conditional paired-bootstrap definition, pooled
   operation-weighted resampling, missing-class handling and maximum attempts,
   exact commands, dependency/resource estimates, terminal checks, and separate
   execution versus scientific statuses.

### Revision 2 changes

- Fixed the truth table to positive=`incorrect OR redundant`,
  negative=`correct AND necessary`, otherwise unresolved after prediction.
- Enumerated every categorical/numeric feature and fixed the existing Ubuntu
  action/target/phase/repetition rules as development provenance.
- Fixed raw-action as the grouped primary alternative and ungrouped transferred
  risk as the localization baseline; removed all target-time comparator
  selection. Exact-repeat and other structures remain controls.
- Defined complete density tie blocks and moved additive mass to secondary
  analysis; AgentProf now validates count stacks while the scorer reconstructs
  full-precision risk by emitted stack key.
- Defined one model fit per fold, shared paired task draws, within-platform
  pooled resampling, 50,000 maximum attempts for 10,000 valid draws, and
  incomplete handling.
- Added exact commands, versions, source sizes, time/disk budget, completion
  checks, and separate execution and hypothesis statuses.

**Files modified by reviewer:** none.
