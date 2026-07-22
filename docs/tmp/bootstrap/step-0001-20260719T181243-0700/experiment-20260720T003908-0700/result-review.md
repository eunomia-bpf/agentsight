# Independent Result Review: RQ1 Real Preflight

Reviewed: 2026-07-20
Scope: approved `plan.md`, all three rounds in `plan-review.md`,
`preflight-result.md`, the capture and condition-construction code, and retained
artifacts under `raw/preflight/attempt-1/` and
`raw/preflight/attempt-2/coding-p2-perturbed/`
Reviewer role: fresh result reviewer; no role in planning, implementation, or
execution

## Verdict

**BLOCK the current approved experiment. Accept the decision to stop.** The
declared static-full-context preflight hit its frozen context-fit veto, and it
also lacked a scorer, leaked perturbation identity into both prompts, and did
not satisfy the approved source-ownership closure criterion. No further worker
episodes, supervisor calls, or full-matrix cells should be run under this plan.

- **run status:** invalid as the approved end-to-end diagnosis preflight; valid
  only as a dependency-level capture and context-fit probe
- **tested hypothesis:** inconclusive
- **research value:** dependency-only
- **paper impact:** mechanism/interface boundary, not additional RQ1 evidence
- **next paper decision:** close the frozen static-serialization experiment and,
  if it remains the highest-value next test, propose and review a scientifically
  distinct matched queryable-retrieval experiment. Make no diagnosis-effect or
  representation-superiority claim from this preflight.

The stop itself obeyed the protocol. Once the first valid real coding episode
exceeded the non-negotiable input ceiling, neither its repaired sibling nor the
research pair could make the frozen universal fit requirement pass. The plan
also says a coverage or context failure aborts preflight. Stopping before any
supervisor invocation and before the full matrix was therefore required, not
premature selective reporting.

## Independently reproduced facts

### Attempt 1

Attempt 1 contains no workspace boundary, native session, or summary output.
Its retained `systemd-run.json` shows that the old controller bind-mounted the
repository workload path into the DynamicUser unit; the executed controller is
68,304 bytes with SHA-256
`45a8529694e51e32b9c84b52327f9095b26276e62ebe92bbaea560b4f3bf3c81`.
Cleanup records show that the unit, credential directory, and ext4 image were
removed. This supports classifying it as a pre-session infrastructure failure.
The retained files do **not** contain the reported permission error or journal
line, so the precise “parent mode 0700 prevented traversal” cause is plausible
from the old bind design but not independently provable from the attempt-1 raw
directory alone.

### Attempt 2 capture and workload

The coding workload is source-faithful. The locally pinned SWE-bench Verified
Arrow row identifies `pytest-dev__pytest-10051` at base commit
`aa55975c7d3f6c9f6d7f68accc41bb7cadf0eb9a`. I compared all 570 tracked files
against that commit: every byte matches, with `active_goal.md` as the only
additional workload file. No gold patch or test patch is present in the worker
workspace.

The capture contains two distinct real Codex 0.144.6 threads. Recomputed native
counts match the report:

| session | JSONL lines | bytes | `item.started` | `item.completed` | `turn.completed` |
|---|---:|---:|---:|---:|---:|
| prior | 37 | 35,495 | 14 | 20 | 1 |
| target | 41 | 35,430 | 16 | 22 | 1 |

The session and timestamp-sidecar line counts agree exactly. The prior session
modified only the regression test and generated runtime/cache artifacts. The
target session read the stale `active_goal.md`, explicitly chose the prior-goal
constraint, continued reproduction/bootstrap work, and did not modify the
production implementation. That is a real manifestation of the intended P2
mechanism, although no blinded gold annotation was produced.

I independently reconstructed every archive manifest directly from each tar
stream and compared it with `manifest.json`, `m1.json`, `m2.json`, and
`archive-manifest.json`. All five representations agree at all four boundaries;
the accepted boundary and archive hashes also verify. The canonical manifest
hashes are:

| boundary | entries | canonical manifest SHA-256 |
|---|---:|---|
| H0 | 644 | `930b01dc2e3fa235b6adce9e925db1893e83e65f3d453048e8611ab109663856` |
| prior goal | 670 | `59199224d5ac7d63a5e51f2024d63785da4d883f62114ec6a560ba6ef4bebe29` |
| target start | 670 | `59199224d5ac7d63a5e51f2024d63785da4d883f62114ec6a560ba6ef4bebe29` |
| target | 733 | `c5365e9e07315928e3445c1f0bc65cca39572886381856396e0605884aabfcea` |

