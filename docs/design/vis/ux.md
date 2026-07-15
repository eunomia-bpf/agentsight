# AgentSight UX: perf/top/strace/Nsight for Coding Agent Runs

## Goal

AgentSight should make one sentence true in both CLI and saved reports:

> See what coding agents actually do to your machine, and connect those actions
> back to the prompts, model calls, and tool decisions that triggered them.

The product should not feel like another generic LLM dashboard. It should feel
like a local systems tool for agent runs: record first, inspect later, export the
run artifact, and drill from high-level intent down to OS-level effects.

The UX model is:

```text
prompt / model call / tool decision
  -> process tree
    -> file, network, resource, stdio side effects
      -> result, risk, artifact
```

This document defines the desired command line and report experience. It complements:

- `vis.md`: Agent Footprint Map, the agent equivalent of a flame graph.
- `agent-workspace-map.md`: workspace/file behavior visualizations.
- `why.md`: why boundary tracing/eBPF is needed.

Current CLI note: the user-facing entrypoint is `agentsight top` for live
session monitoring. Use `agentsight record -- <command>` to save a run and
`agentsight report` to inspect saved runs. Low-level tracing is currently
exposed as `agentsight debug trace`; top-level `script`, `trace`, and `export`
commands below are future UX proposals unless explicitly marked as current.

## Product Positioning

AgentSight should borrow the interaction grammar of familiar systems tools:

| Tool | User expectation | AgentSight equivalent |
| --- | --- | --- |
| `perf top` / `top` | live ranked activity | `agentsight top` |
| `perf record` | capture a session artifact | `agentsight record -- <agent>` |
| `perf report` | inspect a saved artifact | `agentsight report` |
| `perf script` | dump ordered events | future: `agentsight script` |
| `strace -f -tt -e ...` | follow subprocesses and filter events | current: `agentsight debug trace`; future: `agentsight trace` |
| Nsight Systems | time-correlated lanes and markers | Agent run timeline with LLM/tool/process/file lanes |

AgentSight is not trying to replace SDK trace tools. It should be the local,
framework-neutral run activity layer underneath them.

## User Questions First

The UX should start from user questions, not from event types. A user rarely
opens AgentSight because they want "a timeline"; they open it because they need
to decide whether an agent run was correct, safe, efficient, or explainable.

| Scenario | User question | Best first answer | Evidence needed |
| --- | --- | --- | --- |
| Normal run receipt | What did the agent actually do? | `report` summary | LLM calls, commands, files, network, exits |
| PR review | Can I trust this AI-generated diff? | blast radius section in `report` | read/write set, changed files, tests, high-risk paths |
| File-level review | Why did this file change? | provenance chain for one path | prompt/tool/process/file event/diff hunk |
| Debugging | Why did the agent fail or loop? | failed-command and repeated-work sections | tool calls, process exits, repeated reads/greps, tokens |
| Security review | Did it touch secrets, config, or workspace-external paths? | policy/side-effects section | file paths, cwd, argv, network hosts, attribution |
| Hidden behavior | What happened outside observed tool decisions? | unattributed activity section | process/file/network events without semantic parent |
| Capture audit | What could AgentSight not see? | capture health section | probe status, adapters, event loss, observed/inferred fields |

This is the main product distinction from both sides:

- LLM dashboards answer "what did the agent say or call?"
- System tools answer "what did this process do?"
- AgentSight should answer "which agent intent caused which system effect, and
  what system effects had no visible agent intent?"

## Core UX Principles

### 1. Facts First, Interpretation Second

Default output should distinguish:

- observed facts: process exec, file write, network host, token usage
- inferred correlation: "this write likely followed this tool call"
- unavailable data: prompt not captured, SSL not attached, adapter not run

Never imply certainty where only timestamp correlation exists.

### 2. One Run Is the Primary Object

Everything revolves around a recorded run:

```text
run id
start/end time
root command or attached PID
SQLite DB path
capture capabilities
event counts
derived reports
exported artifacts
```

Every output should show which run is loaded and whether it is live or static.

