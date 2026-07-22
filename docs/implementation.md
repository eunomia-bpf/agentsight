# Implementation Frontier

## Existing product path

- `agent-session` parses native Claude, Codex and Gemini sessions into prompts,
  Tool events, LLM responses, token usage, paths, command effects and status.
- `agentvis::build_repository_trace` discovers repository-related sessions,
  preserves complete Tool timelines for repository-direct sessions, resolves
  file actions against every worktree, and orders events by Agent action time.
- `agentvis` computes the Agent Nebula layout once and exports standalone HTML,
  SVG, PNG, GIF and MP4. `agentsight vis` delegates to the same library.
- Git commits are visual flashes and repository-state evidence; they do not
  control event ordering or media frames.

The current product projection is `RepositoryTrace`. It is a thin serializable
view over `agent-session`, not a second general event model.

## Research implementation

`RepositoryEvent` now retains `ToolEvent.effect` and a hashed Tool-worktree
identity. Tool-level workdir precedes session cwd, so parallel worktrees do not
collide by relative path and adapter-recognized validation remains available to
the research projection. This extends the existing `FileAction`; it does not
introduce another IR.

The RQ1 analyzer computes final path existence/tracked state,
introduced-artifact persistence, later artifact reuse,
validation-before-supersession, competing outcomes, and coverage fields. It
writes ordinary JSON/CSV/Markdown under the experiment's raw-result directory.
These are analysis outputs, not a research-control database or production API.

RQ2--RQ7 remain small, research-only Python projections over the same frozen
rows. Each `agentvis/research/plot_rqN.py` writes inspectable CSVs first and
renders its PDF/PNG only by reopening those rows. Large ledgers are committed as
gzip archives while their local uncompressed copies are ignored. The scripts
do not add a server, database, second event IR, generated semantic labels, or a
production frontend.

## Source selection behavior

Repository-direct candidate selection already supports:

- Claude project directories matched to repository/worktree roots;
- Codex native cwd or Git remote metadata; and
- Gemini project hashes.

Complete admitted sessions preserve no-file actions. `--global` uses ripgrep to
find external Tool lines mentioning repository paths and therefore retains only
matching file-effect rows. The empirical CLI must label those rows as global
sensitivity data and never combine them with direct-session validation or
session-boundary denominators.

## Minimal research entrypoint

The research-only `research-rq1` entrypoint accepts the six repository roots and an output
directory, reuse `build_repository_trace`, and produce:

```text
raw/
  projects.json              # project and source-coverage summary
  events/<project>.json      # source-linked projected rows
  rq1-artifacts.csv          # one row per observed artifact
  rq1-mutations.csv          # one row per mutation
  rq1-summary.csv            # project-level metrics
result.md                    # recomputable RQ1 tables and interpretation
```

The same extraction may retain neutral fields needed by later RQs, but the
first command computes and interprets only RQ1. No frontend, server, SQLite,
canonical evidence bundle, semantic labeler or additional runtime dependency is
needed.

## RQ1 computation

For each project:

1. build the complete repository-direct trace;
2. reconcile candidate, parsed, included and excluded sessions, then retain
   coverage by vendor, worktree, session, effect, status and path presence;
3. group source-linked file actions by `(worktree_id, path)` and explicit
   same-worktree rename lineage; delete--recreate begins a new identity;
4. mark only identities born from confirmed-success create as
   observation-born; rename inherits source birth state and existing-file
   writes retain `content_durability=unknown`;
5. for every confirmed non-delete mutation, find later reuse and the next
   recognized successful validation before same-artifact mutation/delete;
6. encode delete/supersede as competing outcomes and only observation end as
   right censoring;
7. query final workspace existence and Git tracked state in the corresponding
   worktree, retaining unknown when the worktree cannot be queried; and
8. aggregate only at project level before any cross-case summary.

Failed calls never create successful mutations. Directory-scope actions remain
scope evidence and do not count as file reuse. Unknown access/effect/status is
retained in coverage and excluded from the corresponding numerator and
denominator rather than imputed.

## Build and verification entrypoints

```bash
cd agent-session && cargo test
cd ../agentvis && cargo test
cd ../collector && cargo test
```

The authoritative command, fresh cutoff, input/output hashes, resource use and
reconciliation are recorded in the RQ1 `commands.log`. The AgentSight preflight
and full six-project run both used real native sessions; unit tests alone were
not counted as research evidence.

## Superseded research-only code

`agentvis research-store`, `agentvis research-supervisor`, and retained Harness
Bench helpers were built for the withdrawn H6 intervention program. They remain
in this research branch only as historical/source-mechanics code and are not
part of the current empirical method or normal user path. The prior reviewed
plans, raw runs and limitations remain in the active BOOTSTRAP step reports.
They produced no intervention-treatment claim and close no current RQ.

## Current evidence status

The reviewed RQ1 run covers 2,049 admitted native sessions, 206,249 Tool
actions, 7,154 observed artifact identities and 13,152 confirmed mutation rows.
All source-ID, hash, cutoff, worktree, lifecycle, final-state and competing-risk
checks passed independent reproduction. F3/F4 are generated from frozen CSVs
and embedded in the paper. Reuse is measurable in 6/6 projects; persistence and
recognized-validation panels remain coverage-only at 3/6.

Separate reviewed projections now produce:

- F5: recognized-validation cadence, with 3/6 coverage and a cross-case stop;
- F6: repeated-mutation structure across all six cases;
- F7: source-session component continuity, with every cross-case estimator gate
  stopped;
- F8a/F8b: path-resolved workspace activity allocation, transitions and return
  gaps, with one low-support N/A;
- F9: Skill/instruction source coverage and an explicit association stop; and
- F10: a dependency-only benchmark-readiness audit. It finds the normalized
  spine present but native-prefix and cutoff-worktree contracts absent, so no
  baseline, question, accuracy, advantage or cost result is produced.

F10 closes the paper's readiness RQ, not the separate capability claim. A
matched comparison still requires immutable native admitted prefixes,
per-worktree cutoff revisions/untracked-state disposition, pinned baseline
interfaces, and a separately reviewed source-explicit oracle.
