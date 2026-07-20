# Independent Complete-Result Review — Experiment 001

**Reviewer model:** Grok 4.5  
**Skill followed:** complete `research-experiment-design/SKILL.md` and
`references/plan-template.md`  
**Mode:** read-only reconstruction from retained raw artifacts; no code, plan,
paper, skill, or other file edited; no git; no second experiment proposed  
**Reviewed plan:** `experiment-plan.md` (plan review APPROVE; implementation
review PASS; real preflight PASS)  
**Raw roots inspected:**
- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/`
- `.agentsight/experiments/rq3-multiresolution-recurrence-v1/full/osworld-equivalence/`
- `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/`
- `.agentsight/experiments/rq3-monotone-recurrence-rust-equivalence-v1/full/`
- code: `agentpprof/src/profile.rs`, `script/rq3_codetracebench_stage_fidelity_eval.py`,
  `script/rq3_recurrence_stack_rust_equivalence.py`

**Trust policy:** `full-run.md` and `summary.json` prose were **not** trusted.
Every primary number below was recomputed from raw JSONL / profile artifacts, or
byte-compared to retained Step 0024 baselines.

---

## Exact Scope (Hard Bound)

This result is **post-hoc mechanism-selection evidence on reused trajectories**.

It is evidence for one local constructor hypothesis inside **RQ3 — How accurate
are the tags?**:

> multi-resolution continuity (coarse OR detail) improves ordinary unweighted
> per-operation B-cubed F1 over the current coarse-only release constructor on
> the complete existing CodeTraceBench population, and exactly falls back when
> non-redundant detail is absent.

It is **not**:

- an answer to all of RQ3;
- untouched confirmation on a held-out future corpus;
- permission to change the thesis
  (**“Agent observability needs profiling, not only debugging.”**),
  the four RQs, the positive paper-level RQ3 hypothesis, contribution structure,
  or original AgentProf story;
- a license to rewrite boundary-F1 decline into a new primary metric.

---

## Verdicts

| Judgment | Value |
|---|---|
| **Validity** | **PASS** |
| **Completeness** | **COMPLETE** |
| **Fixed scientific verdict** | **SUPPORTED** |
| **Release decision** | **ADOPT** |
| run status (skill) | valid |
| tested hypothesis (skill) | supported |
| research value | supporting (mechanism / constructor selection) |
| paper impact | mechanism boundary only; additional RQ3 tag-accuracy evidence for the induction component |
| next paper decision | authorize release replacement of the recurrence constructor and bounded WRITE of mechanism-owned design/impl/eval/algorithm-history/active-paper text only; no thesis/RQ/story rewrite |

---

## 1. Population Counts and Reference–Target Disjointness

### CodeTraceBench (from raw inputs and assignments)

| Quantity | Independent count | Plan expectation | Match |
|---|---:|---:|---|
| Reference operations | 87,703 | 87,703 | yes |
| Reference sessions | 2,229 | 2,229 | yes |
| Target operations | 20,866 | 20,866 | yes |
| Target sessions | 405 | 405 | yes |
| Adjacent decisions | 20,461 | 20,461 (`ops − sessions`) | yes |
| Official stages | 2,948 | 2,948 | yes |
| Distinct tasks | 251 | 251 | yes |
| Frameworks | 4 | 4 | yes |

Framework session counts (from assignments): OpenHands 213, Terminus2 93,
mini-SWE-agent 71, SWE-agent 28 (sum 405).

**Reference ∩ target sessions = ∅** (intersection size 0).

Rust input field isolation (both reference and target JSONL):

- keys exactly `{session, action, action_detail}`;
- unit weight `value == 1` on every row;
- zero empty `action_detail` values.

Pair and assignment coverage:

- 20,461 unique pair keys; 20,866 unique `(session, step_id)` assignments;
- every operation assigned once; recurrence groups contiguous within sessions
  (0 non-contiguous recurrence groups);
- profile stack mass = 20,866 (full mass conservation).

### OSWorld-Human (from five-fold inputs + equivalence summary)

| Quantity | Independent count | Plan expectation | Match |
|---|---:|---:|---|
| Sessions (union of test folds) | 287 | 287 | yes |
| Operations | 3,978 | 3,978 | yes |
| Adjacent decisions | 3,691 | 3,691 | yes |
| Official human groups (source count) | 2,042 | 2,042 | yes |
| Folds | 5 | 5 | yes |

All fold reference/target session sets are disjoint. Inputs contain only
`session` and `action` (no `action_detail`).

---

## 2. Ordinary Unweighted Per-Operation B-cubed (Primary)

Recomputed from
`.agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl`
using the same ordinary B-cubed definition as the scorer (`bcubed` over
per-operation predicted vs official group ids).

| Method | Precision | Recall | F1 | Predicted groups |
|---|---:|---:|---:|---:|
| **Multi-resolution recurrence (candidate)** | 0.782025634215 | 0.575028961707 | **0.662740305102** | 6,018 |
| **Current coarse recurrence (Step 0024 baseline)** | 0.828579403968 | 0.533630051887 | **0.649173103932** | 6,897 |
| Phase-change control | 0.685563500400 | 0.626029583709 | 0.654445403779 | 5,980 |
| Raw-action-key change | 0.891295919294 | 0.388437301454 | 0.541069929379 | 12,231 |
| Action-change control | 0.947622645441 | 0.315368254275 | 0.473241888713 | 12,941 |
| Always-boundary | 1.000000000000 | 0.141282469088 | 0.247585453935 | 20,866 |
| One-session block | 0.173562770775 | 1.000000000000 | 0.295787792690 | 405 |

**Candidate − current B-cubed F1 = +0.013567201170** (higher; plan Supported
conjunct 1 holds).

Precision falls and recall rises, with fewer predicted groups (6,897 → 6,018),
closer to 2,948 official stages. This is a coarser partition relative to the
current release, not a precision-only collapse.

---

## 3. Exact Adjacent-Boundary Confusion (Diagnostic)

Recomputed from raw `pair-decisions.jsonl` against `official_boundary`.

| Method | TP | FP | TN | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Candidate recurrence** | 1,083 | 4,530 | 13,388 | 1,460 | 0.192945 | 0.425875 | **0.265571** |
| **Current recurrence** | 1,297 | 5,195 | 12,723 | 1,246 | 0.199784 | 0.510028 | **0.287106** |
| Raw-action-key change | 1,848 | 9,978 | 7,940 | 695 | 0.156266 | 0.726701 | 0.257220 |
| Phase-change | 915 | 4,660 | 13,258 | 1,628 | 0.164126 | 0.359811 | 0.225425 |
| Action-change | 2,017 | 10,519 | 7,399 | 526 | 0.160897 | 0.793158 | 0.267524 |

**Boundary-F1 delta vs current = −0.021534** (decline).

Candidate boundary F1 remains above raw-action-key change and phase-change
controls. Boundary F1 is **not** the registered primary metric (§10).

---

## 4. Candidate−Current B-cubed Delta by Framework

Independent per-framework recomputation on the same assignments:

| Framework | Ops | Sessions | Current F1 | Candidate F1 | Delta |
|---|---:|---:|---:|---:|---:|
| OpenHands | 10,030 | 213 | 0.661592797442 | 0.676295270553 | **+0.014702** |
| Terminus2 | 7,201 | 93 | 0.593875886482 | 0.605471300402 | **+0.011595** |
| mini-SWE-agent | 2,175 | 71 | 0.683439028787 | 0.691523316904 | **+0.008084** |
| SWE-agent | 1,460 | 28 | 0.707954932775 | 0.708892505808 | **+0.000938** |

**All four framework deltas are positive.** No framework declines. SWE-agent’s
gain is small (only 5 of 879 rescues land there; 7.0% of ops), but it is not a
sign flip.

---

## 5. Paired Task-Cluster Bootstrap (Candidate − Current)

Raw file:
`task-bootstrap-deltas.jsonl` (10,000 rows `{resample, delta}`).

| Item | Independent reconstruction |
|---|---|
| Population / unit | 251 `task_name` clusters |
| Seed | `20260719` (`BOOTSTRAP_SEED`) |
| Draws | 10,000 |
| Comparison | `F1(recurrence) − F1(current_recurrence)` via session-level B-cubed sufficient statistics, tasks resampled with `random.Random(seed).choices` |
| Mean delta | **+0.013506683056** |
| Median delta | **+0.013526534510** |
| 95% CI (linear percentile 0.025 / 0.975) | **[+0.008712278810, +0.018042505435]** |
| Positive fraction | **1.000** (all 10,000 draws > 0) |
| Min / max draw | +0.002012 / +0.022012 |

**Verification that the bootstrap is candidate−current:** exact replay of the
scorer’s `task_cluster_bootstrap` on retained assignments regenerates all
10,000 raw deltas with max abs difference 0.0. CI is wholly positive (plan
Supported conjunct 2 holds).

---

## 6. Detail Rescues, Boundary Subset, Seen/Unseen, Coverage, Mass

From profile
`profile.operation_stack_induction` and its 20,461 `boundary_decisions`,
cross-checked against pair-level `current_recurrence` vs `recurrence`:

| Property | Independent value |
|---|---:|
| Detail rescues (`detail_rescued_coarse_boundary == true`) | **879** |
| Detail-added boundaries (`coarse_boundary == false ∧ boundary == true`) | **0** |
| Seen detail target transitions | **18,082** |
| Unseen detail target transitions | **2,379** |
| Seen + unseen | 20,461 (= all pairs) |
| Seen coverage | 18,082 / 20,461 ≈ 88.37% |
| Coarse boundaries | 6,492 |
| Final candidate boundaries | 5,613 |
| Coarse − final | 879 (= rescues) |
| Boundary-subset violations | **0** |
| Predicted groups | 6,018 |
| Group reduction vs current | 879 (6,897 − 6,018) |
| Stack mass | 20,866 |
| Unique coarse motifs | 534 (all `action=…`; no detail leakage into motif names) |

Rescue composition against official boundaries (diagnostic, not primary):

- 665 rescues remove false current boundaries (FP ↓);
- 214 rescues remove true official boundaries (TP ↓ / FN ↑);
- matches TP −214 and FP −665 between current and candidate confusion matrices.

Detail model (profile `detail_recurrence`):

- signature: ordered `(action, action_detail)` pair;
- reference transitions: 85,474;
- global cutoff 0.385306; signature-change applied cutoff
  `min(global, signature-change)` = 0.270975;
- `rescued_coarse_boundaries = 879`, `added_coarse_boundaries = 0`.

Coarse arm is unchanged relative to Step 0024: identical
`global_cutoff = 0.1229905828183635`,
`cross_action_applied_cutoff = -0.05573920763459794`, and
`reference_transitions = 85474`.

---

## 7. OSWorld Five Folds Through the Changed Rust Path

**Evidence route (required by implementation review MF-1):**  
`script/rq3_recurrence_stack_rust_equivalence.py` with `--induce-operation-stack`
on all five detail-free folds. This is **not** the Python-only score path in
`rq3_recurrence_stack_induction_eval.py` (which would reproduce release scores
without executing the changed constructor).

### Per-fold independent audit

| Fold | Train sess / ops | Test sess / ops | Decisions | Segments | Stack mass | Global cutoff | Cross applied | Detail model | Selected fields |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 242 / 3,457 | 45 / 521 | 476 | 267 | 521 | 0.231168401075 | 0.231168401075 | absent | `["action"]` |
| 1 | 232 / 3,341 | 55 / 637 | 582 | 489 | 637 | 0.321453284049 | 0.283252823447 | absent | `["action"]` |
| 2 | 227 / 2,648 | 60 / 1,330 | 1,270 | 969 | 1,330 | 0.337658816070 | 0.297296282352 | absent | `["action"]` |
| 3 | 225 / 3,344 | 62 / 634 | 572 | 370 | 634 | 0.237264645114 | 0.237264645114 | absent | `["action"]` |
| 4 | 222 / 3,122 | 65 / 856 | 791 | 561 | 856 | 0.305632824173 | 0.267110289396 | absent | `["action"]` |
| **Σ** | — | **287 / 3,978** | **3,691** | **2,656** | **3,978** | — | — | — | — |

Additional per-fold checks:

- inputs: only `{session, action}`; unit weight; no `action_detail`;
- reference/target session disjointness holds on every fold;
- no detail decision fields serialized (`left_action_detail`, `detail_*`,
  `coarse_boundary` all absent);
- motifs remain coarse `action=…`;
- `removed_current_boundaries = 0` and `added_current_boundaries = 0` on every
  fold report;
- every fold command includes `--induce-operation-stack` (changed Rust path).

### Exact fallback to Step 0024

Byte-identical profile SHA-256 vs retained
`.agentsight/experiments/rq3-monotone-recurrence-rust-equivalence-v1/full/fold-*/profile.json`
for **all five folds**:

| Fold | SHA-256 |
|---:|---|
| 0 | `6d63f471dd3da83794091dc82fc2ad705692435e2dea066b3744da16f30d76a2` |
| 1 | `88e9a9dfd0c27638…` (full digest equal to Step 0024) |
| 2 | `48def4554ca98014…` (equal) |
| 3 | `14436c71628ee418…` (equal) |
| 4 | `ae1d97ca4300f5c4…` (equal) |

Deep equality also holds for decisions, NPMI, applied cutoffs (within 1e-12),
segments/motifs, and stack mass. Inputs are byte-identical to the Step 0024
equivalence inputs. Preflight fold-0 profile SHA matches both full-run fold-0
and Step 0024 fold-0.

Because decisions are exactly the Step 0024 OSWorld decisions, the registered
Step 0024 OSWorld metrics are preserved as a **fallback validity identity**,
not a second performance win:

- ordinary B-cubed F1 = **0.786169543748** (reported 0.786170);
- exact boundary F1 = **0.679922405432** (reported 0.679922).

**Plan Supported conjunct 3 (exact OSWorld fallback) holds via measured
Rust-path identity.**

---

## 8. Scorer Isolation and Step 0024 Baseline Reproduction

### Scorer isolation

Code path in `rq3_codetracebench_stage_fidelity_eval.py`:

1. `minimal_rows` emits only `{session, action, action_detail}` with unit weight;
2. `run_recurrence` materializes the profile / predictions;
3. only then `load_stages_after_prediction` opens the verified manifest.

Independent input audit: no stage / phase / task / framework / label fields in
Rust JSONL. Official stages appear only on post-prediction assignment rows
(`official_stage`). Pair rows carry `official_boundary` only in the scorer
artifact, not in the Rust induction input.

`action_detail` is the pre-existing source-visible `raw_action_key` (plan and
implementation review provenance); it is not an official stage identity.

### Step 0024 baseline reproduction

- Candidate `current_recurrence` assignment ids match retained Step 0024
  `operation-assignments.jsonl` on all **20,866** operations (0 mismatches).
- Recomputed B-cubed and boundary metrics on those groups are bit-identical to
  Step 0024 summary recurrence metrics:
  - partition F1 **0.6491731039323719**
  - boundary F1 **0.28710570005534036**
- Coarse NPMI cutoffs in the candidate profile equal Step 0024’s coarse model
  exactly (detail is a second model only).

---

## 9. Framework Heterogeneity vs Predeclared Supported Branch

Plan Supported requires: higher complete B-cubed **and** wholly positive
task-cluster CI **and** exact OSWorld fallback **and** validity.

Plan Promising adds the alternative: higher point estimate with CI including
zero, **or** pooled gain with *materially heterogeneous* framework effects.

Independent findings:

- complete B-cubed higher (+0.013567);
- CI wholly positive with positive fraction 1.0;
- all four framework deltas **positive** (no sign conflict);
- OSWorld exact;
- validity properties hold.

SWE-agent’s near-flat +0.0009 is magnitude heterogeneity on the smallest
framework (28 sessions), not a contradictory framework effect. Session-level
wins/losses (154 improve / 101 worsen / 150 tie) are expected under merge-only
rescue and are **not** the registered uncertainty unit; the registered
task-cluster bootstrap remains wholly positive.

**Conclusion:** no material framework heterogeneity prevents the predeclared
**Supported** branch.

---

## 10. Boundary-F1 Decline Is a Diagnostic Tradeoff

The registered primary is ordinary per-operation B-cubed against official
partitions. Boundary F1 is listed in the plan as a **mechanism diagnostic**.

Observed tradeoff is mechanistically coherent with merge-only detail rescue:

- detail may only remove coarse boundaries (879 removals, 0 additions);
- of those removals, 665 were false boundaries and 214 were true boundaries;
- boundary recall therefore falls (0.510 → 0.426) while partition recall rises
  (0.534 → 0.575) and B-cubed F1 rises;
- predicted group count moves from 6,897 toward 2,948 official stages.

This is the expected partition-granularity tradeoff of positive fine-grain
continuity evidence. It does **not** redefine the hypothesis, does **not**
replace B-cubed as primary, and is **not** evidence that the scientific
contract was changed post hoc.

---

## Validity Properties Checklist

| Property | Result |
|---|---|
| Complete CodeTrace population scored | PASS |
| Reference–target session disjointness | PASS |
| Rust inputs only unit weight + session + action + action_detail | PASS |
| Official stages loaded after prediction | PASS |
| Every pair scored once / every op assigned once | PASS |
| Mass conservation (stack mass = ops) | PASS |
| Candidate boundary ⊆ coarse/current boundary | PASS (0 additions) |
| Detail-free OSWorld exact fallback on changed Rust path | PASS (byte-identical 5/5) |
| Step 0024 current baseline reproduced | PASS |
| Bootstrap unit/seed/draws/comparison as planned | PASS |
| No algorithm/threshold change indicated between preflight and full | PASS (preflight fold-0 SHA = full fold-0 = Step 0024) |
| Scorer circularity | PASS (labels post-prediction only) |

---

## Skill-Formatted Result Judgment

```text
run status: valid
tested hypothesis: supported
research value: supporting
paper impact: mechanism or workload boundary
next paper decision: ADOPT the multi-resolution recurrence constructor as the
  release mechanism; allow only mechanism-owned design/impl/eval/algorithm-history
  and active-paper text updates; preserve thesis, four RQs, and story; mark
  evidence as post-hoc on reused trajectories
