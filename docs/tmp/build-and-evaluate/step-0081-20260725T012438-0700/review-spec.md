# Independent review spec: step 0081 raw-action skeleton control

You are an independent reviewer. Repository:
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Verify the completed experiment in `experiment-001/` (task-spec.md, results.md,
raw-results.json, raw-responses/, packets-stage1/, packets-stage2/).
READ-ONLY except for writing your review file. `git diff`/`git status`
allowed; NEVER any state-modifying git command — explicitly including
`git stash` in any form.

## Checks (all required)

1. **Completeness**: 220 raw responses; failure tallies match results.md.
2. **Scoring**: independently recompute AP from `completed_ranking` in at
   least 5 randomly sampled raw responses against `target_operation_ids`
   (rank -> descending scores -> sklearn average_precision_score); recompute
   all five MAPs from raw-results.json per-query values and compare to
   results.md.
3. **Raw identity provenance**: confirm the grouping identity actually used
   in packets-stage1 matches the documented step-0072 information-matched
   raw path (method-index.json `methods.raw.operation_leaves` composite,
   NOT bare raw_action), by reconstructing the grouping for 3 sampled
   trajectories from the frozen files and diffing against the packet.
4. **Leakage**: sampled stage-1 and stage-2 packets contain no target,
   outcome, judge, or localizer fields.
5. **Manipulation isolation**: for 3 sampled queries, confirm the stage-2
   packet format matches step 0080's (same fields) except the group paths.
6. **DECISION-CRITICAL ADDITION — paired content-efficiency test**: compute
   the per-query paired difference in content-opened fraction between step
   0080 (semantic skeleton) and step 0081 (raw skeleton) over all 220
   queries, and a 10,000-draw paired trajectory-cluster bootstrap 95%
   interval within benchmark strata (same clustering as the MAP bootstrap;
   document your seed). Also report the paired difference and interval for
   stage-2 evidence characters and for selected-evidence-operation counts.
   State plainly whether the semantic skeleton opens significantly less
   content at the fixed 5-group budget.

## Deliverable

Write `independent-review.md` in the step-0081 directory (NOT inside
experiment-001): verdict PASS/FAIL, check table with what you ran, the
content-efficiency numbers with intervals, and any discrepancies (expected
vs actual). Do not fix anything.
