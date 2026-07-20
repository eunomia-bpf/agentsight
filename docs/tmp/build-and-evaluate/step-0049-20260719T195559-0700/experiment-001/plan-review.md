# Independent Pre-Implementation Plan Review — Experiment 001

**Reviewer model:** Grok 4.5  
**Skill followed:** `research-experiment-design` (complete `SKILL.md` + `references/plan-template.md`)  
**Mode:** read-only scientific/executability review; no implementation; no candidate metric computation; no plan edit  
**Reviewed artifact:** `docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-001/experiment-plan.md`  
**Review date:** 2026-07-19  
**Verdict:** **APPROVE**

---

## 1. Scope And Materials Independently Inspected

This review follows the skill’s PLAN REVIEW gate only. It does not authorize
result interpretation, paper edits, or any code change beyond the judgment that
the written plan is scientifically and operationally fit to implement.

### Skill and template

- `/home/yunwei37/workspace/my-paper-work/academic-writing-skills/skills/research-experiment-design/SKILL.md`
- `/home/yunwei37/workspace/my-paper-work/academic-writing-skills/skills/research-experiment-design/references/plan-template.md`

### Experiment and admission history

- `docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-001/experiment-plan.md`
- `docs/tmp/build-and-evaluate/step-0026-20260715T063827-0700/step-report.md`
- `docs/tmp/build-and-evaluate/step-0026-20260715T063827-0700/common-error-audit.md`
- `docs/tmp/build-and-evaluate/step-0026-20260715T063827-0700/admission-review.md`
- `docs/evaluation.md` (RQ3 and operation-induction history)
- `docs/operation-stack-induction-algorithms.md`
- `docs/user-instruction.md`
- `docs/idea-story.md` (fixed story / RQ / thesis boundary only)

### Code and data contracts (provenance and isolation only)

- `script/codetracebench_agentprof_eval.py` — `raw_action_key()` derivation and operation serialization
- `script/rq3_codetracebench_stage_fidelity_eval.py` — visible-input isolation, minimal Rust input, scorer timing
- `script/rq3_recurrence_stack_induction_eval.py` — OSWorld fold protocol and visible-action isolation
- `agentpprof/src/profile.rs` — current recurrence NPMI, two-means calibration, monotone cross-action rule
- Canonical CodeTrace operation files at `docs/visexp/out/codetracebench-rq2/full/{reference,target}-operations.jsonl` (field presence and within-kind diversity only)
- OSWorld retained operation fields under the Step 0024/monotone population (action↔target redundancy only)

No candidate multi-resolution scores, B-cubed values, boundary F1 values, bootstrap draws, or other outcome numbers for the proposed rule were computed or inspected.

---

## 2. Skill PLAN REVIEW Checklist

| Concern | Finding |
|---|---|
| Tests the declared hypothesis and adds valid RQ evidence? | **Yes.** One mechanism hypothesis inside unchanged RQ3; expected and contradictory outcomes are predeclared and falsifiable. |
| Admission rationale holds (non-duplicate, decision-relevant)? | **Yes.** Step 0026 closed further action-only flat-segmentation tweaks; this plan admits a new source-visible discriminator and multi-resolution continuity rule, which is exactly the future path Step 0026 left open. |
| Baselines, workloads, standard primary metric, fairness? | **Yes.** Main baseline is the release Step 0024 coarse recurrence constructor. Ordinary unweighted per-operation B-cubed is the existing standard partition metric. Controls are labeled as controls. At most one main baseline is required; the plan is not baseline-inflated. |
| Command, data path, repetitions, completion, interpretation executable? | **Yes, with ordinary implementation glue.** Populations, isolation rules, validity properties, full-run matrix, and fixed interpretation are sufficient. Exact bash lines are thinner than the Step 0024 plan but point at the same existing eval paths; this is not an invalidating gap. |

Blocking standard applied (skill): only a scientific or executability defect that would invalidate the result blocks execution. Optional polish does not.

---

## 3. Review Against The Seven Required Questions

### 3.1 Exactly one RQ and one tested hypothesis?

**Pass.**

