# BOOTSTRAP Step 0001 Report

Started: 2026-07-19T18:12:43-07:00
Phase: BOOTSTRAP
Target venue family: AAAI, with AI Alignment as the primary full-paper framing

## EXPERIMENT_GATE

### Gate entry

The repository had a runnable visualization prototype and extensive design notes but no `docs/paper/`, `docs/user-instruction.md`, `docs/idea-story.md`, or canonical research frontier. The gate therefore entered first-project BOOTSTRAP rather than treating existing GIF/HTML output as experimental evidence.

The gate read the user instructions now preserved verbatim in `docs/user-instruction.md`. The controlling constraints are: the problem extends beyond coding to persistent workspaces; time follows agent actions rather than commits; the research considers automatic diagnosis or a supervisor agent using the tool rather than human visualization utility; and the target is AAAI under a continuing research loop.

### Node B1 — Day-1 scientific-contract disposition

**Context.** 2026-07-19T18:12:43-07:00; EXPERIMENT_GATE bootstrap root node; status: completed initial disposition.

**Question and entry.** What is the largest faithful paper claim supported by the user’s problem and the existing artifact, without treating visualization novelty as the conclusion?

**Inputs and method.** The node inspected `docs/repository-nebula.zh-CN.md`, `docs/design/visexp/agent-nebula-research.zh-CN.md`, `agentvis/README.md`, the `agentvis` and `agent-session` architecture, and the user’s current scope restriction. It separated existing implementation facts from untested diagnostic claims.

**Results and raw evidence.** The existing artifact reconstructs and renders action-time repository evolution across native agent sessions, but it has no automatic diagnostic query interface, labeled process-failure data, or controlled diagnostic result. The user’s broader scenario includes auto research and explicitly excludes a human-interface study as the current mechanism. The accepted central position is therefore process-level automated oversight from persistent-workspace action trajectories. The visualization remains a source-inspection and demonstration view.

**Scientific impact and decision.** The ambitious target claim is that a supervisor agent using an evidence-linked workspace trajectory can diagnose progress failures and intervention points better than outcome-only, summaries, raw logs, and simple counts under fixed budgets. Alternatives that gains come only from more tokens, simple counts, or LLM reasoning over raw logs remain explicit hypotheses. This disposition is reversible if closest work already establishes the same claim or if equal-budget experiments show no incremental signal.

**Evaluation boundary.** The evaluated consumer is an automatic diagnoser or supervisor agent. Human experts may independently annotate and adjudicate the reference evidence, but human visualization usability, reading speed, and diagnostic performance are not treatment outcomes or paper claims in this research cycle.

**State updates and next action.** Created `docs/user-instruction.md`, the immutable Initial Narrative and hypothesis frontier in `docs/idea-story.md`, and current design, implementation, evaluation, and author-question frontiers. Mandatory claim-oriented literature grounding is next; it must determine same-claim risk, AAAI fit, required baselines, public trace assets, and a valid first experiment before any diagnostic implementation is admitted.

### Literature grounding

Completed at 2026-07-19T18:19:16-07:00. Detailed search and verification are recorded in `literature-20260719T181243-0700/literature-report.md` and summarized in `docs/background-related-work.md`.

### Node B2 — Closest-work, baseline, and experiment-grounding audit

**Context.** EXPERIMENT_GATE bootstrap root child; status: completed.

**Question and entry.** Does existing work already establish automatic trajectory diagnosis, harness diagnosis, online intervention, cross-session analysis, or persistent-workspace evaluation, and what exact claim remains defensible?

**Inputs and method.** The node searched primary papers and official artifacts for automated diagnosis, coding trajectories, harness provenance, online auditors, intervention validation, agent observability, longitudinal agents, cross-session aggregation, and persistent multi-artifact workspaces. It downloaded and full-text checked twelve retained papers and verified official artifacts for AgentRx, RootSE, AFTraj-2K, OR-Space, CSTM-Bench, and AgingBench.

**Results and raw evidence.** AgentRx and TrajAudit already perform automated critical-step diagnosis; AgentForesight performs prefix-level early auditing; HarnessFix attributes failures to harness artifacts; REFLECT validates attribution through intervention; AgentTelemetry supplies an agent-fault observability taxonomy. OR-Space, AgingBench, and Cross-Session Threats show that persistent workspaces and cross-session evidence are also not novel alone. The remaining gap is the incremental diagnostic value of realized artifact lifecycle and workspace transitions across sessions, particularly for progress stalls and successful-but-pathological work.

**Scientific impact and decision.** The generic diagnosis claim is rejected. The root accepts a sharpened claim: under matched information and model budgets, a supervisor Agent using queryable cross-session workspace evolution should improve process-state diagnosis and evidence localization beyond final artifacts, session summaries, counts, and raw-log retrieval. This preserves the ambitious oversight claim while making artifact evolution, rather than “another diagnoser,” the falsifiable mechanism.

**State updates and next action.** Added `docs/background-related-work.md`, the detailed literature report, retained PDFs, and a Narrative Evolution entry. Updated the design and evaluation frontiers with a six-condition pilot and minimal deterministic query surface. Node B3 must now determine whether existing naturalistic traces can support independent labels and choose the smallest valid data slice before admitting implementation.

### Node B3 — Naturalistic trace availability and selection-bias audit

**Context.** 2026-07-19T18:31:18-07:00; EXPERIMENT_GATE data node; status: completed.

**Question and entry.** Are there enough real, complete multi-session traces for the proposed pilot, and are globally matched sessions scientifically equivalent to repository-affiliated sessions?

**Inputs and method.** The node ran the existing release `agentvis`/`agent-session` path over AgentSight, ActPlane, AgentCap, AgentSkill, and AgentFS. It counted the event object already embedded in HTML and used a six-hour inactivity gap only to estimate candidate episode supply.

**Results and raw evidence.** AgentSight has 1,263 direct sessions, 117,266 tool events, 47,346 file actions, and 30 heuristic multi-session candidates; ActPlane has 524 direct sessions, 65,699 tool events, 34,357 file actions, and 27 candidates. AgentSkill provides a 36-session paper/research preflight. Global matching is selected on repository path effects: AgentCap expands from 337 direct tool events to 14,314 global events, of which 14,189 have file effects. It therefore omits surrounding no-file actions and cannot be treated as a complete process trace.

**Scientific impact and decision.** The corpus is sufficient for a real pilot, so synthetic trace generation is unnecessary. The experiment will use complete sessions whose cwd/project/remote proves workspace affiliation. Global matches remain visualization evidence only. Candidate temporal episodes must be independently reviewed for goal coherence before labels or conditions are generated.

**State updates and next action.** The decision-critical audit results are retained in this report, and one decisive RQ1 matched-budget experiment was admitted under `experiment-20260719T183118-0700/plan.md`. A fresh scientific plan review followed; as recorded below, that proposal ultimately closed without a model run.

### Node B4 — Experiment-plan review disposition

**Context.** 2026-07-19; EXPERIMENT_GATE plan-review child; status: closed and returned.

**Question and entry.** Is the matched-budget RQ1 proposal scientifically fair and
executable enough to admit one real automatic-diagnosis preflight?

**Inputs and method.** One fresh independent reviewer examined the plan and two repaired
follow-ups, the maximum allowed by `research-experiment-design`. The review tested the goal
unit, labels, baseline fairness, information and model budgets, episode boundary, evidence
namespace, command auditability, scorer, and completion rule. Non-model commands exercised
the final episode extraction and scorer edge cases.

**Results and raw evidence.** Rounds 1 and 2 found scientific-contract and execution
defects; repairs froze a 40-episode test cohort and a strict AgentSkill preflight interval,
preserved native call IDs, and added a real scoring path. Round 3 confirmed the
four-session/115-action/41-file-effect boundary and 115 unique canonical IDs but still
returned BLOCK for a raw-text final-report bug, an undeclared tool-audit implementation,
and an all-negative F1 bug. Those three defects were subsequently reproduced and repaired:
the final report is valid JSON, native logs are physically time-sliced, a tool-audit path is
specified, and the scorer returns F1 zero for the reproduced false-negative case.

**Scientific impact and decision.** The repairs do not convert a Round-3 BLOCK into an
approval. Per the experiment protocol, this proposal is closed and returned to the outer
orchestrator without invoking a diagnosis model. It contributes no paper result. The
underlying RQ remains open, while the reviewed failure record shows that fair automatic
diagnosis requires exact goal boundaries, a condition-neutral evidence namespace, retained
tool streams, and executable metrics rather than prose-only constraints.

**State updates and next action.** `plan-review.md` records all three rounds and the closed
disposition. The outer orchestrator must choose the next scientifically distinct node; it
must not add a fourth review, call the repaired proposal approved, or report its dependency
fixtures as preflight evidence.

## WRITE_GATE

### Gate entry

The gate entered after the closest-work audit sharpened the claim and the first
experiment proposal closed without a model run. The root reread
`docs/user-instruction.md`, the complete Initial Narrative and evolution history
in `docs/idea-story.md`, the current design/implementation/evaluation frontiers,
the literature report, and the closed experiment review. The declared scope was
a complete AAAI submission-shaped paper whose sole evaluated consumer is an
offline supervisor agent performing automatic diagnosis.

### Node B5 — Submission-shaped paper and full writing refinement

**Context.** BOOTSTRAP WRITE_GATE; status: completed expression and verification.

**Question and entry.** Can the accepted scientific contract be stated as a
complete, falsifiable AAAI paper while preserving the user's non-coding scope,
automatic-diagnosis-only boundary, and every unresolved evidence requirement?

**Inputs and method.** The node created the official AAAI-27 paper under
`docs/paper/`, verified twelve retained references, added an architecture
figure, and ran the complete twelve-round `iter-refine-writing` loop. Fresh
reviewers audited logic, artifact consistency, sentence structure, word choice,
terminology/claim tone, flow, and final meaning preservation. The citation gate
ran the mandatory external metadata script and a missing-citation scan. Round
reports live in `iter-refine-writing-20260719T191537-0700/`.

**Results and raw evidence.** The paper fixes three RQs, four pathologies, five
evidence conditions, one retrospective-intervention output protocol, and one
automatic supervisor consumer. It distinguishes deterministic representation
structure from supervisor-produced pathology and intent, preserves action time
instead of commit time, retains zero-file-effect actions, and prohibits causal
claims from temporal adjacency. The final meaning-preservation reviewer returned
PASS and confirmed that no result placeholder, `Unanswered` gate, non-coding
scope, null branch, or user instruction was lost. Twelve bibliography entries
are real, annotated, locally backed by PDFs, cited, and mechanically verified.

**Phase-form correction.** Early writing rounds exposed current implementation
status inside the paper. At the gate exit, the root applied the BOOTSTRAP phase
policy: the paper now describes the intended complete system in submission
present tense and leaves placeholders only for missing result data. The actual
code frontier remains truthfully recorded in `docs/implementation.md`; no model
diagnosis result is claimed. This is an expression correction, not a mechanism,
RQ, scope, or evidence change.

**Verification.** The official AAAI PDF has eight pages, all main content ends
within page seven, references begin on page seven and continue on page eight,
the abstract is 200 words, and the LaTeX log has no overfull box, undefined
reference, undefined citation, or error. `agentvis` has 11 passing tests,
including source-call provenance preservation. `git diff --check` passes.

