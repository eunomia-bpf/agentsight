---
name: agent-interaction-insights
description: Analyze agent transcripts, OTel GenAI spans, LangSmith/Langfuse/Datadog exports, or Claude/Codex/Gemini logs to recommend collaboration improvements—reduce corrections, improve trust, stop loops, compare agent fit—and generate decision-oriented, reader-safe HTML reports.
---

# Agent Interaction Insights

## Goal

Turn agent conversation and trace evidence into concrete next-run improvements: prompts, AGENTS.md/CLAUDE.md, workflow, validation rules, tool policy, or task routing. Lead with what should change; use evidence to justify the change. Default reports should read like decision material for an agent owner.

## Workflow

0. Privacy mode: Default to `team-share`. Read `references/privacy-modes.md` before extracting prompt/response/path/command/header/secret-adjacent data. For HTML reports and examples, use reader-safe summaries: short task/claim summaries, field categories, time ranges, counts, statuses, and analysis boundaries. Exact local identifiers belong only in private-debug work requested by the user.

1. Classify the question:
   - `improve-collaboration`: reduce corrections, clarify framing, improve AGENTS.md/CLAUDE.md.
   - `improve-trust`: make summaries and validation claims reliable.
   - `reduce-waste`: stop loops, retry churn, token/time waste.
   - `improve-workflow`: decide which instructions, checks, evals, policies, or workflow gates should change.
   - `compare-fit`: compare agents, models, prompts, or task classes.

2. Route evidence to reference docs:
   - Sources: `references/data-source-routing.md`
   - Improvement classes: `references/improvement-classes.md`
   - Evidence model: `references/common-evidence-model.md`
   - Friction taxonomy: `references/friction-taxonomy.md`
   - System summary input: `references/handoff-contract.md`
   - Output shapes: `references/report-shapes.md`
   - Examples: `references/example-patterns.md`

   If the user provides both interaction logs and AgentSight/system data, analyze only interaction evidence here. Consume already summarized system findings as compact context; route raw AgentSight data to `agentsight-system-friction`.

3. Build facts:
   - Map records into sessions, messages, LLM calls, tool attempts, validation claims, and user signals.
   - Extract minimal fields; distinguish observed from inferred.
   - Note when transcripts cannot prove process/file/network side effects.

4. Recommend improvements:
   - Lead with 3-7 changes ranked by expected leverage.
   - Each: target, change, evidence, expected benefit, confidence, next action.
   - Include findings as supporting evidence. Mark causal explanations as inference.

5. Shape output:
   - Quick questions: what to change next + compact evidence.
   - Full analysis or shareable output: self-contained HTML report. Name the reader and their decision before writing. Put decision, top changes, and strongest evidence in the first screen. Put source/privacy/capture details in a short appendix using plain language.
   - PR handoff: PR comment or checklist.
   - System side effects: recommend `agentsight-system-friction` when AgentSight data is available.

## Output Contract

Always include:

- evidence source and time range when available
- the user's likely decision question
- observed facts vs inferences
- evidence gaps
- privacy mode used, phrased for the reader rather than as schema labels
- whether raw logs were read and what field categories were extracted

Use redacted summaries by default.

For HTML reports, translate internal terms before writing: "system summary" for cross-boundary evidence, "single-page report" for the output, "analysis boundary" for scope, and category labels for local identifiers.

## Example Requests

```text
Analyze my last 20 Claude and Codex sessions. Where did the agents waste time and where should I improve AGENTS.md?
```

```text
Use this Langfuse export to tell me whether the agent really validated the PR.
```

```text
Generate a self-contained HTML report from these agent interaction findings, without raw prompts.
```
