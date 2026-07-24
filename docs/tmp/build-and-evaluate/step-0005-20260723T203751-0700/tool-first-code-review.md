# Tool-first diagnose code review

Date: 2026-07-24
Scope: latest uncommitted `agentvis/src/diagnose.rs`,
`agentvis/src/repository.rs`, `agent-session/src/parser.rs`, and the
`agentvis`/`agentsight` CLI wiring.

## Verdict

**BLOCK before treating the generated brief as a correctness-sensitive
automated diagnostic input.**

The architecture is lean and directionally correct:

- `agent-session` remains the native-record abstraction;
- `RepositoryTrace` is the repository projection rather than a second event
  IR;
- `diagnose` derives report-only relations from that projection;
- workspace evolution and root-external exact-path references are now
  presented separately;
- validation is explicitly described as temporal association rather than
  file-level coverage.

Several issues found in the first pass were fixed while this review was in
progress. The remaining blockers are narrower but still affect which
workspace, path, or validation episode the report attributes an action to.

## Open findings

### P1. A remote-only Codex candidate is labelled as a workspace session

Direct discovery admits a Codex session when either its cwd is under a
selected worktree **or** its recorded Git remote matches the repository.
Every admitted direct stream is then passed to `append_session(..., true)`.

Consequently, a session working in another clone of the same remote is marked
`workspace_session=true`. Its relative file actions are rejected because its
cwd is outside the selected roots, but all pathless Tool calls are retained.
Those calls can still change:

- workspace/direct session counts;
- recognized validation counts and action-strategy summaries;
- session start/end boundaries;
- evolution eligibility and transition order.

This violates the field's stated meaning (“the native session itself belongs
to this repository/worktree”). It also creates an asymmetry: a root-external
session found by `--global` retains only exact-path actions, while a
remote-only direct candidate retains all pathless actions.

**Required fix:** use remote equality only as a discovery hint. Classify a
session as workspace/direct only from an exact selected-worktree cwd (or
equivalent native project-root identity). If remote-only candidates are still
useful, admit only their exact-path actions with the same semantics as
`--global`.

Relevant code:

- `agentvis/src/repository.rs:221-239`
- `agentvis/src/repository.rs:359-467`
- `agentvis/src/repository.rs:774-807`
- `agentvis/src/diagnose.rs:331-356`

### P1. Dynamic-`cd` protection can be bypassed by upstream workdir absolutization

`inline_shell_cwd()` now correctly uses `Absent/Known/Unknown`, and it
conservatively rejects multiple cwd regions. However, `agent-session` first
normalizes every shell operand against the Tool input's `workdir`/`cwd`,
without applying shell `cd` clauses.

For example, given:

```text
workdir=/repo
command=cd nested && cat src/lib.rs
```

`agent-session` emits `/repo/src/lib.rs`. The repository layer computes the
inline cwd `/repo/nested`, but an already-absolute operand is not rebased, so
the report attributes the read to `src/lib.rs` rather than
`nested/src/lib.rs`.

The unsafe case is worse:

```text
workdir=/repo
command=cd "$tmpdir" && touch result.json
```

The parser can turn the relative operand into `/repo/result.json` before the
repository layer returns `Unknown`; because absolute operands are still
admitted, an outside-workspace action can be fabricated as a repository
mutation. The current repository test constructs relative `ToolPath` values
manually and therefore does not exercise this cross-layer counterexample.

**Required fix:** shell path extraction must preserve whether an operand was
relative, or perform cwd-segment resolution exactly once. At minimum, add an
end-to-end parser-to-repository regression with explicit `workdir`, one
literal `cd`, and one dynamic `cd`.

Relevant code:

- `agent-session/src/parser.rs:1203-1316`
- `agent-session/src/parser.rs:1453-1495`
- `agentvis/src/repository.rs:402-439`
- `agentvis/src/repository.rs:543-597`
- `agentvis/src/repository.rs:1264-1365`

### P1. Directory scope is inferred globally across the whole history

`annotate_directory_scopes()` builds one directory set from current
`git ls-files`, the current filesystem, and every action path in the entire
trace. It then applies that timeless set to every historical action.

If a path changes kind over time, for example:

```text
delete file `docs`
later create `docs/index.md`
```

the later descendant makes `docs` a directory prefix globally, so the earlier
real file deletion is marked `scope=true` and removed from artifact/mutation
analysis. Conversely, `rm -rf untracked-dir` is not known to be a directory
when no descendant is tracked/observed and the directory no longer exists at
analysis time, so it can be counted as deleting a file artifact.

This is the remaining recursive-`rm` correctness problem. It is no longer the
old “one recursive bit for the entire Tool call” bug, but scope still lacks
event-time evidence.

**Required fix:** classify scope per action at its event time from operand
syntax plus lifecycle evidence. Do not let a future descendant retroactively
change an earlier path's kind. Add a file-to-directory transition and a
deleted untracked directory fixture.

Relevant code:

- `agent-session/src/parser.rs:1497-1547`
- `agentvis/src/repository.rs:735-771`

### P2. Unknown-worktree validation calls share one synthetic repetition run

