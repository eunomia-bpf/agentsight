# AgentPProf Annotation Workspace

**Status:** implemented CLI contract  
**Updated:** 2026-07-22

## Decision

AgentPProf uses a three-file working directory for iterative semantic operation
annotation:

```text
workspace/
|- trace.jsonl
|- annotation.json
`- stacks.folded
```

The authoritative original recording is outside this workspace. It may be an
AgentSight SQLite recording, an agent-native session archive, or a benchmark
dataset. A source adapter materializes the current working trace from that
external source. The workspace does not contain a second `raw-trace` copy.

The separation is strict:

- `trace.jsonl` is the current, inspectable trace plus CLI-derived semantic
  paths;
- `annotation.json` is the only output produced by an annotation backend;
- `stacks.folded` is the CLI-derived aggregate for the current width measure.

Only `annotation.json` expresses an annotator's judgment. The other two files
are maintained deterministically by the CLI and may be regenerated.

## File 1: Current Working Trace

`trace.jsonl` preserves enough source evidence for a backend to understand and
check its decisions. It retains the original session name and user request,
prompt text, LLM response, tool name and arguments, tool result, source
hierarchy, and available additive measurements. Large source content may be
represented by a stable reference plus a readable preview, but it is not
silently discarded.

A minimal node is:

```json
{
  "id": "C3",
  "parent": "P1",
  "kind": "llm",
  "data": {
    "text": "I will construct a minimal reproducer."
  },
  "metrics": {
    "tokens": 830,
    "time_ns": 1200000000
  },
  "path": [
    "Repair software regression",
    "Reproduce problem"
  ]
}
```

The fields have one purpose each:

- `id` is the replay-stable source-node identifier;
- `parent` is the source hierarchy, not a semantic-operation relation;
- `kind` identifies the source node, such as `session`, `prompt`, `llm`,
  `tool`, or `effect`;
- `data` retains the source content needed to understand the event;
- `metrics` contains the additive values owned by the node;
- `path` is the current semantic operation path derived by the CLI.

The source adapter creates the first five fields. The CLI owns only `path`.
Annotation never changes a node's source kind or replaces its original content.

`trace.jsonl` is a working materialization, not the source of record. If it is
lost or invalid, the source adapter recreates it from the external recording.

## File 2: Backend Annotation

Every backend has exactly the same contract:

```text
input:  trace.jsonl
output: annotation.json
```

The minimal annotation maps a source node at which an operation begins to
three fields:

```json
{
  "S1": {
    "tag": "Repair software regression",
    "parent": null,
    "next": null
  },
  "P1": {
    "tag": "Fix the user-reported failure",
    "parent": "S1",
    "next": null
  },
  "C1": {
    "tag": "Understand implementation",
    "parent": "P1",
    "next": "C3"
  },
  "C3": {
    "tag": "Reproduce problem",
    "parent": "P1",
    "next": "C5"
  },
  "C4": {
    "tag": "Run reproducer",
    "parent": "C3",
    "next": "C5"
  },
  "C5": {
    "tag": "Implement fix",
    "parent": "P1",
    "next": null
  }
}
```

The object key is the source node where the annotated operation begins:

- `tag` is the semantic operation name;
- `parent` names the source node where the enclosing annotated operation
  begins, or `null` for a root;
- `next` is the first source node outside this operation, or `null` when the
  operation continues to the enclosing scope's end.

`next` is an exclusive boundary. It is not a second source-order relation and
does not replace the source tree's `parent` field. The annotation relation and
the source relation deliberately remain separate.

The v0 contract contains no full path, region identifier, canonical-operation
identifier, metric, copied prompt, copied response, confidence, or model
metadata. Exact shared tag strings provide the initial cross-session identity.
A backend that produces synonymous names may revise them in later iterations;
name canonicalization is not embedded in the core profiler.

## File 3: Current Folded Aggregate

After applying the annotation, the CLI rewrites every `path` in `trace.jsonl`
and regenerates `stacks.folded` for the selected additive measure. For example:

```text
agent:codex;operation:repair_software_regression;operation:fix_the_user-reported_failure;operation:understand_implementation;llm:turn_1;tool:view 1240
agent:codex;operation:repair_software_regression;operation:fix_the_user-reported_failure;operation:reproduce_problem;llm:turn_3;tool:shell 830
agent:codex;operation:repair_software_regression;operation:fix_the_user-reported_failure;operation:reproduce_problem;operation:run_reproducer;llm:turn_4;tool:bash 1
agent:codex;operation:repair_software_regression;operation:fix_the_user-reported_failure;operation:implement_fix;llm:turn_5;tool:edit 960
```

The visible stack is exactly `agent -> session-level operation -> prompt-level
operation -> recursively refined operations -> LLM call -> tool/effect`.
Equal semantic prefixes therefore aggregate across sessions. Raw session and
prompt IDs remain pprof labels rather than visible frames that split the
aggregate; LLM, tool, and effect nodes remain visible evidence leaves. A source
event is never renamed into a semantic operation, but no source node is allowed
to remain outside an active semantic operation path.

`stacks.folded` is an internal, inspectable workspace intermediate for the
current view. It is not a second AgentPProf product format or a custom
visualization path. The user-facing product artifact remains one standard
pprof `.pb` or `.pb.gz`, inspected with existing pprof-compatible tools.

One annotation applies unchanged to operation count, tokens, time, file
effects, network effects, or another additive width. Regenerating a different
view changes the folded weights and profile, not the semantic annotation.

## CLI Responsibility

Semantic annotation adds one CLI input only:

```bash
agentpprof \
  --annotation-file workspace/annotation.json \
  --view tokens \
  -o profile.pb.gz
