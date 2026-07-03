# Implementation

Last updated: 2026-07-03
Stage at update: stage 4 execute
Source/command: `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, `script/operation_*.py`, `cargo test --manifest-path agentpprof/Cargo.toml`
Completeness: partial

## Repository Layout Relevant To Semantic Profiling

Purpose: identify the maintained implementation boundary.

| Path | Role | Status |
|---|---|---|
| `agentpprof/src/main.rs` | Rust CLI, argument parsing, operation-file entrypoint, output dispatch. | source of truth |
| `agentpprof/src/profile.rs` | Operation loading, mapping, stack construction, pprof/folded/SVG/JSON profile generation. | source of truth |
| `agentpprof/src/tagger.rs` | Regex/LLM prompt tagging for local-session operation fields. | maintained |
| `agent-session/` | Shared local Codex/Claude session parser. | maintained |
| `script/agent_trace_datasets.py` | External labeled trajectory samplers and operation JSONL normalization. | research harness |
| `script/operation_map_infer.py` | Generates reproducible operation-field mapping rules from labeled operations. | research harness |
| `script/operation_stack_quality.py` | Scores operation stacks against dataset-provided labels. | research harness |
| `script/operation_leaveout_eval.py` | Leave-dataset-out mapping validation over external traces. | research harness |
| `script/operation_stack_depth_eval.py` | R286 recursive depth sweep over the Rust `agentpprof` path. | research harness |
| `docs/visexp/` | Historical AgentFlame/visual-experiment notes and older prototypes. | archive/reference; not authoritative |

## Current Implementation Status

Purpose: state what works now.

The current Rust implementation supports:

- normalized operation JSONL via `--operation-file`;
- arbitrary stack shape via `--stack`;
- inline operation-field mappings via `--op-map`;
- reusable mapping files via `--op-map-file`;
- frame-local stack overrides via `--stack-rule`;
- pprof, folded, SVG, and JSON outputs;
- local Codex/Claude session projections and external dataset projections
  through the same stack construction code path.

The Python scripts are experiment harnesses. They download or normalize
third-party traces, generate mapping files, call the Rust CLI, and score
outputs. They are not an alternate semantic-profiler implementation.

## Build And Test Commands

Purpose: make the current runnable path explicit.

```bash
cargo test --manifest-path agentpprof/Cargo.toml
cargo fmt --manifest-path agentpprof/Cargo.toml -- --check
python3 -m py_compile script/agent_trace_datasets.py script/operation_map_infer.py \
  script/operation_stack_quality.py script/operation_leaveout_eval.py \
  script/operation_stack_depth_eval.py
```

R286 depth sweep can be reproduced with:

```bash
python3 script/operation_map_infer.py \
  --operation-file <operation.jsonl> \
  --out docs/visexp/out/operation-stack-depth-r286/inferred-op-map.txt \
  --json-out docs/visexp/out/operation-stack-depth-r286/inferred-op-map.json

python3 script/operation_stack_depth_eval.py \
  --operation-file <operation.jsonl> \
  --op-map-file docs/visexp/out/operation-stack-depth-r286/inferred-op-map.txt \
  --out-dir docs/visexp/out/operation-stack-depth-r286
```

In the tracked R286 run, `<operation.jsonl>` is repeated for the nine operation
files listed in
`docs/visexp/out/external-agent-trace-scaled-r279/agentpprof-result.json`.

## Integration Constraints

Purpose: prevent drift back to old abstractions.

- Do not add prompt/session-specific code paths for external trajectory
  profiling; normalize them into operation fields.
- Do not add separate profiler concepts for tool calls, processes, syscalls, or
  plans; represent them as operation fields and stack frames.
- Keep mapping/tagging rule files reproducible and inspectable.
- Keep large raw samples under `.agentsight/`; tracked experiment outputs should
  be summaries, folded stacks, HTML reports, and JSON analyses.
- Keep README Quick Start stable unless the user-facing first-run flow changes.

## Open Engineering Tasks

Purpose: name work still needed before a paper-ready artifact.

| Task | Why it matters | Status |
|---|---|---|
| Add deeper boundary scorers for step instructions, solution paths, and failure labels. | Action-label F1 is too shallow for final recursive-boundary claims. | pending |
| Add converters for the best next trajectory sources: tau-bench trajectories, OSWorld-Verified/OSWorld 2.0 trajectories, AgentRewardBench, and VisualWebArena trajectories. | Expands scale and domain coverage beyond the current 9 datasets. | pending |
| Add a config-file profile spec that bundles mappings, stack depth, and output choices. | Makes the jq-like configurable workflow easier than long CLI command lines. | pending |
| Add stronger non-flamegraph comparison reports across datasets and depths. | Paper needs visual/analysis alternatives beyond flamegraphs. | partial via R273-R286 |
