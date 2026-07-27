# Build and test record

Final release binary SHA-256:
`8b1351911d72dd33f776613cb5f9b48d50ecfb85be95db17b0205e85c1f7c4b3`.

All commands completed successfully on 2026-07-26:

```text
cargo test --manifest-path agent-session/Cargo.toml
  24 passed, 0 failed, 0 ignored

cargo test --manifest-path agentvis/Cargo.toml
  59 passed, 0 failed, 0 ignored

cargo test --manifest-path agentpprof/Cargo.toml
  14 passed, 0 failed, 0 ignored

cargo test --manifest-path collector/Cargo.toml
  205 passed, 0 failed, 5 ignored
  (197 collector unit + 5 export snapshot + 3 system runner)

cargo build --release --manifest-path agentvis/Cargo.toml \
  --target-dir docs/tmp/build-and-evaluate/\
shell-boundary-repair-20260726/build/cargo-target
  passed

cargo build --release --manifest-path collector/Cargo.toml
  passed

python3 agentvis/research/rq7_measurement.py check-action-fixtures \
  --fixtures agent-session/tests/fixtures/strict-action-grammar.json
  passed: 18 action, 4 lifecycle, 5 native-root fixtures,
  production + two independent oracles

python3 -m py_compile agentvis/research/rq7_measurement.py \
  agentvis/research/rq7_source_oracle_check.py \
  docs/tmp/build-and-evaluate/shell-boundary-repair-20260726/scripts/*.py
  passed

git diff --check
  passed
```

Ignored collector tests require sudo, authenticated external CLIs, or live
provider credentials; no test failed.
