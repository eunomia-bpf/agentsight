# Task spec: freeze, annotate, and profile the research-worktree population

You are an autonomous engineering agent in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Never run git commands. Never modify or delete any existing file (session
files are strictly READ-ONLY). Never touch `docs/agentpprof-paper/` or
`docs/paper/`. All deliverables go in THIS directory. Python:
`/home/yunwei37/workspace/.venv/bin/python3`.

## Phase 1 — freeze the population

1. Recover the 42 sessions whose coarse project label is exactly
   `agentsight-research-semantic-flamegraph` from the step-0084 inventory
   (`step-0084-20260725T193000-0700/experiment-001/inventory-results.json`;
   its `inventory.py` defines the session-key hash so you can reconstruct
   key -> source file path read-only).
2. Write `frozen-population.json`: for each session, the source-relative
   path, freeze-time byte length, sha256 of exactly those bytes, agent
   kind (codex/claude), and the inventory row's coarse stats. From now on
   every read of a session file MUST stop at the frozen byte length, so
   still-active sessions are pinned.
3. Report count (expect 42), total operations, and known token mass; if
   the count differs from 42, use exactly the sessions matching the
   inventory rows and record why.

## Phase 2 — build the annotation workspace

Build the standard three-file workspace (`trace.jsonl`, empty
`annotation.json`, derived `stacks.folded`) from the frozen sessions using
the repository's own tooling: the `agentpprof` CLI / `agent-session` crate
(see `docs/design/visexp/agentpprof-annotation-workspace.md` and
`agentpprof --help`; `cargo run -p agentpprof --release` is available).
The trace must preserve session, prompt, LLM-call, and tool-call structure
with additive measures (operation count; provider tokens where recorded).
Validate: node count, per-kind counts, token mass equal to the frozen
inventory values within documented parsing differences.

## Phase 3 — automatic annotation (you are the backend)

Apply the FIXED instruction at
`docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/automatic-backend-instruction.md`
to every session, exactly as written (variable depth, 1-3 meaningful words
per tag, action-first, session-level and prompt-level operations
mandatory, backend writes only `annotation.json`). Work in deterministic
batches; after each batch run the CLI validation so coverage and nesting
errors surface immediately. One complete pass over all 42 sessions; no
aggregate-aware revision loop (step 0077 showed it does not pay).
Record wall time per batch and any usage counters the codex CLI exposes.

## Phase 4 — materialize and summarize

1. Emit BOTH standard profiles: operation-count and token widths
   (`.pb.gz`), and verify they open with `go tool pprof` and conserve
   exact mass.
2. Produce `aggregate-summary.md` (NOT paper text): top-10 semantic
   responsibilities by token mass and by count with their full paths;
   depth distribution; cross-session name reuse rate; the deepest three
   paths; per-agent (codex vs claude) mass split; and the three
   longest-horizon sessions' dominant responsibilities. Coarse labels
   only; no quoted content; no absolute paths.
3. `cost-record.md`: complete annotation wall time, batches, worker
   pattern, and any token counters, positioned next to step 0077's
   27,362-input-tokens/session reference.

## Deliverables

`frozen-population.json`, the workspace directory, `annotation.json`,
both `.pb.gz` profiles, `aggregate-summary.md`, `cost-record.md`,
`execution-log.md`, and `results.md` tying them together with validity
checks (coverage, conservation, stock-pprof load).

If the workspace tooling cannot ingest these local sessions directly,
STOP after Phase 2 and write results.md describing the exact gap — do not
improvise a parallel parser.

## Amendment (binding, from the orchestrator)

Drop every SHA-256/checksum requirement in this spec. `frozen-population.json`
needs only: source-relative path, byte length at freeze time (practical cut
point for still-growing session files), and agent kind. No hashing, no
freeze ceremony, no "no rescan" audit language — just the simple session
list. If you already computed hashes, leave them; do not compute more.

## Continuation (after the Phase 2 stop)

The stop was correct; the missing path is now authorized as PRODUCT work:

1. Implement in the `agentpprof` crate a way to write the annotation
   workspace `trace.jsonl` from local-session inputs (the existing
   `--session-file`/`--codex-root`/`--claude-root` parsing), e.g. a
   `--workspace-out <dir>` option in local-session mode. Follow the
   existing TraceNode schema exactly as used by
   `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/trace.jsonl`
   (node kinds session/prompt/llm/tool, parent links, stable IDs, data
   previews, metrics: tokens on llm nodes, operations=1 on tool nodes).
   Reuse the agent-session IR; no parallel parser. Add a cargo test;
   `cargo test -p agentpprof` must pass. Do not add any new output format
   beyond the existing workspace files and pprof.
2. Rebuild and rerun Phase 2 on the frozen copies (read-only), then
   continue Phases 3 and 4 exactly as originally specified (with the
   no-hashing amendment). The empty-annotation bootstrap issue noted in
   results.md may be fixed as part of the same product change if needed
   (workspace init writes an empty-but-valid annotation file).
3. Editing product source under `agentpprof/` (and tests) is allowed for
   this continuation; still never touch docs/paper/, the submodule, or
   session files. Update results.md in place when phases complete.