- Paper RQ is exactly **RQ3 — How accurate are the tags?**
- One tested hypothesis: multi-resolution continuity
  (`coarse_continuity OR detail_continuity`) improves ordinary B-cubed F1 on
  the complete existing CodeTraceBench population relative to the current
  coarse-only constructor, and exactly falls back when non-redundant detail is
  absent.
- The plan correctly states it does not answer all of RQ3 and cannot revise the
  paper-level positive hypothesis from its local outcome.
- Exact fallback is a validity/safety clause of the same mechanism, not a second
  independent scientific hypothesis.

No RQ rename, split, merge, or second competing claim is introduced.

### 3.2 Is `action_detail` a genuine observable discriminator rather than a label/proxy/leak?

**Pass.**

Provenance reconstruction:

1. `raw_action_key()` in `codetracebench_agentprof_eval.py` is a deterministic
   parse of source-visible action text: structured tool marker, shell head after
   wrapper stripping, or `"other"`. It is computed in `profile_steps()` together
   with `action_kind`, **before** any official stage range is eligible to load.
2. Canonical CodeTrace JSONL already stores `raw_action_key` on every reference
   and target operation (`docs/visexp/out/codetracebench-rq2/full/`). Field
   presence is complete for the declared populations; empty keys were not
   observed in the inspected complete files.
3. The current stage-fidelity path deliberately **drops** this field today:
   `load_visible_operations()` keeps only `session` / coarse `action` /
   `phase`, and `minimal_rows()` emits only `{session, action}` into Rust.
   Official stages enter only in `load_stages_after_prediction()` after
   predictions are fixed. Passing `raw_action_key` as optional `action_detail`
   therefore extends an already-isolated visible contract; it does not open the
   scorer channel.
4. Within the complete CodeTrace target population, coarse kinds still contain
   substantial source-key diversity (for example many distinct keys under
   `inspect`, `execute`, `edit`, `search`). The compound signature is therefore
   not a tautological rename of `action_kind`. Some keys also appear under more
   than one kind, so the plan’s dual-resolution form
   `(action, action_detail)` is the right unit rather than replacing coarse
   action with raw key alone.
5. The field is already used as the matched **raw-action** organization baseline
   / control in related CodeTrace work. That prior use is a competing simple
   partition of the same visible signal, not an oracle stage identity. The plan
   correctly keeps contiguous `raw_action_key_change` as a descriptive control,
   not as the proposed mechanism.
6. OSWorld-Human retained fields show `target` is a fully deterministic
   function of `action` on the inspected complete population (22 actions, 0
   multi-target actions; e.g. `click→ui`, `type→text`, `press→key`). The plan’s
   refusal to map `target` / `phase` / human-group fields into `action_detail`
   is therefore required, not optional caution.

Causal role stated by the plan is acceptable and non-circular:

- coarse action pools evidence under sparsity;
- recurrent concrete transitions disambiguate occurrences that share a coarse
  pair identity (the Step 0026 aliasing diagnosis: mixed official labels for
  99.7% of CodeTrace ordered coarse pairs).

This is the “observable semantic field with a stated causal role” path that
Step 0026 required. It is **not** a gold stage, human group, phase oracle,
benchmark id, or learned label.

Residual scope note (not a blocker): `raw_action_key` already existed in the
development corpus during Steps 0022–0026. Selecting it after the aliasing audit
makes the result **post-hoc mechanism evidence on reused trajectories**, which
the plan already declares. That does not convert the field into a leak; it only
limits how strongly the outcome may be sold as untouched confirmation.

### 3.3 Is the OR-of-continuity / AND-of-boundaries rule scientifically principled rather than post-hoc benchmark tuning?

**Pass.**

Formal rule in the plan:

- `coarse_continuity`: coarse pair seen and NPMI ≥ applied coarse cutoff
- `detail_continuity`: detailed pair seen and NPMI ≥ applied detail cutoff
- `boundary = not (coarse_continuity or detail_continuity)`

Equivalently: detail may **remove** a current coarse boundary, never add one.

Why this is principled relative to the retained diagnosis, not a second Step
0025-style local suppression chosen after seeing signs:

1. **Problem match.** Step 0026 showed that identical coarse pairs remain
   label-ambiguous; another cutoff, support bucket, local window, or
   population-confounded sign gate cannot break that aliasing. A second
   resolution that is still a directed adjacent transition, still NPMI, and
   still the same two-means / monotone cutoff machinery is the minimal change
   that introduces a new occurrence identity.
2. **Asymmetry has a sparsity justification.** At fine grain, unseen and rare
   pairs are expected. Absence or weak recurrence of a fine pair is therefore
   **not** reliable positive evidence of a boundary. Treating fine resolution as
   *positive continuity evidence only* is the scientifically conservative use of
   a sparse signal. The dual of that statement is exactly OR-of-continuity /
   AND-of-boundaries.
3. **Continuity with the release monotone design.** The current Step 0024 rule
   already encodes “recover continuity without adding a global-rule boundary”
   via `min(global, cross_action)`. The multi-resolution OR extends that same
   monotone philosophy across resolutions rather than inventing a new score
   blend, margin, or population gate.
4. **Not the rejected Step 0025 mechanism.** Step 0025 suppressed boundaries
   using sequence-local raw-NPMI minima on the **same coarse pairs**. That rule
   removed mostly true OSWorld boundaries and mostly false CodeTrace
   boundaries. The present rule uses **cross-session fine identity**, not local
   coarse ranking, and forces exact identity when detail is absent. Same
   symptom class (over-segmentation) does not imply same mechanism.
5. **OSWorld exact fallback is not a tuned dual policy.** It is the required
   behavior of an optional field: when non-redundant detail is unavailable, the
   constructor must not invent pseudo-detail (`target`, `phase`, human group).
   Because OSWorld has no eligible detail, exact reproduction of the release is
   a validity property, not a second performance rule chosen after outcome
   signs.
6. **Literature use is appropriately modest.** van Zelst et al. (2021) and Li
   et al. (2021) are cited only for the multi-resolution / granularity problem
   statement. The plan does not claim their algorithm or import a new named
   method, matching the skill’s preference for necessary adapters over invented
   control interfaces.

What would have been post-hoc and is **not** present:

- benchmark-specific numeric cutoffs;
- OSWorld-vs-CodeTrace sign gates;
- score interpolation between resolutions;
- support buckets or local windows selected from retained labels;
- a second algorithm name or output hierarchy.

The rule remains falsifiable on CodeTrace: if fine-grain rescue merges the
wrong places, ordinary B-cubed can fail to improve or the bootstrap interval can
include zero.

### 3.4 Does absent/unseen detail truly back off and cannot change current output?

**Pass.**

The plan states three label-independent, auditable properties:

1. Without an eligible detail field, every decision, segment, motif, and mass
   value is **exactly** current.
2. With detail, every candidate boundary is also a current coarse boundary
   (candidate boundary set ⊆ current boundary set).
3. Mass is conserved and each operation belongs to exactly one contiguous
   segment.

Logical consequences of the stated rule:

- Missing optional field → only coarse model is constructed → property 1.
- Present field but unseen detailed pair → `detail_continuity = false` →
  decision equals coarse decision.
- Present field, seen detailed pair, NPMI below detail cutoff → same fallback.
- Present field, seen detailed pair, NPMI at/above cutoff → may convert a coarse
  boundary into continuity, never the reverse.

Current Rust release path (`agentpprof/src/profile.rs`) reads only the `action`
association field and builds one NPMI model. An optional second field that is
ignored when absent is therefore implementable without changing historical
defaults. The OSWorld evaluator path already feeds only unit weight, `session`,
and `action`; the plan forbids mapping redundant OSWorld fields into detail.

Implementation must keep these properties machine-checkable in raw output
(current-relative removed/added boundary counts; field-absent bit-identity on
OSWorld). That is already in the plan’s diagnostics and fixed interpretation
(`Invalid/incomplete` if fallback identity or boundary-subset fails).

### 3.5 Are existing complete populations, ordinary B-cubed, task-cluster uncertainty, baselines, isolation, and fixed interpretation sufficient?

**Pass.**