Worktree-level successful association is conservative: an event with no
worktree ID does not close pending mutations in a known worktree. But
repeated-validation tracking maps every missing ID to `""`:

```rust
event.worktree_id.clone().unwrap_or_default()
```

Thus unrelated unattributed tests from multiple native sessions or external
workspaces can become one “validation repetition” run. A mutation with a known
action worktree does not clear that empty bucket.

**Required fix:** exclude unattributed validation calls from worktree-local
repetition, or key a separately named unassociated sequence by at least native
session.

Relevant code:

- `agentvis/src/diagnose.rs:729-840`

### P2. `workspace_session` is still stored as source admission, then exposed as a session fact

`workspace_session` is assigned independently to each appended source stream.
`SessionAgg`, keyed by normalized native session ordinal, copies the value
from the first chronological event and never normalizes later events.

Direct source paths are excluded from the global scan, so ordinary sessions
will usually be uniform. However, a native root represented by multiple
source files can still have one directly discovered stream and one
root-external matched stream. The aggregate result then depends on event
order.

**Recommended fix:** retain a source-origin enum on events, then derive
session origin after all streams with an explicit rule (`workspace`,
`root_external_exact_path`, or `mixed`). Do not expose first-event admission
as a normalized native-session property.

Relevant code:

- `agentvis/src/repository.rs:221-239`
- `agentvis/src/repository.rs:455-467`
- `agentvis/src/diagnose.rs:331-356`

### P2. Global exact-path mode intentionally loses native results and prompts

For Claude and Codex, `behavior_sessions()` parses only `rg`-matched Tool-call
lines. It does not retain the matching Tool result, user prompt, or Codex
session metadata.

The current wording is now appropriately conservative:

- it says `root-external exact-path`;
- mutations remain observed/attempted rather than confirmed;
- the boundary explicitly states that matched-line scanning may lack results;
- it no longer equates every external reference with an independent consumer.

Therefore this is no longer a correctness blocker for the current report
contract. It is still an important capability boundary: external prompt
previews are unavailable, successful external mutation cannot be confirmed,
and a Codex native root can fall back to source-file identity.

If future claims require external producer/consumer classification, the
scanner must reopen the selected file and retain the minimal native envelope:
root metadata, associated prompt, Tool call, and result.

Relevant code:

- `agentvis/src/repository.rs:884-972`
- `agentvis/src/diagnose.rs:1670-1782`

### P2. Read-span labels and endpoints remain slightly stronger than the data

Closed and open-at-cutoff spans are now reported separately, fixing the
earlier ranking error. Two smaller problems remain:

1. the title says “read/search”, but the metric counts normalized file-read
   effects; repository searches such as `Grep` intentionally have no exact
   file action and are not counted;
2. the mutation-closing Tool event is included in `tool_events` and used as the
   displayed end endpoint, so “before a mutation” includes the boundary event.
   An atomic Tool with read and mutation effects also contributes those reads,
   even though their internal order is unknown.

Equal-rank spans can also be nondeterministic because open spans are drained
from a `HashMap` and ranking has no final start/session tie-break.

**Recommended fix:** call these “file-read spans”; document or exclude the
closing Tool from the pre-mutation length; add `(start, session_id)` as a
deterministic tie-break.

Relevant code:

- `agentvis/src/diagnose.rs:897-976`
- `agentvis/src/diagnose.rs:1785-1866`

### P3. Self-diagnose exclusion is correct for plain commands but incomplete for wrappers

The implementation now drops an event only when **all** meaningful clauses
are diagnose invocations. Therefore:

```sh
cargo test && agentsight diagnose .
```

correctly remains visible; the earlier whole-event-loss bug is fixed.

Wrappers such as `sudo -n agentsight diagnose`, `env FOO=bar agentsight
diagnose`, and shell functions are not recognized, so a diagnostic run can
remain as a pathless process event. This should not fabricate file effects,
but it can add one Tool call to session/process counts.

Relevant code:

- `agentvis/src/repository.rs:397-400`
- `agentvis/src/repository.rs:498-520`

## Fixed during review

The following first-pass findings are closed in the latest snapshot:

- Diagnostic artifact keys now combine `worktree_id` and `artifact_id`, with a
  cross-worktree regression.
- Multiple literal `cd` regions and `pushd`/`popd` are conservatively
  classified `Unknown`.
- A compound Tool call containing both validation and diagnose is no longer
  dropped as self-observation.
- Validator script matching uses token-bounded filename parts; the
  `latest_results.py` false positive is covered.
- Open and mutation-closed read spans are reported as separate signals.
- The root-external signal and its boundary no longer claim that every global
  match is a read-only consumer.
- Standalone `agentvis diagnose --help`, version, and unknown-option handling
  work.
- Direct prompt preview mapping correctly converts the Tool's one-based
  prompt ordinal to the zero-based prompt vector.

## Complexity and naming

No additional event IR is needed. The main avoidable complexity is duplicated
shell interpretation:

1. `agent-session` extracts shell paths and applies Tool-level workdir;
2. `repository` separately parses inline cwd;
3. `repository` separately identifies self-diagnose and infers directory
   scope.

