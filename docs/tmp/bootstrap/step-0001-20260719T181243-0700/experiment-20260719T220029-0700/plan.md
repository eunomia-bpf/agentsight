# Experiment Plan: Target-Goal Truth And Longitudinal-Parity Feasibility

Created: 2026-07-19T22:00:29-07:00
Parent: BOOTSTRAP Step 0001, after accepted Target-Goal Estimand Closure
Status: terminally BLOCKED after the third HTIR dependency implementation
review; capture mechanics passed narrowly, but no registry/capture/supervisor
execution is admitted

## Why This Is A New Node

The prior proposal `experiment-20260719T211552-0700` is terminally closed after
three BLOCK reviews and cannot receive a fourth repair. This node starts from the
outer-orchestrator decision in
`estimand-20260719T215859-0700/estimand-report.md`: one registered run contributes
one target-goal outcome vector, while prior goals are input history and
descriptive recurrence truth only.

The experiment question is therefore different and explicit:

> Can we construct reliable **target-goal** pathology/intervention truth and
> matched Full-versus-Target evidence access over exact cross-goal workspace
> history in coding and auto-research, with strong process/trace baselines,
> before running an automatic supervisor?

This node tests measurement and access dependencies only. It does not test
diagnosis accuracy, effect size, human-interface utility, visualization quality,
or intervention causality.

## Terminal Dependency Disposition

The capture-mechanics dependency passed independent result review. The required
Full-HTIR dependency did not. Three independent implementation reviews exposed,
in sequence, an unsafe official-runtime path, incomplete Raw/flow/anchor
semantics, and finally two unresolved cross-record invariants: every TraceStep
must carry an explicit observed/no-effect/unknown state effect, and effects,
anchors, snapshots, boundaries, times, and effective goals must agree. The third
review returned BLOCK, so this proposal is closed rather than repaired a fourth
time. The 80-run registry was not created, prospective capture did not begin,
and no supervisor was invoked. Any continuation requires a scientifically
distinct idea/experiment node, not another patch to this plan.

## Frozen Scientific Outcome

For interval $i$, the registry selects one target goal $g_i^*$ without labels or
outcomes. The sole scientific outcome is

\[
Y_i=(P_i,E_i,A_i,I_i,\tau_i,C_i),
\]

all referring to $g_i^*$:

- four target-goal pathology labels: stagnation, goal drift, validation gap,
  and harness waste;
- minimal sufficient typed evidence IDs and affected artifact/state objects;
- retrospective intervention need and action from
  `{continue, stop, redirect, clarify, repair_harness}`;
- earliest supporting action **within the target goal**; and
- confidence/`insufficient_evidence`.

Every positive label/intervention evidence set cites at least one target-goal
action/effect. Prior-goal evidence may supplement a target positive by showing
recurrence, abandoned state, delayed validation, or a harness pattern, but prior
evidence alone never makes the target positive.

Prior-goal annotations never enter target prevalence, positive counts,
agreement, evidence/intervention gates, insufficient-evidence rates, HTIR shared-
target coverage, power nuisance estimates, or later diagnosis metrics. They are
not additional samples. Any implementation or analysis that unions goals fails
this experiment.

## Paper-Value Admission

- **Role:** last dependency before any RQ1 supervisor pilot.
- **Ambitious claim unlocked:** prior workspace process history and its
  structured lifecycle may help an automatic supervisor diagnose a later goal,
  including nominally successful but pathological work.
- **Reject arguments addressed:** target labels may be sparse/subjective;
  histories may be inexact or selectively sampled; Trajectory may receive facts
  Raw cannot access; the apparent longitudinal gain may be only extra history;
  OCPM/HTIR may be weak or sparsely applicable.
- **Failure:** return to the outer idea gate without deleting a label,
  intervention, domain, baseline, target-only control, or source requirement.
  Any changed claim requires a new idea decision and plan.

## Frozen Prospective Registry

Before capture or eligibility inspection, hash and retain `raw/registry.json`:

- 40 scheduled runs/domain, 80 total, under one fixed capture window;
- at least eight independent workspace/task-family clusters/domain;
- at most five runs/cluster;
- fresh writable workspace instance/run;
- fixed run ID, domain, base-image hash, cluster IDs, Agent/vendor, harness/skill
  revisions, workspace scope/exclusions, capture deadline, and workload/goal
  source; and
