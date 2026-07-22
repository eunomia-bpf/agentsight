# Independent Plan Review Record

Experiment: `experiment-20260719T211552-0700`
Plan purpose: truth-and-access feasibility before any supervisor diagnosis run
Current status: **TERMINALLY CLOSED after Round 3 `BLOCK`**

## Round 1 — BLOCK

The independent reviewer found seven admission-breaking defects:

1. Sparse pathology/intervention evidence could be converted to PASS by deleting
   an output after inspection.
2. The historical ActPlane and AgentSkill paths lacked exact $W_0/W_T$ truth;
   nearby Git commits were only approximations.
3. The annotation unit ended at a new goal, so the experiment tested within-goal
   multi-session aggregation rather than the claimed cross-goal longitudinal
   mechanism. It also lacked a genuine resumed/replaced non-coding path.
4. The prevalence procedure mixed four guide-development items into estimates,
   used optional stopping with ordinary Wilson intervals, lacked positive-case
   agreement, allowed rare-label thresholds to be bypassed by high negative
   agreement, did not gate domains separately, and left later power/attrition
   rules unfrozen.
5. Agent-generated annotations could influence scientific admission even though
   independent human truth is required.
6. Token parity did not pin an exact model/tokenizer/template or charge all
   condition-specific model-visible material.
7. OCPM and Full HTIR could pass as weakened or label-informed nominal baselines.

The reviewer also requested deterministic Session Local remainder allocation and
an explicit distinction between parallel child agents and genuine resumed or
replaced top-level sessions.

## Round-1 Repair Map

| Finding | Binding repair |
|---|---|
| Deletion escape hatch | `plan.md` now fixes four pathologies plus earliest intervention as non-negotiable. Any sparse/unreliable output fails and routes to the outer idea gate; taxonomy changes need a new idea step and plan. |
| Approximate historical state | Historical paths are mechanics-only. Scientific cases require prospectively retained exact boundary archives/manifests or exact replay against every boundary/effect. Nearest Git state is explicitly forbidden. |
| Missing longitudinal mechanism | The unit is now a workspace supervision interval with complete history, at least one prior and one target goal, and at least two genuine top-level resumed/replaced sessions. Raw and Workspace Trajectory see the same history; Session Local sees the exact reset partition. A real long-running non-coding auto-research stratum is mandatory. |
| Biased prevalence/agreement/power | Eight development items are excluded. The scientific census is fixed at 48, 24/domain, with no optional stopping. Positive agreement is mandatory overall and by domain. All agreement thresholds are conjunctive. Domain gates are separate. The later paired-study power rule fixes 90% power, two-sided familywise alpha .05, a 0.10 macro-F1 effect, 10,000 simulations, and attrition inflation. |
| Agent truth contamination | Only two independent human experts plus a third human adjudicator affect labels/admission. Agent outputs can test schema mechanics only and are excluded from all decisions/statistics. |
| Unpinned token parity | Accounting is pinned to `Qwen/Qwen3-32B@9216db...`, `transformers==5.14.1`, `tokenizers==0.23.1`, the pinned chat template, and full `apply_chat_template` requests. System prompts, condition prompts, tool schemas, queries, envelopes, history, and candidate responses are all charged before inference. |
| Weak OCPM/HTIR | OCPM pins PM4Py/OCPA versions and feature families before labels. Full HTIR pins HarnessFix commit `9167a0...`, its complete Raw/data-flow/data-control/Full ladder, a field-level fidelity checklist, and at least one shared diagnosis target. Incompatibility or weak reproduction fails. |
| Session remainder | `access-broker.md` specifies quotient/remainder allocation over sorted top-level session IDs for queries, bytes, and tokens. |
| Child-vs-resumed sessions | `annotation-and-sampling.md` excludes compactions, continuations, child agents, and parallel subagents from the multi-session requirement and retains them under the owning top-level session. |

## Round 2 — BLOCK

