# Experiment Plan: Truth-And-Access Feasibility For Longitudinal Workspace Diagnosis

Created: 2026-07-19T21:15:52-07:00
Revised after independent review: 2026-07-19
Parent: BOOTSTRAP Step 0001, re-entered EXPERIMENT_GATE
Status: **TERMINALLY CLOSED after Round-3 BLOCK**; no dependency implementation
or supervisor diagnosis run is admitted

## Research Question

- **Paper-level question:** Compared with final artifacts, native reports,
  session-local evidence, state changes, established process features, faithful
  HTIR, and equal-budget raw retrieval, can workspace-centered action
  trajectories make an automatic supervisor more reliable at diagnosing
  stagnation, goal drift, validation gaps, and harness waste, and at identifying
  the earliest evidence-supported intervention in long-horizon work?
- **Specific uncertainty tested here:** Can the project construct independent
  human truth with adequate positive coverage, exact historical workspace state,
  a genuinely cross-goal longitudinal unit, faithful strong baselines, and one
  byte/token-enforcing access interface on real coding and non-coding work?
- **What this node does not test:** It does not compare supervisor accuracy,
  estimate a treatment effect, validate a visualization, or produce a paper
  result.

The evaluated consumer remains an **automatic supervisor Agent**. Human experts
appear only as independent ground-truth annotators; this project makes no
human-interface or user-study claim.

## Paper-Value Admission

- **Planned role:** decisive dependency experiment before any new RQ1 pilot.
- **Largest credible story unlocked:** a fair empirical test of process-level
  scalable oversight over persistent workspaces, including ongoing and
  successful-but-pathological work rather than only known failed runs.
- **Load-bearing reject argument addressed:** the labels may be subjective or
  absent, historical state may be approximate, the purported longitudinal
  mechanism may be only within-goal concatenation, non-coding traces may not
  support the same task, and structured access may win through a budget or
  baseline artifact.
- **Independent evidence added:** exact boundary-state, source-coverage,
  label-prevalence, evidence-localization, intervention-label, strong-baseline,
  and access-parity feasibility in coding and auto-research workspaces.
- **Why it is not dominated by the closed pilot:** this plan does not rerun a
  three-times-blocked diagnosis comparison. It first tests dependencies the
  closed plan did not establish.
- **Decision if it fails:** return to the outer idea gate. Do not silently delete
  a sparse label, delete intervention, substitute an approximate snapshot, or
  weaken a named baseline. Any taxonomy or claim change requires a separately
  authorized idea-evolution step and a new reviewed experiment plan.

## Non-Negotiable Scientific Contract

The dependency can pass only for the claim as stated above:

1. all four pathology labels and earliest intervention remain outputs;
2. evidence spans at least one completed prior goal and a later target goal in
   the same persistent workspace;
3. the interval includes at least two resumed or replaced **top-level** Agent
   sessions; parallel child/subagent sessions do not satisfy this condition;
4. exact workspace state is retained at the interval and goal boundaries;
5. feasibility passes separately in coding and non-coding domains;
6. only independent human expert annotations affect scientific admission; and
7. OCPM and Full HTIR are faithful, label-independent baselines rather than
   weakened look-alikes.

Failure of any item is `FAIL -> outer idea gate`, not permission to revise the
contract inside this node.

## Workloads And Label-Independent Selection

### Historical mechanics cases, not scientific evidence

Two already-audited paths remain useful for parser, identifier, view, and broker
mechanics:

1. **ActPlane coding interval**
   `[2026-06-29T21:23:12Z, 2026-06-30T07:05:00Z)`: 1,401 Tool
   actions, 805 projected file actions, 47 affected files, five affiliated
   sessions, Codex and Claude.
2. **AgentSkill citation interval**
   `[2026-07-12T04:40:23.535Z, 2026-07-12T04:58:31.093Z)`: 115
   Tool actions, 41 projected file effects, one parent and three spawned
   sessions.

Both have complete source-call identity in the audited slices. Neither currently
has cryptographically retained exact boundary snapshots, and the AgentSkill
slice is neither long-running nor a resumed/replaced multi-goal path. Therefore:

- they cannot contribute prevalence, agreement, diagnosis, longitudinal-value,
  intervention, or accuracy evidence;
