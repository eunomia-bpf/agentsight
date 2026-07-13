# AgentNet source-schema implementation report

**Completed:** 2026-07-13T03:47:53-07:00  
**Stage:** source preparation repair before REAL PREFLIGHT  
**Execution status:** `VALID`  
**Scientific status:** `NOT_EVALUATED`

## Approved correction

Revision 4 retains all 17,625 checksum-verified Win/Mac trajectory rows while
using the 17,532 original task IDs as dependence clusters. It does not select a
first, last, longest, random, or label-favorable trajectory for the 93 repeated
task IDs.

Each raw row now receives `trajectory_id = <task_id>@row-<source-row>`. The
trajectory ID supplies unique operation and session identity; original
`task_id` remains the selection and bootstrap key. Thus both published records
of a repeated task contribute their real operations to the fixed
operation-weighted estimand, but enter or leave a bootstrap draw together.

## Implementation changes

- `prepare` accepts repeated task IDs only when the complete source still has
  exact expected identity and coverage.
- It enforces 17,625 raw records, 12,427 Windows and 5,198 Darwin trajectories,
  12,364 Windows and 5,168 Darwin unique tasks, and 63/30 repeated task IDs.
- Projection and label rows carry both original `task_id` and unique
  `trajectory_id`; operation IDs derive from trajectory ID.
- Full-source validation checks exact unique-task, trajectory, and
  projection/label operation-ID coverage.
- Predictions and assignments preserve task/trajectory identity and validate
  it before scoring.
- Model reports distinguish target tasks from target trajectories.
- Bootstrap task lists and score multiplicities remain keyed by original task
  ID.
- Hot-group session coverage now uses the trajectory-session index rather than
  incorrectly treating a task ID as a session.

## Verification

`PYTHONDONTWRITEBYTECODE=1 python3 script/test_agentnet_cross_platform_eval.py`
completed 10/10 tests. The new regression constructs two released trajectories
for one task and verifies that both survive conversion with distinct trajectory,
operation, and session IDs while task count remains one.

`pyflakes`, Python byte compilation, and `git diff --check` completed without
errors.

The same independent reviewer explicitly reapplied
`research-experiment-design`, read the current plan, source audit, code, and
tests, reran the test file, and returned `PASS` with zero must-fix. It confirmed
the exact task/trajectory/repeated-record counts, collision-free joins,
task-cluster bootstrap, and trajectory-session diagnostics. The reviewer made
no file changes and requested no extra protocol.

## Paper boundary

No paper, submodule, skill, RQ, hypothesis, feature, baseline, metric, verdict,
or story changed. This repair only makes the implementation match the complete
released public source.

## Next transition

Rerun source preparation from the already verified official files. A successful
prepare must replace the partial projection and then authorize the fixed
256-task-per-platform REAL PREFLIGHT, not a scientific verdict.
