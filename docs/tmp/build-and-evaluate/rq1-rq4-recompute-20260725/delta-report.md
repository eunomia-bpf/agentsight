# RQ1–RQ4 Recompute at HEAD — Delta Report

Date: 2026-07-25
Frozen baseline: `docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/`
(extraction at pre-`69afb4866` revision, cutoff 1784708569241).
Recompute: HEAD (`c47532d38`, includes the `69afb4866` projection hardening),
**same cutoff, same six roots, same real-HOME inclusion contract**
(see `commands.log` here; the frozen contract is recorded in the frozen
`commands.log` files). No frozen artifact was modified; all outputs are under
`docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/`.

The three hardening fixes that drive the deltas (code locations in
`../rq7-error-taxonomy-20260725/taxonomy.md`):

- **FIX-A session join:** `candidate_cwd_matches` fallback
  (`agentvis/src/repository.rs:1002`) — Claude sessions under project dirs whose
  name does not match `encoded_claude_root` (dotted roots like `eunomia.dev`,
  parent-dir sessions) are no longer dropped at the candidate filter.
- **FIX-B fail-drop:** failed tool calls keep their actions
  (`agentvis/src/repository.rs`, `if tool.status == "fail"` branch removed);
  lifecycle/mutation admission still requires confirmed effects.
- **FIX-C path extraction:** sed operand extraction rewritten
  (`agent-session/src/parser.rs:1567`); dedup and native-root identity
  (`deduplicate_native_tool_calls`, per-root `session_ordinal`) collapse
  subagent transcripts and continuation rollouts into one identity.

Corpus drift caveat: the real HOME is live. Candidate session files moved
slightly between the runs (agentsight 1444→1387, bpf 68→61, academic 21→26,
agentskill 36→38, ActPlane 603→604). The cutoff excludes all post-freeze
activity, and attributed action totals are stable (−0.13%), so the deltas
below are dominated by the fixes, not corpus drift. eunomia.dev's candidate
jump (49→148) is the FIX-A effect: the frozen run's Claude candidate filter
matched nothing under `-home-yunwei37-workspace-eunomia-dev`.

## RQ1 headline numbers (evaluation.md lines 55–60)

| Metric | Frozen | HEAD | Driver |
|---|---:|---:|---|
| Admitted native sessions | 2,049 | 551 | native-root identity: subagent transcripts + continuation rollouts deduped into roots (e.g. agentsight 1,363 files → 301 roots). Semantic change, not data loss |
| Tool actions | 206,249 | 181,303 | `deduplicate_native_tool_calls` removes duplicate observations of one call across transcript copies (agentsight source events 1,450,267 → 856,659) |
| Worktree-attributed sessions / actions | 1,825 / 175,850 | 550 / 175,619 | actions essentially unchanged (−0.13%): dedup removed only redundant observations |
| Observed artifact identities | 7,154 | 5,792 | identity dedup + confirmed-only lifecycle admission; unknown-create births 790 → 0, unknown-rename 13 → 1 |
| Confirmed mutation rows | 13,152 | 13,905 (+5.7%) | FIX-A (+569 eunomia.dev) + FIX-B/C extraction fixes (+184 net elsewhere) |
| Reuse observed (eligible mutations) | 89.80–97.26% | 89.29–97.02% | range shifts ≤0.9pp per project; eunomia.dev 89.81% → 93.66% |
| Spearman rho (reuse vs action volume, 6 cases) | 0.0857 | 0.2000 | eunomia.dev moves from bottom-left to mid-pack (157 → 694 eligible) |
| Longitudinal-qualified | 6/6 | 6/6 | unchanged |
| Persistence-qualified (≥1 eligible confirmed create) | 3/6 | 6/6 | confirmed-create births now visible in every project (bpf 0→18, agentskill 0→18, academic 0→1, eunomia 10→30, agentsight 983→1043, ActPlane 50→245) — FIX-B/C |
| Validation-qualified (recognized success) | 3/6 | 6/6 | recognized `effect=test,status=ok` events now surface in bpf (22), academic (9), agentskill (1) — parser/attribution hardening |

Per-project confirmed mutations: agentsight 6,482→6,587 · ActPlane 5,770→5,849 ·
bpf 283→283 · **eunomia.dev 170→739 (+334.7%)** · agentskill 196→196 ·
academic 251→251.

**Does eunomia.dev's recovered activity change pooled stats?** Yes. Its
mutations rise 170→739 (+569 = 76% of the pooled +753 increase); attributed
actions 10,193→13,393 (+31%); reuse-eligible 157→694; and its repeat-observed
share rises 71.8%→82.7% (RQ3), ending its outlier status — pooled rho
strengthens 0.0857→0.2000 largely because eunomia.dev no longer sits at the
bottom-left corner.

## RQ2 (evaluation.md line 22)

