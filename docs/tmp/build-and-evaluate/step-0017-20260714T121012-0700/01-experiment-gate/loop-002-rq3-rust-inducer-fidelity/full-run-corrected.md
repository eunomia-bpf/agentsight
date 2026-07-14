# Corrected Full Run: RQ3 Rust Inducer Fidelity

## Completion And Validity

**COMPLETE and valid for the registered tested hypothesis.** The corrected run
evaluated all 287 eligible OSWorld-Human sessions, 3,978 operations, 3,691
adjacent pairs, and 2,042 official human groups. It contains 574 independent
session-method executions.

All registered validity checks passed. In particular, candidate stop reasons
were exactly `max_depth` and `no_material_split`; no legacy acceptance gate
remained. Every decision was consumed, every operation received one terminal
path, the two method-specific replayers matched Rust stack weights, mass was
conserved per session, no oracle field entered induction, and every candidate
split strictly exceeded `ln(n)/(2n)`. Distinct raw child labels were also
verified to remain distinct after folded-frame normalization. The final
collision-safety patch changed no OSWorld prediction or metric.

## Tested Hypothesis

The registered positive criterion required the candidate to exceed both the
old Rust heuristic and the strongest simple control on boundary F1 and B-cubed
F1. Because it failed both strongest-control comparisons, the registered tested
hypothesis is **contradicted**. This verdict is about this fixed candidate, not
the paper thesis or all of RQ3.

| Method | Boundary F1 | B-cubed F1 |
|---|---:|---:|
| Revised information-gain Rust inducer | 0.4231 | 0.6165 |
| Pre-change Rust heuristic | 0.0843 | 0.4653 |
| Action-change control | 0.4771 | 0.6592 |
| Phase-change control | 0.3337 | 0.6655 |
| Always-boundary control | 0.6445 | 0.6784 |
| Supervised out-of-fold upper comparator | 0.7388 | 0.8160 |

The revised algorithm is a large improvement over the actual shipped baseline:
+0.3388 boundary F1 and +0.1511 B-cubed F1. It still does not beat the strongest
simple controls, so this run cannot authorize the claim that this target-blind
constructor alone accurately recovers official human groups.

This tested-hypothesis result does not answer all of RQ3, alter the four RQs,
or challenge the paper thesis. Unit-weight operations also mean the experiment
checks resource-weight conservation but does not isolate an empirical benefit
of resource weighting.

## Diagnostic Boundary

- Old heuristic emitted no split in 204/287 sessions; candidate: 4/287.
- Candidate reached the arbitrary depth-four cap in 106/287 sessions; old: 3.
- Candidate boundary F1 was 0.557 on 251 sessions shorter than 20 operations,
  but 0.217 on the 36 sessions with at least 20 operations.
- Candidate produced 1,581 contiguous groups versus 2,042 official groups,
  consistent with remaining under-segmentation.

The length/depth observations are post-run mechanism diagnostics. They do not
retune or reinterpret this completed experiment. They provide evidence for an
independent review to decide whether the candidate's arbitrary depth-four
runtime bound conflicts with the registered recursive stopping principle.

## Command And Raw Output

```bash
python3 script/rq3_rust_inducer_fidelity_eval.py \
  --mode full \
  --baseline-binary .agentsight/experiments/rq3-rust-inducer-fidelity-v1/bin/agentpprof-old-heuristic \
  --candidate-binary agentpprof/target/release/agentpprof \
  --out-dir .agentsight/experiments/rq3-rust-inducer-fidelity-v1/full
```

- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/full/summary.json`
- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/full/session-results.jsonl`
- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/full/pair-predictions.jsonl`
