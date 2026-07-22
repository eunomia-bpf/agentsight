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

## Gaps blocking the empirical study

`RepositoryEvent` currently retains tool/category/command name/status and file
actions, but drops `ToolEvent.effect`. RQ1 therefore cannot distinguish a
successful validation command from a generic Bash action. The minimum repair is
to retain the source-native command effect in `RepositoryEvent`; no command
text classifier or new IR is required.

The RQ1 analyzer must additionally compute final path existence/tracked state,
later artifact reuse, next successful validation, and coverage fields. It should
write ordinary JSON/CSV/Markdown under the experiment's raw-result directory.
These are analysis outputs, not a research-control database or production API.

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

## Planned minimal research entrypoint

One research-only entrypoint will accept the six repository roots and an output
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
2. retain source coverage by vendor, session, effect, status and path presence;
3. group source-linked file actions by explicit rename lineage or normalized
   path when no rename exists;
4. for every create/mutation, find the next later access to the same artifact;
5. find the next successful validation event globally and within the same
   session, reporting event and wall-clock distance separately;
6. query final workspace existence and Git tracked state; and
7. aggregate only at project level before any cross-case summary.

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

The empirical run will add one authoritative command after independent plan
review. A real preflight must use one of the six repositories and write the
actual raw output path; unit tests alone do not count as research evidence.

## Superseded research-only code

`agentvis research-store`, `agentvis research-supervisor`, and retained Harness
Bench helpers were built for the withdrawn H6 intervention program. They remain
in this research branch only as historical/source-mechanics code and are not
part of the current empirical method or normal user path. The prior reviewed
plans, raw runs and limitations remain in the active BOOTSTRAP step reports.
They produced no intervention-treatment claim and close no current RQ.

## Current evidence status

The visualization and repository projection run on real local sessions, but no
RQ1 six-project analysis has completed. Exact session counts, effect coverage,
durability, reuse, validation-association results and plots remain unknown until
the reviewed full run finishes. Prototype visuals and passing unit tests do not
close a paper RQ.
