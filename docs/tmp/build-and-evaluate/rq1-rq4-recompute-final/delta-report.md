# RQ1–RQ4 Recompute at Final HEAD — Delta Report

Date: 2026-07-25

Old recompute: `docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/`

Final recompute: `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/`

Contract: release build from the current workspace revision; cutoff
`1784708569241`; the same six roots in the same order; real HOME; the same
RQ1–RQ4 derivation scripts and plotting steps. The copied RQ2 script received
only new input-hash pins, as in the earlier recompute, and the copied headline
script received only the final input path. See `commands.log`. No Git command
was run, no frozen directory was modified, and `docs/paper/*` was not edited.

## HEADLINE CHANGES DETECTED

The paper restructuring must use the final values below. Relative to the
20260725 recompute, final HEAD changes these requested headline quantities:

- worktree-attributed sessions/actions: **550/175,619 → 551/176,288**;
- observed artifacts: **5,792 → 5,746**;
- confirmed mutations: **13,905 → 13,906**;
- reuse range: **89.29–97.02% → 89.29–97.11%**;
- RQ4 totals, after correcting the old arithmetic: **120 components /
  110 boundaries → 121 / 111**; only `academic-writing-skills` changes,
  **16/15 → 17/16**.

Admitted sessions, total Tool actions, Spearman rho, persistence qualification,
F5 validation coverage, and the requested eunomia.dev RQ3 quantities are
unchanged.

The final rerun uses the requested live-HOME contract, not a frozen HOME.
Candidate/parsed files drifted between recomputes (notably agentsight
1387/1383 → 1401/1397, AgentSkill paper 38/38 → 62/62, and writing skills
26/25 → 27/26), although admitted sessions and total Tool actions are
unchanged. The cutoff excludes post-cutoff actions, but this result is an exact
final-HEAD rerun rather than a controlled single-fix ablation. The values in
the **Final HEAD** column are therefore the authoritative revision values.

## RQ1 headline delta

| Metric | 20260725 recompute | Final HEAD | Delta | Status |
|---|---:|---:|---:|---|
| Admitted native-root sessions | 551 | 551 | 0 | **UNCHANGED** |
| Worktree-attributed sessions | 550 | 551 | +1 | **CHANGED** |
| Total Tool actions | 181,303 | 181,303 | 0 | **UNCHANGED** |
| Worktree-attributed Tool actions | 175,619 | 176,288 | +669 (+0.38%) | **CHANGED** |
| Observed artifact identities | 5,792 | 5,746 | −46 (−0.79%) | **CHANGED** |
| Confirmed mutation rows | 13,905 | 13,906 | +1 | **CHANGED** |
| Later-reuse range over six projects | 89.29–97.02% | 89.29–97.11% | upper endpoint +0.09 pp | **CHANGED** |
| Spearman rho, reuse vs attributed action volume | 0.2000 | 0.2000 | 0 | **UNCHANGED** |
| Longitudinal-qualified projects | 6/6 | 6/6 | 0 | **UNCHANGED** |
| Persistence-qualified projects (≥1 eligible confirmed create) | 6/6 | 6/6 | 0 | **UNCHANGED** |
| Validation-qualified projects in RQ1 summary | 6/6 | 6/6 | 0 | **UNCHANGED** |

The artifact and mutation totals are independently checked by the 5,747 and
13,907 CSV line counts (one header plus 5,746/13,906 data rows). The per-project
changes localize the pooled deltas:

| Project | Attributed sessions/actions, old → final | Artifacts, old → final | Mutations, old → final |
|---|---:|---:|---:|
| agentsight | 301/93,557 → 301/94,031 | 3,287 → 3,267 | 6,587 → 6,588 |
| ActPlane | 139/65,333 → 139/65,334 | 1,834 → 1,809 | 5,849 → 5,849 |
| bpf-developer-tutorial | 35/1,661 → 35/1,661 | 170 → 170 | 283 → 283 |
| eunomia.dev | 51/13,393 → 51/13,393 | 360 → 360 | 739 → 739 |
| agentskill-observability-paper | 8/990 → 8/990 | 25 → 24 | 196 → 196 |
| academic-writing-skills | 16/685 → 17/879 | 116 → 116 | 251 → 251 |

Reuse fractions, which define the range and rho inputs:

| Project | 20260725 | Final HEAD | Status |
|---|---:|---:|---|
| agentsight | 5,570/6,111 = 91.15% | 5,573/6,112 = 91.18% | **CHANGED** |
| ActPlane | 5,437/5,604 = 97.02% | 5,442/5,604 = 97.11% | **CHANGED** |
| bpf-developer-tutorial | 257/282 = 91.13% | 257/282 = 91.13% | **UNCHANGED** |
| eunomia.dev | 650/694 = 93.66% | 650/694 = 93.66% | **UNCHANGED** |
| agentskill-observability-paper | 175/196 = 89.29% | 175/196 = 89.29% | **UNCHANGED** |
| academic-writing-skills | 234/247 = 94.74% | 234/247 = 94.74% | **UNCHANGED** |

The minimum remains AgentSkill paper (89.29%) and the maximum remains ActPlane
(now 97.11%). The rank ordering of the six project reuse fractions and action
volumes remains unchanged, so Spearman rho remains exactly 0.2000.

## RQ2 and inconsistency (a): F5 validation coverage is 6/6

**Correct final value: 6/6, UNCHANGED from the data-derived 20260725 value.**