### 3. Intent-to-Effect Is the Main Story

The first view should not be raw logs, a generic timeline, or a process tree.
The first view should answer:

> What did the agent do, and why?

The primary object should be a causality ledger:

```text
User task
  LLM call
    tool decision
      process
        file/network/resource effects
```

### 4. Unattributed Behavior Must Be Visible

Unattributed behavior is a core differentiator. Reports must show a clear section
for system activity that happened without an observed prompt/tool cause:

```text
Background / unattributed
  git status
  shell startup probes
  package manager postinstall
  network connection not tied to LLM traffic
```

This should not be hidden in raw logs.

### 5. Every Summary Must Point Back to Evidence

Useful outputs should be shareable, but they also need raw evidence pointers:

- terminal text
- JSON
- SQLite
- static HTML
- SVG for footprint/workspace maps
- Markdown report for PR review or incident notes

## The System-Agent Intersection

The central object is not an LLM span and not a syscall. It is an edge between
the agent layer and the system layer:

```text
agent intent/event  ->  system effect
```

Examples:

```text
user prompt                    -> run starts
LLM request/response            -> model/token/cost evidence
tool decision: Bash("npm test") -> npm process tree, file reads, exit code
tool decision: Edit(file)       -> file write/truncate/rename, diff hunk
tool decision: install package  -> package manager process, registry network, lockfile write
no observed tool decision       -> unattributed process/file/network event
```

AgentSight should make these edges visible as first-class data. A plain process
tree is not enough because it loses the agent reason. A plain agent trace is not
enough because it loses the actual OS effects.

The useful derived entities are:

| Entity | Meaning | Typical source |
| --- | --- | --- |
| Run | One recorded agent session | `record`, `stat -- <cmd>`, attach session |
| Intent | User prompt, model call, tool decision, plan step | TLS payload, local transcript, adapter |
| Effect | Process exec/exit, file operation, network host, resource sample | eBPF/system runner |
| Attribution edge | Why this effect is linked to this intent | timestamp, PID/tree, cwd, tool payload, adapter |
| Unattributed effect | System activity with no observed semantic parent | process/file/network event without matching intent |
| Verdict | Safe/risky/policy violation/needs review | path rules, host rules, user policy, heuristics |

The strongest views are built from edges, not nodes. For example:

```text
Bash("npm test")
  -> exec npm
  -> exec node
  -> read package.json
  -> read tests/api.test.ts
  -> exit 1
```

This answers a different question from either source alone:

- Agent trace alone: the agent asked to run `npm test`.
- System trace alone: `npm` and `node` ran and touched files.
- AgentSight: this tool decision produced this concrete process/file/result chain.

## Answer Surfaces

The initial product should prioritize command-line and report surfaces. Each
surface should answer a different class of questions:

| Surface | Primary question | Secondary questions |
| --- | --- | --- |
| `top` | What is active or dominant right now? | hot processes, risky paths, token-heavy model calls, unattributed activity |
| `record` | What artifact did we capture? | DB path, capture health, attach target, replay commands |
| `report` | What happened and why does it matter? | counters, intent/effect chain, blast radius, side effects, warnings |
| `script` | What is the ordered evidence stream? | exact time, PID, command, event kind, raw summary |
| `trace` | What did this process family do in detail? | strace-like filtered process/file/network/LLM events |

`report` should be the main product surface for trust and review. It should
contain sections that map directly to user decisions:

```text
Run receipt
Intent -> effect chain
Blast radius
Changed/read files
Commands and exits
Network/API activity
Unattributed activity
Capture health
Raw evidence pointers
```

## Implementation Boundary: Analyzer vs Renderer

AgentSight currently has an `OutputAnalyzer`, but that is not the human-readable
`top`/`report` printer. It is a streaming analyzer that prints each event as raw
JSON while the capture stream is being drained.

The product output should use a separate query-time rendering layer:

```text
runners
  -> runner analyzers
    -> AgentRunner merged stream
      -> global analyzers
        -> MaterializingAnalyzer
          -> row sinks (SQLite / OTEL)
            -> query model
              -> top/report/script renderers
```

