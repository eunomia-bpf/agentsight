# View, Session, And Process Model

## Decision

The view/domain model should stay small:

```text
AgentSession -- SessionProcessMatch --> ProcessTree
ProcessTree  -- flat parent links      --> ProcessNode[]
```

Session-to-process mapping is core, but it is not `Session == PID`. It is a
match between an agent session and a process tree, with evidence and confidence.

## Current View Shape

The current view is a materialized read model for API, CLI, and UI consumers.

```text
raw Event
  -> normalize_event()
  -> MaterializedView
  -> Snapshot / SQLite / API
```

Current in-memory state is roughly:

```text
ViewState
  source
  llm_calls
  token_usage
  audit_events
  tool_calls
  sessions
  network_targets
  resource_samples
```

Current snapshots expose:

```text
Snapshot
  summary
  token_summary
  network_targets
  process_nodes
  audit_events
  resource_samples
  sessions
  agents
```

This is useful as a product read model, but it does not yet make the
session-to-process relationship explicit.

## Minimal Model

```text
AgentSession
  id
  agent_type
  transcript_path?
  conversation_id?
  start_ms?
  end_ms?
  context_hints?

ProcessTree
  id
  root_pid
  root_starttime_ticks
  first_seen_ms
  last_seen_ms

ProcessNode
  tree_id
  pid
  starttime_ticks
  parent_pid?
  parent_starttime_ticks?
  comm
  command?
  first_seen_ms
  last_seen_ms?
  exit_code?

SessionProcessMatch
  session_id
  process_tree_id
  confidence
  evidence_type
  evidence_summary
  first_seen_ms
  last_seen_ms
```

`SessionProcessMatch` is the important relationship. Example evidence types:

```text
proc_fd       transcript path appeared in /proc/<pid>/fd
ebpf_file     eBPF observed a process touching the transcript path
llm_traffic   LLM traffic matched agent/session hints
command_match root command matched a known agent rule
sticky        previous high-confidence binding still valid
```

## Keep Out Of The Core

`AgentDefinition`

Keep this as static/config data in an `AgentRegistry`, not as a view row. It can
own agent-specific process matchers, session log locations, traffic matchers,
parsers, and display names.

`AgentInstance`

Defer this. It may be useful later for daemon, container, remote, or long-lived
agent runtimes. Current CLI-agent workflows can be represented by
`AgentSession + ProcessTree + SessionProcessMatch`.

`AgentRun`

Do not keep both `AgentRun` and `AgentSession`. Use `AgentSession`.

`ObservationEdge`

Too generic for now. It risks turning the view into a graph database. Use the
narrow `SessionProcessMatch` relationship.

`workspace`

Workspace is not reliably inferable. Treat it as an optional context hint, never
as identity or required attribution state.

```text
ContextHint
  key
  value
  source
  confidence
```

Example:

```text
key: workspace_path
source: proc_cwd | agent_log | transcript_path | command_arg
confidence: 0.40..0.95
```

## Field Discipline

Do not make derived or unstable values core identity fields:

- `agent_name`: derive from `agent_type` through `AgentRegistry`.
- `status`: derive from end timestamps, live process state, or recency where
  possible.
- `tokens`: aggregate from token rows.
- `tools`: aggregate from tool rows.
- `cpu` and `rss`: aggregate from resource samples.
- `process_count`: aggregate from process nodes.
- `model`: sessions may use multiple models; expose `primary_model` as a summary
  only if needed.
- `command`: belongs to a root `ProcessNode`; derive `ProcessTree.root_command`
  for display.

## Process Tree Storage

The process tree is recursive conceptually, but should be stored as flat nodes
with parent references.

```text
ProcessNode
  tree_id
  pid
  starttime_ticks
  parent_pid?
  parent_starttime_ticks?
  comm
  command?
```

Render recursion in the UI:

```text
claude(pid=100)
  node(pid=101)
    npm(pid=102)
      node(pid=103)
```

Flat storage is better because:

- PIDs are reused, so identity needs `pid + starttime_ticks`.
- children appear and exit over time
- parents may disappear before children are sampled
- incremental updates and SQLite storage stay simple
- perf/Nsight views usually aggregate flat samples first, then render hierarchy

## Leaf Rows

Keep leaf facts scoped to the side that directly owns them.

Session-scoped:

```text
LlmCall
ToolCall
TokenUsage
```

Process-scoped:

```text
ProcessExec
FileEvent
NetworkEvent
ResourceSample
```

Ownership rule:

```text
Llm/tool/token rows attach to AgentSession.
File/network/resource/process rows attach to ProcessTree or ProcessNode.
SessionProcessMatch connects the two sides.
```

If no reliable match exists, show OS activity as process-only or unattributed.
Do not silently attach it to a session.

## Current Complexity

Identity and attribution are currently spread across:

- `sources/proc.rs`: process discovery and process-tree heuristics
- `sources/session.rs`: local transcript discovery and parsing
- `view/projection.rs`: LLM correlation and row projection on MaterializedView
- `cmd_top.rs` (live capture half): proc fd scans, eBPF file evidence, sticky live bindings
- frontend rendering: process trees are built from snapshot `process_nodes` and
  timestamp-matched `audit_events`

The repeated concepts are agent classification, session identity, process-tree
ownership, match confidence, and source provenance.

## View Implications

Minimal new rows:

```text
ProcessNodeRow
SessionProcessMatchRow
```

Existing `SessionRow` can evolve toward `AgentSessionRow`.

`SessionRow.pid` should become a derived convenience field from the best
`SessionProcessMatch`, not the canonical relationship itself.

## UX And Perf/Nsight Mapping

The top-level UX object remains the agent session. Process-level details are
drill-down evidence.

```text
Agent Session
  -> best matching process tree
      -> process nodes
          -> CPU/RSS/resource samples
          -> exec/file/network events
  -> LLM calls
  -> tool calls
  -> token usage
```

Good provenance labels:

```text
local
proc
proc_fd
ebpf
ebpf_file
llm
sticky
db
unattributed
```

## Refactor Direction

Deletion-first checklist:

- [x] Remove agent-session inference from LLM/token telemetry projection.
- [x] Remove the saved-DB top path that reconstructed process families from
  audit events.
- [x] Add view-native `ProcessNodeRow` so snapshots can expose process structure
  without frontend audit-event tree reconstruction.
- [x] Restore frontend process-tree rendering from `process_nodes`; audit rows do
  not create saved snapshot process-tree nodes.
- [x] Keep live `/proc` process-family handling as the live process-tree builder;
  saved snapshots use `process_nodes`.
- [x] Treat `SessionRow.pid` as display data only; do not add new writes that use
  it as the canonical session-process relationship.
- [ ] Add explicit `SessionProcessMatchRow` only when session-process matching has
  enough evidence to avoid reusing `SessionRow.pid` as ownership.

## Invariant

Every session-level OS attribution must be explainable by a match.

If the system shows CPU, files, network, or process activity under an agent
session, the view should be able to point to the `SessionProcessMatch` that made
that attribution. If no match exists, the activity remains process-only or
unattributed.
