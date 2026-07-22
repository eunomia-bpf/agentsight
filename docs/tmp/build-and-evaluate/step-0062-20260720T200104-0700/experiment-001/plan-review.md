# Independent Experiment-Plan Review

> Historical review note: these three rounds approved the scientific plan
> before the author established the pprof-only product boundary. References to
> a static flamegraph are superseded only at the output layer by the amendment
> in `experiment-plan.md`; no task-state rule, workload, reference, or metric
> changed.

## Review Contract

The independent reviewer read and explicitly applied
`research-experiment-design`. Review is serial, read-only, and limited to the
scientific question, public data/reference, tested mechanism, hierarchy and
identity metrics, baselines, basic leakage, feasibility, and net
simplification. It does not request code, experiment execution, Git protocols,
packets, seals, or additional reproducibility machinery.

## Round 1 — REJECT

The reviewer found the direction valuable but rejected the draft because it
would primarily measure closed-set plan-step classification rather than the
required task-semantic hierarchy.

### Must-fix

1. **No independent operation-level reference.** AgentRewardBench publishes
   trajectory-level judgments, not operation-to-subtask labels. WorkArena's
   flat source `subtasks` and `cheat(..., subtask_idx)` are not attached to the
   released AgentReward trajectories. Two model readers plus model adjudication
   would create project-authored pseudo-gold rather than benchmark ground truth.
   WorkArena/AgentReward must become secondary evidence unless an official
   evaluator can label these exact traces.
2. **Wrong causal mechanism.** One Qwen decision per operation is a dense
   closed-label controller. Step 0061 instead selected sparse task-state
   mutation from task, plan, delegation, progress, and completion events;
   ordinary operations must inherit state. The primary workload must expose
   those control events.
3. **Nested hierarchy ungrounded and unscored.** WorkArena supplies a root and
   ordered atomic steps, not an independently labeled variable-depth tree.
   Qwen-created intermediate groups can be arbitrary because every registered
   metric scores only numbered leaves. The primary workload and metric must
   expose and score the actual hierarchy.
4. **Cross-run identity is handed to the constructor.** Reusing the same
   official step strings as the output vocabulary measures assignment, not
   recovery of independently comparable identities.
5. **Population rule is outcome-dependent and duplicated.** Reference
   assignability cannot exclude difficult cases after labeling. The 475
   WorkArena annotation rows represent 472 unique task/model pairs because
   three Llama pairs are duplicated. Keys and eligible matched runs must be
   defined before scoring.
6. **Success rule is too conjunctive.** One hierarchy/identity metric should be
   primary. Secondary boundary and flat-partition metrics should diagnose the
   result rather than force improvement on every metric and baseline.

### Minimal route

- Use a public primary asset that already releases task, nested subtask, and
  lower-operation/skill intervals or trees.
- Allow stack mutation only on explicit intent/control events.
- Score the hierarchy and independently comparable identity with one primary
  published standard metric.
- Retain WorkArena/AgentReward only for secondary real Web-agent coverage.
- Remove ARI, demote stateless assignment to an ablation, and require only one
  declared rendered example.

**Round 1 verdict: REJECT.** The plan returns to proposal revision before any
implementation or inference.

## Round 2 — REJECT

The independent reviewer again explicitly applied
`research-experiment-design`. It accepted the scientific correction: the
agent's explicitly declared task-control state is a reproducible profiling
target, and keeping incorrect, repeated, or unfinished declared tasks is more
faithful than replacing them with a benchmark's ideal solution. It also found
the complete local Codex population, separate normalized-event candidate and
raw-event reference replay, exact-path accuracy, metadata exclusion, resource
conservation, and one task-centric flamegraph sufficient for a simple
supporting experiment.

### Must-fix

1. The draft treated task state as one serial global stack. Real root sessions
   can receive multiple user turns and can run multiple child agents
   concurrently. Each session needs an independent path; a child must inherit
   the parent's path snapshot at spawn, while parent and siblings continue on
   their own branches. Child completion may close only that branch.
2. Parent/delegated-task linkage and exact-path identity were underspecified.
   The plan must bind a spawn call's output child ID to the child session rather
   than guessing from time/depth/nickname, and accuracy must compare stable raw
   source-coordinate identities rather than cleaned display strings.

### Applied minimal revision

- Each root user turn now opens one concrete-task occurrence; a later turn ends
  its temporal ownership without inventing an outcome.
- Task state is per session. Spawn copies a parent-path snapshot into one
  uniquely linked child branch; completion does not mutate concurrent paths.
- Root, plan, and delegation identities use raw user-event, initial plan-item,
  spawn-call, and child-thread coordinates. Display cleanup is scoring-blind.
- Output states are limited to source-declared completion, explicit native
  failure when present, and `open at capture end`.
- The experiment is explicitly supporting source-fidelity evidence, requires
  one static flamegraph, names one evaluator command/output location, and uses
  exactly three plan-review rounds.

**Round 2 verdict: REJECT pending the applied concurrency and identity
clarifications.** No implementation or inference ran before revision.

## Round 3 — PASS

The independent reviewer completed a third full read with
`research-experiment-design` and found no remaining must-fix issue.

It verified that:

- every root user turn forms a separate task occurrence;
- task state is maintained per session rather than as a false global stack;
- each child inherits the parent path at its uniquely identified spawn while
  parent and sibling branches continue independently;
- child completion closes only that child branch;
- spawn call output, child session ID, and parent thread ID form the required
  unique link;
- exact-path accuracy uses raw source coordinates, never renderer text;
- unfinished state is reported only as `open at capture end`; and
- the result is limited to supporting source-fidelity evidence rather than a
  complete RQ3 or ideal-plan claim.

The reviewer also confirmed that the plan remains one complete real
population, one deterministic constructor, one independent raw replay, one
primary metric, necessary invariants, and one required static flamegraph. It
adds no model, benchmark, baseline, gate, or freeze protocol.

**Round 3 verdict: PASS with zero must-fix.** The experiment may enter REAL
PREFLIGHT.