**Scientific impact and decision.** The complete paper makes the strongest
honest claim still left by closest work: not generic trajectory diagnosis, but
the incremental diagnostic value of same-source, cross-session realized
workspace evolution under matched retrieval budgets. Visualization is auxiliary
and human usability is explicitly outside the claim. The gate transitions to
REVIEW_GATE for scientific-contract disposition, outer audit, and phase routing.

## REVIEW_GATE

### Gate entry and scientific-contract audit

The root compared the verbatim user instructions, Initial Narrative, immediately
previous workspace-trajectory narrative, closest-work evidence, closed plan
review, and current paper.

### Root disposition

**Defer freeze and return the contract to EXPERIMENT_GATE.** The preserved
Initial Narrative already defined an offline automatic supervisor, four
pathologies, five evidence conditions, and retrospective intervention outputs.
The immediately previous framing stated the same goal generically in terms of
cross-session trajectories. The literature-sharpened contract isolates a more
specific mechanism: a bounded offline supervisor uses evidence-linked, realized
workspace evolution to diagnose stagnation, goal drift, validation gap, harness
waste, supporting evidence, and retrospective intervention recommendations
across coding and non-coding persistent workspaces.

This disposition follows the user's explicit restriction to automatic diagnosis
and the literature evidence that run-level diagnosis, harness diagnosis, online
auditing, and cross-session settings already exist. It does not shrink the
long-horizon or non-coding position. Instead, it isolates the falsifiable
mechanism---realized artifact lifecycle and workspace transitions---against a
same-source Raw Retrieval control. No absent result value is treated as a
scientific objection, and no probe result is presented as evidence.

The independent outer audit retained this direction but blocked transition to
BUILD_AND_EVALUATE. Freeze is deferred until adjacent mechanism grounding,
baseline closure, and an executable truth-and-fairness feasibility plan return.

### Independent outer audit and meta-review

**Verdict.** `outer-audit-20260719T205748-0700.md` returned **BLOCK** for phase
transition and routed REVIEW_GATE back to EXPERIMENT_GATE. WRITE_GATE passed as
a truthful BOOTSTRAP expression, but the only concrete empirical proposal is
terminally closed and supplies no model result.

**Decisive findings.** The next node must determine whether object-/artifact-
centric process mining already supplies the lifecycle mechanism and must fix the
baseline consequences for RQ1--RQ3. A subsequent, scientifically distinct plan
must enforce byte/token parity at the interface, construct labels independently
of tested conditions, measure pathology prevalence before committing sample
size, add a $W_0\rightarrow W_T$ state-diff control and a session-local reader,
resolve the HarnessFix comparison, and establish at least one real non-coding
path. Positive support must include retrospective intervention quality rather
than diagnosis alone.

**Maintenance.** The immutable Initial Narrative was not rewritten. Its
comparison with the previous and chosen positions was corrected in
`docs/idea-story.md`; `docs/evaluation.md` now points to the distinct mechanism-
and-baseline node rather than the closed pilot; the closed plan and all three
BLOCK verdicts remain intact; the B3 corpus and selection-bias synthesis remains
in this report; and the redundant standalone data-audit report was retired.

## Ranked open objections

1. Object-/artifact-centric process mining may already provide the claimed lifecycle mechanism, or may imply stronger conformance/state baselines than currently planned.
2. A same-source Raw Retrieval, $W_0\rightarrow W_T$ state-diff, or session-local supervisor may match Workspace Trajectory, leaving only an efficiency claim.
3. Reliable pathology and retrospective-intervention labels may remain subjective or too sparse despite independent evidence-ID adjudication.
4. Native agent records may omit decisive effects; the fixed native-evidence study therefore needs a separate controlled coverage audit.
5. One pathology taxonomy may not transfer from coding to persistent research or operations workspaces; no real non-coding feasibility path has yet passed.
6. RQ3 lacks a HarnessFix comparison or a demonstrated interface incompatibility.
7. The matched query harness, goal-episode constructor, snapshots, indexes, and condition runner are not yet implemented in the current artifact.

### REVIEW_GATE routing

Step 0001 remains active in BOOTSTRAP. The next node is a source-grounded
closest-mechanism and baseline-closure study. It asks whether process-mining or
harness-diagnosis work already establishes the workspace-lifecycle mechanism
and fixes the state-diff, session-local, retrieval, and harness baselines. If
the position survives, the following node is a new independently reviewed
truth-and-fairness feasibility plan, not a fourth review of the closed pilot.

## Re-entered EXPERIMENT_GATE

### Node B6 — Closest-mechanism and baseline closure

**Context.** 2026-07-19T21:10:48-07:00; source-grounded literature node;
status: completed. The detailed report is
`literature-20260719T211048-0700/literature-report.md`.

**Question and entry.** Does object-/artifact-centric process mining or the
strongest harness-diagnosis literature already supply the proposed workspace-
lifecycle mechanism, and which baselines are required to isolate the remaining
claim?

**Inputs and method.** The node searched primary papers and official artifacts,
downloaded five new full-text PDFs, and checked OCEL 2.0, OC-PM, object-centric
conformance, PM4AA, PMAx, PM4Py/OCPM, and HarnessFix. It compared their problem
unit, representation, diagnosis target, evaluation conditions, and runnable
artifact with the current RQs.

**Results and raw evidence.** Object-centric process mining already formalizes
events connected to multiple co-evolving objects, lifecycle and relationship
changes, discovery, performance analysis, and conformance. PM4AA already mines
software-repository OCELs to generate Agent roles, and PMAx already lets an Agent
interpret deterministic process-mining artifacts. HarnessFix Full HTIR already
combines data/control flow, artifact/state effects, and harness implementation
anchors; its 80-case diagnosis evaluation directly improves over raw traces.

**Scientific impact and decision.** Representation novelty, generic artifact
lifecycle, generic object-centric analysis, Agent interpretation of process
artifacts, structured-trace superiority, and generic harness attribution are
rejected as contributions. The root retains a narrower, medium-high-risk but
ambitious empirical claim: longitudinal workspace process state across session
and goal boundaries may improve automatic diagnosis of ongoing or nominally
successful but pathological work and earliest retrospective intervention.

**Baseline closure.** The replacement plan must include Final State, Native
Report, Counts, $W_0\rightarrow W_T$ State Diff, Session Local, equal-budget Raw
Retrieval, official OCPM Features, and Workspace Trajectory. RQ3 additionally
requires Full HTIR on compatible failed harness cases or a disclosed faithful
representation-ladder reproduction. Interface-enforced byte/token parity,
condition-independent truth, prevalence admission, intervention quality, and
one real non-coding path are mandatory.

**Implementation consequence and next action.** Keep `agent-session` as the
native source abstraction. OCEL 2.0 is only an evaluation adapter for reusing
PM4Py/OCPM, not a production IR. The next node is a scientifically distinct
truth-and-fairness feasibility experiment with one real coding and one real
non-coding path. It must pass independent plan review before any supervisor
model is invoked.

### Node B7 — Longitudinal truth-and-access feasibility plan

**Context.** 2026-07-19T21:15:52-07:00; EXPERIMENT_GATE dependency-plan node;
status: terminally closed after Round-3 BLOCK. Owner files
are under `experiment-20260719T211552-0700/`.

**Question and entry.** Can a later automatic-diagnosis experiment be grounded
in exact cross-goal workspace history, independent human truth, faithful OCPM
and HarnessFix baselines, and executable matched access before any supervisor
model is run?

**Inputs and method.** The initial plan used two audited historical paths, a
sequential pathology census, nine evidence conditions, and a shared broker. A
fresh independent reviewer tested the state boundaries, true longitudinal unit,
label admission, human/Agent truth separation, token parity, baseline fidelity,
and later power rule.

**Round-1 result.** The reviewer returned BLOCK: approximate historical Git state
could masquerade as exact snapshots; an episode ending at goal change did not
test cross-goal state; labels/intervention could be deleted after sparse results;
development cases and optional stopping biased prevalence; rare-label agreement
could pass through negative agreement; Agent labels were not fully segregated;
the tokenizer and complete model-visible budget were not pinned; and nominal
OCPM/HTIR outputs could pass without faithful mechanisms.

**Repair and scientific consequence.** The revised contract makes historical
ActPlane/AgentSkill slices mechanics-only and requires prospectively retained
exact snapshots. A scientific supervision interval spans at least one prior and
one target goal across genuine resumed/replaced top-level sessions; parallel
children do not count. The census is fixed at 48 scientific intervals, 24 per
domain, after eight excluded development cases. Only independent human experts
and a third human adjudicator affect truth. All positive-coverage, agreement,
intervention, domain, OCPM, Full-HTIR, and broker thresholds are conjunctive;
failure returns to the outer idea gate rather than shrinking the claim.
Accounting is pinned to an exact open-weight model/tokenizer/chat-template
revision and charges full rendered requests before inference. OCPM versions and
features and the HarnessFix representation ladder/fidelity checklist are frozen
before labels.

**Round-2 result and repair.** The reviewer confirmed every Round-1 issue was
closed, then blocked five remaining attribution risks. Trajectory could consume
snapshots/system/evaluator/specification evidence absent from Raw; the decisive
Full-History versus Target-Only mechanism contrast was not an actual condition;
hashed live-tree archives were not atomic; the candidate denominator and
workspace dependence were unfrozen; and OCPM/HTIR could pass through isolated
cases. The final revision gives Raw generic access to every bottom-level fact,
adds matched Full/Target Raw and Trajectory pairs, freezes an 80-run registry
with one nonoverlapping candidate/run and cluster-aware inference, specifies
cgroup quiescence plus atomic Btrfs boundary snapshots, runs OCPM over every
eligible interval, and requires Full HTIR across all predeclared compatible
intervals with per-domain/cluster/shared-label coverage. Session Local confidence
is explicitly uncalibrated.

**Round-3 result and terminal decision.** The reviewer confirmed every Round-2
repair, then found one remaining estimand defect: the plan annotated every goal
but did not restrict prevalence, agreement, evidence, intervention, insufficient-
evidence, and HTIR shared-label gates to the selected target goal. Prior-goal
positives could therefore approve a target-goal supervisor experiment with zero
target-positive coverage; treating all goals as samples would instead require a
different hierarchical model. Round 3 returned BLOCK. The three permitted rounds
are exhausted, so this proposal is closed and returned without implementation or
model inference. Its confirmed protocol subcontracts remain design provenance,
not evidence or approval.

**Raw evidence and next action.** `plan-review.md` retains all three BLOCK
findings and the terminal disposition. The outer orchestrator must select a
scientifically distinct target-goal-estimand node; it must not add a fourth
review or call this proposal approved. No diagnosis model has run and no paper
result follows from this node.

### Node B8 — Target-goal estimand closure

**Context.** 2026-07-19T21:58:59-07:00; outer-orchestrator decision after the
terminal B7 return; status: completed. Detailed decision record:
`estimand-20260719T215859-0700/estimand-report.md`.

**Question and entry.** Does one supervision interval contribute all included
goals, the union of their labels, or one selected target goal to RQ1 truth and
statistics?

**Inputs and method.** The node compared three estimands against the surviving
longitudinal claim, the Full/Target Raw and Trajectory contrast, cluster
independence, intervention timing, and the final reviewer counterexample. No
condition output or pathology prevalence was inspected.

