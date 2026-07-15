# Independent Plan Review

## Round 1 — 2026-07-15T02:48:00-07:00

**Reviewer:** fresh read-only subagent using `research-experiment-design`
**Verdict:** REVISE

### Must-fix findings

1. The plan conflated CodeTracer's released two-way `phase` classifier with
   the project-authored nine-way `action_kind` mapping in
   `script/codetracebench_agentprof_eval.py`. The plan must identify the actual
   provenance of both fields and require the recurrence adapter to write only
   unit weight and `{session, action}` to Rust, excluding `phase`,
   `raw_action_key`, and official `stages`.
2. A source or coverage defect is not a valid scientific mixed result. It must
   produce an invalid or incomplete run because it fails the declared full
   completion rule.

### Optional suggestion

Disclose that the phase-change baseline classifies richer raw action text while
recurrence sees compressed `action_kind`. This is a conservative information
asymmetry against recurrence, not an invalid baseline.

### Checks that passed

- Official verified stages are complete across all 405 selected target
  trajectories and are described by the source as human-verified ground-truth
  stage ranges.
- Removing the 405 target IDs from the existing 2,634-session / 108,569-
  operation reference leaves exactly 2,229 sessions / 87,703 operations with
  zero target overlap.
- The target population is exactly 405 sessions / 20,866 operations.
- The phase scorer is target-blind and does not read stages.
- The controls, boundary F1, B-cubed F1, preflight, full commands, and no-tuning
  recurrence contract are scientifically credible and executable after adding
  the stated adapter.

## Root Response

The plan was repaired without adding a dataset, feature, metric, baseline,
run, threshold, or control artifact. It now distinguishes project-derived
`action_kind` from CodeTracer-derived `phase`, fixes the exact minimal Rust
input, states the conservative baseline information asymmetry, and separates
valid mixed evidence from invalid/incomplete execution. One follow-up review is
requested on these bounded repairs only.

## Follow-up — 2026-07-15T02:54:00-07:00

**Verdict:** APPROVE
**Remaining blockers:** none

The reviewer confirmed that both must-fix findings were accurately and
minimally repaired: field provenance and the minimal Rust input are explicit;
`phase`, `raw_action_key`, and official `stages` are excluded from recurrence;
valid mixed evidence is separated from invalid/incomplete execution; and the
conservative baseline information asymmetry is disclosed. The step report and
plan are synchronized. The reviewer added no new requirement and did not edit
files or run the experiment.
