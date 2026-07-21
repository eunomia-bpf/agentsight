# Outer audit — step 0063

Timestamp: 2026-07-21T02:32:00-07:00
Outer decision: EXPERIMENT node complete; return to orchestrator

## Inner completion

The experiment followed `PROPOSE → REVIEW → REAL PREFLIGHT → FULL RUN → RESULT
REVIEW`. The plan received three review rounds before execution. A first full
result review correctly rejected two adapter defects. Both were repaired
without changing the hypothesis, and the same complete workload was rerun. The
second independent review passed with no must-fix.

## Required outputs

- Detailed Markdown records exist for every node.
- The product artifact is standard pprof only.
- Two compact real-case pprof files are retained in
  `docs/visexp/out/agentreward-diff-pprof-v1/`.
- The complete raw 676-profile run remains locally reproducible from the
  official dataset through `script/agentreward_diff_pprof_eval.py`.
- No custom frontend, dashboard, or bespoke renderer was added.

## Scope audit

The repository hard rule was added to `CLAUDE.md`, which is shared through the
`AGENTS.md` symlink, and the same human instruction was recorded in
`docs/user-instruction.md`. The implementation changes only AgentPProf's CLI,
pprof writer, focused tests, and README. `frontend/`,
`docs/agentpprof-paper/`, and the skills repository were not modified.

An independent code reviewer found two P2 defects in the first backend draft:
zero difference was rejected and the ordinary writer copied all stack strings.
The final implementation emits a valid empty pprof and uses a borrowed iterator
for the ordinary path. Re-review passed `cargo test --all-targets` (68 tests),
`cargo clippy --all-targets -- -D warnings`, format/diff checks, and real Go
pprof readback for positive, negative, and zero differences.

After commit `7ad6119ce` was pushed, Grok 4.5 performed an external complete
review of the exact commit and returned PASS with no must-fix. Its remaining P2
advice matches this audit: broad coverage is not localization accuracy, and the
scalar feature scores are not a failure detector. The auditable verdict is in
`external-grok-review.md`.

## Research memory update

The durable product conclusion is that AgentPProf should remain a pprof
producer, not a visualization product. Good/bad comparison is a signed pprof
over the same explicit task-semantic stack. A task-centric path can reveal a
wrong object and different conclusion even when total steps, error rate, and
tokens fail to rank the pair correctly.

The durable experimental caution is equally important: benchmark terminal
observations are not operations, target-erasing recurrence creates false loops,
and broad scalar outcome statistics do not validate hierarchy/localization
quality without a gold path.

## Transition

The node has a valid bounded RQ1 result and no remaining implementation or
experiment must-fix. It may return to the outer orchestrator. This audit does
not authorize a paper edit, thesis change, claim narrowing, or new frontend.