- nearest Git commits, Git checkout approximations, and inferred dirty trees are
  explicitly inadmissible as $W_0$ or $W_T$; and
- either path can be promoted only if an exact retained snapshot or a fully
  deterministic replay is later proved against every recorded source/system
  effect. Otherwise it remains a mechanics case.

### Scientific unit: workspace supervision interval

A scientific item contains:

- a prospectively declared workspace scope and capture start $H_0$;
- the complete retained Agent history from $H_0$ through a target goal end;
- at least one completed prior top-level goal and one later target goal;
- at least two genuine resumed or replaced top-level sessions, excluding
  parallel children; and
- atomic snapshots at $H_0$, every included goal boundary, and $W_T$.

Labels attach to each explicit goal, including the target goal. Cross-goal
recurrence and prior evidence are recorded separately. Full-History Trajectory
and Raw receive the same $H_0\rightarrow W_T$ history; Target-Only Trajectory
and Raw receive the same target window; Session Local splits the full history
into reset sessions. No condition changes its declared window after inspection.

### Frozen prospective run registry

Before any eligibility, outcome, or label is inspected, the experiment freezes
and hashes `raw/registry.json`. It contains **40 scheduled autonomous runs per
domain** (80 total), one candidate per run, and one fixed capture-start/capture-
end window for the whole registry. Every registered run remains in the capture-
yield denominator even if it crashes, never reaches a second goal, or later
fails eligibility.

Each row fixes `run_id`, domain, base-workspace image hash, workspace/task-family
cluster IDs, Agent/vendor, harness and skill revisions, capture deadline,
workspace scope, and workload/goal source. The registry contains at least eight
independent workspace/task-family clusters per domain; no cluster contributes
more than five scheduled runs. Runs use fresh writable workspace instances even
when they share a base task family.

Candidate enumeration is automatic: the sole candidate for a run ends at the
**first** explicit top-level target goal after at least one completed prior goal
and after a top-level session resumption/replacement. If that event never occurs
inside the frozen window, the run is ineligible; a later convenient goal cannot
replace it. A target goal is never reused, and because each run yields at most
one candidate, scientific intervals never overlap prior history. Runs from a
shared base workspace/task family remain statistically clustered.

The feasibility corpus is captured from these declared starts rather than
reconstructed from convenient historical commits:

- **coding stratum:** autonomous software-development work that changes a
  persistent repository across multiple top-level sessions/goals;
- **non-coding stratum:** genuine auto-research work that evolves papers,
  research notes, datasets, experiment configurations, results, figures, or
  other persistent artifacts across multiple resumed/replaced top-level
  sessions/goals.

A short citation-check or parallel-subagent fan-out can exercise mechanics but
cannot satisfy the non-coding scientific stratum. Capture stops at the frozen
registry deadline, not when enough eligible or pathological cases appear.

Each run uses an isolated writable workspace on a dedicated Btrfs subvolume in a
mount namespace. The boundary controller owns the Agent, harness, child, and
background-writer process tree in one cgroup; no external process receives write
access. Atomic capture is defined below. `.git` object storage and declared
ephemeral caches may be excluded only by a registry rule. Git commits remain
milestones and outcome evidence, never substitutes for snapshots or Agent-action
time.

### Fixed census, no optional stopping

- Eight hash-selected supervision intervals, four per domain, are
  guide-development only. They are excluded from every prevalence, agreement,
  intervention, and evidence-feasibility estimate.
- The fixed feasibility census contains **48 different intervals**, 24 coding
  and 24 non-coding. There is no stop-when-positive rule.
- Within each domain, eligible registered runs are ordered by SHA-256 of
  `workspace_scope_hash || capture_start || target_goal_start || target_goal_end
  || sorted_top_level_session_ids`; the lowest hashes are selected.
- Selection uses only frozen boundary metadata and eligibility facts. Outcome,
  pathology, condition output, and supervisor behavior are unavailable to the
  sampler.
- Every exclusion is retained with a predeclared reason. After four development
  and 24 scientific intervals per domain are allocated, remaining eligible
  registered runs are unused reserve. If fewer than 28 intervals/domain are
  eligible, the dependency fails rather than extending the registry.

`annotation-and-sampling.md` defines the interval, goal, eligibility, and
independent-human procedures precisely.

## Atomic Boundary Snapshot Protocol