| Element | Plan commitment | Independent check |
|---|---|---|
| CodeTrace population | 2,229 disjoint reference sessions / 87,703 ops; 405 failed targets / 20,866 ops / 20,461 decisions / 2,948 stages / 251 tasks / 4 frameworks | Matches the established stage-fidelity constants and prior Step 0024/0026 populations. |
| OSWorld population | 287 sessions / 3,978 ops / 3,691 decisions / 2,042 groups / 5 session-disjoint folds | Matches the recurrence evaluator’s expected population. |
| Primary metric | Ordinary unweighted per-operation B-cubed P/R/F1 | Already the paper’s standard hard-partition metric for this RQ3 component; token-weighted / budget / reader scores correctly excluded. |
| Uncertainty | Paired task-cluster bootstrap of candidate−current B-cubed F1 over 251 tasks, 10,000 resamples | Reuses the already-used uncertainty unit; does not invent a project score. |
| Main baseline | Release label-free coarse recurrence (Step 0024) | Correct strongest current-mechanism competitor for this hypothesis. |
| Controls | `raw_action_key_change`, `phase_change`, `action_change`, always-boundary, one-session | Correctly labeled descriptive/controls; no new baseline family. |
| Isolation | Candidate sees unit weight + session + action [+ optional action_detail]; stages/human groups load after prediction | Matches current eval architecture; plan strengthens it rather than weakening it. |
| Fixed interpretation | Supported / promising / contradicted / invalid with adoption only on Supported | Predeclared, decision-relevant, and not outcome-editable. |

No additional population, custom primary metric, or extra main baseline is
required for a valid test of this hypothesis. Requests for broader workloads or
more baselines would be polish, not blockers under the skill.

### 3.6 Is the plan minimal, executable, and free of unnecessary contracts?

**Pass, with ordinary implementation detail left free.**

Minimal mechanism:

- keep the release coarse model intact;
- optionally learn a second identical NPMI + two-means + monotone cutoff model
  over `(action, action_detail)`;
- combine only by OR-of-continuity;
- keep motif naming as run-length-compressed **coarse** actions so detail does
  not create a second naming scheme.

No new threshold hyperparameter, embedding, model family, benchmark rule,
promotion gate, schema language, or algorithm product name is introduced. The
implementation surface is “one optional field + second instance of existing
recurrence computation,” which matches the skill’s ban on project-authored
experiment-control interfaces.

Executable sequence is complete enough for a competent implementer:

1. plan review (this document)
2. minimal Rust + eval extension
3. tests / build / implementation audit
4. real preflight (OSWorld fold 0 + one CodeTrace target; execution/isolation only)
5. full OSWorld five folds + all 405 CodeTrace targets once
6. raw retention under `.agentsight/experiments/rq3-multiresolution-recurrence-v1/`
7. fresh result review before adoption

Compared with the Step 0024 plan, this plan is lighter on pasted bash lines.
That is an optional clarity gap, not a missing scientific contract: the
authoritative data paths and evaluators already exist
(`docs/visexp/out/codetracebench-rq2/full/...`,
`.agentsight/experiments/codetracebench-rq2/manifests/verified.parquet`,
`script/rq3_recurrence_stack_induction_eval.py`,
`script/rq3_codetracebench_stage_fidelity_eval.py`).

### 3.7 Does it preserve thesis, four RQs, story, and the user instruction to improve the algorithm on existing trajectories?

**Pass.**

- Thesis remains exactly: **“Agent observability needs profiling, not only debugging.”**
- Four RQs remain attribution, localization, tag accuracy, and cost.
- Only the operation-stack induction mechanism and evidence it owns may change.
- Paper-level positive RQ3 hypothesis is not rewritten from this local outcome.
- `docs/agentpprof-paper/` stays read-only; active paper updates are gated on a
  Supported result and ordinary WRITE discipline.
- User instruction explicitly requested algorithm improvement on already-run
  trajectories rather than a new benchmark campaign
  (`docs/user-instruction.md`: improve the algorithm on existing trajectories).
  This plan is exactly that class of work, scoped as post-hoc mechanism
  development rather than untouched confirmation.
- Relative to Step 0026’s NO-ADMIT under the **action-only** contract: the plan
  does not smuggle another cutoff/window/support tweak. It supplies the missing
  discriminator Step 0026 required.

