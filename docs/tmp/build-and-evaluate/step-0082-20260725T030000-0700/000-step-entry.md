# Step 0082 entry: profile-guided reader protocol v2 (lean + width-annotated)

Timestamp: 2026-07-25T03:00:00-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `grok` CLI agent, orchestrated by the root session

## Why this step exists

Step 0080 established that the semantic profile skeleton concentrates a
strong reader's attention (MAP 0.455 at 53% content opened, stage-1 zero
fallbacks), but its two-stage implementation re-transmitted the skeleton in
stage 2, making total logical input 15,991 tokens/query versus the
full-trace reader's 12,615 (1.27x). The step-0080 loss decomposition
(analysis-001) further showed all 66 index misses were total absences from
the reader's ordered consideration at a saturated budget: the lever is
stage-1 discrimination, not budget size, and hit-conditional MAP (0.618)
already exceeds the full reader (0.587).

Protocol v2 applies both findings without changing the scientific question:

- **Lean stage 2**: only the selected groups' evidence with operation-ID
  anchors; no skeleton re-send. Unopened operations are appended by the
  deterministic completion exactly as before.
- **Width-annotated stage 1**: each group line carries its member count and
  additive measure mass (pprof widths) alongside the semantic path — the
  same signals a human reads in a flame graph, with zero source content.

## Registered targets

- MAP at least 0.48 on the complete 220-query TraceElephant population.
- Total logical input tokens (tiktoken o200k_base over both stages'
  packets) below the full-trace reader's 12,615 mean tokens/query.
- Content-opened fraction at or below step 0080's 53%.

If targets are missed, this remains an iteration step: findings feed
protocol v3 rather than any paper claim (no-negative-results policy).

## Fixed constraints

Identical population, frozen group mapping, reader CLI/flags, retry and
fallback rules, scoring, and paired-bootstrap machinery as steps 0079-0081.
No modification of existing files, no git commands, no
`docs/agentpprof-paper/` or `docs/paper/` access. Complete run only.

Full task specification: `experiment-001/task-spec.md`.
