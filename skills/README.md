# AgentSight Skills Pack

This directory contains skills for AI coding agent behavior analysis using AgentSight data.

## Available Skills

| Skill | Description |
|-------|-------------|
| [agent-session-inventory](agent-session-inventory/) | Summarize agent session histories from local logs, AgentSight data, or telemetry exports |
| [agent-friction-analysis](agent-friction-analysis/) | Diagnose agent friction and cost hotspots from traces and session data |
| [agent-behavior-artifact](agent-behavior-artifact/) | Generate shareable HTML artifacts from agent behavior analysis |

## Data Sources

These skills work with:

- AgentSight snapshot JSON (`agentsight report export -o snapshot.json`)
- AgentSight record SQLite databases (`agentsight-*.db`)
- AgentSight monitor SQLite databases (`~/.agentsight/monitor/*.db`)
- Claude Code native session logs (`~/.claude/projects/*`)
- OpenAI Codex native session logs (`~/.codex/sessions/*`)
- OpenTelemetry GenAI trace exports (JSON/spans)
- LangSmith run JSON exports
- Langfuse trace exports

## Installation

These skills are designed for use with Claude Code or OpenAI Codex. To install:

```bash
# Clone into your skills directory
cp -r skills/* ~/.claude/skills/  # For Claude Code
cp -r skills/* ~/.codex/skills/   # For OpenAI Codex
```
