# Literature And Benchmark Re-grounding: Objective Intervention Utility

Timestamp: 2026-07-21T02:04:51-07:00
Parent node: B20, author-directed closure of the human-gold experiment
Gate: BOOTSTRAP / EXPERIMENT_GATE
Status: completed literature and asset audit; experiment-plan handoff admitted

## Decision Trigger

The author explicitly rejected independent human annotation and requested a
different trajectory or benchmark experiment. This report therefore does not
search for cheaper annotators or use an Agent as a proxy expert. It changes the
scientific outcome from agreement with a subjective diagnosis label to the
observable effect of an intervention on an official executable benchmark.

The claim is stated without project names before searching:

> Under fixed supervisor and continuation budgets, does a source-linked account
> of cross-session workspace evolution let an automatic supervisor produce an
> intervention that improves the subsequent worker's objectively graded outcome
> more than equal-budget access to the complete raw trajectory and matched
> no-op/search controls?

This is stronger than asking whether a model emits the same pathology category
as an annotator. Every candidate intervention is executed from a frozen
workspace checkpoint; the benchmark's test or numerical oracle measures the
consequence.

## Search Questions

1. Which public benchmarks have persistent workspaces, more than one Agent
   round/session, and a deterministic final grader?
2. Which coding and research workloads provide replayable repositories or
   workspaces and objective outcomes?
3. Which recent systems already inject trajectory-derived guidance, optimize
   harnesses from past trajectories, or study experience reuse?
4. What controls are required to distinguish a trajectory representation from
   extra inference, search, benchmark leakage, or a generic reminder?

Representative queries and primary-source checks:

- `long running agent benchmark persistent workspace multi round deterministic oracle`
- `multi turn coding agent benchmark official tests trajectory`
- `research engineering agent benchmark objective score transcripts`
- `agent harness optimization past trajectories self supervised`
- `trajectory memory intervention long horizon agent reminder`
- `harness evolution matched feedback inference budget held out tasks`
- official repository inspection of task specifications, adapters, graders,
  configuration examples, and current Git revisions.

## Direct Same-Claim And Protocol Threats

