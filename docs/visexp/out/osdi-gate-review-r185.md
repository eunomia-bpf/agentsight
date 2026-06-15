# R185 OSDI Gate Review

Date: 2026-06-15
Reviewer: Sartre subagent, read-only
Scope: current AgentFlame research state after R184, C5/C6 readiness, and next
highest-value OSDI action

## Verdict

Level 3 conference-paper mechanism evidence. Not Level 4 systems narrative and
not OSDI weak accept.

The current strong story is C1-C3 plus scoped C4: semantic folded stacks over
real local sessions, baseline-mixing evidence, R131 ablation, and R114 exact
lineage for a fixed 20-task command-mode suite. R182 remains correctly scoped
as a partial record-mode `--trace-net` smoke because target-specific network
rows are 0/0.

R184 correctly records the current human-evidence status as `not_weak_accept`;
it is a useful claim gate, not new C5/C6 outcome evidence.

## Highest-Risk Unsupported Claims

1. **C5 developer utility.** `user-task-results.json` is
   `participant_results_empty`. There are packets, answer keys, a
   preregistration, and a scorer, but no real participant responses.

2. **C6 tag adequacy.** `tag-adequacy-results-r124.json` is
   `human_labels_empty`. R180 syntax/latency/stability does not prove human
   adequacy; the TinyLlama 1.1B collapse is a negative adequacy warning.

3. **C4 broad provenance/network scope.** R114 supports a fixed command-mode
   suite. It does not prove full-history, cross-repo, arbitrary-agent, or
   target-specific network workload provenance.

4. **C7 community usefulness.** R160 is a bounded fixed-session smoke, not a
   fresh-clone/community adoption result.

## Highest-Value Next Artifact

Run a real R142 developer pilot with five human participants using the frozen
P01-P05 packets and existing response template, then score it with
`score_user_task_results.py`. The target result path should be a separate pilot
directory such as:

```text
docs/visexp/out/user-task-pilot-r142/user-task-results.json
```

This directly attacks the largest rejection risk: whether semantic effect
flamegraphs help developers answer forensic questions. R124 human labels remain
required for C6, but C5 is the highest-value next user-value artifact.

## Boundary

Subagent review, LLM labels, author-filled responses, and placeholder rows do
not count as C5/C6 evidence. They can only audit protocols and claim wording.