```

---

## Must-Fix

**None.**

No validity failure, incompleteness, metric misregistration, baseline
non-engagement, OSWorld route vacuity, or Supported-rule miss was found after
independent raw reconstruction.

---

## Optional Observations (Non-Blocking)

1. **SWE-agent near-flat gain.** Only +0.0009 F1 with 5 rescues; still positive.
   Fine for Supported under the plan, but any paper number should not claim
   uniform large gains across frameworks without the table above.
2. **Session-level mixed wins/losses.** 101 sessions worsen under B-cubed while
   154 improve; the registered task-cluster bootstrap remains wholly positive.
   Do not silently upgrade session majority into the uncertainty claim.
3. **Boundary-F1 decline must stay secondary** in any WRITE text. Present it as
   the merge-only granularity tradeoff, never as a failed primary.
4. **Post-hoc scope must remain adjacent** to any paper claim: reused
   CodeTrace/OSWorld trajectories and field selection after the Step 0026
   aliasing audit; not a fresh untouched confirmation corpus.
5. **OSWorld numbers are fallback identity**, not a second performance result.
6. **Implementation-review O-6** (diff-level provenance / formatting) was outside
   this result reconstruction. Mechanism and metric validity do not depend on
   it; close it as ordinary release hygiene if desired before landing the code.

---

## Fixed Interpretation Mapping

| Plan branch | Condition | This run |
|---|---|---|
| **Supported** | higher complete B-cubed **and** wholly positive task-cluster CI **and** exact OSWorld fallback **and** validity | **MET** |
| Promising | higher but CI includes 0, or material framework heterogeneity | not applicable |
| Contradicted | complete B-cubed not higher | not applicable |
| Invalid/incomplete | isolation / fallback / subset / coverage / execution failure | not applicable |

Therefore:

- **Scientific verdict: SUPPORTED**
- **Release decision: ADOPT** the multi-resolution constructor as the release
  operation-stack induction mechanism.

Adoption authorizes only mechanism-owned updates. It does **not** authorize
thesis, RQ, story, or paper-level hypothesis change, and it does **not** answer
all of RQ3.

---

## Completeness

Full planned matrix completed once after preflight with no post-preflight
algorithm change:

- all 405 CodeTrace targets;
- all 5 OSWorld Rust-equivalence folds;
- retained inputs, commands, stdout/stderr, profiles, pair decisions,
  assignments, summary, report, and 10,000 bootstrap deltas.

**Completeness: COMPLETE.**

---

**End of independent complete-result review.**