The capture controller interposes on top-level goal dispatch. It never forwards
a new goal while an Agent action is in flight. At $H_0$, every goal boundary,
and $W_T$, it:

1. stops dispatch and waits for the current model/tool action to return;
2. freezes the complete writer cgroup with cgroup v2 `cgroup.freeze=1` and
   verifies `cgroup.events:frozen=1` for every descendant;
3. verifies through mount-namespace and open-writer audits that no process
   outside the frozen cgroup can write the workspace;
4. calls `syncfs` on the isolated workspace mount;
5. atomically creates a read-only Btrfs subvolume snapshot;
6. records `CLOCK_MONOTONIC_RAW`, wall time, the last fully completed canonical
   source/system action, cgroup membership, mount/subvolume IDs, and snapshot ID;
7. hashes the manifest/archive from the read-only snapshot; and
8. unfreezes the cgroup before forwarding another goal/action.

An action is before the boundary only if its response and effects completed
before freeze. No action starts until unfreeze. An outside writer, in-flight
action, freeze/sync/snapshot failure, clock inconsistency, or non-atomic
filesystem makes the run ineligible. Copying a live tree is never exact state.
The manifest preserves raw bytes, path, mode, size, type and SHA-256 for regular
files, symlink targets, and directory existence; snapshot, archive, and manifest
are content identified.

## Exact State And Source-Coverage Admission

For every scientific interval:

1. atomic retained snapshots exist at $H_0$, each included goal boundary, and
   $W_T$;
2. complete source-native session files are retained by content hash, not as
   line-selected global-search fragments;
3. canonical source-call identifiers are unique and total over source actions;
4. every source-reported artifact effect is checked against later source/system
   evidence or a boundary snapshot;
5. every observed net snapshot change is associated with source/system evidence
   or explicitly marked `unattributed_external_effect`; any unattributed change
   to a goal-, evaluator-, or harness-relevant artifact rejects the interval;
6. every fact used by a derived trajectory item exists in the generic Raw store:
   native records, system effects, boundary snapshot manifests/raw bytes,
   evaluator/outcome records, and task/skill/harness specifications; and
7. unresolved timestamp-order, rename-identity, concurrent-goal, or workspace-
   scope ambiguity makes the interval ineligible.

Deterministic replay is an alternative only when it starts from a retained exact
snapshot, replays in an isolated copy, reproduces all later snapshot hashes, and
accounts for every source/system effect. A replay that merely reaches the same
Git commit is insufficient.

## Independent Human Truth

Two qualified human experts who have prior experience inspecting autonomous
Agent traces and were not involved in implementing any tested view annotate each
non-development item independently
from complete source records, exact snapshots, explicit goals, evaluator/test
evidence, and declared harness artifacts. A third human expert adjudicates.
They never see condition views, supervisor outputs, or another annotation before
submission.

Agent annotators may only dry-run schema parsing and interface mechanics on the
eight development cases. Their output cannot change the guide, labels,
thresholds, sampling order, case admission, evidence set, gold record, or later
power calculation, and is never included in a paper statistic.

Before adjudication, report per label:

- adjudicated positive counts by domain;
- raw agreement, Gwet's AC1, and Cohen's kappa;
- positive agreement $2a/(2a+b+c)$ overall and by domain;
- evidence-action and artifact-path Jaccard; and
- exact/adjacent earliest-evidence agreement.

The four pathology definitions and intervention schema are fixed in
`annotation-and-sampling.md`.

## Conditions Whose Inputs Must Be Constructible

Full-history conditions bind to identical frozen $H_0\rightarrow W_T$ source
membership. Target-only controls bind to the identical target-goal window and
its start/end snapshots. The feasibility node materializes but does not send
these views to a tested supervisor:

1. **Final State/Outcome** — $W_T$ plus evaluator outcome;
2. **Native Report** — frozen source-native reports within the interval;
3. **Counts** — deterministic action/session/goal/artifact/token/duration counts;
4. **State Diff** — exact snapshot changes from $H_0$ to $W_T$ with no
   intermediate order;
5. **Session Local** — the identical interval split by genuine top-level session,
   each read independently with context reset and frozen aggregation;
6. **Full-History Raw Retrieval** — every permitted raw record and byte source in
   the interval, generically indexed but not summarized;
