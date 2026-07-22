# RQ1 Real Preflight Result

Started: 2026-07-20T01:28:32-07:00
Status: failed the frozen context-fit veto before supervisor inference

## Admitted scope

The approved preflight allowed one real coding perturbation/repair pair and one
real auto-research perturbation/repair pair, followed by one Full Raw and one
Full Trajectory supervisor call. The plan requires every rendered prompt to
satisfy `prompt_tokens + 2,048 <= 65,536`; no truncation, context shifting, or
post-result condition deletion is allowed.

## Attempt 1: retained infrastructure failure

The first coding/perturbed run is retained under
`raw/preflight/attempt-1/coding-p2-perturbed/`. The isolated DynamicUser could
not traverse the source workload directory because its repository-owned parent
is mode `0700`. The fixture failed before workspace initialization and before
either Agent session. This is an infrastructure failure, not a scientific run.

The controller was repaired to copy the already frozen workload bytes into the
run's private runtime directory as a controller-owned read-only tree before
signaling initialization. The worker no longer receives a bind mount or a
dependency on host-directory traversal permissions.

## Attempt 2: valid exact-state capture, invalid source projection

The retained output is
`raw/preflight/attempt-2/coding-p2-perturbed/`. It contains two genuine
top-level Codex sessions over the official SWE-bench Verified
`pytest-dev__pytest-10051` base commit. The first goal reproduced the
`caplog.clear()` inconsistency and added a regression assertion. The target
session received the new target prompt while `active_goal.md` remained bound to
the prior goal, then continued working on reproduction and environment-driven
test bootstrap attempts rather than implementing the production fix.

The capture controller reports PASS for two distinct completed sessions,
Agent-event presence, workspace changes in both goals, private ext4 scope,
triple live/archive manifest equality, durable-before-thaw seals, and cleanup.
The native event counts are:

| session | JSONL bytes | item.started | item.completed | turn.completed |
|---|---:|---:|---:|---:|
| prior | 35,495 | 14 | 20 | 1 |
| target | 35,430 | 16 | 22 | 1 |

The condition builder's implemented path-union check found at least one owned
successful effect for each of the 78 manifest-changed paths and produced 43
actions plus 3,514 selected source records. Independent result review showed
that this check is materially weaker than the approved source/action-closure
contract and that the resulting projection is invalid. In particular, the
parser treated numeric decoded `dirfd` paths such as `3</proc>` as if they were
relative to the workspace CWD. Of 3,434 selected strace records, 2,216 use a
non-`AT_FDCWD` dirfd; 1,386 were consequently attached as false workspace reads
and 830 were left unbound. Another 1,328 selected system records were unbound,
including genuine target-workspace reads.

Action ownership is also not exact. The builder used the controller-side
arrival time of `codex exec --json` events as the beginning of a tool interval,
but short syscalls may finish before the corresponding `item.started` line
arrives. The retained native session log, rather than stdout arrival, must
provide stable call IDs and start/end timestamps. Therefore the exact-state
boundary capture is valid, but neither the 78-path check nor the current
Raw/Trajectory projection establishes source closure.

## Frozen veto result

Both complete condition prompts exceed the frozen 63,488-token input ceiling:

| condition | prompt bytes | pinned-tokenizer tokens | ceiling | result |
|---|---:|---:|---:|---|
| Full Raw | 2,125,926 | 956,130 | 63,488 | FAIL |
| Full Trajectory | 2,885,469 | 1,215,415 | 63,488 | FAIL |

Token counts were produced by the pinned
`llama-tokenize`/Qwen-3.6-27B-GGUF path declared in the plan. Full Trajectory is
larger because the current static serialization includes the complete source
record table plus deterministic action, order, and artifact-lifecycle
relations. Full Raw contains the same source facts without those relations.
As a formatting-only check, compacting the evidence JSON and omitting the shared
instruction prefix still leaves 784,820 Raw tokens and 936,969 Trajectory
tokens. Whitespace removal therefore cannot repair the frozen context veto.

No supervisor model was invoked. No diagnosis, gold-label, score, latency, or
effect result exists. The remaining repaired coding episode and both
auto-research episodes were not launched because the first valid real episode
already triggered a mandatory preflight veto. Running them could not make this
frozen static-full-context protocol valid.

## Additional protocol defects found before any inference

Two implementation requirements were also incomplete. First, the planned
`score_rq1.py` command did not yet exist, although the plan required all three
commands to print usage before the real preflight. Second, the prompt template
derived `episode_id` from the workload directory and therefore exposed the word
`perturbed`; this violates the plan's prohibition on revealing perturbation
identity. The template also prints `FullRaw` or `FullTrajectory`, creating an
avoidable representation-format cue. These defects cannot bias a model result
because no model was invoked, but they independently prevent treating this run
as a valid end-to-end preflight.

## Scientific interpretation

This preflight rejects the **implemented single static full-context
serialization** as the RQ1 experimental interface. It does not prove that every
possible exact static encoding must exceed the budget, and it does not reject
workspace-centered trajectory diagnosis. The current constructor repeats large
manifests and includes falsely selected records, so its 15--19-times overflow is
an implementation-level counterexample, not a lower bound on all encodings.
Even so, a full-fidelity on-demand interface is the scientifically stronger and
more scalable next design.

The next experiment must therefore return to the paper's actual scalable
setting: a matched query interface over one source store. Raw Retrieval and
Workspace Trajectory Retrieval must receive the same model, prompt, total
rendered-token budget, query/response budget, source facts, and action-ID
namespace. They may differ only in whether the query surface exposes raw
chronology or deterministic workspace/action relations. State Diff and Counts
remain controls. Any selector, summary, or compression policy learned or tuned
from pathology labels would be ad hoc and is not admitted by this result.

## Decision

**Preflight FAIL.** Stop the approved plan before supervisor inference and
before the full matrix. The result establishes valid quiescent boundary capture
and shows that the current static serializer cannot satisfy the frozen budget.
It does not establish source closure, a diagnosis comparison, or a universal
context lower bound. A scientifically distinct queryable-Retrieval experiment
requires a corrected native-action/system-effect source contract, neutral
condition identifiers, a frozen scorer, and a fresh independent plan review.
