# Real Preflight

## Status

**SUPERSEDED.** The execution/dependency checks passed, but a subsequent code
audit found that the candidate still contained the legacy
`redundant_segment_label` rejection gate. It did not trigger in this one case,
but the binary did not exactly implement the approved algorithm. The raw files
are preserved under `preflight-invalid-legacy-redundancy-gate/`; a corrected
preflight is required. This run is not paper evidence.

## Command

```bash
python3 script/rq3_rust_inducer_fidelity_eval.py \
  --mode preflight \
  --baseline-binary .agentsight/experiments/rq3-rust-inducer-fidelity-v1/bin/agentpprof-old-heuristic \
  --candidate-binary agentpprof/target/release/agentpprof \
  --out-dir .agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight
```

## Real Case And Checks

- Workload: first sorted eligible OSWorld-Human session.
- Size: 11 operations and 10 adjacent pairs.
- Both old and revised release binaries completed.
- Both method-specific replayers consumed every Rust split decision.
- Reconstructed stack weights exactly matched the corresponding Rust profile.
- Every operation received one terminal path and all 11 units were conserved.
- No selected evidence field overlapped the declared oracle/label fields.
- Every revised accepted split had positive information gain, strict
  `score > complexity_penalty`, positive margin, and distinct child labels.

The observed one-session scores are deliberately not interpreted. The only
preflight conclusion is that the approved real path is executable and the full
run may proceed unchanged.

## Raw Output

- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight-invalid-legacy-redundancy-gate/summary.json`
- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight-invalid-legacy-redundancy-gate/session-results.jsonl`
- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight-invalid-legacy-redundancy-gate/pair-predictions.jsonl`