**Decision.** Select exactly one RQ1 outcome vector per registered run, bound to
the label-independently selected target goal. All four pathology labels,
insufficient-evidence status, minimal evidence/artifact sets, intervention
need/action, and earliest supporting action are target-goal outputs. Every
positive cites at least one target action. Prior-goal labels may establish
recurrence/history truth and support descriptive H5 analysis, but never enter
target prevalence, agreement, intervention, HTIR shared-label coverage, power,
or diagnosis denominators. Counting all goals would require a different
hierarchical estimand and is rejected for the next program.

**Scientific impact and routing.** All Full/Target conditions now predict the
same target outcome. The longitudinal statistic is the Full-minus-Target
Trajectory gain controlled by Full-minus-Target Raw. This closes the terminal
plan's estimand defect without retroactively approving it. The next node is a
new, independently reviewed feasibility experiment with a new identifier; it
inherits the target estimand and the reviewer-confirmed atomic snapshot, Raw
parity, cluster, OCPM, and HTIR contracts. No implementation or supervisor model
run is yet admitted.

### Node B9 — Target-goal truth and longitudinal-parity feasibility plan

**Context.** 2026-07-19T22:00:29-07:00; fresh EXPERIMENT_GATE plan node;
status: terminally BLOCKED after the third HTIR dependency review. Owner directory:
`experiment-20260719T220029-0700/`.

**Question and entry.** Can the project build one independently valid target-
goal outcome per run and matched Full/Target evidence conditions over exact
cross-goal workspace history, with sufficient coding/non-coding truth and strong
baseline coverage, before a supervisor is invoked?

**Inputs and method.** The new plan treats the B8 target estimand as its first
non-negotiable rule and incorporates only protocol subcontracts that the terminal
B7 reviewer explicitly confirmed: complete Raw fact parity, Full/Target Raw and
Trajectory contrasts, frozen run/cluster registry, exact writer-quiescence
states, all-interval OCPM, all-compatible Full HTIR, and complete-input broker
accounting. Separate owner files freeze target truth, access, and baselines.

**Environment contact.** A local preflight records ext4, cgroup v2 with a present
but non-writable current `cgroup.freeze`, installed `systemd-run`/GNU tar, and no
Btrfs tooling. Therefore the plan uses an isolated writer cgroup, exclusive
mount scope, `syncfs`, and double live/archive manifest equality rather than
assuming Btrfs. Creating a delegated cgroup and proving freeze/unfreeze is a real
capture-mechanics dependency, not an assumed capability.

**Scientific safeguards.** Each of 80 preregistered runs yields at most the first
eligible target after prior work and top-level session replacement; only the
target record enters scientific statistics. Every positive cites a target
action. Prior-goal labels are auxiliary only. All uncertainty and later power
resample workspace/task-family clusters. HTIR shared-label coverage is target-
positive only. No label/domain/intervention/baseline can be removed on failure.

**Round-1 independent review.** A fresh reviewer confirmed the new target
estimand, registry, exact-state, Full/Target, OCPM, HTIR-coverage, and deletion
contracts, but returned BLOCK on three new operational gaps: only seven of
eleven conditions were explicitly brokered, insufficient-evidence denominators
were incomplete, and the HTIR constructor was not frozen pre-label.

**Repair and Round-2 decision.** The owner files now route all eleven conditions
through one charged turn packer, freeze per-label/record-level sufficiency and
all agreement denominators, and define a deterministic model-free HTIR
constructor with pinned upstream hashes, source-only mapping, compatibility
decision, and pre-capture freeze gate. The same fresh reviewer returned PASS in
Round 2 after independently checking the upstream revision/hashes and current
environment prerequisites.

**Admission and next action.** Dependency implementation and real preflight were
admitted. The first thin dependency was the ext4/cgroup-v2 capture-mechanics
controller and real tests of descendant freeze, stable live/archive manifests,
unfinished-effect rejection, and cross-goal Agent workloads. No supervisor model
run, diagnosis pilot, effect claim, or paper result is admitted by this node.

**Capture result and independent review.** Added the dependency-free
`agentvis/research/quiescent_capture.py` controller. Its first self-reported PASS
was independently BLOCKED because mount isolation, durability, effect evidence,
source/command provenance, partial-freeze thaw, credential crash cleanup,
permissions, and session-ID validation were incomplete. Failed paths remain
retained in `raw/capture-mechanics/attempts.md`.

The repaired controller runs writers in private systemd-mounted ext4 images
under a DynamicUser and delegated cgroup; a separate helper joins the mount
namespace, freezes the complete writer set, verifies mount/writer isolation,
retains source/effect pairs and independent M1/M2/archive/freeze/audit/mount/sync
records, makes its seal durable before thaw, and binds exact controller and
command bytes. Credentials use non-preserved systemd storage with a passing
SIGKILL cleanup test, and outputs are access-restricted.

The final mechanics run and two coding plus two auto-research workloads retained
16 accepted exact boundaries and eight distinct completed Codex sessions. A
fresh Round-2 result review independently reconstructed every boundary and
returned narrow PASS. `experiment-20260719T220029-0700/result-review.md` records
the evidence and limits. These are dependency results only.

**HTIR dependency and terminal result.** A deterministic Raw-linked Full-HTIR
reproduction was independently reviewed three times. The work removed an unsafe
official-runtime route and added strict registry, origin, span, reuse, support,
anchor, call, and ladder checks. The final reviewer nevertheless found that a
model TraceStep could lack an explicit effect/no-effect/unknown record and that
cross-record boundary/time/effective-goal consistency was incomplete. These are
result-validity defects for harness-waste attribution. Round 3 therefore
returned BLOCK and closed B9. No 80-run registry, registered capture, truth
annotation, broker run, or supervisor inference occurred. The outer
orchestrator must select a scientifically distinct idea/experiment node; a
fourth repair review is forbidden.

### Node B10 — Source-complete action evidence decision

**Context.** 2026-07-20T00:23:31-07:00; outer idea decision after terminal B9;
status: completed. Detailed record:
`source-contract-20260720T002331-0700/source-contract-report.md`.

**Decision.** Reject a fourth post-hoc adapter repair, dropping Full HTIR, and
restricting the population to official HarnessFix benchmarks. Select a source-
complete action/effect contract in the existing `agent-session` plus AgentSight
capture path. Every model/tool/environment/finalization action must close with
exactly one `observed`, `no_effect`, or `unknown` effect record and exact call,
time, session, goal, and boundary ownership. Specifications and anchors must
agree with effective goals and same-boundary snapshots.

**Scientific consequence and routing.** The new unit is the action/effect
closure invariant before any HTIR, OCPM, Trajectory, label, or supervisor exists.
This is shared source validity, not a trajectory-specific feature and not a new
general IR. Route next to a fresh EXPERIMENT_GATE source-completeness plan over
excluded coding and genuine auto-research development workloads. Registry
construction and supervisor inference remain forbidden.

### Node B11 — Algorithm/baseline formalization and paper-value admission

**Context.** 2026-07-20T00:33:44-07:00; EXPERIMENT_GATE candidate selection
after B10; status: completed selection audit, no experiment approved.

**Question and entry.** Is source completeness itself the next scientific
experiment, what exactly is the proposed algorithm, and which comparisons are
baselines rather than controls or implementation checks?

**Inputs and method.** The root reread the recorded user instructions, complete
idea/evaluation frontiers, paper RQs, closest-work map, and the experiment-design
admission rules. It inspected the current `agent-session`, AgentSight process
tracer, and Agent Nebula implementation. The process tracer already records file
opens and optional aggregated writes/mutations, but open/mutation success,
old/new rename paths, `dirfd`-relative resolution, exact unaggregated timing,
and action ownership are incomplete. The visual implementation separately uses
hand-tuned D3 force, operation/evidence weights, decay, density, and directory
share constants.

**Results and scientific decision.** The paper algorithm is now formalized as a
one-pass source-linked temporal property-graph construction over actions,
artifact versions, sessions, and goals. It emits only typed relations backed by
Raw IDs and closes every action as `observed`, `no_effect`, or `unknown`;
unresolved system events and shell text cannot fabricate effects. The dynamic
force layout is explicitly outside the scientific method. Main-baseline roles
are now separated by RQ: matched Raw Retrieval for RQ1, the Full/Target
difference-in-differences plus OCPM where needed for RQ2, and Full HTIR on
compatible RQ3 cases. Final State, Native Report, Counts, State Diff, Session
Local, and component removals are controls/ablations rather than a crowded list
of equal-status baselines.

The standalone source-completeness proposal fails PAPER-VALUE ADMISSION. Passing
it would establish infrastructure readiness but would not answer diagnostic
utility, information contribution, or generalization; failing it would only
block the same infrastructure. Its checks must be folded into the real
preflight of a direct paper experiment.

**Higher-value next candidate.** Plan one RQ1 controlled-intervention study over
real coding and auto-research Agent work: matched perturbed/repaired workspace
episodes supply independently checkable pathology/evidence/intervention truth;
Workspace Trajectory is compared with equal-budget Raw Retrieval, with State
Diff and Counts as controls. Source/action closure is a correctness veto in the
preflight. Positive evidence admits the larger naturalistic corpus; a Raw tie or
win reduces or rejects the representation claim before that cost. No workload,
registry, supervisor, or model run is authorized until a concise plan passes a
fresh independent review.

**State updates and next action.** `docs/design.md` now records the formal
algorithm and heuristic boundary; `docs/evaluation.md` records per-RQ baseline
roles and the admission decision; `docs/implementation.md` records the actual
filesystem-observation limitations. Next: draft the executable controlled-
intervention plan and obtain independent review. No Git operation occurred.

### Node B12 — RQ1 controlled-intervention plan

**Context.** 2026-07-20T00:39:08-07:00; EXPERIMENT_GATE plan node; status:
approved after independent review Round 3. Owner directory:
`experiment-20260720T003908-0700/`.

**Question and paper value.** Does deterministic organization of identical
full-history source evidence around persistent artifact evolution improve a
fixed automatic supervisor's diagnosis over a competent full-history Raw
serialization? This is a direct RQ1 pilot; source closure is a correctness
preflight rather than a standalone infrastructure experiment.

**Plan.** The pilot freezes three SWE-bench Verified and three OR-Space task
families, four neutral perturbation/repair mechanisms, 48 target episodes, and
six evidence conditions. Full Trajectory versus Full Raw is the sole RQ1
comparison. Target-only conditions, State Diff, and Counts are non-gating
mechanism controls. All episodes are independently labeled before perturbation
identity or paired outcomes are revealed; repaired siblings are not presumed
negative. The primary metric is four-label pathology macro-F1, with an
accepted-minimal-set evidence-F1 grounding veto and secondary localization,
artifact, intervention, calibration, cost, and latency measures.

**Independent review.** Round 1 BLOCKED mixed RQ1/RQ2 gates, inconsistent
denominators, incomplete gold/scoring rules, permissive unknown effects, and an
unenforceable supervisor path. Repairs fixed the denominator at 48, froze blind
gold and scorer equivalence, required 100% decisive-effect ownership, selected
real assets, and pinned a local full-context Qwen/llama.cpp supervisor. Round 2
found only an overlapping Counts/State Diff decision and a missing generation-
token reservation. Round 3 returned PASS after Counts/State Diff became
non-gating and the plan froze
`rendered_prompt_tokens + 2,048 <= 65,536`, with no truncation or context shift.

