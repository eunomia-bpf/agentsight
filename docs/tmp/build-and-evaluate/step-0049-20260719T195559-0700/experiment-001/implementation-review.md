# Independent Implementation Review — Experiment 001 (Multi-Resolution Recurrence)

**Reviewer model:** Claude Opus 4.8 (`claude-opus-4-8`), acting as the independent
implementation reviewer.
**Mode:** read-only audit. No code, plan, paper, skill, or other file was edited;
no git mutation was run; no preflight or full candidate evaluation was executed;
no candidate B-cubed, boundary, bootstrap, or rescue metric was computed.
**Skill followed:** complete `research-experiment-design/SKILL.md` and
`references/plan-template.md` at
`/home/yunwei37/workspace/my-paper-work/academic-writing-skills/skills/research-experiment-design/`.

**Verdict: PASS** (retained after the post-review repair below).

**Amendment, post-review repair.** After the first issue of this report, a
minimal repair was made in `script/rq3_codetracebench_stage_fidelity_eval.py`
only. I re-read it (lines 758–781) and re-ran `python3 -m py_compile` on the
repaired file (ok). **MF-2 is resolved.** **MF-1 is downgraded to an execution-
and-reporting obligation** with a now-specified route; it was never a code
blocker. Root also supplied external closure evidence for O-6. PASS is retained
and REAL PREFLIGHT remains authorized. Amendment details are recorded inline in
§2 and §3 and summarized in §5.

---

## 0. Scope, Materials, and One Method Limitation

### Inspected

- `experiment-001/experiment-plan.md` (approved plan)
- `experiment-001/plan-review.md` (Grok 4.5, APPROVE, no must-fix)
- `agentpprof/src/profile.rs` — working-tree state, whole induction path
  (report structs at 291–432; `induce_operation_stack` at 1186–1504; recurrence
  primitives at 1506–1671; `recurrence_motif` at 1904–1920; tests at 3700–3903)
- `script/rq3_codetracebench_stage_fidelity_eval.py` — working-tree state,
  whole file
- `script/rq3_recurrence_stack_induction_eval.py` — OSWorld equivalence
  evaluator (contract compatibility)
- `script/codetracebench_agentprof_eval.py` — `raw_action_key()` provenance
  (601–629)
- Step 0024 retained artifacts under
  `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/`
- Canonical CodeTrace operation records under
  `docs/visexp/out/codetracebench-rq2/full/`

### Executed checks (permitted class only)

| Check | Result |
|---|---|
| `cargo test --manifest-path agentpprof/Cargo.toml` | **ok — 50 + 10 + 3 passed, 0 failed** |
| `python3 -m py_compile` on the three eval scripts | **ok** |
| `agentpprof` version vs. the version both evaluators pin (`0.2.37`) | **match** (`agentpprof/Cargo.toml:3`) |
| `python3 -m py_compile` re-run on the repaired stage-fidelity script | **ok** (amendment pass) |
| `cargo fmt --check` | **not run by me** — the harness denied the command; closed externally, see "External closure" below |

### External closure supplied by root (not my independent execution)

Root reports having run, successfully: `cargo fmt --all -- --check`, Python
compilation, and `git diff --check`. I record this as **root-supplied evidence,
not as a check I executed or independently confirmed** — my own git and
`cargo fmt` invocations remained denied throughout. It closes O-6's formatting
and whitespace-hygiene component. Note that `git diff --check` detects
whitespace errors and conflict markers only; it is **not** a diff-content review,
so the diff-level provenance question in O-6 (that nothing unrelated changed in
the two files) is narrowed but not fully closed by it.

### Method limitation, stated honestly

**All `git` invocations were denied by this session's permission layer**
(`git status`, `git diff`, `git show`, `git stash list` — every form refused).
I therefore could **not** isolate the uncommitted diff as a diff. I audited the
**working-tree state** of both files in full and identified the
experiment-introduced surface by inspection (every `action_detail` /
`detail_*` / `coarse_boundary` construct, plus the fallback and legacy paths
they touch). This is sufficient to judge mechanism fidelity, minimality, and
test adequacy, and I state each conclusion from code I actually read. It is
**not** sufficient to certify that no unrelated line elsewhere in these two
files changed. A diff-level provenance check remains open and should be done by
whoever holds git access before adoption. `cargo fmt --check` was likewise
denied; formatting is unverified.

