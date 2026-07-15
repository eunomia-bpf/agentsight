# AgentPProf Backend Architecture

This note defines the backend boundary for the minimal weighted operation tree
model in [semantic-operation-profiling.md](semantic-operation-profiling.md).

## Decision

Keep the core small:

```text
SessionRecord -> Profile { ops } -> folded stacks -> pprof/SVG/JSON
```

Backends, when added, should only rewrite the operation tree. They should not
own output formats, folded stack generation, pprof samples, or SVG rendering.

The current code does not need a backend trait yet. It already builds one
weighted operation tree per view and folds it with one algorithm.

## Current Pipeline

```text
Codex/Claude sessions
        |
        v
session tags / prompt tags / LLM tags
        |
        v
build view-specific Profile ops
        |
        v
fold value-carrying operation paths
        |
        v
pprof / folded stack / SVG / JSON
```

The profile tree is the shared IR. Each view differs only in which operations
it creates and what its `value` means.

| View | Value |
| --- | --- |
| `tokens` | token count |
| `files` | file effect count |
| `network` | network effect count |
| `time` | seconds between timestamped events |

## Future Backend Interface

Add this only when there is a real second backend to plug in:

```rust
pub trait Backend {
    fn apply(&self, profile: &mut Profile) -> anyhow::Result<()>;
}
```

The backend can mutate `profile.ops`:

- insert an `operation:*` node under a prompt;
- rename low-quality labels such as `unmatched` or `unknown`;
- collapse high-cardinality command/process/path names;
- add loop/retry/failure frames;
- drop or bucket unsafe private frames before rendering.

It should not:

- write pprof;
- write SVG;
- emit folded stack rows;
- carry raw prompt/model output into frame names;
- introduce confidence/evidence fields before an evaluation path requires them.

## Minimal Algorithms

### Identity

Do nothing. The profile tree created from sessions is already a valid profile.
This is the current behavior.

### Rule Rewrite

Match existing frame paths and insert or rename semantic operation frames.

Example:

```text
prompt:test
  kind:tool
    tool:exec_command
      cmd:cargo
```

can become:

```text
prompt:test
  operation:run_tests
    kind:tool
      tool:exec_command
        cmd:cargo
```

This can be deterministic and private. It is the best first backend.

### Coding Taxonomy

Use a small built-in mapping:

| Evidence | Operation |
| --- | --- |
| `cmd:rg`, `cmd:grep`, `cmd:fd`, `cmd:find` | `search_code` |
| `cmd:cargo`, `cmd:pytest`, `cmd:npm`, `effect:test` | `run_tests` |
| `cmd:git` | `git_operation` |
| file write/edit effect | `edit_code` |
| network effect | `network_access` |
| install commands | `install_dependency` |

This backend should produce low-cardinality labels and leave unmatched paths
alone rather than guessing.

### Optional LLM Or Clustering

LLM and embedding backends should still produce tree rewrites. They can suggest
operation names, but they should be optional and evaluated against deterministic
baselines.

## Evaluation Metrics

Backend quality should be evaluated outside the core fold algorithm:

- coverage: fraction of weighted paths touched by backend labels;
- cardinality: number of distinct operation labels;
- compression: total value divided by unique folded paths;
- stability: label distribution drift across runs;
- top-k coverage: value mass explained by the largest labels;
- privacy: whether any frame leaks raw prompt, response, secret, absolute path,
  or private URL.

`cardinality` and `privacy` should be hard gates. A backend that creates many
unique labels is not a profiler backend; it is just another trace expander.

## Design Summary

The backend architecture should stay this small until the implementation needs
more:

```text
Profile tree in, Profile tree out.
```

That keeps `agentpprof` centered on profiling rather than becoming a general
agent provenance framework.
