# Round 7 — Word Choice and Grammar

- **Timestamp:** 2026-07-14 04:51 -0700
- **Skill:** `paper-writing-style`
- **Reviewer:** fresh independent subagent, read-only
- **Target:** complete `docs/paper/main.tex`
- **Disposition after fixes:** PASS

## Review outcome

The reviewer found four must-fix and eight should-fix local prose issues. The
only mechanism-level wording error said that predicted boundaries were
projected directly. The implementation instead uses those boundaries to define
the group field that AgentProf projects and folds. The remaining findings were
grammar, word choice, referent clarity, and one duplicated held-out-data rule.
No thesis, RQ, experiment, result, or story change was requested.

## Applied must-fix changes

- Replaced the abstract's unnatural phrase about separating responsibility with
  a direct statement that the profile separates resource use by responsible
  semantic category.
- Split the OSWorld-Human corpus sentence so that `each session` unambiguously
  denotes one task instance.
- Corrected the RQ3 mechanism: predicted boundaries define an ordinary group
  field, after which AgentProf projects and folds that field through the
  released path.
- Replaced the undefined phrase `conserving every operation unit` with the
  precise invariant that the profiler preserves the total weight of all 3,978
  operations.

## Applied should-fix changes

- Simplified the Introduction's opening definition of the profiling layer.
- Replaced nominalized cross-trajectory-cost prose with a direct verb.
- Made the Background's aggregation description grammatical.
- Removed a stacked appositive from the operation definition.
- Combined repeated variable-depth sentences without changing their content.
- Replaced `maps model onto CLI` with an explicit implementation statement.
- Clarified the RQ1 comparison as 285 per-session semantic profiles and one
  flat aggregate.
- Stated the RQ2 held-out-target rule once and connected it directly to the
  two final metrics.

## Quantitative edit summary

- **Finding groups resolved:** 12
- **Scientific content changes:** 0
- **Numbers changed:** 0
- **Citations changed:** 0

## Verification

- `make -C docs/paper`: PASS
- PDF length: 8 pages
- Undefined citations/references: none
- Overfull boxes: none
- `git diff --check`: PASS
- No Git operation performed
- Canonical paper submodule untouched