Responsibilities:

- Analyzer: normalize, filter, parse, export, or store events while capture is
  running. It should not own terminal table layout or report wording.
- Storage/projector: persist raw events and project canonical events, LLM calls,
  token usage, audit events, sessions, and adapter results.
- Query model: aggregate saved data into `AgentTopSnapshot`, `AgentSection`,
  `ActivityRow`, `ReportModel`, and similar typed structures.
- Renderer: print text, JSON, Markdown, or other formats from those typed query
  models.

`cmd_perf.rs` can remain a thin orchestration entry point, but the printing
logic should move toward a dedicated module such as:

```text
collector/src/cli_print/
  mod.rs
  top.rs
  report.rs
  script.rs
  table.rs
  format.rs
```

This keeps `top` and `report` free to become richer without turning analyzer
code into UI code. The only printer that belongs inside an analyzer is the
raw event stream printer used for debug/live event output.

## Command Line UX

### Top-Level Shape

Current top-level command set:

```bash
agentsight top     [options]
agentsight record  [options] [-- command ...]
agentsight report  [options]
agentsight report prompts [options]
agentsight report list
agentsight discover
agentsight report      ...
agentsight debug   ...
```

Future shorthand commands can be considered after the current surfaces are
stable:

```bash
agentsight script  [options]
agentsight trace   [options]
agentsight export  [options]
```

### Run Counters

The old top-level counter surface has been removed. Counter-focused views now
live under `agentsight report`: the default report prints a concise run summary,
while structured counters are available through focused report queries such as
`agentsight report token --json`.

### `agentsight top`

Like `top` or `perf top`: live ranked view. The primary unit should be an
agent root process or agent process family, not a global dashboard panel.

Examples:

```bash
agentsight top
agentsight top --db run.db
agentsight top -p 1234
agentsight top -c claude
agentsight top --sort tokens
agentsight top --view files
agentsight top --once
```

Default layout should mirror normal `top`: a compact summary followed by a
ranked table. For AgentSight, the top-level table ranks agent sections. Each
agent section represents one root process plus descendants:

```text
AgentSight top - 3 agents   live   00:02:13   events: 7,820   lost: 0

AGENT   PID    CPU%  RSS    TOKENS  EXECS  FAIL  FILES  NET  UNATTR  COMMAND
claude  1234   12.1  318M   128k       42     3    318    7      12   claude
codex   2220    8.4  210M    76k       31     1    144    3       4   codex
gemini  3310    4.0  180M    91k       12     0     62    2       1   gemini

[expanded claude]
  SCORE  RATE/s  COUNT  KIND          STATUS  ENTITY                 ATTRIBUTED TO
   98.1    62.0    420  process.exec  ok      node                   Bash("npm test")
   72.4    39.4    267  file.read     ok      src/api/handler.ts     grep "handler"
   41.2    15.2    103  file.write    risk    package-lock.json      npm install
   19.3     5.7     38  process.exit  fail    npm                    Bash("npm test")
   12.0     4.4     29  process.exec  warn    git status             unattributed
```

This keeps the shape of normal `top` while making AgentSight's extra value
visible: each hot system object is tied back to an agent decision when possible.

Rules:

- An agent section corresponds to an agent root PID plus descendants.
- Child processes, files, network, resource samples, and LLM calls should roll
  up into that agent section.
- Unattributed events should first be grouped inside the owning agent process
  family. Only events that cannot be assigned to any agent root should appear in
  a global background section.
- Expanded rows should be system-agent edges: `kind + entity + attributed to`.
- The first table answers "which agent is active or risky?" The expanded table
  answers "which system effects inside this agent are active or risky?"

Implementation notes:

1. Build agent roots from the recording target: launched command root PID,
   attached PID, or matching `comm`.
2. Build process families from process exec/exit events using `pid`/`ppid`.
3. Assign every event to the nearest owning agent family by `pid`, descendant
   PID, or adapter session metadata.
