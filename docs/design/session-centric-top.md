# AgentSight Top as a Session Monitor

## Problem

`agentsight top` should not be a thin wrapper around Linux `top`.
Traditional `top` answers:

- Which process is using CPU or memory?

AgentSight must answer the agent-era version:

- Which agent session is active?
- What is that session doing to the machine right now?
- Which prompt, model call, tool call, process, file, or network edge does the
  activity belong to?

The unit of display is therefore an agent session, not a raw process. In the
agent era, a session is the process-like object users actually reason about.
Processes, subprocesses, prompts, token use, files, network, and failures hang
off that session.

## Product Definition

`agentsight top` is the primary live display for AgentSight.

Default behavior:

```bash
sudo agentsight top
```

should:

1. Discover currently running agent processes.
2. Discover agent-native local sessions such as Claude Code and Codex JSONL
   logs under the user's home directory.
3. Attach OS activity to the best owning session.
4. Start or reuse AgentSight capture when possible so eBPF-backed process, file,
   network, resource, prompt, token, and failure events flow into the display.
5. Fall back clearly when only process or only local session evidence is
   available.

The command should not feel like "read a DB". A DB is an implementation detail
and a durable artifact for `record`, `report`, and post-hoc analysis.

## Display Unit

Top-level rows are sessions:

```text
SESSION       AGENT    PID     CPU%  RSS    PROCS  TOKENS  TOOLS  EXECS  FAIL  FILES  NET  TRACE       COMMAND / PROMPT
claude:abc12  claude   1234    12.1  318M       7   128k      42     31     2    144    3  ebpf+local  fix the failing API test
codex:9fd31   codex    2220     8.4  210M       3    76k      18     12     1     62    2  ebpf+local  implement retry handling
proc:3310     gemini   3310     4.0  180M       2      -       0      0     0      0    0  proc        gemini
```

Rows should communicate evidence provenance:

- `ebpf`: live AgentSight capture events.
- `local`: agent-native session logs from the user's home directory.
- `db`: saved AgentSight SQLite session.
- `proc`: `/proc` process fallback.
- combinations such as `ebpf+local` or `local+proc`.

Expanded rows should be activity edges inside the selected session:

```text
KIND          RATE/s  COUNT  STATUS  ENTITY                    ATTRIBUTED TO
llm.request     0.2      3   ok      claude-sonnet-4           prompt turn 7
tool.call       0.4     18   ok      Bash                      assistant tool_use
process.exec    1.1     42   ok      npm test                  Bash("npm test")
file.write      0.4     12   warn    package-lock.json         npm install
network         0.1      2   ok      api.anthropic.com         LLM call
process.exit    0.1      2   fail    npm                       exit code 1
```

## Data Sources

### 1. eBPF / AgentSight Capture

This is the preferred source for system truth:

- process exec/exit
- file operations
- network destinations
- resource samples
- SSL/TLS plaintext LLM traffic when supported
- prompt/model/token data from parsed traffic

For `top`, capture should eventually work as:

1. Discover likely agent roots using process discovery:
   `claude`, `codex`, `gemini`, `opencode`, `openclaw`, `aider`, `goose`,
   plus explicit `-p` and `-c`.
2. Resolve the real executable for SSL uprobes, following symlinks and wrappers.
3. Start capture in a temporary live mode if no active AgentSight capture exists.
4. Persist only bounded live state unless the user asked to record.
5. Promote to durable SQLite only for `record`, explicit `--db`, or generated
   reports.

Open implementation issue: attaching eBPF from `top` requires the same
privilege flow as `record`, but the terminal experience must stay top-like.
The sudo prompt should happen once before the refresh loop starts.

### 2. Agent-Native Local Sessions

`top` should discover session logs on startup and refresh them periodically:

- Claude Code: `~/.claude/projects/**/*.jsonl`
- Codex: `~/.codex/sessions/**/*.jsonl`
- Future: Gemini CLI, OpenCode, Goose, Aider, OpenClaw when stable session
  locations or formats are known.

