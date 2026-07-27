# Shell-boundary projection repair

Date: 2026-07-26

Trigger: `shell-boundary-audit-20260726/report.md` found a material
source/projection boundary defect in the frozen RQ7 v2 run. This repair reads
the native command as the semantic source of truth; it does not tune the
projection to the prior oracle.

## Repaired paths

| Native shape | Production projection | Source-direct oracle |
|---|---|---|
| Multi-source `cp ... DIR 2>&1` | Preserve every source read and create `DIR/basename(source)` for every source; strip the fd redirection instead of dropping the command. | Remove the fabricated redirection operand and use the same real `cp` semantics. |
| `git rm` | Preserve non-recursive exact deletes. Mark recursive deletes as directory scope even when `rm` is inside a compound command. Directory-scope deletes do not enter the strict artifact ledger. | Admit non-recursive `git rm`; omit recursive operands from the exact-artifact oracle. |
| Process substitution | Preserve the inner `sed` file reads under the audited command's single literal leading `cd`. | Parse the balanced `<(...)`/`>(...)` bodies and resolve them under that leading cwd. |
| Cross-line quote | Parse the command as one logical shell input, so commands before a multiline commit message are retained. | Stop applying `shlex` independently to unmatched physical lines. |
| Leading bare backslash-newline | Emit no attempted file effect for the native Claude `Bash` shape rejected by the wrapper before shell launch. Generic shell transports still treat backslash-newline as POSIX continuation. | Preserve the prior source-direct rejection for Claude `Bash`, without generalizing it to other transports. |
| Nested static `exec` | Decode the path effects of every supported JSON-like static `tools.exec_command({...})` object and apply each nested workdir. | Replace the previous first-object-only path scan with an ordered all-object scan. |

The v2 primary grammar had runner-local support for static
`tools.apply_patch` wrappers and literal inline `cd`, while the active research
module did not. Those already-established v4 controls were retained in the
active oracle before the rerun so this repair did not regress unrelated
source-direct behavior.

## Oracle corrections

The prior oracle was semantically wrong where it:

- fabricated a `docs/1` destination from `2>&1`;
- ignored three copies preceding a multiline quoted commit message;
- ignored process-substitution reads;
- ignored the eleven exact paths in a non-recursive `git rm -f`;
- retained only the first of two nested static exec calls.

The leading-backslash case was instead a production-only defect: the prior
oracle correctly emitted no action, while production fabricated an attempted
read. That rejection is deliberately scoped to the native Claude `Bash`
wrapper that reported the pre-launch error.

Recursive `git rm -r` is a real directory-scope effect but is intentionally
absent from the strict exact-artifact ledger. The production trace retains the
scope annotation for non-ledger consumers.

## Regression fixtures

`agent-session/tests/fixtures/strict-action-grammar.json` contains the seven
native command shapes from the v2 audit: multi-source copy plus fd
redirection, recursive `git rm`, process substitution, cross-line quoting,
leading wrapper rejection, two nested exec calls, and the eleven-path
non-recursive `git rm`.

The shared fixture gate checks the production Rust parser, the primary
source-direct grammar, and the independent checker. The recursive delete
scope, compound-command scope isolation, and delete-only recursive scope also
have repository projection unit tests. One additional negative fixture proves
that a generic `exec_command` still accepts POSIX backslash-newline
continuation. Another redirection fixture proves that a named `&>` target is
removed rather than fabricated as a `cp` operand. A final boundary fixture
proves that a nested exec without its own workdir falls back to the outer
native cwd rather than inheriting the preceding nested exec's workdir.

The Rust parser fixture records parser-layer relative paths. Where the
source-direct oracle applies the fixture cwd, `oracle_actions` records the
corresponding absolute path. This is an intentional layer boundary, not an
oracle exception.

## Scope and residual boundaries

Directory-scope knowledge is now applied after the global event sort, so it is
action-time state rather than candidate-file scan state. A compound shell
whose first segment happens to be `ls` or `mkdir` no longer scopes later exact
`cp`, `sed`, or `mv` actions. Recursive scope is applied only to delete
actions. The two source-direct oracles update directory rename/delete state per
action, so a directory rename in a compound call does not suppress a separate
file rename.

The repaired nested-exec path projection visits every supported JSON-like
static object. Single-quoted, template-literal, or dynamically constructed
objects remain outside this grammar. The outer native call still contributes
one action atom, using the first decoded nested command; this stage does not
redefine the family-A atom contract.
Mixed recursive `rm` clauses containing both directory and exact file operands
remain outside the audited fixture. They are recorded as a future third-corpus
stress case rather than generalized from the inspected corpus. Multiple shell
cwd transitions inside one Tool call likewise remain outside this repaired
grammar; an attempted generalization caused an original-corpus regression and
was rejected by the 60/60 stop gate.

## Reproduction

The two append-only runners are:

- `scripts/run_repair_corpus.py`
- `scripts/run_heldout.py`

Both record the release binary SHA-256. Large projection traces, copied frozen
sources, raw deterministic output, build products, and retained debugging
attempts are ignored; the compact CSV and JSON gate records are committed.

The two source-direct implementations share only the written specification
and fixture contract. The primary uses line-accumulating shell tokenization,
dict actions, and `ArtifactTracker`; the checker independently normalizes the
whole command, emits tuple effects, and uses `Identities`. Their balanced
substitution scanners, cwd reducers, and directory-state transitions are
separate functions. This intentional duplication is the cross-check, not
production code reuse.
