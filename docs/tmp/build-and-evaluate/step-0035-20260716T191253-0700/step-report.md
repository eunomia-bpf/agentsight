# Step 0035 — Independent Same-Input Resource Attribution

**Entered:** 2026-07-16T19:12:53-07:00

**Phase:** `BUILD_AND_EVALUATE`

**Outer sequence:** `EXPERIMENT_GATE -> WRITE_GATE -> REVIEW_GATE`

**Current state:** `WRITE_GATE / EVIDENCE INTEGRATION`

**Fixed thesis:** **Agent observability needs profiling, not only debugging.**

**Selected paper question:** **RQ1 — Does Semantic Profiling Improve Resource Attribution?**

## Resume And Entry Audit

Step 0034 is scientifically complete and committed locally as `26ed64d3` on
the unchanged `research/semantic-flamegraph-artifacts-v2` branch. Its single
ordinary push returned without an error, but a direct remote read still shows
`f2e878ac`; the unpushed history therefore remains persistence backlog and does
not affect experiment admission. No force push or branch change is permitted.
The read-only `docs/agentpprof-paper` submodule remains clean at `7f80c433`.

At entry, the root reread the complete `docs/user-instruction.md`, complete
`docs/idea-story.md`, `docs/questions-for-author.md`, the four-RQ frontier,
Step 0034 result and outer audit, and the current closest-work map. There are no
open author questions. The exact thesis, four RQs, positive RQ1 hypothesis,
operations, operation stacks, and submodule-derived story remain fixed.

The root accepts one evidence-validity distinction rather than a reviewer
preference: R114 establishes scoped source lineage and lossless folding, while
R170 prompt-tag mixedness is not an independent semantic-responsibility target
because the same prompt tag defines the grouping and reference category. The
selected question therefore remains the original RQ1; this step seeks stronger
evidence for it rather than narrowing or replacing it.

The user explicitly prefers reusing complete real trajectories and avoiding a
new custom experiment when existing evidence can decide the question. The gate
first inspects R114, R170, their manifests/raw outputs, and established
profiling/trace-query alternatives to determine whether an independently
defined responsibility target unavailable to construction already exists. No
plan is admitted until that non-circular target and a decision-relevant
same-input comparison are identified.

## EXPERIMENT_GATE

### Node 001 — Existing-Asset And Published-Protocol Screen

**Status:** complete at 2026-07-16T19:55:22-07:00.

**Question.** Can the complete existing real AgentProf/AgentSight trajectories
support one non-circular same-input attribution comparison, or must the project
use an official external asset? The screen must distinguish source lineage,
semantic grouping, and independent responsibility truth; conservation or a
grouping label scored against itself is insufficient.

**Candidate inputs.** R114's fixed 20-task real-Codex source-effect suite,
R170/R224/R251 full-history operations and prompt tags, current AgentProf
outputs, pprof label/pseudo-frame behavior, Perfetto-style grouped queries,
Pivot Tracing precedent, and any official/public dataset already present in the
repository with an independent task-to-effect or root-cause oracle.

**Admission rule.** Admit one experiment only if the same stored operations and
effects can be shown to each method under a fair declared information contract,
the responsibility target is fixed independently of the proposed grouping,
and positive versus contradictory outcomes change the RQ1 paper decision. If
the existing assets cannot meet that rule, reject reuse honestly and select a
real official external asset rather than manufacture labels or a toy harness.

**Screen result.** The complete already-downloaded CodeTraceBench failed target
does meet the rule. Its 405 trajectories contain 20,866 operations, 2,948
independently human-verified stage intervals, and recoverable real provider
token usage for every operation. OpenHands and mini-SWE-agent preserve usage in
structured response metadata. SWE-agent's final trajectory tool-call IDs select
the exact response span despite concatenated retry logs. Terminus2's official
command stream is an exact ordered subsequence of response command strings;
unexecuted malformed/empty response commands are not invented as operations.
The full source and standard-metric audit is recorded in
`01-experiment-gate/experiment-001/asset-and-metric-screen.md`.

