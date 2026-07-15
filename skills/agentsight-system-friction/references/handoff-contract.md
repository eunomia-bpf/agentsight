# Correlation Summary

Use this to pass system findings to `agent-interaction-insights` without opening
raw AgentSight data.

## Shape

A correlation summary should contain:

- severity
- plain-language system claim
- redacted evidence summary
- optional correlation hints such as time range, tool category, command category,
  path category, host category, or session category
- privacy mode
- whether raw data is included

For reader-facing HTML, write this as prose or bullets. Use exact join keys only
internally or in private-debug output requested by the user.

## Use

- Keep evidence summaries compact and redacted.
- Render shareable HTML with operating categories, short evidence summaries, and
  capture gaps.
- If user intent is needed, hand this summary to `agent-interaction-insights`.

## Optional Interaction Summary Input

If the user supplies an already summarized interaction finding, use it only as
context for ranking system findings. Route raw transcripts to
`agent-interaction-insights`.