---

## 1. The Ten Required Fidelity Checks

### 1. Detail activates only with complete reference **and** target detail, and only when supervised calibration is absent — **PASS**

`profile.rs:1214-1216`:

```rust
let detail_enabled = supervised_calibration.is_none()
    && recurrence_uniform_detail(reference, "induction reference")?
    && recurrence_uniform_detail(&samples, "induction target")?;
```

`recurrence_uniform_detail` (1544–1560) returns `true` only when `present ==
samples.len()`, i.e. **every** operation carries exactly one non-empty
`action_detail`; it hard-errors on multi-valued detail. Partial coverage
silently disables detail rather than half-enabling it — correct. Short-circuit
`&&` means the supervised path never even evaluates detail presence. The
detail model is built only under `detail_enabled` (1217–1225).

### 2. Detail state is the full `(action, action_detail)` identity, with the same NPMI / two-means / `min(global, signature-change)` rule — **PASS**

`RecurrenceState { action: String, detail: Option<String> }` (1516–1520) is the
compound signature; `recurrence_state` (1562–1574) fills `detail` only when a
detail field is requested. The **same** `recurrence_model` function (1601–1658)
is reused with `detail_field = Some("action_detail")` — same NPMI formula, same
`recurrence_calibration` → `deterministic_recurrence_two_means`, same
occurrence-weighted score vector. `recurrence_applied_cutoff` (1576–1586)
compares `left == right` on the **whole** `RecurrenceState`, so at detail
resolution "same signature" means identity of the compound pair and
`(inspect,ls)→(inspect,cat)` correctly takes the
`min(global, signature-change)` branch. This resolves plan-review optional
note #2 exactly as that note requested. `cross_action_scores` in
`recurrence_model` (1643) likewise partitions on full-state inequality, so the
detail model's "signature-change" calibration population is coherent.

No score blending, no interpolation weight, no new threshold, no support
minimum, no window. Confirmed against plan-review §3.6 and the plan's
"no field combination" clause read as *compound signature yes, score blend no*.

### 3. Final continuity is coarse OR detail; detail can remove but never add a coarse boundary — **PASS**

`profile.rs:1312`:

```rust
let boundary = coarse_boundary && !detail_continuity.unwrap_or(false);
```

Since `coarse_boundary == !coarse_continuity`, this is exactly
`boundary = !(coarse_continuity || detail_continuity)`. `boundary → coarse_boundary`
holds by boolean construction, so a detail-added boundary is **structurally
impossible**, not merely checked. The defensive guard at 1386–1391 (`bail!("detail
recurrence added a coarse-relative boundary")`) and the Python per-decision
`require` at `rq3_codetracebench_stage_fidelity_eval.py:240-243` are therefore
belt-and-braces. See optional note O-1 on what that implies for test strength.

`coarse_boundary` (1265) is computed from `applied_cutoff` exactly as the
release `boundary` was, so the coarse arm is untouched.

### 4. Missing / unseen / weak detail exactly falls back — **PASS**

Three fallback routes, all verified in code:

- **Field absent or partially present** → `detail_enabled == false` →
  `detail_model == None` → the tuple at 1309–1311 is all `None` →
  `detail_continuity.unwrap_or(false) == false` → `boundary == coarse_boundary`.
- **Field present, pair unseen in reference** → `score == None` →
  `continuity = score.is_some_and(...)` is `false` (1294) → coarse decision.
- **Field present, pair seen, NPMI below applied cutoff** → same `false`.

`Operation::values` (517–519) returns an empty slice for a missing key, so an
absent field is a clean no-op rather than an error.

### 5. Motifs remain coarse — **PASS**

`recurrence_motif` (1904–1920) reads only `OPERATION_STACK_ASSOCIATION_FIELD`
and emits `action=<run-length-compressed coarse actions>`. `action_detail` never
reaches the visible hierarchy or the derived `operation` field. The new test
asserts `"action=a-then-b"` on a detail-rescued segment (3902).

### 6. Legacy no-detail and supervised paths are semantically unchanged — **PASS**

