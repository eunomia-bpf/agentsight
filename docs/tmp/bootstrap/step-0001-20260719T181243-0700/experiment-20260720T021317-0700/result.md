# RQ1 Queryable Two-Domain Preflight Result

Status: superseded on 2026-07-21 by explicit author instruction before
supervisor inference
Scientific effect status: no diagnosis, accuracy, localization, intervention,
or superiority result exists
Approved scope: one excluded coding episode and one excluded auto-research
episode, Raw and Trajectory once each after immutable blinded gold

## Attempt history

### Attempt 01: capture passed, source projection invalid

Both diagnostic workloads retained four accepted quiescent boundaries and two
top-level Codex sessions. The first coding store could be serialized after an
initial parser repair, but it contained only 348,336 Raw records, 27 actions,
and 4,143 unbound workspace effects. The auto-research store could not
faithfully bind generated result/test effects.

The cause was source-contract failure rather than workload failure. Codex runs
inside a PID namespace; ordinary `strace -f` output exposed a host PID on the
line prefix but returned child PIDs in the tracee namespace. The constructor
therefore could not prove process-subtree ownership. The first attempt is
retained as failed evidence and is excluded from all condition runs.

### Attempt 02: capture and source-store mechanics passed

Capture was rerun with `strace -f --decode-pids=pidns -ttt -yy -s 4096` over
file and process syscalls. Process edges retain clone time and prefer the
decoded host PID, so reused or pre-exec PIDs cannot enter the matched subtree.
Codex nested `exec_command` wrappers, array-valued results, native result times,
and embedded `apply_patch` calls are parsed through `agent-session`.

The two diagnostic stores are:

| Domain | Episode | Raw records | Actions | Closure counts | Effects | Unbound workspace trace records | Source-store SHA-256 |
|---|---|---:|---:|---|---:|---:|---|
| coding | `e-mxk0i47n5k` | 640,208 | 38 | 33 observed, 3 no-effect, 2 unknown | 1,638 | 1,140 | `1a43e49dcee094a68289ee7a45557fe3dc8bb303fed52d8d9d663a6a1873232b` |
| auto-research | `e-p8f9lghqxh` | 169,474 | 20 | 19 observed, 1 no-effect, 0 unknown | 101 | 738 | `e06a13498b616863e9df9ad0eb987698a28cda33ce35b4150220c010a85fc40f` |

All target-goal actions in both diagnostic stores have `observed` or
`no_effect` closure; neither has a target-goal `unknown` action. Unbound rows
remain visible in `store.json` and Raw evidence and are not silently assigned.
Two separately captured repaired siblings also passed four boundaries and
strict store construction. Their pairing and intervention provenance remain in
the hidden post-gold store and are unavailable to labelers and supervisors.

These counts establish source-path mechanics only. They do not establish that
the projected effects are complete for a scientific population; the approved
preflight still requires closure review over every adjudicated gold action and
used lineage before inference.

## Raw/Trajectory interface parity repair

Raw and Trajectory use the same immutable source store. The common Raw
operations are `list_scopes`, ROUGE-L `search`, exact `read_record`, and exact
`read_range`. Search, record, and range responses now expose the canonical
action IDs supported by each returned Raw ID. This removes the prior schema
asymmetry in which the Raw supervisor was required to predict canonical action
IDs that only the Trajectory interface made directly visible.

Trajectory receives only three additional deterministic relations:
`artifact_history`, `goal_diff`, and `effects`. No diagnosis label, recurrence,
validation decision, hotspot, importance score, or generated summary is
returned by the broker.

## Executable path checks

- `agent-session`: 11 unit tests passed, including nested Codex wrappers,
  embedded patch paths, result pairing, and native end timestamps.
- `agentvis` passes 28 library tests, including PID-namespace subtree
  ownership, unresolved ownership, store-reference validation, Raw/action
  evidence mapping, ROUGE-L conformance, scorer behavior, and condition
  schemas; `agentpprof` passes 14 tests; and the collector passes 205
  non-ignored unit and integration tests (197 library, 5 export/CLI, and 3
  system-runner tests).
