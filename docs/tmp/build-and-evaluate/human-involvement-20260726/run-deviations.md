# Run deviations

## 2026-07-26: Codex subagent-source exclusion

The first complete computation produced 50,952 project-attributed user
messages, including 39,406 in one Codex root membership. This failed the
planned extreme-value and projection-pair audit.

Inspection of the referenced native rollout metadata showed that Codex nested
subagent files can be projected with `source_role=user`. Their
`event_msg/user_message` records are Agent-authored task prompts to subagents,
not human instructions. The repair uses native
`session_meta.thread_source=subagent` or nested `source.subagent` metadata to
exclude the entire rollout file from human-message, assistant-message,
interruption, approval, and interaction-timing reconstruction. Its projected
tool actions remain in the all-Agent-action denominator.

The invalid first-run CSVs, report, and figures are overwritten by the repaired
full run. The already completed third preflight is not repeated because the
experiment protocol caps preflight attempts at three; correctness is instead
checked through the full-corpus reconciliation and extreme-value audit.

The same audit also showed that the fixed projection's 550 unique session
identifiers are not uniformly native roots: 17 identifiers contain only
subagent sources under the native metadata. They remain in corpus and Agent
action totals but are labeled `subagent_only`, not startup-only or guided.
Accordingly the report uses “projected session identifiers” instead of
claiming that every identifier is a native root.