**Admission and next action.** Only the real preflight is admitted: one coding
perturbation/repair pair and one auto-research pair, each crossing a genuine
goal and top-level-session boundary, followed by one Full Trajectory and one
Full Raw supervisor call. Runner implementation is limited to the three named
commands needed for that path. The 48-episode matrix, paper effect claim, and
phase transition remain forbidden until the real outputs pass independent
result review. No Git operation occurred.

### Node B13 — Static RQ1 preflight execution and independent result review

**Context.** 2026-07-20T01:28:32-07:00; EXPERIMENT_GATE execution/result node;
status: terminally blocked. Owner directory:
`experiment-20260720T003908-0700/`.

**Execution.** Attempt 1 failed before an Agent session because the DynamicUser
could not traverse the repository-owned workload parent. The controller was
repaired to copy frozen workload bytes into a private read-only runtime tree.
Attempt 2 completed two genuine Codex 0.144.6 sessions over the official
SWE-bench Verified `pytest-dev__pytest-10051` base and retained exact quiescent
H0, prior-goal, target-start, and target boundaries. The first valid episode
produced 956,130-token Full Raw and 1,215,415-token Full Trajectory prompts,
both above the frozen 63,488-token input ceiling. The protocol required an
immediate stop; no repaired sibling, research pair, supervisor inference, or
full matrix ran.

**Independent result review.** The fresh reviewer confirmed the stop and exact
boundary capture but BLOCKED the experiment. The current constructor's
78-changed-path union check is weaker than the approved operation/goal/version/
validation/gold/lineage closure. It also mis-resolved numeric decoded `dirfd`
paths, attached false workspace reads, left genuine fast syscalls unbound due
to stdout-arrival action timestamps, leaked `perturbed` and condition labels,
and lacked the frozen scorer. The static token result applies only to this
redundant constructor and is not a universal lower bound.

**Decision.** Close the approved static-full-context plan. The result is valid
only as a capture/interface dependency finding. It supplies no pathology,
diagnosis, evidence-localization, intervention, or representation-effect result.
The 48-episode matrix is forbidden. A queryable experiment must be planned and
reviewed as scientifically distinct work.

### Node B14 — Closest graph/retrieval work and source-contract repair

**Context.** 2026-07-20T01:59:52-07:00; EXPERIMENT_GATE literature/source
dependency node; status: completed, no model run admitted. Detailed literature
record:
`literature-20260720T015952-0700/literature-report.md`.

**Closest-work result.** AgentTether already provides Transition Units, a
dependency-aware Critical Transition Graph, graph-model/run-local failure
localization, repair memory, and intervention. AggAgent already provides
full-fidelity on-demand navigation over long trajectories through search and
exact segment reads. DyG-RAG and HippoRAG establish event-centric temporal
graphs, time-aware traversal, and PPR graph retrieval. Therefore graph
representation, graph-guided diagnosis, interactive trace navigation, temporal
graph retrieval, and PPR are rejected as novelty.

**Surviving claim and baseline.** The remaining falsifiable delta is whether
exact persistent-workspace effects across independent top-level sessions and
goals add diagnostic evidence beyond run-local graphs and improve an automatic
supervisor over an equal-budget, AggAgent-style full-fidelity Raw interface.
AgentTether is the closest structured diagnostic competitor on compatible
failed-run cases. State Diff and Counts remain reduced controls; OCPM and Full
HTIR retain their mechanism/domain-specific roles.

**Source repair.** `agent-session` now retains native tool-result end times and
pairs Claude/Codex calls by source ID. The research adapter reads retained
Codex rollout logs through `agent-session`; decoded directory FDs are resolved
per syscall. A development replay of the retained blocked episode produced 31
tool/environment actions and 1,505 selected records, covered the 78 changed
paths, and left zero selected system effects unbound. Tests pass across
`agent-session`, `agentvis`, and `agentpprof`. This path/time repair has not yet
implemented the stricter process-subtree ownership rule required by the next
plan. It does not resurrect B13 and is not paper evidence.

**Next action.** Specify a minimal neutral broker with common Raw
`search/read_record/read_range` tools and only deterministic
`action_context/artifact_history/goal_diff/effects` conveniences in the proposed
condition. Freeze one source store, neutral IDs, complete byte/token/tool-call
accounting, blinded gold, and a working scorer. Submit that new two-domain
preflight plan to fresh independent review before any supervisor call.

### Node B15 — Queryable RQ1 preflight plan and three-round review

**Context.** 2026-07-20T02:13:17-07:00; EXPERIMENT_GATE plan node; status:
approved in independent Review Round 3. Owner directory:
`experiment-20260720T021317-0700/`.

**Plan.** The scientifically distinct experiment compares one AggAgent-style
full-fidelity Raw interface with one Workspace Trajectory interface over a
byte-identical neutral source store. Both expose scope listing, frozen ROUGE-L
search, exact record reading, and bounded contiguous ranges. Trajectory adds
only `artifact_history`, `goal_diff`, and source-backed `effects`; it has no
generic action-context shortcut, ranking, anomaly score, semantic label,
hotspot, recurrence, or validation helper. Qwen3.6-27B, llama.cpp, decoding,
context/output/tool/byte/token limits, search serialization, continuation,
commands, blinded gold, manipulation audit, scoring, and vetoes are frozen.

**Independent review.** Round 1 BLOCKED a proposed-only generic
`action_context` confound, asserted rather than executable system ownership,
circular gold using hidden intervention provenance, incomplete scoring, and
unfrozen execution/search/budgets. The plan removed `action_context`; specified
native call/result intervals, exact command/CWD and process-subtree ownership,
decoded `dirfd`, syscall success, concurrency, and `unknown`; froze blinded gold
before a separate manipulation audit; defined alternate evidence/path sets,
earliest/intervention/confidence/abstention scoring; and pinned all execution
parameters and commands. Round 2 found one contradiction saying repaired
siblings were available to gold experts. After restricting them to the
post-gold manipulation auditor, Round 3 returned PASS.

**Admission.** Only the declared mechanics preflight is admitted: one excluded
SWE-bench Verified development episode, one excluded OR-Space episode, and one
Raw plus one Trajectory supervisor run per domain. It can verify source,
blinding, broker, budget, scoring, and two-domain execution mechanics. It cannot
support accuracy, superiority, diagnosis, generalization, or any paper-level
effect. Next: implement only the three frozen CLI paths and required source
ownership, run fixtures, then execute this bounded preflight.

### Node B16 — Queryable RQ1 source/broker preflight and blinded-gold handoff

**Context.** 2026-07-20T04:09:36-07:00; resumed EXPERIMENT_GATE execution
node under B15; parent `experiment-20260720T021317-0700`; status: incomplete at
the external-participant boundary. The current result record is
`experiment-20260720T021317-0700/result.md`.

**Question and entry.** Can the approved two-domain mechanics path reach the
independent-gold boundary with real source stores, exact system ownership, a
fair Raw/action namespace, the frozen model endpoint, and a condition-neutral
labeling handoff, without invoking a supervisor early? This node resumed the
innermost incomplete B15 execution after rereading `docs/user-instruction.md`,
this step report, the approved plan and three-round review, canonical design,
implementation and evaluation frontiers, and the retained raw attempts.

**Inputs and method.** Attempt 01 and attempt 02 used real Codex 0.144.6
sessions over one SWE-bench Verified coding workspace and one OR-Space
auto-research workspace, each with four exact ext4/cgroup boundaries and two
top-level sessions. The repair retained source-native call/result time,
`strace -f --decode-pids=pidns` process creation/exit and file records, exact
argv/CWD matching, clone-time-constrained host-PID subtrees, decoded directory
FDs, and successful syscall results. The broker and scorer used the approved
Rust CLI path; the model/template/tokenizer check contacted the pinned local
Qwen3.6-27B llama.cpp server but did not call completion.

**Results and raw evidence.** Attempt 01 capture passed but its source
projection was invalid because tracee-namespace child PIDs could not prove
subtree ownership. Its coding store had 348,336 Raw records, 27 actions, and
4,143 unbound workspace effects; the auto-research store could not faithfully
bind result/test effects. Attempt 02 passed capture and strict store
construction. The diagnostic coding store contains 640,208 Raw records, 38
actions, and 1,638 effects; the diagnostic auto-research store contains 169,474
Raw records, 20 actions, and 101 effects. All target actions have observed or
no-effect closure. Independent set checks found zero duplicate Raw IDs, zero
missing action/effect Raw references, and zero missing boundary Raw references.
The exact hashes and attempt paths are recorded in the child result file.

The parser now handles Codex nested JavaScript-like `exec_command` wrappers,
embedded `apply_patch`, array-valued outputs, and native result timestamps. Raw
search, exact record, and exact range responses now return canonical action IDs
supported by each Raw ID, removing a condition asymmetry in the required output
schema. `load_store` rejects duplicate Raw/action IDs and missing action,
effect, or boundary references. The optimized CLI build succeeds;
`agent-session` passes 11 tests, `agentvis` 28, `agentpprof` 14, and the
collector 205 non-ignored unit/integration tests. The pinned model health,
tool-bearing chat template, and tokenizer endpoints pass.

`experiment-20260720T021317-0700/raw/preflight/gold-blind/` contains an
unlabeled annotation guide, independent expert form, adjudication form, and
JSONL template with exact target action orders. It exposes neither assignment
values nor sibling identities. Labelers must receive a clean filesystem view
of only this material and the two diagnostic stores; repository-wide access
would break the blind.

**Scientific impact and decision.** This is dependency-only progress and does
not test RQ1. It establishes that the approved source, parser, broker, scorer,
and model paths can reach the participant boundary in both domains. It does not
establish diagnosis quality, representation superiority, generalization, or
even manipulation validity. The approved plan requires two qualified human
experts and one third blinded human adjudicator before supervisor inference;
Agent or root-authored labels would violate the truth contract. The root
therefore preserves the ambitious Raw-versus-Trajectory comparison and does not
replace gold with a cheaper proxy.

**State updates and next action.** `docs/design.md` now matches the frozen
three-query interface, `docs/evaluation.md` records the current RQ1 boundary,
and `docs/questions-for-author.md` records the external-participant handoff.
When the two independent submissions and adjudication return, freeze and hash
the scorer-compatible gold, audit closure/parity for every accepted fact,
perform the separate post-gold manipulation audit, run exactly four supervisor
cells, and invoke a fresh result reviewer. Reopen B16 immediately if a human
submission reveals guide ambiguity, evidence insufficiency, or source closure
failure; do not edit labels from hidden provenance. No Git operation occurred
because BOOTSTRAP step 0001 remains incomplete.

### Node B17 — Clean blinded-evidence archive and handoff verification

**Context.** 2026-07-20T04:19:12-07:00; resumed EXPERIMENT_GATE dependency
node under B16; parent `experiment-20260720T021317-0700`; status: completed as
an external-handoff dependency, with B16 still incomplete.

**Question and entry.** Can the two diagnostic episodes be delivered to the
three required human participants through a clean filesystem view that is
self-contained, byte-faithful to the verified source stores, and excludes both
repaired siblings and hidden manipulation provenance? This node resumed the
innermost incomplete experiment after rereading `docs/user-instruction.md`, the
approved plan, current result, blind guide, author question, and B16 record. It
does not change the experiment, generate gold, or call a supervisor.

