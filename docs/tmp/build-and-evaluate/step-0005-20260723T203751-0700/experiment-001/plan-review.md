# Independent Plan Review

## Verdict

**BLOCK**

The experiment is directionally the right repair: Step 0004 is a legitimate
development set, the proposed held-out source files are numerous enough, and a
source-direct checker that imports neither production parser nor projection
code is an appropriate implementation-conformance oracle.  However, the
current plan can still pass while leaving the paper's cross-session and
artifact measurements invalid.  The following defects must be fixed before
opening the held-out answers.

## Blocking Defects

1. **The held-out split excludes only file hashes, not native-session
   families.**  Multiple transcript/source-stream files can share one
   `native_session_id`, parent history, or forked call prefix.  Selecting a new
   SHA-256 from a native root already present in Step 0004 leaks development
   behavior into the claimed held-out set, especially for the cross-session
   repair being tested.  Freeze by group: exclude every candidate sharing a
   vendor plus native-root identity with any development source, and deduplicate
   repeated calls shared by streams of the same root.  Publish group-overlap
   counts as part of the freeze check.

2. **The declared session unit contradicts the unchanged oracle.**  The
   Step 0004 oracle assigns one session ordinal to each selected physical
   source file (`session_id` includes the source hash), whereas `strict-v1`
   says native-root and source-stream identities remain distinct and the paper
   requires native-root session semantics.  C1--C5 therefore have no frozen,
   unambiguous unit: passing the old questions could preserve the bug rather
   than repair it.  Before freezing, define whether each C question ranges over
   source streams, native-root sessions, or deduplicated native-root
   components; update the independent oracle and question text consistently.
   Source stream must remain provenance, not silently become the semantic
   session.

3. **The A-family control is tautological in the current authoritative
   workflow.**  `deterministic_methods()` currently sets both ProcGrep and
   trajectory A answers from `project["procgrep_action_atoms"]`; equality is
   guaranteed by copying the baseline, not demonstrated by `agent-session` or
   `strict-v1`.  Either derive strict-v1 A answers from strict-v1's own parsed
   action sequence and compare them with pinned ProcGrep, or remove A equality
   as evidence.  No positive result may call the current copied row
   “preservation.”

4. **The proposed total order does not match the frozen source order.**  The
   oracle orders equal timestamps by source SHA-256, native record index, and
   call index.  The plan proposes
   `(timestamp, source_stream_id, source_call_id/event_id)`, but call IDs are
   identifiers rather than native order and can reorder calls sharing a
   timestamp.  Freeze one identical deterministic key on both sides using
   existing source record/call ordinals (with event ID only as a final
   uniqueness tie-breaker), or explicitly revise and independently check the
   oracle order before implementation.

5. **Zero wrong B+C answers is insufficient to validate the projection used
   by RQ1--RQ4.**  A method that abstains on all 60 questions passes the
   zero-wrong clause, while “substantial coverage” has no prospective
   definition.  More importantly, five anchor artifacts and 60 aggregate facts
   do not validate the complete edge set from which RQ1--RQ4 are computed.
   Make exact strong-edge conformance on the whole held-out corpus a
   correctness gate: predeclare required precision and recall (ideally exact
   equality for the deliberately shared strict grammar), report discrepancies
   by vendor/evidence class, and predeclare the minimum B+C answered coverage
   for a positive capability result.  If partial recall is allowed, the paper
   estimands need explicit coverage bounds rather than unqualified recomputed
   values.

6. **Attempted actions and observed effects are mixed without an oracle.**  The
   unchanged question grammar counts attempted reads and mutations regardless
   of Tool result, while strict-v1 says failed paths remain actions but status
   determines whether a mutation is an observed effect.  The standalone
   checker currently does not independently pair Tool results or validate this
   status-dependent effect view.  Specify one measurement contract for each
   paper quantity.  If RQ1--RQ4 use observed effects, the source-direct checker
   must independently reconstruct and score result status/effect admission; if
   only attempted actions are validated, the paper must not upgrade them to
   realized file effects.

