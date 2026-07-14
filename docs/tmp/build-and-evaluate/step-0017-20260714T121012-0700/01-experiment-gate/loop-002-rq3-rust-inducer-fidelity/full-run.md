# Superseded Full Run: Legacy Rejection Gate Still Present

## Completion

**INVALID for the approved tested hypothesis.** The run evaluated the entire
population, but a subsequent code audit found that the candidate still retained
the old `redundant_segment_label` rejection gate. It triggered 16 times. The
plan explicitly removed every legacy acceptance gate, so this binary was not
the registered candidate. The run is preserved for provenance and must not
authorize a paper or mechanism conclusion.

The mechanically completed population was:

- 287 OSWorld-Human sessions;
- 3,978 operations;
- 3,691 adjacent pairs;
- 2,042 official human groups;
- 574 session-method executions, 287 for each Rust binary.

All execution checks passed, but they were insufficient because the runner did
not assert absence of legacy stop reasons. The corrected runner must enforce
that invariant before the replacement full run.

## Tested Hypothesis Result

For historical reference only, the registered positive criterion required the candidate to beat both the old
Rust heuristic and the strongest simple control on boundary F1 and B-cubed F1.
That criterion was **not met by this invalid implementation**.

| Method | Boundary F1 | B-cubed F1 |
|---|---:|---:|
| Revised information-gain Rust inducer | 0.4192 | 0.6136 |
| Pre-change Rust heuristic | 0.0843 | 0.4653 |
| Action-change control | 0.4771 | 0.6592 |
| Phase-change control | 0.3337 | 0.6655 |
| Always-boundary control | 0.6445 | 0.6784 |
| Supervised out-of-fold upper comparator | 0.7388 | 0.8160 |

The invalid intermediate implementation appeared to improve the shipped mechanism: +0.3348
boundary F1 and +0.1482 B-cubed F1 over the pre-change heuristic. It does not
yet clear the strongest simple controls, so this run cannot authorize a claim
that the target-blind revised constructor recovers human groups accurately
enough by itself.

These numbers are not the approved constructor result. They do not answer RQ3,
alter the paper thesis, change the four RQs, or justify any paper update.

## Mechanism Diagnostics

- Old heuristic emitted no split for 204/287 sessions; revised: 4/287.
- Revised induction reached the configured depth cap in 106/287 sessions; old:
  3/287.
- Revised boundary F1 was 0.556 on the 251 sessions shorter than 20 operations,
  but 0.208 on the 36 sessions with at least 20 operations.
- The revised method produced 1,557 contiguous groups versus 2,042 official
  groups, consistent with remaining under-segmentation rather than a mass or
  replay failure.

The depth-cap and session-length observations are diagnostics from an invalid intermediate implementation, not a
new scored hypothesis. They identify an arbitrary implementation bound that an
independent result review must decide whether to remove in a separately planned
iteration; they do not justify silently retuning the completed run.

## Command And Raw Output

```bash
python3 script/rq3_rust_inducer_fidelity_eval.py \
  --mode full \
  --baseline-binary .agentsight/experiments/rq3-rust-inducer-fidelity-v1/bin/agentpprof-old-heuristic \
  --candidate-binary agentpprof/target/release/agentpprof \
  --out-dir .agentsight/experiments/rq3-rust-inducer-fidelity-v1/full
```

- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/full-invalid-legacy-redundancy-gate/summary.json`
- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/full-invalid-legacy-redundancy-gate/session-results.jsonl`
- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/full-invalid-legacy-redundancy-gate/pair-predictions.jsonl`