7. **OCPM Features** — the predeclared official object-centric process-mining
   feature families below through an evaluation-only OCEL 2.0 adapter;
8. **Full HTIR** — the official HarnessFix implementation on directly compatible
   cases or a fidelity-checked reproduction of its complete representation;
9. **Full-History Workspace Trajectory** — cross-goal order, artifact lifecycle, workspace
   relations, real session/goal boundaries, candidate-validation relations, and
   canonical source links;
10. **Target-Only Raw Retrieval** — the same generic raw interface restricted to
    the target-goal window and its exact boundary state; and
11. **Target-Only Workspace Trajectory** — the identical trajectory projection
    restricted to that target-goal window, with no prior-goal actions or
    recurrence candidates.

Every derived Full/Target Trajectory item must link to a record retrievable
through corresponding Full/Target Raw: native Agent records, exact snapshot
manifests and allowed file-byte chunks, system-effect records,
evaluator/outcome records, or task/skill/harness specifications. No view may
contain a generated pathology, intent, failure cause, or semantic summary absent
from source evidence. OCEL is evaluation glue only and does not replace
`agent-session` or become a production dependency.

## Frozen OCPM Baseline

The baseline is frozen before human labels:

- implementation: `pm4py==2.7.23.3` and `ocpa==1.3.4`, captured with a hashed
  dependency lock;
- input: the same OCEL 2.0 adapter and full interval membership as Full-History
  Raw and Full-History Workspace Trajectory;
- feature families: object-centric directly-follows graph activity/node/edge
  frequencies and performance; per-object lifecycle variants, counts, lengths,
  and entropy; object-interaction graph degree/component statistics; event- and
  object-type counts/durations; and official object-centric Petri-net discovery
  and token-replay/conformance outputs where the official implementation accepts
  the case;
- normative constraints: only requirements already present in a task, evaluator,
  skill, or harness specification frozen before capture. No pathology label or
  annotation may create a conformance rule; inapplicable constraints return
  `not_applicable`, not an invented proxy;
- supervisor exposure: fixed tables/JSON returned by allowlisted broker queries,
  with no label-informed feature selection.

All non-conformance families must execute on **every eligible scientific
interval**. A conformance field may be `not_applicable` only when the registry
lacks an independently frozen normative specification. Every failure/reason is
reported by domain and cluster; any non-conformance execution failure violates
the OCPM obligation. A hand-written count table cannot be renamed OCPM.

## Frozen Full-HTIR Fidelity Obligation

The preferred baseline is HarnessFix repository revision
`9167a0b9a58748c73b56c3ee04fdc3437ba0c56e`. Its comparison must cover the
shared diagnosis targets `validation_gap` and `harness_waste`, but compatibility
is decided from input/interface facts before either label is known. The retained
output must satisfy all of the following:

1. one recoverable TraceStep per model/tool/environment/finalization step with
   request, response, role, execution status, and artifact/state effect;
2. temporal order plus source-grounded data/context-flow links with source span,
   target span, and reuse relation;
3. source-grounded control-flow links with source, target, triggering logic, and
   triggering condition/status;
4. artifact/state effects containing entity, observed transition, and supporting
   evidence, including explicit no-effect/unknown states;
5. implementation anchors containing concrete artifact reference, anchor
   relation, and supporting evidence;
6. HarnessFix responsibility-layer mapping when the implementation provides it;
7. the published representation ladder `Raw -> Raw+data-flow ->
   Raw+data/control -> Full HTIR`, all from identical source membership; and
8. no annotation-derived or diagnosis-derived edges, effects, or anchors.

Official code output is checked field-by-field against this list. A reproduction
must match the same checklist and published ladder; merely emitting ordered
steps, inferred file edges, or an “HTIR-compatible” name is not sufficient. If
official Full HTIR is incompatible and a faithful reproduction is infeasible,
the baseline obligation fails and the project returns to the idea gate.

Compatibility is frozen per registry row before labels. A compatible interval
must retain full model/tool/environment/finalization request-response steps,
corresponding system effects, exact harness/skill/prompt/tool-schema/orchestrator
artifacts, and enough implementation identity for concrete anchors. The registry
must designate at least 20 scheduled compatible runs per domain across at least
four independent clusters. Full HTIR runs on **all** eligible compatible
intervals. It must succeed on at least 80% of them, cover at least 12 scientific
intervals and four clusters per domain, and, after independent labels, include
at least two positives per domain for both shared targets. Compatibility rate,
execution success/reasons, domain, cluster, and label coverage are reported. One
successful case cannot pass any coverage requirement.