7. **The plan lacks an executable frozen selection command and scope.**  It
   does not give the actual held-out projects file, selection seed, exclusion
   mode, or raw-byte limit.  The existing `freeze` default is an aggregate
   163,840-byte cap, which cannot select twelve typical files in several
   projects.  A read-only inventory found ample fresh file hashes
   (AgentSight 1,208; ActPlane 517; bpf-developer-tutorial 43; eunomia.dev 128;
   agentskill-observability-paper 24; Sandlock 42), but the fresh inventory
   contains Claude/Codex and no fresh Gemini files in these workspaces.
   Provide the exact command and fixed seed/cap, verify twelve
   native-root-disjoint sources per project, and restrict the positive
   held-out claim to the vendors actually represented unless a genuinely
   held-out Gemini group is added.  There may be no seed retry after question
   generation or method scoring.

8. **The RQ1--RQ4 before/after sensitivity is not protected against corpus
   drift.**  “Rerun over the original complete six-project corpus” is not
   enough if v0 uses old values and v1 rediscovers live sessions or a changed
   workspace.  Run v0 and v1 on the same immutable archived source set,
   cutoff, worktree mapping, and Git/index manifest.  If the complete original
   corpus was not archived sufficiently to do this, do not report paired
   before/after estimand changes; report the new measurement as a new corpus
   with the old result non-comparable.

## Required Scope Boundary

Even after these repairs, this experiment establishes conformance to a frozen,
project-defined native-record grammar.  It does not establish that native
records contain every real system-level file effect.  The paper may use a
passing result to validate measurements within the declared source-record
scope, but must not call it system-ground-truth completeness.

## What Does Not Block

- Reusing Step 0004 only as a development/error-taxonomy set is sound.
- `current-v0` is a fair paired implementation baseline once its output is
  sealed before repair.
- ProcGrep is a suitable action-only control, and Final State is a suitable
  D-family lookup control, provided neither is copied into the proposed
  method's claimed answer.
- No human annotation, new product IR, or force-layout measurement is needed.
- The six-project block bootstrap is acceptable as corpus sensitivity, not
  population inference.

After the eight defects above are resolved in the plan, a single follow-up
review can decide whether the freeze may run.

---

## Follow-Up Review

### Verdict

**BLOCK — two narrow contract defects remain.**

The revision substantively resolves most of the prior review:

| Prior blocker | Follow-up judgment |
|---|---|
| 1. Native-root leakage | Resolved: exclusion is grouped by `(vendor, native_root_session_id)`, one stream is admitted per held-out root, and file/root/call overlap must be zero. |
| 2. C-family session unit | Resolved in the new workload contract: C1--C5 range over native roots, streams are provenance, and within-root repeated calls are deduplicated. |
| 3. Tautological A control | Resolved: strict-v1 A answers must come from its own ordered `RepositoryEvent` sequence. |
| 4. Inconsistent ordering | Resolved: production and oracle share timestamp, deterministic stream ID, and native Tool ordinal; opaque call ID no longer determines time. |
| 5. All-abstain loophole/incomplete edge audit | Resolved: full strong-edge precision and recall must both be 1.0 overall and per represented vendor, and B+C must be 60/60 with no abstentions. |
| 6. Attempt/effect ambiguity | **Partially resolved; one gate is still missing.** |
| 7. Freeze executability/vendor scope | Resolved: the command fixes seed, source count, exclusion mode, and byte cap; the claim is limited to Claude/Codex. |
| 8. Old/new corpus drift | Resolved: the revised plan explicitly rejects a paired old/new effect and treats the new cutoff as a non-comparable replacement extraction. |

Two remaining defects block the freeze:

1. **Positive status/effect conformance has no explicit pass threshold.**  The
   checker now independently pairs Tool results and the completion rule asks
   for status ledgers, but the primary gate covers only the attempted-edge key,
   which does not contain status.  The Positive interpretation likewise
   requires only exact strong-edge equality and B+C answers.  Therefore
   strict-v1 could assign every successful mutation `fail` (or every failed
   mutation `ok`), pass the written positive gate, and then corrupt the
   status-gated RQ1--RQ4 extraction.  Add an explicit gate requiring exact
   equality of the independently derived per-call status/effect-admission
   ledger—overall and per represented vendor—or include normalized status in
   the complete conformance object.  Define how missing/unknown Tool results
   map to `unknown`, and require effect inclusion decisions to agree exactly.
   Positive and Mixed/Negative interpretation clauses must reference this
   gate.