**Metric decision.** Use standard ordinary operation-level B-cubed as the
primary metric. Admit the published weighted B-cubed formulation with observed
total tokens only as a resource-sensitive secondary analysis. Reject the custom
mixed-weight score. Boundary F1 remains an RQ3 segmentation diagnostic and does
not decide resource attribution.

### Node 002 — One-Experiment Plan And Independent Review

**Status:** complete after three serial independent review rounds; final
verdict `PASS`.

Write one reuse-only experiment plan for the unchanged Step 0024 recurrence
assignments, the source-native `raw_action_key`/session controls, complete pre-
existing 405-session source-valid target population, ordinary B-cubed primary
metric, and token-weighted secondary analysis. Round 1 required truthful
405/468 population wording, the corrected raw-action baseline, task-cluster
uncertainty, and a multi-operation allocation audit. These corrections are
recorded in `01-experiment-gate/experiment-001/plan-review.md`. Round 2
confirmed those fixes and required one interpretation correction: a positive
ordinary B-cubed result with a nonpositive allocation-stable token-weighted
direction is `MIXED`, not improved resource attribution. Round 3 verified that
final correction and returned `PASS`; no
additional metric, baseline, workload, or experiment is required.

### Node 003 — Real Preflight

**Status:** complete; independent verdict `PASS`.

Implement only the approved read-only source adapter and scorer, then run the
declared real preflight over one released target from each of the six source
forms. Do not tune the recurrence constructor or inspect target stages/tokens
inside construction.

The real preflight completed over six sessions and 267 operations, with one
complete trajectory per source form. All operations recovered provider usage;
provider and allocated token mass agree; the selected Terminus2 and SWE-agent
inputs exercised multi-command allocation and retry/empty-operation recovery.
The scorer explicitly records `preflight_only`. The independent reviewer
recomputed all joins and metrics and additionally checked every SWE-agent and
Terminus2 target; it returned `PASS`. Detailed evidence is in
`01-experiment-gate/experiment-001/preflight-report.md`.

### Node 004 — Complete Full Run

**Status:** complete at 2026-07-16T20:35:44-07:00; `VALID / SUPPORTED`.

The approved command completed once over all 405 source-valid target
trajectories and 20,866 operations. Recurrence raises ordinary B-cubed F1 over
the matched raw-action-key view from 0.541070 to 0.649173, a `+0.108103` effect
with paired task-cluster-bootstrap 95% interval
`[+0.087091,+0.129132]`. Token-weighted recurrence-minus-raw effects remain
positive under equal, all-to-first, and all-to-last allocation: `+0.084574`,
`+0.075910`, and `+0.075671`. All planned views, resource components,
framework breakdowns, reproduction, selection, mass-conservation, and
multi-operation checks complete. The detailed record is
`01-experiment-gate/experiment-001/full-run.md`.

### Node 005 — Independent Result Review

**Status:** complete at 2026-07-16T20:45:00-07:00; verdict `PASS`.

A fresh read-only reviewer independently reconstructed all 20,866 joins,
ordinary and weighted B-cubed results, three allocation sensitivities, and
10,000 bootstrap resamples without calling the experiment scorer. It confirms
the registered result and routes directly to WRITE with no rerun, new
benchmark, or new algorithm. It also fixes the interpretation boundary:
phase-only reaches 0.654445 ordinary B-cubed F1, statistically
indistinguishable from recurrence, so this experiment establishes semantic
stage-aligned attribution over raw action identity rather than recurrence's
dominance over every semantic view. The complete review is
`01-experiment-gate/experiment-001/result-review.md`.

## WRITE_GATE

Entered. Integrate the standard ordinary B-cubed primary result and explicitly
secondary token-weighted sensitivity into RQ1 while preserving source-lineage,
multi-resolution, and multi-weight evidence. Demote the circular prompt-tag
mixedness analysis from main correctness evidence. Keep the phase-only row and
post-hoc boundary visible. Do not change the fixed thesis, four RQs, story, or
algorithm, and do not touch the canonical paper submodule.

## REVIEW_GATE

Not yet entered.

## Current Transition

Continue `WRITE_GATE / INTEGRATE STEP 0035 RQ1 EVIDENCE`, then run the complete
paper `REVIEW_GATE`.
