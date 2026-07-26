# Results: frozen population and Phase 2 stop

Status: **STOPPED at Phase 2 as required by `task-spec.md`**

## Outcome

Phase 1 completed and is valid. The step-0084 inventory contains exactly 42
rows whose coarse project label is
`agentsight-research-semantic-flamegraph`. Their byte-exact freeze is recorded
in `frozen-population.json` and retained under `frozen-sessions/`.

Phase 2 could not create the required standard annotation workspace with the
repository's existing tooling. The local-session parser works, but no existing
AgentPProf command or repository source adapter converts local Codex/Claude
sessions into the annotation workspace's source-tree `trace.jsonl`. The task
specification explicitly requires stopping at this point rather than
improvising a parallel parser, so Phases 3 and 4 were not run.

## Phase 1: frozen population

| Check | Result |
| --- | ---: |
| Expected sessions | 42 |
| Frozen sessions | 42 |
| Unique session keys | 42 |
| Codex sessions | 18 |
| Claude sessions | 24 |
| Inventory user prompts | 1,132 |
| Inventory LLM calls | 5,540 |
| Inventory tool calls | 3,451 |
| Inventory operations (LLM + tool) | 8,991 |
| Known provider token mass | 897,606,071 |
| Sessions with known provider tokens | 42 |
| Freeze-time bytes | 55,000,887 |
| Hash or length failures on frozen copies | 0 |

The step-0084 inventory recorded 54,351,949 source bytes. The freeze is
648,938 bytes larger because some selected sessions grew between inventory
time and freeze time. Each manifest row therefore records both the inventory
row's coarse `source_bytes` value and the later `freeze_byte_length`. Every
post-freeze parser invocation used only the frozen copies.

`frozen-population.json` records, for every session:

- the step-0084 session key;
- agent kind;
- path relative to that agent's source root;
- path of the frozen copy relative to this experiment directory;
- freeze-time byte length;
- SHA-256 of exactly that byte prefix; and
- the complete inventory row's coarse statistics.

## Phase 2: direct-ingestion probe

The release AgentPProf binary was built with its target directory inside this
experiment directory. Its help exposes:

- local-session input through `--session-file`, `--codex-root`, and
  `--claude-root`;
- portable agent-session input through `--trace-file`; and
- replay of an existing annotation workspace through `--annotation-file`.

It does not expose a command that initializes `workspace/trace.jsonl` from
local sessions.

Two read-only frozen-root probes established that parsing itself works:

| Probe | Sessions | Parsed prompts | Parsed LLM calls | Profile mass | Stock pprof |
| --- | ---: | ---: | ---: | ---: | --- |
| operations | 42 | 1,252 | 5,620 | 10,381 | loads |
| tokens | 42 | 1,252 | 5,620 | 1,380,863,014 | loads |

The operation view counts prompts, LLM calls, and tools. Its implied parsed tool
count is `10,381 - 1,252 - 5,620 = 3,509`, so the comparable parsed LLM-plus-tool
count is 9,129.

These values differ from the coarse inventory by +120 prompts, +80 LLM calls,
+58 tools, and +138 LLM-plus-tool operations. This is an expected parser-scope
difference: the inventory scanner uses its own coarse deduplication and
ownership rules, whereas `agent-session` materializes the richer session IR.

The token masses are not the same construct. The inventory uses each Codex
session's maximum cumulative provider total and Claude's deduplicated
session-level usage total. AgentPProf's token view emits and sums bounded
per-LLM input, output, and cache components. Consequently the direct token
probe is not a conservation comparison against the inventory token total.

The two files `phase2-direct-ingestion-probe.pb.gz` and
`phase2-direct-ingestion-token-probe.pb.gz` are diagnostic direct-ingestion
profiles. They are **not** the requested annotated count/token profiles and
must not be treated as experiment results.

## Exact tooling gap

The missing path is:

```text
frozen Codex/Claude JSONL
  -> agent-session AgentSession forest
  -> annotation-workspace TraceNode JSONL
```

The repository implements the first arrow for ordinary AgentPProf profiling,
and it implements workspace validation/replay after `trace.jsonl` already
exists. It does not implement the second arrow for local sessions.

More specifically:

1. `agentpprof --annotation-file` immediately reads sibling `trace.jsonl` and
   `annotation.json`; it does not accept session inputs in that mode.
2. Annotation-workspace mode rejects an empty annotation object, so it cannot
   be used to bootstrap the trace.
3. Normal local-session mode builds a pprof directly and does not serialize the
   session/prompt/LLM/tool forest as workspace `TraceNode` records.
4. `agent-session` provides a Rust library API and portable `AgentTrace`
   schema, but no existing binary converts that schema into the distinct
   annotation-workspace schema.
5. Existing workspace materializers target already-normalized experiment
   packets or AgentReward data, not local Codex/Claude session files.

Creating a new converter would require defining the source-node ordering,
parent assignment, stable IDs, previews, and ownership of operation/token
metrics. That would be a new adapter outside the existing direct-ingestion
tooling, which `task-spec.md` forbids for this run.

## Validity disposition

```text
phase 1 status: valid
phase 2 status: incomplete due to missing repository ingestion path
phases 3-4: not executed by mandatory stop rule
annotation coverage: not measured
annotated-profile mass conservation: not measured
annotated-profile stock-pprof load: not measured
```

No `workspace/`, `annotation.json`, final annotated profiles,
`aggregate-summary.md`, or `cost-record.md` was created, because doing so would
either fabricate a successful Phase 2 or continue beyond the specification's
mandatory stop.