- at least 20 predeclared HTIR-compatible scheduled runs/domain across at least
  four clusters, based only on trace/harness/interface availability.

Every registered run remains in the capture-yield denominator. The sole
candidate is the first target goal after both (a) a completed prior top-level
goal and (b) a genuine top-level session resumption/replacement. Parallel
children, compaction, and automatic continuation do not satisfy (b). If the run
never reaches this event by its frozen deadline, it is ineligible. A later goal
cannot be substituted; a target is never reused; one run yields at most one
candidate, so histories do not overlap across items.

Within domain, eligible runs are hash-ordered from frozen boundary metadata. The
first four/domain are human-guide development only; the next 24/domain form the
fixed 48-item scientific census. Later eligible runs are unused reserve. Fewer
than 28 eligible/domain fails; capture does not continue beyond the registry.

## Quiescent Exact-State Protocol

Each run has an isolated workspace mount namespace. All Agent, harness, tool,
child, and background-writer processes are started in one owned cgroup; no other
process has write permission to the in-scope tree. The goal dispatcher is
interposed and does not start a new action/goal while a boundary is captured.

At $H_0$, every included goal boundary, and $W_T$, the controller:

1. waits for the current model/tool action and its source/system effect records
   to complete;
2. freezes the complete writer cgroup and verifies every descendant is frozen;
3. audits `/proc/*/fd`, file-backed writable `/proc/*/maps`, writable mount
   handles, and mount permissions to prove no external writer can mutate scope;
4. calls `syncfs` on the workspace mount;
5. creates manifest $M_1$ over all in-scope paths, raw-byte hashes, modes, sizes,
   types, symlink targets, and directory existence;
6. archives those bytes while writers remain frozen;
7. creates independent manifest $M_2$ from the live frozen tree and manifest
   $M_A$ from the archive, requiring byte-identical $M_1=M_2=M_A$;
8. records `CLOCK_MONOTONIC_RAW`, wall time, last completed source/system action,
   cgroup/process set, mount identity, and manifest/archive hashes; and
9. unfreezes only after the boundary record is durable.

No action crosses a boundary. An in-flight action, outside writer, freeze/audit/
sync/read/hash failure, manifest mismatch, clock-order inconsistency, or scope
escape rejects the run. This protocol proves a stable exact state on ordinary
Linux filesystems without requiring a live-tree copy to be atomic. A Git commit
or checkout is never a substitute.

Historical ActPlane and AgentSkill slices lacking this evidence remain mechanics
cases only.

## Independent Human Truth

`target-truth-contract.md` is authoritative. In summary:

- two human experts with autonomous-Agent trace-review experience and no tested-
  view implementation role annotate independently;
- a third human expert adjudicates only after raw submissions are retained;
- boundary annotators do not see pathology/outcome/condition data;
- scientific annotators see complete raw evidence and exact states, never tested
  views or supervisor outputs;
- Agent dry runs can validate JSON mechanics on development cases only and
  cannot affect the guide, threshold, selection, truth, or PASS; and
- all scientific statistics use the 48 target-goal records only, cluster-
  resampled by frozen workspace/task family.

Target admission requires, in each domain, record-level and per-output
sufficient-evidence and target-
positive coverage plus non-bypassable raw/AC1/positive agreement. Intervention
need/action/earliest support have explicit thresholds. Prior-goal records are
reported only as auxiliary recurrence/history data.

## Eleven Evidence Conditions

All conditions predict the same target outcome $Y_i$ and all enter through the
single budgeted broker/turn packer before any condition evidence is visible:

1. Final State/Outcome;
2. Native Report;
3. Counts;
4. exact $H_0\rightarrow W_T$ State Diff;
5. Session Local over full history with reset contexts and deterministic
   aggregation;
6. Full-History Raw;
7. OCPM Features over full history;
8. Full HTIR over full history on predeclared compatible intervals;
9. Full-History Workspace Trajectory;
10. Target-Only Raw; and
11. Target-Only Workspace Trajectory.

Full-History conditions bind to identical $H_0\rightarrow W_T$ evidence.
Target-only Raw/Trajectory bind to the identical target action window, its exact
start/end states, target evaluator records, and specification versions in force
at target start or changed during target work. Earlier specification versions
are prior history and excluded. All eleven use budgets computed from the full
interval.

