# Independent experiment-plan review

Timestamp: 2026-07-22T00:12:00-07:00
Reviewer: independent Codex subagent using `research-experiment-design`
Final verdict: **PASS**

## Round 1 — REVISE

The reviewer identified three blocking ambiguities:

1. CodeTraceBench provides an independent flat stage partition, not nested
   ancestor, name, or cross-session identity ground truth. The original plan
   over-authorized the result as a decisive nested-structure experiment.
2. `start_evidence_id` was not a defined replay-stable identity, and the
   recursive `STOP`/`SPLIT` and path-emission contract was incomplete.
3. Source-native, old one-shot Qwen, Agent-produced marks, and recurrence had
   overlapping baseline/control roles and inaccurately implied equal visible
   information. Name-pool and target-label leakage rules were underspecified.

The plan was revised to make this a supporting flat-partition experiment plus a
product case; define B$^3$ over the complete visible operation-ID path scoped to
the trajectory; specify unique source IDs, ordered marks, the name pool, and
fail-closed behavior; separate baseline and control roles; and state each
backend's unequal information boundary and scoring-blind pool rules.

## Round 2 — REVISE

One ambiguity remained: `STOP(operation_id)` could either append a new frame or
terminate an already named child. The reviewer required an executable recursive
state.

The plan now defines
`segment(interval, current_operation_id, ancestor_path)`. The root is named
before the first call. `STOP` has no argument and assigns
`ancestor_path + current_operation_id`; `SPLIT` creates two named sibling calls.
Each semantic split adds exactly one level, length-one intervals stop, and
binary-search scaffolding never enters the visible path.

## Round 3 — PASS

The reviewer found no remaining must-fix. The flat scientific authorization,
stable-ID mark contract, recursive state, baseline/control roles, information
boundaries, name-pool isolation, and target-label leakage rules were all
considered executable and appropriately scoped.