| Work | What already exists | Consequence for this project |
|---|---|---|
| [Retrospective Harness Optimization](https://arxiv.org/abs/2606.05922) | Self-supervised harness optimization from past trajectories, without external labels, using re-solving, self-validation, self-consistency, and self-preference. | “No human labels” is not novelty. Harness changes must be tested on held-out tasks with objective outcomes. |
| [Rethinking the Evaluation of Harness Evolution for Agents](https://arxiv.org/abs/2607.12227) | Shows that harness-evolution gains can be explained by extra search/feedback and may not generalize; requires matched inference/feedback budgets and held-out evaluation. | Add a matched generic reflection/search control, paired no-intervention outcome, fixed budgets, and workspace/task-family-held-out analysis. Do not attribute a gain to better process evidence if extra inference explains it. |
| [Remember When It Matters](https://arxiv.org/abs/2607.08716) | A separate memory Agent selectively injects trajectory-grounded reminders into an unmodified action Agent and improves objective benchmark success. | Active reminder injection is prior art. The remaining delta must isolate realized, cross-session workspace evolution versus same-source raw access, not claim reminder injection itself. |
| [SWE Context Bench](https://arxiv.org/abs/2602.08316) | Related repository tasks with shared context; compares full trajectories, summaries, oracle/autonomous retrieval, accuracy, time, and cost. | Cross-task experience reuse and full-trajectory retrieval are not novel. This benchmark is a strong coding workload or external baseline, and splits must keep related task sequences together. |
| [REFLECT](https://arxiv.org/abs/2605.15104) | Tests attribution by intervention and replay rather than relying only on judge agreement. | Use executed counterfactual continuation as the validity protocol. The project contribution is not causal replay itself. |
| [Harness Bench](https://www.harness-bench.ai/) | Measures harness effects across 106 sandboxed workflow tasks and reports 5,194 trajectories; includes long-running multi-round tasks and executable graders. | A harness-effects benchmark is not novelty. It is the best immediate test bed because its multi-round Codex adapter creates fresh top-level sessions over one persistent workspace. |

## Benchmark And Trajectory Asset Audit

### Immediate preflight: Harness Bench

- Primary artifacts: [official site](https://www.harness-bench.ai/),
  [official repository](https://github.com/Qihoo360/harness-bench), and
  [paper](https://arxiv.org/abs/2605.27922).
- Audited repository revision:
  `1025086a446653702b80cfb48babbeec35db6b2c`.
- Scale: 106 offline tasks in eight workflow categories; the site reports
  5,194 execution trajectories.
- Outcome rule: repository inspection confirms that only tasks 008 and 013 use
  the default nonzero outcome-LLM blend; the selected tasks below use
  `outcome_llm_weight = 0`, so the primary result is the executable
  `oracle_grade.outcome_score`, not an LLM rubric.
- Session property: the official Codex adapter calls a new `codex exec` for
  every prompt round while preserving the same sandbox workspace and isolated
  `CODEX_HOME`. Thus multi-round tasks naturally create the independent
  top-level sessions needed by the research question.
- Admitted deterministic multi-round tasks:
  `057-interruption-resume`, `058-multiday-project-state`,
  `059-event-update-replan`, `060-task-cancellation-cleanup`,
  `103-policy-update-replan-diff`, and
  `105-partial-batch-resume-ledger`.
- Excluded task: `007-session-memory` explicitly tests memory inside the same
  conversation rather than workspace-mediated continuity, so it does not
  isolate the target mechanism.
- Preflight seed: task 058 has three rounds, persistent audit artifacts, exact
  required state transitions, and a deterministic final oracle. Intervention
  occurs after Day 2 and before the fresh Day 3 Codex session.

Harness Bench is selected for the first real preflight because it already has
the required runner, sandbox, persistent files, independent session calls, and
grader. The experiment may add only a thin pause/fork/inject adapter; it must
not change fixtures, future prompts, ground truth, or the official oracle.

### Coding expansion

| Asset | Primary source and version | Fit | Decision |
|---|---|---|---|
| SWE-Interact | [paper](https://arxiv.org/abs/2606.30573); audited dataset revision `2005fb10bbe93880766d2211cc146692ea551eb8af` | 125 long-horizon interactive coding tasks with repository tests and evolving requirements. | Preferred coding expansion once the official runner is pinned and the user-simulator contribution can be separated from the supervisor intervention. |
| SWE Context Bench | [paper](https://arxiv.org/abs/2602.08316); audited dataset revision `5bec275a2095768a53ac804ae4fdf90b1723b8af` | 300 base and 99 related tasks; directly tests reuse of full trajectories and summaries with objective SWE tests. | Mandatory closest-setting workload/baseline. Use cluster-held-out related-task groups; do not claim experience reuse as novelty. |
| SWE-Together | [paper](https://arxiv.org/abs/2606.29957) | 109 tasks reconstructed from 11,260 real sessions, final correctness plus corrective-turn count. | Useful secondary external validation, but its LLM user simulator can confound an automatic supervisor intervention. |

### Auto-research and scientific-work expansion

| Asset | Primary source and version | Fit | Decision |
|---|---|---|---|
| CORE-Bench | [official repository](https://github.com/siegelz/core-bench), revision `e32a2980e72fe6eb04ee04eb749458f570625663` | 270 computational-reproducibility tasks from 90 papers across Python/R and multiple disciplines; isolated workspace and objective report questions. | Preferred non-coding/research expansion through the currently recommended Holistic Agent Leaderboard harness. Verify a small public task slice before admission. |
| RE-Bench | [official METR release](https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/), [official repository](https://github.com/METR/RE-Bench), revision `93b98062e55f6945d4a7e213a3226dd419896170` | Seven realistic ML research-engineering environments with objective continuous scores and released transcripts; runs can last eight hours and use GPUs. | High-value stress test after the cheaper mechanism experiment; not the first preflight because cost and task count make failures hard to diagnose. |
| MALT | [official METR release](https://metr.org/blog/2025-10-14-malt-dataset-of-natural-and-prompted-behaviors/) | Thousands of software/research trajectories with outcomes and public tasks. | Useful offline robustness/case-discovery corpus, but not decisive because a static trajectory cannot test whether an intervention causally improves the same continuation. |

### Offline development-only trajectory corpus

TraceBench provides thousands of Terminal-Bench/SWE trajectories with
artifacts and outcomes (audited dataset revision
`7da2e4f45b330be8b6e8f1cff835247723cb3341`). It is useful for parser coverage,
retrieval load, and retrospective case finding. It is rejected as the headline
experiment because it does not by itself supply a checkpoint from which the
same worker can be continued under alternative interventions.

## Revised Decisive Experiment

### Unit and causal protocol

One experimental unit is a benchmark task checkpoint immediately before a new
top-level worker session. A prefix worker first executes all earlier rounds.
The complete workspace, source sessions, benchmark state, next official prompt,
model configuration, and budgets are frozen. The checkpoint is cloned into
each condition. Only the supervisor evidence interface and resulting bounded
message differ.

Conditions:

1. **No intervention:** the worker receives only the official next-round
   prompt.
2. **Generic matched control:** an equal-budget supervisor produces a generic
   review/validation reminder without access to prior trajectory evidence.
3. **Full Raw Retrieval:** the supervisor receives complete same-source records
   through search, exact-record, and exact-range tools.
4. **Workspace Trajectory Retrieval:** the same supervisor receives the same
   Raw tools plus deterministic source-linked workspace-history, action-effect,
   and state-transition relations.

Each supervisor returns either one bounded message or `ABSTAIN`, with source
IDs where evidence is used. The message is appended to the unchanged official
next-round prompt. A fresh top-level worker continues from the cloned
checkpoint under the same model, reasoning effort, timeout, and remaining
budget. The unmodified official executable oracle grades the final workspace.

The primary contrast is Workspace Trajectory minus Full Raw Retrieval. The
other two conditions measure harm and the value of extra inference or a generic
reminder. All continuations are actually run; no Agent judge predicts which
would have worked.

### Outcomes

- Primary: paired change in official `outcome_score` relative to no
  intervention, and paired Workspace-Trajectory minus Raw score.
- Safety: intervention harm rate relative to the no-intervention fork.
- Efficiency: supervisor plus worker tokens, wall time, tool calls, and bytes
  returned.
- Calibration: abstention rate and whether non-abstaining interventions have
  positive realized utility.
- Mechanism ablations after a nonzero main effect: remove prior-session history,
  action order, lifecycle continuity, or workspace transitions one at a time.

No pathology macro-F1, evidence-set F1, recommendation F1, or human agreement
is part of this revised experiment. Source IDs are an auditable grounding
constraint, not a semantic gold label.

### Validity and leakage controls

- The supervisor sees the current official prompt but never future prompts,
  ground-truth files, oracle code/results, repaired siblings, or other
  conditions' outputs.
- Prefix checkpoints are byte-identical across condition forks.
- Worker and supervisor models, prompts, inference budgets, tool budgets, and
  condition order are fixed or randomized as declared.
- Related tasks and repositories remain in the same split; held-out evaluation
  is by task/workspace family rather than continuation.
- Multiple continuation repetitions estimate model stochasticity. The
  checkpoint, not each fork, is the clustering unit.
- Any task with an LLM-weighted primary outcome is excluded from the main
  analysis.
- A positive claim requires benefit beyond Full Raw and the matched generic
  extra-inference control. A Raw tie with lower cost supports compression only;
  no-op or generic-control parity refutes the stronger mechanism claim.

## Asset Selection And Rejections

- **Selected now:** Harness Bench task 058 for the real preflight, followed by
  the six deterministic multi-round tasks if the pause/fork/inject mechanism
  and non-ceiling outcome variance pass.
- **Selected for later breadth:** SWE-Interact or SWE Context Bench for coding;
  CORE-Bench for scientific reproducibility; RE-Bench as an expensive research
  stress test.
- **Rejected as primary truth:** human labels, Agent-generated labels, LLM
  rubrics, static-only trajectory classification, and visualization judgments.
- **Rejected as first run:** RE-Bench due GPU/time cost; task 007 due
  same-conversation memory semantics; Harness Bench tasks 008/013 due LLM-blended
  outcomes.
- **Rejected as a claim:** new event IR, graph novelty, reminder injection,
  trajectory reuse, harness optimization, or causal replay in isolation.

## Handoff To Experiment Design

The first executable plan should answer one revised RQ:

> Under fixed supervisor and continuation budgets, does Workspace Trajectory
> Retrieval produce interventions with higher objectively measured continuation
> utility than Full Raw Retrieval on persistent, multi-session benchmark tasks?

The real preflight is admitted only to verify: one official multi-round task,
one checkpoint fork, four real continuations, deterministic oracle invocation,
same-source/budget parity, absence of future/oracle leakage, and non-ceiling
variance. Passing dependencies admits the predeclared six-task matrix; it does
not itself establish the paper claim.

Residual uncertainties before the larger run are the exact official runner for
SWE Context Bench, the current HAL integration for CORE-Bench, worker outcome
variance under the locally available model, and the number of repetitions
needed for a stable paired estimate. These are execution and power questions,
not reasons to reinstate subjective gold.
