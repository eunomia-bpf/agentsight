# Agent Footprint Map: A New Visualization for AI Agent Observability

## The Problem

Every existing agent observability tool visualizes the **application layer** only:

| Tool | What it shows | Visual paradigm |
|------|--------------|-----------------|
| LangSmith / Langfuse | API calls, token usage, prompt/response | Nested trace tree (borrowed from APM) |
| CodeBurn (7.3k stars) | Token cost breakdown from ~/.claude | TUI dashboard + daily cost charts |
| Agent Flow | Tool call node graph | Interactive canvas |
| AgentOps | Session timeline | Waterfall / Gantt |
| Datadog (DASH 2025) | Agent decision flow | Execution flow chart |

**None of them see what the agent actually did to the OS.** When Claude
requests `Bash("df -h")`, these tools record the tool_use and the result text.
They cannot tell you that `bash` spawned `df`, which opened `/proc/mounts`, or
that 6 background `git` processes ran during startup that no tool_use requested.

Conversely, OS-level tools (strace, eBPF, perf) see every syscall but have no
idea which LLM turn caused them.

**AgentSight sits at the intersection** — it captures both SSL/TLS traffic (LLM
intent) and kernel events (OS reality) via eBPF. The data exists. What's missing
is the visualization that makes it instantly legible.

## The Opportunity

Brendan Gregg's flame graphs succeeded because they followed a formula:

1. **One question, answered at a glance** — "Where is CPU time being spent?"
2. **Visual structure = data structure** — call stacks are trees, the graph is a tree
3. **One visual channel = one metric** — width = time. Color is decorative.
4. **Works as a static image** — SVG you can paste in Slack, blog posts, incident reports
5. **Scale-invariant** — 10 functions or 10,000 functions, same readability

No equivalent exists for AI agents. The unclaimed question:

> **"What did this agent actually do to my system?"** (9 words)

## The Concept: Agent Footprint Map

Agent execution has a natural tree structure:

```
Session
├─ LLM Turn 1 (tool_use: Read /etc/hostname)
│  └─ OS effects: (none — internal read)
├─ LLM Turn 2 (tool_use: Bash "df -h")
│  └─ OS effects: bash → df
├─ LLM Turn 3 (response, 244 tokens out)
│  └─ OS effects: (none)
└─ Background (not from any tool_use)
   └─ git×6, cat×2, head×3, sed×2 (startup probes)
```

### Visual mapping

```
┌─────────────────────────────────────────────────────────┐
│ Turn 1: Read /etc/hostname           ███░░░  $0.04      │
│                                      (no OS effect)     │
├─────────────────────────────────────────────────────────┤
│ Turn 2: Bash "df -h"          ██████████░░░░░  $0.02    │
│  └ bash → df                  ██                        │
├─────────────────────────────────────────────────────────┤
│ Turn 3: response              ████████████████  $0.03   │
│                                      (no OS effect)     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤
│ ⚠ Background (no tool_use)                              │
│  git×6  cat×2  head×3  sed×2          (startup)         │
└─────────────────────────────────────────────────────────┘
  ◀──────────── width = tokens/cost ──────────────▶
```

### Design properties

- **Width = token consumption or dollar cost.** Widest block = most expensive
  turn. One glance tells you where the money went.
- **Nested layers = intent → effect chain.** LLM turn on top, OS processes
  nested below. The hierarchy IS the correlation.
- **Dashed "Background" section = AgentSight's unique value.** System activity
  not attributable to any tool_use. This is what no other tool can show.
- **Static SVG output.** Paste in a blog post or Slack and it's still
  self-explanatory. No running server needed.

### Comparison with flame graphs

| Property | Flame Graph | Agent Footprint Map |
|----------|------------|-------------------|
| One question | "Where is CPU time spent?" | "What did this agent do to my system?" |
| Data structure | Call stack (tree) | Turn → tool_use → OS effects (tree) |
| Width encodes | CPU time proportion | Token cost / dollar cost |
| Unique insight | Hidden hot functions | Hidden OS activity (Background section) |
| Output format | SVG | SVG |

## Research Landscape (2025-2026)

### What exists

- **Trace trees** (LangSmith, Langfuse, Braintrust) — nested span view, borrowed from Jaeger/Zipkin
- **Node graphs** (Agent Flow, Arize Phoenix, Datadog) — agent decision DAGs
- **Session waterfalls** (AgentOps, New Relic) — time-axis Gantt-style view
- **Cost dashboards** (CodeBurn, Helicone) — token/dollar breakdowns
- **Academic work**: AGDebugger (CHI 2025) for fork/branch visualization, AgentStepper for dual-column agent-vs-tool view, DiLLS for layered summaries

### What doesn't exist

1. **API intent ↔ OS behavior correlation visualization** — nobody
2. **Agent "flame graph"** (width=cost execution hierarchy) — nobody
3. **Multi-agent swimlane diagrams** — nobody
4. **Wasted work / abandoned branch visualization** — nobody
5. **Context decay visualization** — nobody

### Why AgentSight is uniquely positioned

AgentSight already captures both layers via eBPF:
- SSL/TLS interception → LLM API calls, tool_use content, token usage
- Process tracing → exec, exit, process trees
- File monitoring → openat syscalls
- All with nanosecond timestamps for correlation

The correlation engine exists. The data is in SQLite. What's needed is the
rendering layer that turns it into an Agent Footprint Map.

## Implementation Path

1. **Data**: Already captured — `token_usage`, `audit_events`, `canonical_events` tables in session DB
2. **Correlation**: Match tool_use timestamps with process/file events in the same time window
3. **Rendering**: Generate SVG from correlated data (similar to how flamegraph.pl generates SVGs from collapsed stacks)
4. **CLI**: `agentsight footprint --db session.db` → outputs SVG or HTML
5. **Integration**: Embed in web UI at localhost:7395, export for blogs/reports

## References

- Brendan Gregg, [Flame Graphs](https://www.brendangregg.com/flamegraphs.html) (2011)
- Brendan Gregg, [AI Flame Graphs](https://www.brendangregg.com/blog/2024-10-29/ai-flame-graphs.html) (2024)
- [AGDebugger: Interactive Debugging of Multi-Agent Systems](https://arxiv.org/abs/2503.02068) (CHI 2025)
- [AgentStepper: Interactive Debugging of Software Development Agents](https://arxiv.org/abs/2602.06593) (2026)
- [DiLLS: Interactive Diagnosis via Layered Summary](https://arxiv.org/abs/2602.05446) (2026)
- [AgentTrace: Causal Graph Tracing for Root Cause Analysis](https://arxiv.org/abs/2603.14688) (2026)
- [AgentSight: System-Level Observability Using eBPF](https://arxiv.org/abs/2508.02736) (2025)
- [CodeBurn](https://github.com/getagentseal/codeburn) — token cost TUI dashboard
- [Agent Flow](https://github.com/patoles/agent-flow) — Claude Code node graph visualization