**Inputs and method.** The handoff uses only the five unlabeled files under
`raw/preflight/gold-blind/` and the verified diagnostic stores
`attempt-02/stores/e-mxk0i47n5k/` and
`attempt-02/stores/e-p8f9lghqxh/`. Source-type enumeration confirmed that the
stores already contain the complete native session, system trace, workspace
snapshot/archive, boundary manifest/proof, evaluator/specification, and
worker-visible task/skill/harness bytes required by the approved plan. The
README was clarified so original capture directories are explicitly excluded.

**Results and raw evidence.** The clean archive is
`experiment-20260720T021317-0700/raw/preflight/agent-nebula-rq1-gold.tar.zst`,
25,867,752 bytes with SHA-256
`bf1de475f6f6ca9e7c1b2d7647a68330d993c5c95087f4ad7a3f5767ef13cbed`.
It has one root, five guide/template files, and exactly two four-file evidence
stores. A fresh temporary extraction reproduced every store file byte-for-byte,
matched each `raw.jsonl` and `actions.jsonl` hash against `store.json`, parsed
all JSON/JSONL, confirmed the four exact boundary names and target action
orders, and found no repaired-sibling ID, hidden-provenance path, device, pipe,
or symlink. The diagnostic stores contain none of the constructor's forbidden
assignment/mechanism terms. No human submission, adjudicated label,
manipulation audit, supervisor transcript, or score exists.

**Scientific impact and decision.** This is necessary logistics and source
integrity, not research evidence. It removes repository-wide access and
accidental sibling inclusion as practical threats to the blind, but it neither
tests RQ1 nor changes any claim, baseline, workload, metric, or algorithm. The
root rejects substituting Agent labels or inferring labels from the hidden
sibling because either would violate the approved truth contract.

**State updates and next action.** The child result now records the archive,
hash, source coverage, and extraction checks. B16 remains at the same external
participant boundary: distribute the archive separately to two qualified
experts, obtain independent submissions, give only those submissions and the
same archive to a third blinded adjudicator, then freeze and hash the completed
gold. Only after that may the post-gold manipulation auditor and four planned
Raw/Trajectory cells run. No Git operation occurred because step 0001 is still
incomplete.

### Node B18 — Versioned artifact-lifecycle plan-conformance repair

**Context.** 2026-07-20T04:35:22-07:00; resumed EXPERIMENT_GATE real-preflight
repair under B16; parent `experiment-20260720T021317-0700`; status: completed
as a pre-inference implementation repair, with B16 still incomplete.

**Question and entry.** Does the implemented Trajectory condition actually
engage the versioned artifact lifecycle frozen in the approved plan, without
changing the hypothesis, baseline, evidence, budget, query count, or output
task? A source-to-plan audit found a concrete contradiction: the design and
plan required artifact versions and delete/recreate separation, while
`artifact_history` used a permanent path-alias map. The same code also reduced
`goal_diff` to one path-state comparison and returned no explicit unknown
candidate records. This would invalidate mechanism engagement if left until
the four condition runs.

**Inputs and method.** The repair changes only deterministic derived queries in
`agentvis/src/research.rs`. It seeds active artifact identities from the exact
`h0` boundary, then processes source-backed effects in monotonic action/source
order. Read preserves a version; write advances it; rename preserves identity
and changes path; delete terminates identity; recreate allocates a new identity;
and successful rename-overwrite terminates the displaced identity. An effect
with missing prior state, create-on-existing ambiguity, missing rename source,
or unknown operation remains unresolved rather than inheriting a path alias.
The projection is lazily computed once per loaded store and shared by all
queries. `goal_diff` compares exact identity participation in each requested
scope while also returning each scope's boundary state changes. `effects`
returns the versioned effects and exposes temporal overlaps with unbound Raw
records only as explicitly unknown candidates for an unknown action.

**Results and raw evidence.** Three permanent tests cover rename plus later
path reuse, identity continuity across a cross-scope rename, and temporal
filtering of unknown candidates. `agentvis` passes 30 library tests and
warning-free Clippy. A temporary read-only real-data check loaded and
hash-verified both attempt-02 diagnostic stores, evaluated `goal_diff(g1,g2)`,
evaluated `effects` for all 58 actions, and evaluated twelve distinct affected
paths per domain; it passed in 17.08 seconds including parsing 809,682 Raw
records. The temporary test was removed after execution; the three general
mechanism tests remain. Because the projection is derived after store loading,
the two source-store hashes and blinded archive hash are unchanged.

**Scientific impact and decision.** This repair makes the executable mechanism
match the already reviewed algorithm; it does not revise the treatment or add
a pathology-aware feature. No generated semantic label, threshold, recurrence
similarity, anomaly score, importance weight, or learned ranker was introduced.
The exact same Raw facts remain retrievable in the baseline. It therefore does
not require a new experiment plan, but it is still dependency-only and cannot
be presented as an RQ result.

**State updates and next action.** `docs/evaluation.md`, `docs/implementation.md`,
and the child result now state the executable lifecycle semantics and the
unchanged human-gold boundary. B16 next requires two independent qualified
expert submissions and one blinded human adjudication from the clean archive.
After gold is frozen, closure/source parity must be reviewed against every
accepted action and lineage before any supervisor completion call. No Git
operation occurred because BOOTSTRAP step 0001 remains incomplete.

### Node B19 — Exact-boundary reconciliation and algorithm ad-hocness audit

**Context.** 2026-07-20T04:56:07-07:00; resumed EXPERIMENT_GATE
plan-conformance audit under B16; parent
`experiment-20260720T021317-0700`; status: completed as a pre-inference
correctness repair, with B16 still incomplete.

**Question and entry.** Does the derived lifecycle reach every retained exact
workspace state, and does the Raw/Trajectory comparison isolate organization of
the same evidence rather than a hidden label-aware heuristic? This node followed
the user's request to explain the algorithm, strongest baseline, and ad-hoc
risk. The root reread `docs/user-instruction.md`, the open author question, the
approved plan, formal design, current implementation, related-work baseline
audit, child result, and B16--B18 records. `research-experiment-design` supplied
the baseline/fairness standard. The node does not change the hypothesis,
pathology definitions, baseline families, workloads, metrics, budgets, model,
gold contract, or output task.

**Inputs and method.** Source-to-implementation comparison found that the
formal algorithm allowed exact quiescent boundaries to update or validate
artifact state, while the executable projection used only `h0`; later manifests
were returned separately by `goal_diff`. The repair replays actions in explicit
scope order and reconciles predicted existence/path state after `g1`, the
environment transition, and `g2`. An owned mutation receives a boundary anchor
without a second revision increment. An unowned content replacement terminates
the old identity and creates a distinct boundary-observed identity; a missing
create/delete effect is recorded analogously. Complete-manifest hash/count Raw
records support path absence. `research-store --verify` and
`research-supervisor` now reject any replay/boundary discrepancy before model
inference. The audit also traced every derived relation family back to common
Raw IDs and checked current vendor scope.

**Results and raw evidence.** Three permanent tests cover attributed mutation
anchoring, unexplained replacement with identity split and preflight veto, and
end-boundary proof for removal. Together with B18's lifecycle tests, the
`agentvis` library now has 33 passing tests; warning-free Clippy passes. A
temporary read-only test loaded and hash-verified both attempt-02 diagnostic
stores, replayed all 809,682 Raw records and 58 actions through all four exact
states, and found zero boundary discrepancy in 16.92 seconds. The temporary
test was removed. The immutable store hashes and clean archive hash remain
unchanged. The Trajectory relations still contain only source-linked action,
artifact, scope, version, path, and boundary facts; all supporting Raw IDs are
available through the common Raw interface. A separate temporary audit
enumerated every affected path, every action-effect answer, and all three
ordered scope-pair diffs for both real stores and recursively checked every
returned `raw_id/raw_ids` against the common Raw-ID sets. It found zero
inaccessible reference in 17.49 seconds and was removed after the run. No
completion endpoint, label,
prediction, score, or manipulation audit was produced.

The audit also identified honest residual scope and risk. `version` is an
ordered mutation revision rather than proof that every write changed bytes;
exact content is anchored at boundaries. The selected three query plans,
AggAgent-style ROUGE-L search, and one resource-budget point remain hand-chosen
and require later ablation/budget curves. The admitted episodes are Codex-only:
`agent-session` supports other vendors for the product path, but research-grade
Claude/Gemini source-record/action/effect binding is not yet qualified. These
limitations do not invalidate this two-episode Codex mechanics preflight, but
they preclude a cross-Agent result claim.

**Scientific impact and decision.** This closes a mechanism-engagement defect
that could have made a later positive result uninterpretable; it is still
dependency-only and adds no RQ evidence. The root keeps AggAgent-style Full Raw
Retrieval as the one strongest main baseline and treats Final State, summaries,
Counts, State Diff, and session/target-only views as controls. OCPM,
AgentTether, and Full HTIR remain compatible-slice mechanism comparisons for a
later effect study. The repair makes the existing approved treatment more
faithful rather than broadening it, so the experiment plan is unchanged.

**Review, state updates, and next action.** A requested fresh cross-Agent code
review could not be dispatched because the task's collaboration-thread quota
was exhausted; the root therefore performed the source/plan/code audit directly
and does not call it independent review. `docs/design.md`,
`docs/implementation.md`, `docs/evaluation.md`, and the child `result.md` now
record boundary reconciliation, mutation-version semantics, Raw information
parity, and Codex-only qualification. B16 remains at the independent-human-gold
boundary. Completion still requires two independent expert submissions, one
blinded adjudication, closure/parity audit for accepted facts, the separate
post-gold manipulation audit, exactly four Raw/Trajectory cells, and a fresh
result review. No Git operation occurred because BOOTSTRAP step 0001 remains
incomplete.

### Node B20 — Author-directed closure of human-gold experiment

**Context.** 2026-07-21T01:58:44-07:00; resumed EXPERIMENT_GATE scientific
disposition; parent B16/B19 and
`experiment-20260720T021317-0700`; status: human-gold branch closed and
replacement experiment selection in progress.

**Question and entry.** The author instructed: “不要考虑人工标注, 想别的方案实验”
and then explicitly rejected the two-expert plus third-adjudicator requirement,
requesting another trajectory or benchmark experiment. The root reread
`docs/user-instruction.md`, the former `docs/questions-for-author.md` closure
record (subsequently removed), the complete
`docs/idea-story.md`, the current evaluation frontier, the approved plan, the
preflight result, and B15--B19 before disposing the conflict. The newer
instruction governs execution and is recorded verbatim in
`docs/user-instruction.md`.

**Inputs and method.** The old branch had reached a verified source/broker
mechanics boundary but had made no supervisor call. Three alternatives were
considered: continue recruiting humans, substitute Agent labels, or change the
estimand to an automatically verified causal outcome. The first violates the
new author instruction. The second would preserve the file format while making
gold circular and is therefore rejected. The third keeps automatic oversight
as the consumer and tests it through real benchmark outcomes and replayed
interventions.

**Results and raw evidence.** The old experiment result is now explicitly
marked superseded and closed without inference. Its 809,682 Raw records,
versioned artifact lifecycle, exact-boundary checks, and Raw/Trajectory parity
remain dependency evidence only. The blind archive is not a label source and
will not be distributed. The former author-question handoff was marked resolved
and then removed because participant recruitment is no longer part of the
active study. No diagnosis or RQ result is inferred from this closure.

