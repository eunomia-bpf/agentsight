# Experiment Plan: Randomized Workspace-Trajectory Supervision On SWE-INTERACT

Created: 2026-07-21T21:20:00-07:00
Status: draft; no real benchmark or model call is permitted before independent
plan review accepts this file
Gate: BOOTSTRAP / EXPERIMENT_GATE
Owner hypothesis: H6

## Research Question

Under fixed supervisor and worker budgets, does an automatic supervisor with
Workspace Trajectory Retrieval improve the final executable SWE-INTERACT
outcome beyond an equal-budget Full Raw supervisor and a matched Generic
current-state supervisor?

The treatment is activated at the source-native boundary after `01_plan` and
before `02_implement`.  Step 1 is treatment-blind.  Steps 2--5 and the final
evaluator remain the official benchmark workflow.

## Hypothesis And Falsification

**H6.** Across prospectively selected SWE-INTERACT tasks, Workspace Trajectory
advice produces a higher task-balanced official final reward than Full Raw, and
its gain over No-op exceeds Generic's gain over No-op.

H6 is rejected for this workload if either registered contrast is non-positive,
if the historical-evidence engagement gate fails, or if the result depends on
RF tasks, LLM rubrics, post-outcome task selection, unequal inference budgets,
or changes to the official final evaluator.

This experiment does not ask an annotator or another Agent whether a trajectory
contains a pathology.  It asks whether the advice changes the subsequent
workspace and executable outcome.

## Why This Is The Highest-Value Next Experiment

- The previous Harness Bench configuration validated mechanics but never used
  its Raw or Trajectory tools and failed its preregistered headroom gate.
- SWE-INTERACT is source-natively multi-step: every stage uses a fresh Agent
  conversation by default while sharing one workspace.
- The end of `01_plan` is a task-defined intervention point before production
  implementation, not a failure-dependent timestamp.
- DeepSWE and SWE-bench Pro tasks end in executable tests.  No subjective gold
  or model judge is required.
- A delayed randomized design preserves the official in-memory simulated user
  instead of adding a custom container/process checkpoint system.

A positive result supports a process-level supervision claim in coding.  It
does not by itself establish cross-domain scientific-work generalization; the
24 held-out tasks and a later natively multi-step non-coding workload remain
closed until RQ1 succeeds.

## Official Assets And Pins

- SWE-INTERACT repository:
  `scaleapi/SWE-Interact@b32f98c3b8f76ca65e84341d1f30e5af7135f85d`.
- Harbor runner:
  `laude-institute/harbor@00c19fe2a9c1b9b7ed07efc270412007ac4cb3da`.
- Official task schema: five steps named `01_plan`, `02_implement`,
  `03_handoff`, `04_write_tests`, and `05_test_handoff`, with
  `multi_step_reward_strategy = "final"`.
- Official worker configuration: Codex with `openai/gpt-5.5`, high reasoning,
  matching `run_configs/multiturn/gpt-5p5-high_codex.sh`.
- Official simulated user configuration: `openai/gpt-5.5`, high reasoning,
  through the unchanged task-local `user-server`.
- Supervisor: the already pinned local Qwen3.6-27B Q4_K_M and llama.cpp pair
  used by the completed mechanics pilot.  Their exact hashes, argv, and runtime
  limits must be copied into the preflight report before inference.

No task solution, hidden tests, RF rubric, benchmark result, user persona, or
future-stage artifact is visible to a supervisor or worker.

## Frozen Population And Allocation

The official release has 75 tasks: 25 DeepSWE, 25 SWE-bench Pro, and 25 RF.
RF is excluded before any task-level score because its final evaluator includes
an LLM rubric.  The eligible population is therefore the 50 deterministic-test
tasks.

`allocation-manifest.json` freezes the complete allocation.  Within each
eligible family, tasks are ranked by:

```text
sha256("agentsight-swe-interact-rq1-20260721-v1" + NUL + task_name)
```

- rank 1 in each family: mechanics/engagement preflight, permanently excluded;
- ranks 2--13: RQ1 population, 12 tasks per family, 24 total;
- ranks 14--25: untouched holdout, 12 tasks per family, 24 total.

