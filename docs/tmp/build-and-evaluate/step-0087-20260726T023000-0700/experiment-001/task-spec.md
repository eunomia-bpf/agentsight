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

## Amendment: staged pilot first (binding)

Phase A (pilot): run the direct-annotation backend on a deterministic
40-trajectory slice (the first 40 trajectory IDs in sorted order). Score
the slice with the unchanged pipeline against A2's stored per-trajectory
scores on the SAME 40 trajectories. Write pilot-results.md with paired
B3/boundary deltas and pilot cost. Existing outputs from the interrupted
first attempt (packet index, preflight, raw marks) may be reused as cache.

Gate: if pilot B3 F1 is within 0.03 of A2 on the slice (or better),
proceed directly to the full 405-trajectory run. If worse, STOP after
pilot-results.md; the orchestrator decides.

## Amendment 2: completion phase for ordinal 53 (binding)

Authorize ONE additional backend attempt for ordinal 53 only, with the
format instruction strengthened to require copying the session ID string
exactly, character for character, including its trailing suffix. If the
response is valid, package/canonicalize/score the COMPLETE 405-trajectory
population with all originally specified comparisons, conservation and
collision checks, and paired intervals vs A2 and recurrence; update
results.md and raw-results.json in place. If it fails again, apply one
documented deterministic normalization (replace only the session-id
string in the otherwise-valid attempt-2 marks with the known correct
string), disclose it in results.md, and score the complete population.