- optimized `agentvis` build passed; `research-store --help`,
  `research-supervisor --help`, and `research-score --help` all exited zero.
- the pinned local llama.cpp server is healthy at the frozen endpoint;
  `/apply-template` returned the tool-bearing Qwen prompt and `/tokenize`
  returned exact tokens.
- the coding and auto-research diagnostic store hashes and counts were reread
  from `store.json` after the broker repair.
- an independent set comparison over the real stores found 640,208/640,208 and
  169,474/169,474 unique Raw IDs respectively, zero missing action/effect Raw
  references, and zero missing boundary Raw references. `load_store` now rejects
  duplicate Raw/action IDs and missing action, effect, or boundary references.

No supervisor completion endpoint was called. The approved order requires gold
to exist and be immutable before either condition can see an episode.

## Blinded-gold boundary

`raw/preflight/gold-blind/` now contains the condition-independent annotation
guide, two independent expert forms, a blinded adjudication form, and an
unpopulated scorer-compatible JSONL template with the exact target action
orders. It contains no labels or hidden assignment values. A distributor must
give experts a clean view containing only that material and the two diagnostic
evidence stores; repository-wide access would violate the blind.

The remaining dependency is external human judgment: two qualified independent
experts and a third blinded adjudicator must create the labels, alternate
minimal evidence/action and artifact-lineage sets, intervention, earliest
target action, confidences, and evidence-sufficiency decision. Agent-generated
labels cannot substitute for this requirement.

The clean external handoff is now materialized as
`raw/preflight/agent-nebula-rq1-gold.tar.zst` (25,867,752 bytes, SHA-256
`bf1de475f6f6ca9e7c1b2d7647a68330d993c5c95087f4ad7a3f5767ef13cbed`).
It contains the five unlabeled guide/template files and only the four-file
diagnostic stores for `e-mxk0i47n5k` and `e-p8f9lghqxh`; it contains no capture
directory, repaired sibling, hidden provenance, submission, or supervisor
output. An independent extraction check compared all eight store files
byte-for-byte with their source stores, recomputed the `raw.jsonl` and
`actions.jsonl` hashes recorded in each `store.json`, validated all JSON/JSONL,
confirmed the four boundary names and exact target-action orders, and found no
sibling episode ID or forbidden assignment/mechanism term in either store.

The coding store's 640,208 Raw records cover 198 `agent_native`, 193
`capture_native`, 446,155 `system_trace`, 126,857 `worker_visible_input`, and
the retained boundary archive/manifest/proof and environment/summary records.
The auto-research store's 169,474 Raw records analogously cover 119
`agent_native`, 115 `capture_native`, 164,148 `system_trace`, 1,062
`worker_visible_input`, and all boundary/environment/summary sources. This
establishes that labelers can inspect the approved evidence from the clean
archive without repository-wide or original-capture access; it does not
validate any label.

## Pre-inference artifact-lifecycle conformance repair

A source-to-plan audit after the handoff found that the formal algorithm and
tool description promised versioned artifact identity, but the executable
`artifact_history` still collapsed every rename-connected path into one
permanent string alias. That implementation could conflate delete/recreate and
path reuse, returned no explicit versions, made `goal_diff` a path-only boundary
comparison, and exposed no per-action unknown candidates. Running either
condition with that mismatch would fail the approved mechanism-engagement
check, so it was repaired before gold or inference.

The derived query layer now constructs one deterministic lifecycle projection
per loaded store and reuses it for all calls. Initial non-directory artifacts
come from `h0` in sorted order; read preserves a version; write advances it;
observed rename preserves identity, advances the version, and changes location;
delete terminates the active identity; recreate allocates a new identity; and a
rename overwrite closes the displaced identity using the same source evidence.
Missing prior state, create-on-existing ambiguity, missing rename source, and
unknown operations do not invent identity and remain explicit unresolved
events. `goal_diff` now reports artifacts mutated in both scopes versus only
one scope, with per-scope events and exact boundary state changes. `effects`
returns versioned effects and, only for an `unknown` action, temporally
overlapping unbound Raw IDs as candidates whose attribution remains unknown.