`docs/idea-story.md` local “no further field search” notes from the closed
action-only branch do not freeze the scientific story; they record that branch’s
closure. The fixed narrative baseline, thesis, and four RQs remain intact.

---

## 4. Paper-Value Admission Judgment

| Item | Judgment |
|---|---|
| Planned role | Supporting / decisive-for-mechanism (local constructor improvement), not a whole-RQ or thesis experiment. Explicit role label is missing in the plan template sense but recoverable from the plan’s own wording. |
| Load-bearing uncertainty | Whether pair-level observational aliasing can be broken by source-visible multi-resolution continuity without label leakage or population-specific gates. |
| Independent evidence | Yes, relative to Steps 0024–0026: new field use + dual-resolution continuity rule, not another arrangement of the same coarse score. |
| Tautology risk | Low. Improvement is not guaranteed by construction; merge-only rescue can harm B-cubed precision if wrong. |
| Positive paper decision | Authorize release replacement and bounded design/eval/paper mechanism update, still marked post-hoc on these trajectories. |
| Negative / mixed / inconclusive | Keep Step 0024 release; no thesis/RQ/story change; no further candidate inside this experiment. |
| Best alternative | Untouched new-family confirmation or a heavier sequence model would be larger campaigns. Given the user request and Step 0026 diagnosis, this is the highest decision-value **minimal** next experiment on the existing trajectories. |

Admission holds.

---

## 5. Must-Fix Items

**None.**

No scientific or executability defect was found that would invalidate a faithful
execution of the written plan.

---

## 6. Optional Observations (Non-Blocking)

These may improve clarity during implementation or result review. They are
**not** conditions of approval and must not broaden the experiment.

1. **Name the authoritative input paths explicitly** in the execution notes
   when implementing, reusing the established Step 0024 paths:
   - CodeTrace ops: `docs/visexp/out/codetracebench-rq2/full/{reference,target}-operations.jsonl`
   - Manifest: `.agentsight/experiments/codetracebench-rq2/manifests/verified.parquet`
   - OSWorld: existing recurrence evaluator default population / five folds
2. **Spell out “same-action” at detail resolution** as identity of the full
   compound signature `(action, action_detail)`, so the reused monotone
   `min(global, cross)` rule is unambiguous for pairs such as
   `(inspect,ls)→(inspect,cat)`.
3. **Clarify the plan’s “no field combination” sentence** if anyone misreads it:
   dual-resolution compound signatures are allowed; score-level blending of
   coarse and detail NPMI is not.
4. **Keep `selected_source_fields` / report assertions honest** after the
   optional field is added (current stage-fidelity code asserts
   `["action"]` only). That is ordinary eval maintenance, not a new contract.
5. **Template polish only:** label planned role as `supporting` (mechanism) and
   keep the post-hoc-development qualifier adjacent to any future paper number.
6. **Do not promote OSWorld exact-match into a second performance win.** The
   plan already treats it as fallback validity; result review should do the same.

---

## 7. Final Verdict And Authorization

### Verdict

**APPROVE**

### Authorization

**Implementation is authorized** exactly as specified in
`experiment-plan.md`, subject to the plan’s own fixed scientific contract:

- one RQ (RQ3) and one mechanism hypothesis;
- optional `action_detail` from existing source-visible `raw_action_key` only;
- OR-of-continuity / no detail-added boundaries;
- exact fallback when detail is absent or unseen;
- complete existing populations only;
- ordinary B-cubed primary metric and task-cluster uncertainty;
- no candidate-metric peeking or post-preflight rule change;
- no thesis, RQ, story, or paper-level hypothesis rewrite from this experiment;
- adoption only under the predeclared Supported rule after raw retention and a
  fresh result review.

### Prohibition (still in force)

- Do **not** broaden to a new benchmark, second candidate, score blend,
  population-specific gate, or alternative primary metric inside this experiment.
- Do **not** map OSWorld `target` / `phase` / human-group fields into
  `action_detail`.
- Do **not** treat a Supported local mechanism result as an untouched answer to
  all of RQ3 or as license to alter the four RQs or thesis.
- Do **not** edit the read-only `docs/agentpprof-paper/` submodule.

---

**End of plan review.** Implementation may proceed under the authorization above.