- Every new field on `OperationStackBoundaryDecision` (405–422) and
  `detail_recurrence` on the report (338–339) carries
  `#[serde(skip_serializing_if = "Option::is_none")]`. With detail disabled all
  are `None`, so **serialized legacy JSON is byte-identical** to the release
  shape. `coarse_boundary: detail_enabled.then_some(coarse_boundary)` (1339) and
  `detail_rescued_coarse_boundary` (1313–1314) are `None` on the legacy path.
- `selected_evidence_fields` / `selected_source_fields` stay `["action"]` unless
  detail is enabled (1392–1395).
- Supervised path: detail is disabled by construction (check 1), and
  `fit_supervised_recurrence_cutoff` (1681+) still calls `recurrence_state(..,
  None, ..)`, so its states carry `detail: None` and its cutoff search is
  unchanged.
- **Empirical:** the pre-existing induction regression tests
  (`operation_stack_induction_only_removes_current_cross_action_boundaries`,
  `..._derives_operation_frames_without_oracle_fields`,
  `..._disambiguates_normalized_child_labels`, the supervised-calibration tests,
  and all 10 `profile_spec_cli` integration tests including
  `cli_induces_operation_stack_from_external_reference_corpus` and
  `cli_calibrates_recurrence_from_grouped_reference_operations`) **all pass
  unchanged**. This is the real evidence for exact fallback — see MF-1.

### 7. Report fields permit raw reconstruction without leaking scorer labels — **PASS**

Per decision: `left_action_detail`, `right_action_detail`, `detail_npmi`,
`detail_unseen_in_reference`, `detail_calibration_population`,
`detail_applied_cutoff`, `detail_continuity`, `coarse_boundary`,
`detail_rescued_coarse_boundary`, alongside the retained coarse `npmi`,
`applied_cutoff`, `current_boundary`, `boundary`. Model-level:
`OperationStackDetailRecurrenceReport` (344–368) carries both calibrations'
centers, occurrences, iterations, cutoffs, the `signature_change_applied_cutoff`
= `min(global, cross)`, transition counts, seen/unseen counts, and
rescued/added counts. A reviewer can recompute every boundary from these fields
alone. None of these is a stage, human group, phase, benchmark id, or any
`ORACLE_OR_LABEL_*` entry; `action_detail` matches no oracle field, prefix, or
suffix in the lists at 1114–1174.

### 8. CodeTrace adapter passes only pre-existing source-visible `raw_action_key`, before manifest stages load — **PASS**

- `load_visible_operations` (105–139) reads the operations JSONL only, requires
  `raw_action_key` non-empty, and maps it to `action_detail`.
- `minimal_rows` (142–158) emits exactly `{session, action, action_detail}` with
  `value: 1`; the contract is re-asserted at 666–674 over **both** reference and
  target rows.
- Ordering is correct: `run_recurrence` at line 675, `recurrence_predictions` at
  676, and only then `load_stages_after_prediction` at 681 — the function whose
  own docstring marks it as "the only function allowed to read scorer-only
  official stages". No parquet read occurs before prediction.
- Provenance: `raw_action_key()` (`codetracebench_agentprof_eval.py:601-629`) is
  a pure deterministic function of the action text (structured `[tool]` marker,
  else shell head after env/wrapper/`bash -c` stripping, else `"other"`). No
  label, stage, oracle, or manifest input. Confirmed present in the retained
  canonical records (`docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl`).
- The scorer-only manifest columns remain `traj_id, agent, task_name, solved,
  step_count, stages`.

### 9. Baseline reproduction, B-cubed, task-cluster bootstrap, full population, fixed verdict — **PASS**

- **Baseline reproduction.** `attach_current_recurrence` (427–449) loads the
  Step 0024 release assignments from
  `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/operation-assignments.jsonl`
  (verified to exist and to contain the `recurrence` group column). In `full`
  mode the recomputed baseline B-cubed precision/recall/F1 must match the
  retained Step 0024 summary to `1e-12` (717–725), and the population dict is
  checked field-by-field (703–716). This is genuine reuse plus a hard
  reproduction gate, matching the skill's reuse-before-rerun preference.