**Scientific impact and decision.** The four-label classification estimand and
expert evidence-set scoring no longer define RQ1. During BOOTSTRAP the root will
replace them with a stronger behavioral test: an automatic supervisor observes
a paused multi-session workspace, produces or selects an intervention under a
fixed budget, and the same benchmark worker continues from the checkpoint.
Official executable graders and counterfactual replay, not an annotator or
judge model, determine whether the intervention helped. This preserves the
paper's process-level scalable-oversight objective while removing an
unavailable and now forbidden truth source.

**Review, state updates, and next action.** `research-literature-novelty` is
reopened because the RQ outcome and evaluation promise are changing. It will
verify official multi-session workspace tasks, objective graders, available
trajectories, intervention/replay precedents, and matched-budget baselines.
After that evidence is recorded, the root will append a scientific-contract
evolution entry and `research-experiment-design` will submit one revised RQ1
experiment to fresh independent plan review. No Git operation occurred because
BOOTSTRAP step 0001 remains incomplete.

### Node B21 — Objective-outcome benchmark and closest-work audit

**Context.** 2026-07-21T02:04:51-07:00; BOOTSTRAP scientific-contract
revision after B20; status: completed literature/asset audit and admitted one
new experiment-plan direction.

**Question and entry.** Can the project test automatic process-level
supervision without human or Agent-generated semantic gold, using other
trajectories or benchmarks? The root used `research-literature-novelty` and
`research-experiment-design`, reread the complete idea history before changing
the RQ frontier, and searched current primary papers, benchmark sites, official
repositories, task specifications, adapters, and graders. The author
instruction remains hard: no two-expert annotation, no third adjudicator, and
no Agent substitute for them.

**Inputs and method.** Candidate claims were stripped of project terminology
before search. The audit covered active trajectory-grounded reminder injection,
self-supervised harness optimization, causal intervention/replay, shared-context
coding, multi-round persistent-workspace evaluation, scientific
reproducibility, and research-engineering benchmarks. Official artifacts were
locally inspected at pinned revisions for Harness Bench, CORE-Bench, and
RE-Bench. Harness Bench's Codex adapter was traced through its round loop: each
prompt round launches a new `codex exec` while preserving one workspace and
isolated Codex home. Task YAMLs, prompts, hooks, and oracles were inspected for
all multi-round candidates. Tasks with same-conversation semantics or an
LLM-weighted primary outcome were excluded.

**Results and raw evidence.** The detailed report is
`literature-20260721T020451-0700/literature-report.md`. Harness Bench revision
`1025086a446653702b80cfb48babbeec35db6b2c` supplies six deterministic
multi-round tasks suitable for the first matrix, with task 058 selected for a
real checkpoint-fork preflight. SWE-Interact and SWE Context Bench provide
objective coding expansions; CORE-Bench provides 270 scientific
reproducibility tasks from 90 papers; RE-Bench provides seven expensive,
continuous-score research-engineering environments. Static trajectory corpora
such as TraceBench remain parser/load assets rather than decisive causal
evidence because they do not provide a continuation checkpoint.

The closest-work audit also narrowed novelty. Remember When It Matters already
injects trajectory-grounded reminders; RHO already optimizes harnesses without
external labels; SWE Context Bench already evaluates trajectory/summary reuse;
REFLECT already validates attribution through intervention; and Rethinking
Harness Evolution shows why extra search/feedback and same-benchmark tuning are
critical confounds. Therefore the contribution cannot be label-free diagnosis,
reminder injection, harness optimization, trajectory reuse, or replay alone.

**Scientific impact and decision.** H6 replaces H1 as the active hypothesis:
at a frozen persistent-workspace checkpoint, does Workspace Trajectory enable a
fixed-budget automatic supervisor to produce an intervention whose actually
executed continuation receives a better official benchmark outcome than Full
Raw Retrieval, no intervention, and generic matched reflection/search? Every
condition receives a byte-identical checkpoint and the same future official
prompt, supervisor/worker models, and budgets. The supervisor emits one bounded
message or abstains. A fresh worker session executes each fork, and the
unmodified deterministic oracle supplies truth. No pathology macro-F1,
recommendation F1, human agreement, or LLM-judge outcome remains in the active
contract.

**State updates and next action.** `docs/background-related-work.md`,
`docs/idea-story.md`, `docs/design.md`, `docs/evaluation.md`, and
`docs/implementation.md` now identify the human-label program as superseded and
record the closed-loop estimand, controls, workloads, and validity rules. The
next node must write one executable task-058 pause/fork/inject plan, including
exact commands, immutable artifacts, budget parity, leakage vetoes, and
preflight completion criteria, then obtain a fresh independent plan review
before any model or benchmark run. No Git operation occurred because BOOTSTRAP
step 0001 remains incomplete.

### Node B22 — Objective continuation plan and independent review

**Context.** 2026-07-21T02:36:42-07:00; BOOTSTRAP EXPERIMENT_GATE after B21;
child `experiment-20260721T021426-0700`; status: plan accepted for
implementation, while real P0 remains gated by no-model preparation.

**Question and entry.** Can H6 be tested with real alternative trajectories and
benchmark outcomes, without human annotation, Agent substitute labels, or an
LLM judge? The root used `research-experiment-design` to register one fixed RQ,
one Harness Bench mechanism pilot, four checkpoint continuations, objective
outcomes, and a narrow decision rule. No model or benchmark call ran during
planning.

**Inputs and method.** The plan pins Harness Bench revision
`1025086a446653702b80cfb48babbeec35db6b2c`, Codex CLI/model settings, the local
Qwen supervisor blob and llama.cpp revision, six deterministic multi-round
tasks, one task-058 mechanics P0, and a six-task no-intervention headroom gate.
Each block pauses before a fresh official round and compares no intervention,
generic current-state reflection, same-source Full Raw Retrieval, and Workspace
Trajectory Retrieval. The worker actually continues from the frozen workspace;
only the official executable oracle supplies the outcome.

**Independent review and repair.** A fresh read-only reviewer returned BLOCK in
round 1. It found that the current broker still implemented the old pathology
task, exact `session_diff` lacked per-round snapshots, fork paths could leak
condition identity, Agent tools could download the public oracle, the ceiling
gate was weak, and the statistical verdict overstated six fixed tasks. The plan
was repaired with an explicit minimal implementation contract, immutable
post-`after_round` `lstat` snapshots, field-by-field Raw recomputation, one
stable execution slot and worker-visible path set, no-egress model-generated
tools with still-functional trusted Codex transport, an evidence allowlist,
executable-oracle-only grading, one excluded no-op checkpoint for every fixed
task, fixed-task clustered inference, uncertainty-controlled verdicts, and
whole-block failure reruns. Round 2 returned PASS with no remaining plan-level
blocker. The full record is `experiment-20260721T021426-0700/plan-review.md`.

**Scientific impact and decision.** The active experiment now measures realized
continuation utility rather than agreement with semantic labels. A positive
pilot requires both registered interval lower bounds above zero, positive signs
on at least four of six fixed tasks, and no observed harm-count increase over
Raw or Generic. Even that result only admits a held-out coding/scientific-work
expansion; it is not a task-population claim. Raw/generic superiority or higher
harm rejects H6, and an interval crossing zero is inconclusive.

**State updates and next action.** The plan is accepted for implementation, not
for immediate inference. The current Rust research path is explicitly
nonconforming. Next, minimally refactor the existing store/broker and add the
thin Harness Bench driver. `--prepare-only` must construct and verify the store,
snapshots, stable prompts/argv/environment, three broker schemas and frozen
budgets without model calls. Only after that contract passes may the real
task-058 P0 begin. No Git operation occurred because BOOTSTRAP step 0001 remains
incomplete.

### Node B23 — Objective implementation, no-model gate, and real P0 execution

**Context.** 2026-07-21T18:14:04-07:00; BOOTSTRAP EXPERIMENT_GATE after B22;
child `experiment-20260721T021426-0700`; status: implementation and P0 execution
mechanics completed, while treatment engagement remained unverified and the
preregistered six-task headroom gate was running.

**Question and entry.** Can the accepted no-gold protocol be implemented and
executed end to end with real benchmark continuations, while preventing the
controller and worker from observing oracle, retained evidence, or sibling
condition state? The implementation remained within the accepted H6 contract:
no human labels, Agent substitute labels, semantic scorer, or LLM judge were
created.

**Implementation and preparation.** The retained research store now consumes
native Codex sessions and exact per-round snapshots for arbitrary completed
prefix rounds. The supervisor exposes only Generic current-state tools, the
complete allowlisted Raw store, or the same Raw tools plus three deterministic
source-linked trajectory relations. The structured output schema constrains
citations to IDs actually exposed in that call, and all result artifacts are
written atomically. A thin driver reuses the official Harness Bench Codex
adapter, prompts, fixtures, hooks, and executable oracle. Its named no-egress
profile permits normal workspace tools but denies hidden benchmark/evidence
paths, DNS, and network. The no-model `--prepare-only` report passed every
registered construction, recomputation, parity, and fork check with zero model
and benchmark calls.

**Strict real P0 result.** Task `058-multiday-project-state` produced two
distinct prefix sessions, 133 Raw records, and seven native actions with no
unresolved admitted relation. The actual worker-model isolation probe exercised
a shell tool and passed workspace read/write, hidden-path denial, DNS denial,
and network denial. All forks shared the same checkpoint manifest, prompt,
argv, environment, source/model identity, and registered budgets; each official
oracle was run twice with identical results, and the rubric/provider request
count was zero. No intervention, Full Raw, and Workspace Trajectory each scored
0.8594; Generic scored 0.9219. All three supervisors made zero retrieval calls,
so their exposed and returned source-ID sets were empty.

**Failure provenance.** Earlier attempts with an incorrect wrapper path, a
legacy approval flag, a wrongly nested llama.cpp response schema, unexposed
source IDs, and an interrupted zero-filled build were archived under
`raw/preflight/attempts/`. They are retained for audit and excluded from the
accepted result. The final report is `raw/preflight/p0-report.json`.

**Scientific impact and decision.** P0 validates execution mechanics only. It gives
no support for the trajectory mechanism on this checkpoint, and the Generic
fork's higher outcome is contradictory single-checkpoint evidence rather than a
claim. No prompt or algorithm was tuned from this outcome. The registered next
step is one no-intervention development checkpoint for each of the six fixed
tasks. The four-condition effect matrix is admitted only if at least four of
six scores are below 0.95. No Git operation occurred because BOOTSTRAP step
0001 remains incomplete.

### Node B24 — Headroom stop, independent result review, and security boundary

**Context.** 2026-07-21T18:39:49-07:00; BOOTSTRAP EXPERIMENT_GATE after B23;
child `experiment-20260721T021426-0700`; status: current Harness Bench matrix
closed as dependency-only, H6 remains open and untested.

**Question and entry.** Does the fixed six-task workload have enough objective
no-intervention headroom to justify the registered four-condition continuation
matrix, and did the real P0 actually exercise the proposed retrieval treatment?
The root completed all six excluded development checkpoints in their registered
order and then requested a fresh read-only result review. The reviewer did not
act as a semantic annotator and did not run another model or benchmark.

**Observed result.** The six scores were 0.6154, 0.8594, 1.0, 1.0, 1.0, and
0.4994 for tasks 057, 058, 059, 060, 103, and 105. Only 3/6 were below 0.95,
against the preregistered 4/6 admission rule. The aggregate therefore correctly
records `full_matrix_admitted=false`. No effect condition was run, and the
three lower-scoring tasks were not promoted into a post-hoc subset.