The authoritative evidence is `rq2/raw/rq2-coverage.csv`: all six rows have a
positive `recognized_success` count and `qualified_with_success=True`.

| Project | Recognized success, 20260725 → final | Final qualified | Status |
|---|---:|---:|---|
| agentsight | 3,230 → 3,288 | true | **CHANGED count; coverage unchanged** |
| ActPlane | 2,576 → 2,576 | true | **UNCHANGED** |
| bpf-developer-tutorial | 22 → 22 | true | **UNCHANGED** |
| eunomia.dev | 52 → 52 | true | **UNCHANGED** |
| agentskill-observability-paper | 1 → 1 | true | **UNCHANGED** |
| academic-writing-skills | 9 → 9 | true | **UNCHANGED** |

The contradictory “3/6” sentence in `rq2/result.md` and the same figure
annotation are canned literals in `scripts/plot_rq2.py`; they are not computed
from the coverage table. The script computes all six rows and explicitly
prints `recognized-success coverage = 6/6` when the value differs from the
frozen pre-hardening expectation of 3/6. Therefore:

- **6/6** is the correct F5 coverage for both the 20260725 recompute and final
  HEAD;
- **3/6** describes the older frozen pre-hardening run only and must not be
  used for the final revision.

Supporting RQ2 per-project attempt counts changed only for agentsight:
`3230/372/202 → 3288/373/202` (success/fail/observed); ActPlane remains
`2576/277/159`, bpf `22/0/0`, eunomia.dev `52/3/95`, AgentSkill paper
`1/3/0`, and writing skills `9/0/0`.

## RQ3 headline delta

| Metric | 20260725 recompute | Final HEAD | Delta | Status |
|---|---:|---:|---:|---|
| Mutation episodes, pooled | 13,859 | 13,860 | +1 | **CHANGED** |
| eunomia.dev mutated/all artifacts | 128/360 | 128/360 | 0 | **UNCHANGED** |
| eunomia.dev repeat episodes / total episodes | 610/738 | 610/738 | 0 | **UNCHANGED** |
| eunomia.dev repeat fraction | 82.6558% (82.7%) | 82.6558% (82.7%) | 0 | **UNCHANGED** |
| eunomia.dev top-10% episode share | 71.4% | 71.4% | 0 | **UNCHANGED** |
| eunomia.dev cross-session repeat episodes | 29 | 29 | 0 | **UNCHANGED** |
| eunomia.dev maximum episode load | 165 | 165 | 0 | **UNCHANGED** |
| eunomia.dev `unknown_create_status` births | 0 | 0 | 0 | **UNCHANGED** |
| `unknown_create_status` births, pooled | 0 | 0 | 0 | **UNCHANGED** |
| `unknown_rename_source` births, pooled | 1 | 1 | 0 | **UNCHANGED** |
| Qualified episode curves | 6/6 | 6/6 | 0 | **UNCHANGED** |

Thus the requested eunomia.dev paper values remain **82.7% repeat fraction**
and **0 unknown-create births**. The pooled episode count increases by one
because the final RQ1 extraction adds one agentsight confirmed mutation.

## RQ4 and inconsistency (b): exact components and boundaries

| Project | 20260725 components/boundaries | Final HEAD components/boundaries | Status |
|---|---:|---:|---|
| agentsight | 31/28 | 31/28 | **UNCHANGED** |
| ActPlane | 24/22 | 24/22 | **UNCHANGED** |
| bpf-developer-tutorial | 29/28 | 29/28 | **UNCHANGED** |
| eunomia.dev | 18/16 | 18/16 | **UNCHANGED** |
| agentskill-observability-paper | 2/1 | 2/1 | **UNCHANGED** |
| academic-writing-skills | 16/15 | 17/16 | **CHANGED** |
| **Total** | **120/110** | **121/111** | **CHANGED (+1/+1)** |

**Correct final value: 121 components and 111 boundaries.**

Evidence:

1. The final generated per-project table sums to 121/111.
2. `rq4-components.csv` has 122 lines and `rq4-boundaries.csv` has 112 lines,
   i.e., 121 and 111 data rows after removing one header.
3. The same checks on the 20260725 raw files give 121 and 111 lines,
   i.e., **120 components and 110 boundaries**. Its per-project result table
   also sums to 120/110.

The paper’s prior **121 components / 108 boundaries** statement and the same
headline in the 20260725 delta report are unsupported by both generations of
raw CSVs. They combine neither the old per-project sum (120/110) nor the final
sum (121/111). For the revision now being restructured, use **121/111** and
the final per-project breakdown above.

The 20-boundary gate remains **3/6 projects, UNCHANGED**: agentsight 28,
ActPlane 22, and bpf-developer-tutorial 28 meet it; eunomia.dev 16,
AgentSkill paper 1, and writing skills 16 do not. The four-project estimator
gate therefore remains stopped.

## Bottom line

Final HEAD does change paper-facing counts. The final revision should use:

- 551 admitted sessions, 181,303 total actions, and **551 attributed sessions /
  176,288 attributed actions**;
- **5,746 artifacts** and **13,906 confirmed mutations**;
- **89.29–97.11%** reuse and Spearman rho **0.2000**;
- persistence **6/6** and F5 validation coverage **6/6**;
- eunomia.dev repeat fraction **82.7%** and unknown-create births **0**;
- RQ4 **121 components / 111 boundaries**, with the per-project values above.

All generated raw tables, figures, result summaries, copied scripts, and this
audit are contained under `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/`.