## Same-Raw And Matched-Access Contract

`evidence-access-contract.md` is authoritative. The raw store contains complete:

- native Agent records;
- system-effect records;
- boundary manifests and permitted raw file bytes/chunks;
- evaluator/test/metric/outcome records; and
- task/goal/skill/prompt/tool-schema/harness/orchestrator specifications.

Every structured item cites typed bottom-level IDs that matching Raw can retrieve
byte-for-byte. Raw exposes generic filters/search/byte ranges, not derived
lifecycle, flow, recurrence, conformance, diagnosis, intent, or summary.

One broker and turn packer enforce query, UTF-8 byte, and cumulative complete-
input-token budgets before inference. Accounting is pinned to
`Qwen/Qwen3-32B@9216db5781bf21249d130ec9da846c4624c16137`,
`transformers==5.14.1`, `tokenizers==0.23.1`, and the pinned chat template.
System/condition prompts, tool descriptions/schemas, queries, envelopes,
responses, and repeated history all count through
`apply_chat_template(..., tokenize=True)`. Opaque provider wrapping is
inadmissible.

Mandatory opening/static payloads are not free: each consumes a query and its
canonical response bytes. Oversized first payloads are rejected before model
visibility. If any required condition cannot fit, the experiment fails rather
than dropping it or changing budgets.

For full-interval top-level session count $S$, every condition gets
$Q=\max(8,2S)$ successful queries, $B=\max(131072,8192S)$ returned bytes, and
$T=\max(32768,2048S)$ cumulative full model-input tokens for dependency testing.
The future effect-study budget is separately frozen before test outputs.

## Strong-Baseline Contract

`baseline-contract.md` is authoritative:

- PM4Py 2.7.23.3 and OCPA 1.3.4 non-conformance families run on every eligible
  scientific interval; conformance is `not_applicable` only without an
  independently frozen normative specification.
- HarnessFix revision `9167a0b9a58748c73b56c3ee04fdc3437ba0c56e` or a
  field-faithful reproduction runs its full Raw/data-flow/data-control/Full-HTIR
  ladder on every predeclared eligible compatible interval.
- HTIR must succeed on at least 80% of compatible intervals, cover at least 12
  scientific target intervals and four clusters/domain, and include at least two
  **target-goal** positives/domain for both `validation_gap` and `harness_waste`.
- HTIR construction is a pinned deterministic, model-free HarnessFix procedure;
  its official-entrypoint selection, source hashes, faithful mapping, resource
  limits, and pre-label compatibility decision are frozen before capture. It
  sees only matching Raw evidence, never target truth or Trajectory output.

Sparse or nominal baseline success fails; one compatible example cannot pass.

## Planned Dependency Runs

| Run | Workload | Output | Pass consequence |
|---|---|---|---|
| registry-freeze | all 80 scheduled runs | hashed registry/window/cluster table | Fix denominator before eligibility. |
| capture-mechanics | two new real development runs/domain | freeze/audit/double-manifest transcripts | Prove exact-state protocol on current filesystem. |
| prospective-capture | registry | complete raw stores and boundary states | Supply nonoverlapping target intervals. |
| boundary/source audit | all registered/eligible runs | independent boundaries, capture yield, source coverage | Gate each domain/cluster. |
| target-truth census | fixed 48 scientific intervals | independent target-only annotations, agreement, adjudication | Gate unchanged target outcome. |
| view construction | development cases | all eleven views and typed raw links | Prove Full/Target and baseline inputs. |
| broker parity | development cases | exact-fit/overrun/scope/byte-link tests and transcripts | Prove pre-response parity. |
| OCPM coverage | every scientific interval | official outputs/failure table | Gate strong process baseline. |
| HTIR coverage | every compatible interval | faithful ladder/fidelity/coverage table | Gate strong harness baseline. |

No tested supervisor diagnosis model runs in this node. Passing admits a fresh,
powered diagnosis-pilot plan with another independent review.

## Admission Rules

All are conjunctive:

1. each domain retains at least 75% boundary-resolvable and at least 75% exact-
   state/source-complete registered runs, at least 28 eligible targets, and at
   least eight clusters;
2. in each domain, at least 75% of adjudicated scientific **target records** are
   sufficient across all four pathologies and intervention need, and every
   individual pathology plus intervention need is sufficient for at least 75%
   of targets, using the frozen formulas in `target-truth-contract.md`;
