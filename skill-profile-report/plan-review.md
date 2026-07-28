# Experiment Plan Review

## Round 1

Verdict: **REVISE**.

The reviewer accepted the experiment's RQ1 role, use of exact source-native Skill fields, noncrossing latest-wins attribution, and aggregate-versus-session comparison. Four blockers were identified before a valid real run:

1. Internal Claude `user` metadata and `last-prompt` snapshots would immediately erase most scopes unless a genuine prompt boundary were defined operationally.
2. Claude can split one completion across several assistant rows with identical `message.id`/`requestId` and repeated usage, so text-hash deduplication could double-count tokens.
3. Default discovery filters by the current project, so the full-history command had to pass every JSONL explicitly and report discovered/parseable/excluded/emitted counts.
4. The plan had to fix the complete frame order and commit to a `skill` pprof label.

Disposition: all four are accepted. The plan now defines prompt boundaries by `promptId` plus explicit metadata exclusions; requires source-completion identity deduplication; gives the explicit all-file input strategy; and fixes the frame and label contract. It also records named-scope coverage, the invocation-completion boundary, and all requested over-/under-count limitations.

## Round 2

Initial verdict: **REVISE**.

The fresh reviewer found that merging a later fragment with the same source completion ID could promote an intentionally unscoped earliest fragment into the newly invoked skill. That would retroactively charge the completion that chose the skill to the skill itself.

Disposition: accepted. Completion merging now preserves the earliest fragment's scope and never promotes it from later fragments. The regression fixture is a text fragment followed by a Skill tool call and then another fragment with the same `message.id`; the merged completion remains unscoped and repeated usage is counted once.

Final verdict: **APPROVE — real preflight and full run admitted.**
