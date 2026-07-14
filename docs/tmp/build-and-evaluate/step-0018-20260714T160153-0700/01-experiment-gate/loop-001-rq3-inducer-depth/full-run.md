# Complete Run: RQ3 Inducer Depth

## Status: COMPLETE AND VALID BY RUNNER CHECKS

The registered complete command ran the same current release binary at depth
255 and depth four over every eligible OSWorld-Human session. Raw artifacts are
under `.agentsight/experiments/rq3-rust-inducer-depth-v1/full/`.

## Coverage And Validity

- Sessions: 287 per method, 574 profiler executions total
- Operations: 3,978 per method
- Adjacent pairs: 3,691
- Official scorer-only human groups: 2,042
- Input and output mass: 3,978 per method
- Same binary and policy: yes
- Reported maximum depths: 255 and 4 as registered
- Depth 255 non-binding: yes; no `max_depth` stop
- Depth-four baseline reproduces every corresponding Step 0017 session row:
  yes
- Every operation assigned exactly once: yes
- Every split decision consumed: yes
- Rust stack weights reconstructed exactly: yes
- Scorer/oracle fields excluded from induction: yes
- Every accepted split strictly clears the fixed penalty: yes
- Complete population: yes

No algorithm, field, penalty, tie rule, label, workload, metric, or scorer
changed after plan approval or preflight. The first preflight-only stale-name
repair is recorded in `real-preflight.md`. After the first complete execution,
the root removed one misleading legacy validity key,
`maximum_depth_four=true`, from the depth-limit summary. The same summary also
reported the actual 255/4 configurations correctly, and the stale key did not
enter scoring. The identical preflight and complete commands were rerun after
this output-label-only repair; all paths, counts, and metrics remained
unchanged. The final raw directories contain only the corrected outputs.

## Registered Metrics

| Method | Boundary precision | Boundary recall | Boundary F1 | B-cubed precision | B-cubed recall | B-cubed F1 |
|---|---:|---:|---:|---:|---:|---:|
| Depth 255 | 0.4867 | 0.4581 | **0.4720** | 0.6066 | 0.7533 | **0.6720** |
| Depth 4 | 0.4985 | 0.3675 | 0.4231 | 0.4994 | 0.8054 | 0.6165 |
| Action change | 0.3855 | 0.6256 | 0.4771 | 0.8183 | 0.5519 | 0.6592 |
| Phase change | 0.4410 | 0.2684 | 0.3337 | 0.5651 | 0.8092 | 0.6655 |
| Always boundary | 0.4755 | 1.0000 | **0.6445** | 1.0000 | 0.5133 | **0.6784** |
| Supervised OOF comparator | 0.6998 | 0.7823 | 0.7388 | 0.8359 | 0.7971 | 0.8160 |

Removing the cap improves the current Rust algorithm by `+0.0489` boundary F1
and `+0.0555` B-cubed F1. It exceeds the phase-change control on boundary F1
and both action- and phase-change controls on B-cubed F1. It remains below the
strongest simple control on both registered metrics: `-0.1725` boundary F1 and
`-0.0064` B-cubed F1 relative to always boundary. It also remains `-0.0051`
below action change on boundary F1.

## Mechanism Diagnostics

- Depth four makes 1,294 splits and predicts 1,294 boundaries.
- Depth 255 makes 1,652 splits and predicts 1,652 boundaries.
- The official partition has 1,755 adjacent boundaries.
- Removing the cap changes terminal paths in 60/287 sessions; all 60 are among
  the 106 sessions with a depth-four cap stop.
- The other 46 cap-stop sessions produce the same paths once the deeper nodes
  are evaluated; their cap stops become intrinsic `no_material_split` stops.
- Depth 255 ends at maximum observed leaf depth 26, far below 255, with 1,939
  `no_material_split` leaves and no cap stop.
- Depth 255 produces 1,939 predicted groups versus 1,581 at depth four, 2,042
  official groups, and 3,978 groups for always boundary.

These diagnostics reject both simplistic explanations. The hard cap did
materially suppress useful recursive splits in 60 sessions, but it was not the
only barrier because 46 nominally cap-hit sessions had no further acceptable
split. Conversely, cap removal does not degenerate to always boundary: it
predicts 1,652 of 3,691 possible boundaries and stops intrinsically at every
terminal leaf. The remaining gap is about boundary placement, not simply the
number of boundaries.

## Registered Verdict

**CONTRADICTED.** The candidate improves both registered metrics over depth
four, but clears neither metric's strongest simple control. That outcome meets
the mutually exclusive registered `Contradicted` rule. It cannot be relabeled
`Supported` or `Mixed` after seeing that B-cubed is close to the strongest
control.

This verdict applies to the tested hypothesis that the arbitrary depth-four cap
was the sufficient explanation for the built-in mechanism gap. It does not
answer all of RQ3, change the fixed RQ, challenge the paper thesis, or retract
the already admitted supervised and task-partition evidence. The cap-free
configuration is nevertheless the better current implementation because it
removes an arbitrary constraint and improves both registered metrics under the
same intrinsic objective.

## Required Independent Review

A fresh result reviewer must recompute the raw counts and metrics, verify the
same-binary/depth-only comparison and Step 0017 baseline reproduction, audit
the registered verdict, and decide the largest admissible paper/implementation
conclusion. No new depth, penalty, score term, threshold, or OSWorld-Human
variant is admitted by this result.