The executed attempt-2 controller is byte-identical to the reviewed current
capture script: 68,737 bytes, SHA-256
`b095fb3bed41a063e29e1344bee3a1c89cead92b27ee3d83ebed6096d1e3a266`.
This validates the quiescent snapshot sub-result; it does not validate the
later action projection.

### Condition parity and token accounting

The prompt hashes are:

| condition | bytes | SHA-256 |
|---|---:|---|
| Full Raw | 2,125,926 | `e47b3ff7a6d5eaccdf3ffd349cdc9286f5dfd80d4a6fc31746441101b9d67f31` |
| Full Trajectory | 2,885,469 | `4328af2c054074b0a1384b11675f1df5afcdd04ab575a8606ea7f84b2ee70ebf` |

Their 3,514 `source_records` arrays are exactly equal, with canonical SHA-256
`47b824bc3a72789186db394852f020a80de06f349fb36e0f3e1433e27fd1d361`.
The four boundary arrays and `source_effect_coverage` objects are also exactly
equal. The source-record composition is 3,434 retained strace rows, 78 native
Codex rows, and two environment-effect rows. Full Trajectory additionally has
43 actions, 42 next-action relations, and 970 artifact-lifecycle keys.

I reran `llama-tokenize --show-count --log-disable` with llama.cpp revision
`2d973636e292ee6f75fadcf08d29cb33511f509f` and the pinned model blob whose
content hash is
`f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`.
The report's counts reproduce exactly:

| condition | raw prompt tokens | frozen ceiling | excess factor |
|---|---:|---:|---:|
| Full Raw | 956,130 | 63,488 | 15.06× |
| Full Trajectory | 1,215,415 | 63,488 | 19.14× |

These are raw prompt token counts rather than a retained chat-template-rendered
transcript, but this distinction cannot rescue the row: the raw prompt alone is
already over the complete context by more than an order of magnitude. The
frozen `prompt + 2,048 <= 65,536` condition therefore fails decisively. No
supervisor output exists, as required after this veto.

## Blocking validity findings

### 1. The implemented path-set closure passes, but the approved source closure does not

The narrow implemented check is reproducible. Across H0→prior and
target-start→target there are 78 unique changed non-directory paths (80
boundary-specific path transitions because two paths change in both goals),
164 observed non-read paths, and zero missing paths. I additionally checked
each boundary-specific transition rather than only the union: every transition
has at least one same-goal compatible successful mutation effect, every cited
evidence ID exists, and none of those mutation evidence rows reports a failed
syscall. Thus the report may accurately say “the implemented manifest-path
check returned zero missing paths.”

That is weaker than the approved veto. `research.rs` unions changed path names
across the two goal intervals and asks only whether the same path appears in
any non-read effect. It does not require a matching operation, matching goal
interval, terminal version, or complete sequence of changes. It also has no
mechanism that identifies and checks all validation actions, accepted-gold
actions, or cross-goal lineages. No expert gold exists at preflight. Therefore
the implementation cannot establish the plan's broader claim that every
task-relevant mutation, validation, gold-evidence action, and used lineage has
100% source-backed ownership.

### 2. System-event parsing materially corrupts trajectory attribution

The strace parser treats every relative `openat` pathname as relative to the
process CWD, even when the call uses a different directory FD. For example,
`openat(3</proc>, "4100402/ns", ...)` is normalized as if `4100402/ns` were a
workspace path. In the retained prompts, 2,216 of the 3,434 selected system
records have a non-`AT_FDCWD` `openat` directory FD with a relative pathname.
Of these, 830 are reported unbound and 1,386 are attached to actions as false
workspace reads. None happens to be the exclusive proof for one of the 78
changed-path mutations, but they inflate both prompts and corrupt the proposed
artifact lifecycles and action effects.