- **B-cubed.** Ordinary unweighted per-operation, computed over
  `operation_rows`; both predicted and official group ids are session-scoped, so
  no cross-session mixing is possible. Token-weighted / budget / reader scores
  are absent, as the plan requires.
- **Bootstrap.** `task_cluster_bootstrap` (462–525) clusters on `task_name`,
  hard-requires exactly 251 clusters (486), resamples 10,000 times with a fixed
  seed (`BOOTSTRAP_SEED = 20260719`), and computes the **paired**
  candidate−current F1 delta from per-session sufficient statistics. Raw draws
  are retained to `task-bootstrap-deltas.jsonl`.
- **Full population.** `EXPECTED_*` constants pin 2,229 disjoint reference
  sessions / 87,703 ops and 405 targets / 20,866 ops; disjointness, action-kind
  set, and Rust-side reference/target counts are all re-checked (632–659,
  733–743).
- **Fixed verdict.** 758–772 implements the plan's registered rule verbatim:
  `delta > 0 AND ci95_low > 0 → supported`; `delta > 0 → promising_but_not_established`;
  else `contradicted`. Preflight is hard-wired to `"not tested"` with an
  explicit "diagnostics only" interpretation (747–757). No outcome-dependent
  branch can rewrite the rule. See MF-2 on the one gap: this verdict does not
  itself consult the OSWorld arm.

### 10. Minimality and focused tests — **PASS with a noted gap**

**Minimality: confirmed.** The Rust surface is one constant, one `Option<String>`
field on `RecurrenceState`, one `detail_field` parameter threaded through two
existing functions, one gate, one second model instance, one OR, one report
struct, and the decision fields. No new algorithm name, hyperparameter,
embedding, promotion gate, schema language, or control interface — consistent
with the skill's ban on project-authored experiment-control interfaces. The
Python surface is one extra field through the existing loader/serializer plus
report/validity plumbing.

**Test: one focused test,
`operation_stack_induction_uses_recurrent_detail_only_to_rescue_continuity`
(3841–3903).** It constructs a reference where the coarse `a→b` pair is diluted
but the detailed `(a,x)→(b,y)` pair recurs, then asserts
`coarse_boundary == Some(true)`, `detail_continuity == Some(true)`,
`detail_rescued_coarse_boundary == Some(true)`, `!boundary`,
`segments.len() == 1`, coarse motif `"action=a-then-b"`, and
`selected_source_fields == ["action", "action_detail"]`.

**This test does fail if detail is ignored** — with detail ignored the coarse
boundary stands, `boundary` is true and `segments.len()` becomes 2. That half of
requirement 10 is satisfied. The "allowed to add a boundary" half is satisfied
only vacuously; see O-1.

---

## 2. Must-Fix

Neither item blocked REAL PREFLIGHT. Post-repair status: **MF-2 resolved**;
**MF-1 open as an execution-and-reporting obligation**, with the route now
specified.

### MF-1 — OSWorld must run the Rust-equivalence route, and the result report must say so — **OPEN (execution/reporting obligation, not a code blocker)**

`script/rq3_recurrence_stack_induction_eval.py` computes OSWorld boundaries in
**Python**: `transition_npmi` (121), `deterministic_two_means` (171),
`predict_fold` (219) with its own `min(global, cross_action)` cutoff at 237.
`run_profiler` (562–629) invokes `agentpprof` **without**
`--induce-operation-stack` — it passes `--stack project,dataset,operation` over
rows whose `operation` motif was already assigned in Python
(`candidate_operation_rows`, 538–559). The Rust induction path is never called.