These layers currently disagree about the granularity of a shell segment,
which directly causes the dynamic-cwd and scope findings above. A small shared
shell-segment result inside `agent-session`—executable, cwd certainty,
operands, access, and segment identity—would remove logic rather than add a
new architecture layer.

`diagnose.rs` is over 2,600 lines and combines aggregation, relation
algorithms, signal selection, evidence formatting, Markdown rendering, manual
CLI parsing, and tests. Keeping `RepositoryTrace` as the sole input model is
good, but pure analysis and rendering should become private modules before
more signals are added. The six-element tuple used as read-span state is an
immediate readability risk.

## Validation performed on the final reviewed snapshot

- `cargo test --manifest-path agent-session/Cargo.toml`: **21 passed**
- `cargo test --manifest-path agentvis/Cargo.toml`: **50 passed**
- `cargo test --manifest-path collector/Cargo.toml`:
  **197 unit passed, 1 ignored; 5 CLI integration passed; 3 system tests
  passed; 4 privileged/live tests ignored**
- `cargo fmt --check` for all three manifests: **PASS**
- `git diff --check`: **PASS**
- `agentvis diagnose --help`: **PASS**
- `agentsight diagnose --help`: **PASS**

No implementation file was modified during this review.

## Follow-up addendum: latest fixes

Follow-up date: 2026-07-24
Status below supersedes the corresponding open findings above.

| Previous blocker | Latest status | Evidence |
|---|---|---|
| Same remote, different clone classified as workspace | **Resolved** | Codex direct discovery now requires a recorded cwd under one of the selected worktree roots. Git-remote equality was removed from admission (`repository.rs:821-844`). |
| Dynamic `cd` bypass | **Partially resolved; one blocker remains** | The `Unknown` branch now admits only an absolute path literally present in the command, so a path pre-absolutized only by parser `workdir` no longer leaks through. However, a *known literal* `cd` still composes incorrectly with parser-side workdir absolutization: `workdir=/repo; cd nested && cat src/lib.rs` is parsed as `/repo/src/lib.rs`, and repository projection cannot rebase that absolute path to `/repo/nested/src/lib.rs` (`parser.rs:1453-1495`, `repository.rs:399-423`). The new regression covers a manually relative `ToolPath`, not the parser-to-repository path. |
| Directory scope is globally retroactive | **Resolved for temporal locality; residual unknown-directory limitation** | Scope state is now maintained forward in event order and partitioned by worktree; an exact file Tool can turn a path back into a file, and directory deletion removes descendant state. The file→directory→file regression passes (`repository.rs:739-782`, `1390-1434`). A recursive deletion of a never-observed, now-absent untracked directory still looks like a file deletion because `rm -r/-R/--recursive` is not used as per-operand directory evidence. |
| Unknown-worktree validations merge across sessions | **Resolved** | Successful association requires `Some(worktree)`, and repetition tracking keys unknown worktrees by native session. The new cross-session regression passes (`diagnose.rs:786-821`, `2650-2662`). |

### Full native-envelope global scan

`behavior_sessions()` now uses `rg` only to select candidate source files, then
passes each selected file through the same full `repository_session()` /
`agent-session` parser used by direct candidates. This restores:

- native session/root metadata;
- preceding prompt boundaries and `prompt_preview`;
- Tool-call/result pairing and `ok`/`fail` status;
- model/skill/agent attribution retained by the normal parser.

`append_session(..., false)` still removes every Tool event with no resolved
action under the selected roots, so parsing the rest of the file does not by
itself admit unrelated pathless calls or other-workspace file actions. I found
no new positive misattribution introduced by this change. It does increase
I/O to one filtered full-file parse per `rg`-selected source, which is a
performance tradeoff rather than a correctness problem.

There is not yet a dedicated end-to-end fixture proving that
`behavior_sessions()` preserves an external prompt plus successful/failed
Tool result while excluding unrelated actions. The behavior follows from the
shared parser path, but this boundary deserves one regression.

### Updated verdict

Three of the four prior blockers are resolved, and the global native-envelope
change is correct. The report should still be **BLOCKED for
correctness-sensitive automated use** until literal `cd` plus explicit Tool
`workdir` is resolved exactly once across `agent-session` and repository
projection. Recursive deletion of a never-observed directory should either
be fixed or explicitly reported as an unknown scope rather than a file
artifact.

Latest follow-up validation:

- `cargo test --manifest-path agent-session/Cargo.toml`: **21 passed**
- `cargo test --manifest-path agentvis/Cargo.toml`: **52 passed**
- formatting checks for both manifests: **PASS**
- `git diff --check`: **PASS**

Final literal-`cd` recheck: the new rebase closes the absolute-`workdir` case, but the blocker is not fully resolved for a supported relative Tool workdir—minimal reproduction: session cwd `/repo`, Tool `workdir="nested"`, command `cd sub && cat src/lib.rs`; `agent-session` emits `nested/src/lib.rs`, then repository projection joins it under `/repo/nested/sub` and produces the incorrect `nested/sub/nested/src/lib.rs` instead of `nested/sub/src/lib.rs`.
