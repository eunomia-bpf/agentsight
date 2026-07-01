# System Summary Input

Use this when consuming already summarized system findings from
`agentsight-system-friction`. Route raw AgentSight DBs and raw system rows to
`agentsight-system-friction`.

## Shape

A system summary should contain:

- severity
- plain-language claim
- redacted evidence summary
- optional correlation hints such as time range, tool category, command category,
  path category, host category, or session category
- privacy mode
- whether raw data is included

Use exact local identifiers only internally for correlation or in private-debug
output requested by the user.

## Use

- Treat the system summary as observed system evidence.
- Use interaction evidence for user intent, corrections, trust, and workflow.
- If exact system details are needed, ask for a system-friction analysis.
- In HTML reports, render system summaries as normal prose or bullets, not as
  machine-readable schema blocks.
