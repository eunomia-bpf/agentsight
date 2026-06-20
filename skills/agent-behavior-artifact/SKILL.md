---
name: agent-behavior-artifact
description: Generate shareable single-file HTML artifacts from agent behavior analysis, including session summaries, friction findings, cost breakdowns, and evidence timelines. Use when the user asks for a shareable report, artifact, investigation page, or wants to export analysis for sharing with others. Do not use for quick inventory checks or live diagnosis.
---

# Agent Behavior Artifact

## Goal

Generate a self-contained HTML artifact that can be shared without a backend. The artifact should lead with findings and evidence, not raw data. It should be safe for sharing (privacy-aware) by default.

## When to Use

- User asks for a "shareable report" or "artifact"
- User wants to share findings with teammates
- User needs to document an investigation
- User wants a standalone file for archival

## When NOT to Use

- Quick session inventory (use agent-session-inventory)
- Root-cause diagnosis without output (use agent-friction-analysis)
- Live monitoring or debugging (use AgentSight directly)

## Privacy Considerations

By default, the artifact should NOT include:

- Raw prompts or responses
- Authentication headers or tokens
- Full file paths (redact home directory to `~`)
- API keys or credentials

For public artifacts, use aggregate data:
- Session counts, not session IDs
- Model distribution, not individual calls
- Token totals, not specific prompts

If the user explicitly requests raw details, warn them about privacy implications.

## Artifact Structure

### Header Section

- Title and generation timestamp
- Data source summary (monitor DB, record DB, snapshot, etc.)
- Date range covered
- Privacy level indicator (internal/public)

### Executive Summary

- 3-5 bullet findings with severity
- Key metrics: sessions, tokens, cost, failures
- One-sentence recommendation

### Findings Section

Each finding includes:
- Severity badge (high/medium/low)
- Category (token waste, tool failure, latency, resource)
- Evidence summary with specific numbers
- Recommended action

### Evidence Tables

- **Session Summary**: top sessions by tokens/cost/failures
- **Model Distribution**: calls and tokens by model
- **Tool Calls**: success/failure rates by tool type
- **Resource Peaks**: top CPU/memory events

### Timeline View (collapsible)

- Chronological event list
- Color-coded by event type
- Expandable details for each event

### Raw Data (collapsible, optional)

- JSON export of summary data
- Query results if requested
- Only include if explicitly requested

## Workflow

1. Run inventory and friction analysis first (or accept existing findings)
2. Determine privacy level (internal/public)
3. Generate HTML using embedded template
4. Validate output file exists and is valid HTML
5. Report file path and size

## Output Format

The generated HTML file should:

- Be a single self-contained file (CSS/JS inlined)
- Work offline in any modern browser
- Be under 1MB for typical sessions
- Use semantic HTML for accessibility
- Include a print-friendly stylesheet

## Commands

Generate from AgentSight snapshot:
```bash
python3 scripts/behavior_artifact.py \
  --snapshot snapshot.json \
  --out agent-behavior-report.html
```

Generate from record DB:
```bash
python3 scripts/behavior_artifact.py \
  --record-db agentsight-latest.db \
  --out agent-behavior-report.html
```

Generate public version:
```bash
python3 scripts/behavior_artifact.py \
  --snapshot snapshot.json \
  --public \
  --out agent-behavior-public.html
```

Include friction analysis:
```bash
python3 scripts/behavior_artifact.py \
  --snapshot snapshot.json \
  --friction-findings friction.json \
  --out agent-behavior-report.html
```

## HTML Template Elements

### Required CSS Classes

- `.artifact-header`: Title and metadata
- `.finding`: Individual finding card
- `.finding-high`, `.finding-medium`, `.finding-low`: Severity styling
- `.evidence-table`: Data tables
- `.timeline`: Event timeline
- `.collapsible`: Expandable sections
- `.metric-card`: Key metric displays

### Required JavaScript

- Collapsible section toggle
- Table sorting
- Timeline zoom/filter (optional)
- Copy-to-clipboard for code blocks

## References

Read `references/html-template.md` for the HTML template structure.
Read `references/artifact-examples.md` for example outputs.