The HTIR constructor's exact model, prompt/configuration, package/repository
revision, token use, latency, and failures are frozen and reported. It sees only
evidence/harness artifacts generically available to the corresponding Raw
condition, never human annotations or Workspace Trajectory output.

## Matched Access And Exact Token Accounting

`access-broker.md` defines one read-only broker and a pre-response turn packer.

- The supervisor receives no arbitrary shell, file, `rg`, or `jq` access.
- Feasibility accounting is pinned to open-weight
  `Qwen/Qwen3-32B@9216db5781bf21249d130ec9da846c4624c16137`,
  `transformers==5.14.1`, and `tokenizers==0.23.1`.
- The counter renders every full model-visible turn with the repository's pinned
  chat template: common system prompt, condition instructions, complete tool
  schemas/descriptions, user/query messages, cursors/envelopes, tool responses,
  and assistant history. It uses `apply_chat_template(..., tokenize=True)` and
  admits the turn only before inference.
- A model/provider with opaque or unreproducible pre-response wrapping is
  inadmissible. Changing the model, revision, template, or tokenizer requires a
  new broker-parity review before any condition run.
- Raw and every structured condition can follow canonical source IDs through the
  same endpoint. Counters update atomically before bytes are released.
- Input budget, output-token cap, final output schema, model revision, and
  stopping rule are identical. All repeated Session Local prompts and schemas
  count against its condition total.

The temporary feasibility budget is defined label-independently from session
count: for $S$ genuine top-level sessions, every condition receives
`max(8, 2*S)` successful broker queries, `max(131072, 8192*S)` returned UTF-8
bytes, and `max(32768, 2048*S)` cumulative complete model-input tokens. This
only exercises enforcement; future study budgets must be frozen before viewing
condition results.

## Planned Dependency Runs

| Run | Role | Workload | Action | Decision consequence |
|---|---|---|---|---|
| registry-and-capture | sampling/state dependency | frozen 80-run registry | atomically snapshot and enumerate one candidate/run | Registry denominator, clusters, and failures remain visible; live copies/Git approximations fail. |
| boundary-audit | truth dependency | fixed census | two independent human boundary decisions | Report and threshold separately by domain. |
| source-coverage | evidence dependency | same intervals | audit native actions, exact snapshots, and attributed effects | Decide whether each domain is admissible. |
| label-census | truth dependency | fixed 48 intervals | two independent human annotations plus human adjudication | Admit or reject the unchanged four-label/intervention contract. |
| view-construction | mechanism dependency | historical mechanics + development cases | generate all eleven views, including Full/Target Raw and Trajectory pairs | Prove inputs and raw links are constructible. |
| broker-parity | fairness dependency | same cases | exhaust, paginate, and overrun every condition | Prove exact pre-response byte/token/query enforcement. |
| OCPM fidelity | baseline dependency | every eligible scientific interval | execute frozen official non-conformance families and applicable conformance | Missing coverage returns to idea gate. |
| HTIR fidelity | baseline dependency | every predeclared eligible compatible interval | execute pinned code or fidelity-checked ladder and audit coverage | Weak or sparse reproduction cannot pass. |

No tested supervisor model is invoked in this node. Passing all dependencies
admits a new diagnosis pilot plan, which receives independent review.

## Admission And Failure Rules

The dependency passes only if **all** conditions hold:

1. in each domain separately, at least 75% of all 40 registered runs have
   independently resolvable supervision/goal boundaries and at least 75% satisfy
   atomic-state/source coverage; at least eight frozen clusters/domain remain;
2. in each domain separately, at least 75% of the fixed census is not
   `insufficient_evidence` after full-source inspection;
3. every pathology has at least four adjudicated positive intervals overall and
   at least two in each domain;
4. every pathology independently satisfies pooled raw agreement $\ge 0.80$,
   pooled AC1 $\ge 0.60$, pooled positive agreement $\ge 0.60$, and per-domain
   positive agreement $\ge 0.50$; no conjunction or low-prevalence exception can
   bypass any threshold;
