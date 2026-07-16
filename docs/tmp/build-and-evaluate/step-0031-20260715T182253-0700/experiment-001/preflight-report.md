# Real Preflight Report

**Executed:** 2026-07-15T18:50:42-07:00
**State:** complete; connectivity evidence only
**Scored evidence:** none

## Inputs

- Official AgentBoard release root: `/tmp/agentboard-data/data`
- Preflight population: the first source-ordered row of each of the nine
  official task families
- Local model:
  `qwen2.5-3b-instruct-q4_k_m.gguf`
- llama.cpp server: `127.0.0.1:18081`, one 4,096-token slot, GPU offload
- AgentProf path: release Rust binary built from the current worktree
- Cache: disabled for reads, in-run hits, and writes
- Output:
  `.agentsight/experiments/step-0031-agentboard-task-identity/preflight-profile.json`

The `/v1/models` endpoint reported the expected 3,397,103,616-parameter GGUF.
The adapter independently revalidated the complete release before selecting
the preflight rows: 1,012 rows, no empty goal, exactly the nine expected
official identities, and the predeclared per-family counts.

## Path Checks

The real AgentProf command completed successfully and reported:

- 9 imported portable sessions;
- 9 operation samples and 9 unique stacks;
- a nonempty raw `session_tag` for every row;
- a separate nonempty declared `task_tag` for every row;
- a nonempty raw prompt tag for every row; and
- 9/9 declared outputs inside the enumerated grammar.

The profile stack contains `session`, `task`, and `prompt` simultaneously, so
the new declared taxonomy does not overwrite the established open-vocabulary
field. Unit and integration verification before preflight comprised 48 Rust
unit tests and 13 Rust CLI integration tests, all passing.

## Observed Outputs

For auditability, the declared outputs in canonical source order were:

`alfworld`, `toolop`, `webshop`, `alfworld`, `toolop`, `webbrowse`,
`webbrowse`, `toolquery`, and `webshop`.

These nine rows are not scored, summarized as accuracy, or used to select a
prompt, description, model, label, or threshold. Their only role is to prove
that real data traverse the approved shared Rust request, retry, sanitation,
cache-disable, profile-field, and JSON-output path. The fixed full run proceeds
without changing the approved mechanism.

## Preflight Decision

**PASS for full execution.** No server, schema, population, grammar, missing-
field, or shared-path failure remains. The full 1,012-row population and all
three independent no-cache repetitions must now complete before scientific
interpretation.