Three focused lifecycle tests cover rename plus path reuse, cross-scope identity
through rename, and bounded unknown candidates. The 30-test `agentvis` library
suite and warning-free Clippy check pass. A temporary read-only check loaded
both immutable attempt-02 stores, evaluated `goal_diff(g1,g2)`, evaluated
`effects` for all 58 actions, and evaluated histories for twelve affected paths
per domain without error. The projection is cached after the first query; the
real-store check, including parsing and hash-verifying 809,682 Raw records,
completed in 17.08 seconds. No source-store byte, Raw/action ID, archive, model
prompt, budget, label, or planned condition changed. This is a plan-conformance
repair and still has no scientific effect.

## Exact-boundary reconciliation and ad-hocness audit

A subsequent algorithm audit found one remaining formal/implementation gap.
The approved method allowed exact quiescent states to update and validate
artifact state, but the executable lifecycle used only `h0`; later manifests
were returned by `goal_diff` without checking that action replay actually
reached them. This could preserve a false identity after an unowned content
replacement or silently miss a create/delete even though the final state was
known exactly.

The projection now reconciles after `g1`, the environment transition, and `g2`.
An artifact with an owned mutation retains identity and receives a
source-backed `boundary_state` anchor without incrementing its mutation revision
twice. If content changes without an owned mutation, the old identity ends and
the newly observed state receives a distinct identity; missing create/delete
effects are likewise explicit boundary issues. The supervisor executable calls
the verifier before creating an output directory or contacting the model. For
an absent path, state-difference answers cite the retained boundary proof rows
containing the complete manifest hash and entry count rather than treating
absence as self-evident.

Two permanent tests cover observed-mutation anchoring and unexplained boundary
replacement; a third checks that a removed path cites the end-boundary proof.
The resulting `agentvis` library suite has 33 tests and Clippy remains clean. A
temporary read-only conformance test again loaded and hash-verified both
diagnostic stores and replayed all 809,682 Raw records and 58 actions through
all four exact states. Both stores had zero boundary discrepancy; the test took
16.92 seconds and was removed after the run. The immutable stores and blinded
archive were not modified.

The same audit confirmed that the declared treatment remains an interface
comparison rather than new information: every event, boundary state, and
unknown candidate returned by Trajectory cites a Raw ID available through the
common `read_record`/`read_range` path, and common Raw responses expose the same
action-ID namespace. A second temporary real-store audit enumerated every
affected path, all 58 action-effect answers, and all three ordered scope-pair
diffs in both domains, recursively checked every returned `raw_id/raw_ids`
against the common Raw-ID sets, and found zero inaccessible reference in 17.49
seconds; that temporary test was also removed. Residual ad-hoc risk remains for the selected three query
plans, ROUGE-L Raw search, and one fixed resource budget; these are evaluation
questions for the later effect pilot, not reasons to alter the approved
two-episode mechanics preflight. The current research captures are Codex-only;
Claude/Gemini source-effect binding remains unqualified and cannot yet support
the future cross-Agent claim.

## Current result judgment

- **run status:** superseded and closed without inference;
- **tested hypothesis:** not tested;
- **research value so far:** dependency-only;
- **paper impact:** none;
- **next paper decision:** replace the human-label estimand through the
  BOOTSTRAP scientific-contract process with an automatically verifiable
  benchmark outcome or causal-replay estimand. The verified source-store,
  lifecycle, boundary, broker, and parity mechanics remain reusable only where
  the replacement experiment independently requires them.

## Closure after author instruction

On 2026-07-21 the author explicitly instructed the project not to use human
annotation and to seek another trajectory or benchmark experiment. This closes
the approved human-gold path. The clean archive remains a record of completed
dependency work, but it will not be distributed for labeling and will not be
used to manufacture Agent-authored substitute gold. No supervisor completion,
label, diagnosis, intervention score, or RQ result was produced. A later
experiment may reuse source-complete capture mechanics, but it must receive a
new plan and independent review because its scientific outcome, oracle, and
comparison task will differ.