5. intervention need satisfies the pathology agreement thresholds; intervention
   action has pooled raw agreement $\ge0.70$, pooled multicategory AC1
   $\ge0.60$, and per-domain raw agreement $\ge0.60$; exact-or-adjacent earliest
   evidence agreement is $\ge0.60$ pooled and $\ge0.50$ per domain;
6. all full-history views preserve identical full membership, both target-only
   views preserve identical target membership, every trajectory item links to
   generically retrievable Raw evidence, and State Diff derives only from atomic
   retained snapshots;
7. broker counters never exceed frozen caps; deliberate byte, token, query,
   cursor, and source-scope overruns fail before data delivery;
8. official OCPM executes on every eligible scientific interval as frozen; and
9. Full HTIR passes every fidelity and coverage threshold over all predeclared
   compatible intervals and both shared targets.

Any failure is a scientific `FAIL` for the current claim and routes to the outer
idea gate. It cannot be converted to PASS by removing a label, intervention,
domain, history, baseline, or source requirement inside this experiment.

## Frozen Rule For The Later Accuracy Study

If and only if this dependency passes, the later diagnosis study uses a paired
within-interval design. Its primary accuracy comparison is Full-History
Workspace Trajectory versus Full-History Raw Retrieval. Its decisive
longitudinal contrast is Full minus Target-Only Trajectory, controlled by the
corresponding Full-minus-Target Raw contrast; Session Local, OCPM, and Full HTIR
are multiplicity-controlled secondary comparisons. Before selecting any
held-out test interval:

1. a separate development pilot estimates only label prevalence, paired
   prediction covariance/discordance, and per-domain attrition;
2. a frozen simulation script evaluates sample sizes using 10,000 Monte Carlo
   repetitions that resample complete workspace/task-family clusters and retain
   within-cluster dependence;
3. the target is 90% power at two-sided familywise $\alpha=0.05$ with Holm
   correction to detect an absolute **0.10 macro-F1 improvement**, the smallest
   effect considered paper-relevant;
4. the selected size is the maximum required across the pooled analysis, the
   two domain strata, and the full-versus-target longitudinal contrast; and
5. it is inflated by the one-sided 95% upper confidence bound on observed
   pre-model attrition. Excluded/failed model calls are not silently dropped;
   the estimand and missingness policy are preregistered before test inference.

All train/development/test allocation is by complete frozen workspace/task-
family cluster; no base workspace, target goal, prior history, harness/task
family clone, or derived slice crosses a split.

The held-out test set, model outputs, and condition outputs cannot influence the
sample size. If the required sample is infeasible, the accuracy experiment is
not run.

## Raw Evidence And Reproducibility

- Raw outputs live under this experiment directory in `raw/`, one immutable
  subdirectory per audit/run.
- The pre-capture registry and its capture window are content-hashed before the
  first run. Each run manifest records cluster IDs, canonical source paths, size,
  mtime, SHA-256, session/parent identity, goal boundary, workspace-scope hash,
  cgroup/mount/subvolume identity, monotonic boundary record, snapshot/archive
  hashes, repository revision, parser revision, dependency lock, and command.
- Frozen source slices, exact snapshots, human annotation JSON, pre-adjudication
  disagreements, broker transcripts, rendered token-count inputs, OCEL files,
  official baseline outputs, and generated views are retained when licensing and
  privacy permit; otherwise a cryptographic manifest and reproducible local
  access procedure are mandatory.
- Every derived table has one executable command from retained raw inputs.
  Aggregate-only or unverifiable evidence is insufficient.

## Terminal Disposition

Round 3 returned `BLOCK` because the plan annotated every included goal but did
not restrict prevalence, agreement, evidence, intervention, and HTIR shared-label
gates to the selected target goal. Prior-goal positives could therefore admit a
later supervisor study with no target-goal positive coverage. The permitted
three review rounds are exhausted.

This proposal is closed and returns to the outer orchestrator. It cannot be
repaired a fourth time, relabeled approved, implemented as an admitted
dependency, or used to authorize a supervisor model run. The reviewer-confirmed
Raw parity, Full/Target contrasts, atomic capture, registry/clustering, and
baseline-coverage designs remain provenance for a scientifically distinct
replacement node; they are not experimental results.