No task may move between these groups because of build success, cost, No-op
score, supervisor output, or final reward.  A task whose official image cannot
be obtained is reported as an asset failure; it is not replaced.

## Experimental Unit And Delayed Randomization

One experimental unit is one complete official SWE-INTERACT trial.  The unit
contains five fresh top-level Agent sessions over one persistent workspace.

The randomization block is `task x wave`.  Each RQ1 task has two waves.  Within
each block, four independent official trials are assigned one each to:

1. No-op;
2. Generic;
3. Full Raw;
4. Workspace Trajectory.

The assignment permutation and execution order are generated from a frozen
seed and stored behind opaque trial IDs before the block begins.  The adapter
does not read or activate the assignment during `01_plan`.  It reveals the
assigned condition only after the planning step terminates and immediately
before the step-2 Agent receives its instruction.

The four trials do not share an identical prefix.  This is deliberate.  The
official user-server holds conversation state in process memory and exposes no
sampling seed; exact forking would require changing the simulator or cloning
process memory.  Blocked randomization instead estimates the average treatment
effect over worker and simulator stochasticity while leaving the official
environment intact.  Results are called randomized task-block effects, not
same-checkpoint counterfactual effects.

## Conditions

### No-op

The benchmark runs unchanged.  No supervisor process, prompt wrapper, or
evidence store is created in the worker-visible environment.

### Generic current-state supervisor

The supervisor sees the unchanged step-2 instruction and bounded list/read/
search access to the current workspace.  It sees no earlier native Agent
records, user-server transcript, or trajectory relations.

### Full Raw Retrieval

The supervisor receives the same current-workspace tools plus complete bounded
search/read access over the registered step-1 evidence universe:

- the native step-1 Agent session and tool records;
- the worker-visible planning instruction and responses;
- exported user-server questions and replies, but not its hidden persona;
- exact current workspace paths/content and `/tmp/plan.md`;
- Harbor's worker-visible step log and timing metadata.

It receives no derived lifecycle, difference, effect, hotspot, intent, failure,
or semantic label.

### Workspace Trajectory Retrieval

The supervisor receives identical Full Raw membership and tools plus only the
existing deterministic source-linked relations:

- `artifact_history(path)`;
- `session_diff(from_session, to_session)`; and
- `effects(action_id)`.

At this checkpoint there is one completed Agent session, so `session_diff`
may legitimately return no cross-session pair.  It remains registered because
the method is fixed across later stages; an empty result does not satisfy the
engagement gate.  Every non-empty relation field must be independently
recomputable from cited Raw source IDs.

## Supervisor Output And Evidence Engagement

Generic, Full Raw, and Workspace Trajectory emit exactly:

```json
{
  "decision": "INTERVENE or ABSTAIN",
  "message": "worker-facing advice",
  "source_ids": ["retrieved source IDs"]
}
```

`message` is at most 512 model tokens.  `ABSTAIN` has an empty message.  Advice
is appended after the unchanged step-2 instruction in the same neutral wrapper
for all three supervisor arms.

Before an outcome can enter the RQ1 matrix:

- Generic must successfully use a current-workspace read/search tool;
- Full Raw must successfully use a step-1 Raw-history tool;
- Workspace Trajectory must successfully use a non-empty relation query;
- every successful evidence response must expose at least one registered source
  ID; and
- a syntactically valid empty response does not count.

Failure invalidates the mechanics preflight or the entire affected task-wave
block; it is never converted into No-op or abstention.

## Resource And Information Parity

The three supervisor arms share the same model, base prompt, step-2 instruction,
output schema, 65,536-token context, 2,048-token model-output limit,
8,192 returned-evidence-token limit, 32,768 returned-evidence-byte limit,
16 tool-call ceiling, 512-token advice limit, and 20-minute timeout.  Tool
schemas count against the context budget; unused budget is reported, not
credited.

Full Raw and Workspace Trajectory have identical registered source membership.
Trajectory relations are conveniences over those sources, not extra records.
Generic has no history by definition but receives the same total model and tool
budgets.  No-op has no supervisor cost.