4. Keep unmatched events in a global background bucket.
5. Roll up per-agent counters: tokens, execs, failed exits, file ops, hosts,
   max CPU/RSS, unattributed count.
6. Build per-agent activity rows from system-agent edges:
   `kind`, `entity`, `count/rate/score`, `status`, `attributed_to`.
7. Print top-level agent rows first; print the selected/expanded agent's edge
   rows below it.

Interactive keys:

```text
space    expand/collapse selected agent
s        change sort
f        filter
t        time window
a        show attributed/unattributed
q        quit
```

### `agentsight record`

Like `perf record`: capture a run artifact.

Examples:

```bash
agentsight record -- claude "fix the failing API test"
agentsight record -c claude
agentsight record -p 1234
agentsight record --db run.db -- claude
```

Default output:

```text
AgentSight record
  target: claude "fix the failing API test"
  db: ~/.local/share/agentsight/sessions/20260602-113015.db

Recording. Press Ctrl-C to stop.
```

At exit:

```text
Recorded 13.2s to ~/.local/share/agentsight/sessions/20260602-113015.db
Run:
  agentsight report --db ...
```

### `agentsight report`

Like `perf report`, but for agent runs.

Examples:

```bash
agentsight report
agentsight report --db run.db
agentsight report --section side-effects
agentsight report --markdown -o report.md
agentsight report --json
```

Default report structure:

```text
AgentSight report: claude "fix the failing API test"

Summary
  13s, 1 LLM call, 1,380 tokens, 4 processes, 3 files, 2 hosts

Intent -> effect chain
  user prompt: fix the failing API test
    model: claude-sonnet-4
    tool: Bash("npm test")
      process: npm -> node
      exit: failure, code 1
    tool: Edit("src/api/handler.ts")
      file: write src/api/handler.ts
    tool: Bash("npm test")
      process: npm -> node
      exit: success, code 0

Side effects
  files written:
    src/api/handler.ts
    tests/api.test.ts
    package-lock.json
  network:
    api.anthropic.com
    registry.npmjs.org

Unattributed activity
  none observed

Capture notes
  prompts: observed via TLS
  process/file events: observed via eBPF
  correlation: timestamp + process context
```

### Future: `agentsight script`

Like `perf script`: ordered event stream. Current CLI users should query saved
sessions with `agentsight report audit --json` until this shorthand exists.

Examples:

```bash
agentsight script --db run.db
agentsight script --db run.db -F time,pid,comm,kind,summary
agentsight script --db run.db -e process,file
agentsight script --json --db run.db
```

Example output:

```text
00.000  claude[1200] llm.request      POST api.anthropic.com/v1/messages
01.232  claude[1200] tool.call        Bash("npm test")
01.240  npm[1244]    process.exec     /usr/bin/npm test
01.510  node[1250]   file.open        /workspace/app/package.json
03.902  npm[1244]    process.exit     code 1
```

### Current: `agentsight debug trace`; Future: `agentsight trace`

Like `strace`: detailed follow/filter mode. The current implemented command is
`agentsight debug trace`; the shorter top-level `trace` spelling is a future UX
proposal.

Examples:

```bash
agentsight debug trace -c claude
agentsight debug trace -p 1234 --process true --ssl false
agentsight debug trace -c claude --ssl true --process true --server
```

Design notes:

- `-f`: follow children.
- `-tt`: absolute timestamps.
- `-T`: include event duration when known.
- `-e`: event selection, similar to `strace -e`.
- `-o`: write raw event stream.
- `--db`: write normalized run DB.

## Report Sections

Make `report` the place where the system-agent intersection is easiest to see.

### Run Receipt

Question:

> What was the run's behavior radius?

Output:

```text
Touched files: 17
Read files: 143
Generated files: 6
Deleted files: 1
External network hosts: 4
Failed commands: 2
Unattributed activity: 6 process execs, 12 file ops
High-risk paths:
  .github/workflows/release.yml
  package-lock.json
  ~/.config/tool/config.json
```