**Independent recomputation and protocol audit.** The reviewer recomputed all
six outcomes from the retained official oracle details, verified the fixed
tasks/order/threshold, clean pinned benchmark revision, distinct P0/P1 task-058
prefixes, exclusion of development checkpoints, P0 manifest/prompt/argv/env
parity, actual worker isolation, and absence of result-selective reruns. The
headroom gate and stop decision received PASS. The complete review is
`experiment-20260721T021426-0700/result-review.md`.

**P0 correction.** The independent review found that Generic, Raw, and
Trajectory each used zero tool calls, zero returned evidence, and zero exposed
source IDs. Thus P0 did not exercise either retrieval treatment and is BLOCKED
as a retrieval-mechanism preflight; it only passed checkpoint/fork/isolation/
continuation mechanics. Generic also mentioned the supervisor-only
`read_current` tool in worker-facing advice. In addition, `oracle_twice`
compared two canonical results but retained only the first payload plus a count,
and `rubric_provider_requests=0` is a hard-coded assertion rather than measured
transport accounting. These are mandatory repairs for a scientifically
distinct future protocol, not reasons to tune and rerun the inspected tasks.

**Security incident and repair.** Runtime Codex homes retained copied
`auth.json` files. The worker sandbox could not read them, so condition fairness
and headroom scores are unaffected, but the artifacts were not publishable.
The root deleted every runtime credential file without reading it, added
post-adapter cleanup in a `finally` path, and verified none remain under
`docs/tmp`. A concurrent/local commit `47893046f` nevertheless contains nine
credential blobs. The tracked origin branch contains zero. The local commit
must be rewritten before push so those blobs are not reachable from the remote
tip; a deletion-only child commit is forbidden.

**Scientific impact and decision.** The current six-task Harness Bench
configuration has an observed ceiling boundary and cannot test H6 as planned.
H6 is inconclusive, not refuted, because the condition matrix never ran and P0
never engaged retrieval. The next admitted direction is a newly preregistered
objective cross-domain checkpoint-continuation workload using structurally
selected SWE Context Bench related-task sequences and CORE-Bench scientific
reproduction tasks, official tests/evaluators only, mandatory matched tool
engagement, and both oracle payloads/hashes retained. Selecting only
057/058/105, changing 4/6 to 3/6, rerunning until low scores appear, weakening
Generic, or using P0/P1 in effects is prohibited outcome-driven tuning.

### Node B25 — H6 paper migration and twelve-round WRITE gate

**Context.** 2026-07-21T18:55:46-07:00; BOOTSTRAP WRITE_GATE after B24;
status: completed expression, citation, and meaning-preservation checks.

**Question and entry.** Can the submission-shaped paper be migrated from the
superseded human-label diagnosis experiment to the objective H6 intervention
contract without overstating the incomplete Harness-Bench result? The root
froze entry snapshot `a6f58cfe3d42634d059c727cebdc46da8793f6c5`, retained
the user prohibition on human or Agent substitute labels, and ran the complete
twelve-round `iter-refine-writing` workflow. Round reports live in
`iter-refine-writing-20260721T185546-0700/`.

**Inputs and method.** Independent read-only reviewers checked macro and micro
structure, section conventions, logic, abstract/introduction correspondence,
cross-paper facts, sentence structure, word choice, terminology/information
flow, six-page organization, citations, and final meaning preservation. The
root applied each accepted repair, compiled after every round, and did not run
another model continuation or benchmark task. The citation gate ran the
mandatory external metadata verifier and read original PDFs for every newly
cited benchmark.

**Paper contract.** The paper now defines objective intervention utility as an
executed-continuation outcome under matched resources. RQ1 registers
Workspace-Trajectory minus Full-Raw as the primary estimand,
`Gain(Trajectory)-Gain(Generic)` as the mandatory competing contrast, and No-op
as the realized benefit/harm reference. RQ2 removes `artifact_history`,
`session_diff`, and `effects` only after RQ1 support; earlier-session source
scope is a separate matched contrast. RQ3 remains closed until disjoint coding
and scientific-work families independently pass structural, headroom, and
historical-evidence engagement gates.

**Accuracy repairs.** Full Raw now includes sanitized native sessions, prior
official prompts and worker-visible logs, and immutable checkpoint/snapshot
bytes and manifests. The action-effect state distinguishes `observed`,
qualified `no_effect`, and unresolved `unknown`. Source IDs, oracle naming, and
completed-versus-future repair tense are consistent. The completed run is
reported as retaining only the first oracle payload plus the invocation count;
post-run code repairs configure future dual-payload hashing and credential-home
purge, and the inspected tasks were not rerun.

**Results and citation gate.** The paper preserves 133 Raw records, seven
actions, scores 0.8594/0.9219, all six headroom scores, the failed 3/6 versus
4/6 gate, zero historical-evidence calls, no effect matrix, and unanswered RQ1.
Sixteen bibliography entries are verified and annotated; fifteen are active and
one is explicitly unused. Four missing benchmark citations were added from the
original Harness-Bench, SWE-ContextBench, SWE-INTERACT, and published
CORE-Bench sources. The PDF compiles with six content pages plus one
reference-only page and no undefined citation or reference.

**Independent meaning-preservation result.** The final reviewer found no
material drift. Intentional differences from the entry paper correct earlier
contract errors: co-primary wording became the registered primary/mandatory
contrasts; prospective query names became the three implemented operations;
`unknown` no longer collapses into `no_effect`; and unverified future repairs
are no longer written as completed-run facts.

**Scientific impact and decision.** H6 remains open, not supported or refuted.
The current paper is an honest experiment-ready statement plus dependency
evidence, not a completed AAAI result. The next gate is an independent outer
audit of paper/code/evidence/security consistency. If that audit passes, the
local credential-bearing commit must be rewritten out of history before a
normal push. The following research node must prospectively qualify a distinct
objective workload; it must not subset or rerun the inspected Harness-Bench
tasks.

### Node B26 — Independent outer audit and publication gate

**Context.** 2026-07-21T20:38:51-07:00; BOOTSTRAP outer audit after B25;
status: scientific audit passed, publication pending local history rewrite.

**Question and entry.** Does the H6 paper, canonical contract, future experiment
implementation, retained evidence, and proposed Git payload consistently remove
human gold and support a benchmark-oracle intervention experiment without
leaking local credentials or unbounded runtime state? A fresh independent agent
reviewed the paper, canonical documents, code, tests, selected raw evidence,
Git ancestry, index, and origin without editing or reading credential contents.

**Findings and repairs.** The audit found and the root repaired four substantive
contract defects: stale co-primary/No-op language, an obsolete four-component
RQ2 ablation, property-graph/goal/system-evaluator expansions not present in the
paper method, and a tool-engagement implementation that originally counted any
call. The final gate counts only successful responses that expose a registered
source ID, with one cost-symmetric required family per condition: Generic
current workspace, Full Raw history, and Workspace Trajectory relation. Empty
queries fail. Three ledger counters and three focused tests cover current-only,
wrong-family, relation-only, and empty-success behavior. Five obsolete
Full-HTIR/human-gold capture files and `docs/questions-for-author.md` were
removed, reducing the inactive implementation by more than two thousand lines.

**Independent result.** The reviewer recomputed the pilot record/action counts,
the four continuation scores, all six headroom scores, and the failed 3/6 gate.
It confirmed that RQ1 remains unanswered, that post-run oracle/credential repairs
are stated prospectively, and that no human or Agent semantic label enters the
outcome. `agentvis` passes 31 tests, `agent-session` 11, `agentpprof` 14; Python
helpers compile; all active citations verify; the seven-page PDF compiles; and
`git diff --check` passes. The full report is
`outer-audit-20260721T203851-0700.md`.

**Security and publication decision.** Origin is safe, but local-only commit
`47893046f` contains nine credential paths and thousands of runtime files. A
deletion-only child commit is forbidden because it would retain those blobs in
history. Before the normal push, clear `docs/tmp` from the index, re-add all
non-Raw reports plus only the audited current-experiment Raw allowlist, exclude
runtime/session/SQLite/cache/credential paths and gitlinks, and amend the
local-only commit so `47893046f` is not an ancestor of the new tip. Publication
remains blocked until the rewritten tree and dry-run push pass the recorded
denylist checks.

**Next action.** After the safe normal push, keep H6 active and preregister a
new objective cross-domain workload qualification. SWE Context Bench is
eligible only if its related tasks preserve one workspace across a genuine
fresh-session boundary; otherwise use SWE-INTERACT or another compatible coding
workload. CORE-Bench is eligible only if the official runner can pause/resume at
a structural boundary and apply its unchanged executable evaluator afterward.

### Node B27 — Recovery and author-directed empirical-study reconstruction

**Context.** 2026-07-21T23:54:53-07:00; BOOTSTRAP EXPERIMENT_GATE after B26;
status: recovered on commit `137b0d7a3`, with the intervention experiment
closed before execution and the scientific contract reopened by explicit
author instruction.

**Question and entry.** The author asked to reduce the claims, stop requiring
the representation to improve an Agent, and study trajectories themselves.
They then fixed a broader empirical objective: determine whether days of Agent
activity become durable, verified progress; characterize rework and
cross-session continuity; study associations with skill and harness use; write
a dedicated empirical-study document with at least five study RQs plus one tool
measurement RQ; and analyze five or six local projects. This is a material
BOOTSTRAP contract change, not an implementation repair to H6.

**Inputs and recovery evidence.** The root reread `docs/user-instruction.md`,
the complete `docs/idea-story.md`, the paper and canonical evaluation state,
the latest B22--B26 records, and current Git state. The safely rewritten and
pushed branch is clean at `137b0d7a3` before this node's new documentation
changes. The subsequent SWE-INTERACT intervention draft and its independent
review remain under `experiment-20260721T212000-0700/`; no real benchmark or
model call was made. The review returned BLOCK on intervention timing,
repository leakage, ITT handling, headroom reuse, source-effect engagement,
regrading feasibility, and missing execution details. Those defects do not
route to repair because the author has withdrawn the improvement/intervention
question itself.

**Scientific impact and decision.** H6 and its four-arm continuation matrix are
superseded without inference. The next paper studies long-running Agent work as
the evolution of persistent artifacts. The central empirical distinction is
activity versus durable and verification-associated progress; Git history is a
supporting observability contrast, not the headline. Source-linked trajectory
reconstruction remains a method contribution and implementation qualification,
not an empirical RQ. The first study is a multi-case analysis, so skill/harness
differences are descriptive associations rather than causal effects. A tool RQ
may compare process-fact recovery from Final Diff, Counts, equal-budget Raw-log
LLM analysis, and trajectory queries, but it must use source-verifiable facts
and no human semantic gold.

**Review, state updates, and next action.** The exact new author prompt was
appended verbatim to `docs/user-instruction.md`. Because the RQ set and central
position changed during BOOTSTRAP, `research-literature-novelty` is reopened
before a new experiment plan. The root will create a Chinese empirical-study
design document, update `docs/idea-story.md` only after disposing the new
literature evidence, qualify five or six distinct local repositories and their
native Agent traces, and send one selected empirical RQ through the complete
`research-experiment-design` loop. Completion requires a real multi-project
result rather than a parser smoke test.