2. **The plan still simultaneously calls the Step 0004 question grammar
   “unchanged” and changes its C semantics.**  Step 0004 ordered selected
   physical source files as sessions; the revised plan correctly makes native
   root the C-family unit and also corrects path parsing.  Those are necessary
   semantic revisions, not an unchanged grammar.  Replace the “unchanged Step
   0004 question grammar” statement with a precise declaration that the
   A/B/D templates are retained while C session semantics and specified parser
   defects are revised and frozen before held-out selection.  Record a new
   question-spec hash.  Otherwise two incompatible oracle contracts remain
   authorized.

Once these two clauses are corrected, the plan is scientifically executable
as a held-out conformance repair.  Its valid claim remains native-record
conformance, not completeness relative to unrecorded system-level effects.

---

## Final Review

### Verdict

**BLOCK — one contradictory old-contract reference remains.**

The status/effect blocker is resolved.  Exact per-call
`ok`/`fail`/`observed` equality and exact confirmed-effect precision/recall
are now hard gates, and the Positive clause requires both.  This is sufficient
to prevent a correct attempted-edge ledger with incorrect effect admission
from validating RQ1--RQ4.

The new `native-root-conformance-v2` contract is also stated correctly in
Workloads and Metrics and Reproducibility Notes.  However, two earlier lines
still authorize the incompatible Step 0004 contract:

- Published Precedent says: “Reused: the **unchanged Step 0004 question
  grammar** and independent `rq7_source_oracle_check.py`.”
- Planned Runs labels the freeze system as “**unchanged source oracle**.”

The v2 C-family unit, status pairing, path corrections, and checker behavior
cannot all be obtained from the unchanged Step 0004 grammar/oracle.  Replace
these with wording that the A/B/D templates and independent-checker approach
are reused, while the v2 specification and both source derivations are newly
frozen and Step 0004 remains immutable development-only evidence.

No other scientific or executability blocker remains.  Once those two stale
references are removed, the plan merits **PASS** without another substantive
redesign.

---

## Approval

### Verdict

**PASS**

The two stale Step 0004 references have been removed.  The reviewed plan now
freezes a distinct `native-root-conformance-v2` specification and two
independently implemented source derivations, while retaining Step 0004 only
as immutable development evidence.

All eight original blockers are substantively resolved: native-root-disjoint
selection; unambiguous C-family semantics; non-tautological A answers; shared
native ordering; exact attempted-edge, call-status, and confirmed-effect
conformance gates; an executable fixed-seed freeze with Claude/Codex scope; and
an explicitly non-comparable new-cutoff extraction for RQ1--RQ4.  The plan is
scientifically valid and executable for its stated native-record-conformance
claim.  It does not claim completeness for system effects absent from native
records.

---

## Pre-Freeze Feasibility Amendment Review

### Verdict

**PASS**

The amendment is a permissible pre-freeze feasibility correction, not a
post-result workload substitution.  The failed 72-file attempt produced no
copied corpus, question set, oracle answers, or scored projection output; the
experiment directory contains only the plan, review, and held-out project
manifest.  Choosing replacements from native-root availability therefore does
not use outcome information.

A fresh read-only inventory and invocation of the fixed-seed selector confirms
that all six amended cases can supply eight development-disjoint native roots
under the planned 256 MiB per-project bundle cap:

| Case | Eligible roots in selected worktree | Selected roots | Selected vendors |
|---|---:|---:|---|
| AgentSight | 592 | 8 | Claude, Codex |
| ActPlane | 168 | 8 | Claude, Codex |
| bpf-developer-tutorial | 24 | 8 | Claude |
| eunomia.dev | 49 | 8 | Claude, Codex |
| bpf-benchmark | 2,185 | 8 | Claude, Codex |
| kernel-script-paper | 8 | 8 | Claude, Codex |

The selected bundles are all far below the cap.  `kernel-script-paper` has
exactly eight eligible roots, but the authoritative selector completes with
eight distinct roots at the frozen seed and does not require a retry.

The resulting matrix remains internally consistent: 48 held-out source files,
six project blocks, 20 questions per project, 120 total questions, and 60 B+C
questions.  Native-root grouping, v2 semantics, ordering, status/effect gates,
Claude/Codex scope, no-retry rule, and non-comparable later extraction are
unchanged.  Replacing the two infeasible cases with one large repository and
one auto-research workspace does not change the tested conformance claim.