This is the command-line version of the AI PR Blast Radius View from
`agent-workspace-map.md`.

### Intent -> Effect Chain

Question:

> Which agent decision caused this system behavior?

Output:

```text
tool: Bash("npm test")
  process: npm[1244] -> node[1250]
  files read: package.json, tests/api.test.ts
  exit: failure, code 1
```

This is the core AgentSight object. It should be present in the CLI report.

### Why This File Changed

Question:

> Why did this file change?

Output:

```text
src/api/handler.ts
  read after: grep "handler"
  written by: tool Edit("src/api/handler.ts")
  related command: npm test
  result: later test success
  attribution: observed tool payload + file write event
```

This is the textual form of the provenance DAG from `agent-workspace-map.md`.

### Unattributed Activity

Question:

> What happened at the system layer without an observed agent/tool parent?

Output:

```text
unattributed process execs:
  git status x6
  cat ~/.config/tool/config.json

unattributed network:
  telemetry.example.com
```

This is where AgentSight should feel most different from SDK trace tools.

### Capture Health

Question:

> Which parts of the answer are observed, inferred, or unavailable?

This section should be short but always present.

## Capture Health UX

AgentSight should always explain what it could and could not see:

```text
Capture health
  process tracing: ok
  file tracing: ok
  SSL/TLS plaintext: partial
  prompts: observed
  responses: observed
  tool calls: inferred from prompt payload
  event loss: 0
  adapters: claude-code v1
```

This belongs in:

- `report`
- exported reports

## Empty and Partial States

Empty states should be action-oriented:

```text
No run loaded.

Start a run:
  agentsight record -- claude

Or open an existing run:
  agentsight report --db run.db
  agentsight script --db run.db
```

Partial states should be explicit:

```text
No prompts captured.
Process/file/network facts are still available.

Likely causes:
  SSL binary was not discovered
  provider used unsupported TLS path
  traffic came from a different process
```

## Visual Language

AgentSight is an operational tool. It should feel closer to Nsight Systems,
perf, strace, and a PR review tool than to a marketing dashboard.

Preferred:

- dense tables
- timelines with lanes
- process/file provenance trees
- stable monospace identifiers
- restrained badges for risk/status
- export commands

Avoid:

- decorative presentation
- vague health cards that cannot point to events
- charts that cannot be traced back to events
- hiding raw data behind summaries

## Search and Filter Model

Filters should mirror CLI event selectors:

```text
kind:process.exec
kind:file.write
path:~/.aws
host:registry.npmjs.org
comm:npm
status:failure
attribution:unattributed
risk:high
model:claude-sonnet
```

The same filter grammar should work in:

- `agentsight script -e ...`
- `agentsight top --filter ...`
- `agentsight report --filter ...`
- export commands

## MVP Priorities

### P0: Make the Core Claim Visible

1. Run receipt in `report`.
2. Intent -> effect chain in `report`.
3. Side effects and blast radius sections in `report`.
4. Capture health block.
5. Attributed vs unattributed grouping.

### P1: Make It Shareable

1. `agentsight report --markdown`.
2. Footprint SVG export.
3. Workspace changed-file table.
4. `agentsight script`.
5. Raw evidence pointers for every summarized claim.

### P2: Make It Feel Like a Systems Tool

1. Interactive `top`.
2. Filter grammar shared by `top`, `script`, and `report`.
3. Strace-like `trace -f -tt -e ...`.
4. Event-loss and overhead counters.
5. TUI mode for SSH-only environments.

## What Is Good Enough for the Next Release?

The next release is good enough when a user can run:

```bash
agentsight record -- claude "fix the failing API test"
agentsight report
agentsight script --summary
```

And immediately answer:

1. What prompt/model/tool sequence happened?
2. What commands actually ran?
3. What files changed or were read?
4. What network destinations were contacted?
5. Which actions were not attributable to an observed tool decision?
6. Which details are observed vs inferred?

If the output only lists process trees and raw logs without connecting them to
agent intent, it is not good enough, even if the underlying data is present.