### Node B28 — Closest-work audit for longitudinal artifact progress

**Context.** 2026-07-21T23:59:34-07:00; BOOTSTRAP EXPERIMENT_GATE; parent B27;
status: complete.

**Question and entry.** With intervention utility withdrawn, which parts of a
six-case trajectory study and tool comparison remain scientifically
distinguishable from current Agent-trajectory work? The root reread the exact
user instructions, complete idea history, paper, and previous literature
frontier before reopening `research-literature-novelty`.

**Inputs and method.** The node declared six search branches: coding-Agent
trajectory studies, procedure representations and fingerprints, long-horizon
diagnosis, persistent workspace systems, Agent-authored open-source evolution,
and LLM-as-judge trace analysis. It verified primary papers and official
artifacts, including ASE 2025's thought--action--result study, the ICSE behavior
study, *Beyond Resolution Rates*, TRAJEVAL, HORIZON, AgingBench, AiScientist,
FS-Researcher, AIDev, and the official ProcGrep repository at
`2e8277003dacaa774b5ef61ba150ae03a4f06693`. Full queries, source evidence,
coverage boundary, and baseline handoff are in
`literature-20260721T235934-0700/literature-report.md`.

**Results and raw evidence.** Generic trajectory analysis, action motifs,
validation gaps, rework, behavior fingerprints, persistent file workspaces,
deterministic action search, and broad LLM-comparison claims all have high
same-claim risk. ProcGrep is the mandatory action-only tool baseline: it already
supports local Claude/Codex ingest, canonical atoms, learned procedures,
fingerprints, exact queries, and an LLM comparison. Its standard spine does not
retain stable artifact identity, lifecycle, hierarchy, or cross-session
lineage. Large PR studies cover public repository metadata but not native reads,
transient artifacts, failed validation, or session lineage.

**Scientific impact and decision.** The central empirical claim is restricted
to observable artifact accumulation over independent native sessions: activity
volume is not itself a measure of durability, later reuse, successful-
validation association, rework, attention, or re-grounding. The tool claim is
incremental source-verifiable fact coverage beyond action-only procedure
representations, not a new IR or blanket superiority. Skill/harness effects in
the six local cases are descriptive associations. The local corpus is
supporting and hypothesis-generating; broad AAAI population claims require a
later independent public or prospective corpus.

**Review, state updates, and next action.** The root accepted the narrowed
novelty boundary because it preserves the user's central activity-versus-
progress problem while removing claims directly occupied by primary work. It
updated `docs/background-related-work.md`; no user-authored scientific scope
was deleted. The next node freezes the complete study contract before any rate
is computed.

### Node B29 — Empirical-study contract and H7 disposition

**Context.** 2026-07-22T00:10:47-07:00; BOOTSTRAP EXPERIMENT_GATE; parent B28;
status: complete.

**Question and entry.** Convert the author's scenario into at least five
empirical RQs plus one tool RQ without turning a by-construction reconstruction,
Git omission, visualization, or a weighted score into the main claim.

**Inputs and method.** The root compared the intact Initial Narrative, the
immediately previous H6 intervention narrative, all user instructions, and B28.
It wrote `docs/empirical-study.zh-CN.md` with six empirical RQs and one tool RQ,
operational units, source rules, metrics, cases, baselines, analysis policy, and
non-claims. It updated the current frontiers in `docs/idea-story.md`,
`docs/evaluation.md`, `docs/design.md`, and `docs/implementation.md`.

**Results.** RQ1 studies activity to observable artifact durability, reuse and
validation association; RQ2 validation dynamics; RQ3 rework and convergence;
RQ4 cross-session continuity; RQ5 attention allocation; RQ6 skill/harness
association; and RQ7 incremental fact coverage against Final State, Counts,
official ProcGrep, and bounded Raw-log LLM analysis. “Durable verified
progress” is a vector and conjunction, not an arbitrary weighted scalar.
Complete distance/survival curves replace fixed event windows. Event time is
authoritative; Git supplies final-state evidence only.

**Scientific impact and decision.** H6 is superseded without execution. H7
predicts that activity counts do not collapse the durability, reuse,
validation, rework, and continuity dimensions, and that stable artifact
identity adds fact coverage beyond an official action-only representation. This
is more faithful than both the Initial Narrative and H6: it retains the initial
persistent-workspace unit and automatic measurability, directly answers the
author's activity-versus-progress anxiety, and removes an intervention
requirement the author explicitly withdrew. Reopen interventions only on
explicit author instruction; revisit broad empirical scope after source
qualification or closer same-claim work.

**Review, state updates, and next action.** The canonical docs now agree on H7,
but the reader-facing paper still expressed H6. `research-experiment-design`
requires the selected RQ to appear in the paper. The experiment gate therefore
does not manufacture an RQ1 plan against a stale paper; it transitions to the
WRITE gate to express the accepted contract, then a new step will run RQ1.

### EXPERIMENT_GATE transition after B29

The central position and RQ set changed by explicit author instruction during
BOOTSTRAP. Literature grounding completed, but no RQ experiment was admitted in
this gate because the paper did not yet contain the new RQs. The obsolete
SWE-INTERACT plan remains reviewed and unexecuted; repairing it would answer a
withdrawn question. The exact next handoff is to WRITE_GATE: express H7 and all
seven RQs in the paper without inventing result values, compile it, and then
perform the step-level independent audit.

## WRITE_GATE — H7 paper reconstruction

**Entry and alignment.** The root reread `docs/user-instruction.md`, the
complete `docs/idea-story.md`, B28--B29, and all current canonical docs.
`docs/questions-for-author.md` is absent in this worktree and therefore was not
used as evidence. The permitted BOOTSTRAP change is expression of
the author-fixed H7 contract. No result value may be invented, and the old H6
intervention findings remain historical mechanics rather than active results.

### Node B30 — Reader-facing paper updated to the empirical-study contract

**Context.** 2026-07-22T00:14:00-07:00; BOOTSTRAP WRITE_GATE; parent B29;
status: complete with one recorded skill incompatibility.

**Question and method.** Replace the stale three-RQ intervention paper with a
submission-shaped account of the accepted activity-versus-progress study. The
paper now contains the central user problem, persistent-workspace unit,
deterministic source projection, six empirical RQs, one tool RQ, fixed six-case
corpus, baseline roles, source/causal limits, and explicit placeholders for
missing results. Two closest-work citations were added from verified primary
sources: ASE 2025 and ProcGrep/arXiv 2606.16988.

The required full `iter-refine-writing` component was inspected but could not
enter: its First Step hard-rejects any paper-level RQ set outside two to five,
while the author explicitly requires at least five empirical RQs plus one tool
RQ. Collapsing or deleting RQs to satisfy a writing tool would violate user
authority and the skill's own prohibition on changing RQ meaning. The component
is therefore skipped with this failed entry condition; no claim is made that
its twelve-round loop ran. The root performed the contract rewrite directly
and leaves writing-style polish to a future compatible pass.

**Results and evidence.** `docs/paper/main.tex` is now five pages and compiles
with `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`. The final
run resolves all citations and cross-references. B32 subsequently removes the
remaining overfull equation box and visually validates both method figures;
two underfull prose warnings do not invalidate the contract or build.
`docs/paper/main.pdf` is the compiled artifact.

**Scientific impact and decision.** The paper no longer claims intervention
utility, human/LLM diagnostic gold, or a new general trajectory language. It
states no empirical result before the real run. The contribution and case-study
findings are separated, Git omission is supporting contrast, and ProcGrep is
positioned as a baseline expected to tie or win action-only questions.

**Review, state updates, and next action.** Canonical docs and paper now agree
on H7. The next gate is REVIEW: a fresh reviewer must audit the contract
transition, literature coverage, writing-skill skip, paper consistency, and
whether a new step may admit RQ1 without silently narrowing the user's seven-RQ
program.

## REVIEW_GATE — Independent audit and BOOTSTRAP closure

### Node B31 — Fresh outer audit of the H7 contract

**Context.** 2026-07-22T00:28:00-07:00; BOOTSTRAP REVIEW_GATE; parent B30;
status: complete; verdict: PASS.

**Question and independence.** A fresh reviewer with no editing or execution
role in B27--B30 audited user fidelity, the narrowed novelty boundary, paper
consistency, the disclosed writing-skill incompatibility, and whether RQ1 can
enter a real experiment. An earlier reviewer invocation was interrupted before
producing an artifact or verdict; it supplied no evidence to the successful
reviewer. The complete successful review is
`outer-audit-20260722T002800-0700.md`.

**Results.** The reviewer found no scientific or executability blocker. It
confirmed six empirical RQs plus one tool RQ, the six-case local corpus,
exclusion of human gold, observational treatment of skill/harness effects,
ProcGrep as the mandatory action-only baseline, and the intentionally narrow
incremental tool claim. It also confirmed that RQ1 has fixed cases, source
admission rules, non-circular dimensions, explicit limitations, and planned
source-linked JSON/CSV evidence. The three ranked non-blocking risks are native
effect coverage, external validity of six author-associated cases, and later
RQ7 baseline coverage.

**Root response and provenance correction.** The root accepts the PASS and
the exact routing recommendation: the next step enters BUILD_AND_EVALUATE with
RQ1 as its sole interpreted experiment, while neutral extraction fields may
support later RQs. Two diagnostic paths mentioned by earlier orchestration
records, `scripts/check_progress.py` and `docs/questions-for-author.md`, are
absent in this worktree; no claim is made that they ran or were read. Their
absence does not alter the user instruction record, scientific contract, or
RQ1 executability.

### Node B32 — Required figures and visual validation

**Context.** 2026-07-22T00:33:27-07:00; BOOTSTRAP REVIEW_GATE presentation
follow-up; parent B31; status: complete.

**Question and method.** The author required that every figure warranted by
the study be drawn. The root used the paper-figure workflow to separate
definition/architecture figures from empirical result figures. It added two
data-free TikZ figures to the paper: (F1) an Agent-action-time schematic
defining durability, later reuse, validation distance, and cross-session
observable re-grounding, and (F2) the native-session to `agent-session` to
artifact-projection data flow. It fixed the projection figure for a
single-column layout and split the effect equation to remove the remaining
overfull box.

**Results and evidence.** `docs/empirical-study.zh-CN.md` now fixes F1--F10,
with one principal question, data source, and rendering form per figure. F3--F10
are deliberately not fabricated: each must be generated by Python/matplotlib
from its frozen RQ CSV/JSON and exported as vector PDF, with source rows and
scripts retained. `latexmk -pdf -interaction=nonstopmode -halt-on-error
main.tex` succeeds, produces a five-page PDF, and the log contains no overfull
box, undefined reference/citation, or LaTeX error. Page 3 was rendered to PNG
and visually inspected; both figures are legible and remain distinct from
numeric evidence.

**Decision and phase transition.** Presentation changes do not alter the H7
contract audited in B31. BOOTSTRAP step 0001 closes on H7: long-running Agent
activity is measured against separate observable artifact durability, reuse,
validation, rework, attention, and continuity dimensions; the tool claim is
incremental source-verifiable fact coverage. The next step is
BUILD_AND_EVALUATE/RQ1: independently review the experiment plan, run one real
repository preflight, execute all six fixed cases, generate F3--F4 from frozen
outputs, and independently review the results before interpreting RQ1.