| Metric | Frozen | HEAD |
|---|---:|---:|
| Recognized-success coverage gate | **3/6 — cross-case gate stopped** | **6/6 — gate condition now passes** |
| Success/fail/observed (agentsight) | 2065/331/110 | 3230/372/202 |
| Success/fail/observed (ActPlane) | 1493/201/77 | 2576/277/159 |
| bpf / academic / agentskill successes | 0 / 0 / 0 | 22 / 9 / 1 |
| eunomia.dev successes | 6 | 52 |

The frozen `plot_rq2.py` hard-fails on any coverage ≠ 3
("frozen 3/6 recognized-success coverage changed"); the recompute copy reports
instead (`scripts/plot_rq2.py`). Note the script's canned result.md header
still says "3/6" — a hardcoded string; the coverage table is the authoritative
output. Driver: the hardened adapters now attribute recognized test successes
to worktrees in all six projects. Consequence: the RQ2 "coverage-only, F5
complete for 3/6" caveat in evaluation.md no longer holds — F5 evidence is
complete for 6/6 source-covered projects, and the cross-case stop rationale
needs re-review (this report does not rerun the stop decision itself).

## RQ3 (evaluation.md line 23, F8a/F8b)

| Metric | Frozen | HEAD |
|---|---:|---:|
| Mutation episodes | 13,150 | 13,859 |
| eunomia.dev mutated artifacts | 48/362 | 128/360 |
| eunomia.dev repeat fraction / top-10% share | 71.8% / 41.9% | 82.7% / 71.4% |
| eunomia.dev cross-session repeat episodes | 1 | 29 |
| eunomia.dev max episode load | 20 | 165 |
| `unknown_create_status` births (pooled) | 790 | 0 |
| `unknown_rename_source` births (pooled) | 13 | 1 |
| Qualified episode curves (≥20 episodes, ≥10 mutated) | 6/6 | 6/6 |

The F8 "return" evidence: frozen eunomia.dev had a single cross-session repeat
episode (return-gap statistics effectively N/A — the "one case remains N/A" in
evaluation.md); at HEAD it has 29 cross-session repeat episodes over the same
observation span, so all six cases now carry return evidence. Driver: FIX-A
recovered the Claude sessions that actually revisited earlier artifacts.

## RQ4 (evaluation.md line 24, F7)

| Metric | Frozen | HEAD |
|---|---:|---:|
| Components (pooled) | 120 | 121 |
| Boundaries (pooled) | 108 | 108 |
| Projects meeting the 20-boundary gate | 3 (agentsight 29, ActPlane 22, bpf 31) | 3 (agentsight 28, ActPlane 22, bpf 28) |
| Four-project estimator gate | **stopped** | **still stopped** |
| eunomia.dev components/boundaries | 13/11 | 18/16 |
| bpf components/boundaries | 34/31 | 29/28 (session dedup) |

**RQ4 gate status does NOT change**: with corrected native-root/subagent
identity, still only three projects meet the 20-boundary gate, so the
four-project estimator stop stands and continuity remains
coverage/within-case evidence. eunomia.dev gains 5 components (recovered
sessions) but stays below the gate. The evaluation.md action item "recompute
with corrected native root/subagent identity before estimating continuity" is
now satisfied by this recompute — the estimator can be unblocked only by data
(more boundaries), not by the identity fix.

## Recompute notes for reviewers

- `plot_rq4.py`'s Python identity replay encoded the pre-fix semantics
  ("status does not suppress lifecycle"). HEAD `rq1.rs` admits confirmed
  effects only (`if event.status != "ok" { continue }`), and failed events now
  retain actions. The recompute copy (`scripts/plot_rq4.py`) mirrors the HEAD
  gate; on frozen data this is a no-op (failed events had no actions then).
  The replay reconciles all 5,792/5,792 artifact births and 13,905/13,905
  confirmed mutation identities with zero unresolved non-scope identities; the
  synthetic test matrix was extended with a failed-create case.
- `plot_rq2.py` input hash pins were updated to the HEAD extraction hashes in
  the recompute copy; analysis logic unchanged.
- `plot_rq3.py` needed no changes.
- Figures regenerated: `rq1-figures/`, `rq2/figures/`, `rq3/figures/`,
  `rq4/figures/` (paper figures under `docs/paper/figures/` untouched).

## Bottom line

The hardening leaves the headline *activity volume* (attributed actions)
stable but substantially rewrites session/artifact identity accounting
(sessions 2,049→551, artifacts 7,154→5,792 by dedup, not loss), lifts
mutations +5.7% (dominated by eunomia.dev's recovered Claude activity),
moves RQ1 persistence and RQ2 validation coverage gates from 3/6 to 6/6,
strengthens the reuse–volume rho 0.0857→0.2000, completes RQ3 return evidence
for the sixth case — and does NOT unblock RQ4's four-project estimator gate.