Action ownership is also not complete. There are 1,328 unbound selected system
records. Some are task-relevant real workspace reads, not merely startup noise.
For session 1, the successful read of `active_goal.md` occurs at
`1784536449.311318`, while the corresponding Codex `item.started` line is only
observed at `1784536449.342255285`; session 2 has the same pattern at
`1784536573.016154` versus `1784536573.023998632`. Reads of
`src/_pytest/logging.py` and `testing/logging/test_fixture.py` are likewise
unbound. The sidecar records stdout arrival time, and fast command effects can
precede the arrival of their own start event. Consequently, interval matching
does not provide the success ownership promised by the plan.

The 157,415 retained strace lines are reduced to 3,434 selected rows; failed
file syscalls, unrecognized file syscalls, and most non-effect records are not
present in either prompt. Both conditions are equal to each other at the
`source_records` level, but neither is a complete raw serialization of the
captured system trace. The prompt's workspace “snapshots” are manifests with
hashes and sizes, not the archived file bytes. Fact parity between these two
files is therefore real, while the stronger “same complete native/system/
workspace evidence” claim in the plan is not established.

### 3. Prompt construction leaks the intervention and format

Both prompts set `episode_id` to `coding-p2-perturbed` and print the condition
name (`FullRaw` or `FullTrajectory`). More seriously, the runtime path embedded
in retained strace payloads also contains `coding-p2-perturbed`; the word
`perturbed` appears 2,666 times in each prompt. This directly violates the
plan's rule that perturbation identity remains outside supervisor evidence.
The condition label additionally violates the promised same prompt apart from
the evidence representation and may prime the model about the method. Because
no model was called, these are pre-inference invalidity findings rather than a
post-hoc explanation of model behavior.

The stale content of `active_goal.md` is not itself leakage: it is the intended,
neutral P2 treatment visible to the worker and necessary evidence for a later
supervisor. The leak is the treatment name in episode/runtime identifiers.

### 4. The approved end-to-end path was incomplete before inference

`agentvis/research/score_rq1.py` does not exist, although the approved plan
requires the capture, condition, and scoring commands all to exist and print
usage before real preflight. There are no blinded gold labels, supervisor JSON,
metric outputs, or latency records. This alone prevents an end-to-end preflight
PASS and confirms that no diagnosis result can be inferred.

The retained `full-raw.build.log` and `full-trajectory.build.log` record the
earlier missing-relative-rename failure; no retained successful rebuild or
tokenizer command log accompanies the later prompt files. The current prompt
and token hashes make the context veto independently reproducible, but the raw
directory should not be described as a complete command provenance record.

## Interpretation and next experiment

The strongest supported statement is narrow:

> On this real coding episode, the current static Full Raw and Full Trajectory
> prompt constructors exceed the frozen Qwen context budget by 15.06× and
> 19.14×, respectively, before generation; therefore this approved static
> protocol cannot proceed.

The preflight does **not** show that every possible exact static encoding is
fundamentally impossible. The current prompts pretty-print four largely
repeated full manifests and retain many irrelevant or falsely scoped system
rows. A different exact dictionary/delta encoding could be materially smaller.
Nor does the preflight show that trajectory organization helps diagnosis, that
raw retrieval is insufficient, or that any pathology can be detected. Those
questions were never presented to a supervisor.

Moving to a queryable-retrieval comparison nevertheless follows as a reasonable
and scientifically distinct next experiment: it returns to the paper's actual
scalable setting and tests a different interface under a bounded evidence
budget. It must be admitted and plan-reviewed as a new experiment, not treated
as a repair, continuation, or positive result of this one. At minimum, that
plan must:

1. fix directory-FD path resolution and action ownership, then repeat source
   closure on real coding and research episodes;
2. remove treatment, pair, condition, and runtime-name cues from all evidence;
3. provide the frozen scorer and blinded human gold before model inference;
4. give Raw Retrieval and Workspace Trajectory Retrieval the same source
   store, action-ID namespace, model, system prompt, total rendered input and
   output tokens, number of queries, and query-response budget;
5. define the raw retrieval surface as a competent competing mechanism rather
   than a deliberately inconvenient dump, while making deterministic
   workspace/action relations the only intended treatment difference; and
6. freeze any selection, ranking, compression, or stopping policy without using
   pathology labels. A learned or label-tuned selector would confound the
   representation claim.

Until that distinct experiment completes, the paper may cite this artifact
only as an engineering/preflight reason for abandoning the current static
interface, not as RQ1 evidence or a diagnosis-effect result.
