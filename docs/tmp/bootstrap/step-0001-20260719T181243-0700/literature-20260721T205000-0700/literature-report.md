# Literature And Official-Asset Qualification: Objective Cross-Session Workloads

Created: 2026-07-21T20:50:00-07:00
Gate: BOOTSTRAP / LITERATURE
Question: how to replace rejected human or Agent-generated diagnostic gold with
objective long-horizon trajectories and executable benchmark outcomes?

## Decision

Use randomized continuation utility as the active truth contract.  A benchmark
supplies a persistent workspace, native session boundaries, and an unchanged
executable final evaluator.  Treatment is assigned only after a treatment-blind
planning session; No-op, Generic, Full Raw, and Workspace Trajectory then
continue through the same official remaining stages.  The benchmark's final
reward is the outcome; neither a human annotation nor an LLM diagnosis is gold.

The first admissible workload is the deterministic-test subset of the current
official SWE-INTERACT release.  SWE-ContextBench is rejected as the main
workload because its related examples start from task-specific clean testbeds,
not one workspace that persists across sessions.  CORE-Bench v1.1 is retained
as a later scientific-work candidate, but it is not currently admissible for
RQ1 because the official task is one continuous reproduction and accuracy is
near saturation.  A long task alone is not evidence of a cross-session
workspace process.

## Eligibility Contract

A workload is eligible only when all of the following are true before any
treatment outcome is inspected:

1. the same workspace state persists across at least two top-level Agent
   sessions;
2. the boundary is defined by the workload or runner rather than selected from
   an observed failure;
3. the next worker starts without the prior worker's conversation state;
4. the final condition is scored by the official executable evaluator;
5. treatment is assigned prospectively within task/replication blocks, and all
   arms use identical official prompts, worker/model budgets, simulator
   configuration, and evaluator code;
6. no human label, Agent label, LLM rubric, or semantic judge contributes to the
   primary outcome;
7. there is prospective outcome headroom and the registered evidence tools are
   actually used before a four-arm comparison is admitted.

## SWE-ContextBench: Rejected As The Main Workload

Official sources checked:

- paper and local PDF: `docs/reference/2026-zhu-swe-context-bench.pdf`;
- dataset: `https://huggingface.co/datasets/jiayuanz3/SWEContextBench`.

The benchmark contains base tasks and related tasks intended to test reuse of
prior experience.  However, the dataset constructs a clean task testbed from
each example's repository and base commit.  Related examples share retrievable
experience, not a source-native persistent workspace whose artifacts have been
changed by several fresh sessions.  It is therefore close prior work and a
possible experience-reuse baseline, but using it as the main workload would
silently replace workspace continuity with cross-task memory.

Verdict: structurally ineligible for the active RQ1 continuation experiment.

## SWE-INTERACT: Accepted For Preregistered Qualification

Official sources checked:

- paper: `https://arxiv.org/abs/2606.30573`;
- paper and local PDF: `docs/reference/2026-raghavendra-swe-interact.pdf`;
- task repository: `https://github.com/scaleapi/SWE-Interact`, revision
  `b32f98c3b8f76ca65e84341d1f30e5af7135f85d`;
- runner: `https://github.com/laude-institute/harbor`, revision
  `00c19fe2a9c1b9b7ed07efc270412007ac4cb3da`;
- runner contract:
  `https://www.harborframework.com/docs/tasks/multi-step`.

The current official repository contains 75 multi-step tasks: 25 DeepSWE, 25
SWE-bench Pro, and 25 SWE Atlas Refactoring (RF).  Every task has the same five
source-native stages:

1. `01_plan`;
2. `02_implement`;
3. `03_handoff`;
4. `04_write_tests`;
5. `05_test_handoff`.

Every task uses `multi_step_reward_strategy = "final"`.  Intermediate verifier
scripts return a neutral reward; the final step runs the task's end-to-end
evaluator.  Harbor's documented default is a fresh Agent conversation for
every step while retaining one shared environment and filesystem.  Native
resume is opt-in through `--resume-trajectory`; it is not enabled by the
official SWE-INTERACT run scripts.  Thus the benchmark already supplies the
precise experimental object needed here: several independent top-level Agent
sessions transforming one persistent workspace.

### Primary-outcome filter

The 25 RF tasks combine executable tests with an LLM rubric in their final
`canonical_test.sh`.  They are excluded prospectively from the primary
experiment because the author rejected model-defined truth.  The 25 DeepSWE
and 25 SWE-bench Pro final evaluators use executable repository tests and do
not invoke the RF rubric path.  This leaves a frozen eligible population of 50
tasks before any task-level treatment or No-op score is observed.