Local session logs provide:

- session identity
- model
- token usage
- tool calls
- prompt/turn summaries when present
- last updated time

They are not trusted as system truth, but they are the best way to name the
session and connect OS effects to the user's agent conversation.

### 3. `/proc`

`/proc` is a fallback and enrichment source:

- PID
- PPID and process family
- CPU
- RSS
- command line

It is not enough by itself. If the display is proc-only, `top` must say that
token, file, network, and failure columns are unavailable until capture or a
saved session is present.

### 4. Saved SQLite Sessions

SQLite is the durable evidence store used by:

- `agentsight record`
- `agentsight report`
- explicit `--db`
- exported dashboards and CI artifacts

`agentsight top --db run.db` is a static or polling saved-session view. It is
useful, but it is not the default mental model for `top`.

## Session Attachment Rules

Attach evidence to sessions in this order:

1. Exact session metadata PID if available.
2. Agent-native session file that is actively being written while a matching
   agent process is alive.
3. Process family root matching the agent type.
4. Saved SQLite session metadata.
5. Unattributed background bucket.

When multiple sessions of the same agent exist:

- Prefer the most recently modified local session.
- Prefer a session whose mtime changes during the `top` refresh interval.
- Do not duplicate CPU/RSS across multiple sessions unless the process match is
  unambiguous.
- Mark ambiguous rows with `TRACE local` or `TRACE proc` instead of pretending
  the attribution is strong.

## Persistence Policy

Default local persistence should be bounded and predictable.

Recommended policy:

- `record`: durable SQLite by default.
- `report`: reads the latest local/native session or latest AgentSight DB; when
  it materializes a report artifact, that artifact is explicit.
- `top`: should not create an unbounded durable DB just because it was opened.
  Live capture state should be temporary unless the user requests recording.
- `top --db`: reads a saved DB.
- `top --record` or a future equivalent can explicitly persist a live top
  capture.

Retention:

- Keep at most 50 MiB of default AgentSight session DBs.
- Keep a count cap as a secondary guard.
- Never delete user-provided `--db` paths.
- Never delete agent-native local sessions such as `~/.claude` or
  `~/.codex`; only read them.

## Implementation Stages

### Stage 1: Session-Centric Fallback Top

Implemented first because it changes the user-visible shape without requiring
runner lifecycle changes:

- Discover Claude and Codex local sessions.
- Show sessions as rows even without an AgentSight DB.
- Merge `/proc` CPU/RSS/process-family data when a matching agent process is
  active.
- Keep proc-only rows only as fallback.
- Add tests with fake Codex local session data.
- Reduce default DB retention to 50 MiB.

### Stage 2: Live Capture Integration

- Add a `top` live capture controller.
- Reuse binary discovery from `record`.
- Prompt for sudo before entering the refresh loop.
- Start process/system/SSL capture for discovered roots.
- Feed events into an in-memory activity window.
- Optionally persist only when requested.

### Stage 3: Activity Edges and Attribution

- Add expanded per-session activity rows.
- Attach process/file/network events to session root families.
- Attach LLM calls to local session turns when possible.
- Show attribution confidence.

### Stage 4: Interactive Top

- Selection and expand/collapse.
- Sort changes.
- Filters.
- Time window controls.
- Toggle evidence sources.

## Non-Goals

- Do not replace Linux `top`.
- Do not claim local agent logs are system truth.
- Do not silently upload or externalize prompts.
- Do not silently create unlimited DBs.
- Do not block the UI on full historical parsing of huge local session trees.

## Current MVP Contract

After Stage 1:

```bash
sudo agentsight top --once
```

should show a session-first table when local Claude/Codex sessions exist, even
without an AgentSight DB.

If a matching process is live, CPU/RSS/PROCS are attached. If not, the session
still appears with local token/tool evidence and `TRACE local`.

If no local session exists, `top` falls back to proc-only agent process rows and
prints a note that capture or local session evidence is unavailable.
