# Execution log

Run date: 2026-07-25 (America/Vancouver)

## Constraints honored

- No Git command was run.
- No existing session file was modified or deleted.
- No file under `docs/agentpprof-paper/` or `docs/paper/` was touched.
- All generated files and build artifacts were placed in this experiment
  directory.
- After freezing, every session-content read used the frozen copies.
- The automatic annotation phase was not started after Phase 2 hit the
  task-specified stop condition.

The pre-existing `task-spec.md` and `codex-stdout.log` were not modified.

## Required inputs read

1. `task-spec.md`
2. `docs/user-instruction.md`
3. `docs/idea-story.md`
4. `docs/design/visexp/agentpprof-annotation-workspace.md`
5. the fixed step-0077 automatic-backend instruction
6. the step-0084 inventory, inventory scanner, and session-key definition
7. AgentPProf and agent-session CLI/source documentation needed to determine
   the supported ingestion paths

## Phase 1

`freeze_population.py` reconstructed inventory keys as the first 16
hexadecimal characters of SHA-256 over
`<agent>:<source-relative-path>`, exactly matching step 0084. For every
selected file it:

1. opened the source read-only;
2. fixed the byte boundary from the open file descriptor;
3. copied exactly that many bytes;
4. computed SHA-256 while copying; and
5. wrote the manifest only after all 42 copies completed.

Freeze completed at `2026-07-26T04:20:50Z` in about 0.92 seconds.

Independent readback of the frozen copies found:

```text
sessions=42
unique_keys=42
codex=18
claude=24
bytes=55000887
hash_or_length_problems=0
```

## Phase 2

AgentPProf was built from the checked source with:

```text
CARGO_TARGET_DIR=<experiment>/cargo-target
cargo run -p agentpprof --release --locked -- --help
```

The first attempt from the repository root failed because that directory has
no root `Cargo.toml`; it wrote no source or session file. The command was then
run from `agentpprof/` and completed in 21.66 seconds. The target directory
remained inside this experiment directory.

The complete frozen population was passed through the existing local-session
input using the frozen Codex and Claude roots. The operations probe completed
in about 0.45 seconds; the token probe completed in about 0.85 seconds. Both
reported 42 parsed sessions. Stock `go tool pprof -top` opened both files in
about 0.37 seconds total.

The CLI/source audit then confirmed that no supported command materializes the
annotation workspace's `trace.jsonl` from those parsed local sessions. Per the
last sentence of `task-spec.md`, execution stopped after Phase 2.

## Files created

- `freeze_population.py`
- `frozen-population.json`
- `frozen-sessions/`
- `cargo-target/`
- `phase2-direct-ingestion-probe.pb.gz`
- `phase2-direct-ingestion-token-probe.pb.gz`
- `results.md`
- `execution-log.md`

The two pprof files are parser/readback probes only, not the requested final
annotated profiles.

## Not run

- no annotation batches;
- no annotation backend calls or token usage;
- no CLI annotation validation;
- no annotated count/token profile materialization;
- no aggregate responsibility summary; and
- no annotation cost record.

Reason: the mandatory Phase 2 stop condition, detailed in `results.md`.