The reviewer confirmed that all seven Round-1 must-fix items and both optional
items were repaired and non-bypassable, then found five new defects:

1. Raw Retrieval exposed only native sessions while Trajectory could consume
   snapshots, system effects, evaluator records, and specifications.
2. The plan claimed cross-goal incremental value but did not construct or meter
   target-goal-only Trajectory/Raw controls.
3. A content-hashed live archive did not prove an atomic goal/action-boundary
   state when background writers could continue.
4. The candidate denominator, overlapping histories, and statistical clusters
   were not frozen; interval-level binomial/power procedures assumed false
   independence.
5. OCPM/Full HTIR could satisfy the baseline gate with isolated successful
   cases; Session Local also referenced an unspecified confidence calibrator.

## Round-2 Repair Map

| Finding | Binding repair |
|---|---|
| Raw evidence asymmetry | The raw store now includes native Agent records, system effects, atomic snapshot manifests/allowed file bytes, evaluator/outcome records, and task/skill/harness specifications. Every structured item cites typed bottom-level IDs that the corresponding Raw scope must byte-retrieve. |
| Missing longitudinal contrast | The condition set now includes Full-History Raw, Target-Only Raw, Full-History Trajectory, and Target-Only Trajectory. Full/Target pairs use identical evidence windows and equal full-interval budgets. The later mechanism estimand is Full-minus-Target Trajectory controlled by Full-minus-Target Raw. |
| Non-atomic snapshots | Registered runs use isolated Btrfs subvolumes/mount namespaces. The interposed controller waits for action completion, freezes/validates the whole writer cgroup, audits outside writers, syncs, atomically snapshots, records monotonic/action order, then unfreezes. Any ambiguity fails. |
| Unfrozen sampling/dependence | A pre-capture hashed registry fixes 40 runs/domain, one candidate/run, capture window, workload metadata, and at least eight clusters/domain. The first eligible target is automatic; goals/history never overlap across candidates. Cluster bootstrap and cluster-resampling power replace independent-interval assumptions; splits hold out whole clusters. |
| Sparse baselines/calibration | OCPM non-conformance features run on every eligible interval. HTIR compatibility is frozen pre-label, all compatible intervals run, and per-domain/cluster/success/shared-label coverage gates are mandatory. Session Local confidence is explicitly uncalibrated and cannot be reported as calibrated. |

## Round 3 — BLOCK

The reviewer confirmed that all five Round-2 defects were truly repaired:

- Raw byte-retrieves every bottom-level fact used by Trajectory;
- Full/Target Raw and Full/Target Trajectory form equal-budget longitudinal
  controls;
- cgroup quiescence plus atomic Btrfs snapshots produces an executable boundary;
- the 80-run registry, one candidate/run, nonoverlapping history and cluster-
  aware inference close sampling and independence defects; and
- OCPM/HTIR coverage and uncalibrated Session Local confidence are explicit.

One new admission-breaking defect remained. The contract labels every goal in a
supervision interval and calls the selected target goal the “main” target, but
its prevalence, agreement, evidence, intervention, insufficient-evidence, and
HTIR shared-label gates count ambiguous “positive intervals.” Prior-goal
positives could therefore satisfy all gates even when every selected target goal
is negative or unsupported. Treating all goals as samples would additionally
change the estimand and introduce within-interval pseudoreplication.

The minimum scientific correction is to define exactly one RQ1 outcome vector
per selected target goal; calculate every admission truth statistic and HTIR
shared-label coverage from target-goal records only; and reserve prior-goal
labels for recurrence/history truth and descriptive H5 analysis. Alternatively,
using all goals would require a new hierarchical estimand, statistical model,
and power contract.

## Final Disposition

The three permitted rounds are exhausted. This proposal is **closed and returned
to the outer orchestrator**. It does not authorize dependency implementation or
any supervisor model call. A target-goal estimand may be incorporated only in a
scientifically distinct replacement node with its own plan and independent
review; it cannot be called a Round-4 repair.