Consequence: running all five OSWorld folds will reproduce the release numbers
**by construction**, because none of the changed code runs. The plan's
OSWorld-Human section ("The candidate must reproduce all current release
decisions and standard metrics exactly. Any difference invalidates the
implementation") is therefore **trivially satisfied and verifies nothing** about
the new constructor. Writing it up as "OSWorld confirms exact fallback of the
multi-resolution constructor" would be a validity misstatement.

The genuine exact-fallback evidence is elsewhere and is real: the
`skip_serializing_if` field discipline, `boundary == coarse_boundary` when
`detail_enabled` is false, and the full set of pre-existing Rust induction and
CLI tests passing unchanged (check 6).

**Route decided by root (accepted).** OSWorld execution will use the **existing
Rust/Python equivalence evaluator over all five detail-free folds**, not the
Python-only score path described above. That is the correct resolution: it
routes the detail-free OSWorld population through the modified Rust constructor,
so exact fallback becomes a **measured** property of the changed code rather
than a vacuous consequence of the changed code never running. It uses an
evaluator that already exists, so it adds no new control interface and does not
broaden the experiment.

**What remains open, and why it is not a code blocker.** Nothing in the
implementation needs to change for this; the obligation is on execution and
reporting. I have **not** verified by execution that the equivalence route
produces exact Rust-level fallback on all five folds — that is precisely what
the run must establish, and I am prohibited from running it here. Two conditions
therefore carry forward:

1. **Execution.** All five detail-free OSWorld folds must go through the
   Rust/Python equivalence evaluator. If any fold diverges from the release
   decisions, the plan's own rule applies: the implementation is invalid, not
   the experiment inconclusive.
2. **Reporting.** The result report must state the distinction explicitly —
   that OSWorld fallback was established via the **Rust equivalence route**, and
   **not** via the Python-only score path in
   `rq3_recurrence_stack_induction_eval.py`, whose `run_profiler` (562–629)
   omits `--induce-operation-stack` and would have reproduced the release
   numbers by construction. Without that sentence a reader cannot tell a
   measured fallback from a vacuous one.

The underlying finding stands as originally written: this was a **wiring and
evidence-route** defect, never a mechanism defect. The plan's validity property 1
is true of the implementation on inspection (§1 check 4); the repair makes the
OSWorld arm actually capable of demonstrating it.

### MF-2 — Per-population verdict was readable as the plan-level verdict — **RESOLVED**

*Original finding.* The plan's Supported rule is a conjunction: point estimate
higher **and** bootstrap CI wholly positive **and** OSWorld fallback exactly
identical **and** all validity properties pass.
`rq3_codetracebench_stage_fidelity_eval.py` registered `"supported"` on the
first two conjuncts alone, under the unqualified key `registered_verdict`, so
`summary.json` could be read as declaring the plan-level verdict.

*Repair verified.* I re-read lines 758–781. The local outcome is now named
`codetrace_verdict`, and a sibling key states
`"experiment_verdict": "pending_osworld_fallback_and_independent_review"`.
`tested_hypothesis` is namespaced to `f"codetrace_{codetrace_verdict}"` (767),
and the prose `interpretation` (774–781) now says the verdict is "for this
population" and that the experiment verdict "remains pending the Rust-level
OSWorld fallback check, all validity checks, and independent result review."

*Assessment.* This is the smallest sufficient fix and I accept it. The
decision logic itself is untouched — the three-way rule at 761–766 is byte-for-
byte the plan's registered rule, so the repair renames and qualifies the output
without altering any threshold, comparison, or branch. No metric was recomputed.
The preflight branch (747–757) still hard-codes `"not tested"`. `py_compile`
passes on the repaired file. The pre-existing
`"overall_verdict": "requires the complete OSWorld-Human population"` at 555 and
its mirror in the OSWorld script (644) remain consistent with the new naming.

**MF-2 is closed.** No further action is required on it.

---

## 3. Optional Notes (non-blocking, must not broaden the experiment)

- **O-1 — "detail never adds a boundary" is structurally true, so its assertions
  are vacuous.** `assert_eq!(detail.added_coarse_boundaries, 0)` (3894), the
  Rust `bail!` at 1386–1391, and the Python `require` at 240–243 cannot fail
  given `boundary = coarse_boundary && !continuity`. They are fine as defensive
  guards, but the result review should credit the **boolean form**, not these
  counters, as the guarantee.
- **O-2 — Untested fallback branches.** There is no unit test for (i) a present
  but *unseen* detail pair falling back, (ii) *partial* detail coverage
  disabling the mechanism, (iii) supervised calibration suppressing detail, or
  (iv) legacy JSON omitting the new fields. All four are correct by reading, and
  the existing legacy tests cover the field-absent case implicitly. Adding them
  would be cheap, but they are polish, not blockers.
- **O-3 — OSWorld input scrubbing is a denylist, not an allowlist.**
  `candidate_operation_rows` (546–551) forwards every non-leakage field. Today
  OSWorld has no `action_detail` field, so the fallback holds. If such a field
  ever appeared, detail would activate silently. Worth a comment, not a gate.
- **O-4 — Several `validity` entries are literals, not computations.**
  `reference_target_session_disjoint`, `rust_inputs_only_*`,
  `action_detail_is_preexisting_source_visible_raw_action_key`,
  `phase_and_stages_excluded_from_rust`,
  `official_stages_loaded_after_prediction`, `algorithm_or_threshold_search`
  are hardcoded (849–866). Each is backed by an earlier hard `require` that
  aborts the run, so they are not false — but they assert rather than measure.
  This matches the pre-existing Step 0024 pattern.
- **O-5 — Preflight prints candidate metrics.** Preflight emits `boundary_f1`
  and `bcubed_f1` to stdout and a metrics table to `report.md`, correctly
  labelled "Diagnostic Metrics (not a scientific result)" with
  `tested_hypothesis: "not tested"`. This is pre-existing behavior. The plan
  permits it ("its metric cannot alter the rule") but the operator must not act
  on the number, and the result review should confirm no algorithm or threshold
  change occurred between preflight and the full run.
- **O-6 — Unverified by me:** `cargo fmt --check` (command denied) and
  diff-level provenance that nothing unrelated changed in the two files (all git
  denied). Both should be closed by someone with the necessary permissions.

---

## 4. Fidelity Summary

| # | Check | Verdict |
|---|---|---|
| 1 | Activation gate (complete detail both sides; supervised absent) | PASS |
| 2 | Full `(action, action_detail)` identity; same NPMI/two-means/min rule | PASS |
| 3 | `coarse OR detail`; removal-only, never additive | PASS |
| 4 | Missing / unseen / weak detail falls back exactly | PASS |
| 5 | Motifs remain coarse | PASS |
| 6 | Legacy no-detail and supervised paths semantically unchanged | PASS |
| 7 | Raw reconstruction possible; no scorer-label leakage | PASS |
| 8 | CodeTrace adapter: source-visible `raw_action_key` only, pre-manifest | PASS |
| 9 | Baseline reproduction, B-cubed, bootstrap, full population, fixed verdict | PASS |
| 10 | Minimal implementation; test fails if detail ignored | PASS (gap in O-1/O-2) |

The implementation is a faithful, minimal expression of the approved mechanism.
I found no deviation from the plan's algorithm, no scorer-label channel, no new
threshold or control interface, no broadening of scope, and no change to the
thesis, the four RQs, or the paper-level hypothesis. The two must-fix items are
about **how the evidence may be described**, not about what the code computes.

---

## 5. Authorization

**REAL PREFLIGHT is AUTHORIZED**, under the approved plan's Execution Sequence
step 4 and unchanged constraints:

- one OSWorld fold-0 run and one complete CodeTraceBench target, `preflight`
  mode only;
- preflight establishes **executability and isolation only**; its metrics are
  diagnostics and may not alter the rule, the cutoffs, the fields, or the
  verdict logic;
- **no algorithm, threshold, field, or evaluation change after preflight**; any
  such change is a recorded plan deviation that reruns affected cells;
- at most three preflight attempts, per the skill;
- retain raw commands, stdout/stderr, profiles, inputs, decisions, and
  assignments under
  `.agentsight/experiments/rq3-multiresolution-recurrence-v1/`.

**Still prohibited:** proceeding to the full run before preflight succeeds;
adding a second candidate, score blend, population-specific gate, new benchmark,
or alternative primary metric; mapping OSWorld `target` / `phase` / human-group
fields into `action_detail`; touching `docs/agentpprof-paper/`; treating a
Supported CodeTrace result as an untouched answer to all of RQ3 or as license to
alter the thesis or the four RQs.

**Gate on the result review, not on preflight:** MF-1 and MF-2 must be closed
before any conclusion is written. Additionally, someone with git access should
close O-6 (formatting check and diff-level provenance) before adoption, since I
could not.

---

**End of implementation review.**
