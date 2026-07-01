# Report Shapes

Choose the smallest shape that answers the system question.

Routing:

- Immediate diagnosis → System Findings
- Recovery or rollback → Incident Brief
- Tool/MCP/runtime-policy verification → Policy Or MCP Verification
- Full analysis or shareable output → Decision HTML Report (default); text-only when requested

## System Findings

Use for quick diagnosis:

1. AgentSight source and time range.
2. What command, workflow, lifecycle, network, cleanup, or capture rule should change next.
3. 3-7 recommendations ordered by risk, waste, or cleanup reduction.
4. Evidence table with reader-safe correlation categories.
5. Capture gaps and next-run instrumentation changes.

## Incident Brief

Use for recovery:

1. What changed on the machine.
2. Cleanup and rollback targets.
3. Timeline of process/file/network/resource events.
4. Suspected system cause, marked as inference.
5. Prevention changes: timeout, resource budget, cleanup hook, network binding, or capture field.

## Policy Or MCP Verification

Use for tool, plugin, MCP, or runtime-policy checks:

1. Claimed policy.
2. Observed system behavior.
3. Pass/fail/unknown verdict per observed behavior.
4. Evidence rows and capture gaps.

## Decision HTML Report

Use for full system analysis or shareable output. Build a self-contained single file (no backend, no fetch, no external assets, findings first, technical details summarized at the end).

Reader: agent owner, operator, security reviewer, or team lead. Translate AgentSight rows into operating decisions.

Before writing:

1. Write a one-sentence reader/decision contract.
2. First viewport: operating verdict, top 3-5 actions, highest-confidence evidence in plain language.
3. Technical details in an appendix using reader-safe categories.

Section order:

1. Executive decision: what should change before the next run.
2. Immediate actions: timeout, budget, retry, cleanup, binding, logging, or capture changes with done conditions.
3. System overview: 3-5 modules matching the system question.
4. Operational changes: command budgets, service lifecycle, network binding, file/log hygiene, capture fields.
5. Evidence in plain language: facts, inferences, monitor vs record limits.
6. Detailed evidence tables with category labels rather than exact private identifiers.
7. Appendix: source summary, capture coverage, privacy notes, and optional human-readable correlation summary.

Operating modules (pick 3-5):

- Operating verdict
- Resource pressure
- System impact
- Cleanup queue
- Network exposure
- Capture confidence
- Operational backlog

Interactive controls may filter findings or copy a reader-facing system summary using inline data.

For reader-facing HTML, convert local identifiers to categories such as "private project directory", "long-running local service", "external HTTPS target", "workspace-external path", or "resource peak window".
