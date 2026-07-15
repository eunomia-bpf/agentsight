# Report Shapes

Choose the smallest shape that answers the user's question.

Routing:

- Immediate answer → Concise Findings
- Code-review handoff → PR Review Comment
- Recovery context → Incident Brief
- Full analysis or shareable output → Decision HTML Report (default); text-only when requested
- Management update → Team Brief

## Concise Findings

Use for quick analysis. Structure:

1. Decision question.
2. What should change next.
3. 3-7 recommendations ordered by expected leverage.
4. Supporting evidence and confidence.
5. Evidence gaps.

## Inventory Table

Use when the user asks what happened across sessions. Include sessions by project, agent, model, status, duration, tokens/cost, and tool counts when available.

## PR Review Comment

Use for code-review handoff. Structure:

1. Trust verdict or caveat.
2. Validation evidence: checks run and statuses.
3. File/process/network side-effect notes.
4. Reviewer checklist.

## Incident Brief

Use for recovery. Structure:

1. What changed.
2. Timeline of relevant actions.
3. Suspected cause, marked as inference.
4. Recovery or rollback targets.
5. Evidence gaps.

## Decision HTML Report

Use for full analysis or shareable output. Build a self-contained single file (inline CSS/JS, no backend, no fetch, no external assets).

Reader: decision owner, reviewer, team lead, or agent owner. Translate evidence into decision language and avoid exposing the report-generation process.

Before writing:

1. Write a one-sentence reader/decision contract.
2. First viewport: executive decision, top 3-5 changes, highest-confidence evidence in plain language.
3. Technical details in an appendix using reader-safe categories.

Section order:

1. Executive decision: what to trust, review, or change.
2. Next changes: 3-5 improvements with owner and confidence.
3. Decision overview: 3-5 modules matching the decision question.
4. Evidence in plain language: sources, observations, inferences, gaps.
5. Workflow backlog: instructions/policies to change before the next run.
6. Detailed findings: only as needed.
7. Appendix: source type, field categories, privacy notes, and evidence gaps.

Decision modules (pick 3-5):

- Trust verdict
- Validation coverage
- Correction hotspots
- Retry waste
- Task-fit matrix
- Instruction backlog
- Evidence coverage

Interactive controls may filter findings or copy a reader-facing summary using inline data.

For reader-facing HTML, use plain labels rather than schema names. Write "system summary" for external system evidence, "single-page report" for the output, "analysis boundary" for scope, and category labels for local identifiers.

## Team Brief

Use for non-interactive sharing. Keep it concise, avoid raw content, and focus on decisions: trust, cost, risk, follow-up.
