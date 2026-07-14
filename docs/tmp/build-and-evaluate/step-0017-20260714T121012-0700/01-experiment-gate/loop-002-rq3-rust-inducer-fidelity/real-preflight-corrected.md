# Corrected Real Preflight

## Verdict

**PASS.** This is an execution/dependency check, not paper evidence.

After removing the residual legacy rejection gate, the revised release binary
and frozen old binary both ran on the first sorted eligible real OSWorld-Human
session: 11 operations and 10 adjacent pairs.

The scorer verified all split decisions were consumed, every operation received
one terminal path, replayer and Rust stack weights matched, all 11 units were
conserved, selected oracle fields were empty, the maximum depth was four, and
every candidate decision strictly satisfied the registered gain/penalty rule.
Candidate stop reasons were limited to `max_depth` and `no_material_split`.

## Command And Raw Output

```bash
python3 script/rq3_rust_inducer_fidelity_eval.py \
  --mode preflight \
  --baseline-binary .agentsight/experiments/rq3-rust-inducer-fidelity-v1/bin/agentpprof-old-heuristic \
  --candidate-binary agentpprof/target/release/agentpprof \
  --out-dir .agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight
```

- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight/summary.json`
- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight/session-results.jsonl`
- `.agentsight/experiments/rq3-rust-inducer-fidelity-v1/preflight/pair-predictions.jsonl`