Worker model, reasoning effort, step timeouts, network configuration, user
simulator, prompts, environment images, task files, and final evaluator are the
official pinned values for every trial.  Condition names, source stores,
supervisor transcripts, hidden tasks, and sibling outcomes are never mounted
inside the worker workspace.

## Minimal Implementation Contract

Do not extend the 1,468-line Harness Bench fork driver.  Implement one small
Harbor Agent decorator that delegates to Harbor's pinned official Codex Agent:

1. steps 1, 3, 4, and 5 pass through unchanged;
2. at step 2, the decorator reads the opaque delayed assignment;
3. No-op delegates immediately;
4. other conditions call the existing `agentvis research-store` and
   `research-supervisor` paths, validate engagement/output, append the neutral
   advice wrapper, and delegate to the same Codex Agent;
5. after the trial, one deterministic collector records official results and
   resource ledgers.

Use `agent-session` for native session parsing and the existing Agentvis store;
do not introduce another event IR, benchmark schema, database, web frontend,
fork engine, process checkpoint layer, or semantic classifier.  The adapter may
depend on the pinned official Harbor package because Harbor is the benchmark
runner.  It must print live progress and write machine-readable records.

The initial adapter plus tests should remain below 500 non-generated source
lines.  Crossing that boundary requires plan-review justification that the
extra code enforces a registered validity invariant rather than convenience.

## Preflight And Headroom Gates

### P0: mechanics and engagement

Run one four-condition wave on each of the two frozen preflight tasks.  These
eight trials are permanently excluded from every effect estimate.  P0 passes
only if:

1. Harbor runs five fresh Agent sessions over one shared workspace;
2. assignment is absent from every step-1 prompt, environment, tool response,
   source path, and user-server message;
3. step-2 assignment activates exactly one registered condition;
4. all three supervisor arms satisfy their condition-specific engagement gate;
5. Raw and Trajectory source membership hashes match;
6. every returned relation is recomputed successfully from cited Raw bytes;
7. the worker sees the unchanged official instruction plus at most one neutral
   advice wrapper and cannot read supervisor-only state;
8. RF rubric/provider calls are zero;
9. the official final evaluator returns a finite reward, and a second official
   regrade of the unchanged archived trial yields the same payload; both
   payloads and hashes are retained; and
10. all task/revision/image/prompt/model/config hashes and actual resource
    ledgers are retained.

Any failure blocks the main experiment.  Outcomes from P0 may be inspected only
for mechanics; they cannot change queries, population allocation, budgets, or
the headroom rule.

### P1: prospective headroom

After P0 passes, run only the first-wave No-op trial for all 24 frozen RQ1
tasks.  The main matrix is admitted only if at least 12 of 24 official rewards
are below 1.0.  No task is removed or replaced.  If the gate passes, these 24
No-op trials remain the registered No-op cells for wave 1; the other wave-1
conditions and all four wave-2 conditions then run.  If it fails, stop and
report the full fixed task vector.

This gate controls whether the workload has room for an intervention; it does
not select a favorable subset.

## Planned Runs

| Group | Tasks | Waves | Conditions | Trials | Role |
|---|---:|---:|---:|---:|---|
| P0 | 2 | 1 | 4 | 8 | mechanics, isolation, engagement; excluded |
| P1 | 24 | 1 | No-op only | 24 | group-level headroom; becomes wave-1 No-op if admitted |
| RQ1 remainder | 24 | 2 | registered missing cells | 168 | completes 48 four-arm blocks |

The admitted RQ1 matrix therefore has 192 trials: 24 tasks x 2 waves x 4
conditions.  P0 is outside that count.

## Outcomes And Estimands

The sole primary outcome is the unchanged official final executable reward
`Y` in `[0,1]`.  For the eligible families it is expected to be binary; any
official fractional reward is retained without thresholding.

Primary estimand:

```text
mean_task(mean_wave(Y_Trajectory - Y_Raw))
```

Mandatory competing estimand:

```text
mean_task(mean_wave((Y_Trajectory - Y_No-op)
                    - (Y_Generic - Y_No-op)))
```