The simulated maintainer used during planning is part of the workload, not the
outcome oracle.  It must remain identical across arms and cannot supply labels
to the supervisor.

The official user-server keeps its conversation in process memory and does not
offer a sampling seed.  Exact four-way checkpoint cloning would therefore
require process-memory checkpointing or a project-authored simulator-state
patch.  Either choice adds substantial mechanism outside the benchmark and can
silently change later user feedback.  The main experiment should instead use
delayed blocked randomization over independent official trials: step 1 is
treatment-blind; the condition is selected at the step-2 boundary according to
a frozen task-by-wave schedule.  Prefix and simulator stochasticity then enter
the estimand as randomized environment variation rather than an uncontrolled
fork artifact.

### Natural intervention checkpoint

The defensible checkpoint is the end of `01_plan` and before
`02_implement`:

- the first worker has explored the repository, interacted with the simulated
  maintainer, and written `/tmp/plan.md`;
- the next implementation worker is source-natively fresh;
- a bounded supervisor message can still affect production implementation and
  the unchanged final tests;
- selecting a later boundary would leave little or no opportunity to repair
  implementation, because the benchmark separates implementation and test
  commits and its final wrapper evaluates the implementation commit.

This checkpoint is selected from the task protocol, not from observed worker
success or failure.

Verdict: structurally eligible, subject to a new plan review, one real runner
preflight, prospective No-op headroom, and mandatory evidence-tool engagement.

## CORE-Bench v1.1: Strong Oracle, Wrong Immediate Structure

Official sources checked:

- paper: `https://arxiv.org/abs/2606.26158`;
- official collection:
  `https://huggingface.co/collections/agent-evals/core-bench-v11`;
- analysis/log repository:
  `https://github.com/nnadgi01/corebench-analysis`, revision
  `167da1562809ee3ddf73816bffeddb738f4a0d82`.

CORE-Bench v1.1 has 39 mainline tasks and CORE-Bench OOD has 19 tasks.  The
update removes or repairs construct-validity defects and shortcut-prone tasks
from the older benchmark.  It is therefore preferable to the original
270-task Easy/Medium/Hard framing for future scientific-work evaluation.

However, its official autonomous protocol is one continuous computational
reproduction.  The separate human-Agent collaboration study also launches one
Agent session per reproduction; human interventions are not a standardized
fresh-session task boundary.  Moreover, the current paper reports near-ceiling
accuracy among leading agents.  Taking an arbitrary elapsed-time cut would be
a project-authored boundary and could select a treatment-friendly point.

Verdict: do not use CORE-Bench v1.1 in the first RQ1 matrix.  Reconsider it for
RQ3 only if a preregistered plan derives a source-independent structural stage
boundary, preserves the official evaluator, and separately demonstrates
headroom.  Otherwise use a scientific benchmark whose workflow is natively
multi-step.

## Resulting Experiment Direction

The next admitted experiment should use SWE-INTERACT's 50 deterministic-test
tasks as its frozen population and retain the published five-step workflow.
It should:

- run independent official trials in task-by-replication blocks containing one
  prospectively randomized No-op, Generic, Full Raw, and Workspace Trajectory
  assignment each;
- keep step 1 treatment-blind and activate the assigned condition only before
  the unchanged step-2 instruction;
- freeze each trial's workspace, `/tmp/plan.md`, user-server transcript, native
  Agent session, official instruction, and per-step logs at that boundary;
- inject at most one bounded supervisor message before the unchanged
  `02_implement` instruction;
- run steps 2--5 with fresh workers and the official final verifier;
- use only the final executable reward as the primary outcome;
- require successful family-specific evidence retrieval with exposed source
  IDs before admitting an arm;
- retain both duplicate final evaluator payloads and their hashes;
- freeze the headroom/task-selection rule before running any No-op prefix.

The experiment tests process-level supervision, not benchmark answer
prediction: the supervisor is useful only if its trajectory-grounded advice
changes the subsequently executed workspace and improves the blocked randomized
official outcome beyond equal-budget Full Raw and Generic controls.

## Novelty Consequence

This asset does not make multi-step coding, trajectory reuse, or fresh-session
workspaces novel.  SWE-INTERACT and Harbor establish those settings.  The
remaining claim is narrower and falsifiable: whether deterministic,
source-linked workspace-evolution relations improve a bounded automatic
supervisor's realized continuation utility beyond complete same-source Raw
retrieval and matched extra inference.
