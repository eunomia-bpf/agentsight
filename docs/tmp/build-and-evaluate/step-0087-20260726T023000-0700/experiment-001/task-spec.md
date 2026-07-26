# Task spec: direct multi-level annotation vs A2 recursive on CodeTraceBench

You are an autonomous engineering agent in
/home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
Never run git commands. Never touch docs/paper/ or the submodule. All
deliverables in THIS directory. RQ3 subject unchanged: tag accuracy.

## Hypothesis (user-proposed)

A strong backend that DIRECTLY writes multi-level transition marks in one
pass per trajectory matches or beats the evaluated A2 binary-recursive
policy on the same population and metrics.

## Setup

- Population: all 405 CodeTraceBench trajectories, the same source-only
  packets the A2 run used (locate via step-0071/step-0075 records; the
  reconstruction script exists in script/).
- Backend: you (codex CLI, gpt-5.6-sol), one call per trajectory. Input:
  the source-only packet (target-blind, no stages/outcomes/scores).
  Output: sparse complete-path marks in the exact A2 mark format —
  variable depth, 1-3 meaningful words per tag, action-first, mandatory
  session root — produced DIRECTLY (no STOP/SPLIT recursion protocol).
  One format retry per trajectory; tally failures.
- Then apply the UNCHANGED downstream pipeline: deterministic root-prefix
  repair, the fixed action-object canonicalization replay, and the
  existing RQ3 scorer (ordinary B-cubed P/R/F1 and exact adjacent
  boundary P/R/F1 against the official 2,948 stages; task-clustered
  bootstrap for the delta vs A2's stored per-trajectory scores).
- Comparisons: this backend vs A2 (0.704 B3 / 0.394 boundary) and vs
  multi-resolution recurrence (0.663 / 0.266), paired where possible.
- Record cost: wall time, worker pattern, token counters; place next to
  the A2 wave envelope and step-0086 figures.
- Validity: coverage of every turn, conservation of 20,866 operations and
  494,862,929 tokens on replay, zero adjacent display-path collisions.

## Deliverables

direct_annotation harness/scripts, raw marks, raw-results.json,
results.md (hypothesis verdict with paired intervals), cost-record.md,
execution-log.md. Complete population only; a <=3-trajectory recipe
validation is never reported as a result.