The algebraically equivalent Trajectory-minus-Generic difference is also
reported, but the gain notation keeps No-op's role explicit.  No-op separately
anchors adverse outcome differences.  Full Raw is the strongest main baseline;
Generic tests whether any extra planning/search inference explains the effect.

Secondary outcomes are supervisor and worker tokens, tool calls, returned
bytes, elapsed time, intervention/abstention rate, and final changed-file count.
They cannot rescue a non-positive primary contrast.  No pathology accuracy,
evidence F1, human agreement, LLM-rubric score, or Agent-judge label is computed.

## Statistical Analysis

- Show every task-wave-condition reward; no cell is silently dropped.
- Compute task-balanced means so repeated repositories do not dominate merely
  because they have more tasks.
- Use the frozen within-task-wave four-arm assignment to perform one-sided
  randomization inference for the two directional registered contrasts.
  Enumerate assignment permutations when feasible; otherwise use 1,000,000
  Monte Carlo permutations with seed `20260721`.
- Report 95% task-cluster bootstrap intervals with 10,000 resamples over the 24
  RQ1 tasks.  Waves remain inside their sampled task cluster.
- Report DeepSWE and SWE-bench Pro effects separately as descriptive subgroup
  checks; neither subgroup can replace the combined estimand.
- Report adverse outcome differences `Y_condition - Y_No-op`; because prefixes
  are independently randomized, do not call individual discordances causal
  harm events.

H6 receives support on this workload only if both registered point estimates
are positive, both randomization p-values are below 0.05, both 95% task-cluster
interval lower bounds exceed zero, and Trajectory's mean adverse outcome
difference versus No-op is not worse than both Raw and Generic.  Otherwise the
result is contradictory or inconclusive as specified below.

## Failure, Retry, And Missingness Rules

An Agent decision, missing plan, test failure, timeout under the official limit,
or simulator refusal is an outcome, not infrastructure missingness.  It remains
in the assigned cell.

An infrastructure failure is limited to runner crash, unavailable official
image, credential transport failure before model execution, corrupted archive,
or verifier failure unrelated to the workspace.  Every failed attempt is
retained.  Retry uses the same task, wave, assignment, model/config, and opaque
ID.  A task is never replaced and a single favorable retry is never selected;
the first protocol-valid attempt is canonical.  If a whole block cannot be
completed, it remains missing and the complete-case primary analysis is
supplemented by worst-case bounds.  More than 5% missing registered cells makes
the experiment inconclusive.

## Interpretation

- **Supported:** all preregistered support criteria pass.  This establishes an
  average randomized intervention benefit on the selected coding population,
  not cross-domain generalization and not same-checkpoint causality.
- **Contradictory:** either registered point estimate is non-positive or Raw/
  Generic clearly matches or beats Trajectory.  Reject the stronger workspace-
  relation claim; do not add learned retrieval to rescue it.
- **Inconclusive:** positive but uncertain effects, engagement/parity failure,
  excessive missingness, or a headroom failure.  Report the fixed outcomes and
  do not retune on the same tasks.
- **Efficiency-only:** Trajectory ties Raw on outcome but uses materially fewer
  evidence tokens/bytes without worse adverse outcomes.  This supports only a
  compression/access claim.

Only a supported RQ1 result may open query ablations, the 24 untouched coding
tasks, another worker/model, or a natively multi-step scientific-work workload.

## Reproducibility And Reporting

The experiment directory stores the reviewed plan, allocation manifest,
implementation hashes, preflight report, raw per-trial Harbor archives,
supervisor ledgers, duplicate evaluator payloads, derived tidy table, analysis
script, and independent result review.  Credentials, native auth stores,
runtime caches, model blobs, Docker layers, and benchmark checkouts are never
committed.

The runner prints task, wave, opaque trial ID, current stage, supervisor tool
engagement, official reward, elapsed time, and artifact path as it runs.  Raw
records retain condition mappings outside worker-visible paths.  A fresh
reviewer must approve this plan before implementation, and a separate fresh
reviewer must inspect the completed result before the paper changes.