3. each pathology has at least four target positives overall and at least two
   target positives/domain;
4. for each target pathology: pooled raw agreement $\ge0.80$, pooled AC1
   $\ge0.60$, pooled positive agreement $\ge0.60$, and per-domain positive
   agreement $\ge0.50$;
5. among independently jointly positive target labels, median evidence-ID and
   artifact-object Jaccard are $\ge0.50$ pooled and $\ge0.40$/domain, while
   exact-or-adjacent target-onset agreement is $\ge0.60$ pooled and
   $\ge0.50$/domain;
6. target intervention need meets rule 4; action has pooled raw agreement
   $\ge0.70$, pooled multicategory AC1 $\ge0.60$, and per-domain raw agreement
   $\ge0.60$; exact-or-adjacent earliest target-action agreement is $\ge0.60$
   pooled and $\ge0.50$/domain;
7. every structured item byte-links to matching Raw; Full/Target pairs preserve
   their fixed windows; State Diff uses exact quiescent states;
8. all eleven conditions pass mandatory-open and later-delivery exact-fit and
   deliberate byte/token/query/cursor/scope overruns before delivery; any
   required-condition infeasibility fails;
9. OCPM executes on every eligible scientific interval; and
10. HTIR passes fidelity, success, cluster/domain, and target-positive shared-
   label coverage.

Failure routes to the idea gate. Prior-goal labels, pooled-domain success,
negative agreement, output deletion, later capture, or one baseline example
cannot bypass a failed rule.

## Cluster-Aware Statistics And Later Power Rule

Feasibility point estimates are interval-weighted, but 95% uncertainty uses
10,000 stratified bootstrap replicates of complete frozen workspace/task-family
clusters. Report percentile and BCa intervals, cluster count/size, and effective
sample size; independent-binomial intervals are sensitivity only.

If this node passes, a separate development pilot fixes the held-out paired
sample. A frozen 10,000-replicate cluster Monte Carlo script targets 90% power at
two-sided familywise $\alpha=0.05$ with Holm correction for an absolute 0.10
macro-F1 effect, inflated by the one-sided 95% upper bound on pre-model
attrition. The primary comparison is Full Trajectory vs Full Raw. The decisive
longitudinal statistic is

\[
(M_{Traj,full}-M_{Traj,target})-(M_{Raw,full}-M_{Raw,target}).
\]

The chosen size is the maximum needed across pooled, domain, primary, and
longitudinal contrasts. Entire clusters are held out; no base workspace, target,
prior history, harness/task clone, or slice crosses splits.

## Review Disposition And Next Decision

Independent plan review returned BLOCK in Round 1, the three defects were
repaired, and Round 2 returned PASS. Dependency implementation and real
dependency preflight were admitted. Capture execution then received a separate
result review: Round 1 BLOCK exposed mount-isolation, durability, effect-
completion, provenance, thaw, credential-retention, permission, and session-ID
defects; after repair and complete rerun, Round 2 returned PASS. Details are in
`result-review.md`.

No supervisor may run in this node. Passing every dependency admits a separate,
powered diagnosis-pilot plan with its own independent review.

## Capture-Mechanics Execution

The authoritative mechanics output is
`raw/capture-mechanics/preflight-repair-final-20260719T232531-0700/`. It uses a
private systemd-mounted ext4 image, DynamicUser, delegated cgroup, explicit TCB,
fail-closed audits, independently retained source/effect completion, durable
acceptance-before-thaw, content-bound controller/command provenance, secure
outputs, and crash-tested ephemeral credentials. Four accepted boundaries froze
at least two writer processes and satisfied $M_1=M_2=M_A$. The deliberately
unfinished asynchronous effect was rejected from its pending transcript record
and accepted only after completion.

Two new coding and two new auto-research development workloads also passed with
eight distinct completed top-level Codex sessions and exact states at H0, the
prior-goal boundary, and the target boundary. Paths and the independent
recomputation are recorded in `result-review.md`.

**Disposition:** the capture-mechanics/development dependency PASS is narrow and
has no paper effect. The immediate next action is `registry-freeze`: construct,
hash, and verify all 80 scheduled run entries before any eligibility inspection
or prospective capture. Supervisor inference remains forbidden.