```

The annotation path identifies the workspace. The CLI finds the sibling
`trace.jsonl`, updates that file's derived `path` fields, and rewrites the
sibling `stacks.folded`. It then emits the requested standard pprof.

The CLI does not provide a model runner, annotation editor, tagger loop,
backend registry, or custom frontend. It performs five deterministic actions:

1. validate that referenced source nodes exist, annotated ranges are nested
   rather than crossing, every source root begins a session-level operation,
   every prompt begins a prompt-level operation, and every source node is
   covered;
2. compute the active semantic path for every source node;
3. report nonblocking hierarchy warnings for degenerate unary refinement or a
   large flat fan-out with little recursive refinement;
4. atomically update `trace.jsonl` and `stacks.folded`;
5. encode the folded stacks and source evidence in one standard pprof.

An invalid annotation leaves both derived files unchanged and reports the
smallest actionable structural error.

## Iterative Recursive Segmentation

The model starts with the two source scopes that must always be semantically
named and grows only where a more detailed distinction helps answer the user's
profiling question:

```text
Repair software regression                 # session-level operation
`- Fix the user-reported failure            # prompt-level operation
```

After one iteration:

```text
Repair software regression
`- Fix the user-reported failure
   |- Understand implementation
   |- Reproduce problem
   `- Implement fix
```

After refining only the reproduction interval:

```text
Repair software regression
`- Fix the user-reported failure
   |- Understand implementation
   |- Reproduce problem
   |  |- Construct reproducer
   |  `- Run reproducer
   `- Implement fix
```

Each iteration is the same:

```text
read trace.jsonl and its current paths
-> select one region whose current expression is not useful enough
-> add or revise annotation.json
-> run AgentPProf
-> inspect the new trace paths, folded aggregate, and stock pprof
-> continue only where another split improves the explanation
```

There is no fixed depth, target depth distribution, or requirement to annotate
every node. Different branches naturally stop at different depths. The normal
search direction is monotonic refinement, but a backend may remove, merge, or
rename a bad earlier split instead of accumulating errors.

The objective is not maximum segmentation. The session-root and prompt-scope
annotations cover the complete source tree from the first iteration; later
annotations refine that coverage rather than introducing a parallel tree. A useful annotation reveals how
the agent decomposed the assigned task, where it repeated or returned to work,
which paths consumed resources, and which expensive paths failed to reach a
supported result. Splits that merely restate `session`, `prompt`, model, tool,
command, file, or status fields do not add semantic value.

The hierarchy audit is deliberately advisory. A recursively introduced
operation with only one explicit semantic child is usually a redundant unary
chain, and a large parent with many direct children but almost no recursive
children is often a prematurely flat decomposition. Both produce warnings, not
failures. Mandatory session/prompt operations are exempt from the unary check,
and the CLI never invents a second child merely to make a tree look deeper.

## Interchangeable Backends

AgentPProf does not need an in-process backend framework. Any program that
reads `trace.jsonl` and writes the same `annotation.json` is a backend:

1. **Agent backend.** A Codex subagent or another autonomous agent reads the
   current region, proposes a boundary and tag, applies the CLI, examines the
   result, and recursively refines useful regions.
2. **LLM backend.** A local or remote model, such as Qwen through llama.cpp,
   predicts annotations without an autonomous tool loop.
3. **Source-native baseline.** The original session, prompt, LLM, and tool
   hierarchy supplies a deterministic no-semantic-reasoning baseline.
4. **Rule or regex backend.** Visible tool, command, object, and status changes
   provide cheap candidate boundaries and names. It remains a baseline because
   a tool name alone is not an operation intent.
5. **Change-point backend.** Text representations and visible event features
   locate adjacent distribution changes; a separate summarizer names the
   resulting spans.
6. **Cross-run recurrence backend.** Repeated transitions across sessions
   identify reusable continuous regions and shared tags.
7. **Hybrid backend.** A deterministic method proposes coarse regions and an
   Agent selectively refines or renames them.

The minimal comparison set is source-native, one non-LLM automatic method, and
one Agent semantic backend. They differ only in how they produce annotation;
the source trace, CLI projection, widths, pprof encoder, workloads, and scoring
remain shared.

Backend quality is evaluated outside the CLI. Standard boundary and partition
metrics test segmentation where references exist; independent tag metrics test
semantic names; the paper's attribution and localization RQs test whether the
resulting aggregate actually helps answer profiling questions. No backend is
declared better merely because it produces more frames or a deeper tree.

## Product And Research Boundaries

The workspace JSON and folded file are internal inputs and intermediates. They
do not weaken the product rule that every successful AgentPProf invocation
returns one `.pb` or `.pb.gz` profile and relies on stock pprof-compatible
visualization.

The annotation algorithm is automatic when an Agent or other automatic method
produces `annotation.json`; using a configuration file does not make it human
annotation. Human labels, when a benchmark provides them, are evaluation
references only and never enter target-time construction.

The current implementation's complete-path operation-mark file is a predecessor
to this design. It remains valid evidence for the experiments already run, but
it is not the target interface described here. Migration should preserve those
artifacts as historical evidence, introduce the three-file workspace with the
small annotation contract, and rerun comparisons through the shared projection
before changing paper claims.
