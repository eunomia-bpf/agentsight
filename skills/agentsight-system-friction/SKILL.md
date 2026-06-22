---
name: agentsight-system-friction
description: "Analyze AgentSight record snapshots, SQLite sessions, monitor DBs, and process/file/network/resource evidence to recommend concrete operational improvements to existing agent runs—timeouts, resource budgets, retry behavior, service lifecycle cleanup, network binding, file/log hygiene, and capture quality—and generate decision-oriented, reader-safe system HTML reports."
---

# AgentSight System Friction

## Goal

Use AgentSight evidence to recommend operational improvements for agent runs: resource budgets, retry behavior, service lifecycle, cleanup/recovery, network binding, file/log hygiene, tool/MCP behavior checks, and capture quality. Use system metadata, not raw conversation payloads. Default reports should help an owner improve the next run using changes to existing commands, configs, hooks, and workflows; they should not expose the local machine's private identifiers.

## Workflow

0. Privacy mode: Default to `team-share`. Read `references/privacy-modes.md` before including paths, commands, hosts, headers, or secret-adjacent details. For HTML reports and examples, use reader-safe summaries: path categories, command categories, host categories, port classes, session categories, resource windows, source types, counts, durations, and operating decisions. Exact local identifiers belong only in private-debug work requested by the user.

1. Route evidence to reference docs:
   - Sources and limits: `references/agentsight-sources.md`
   - Evidence model: `references/system-evidence-model.md`
   - Improvement classes: `references/operational-improvement-classes.md`
   - Friction taxonomy: `references/system-friction-taxonomy.md`
   - Correlation summary: `references/handoff-contract.md`
   - Output shapes: `references/report-shapes.md`
   - Examples: `references/example-patterns.md`

2. Build system facts:
   - Summarize session/process correlation, command exits, long-running processes, file activity, network endpoints, resource outliers.
   - Prefer timestamps, statuses, counts, durations, and categories over LLM payload columns.
   - Distinguish monitor aggregates from record-level evidence.
   - Preserve join keys internally for later correlation, but render category labels in reader-facing HTML by default.
   - If user intent is needed, state that it requires `agent-interaction-insights` or a user-provided summary.

   If the user provides both system data and raw interaction logs, analyze only system evidence here. Route raw conversation data to `agent-interaction-insights`.

3. Recommend operational changes:
   - Lead with 3-7 changes ranked by expected next-run improvement: less time, memory, disk churn, network exposure, cleanup burden, or uncertainty.
   - Prefer changes that fit the user's existing workflow: command timeouts, retry budgets, narrow-first reruns, cache/reuse rules, service leases, shutdown hooks, localhost binding, log rotation, redacted summaries, and capture fields.
   - Each: observed system effect, likely cause if inferable, concrete change, expected next-run benefit, confidence, success condition.
   - Include findings as supporting evidence. Use interaction summaries for user intent.

4. Shape output:
   - Quick diagnosis: what command, workflow, lifecycle, network, cleanup, or capture rule should change + compact evidence.
   - Full analysis or shareable output: self-contained HTML report. Name the reader and their operating decision before writing. Put verdict, top actions, and strongest evidence in the first screen. Technical details go in an appendix.
   - Incident recovery: cleanup and rollback changes, not just timeline.
   - Policy/MCP verification: pass/fail/unknown behavior + concrete workflow or configuration changes.
   - Conversation-level context needed: emit a compact system summary and recommend pairing with `agent-interaction-insights`.

## Output Contract

Always include:

- AgentSight source type: record snapshot, saved SQLite session, monitor DB, report export, or live/local summary
- time range and session categories when available
- observed system facts vs inferred causes
- correlation notes for optional interaction analysis
- evidence gaps and collection limits
- privacy mode used
- whether raw data is included, phrased for the reader rather than as schema labels
- the low-friction improvement path: budget, timeout, retry rule, service cleanup, network binding, file/log lifecycle, or capture field

Use redacted summaries by default.

For HTML reports, render local evidence as operating categories: source type, time window, session category, command category, path category, host category, port class, resource window, and capture gap. Put machine-readable correlation data only in private-debug output or a separate file requested by the user.

## Example Requests

```text
Analyze this AgentSight monitor DB for long-running processes and resource-heavy agent sessions.
```

```text
Use this AgentSight report export to tell me whether the agent touched files outside the workspace or contacted unexpected hosts.
```

```text
Create a system-level incident brief from this AgentSight record snapshot, with cleanup actions first.
```
