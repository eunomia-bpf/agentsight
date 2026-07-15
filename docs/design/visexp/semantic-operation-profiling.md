# Semantic Operation Profiling

This note defines the minimal model behind `agentpprof` and the semantic
flamegraph experiments.

## Decision

AgentPProf should be framed as a semantic operation profiler, not as a trace
viewer or dashboard.

The implementation model is deliberately small:

```rust
pub type OpId = usize;

pub struct Operation {
    pub parent: Option<OpId>,
    pub kind: &'static str,
    pub name: String,
    pub value: u64,
}

pub struct Profile {
    pub view: &'static str,
    pub sample_type: &'static str,
    pub unit: &'static str,
    pub ops: Vec<Operation>,
}
```

This is a weighted typed operation tree.

- `parent` is the only v0 relation.
- `kind:name` is the profile frame.
- `value == 0` means context.
- `value > 0` means a weighted sample.
- One profile has one value semantic, described by `sample_type` and `unit`.

The pprof, folded-stack, SVG, and JSON outputs are all generated from the same
operation tree.

## Why A Tree Is Enough

A profiler needs an attribution path:

```text
root -> context -> activity -> weighted sample
```

That is exactly what a parent tree represents. It is not a complete provenance
graph and it is not a counterfactual causal model. It is the profile projection
needed to answer where tokens, time, file effects, network effects, or system
events accumulated.

Examples:

```text
tokens profile, value = token count:

project:agentsight
  agent:codex
    session:review
      prompt:debug
        call:llm/summarize
          model:gpt-5
            kind:input 1200
```

```text
files profile, value = file effect count:

project:agentsight
  agent:codex
    session:review
      prompt:test
        path:collector/src
          effect:read
            status:ok 1
```

```text
network profile, value = network effect count:

project:agentsight
  agent:codex
    session:review
      prompt:test
        domain:api.example.com
          process:node
            status:ok 1
```

## Fold Algorithm

The fold algorithm is the whole projection layer:

```text
for each operation with value > 0:
  walk parent pointers to root
  convert every op to "kind:name"
  add value to that folded path
```

In Rust terms:

```rust
fn profile_to_stacks(profile: &Profile) -> Counter {
    let mut out = Counter::new();
    for id in 0..profile.ops.len() {
        let value = profile.ops[id].value;
        if value == 0 {
            continue;
        }
        folded_add(&mut out, op_frames(profile, id), value);
    }
    out
}
```

This keeps the model unified without adding `Relation`, `Metric`, `Field`,
`OperationStore`, or `ProjectionSpec` types.

## Operation Semantics

Session, prompt, LLM call, tool call, process, file effect, network effect,
status, model, and token-kind frames are all represented as operations in the
profile tree.

Some of these are real execution units; some are profiling dimensions. That is
acceptable because the tree is a profile IR, not a complete execution ontology.
The paper can call this a "profile projection of agent execution" to avoid
overclaiming.

## Backend Rule

Backends should be tree rewrites, not pprof writers.

A future backend may:

- insert `operation:run_tests` between `prompt:*` and tool/process frames;
- rename `prompt:unmatched` or `operation:unknown`;
- collapse noisy command/process names into low-cardinality labels;
- add loop or retry frames.

It should not output folded stacks, SVG, pprof samples, or raw prompt text.

The minimal future interface is:

```rust
pub trait Backend {
    fn apply(&self, profile: &mut Profile) -> anyhow::Result<()>;
}
```

No backend trait is needed until the first real backend exists. The current code
already uses the tree IR internally and preserves existing output behavior.

## Boundaries

This model supports most profiling scenarios:

- token/cost profiles;
- file/network/system-effect profiles;
- wall-time profiles;
- tool/status profiles;
- profile diff and regression checks over folded stacks.

It does not directly represent:

- one operation with multiple parents;
- evidence supporting final-answer claims;
- memory influence across many prompts;
- counterfactual causality;
- general multi-agent provenance graphs.

Those can be added later with optional non-tree links if needed. They should not
be part of the v0 profiler core.

## Paper Framing

The contribution should be described as:

> AgentPProf uses a weighted semantic operation tree as a profiling IR. It turns
> local agent histories into pprof-compatible profiles over tokens, time, files,
> network activity, and system effects.

This is stronger and more precise than "AgentPProf draws flamegraphs." The
flamegraph is just one renderer for the folded operation paths.

The evaluation note tracks current evidence:
[paper/evaluation-claims-setup.zh-CN.md](paper/evaluation-claims-setup.zh-CN.md).
