# Step 0049 Task-Hierarchy Literature Search And Experiment Handoff

- report persisted: 2026-07-20T01:47:21-07:00
- parent: Step 0049 REVIEW routing
- objective: find the closest task-semantic mechanism, a real hierarchy-bearing
  workload, and standard structural metrics for the next EXPERIMENT gate
- canonical output: `docs/background-related-work.md`
- completion: complete for experiment selection

## Fixed Claim Questions

1. What prior work already turns one agent trajectory into task/subtask/result
   structure?
2. What prior systems already correlate resources across execution layers and
   canonicalize them across runs?
3. Which public real datasets expose independent task/subtask/action/object or
   result structure rather than a project-authored label?
4. Which published standard metric compares a predicted nested ordered task
   tree with a reference tree?

The search preserved the exact thesis and four RQs. It did not treat overlap as
authorization to shrink the contribution.

## Query And Source Families

Searches covered hierarchical task decomposition benchmarks, agent trajectories
with subtask annotations, process-mining hierarchy discovery, GUI-agent
trajectory segmentation, constituency-tree evaluation, and ordered tree-edit
distance. Primary sources and official dataset pages were opened for decisive
judgments.

## Verified Findings

### Closest mechanisms

- Magpie is the most important cross-layer profiling ancestor.
- GUIDE is the closest task-semantic trajectory mechanism. Its text-only
  segmentation module reads the full action sequence, emits coherent subtask
  segments, then separately produces subtask verdicts and task-level summary.
  This directly suggests why the failed per-operation Qwen policy lacked enough
  context, but it also means simple task segmentation is not novel.
- Grosz and Sidner remain the conceptual precedent for variable-depth active
  intention stacks.
- BPMN Miner and hierarchical process-mining work remain process/subprocess
  discovery precedents.

### External assets

| Asset | Independent structure | Execution provenance | Fit | Main limitation |
|---|---|---|---|---|
| TaskBench | task steps plus tool-dependency DAG | benchmark-generated realistic multi-tool requests | software/tool agent | DAG, not nested execution tree |
| CRAB | decomposed-subtask DAG plus reward functions | executable cross-environment agent tasks | strong subtask completion gold | DAG and environment setup cost |
| WorkArena++ | compositional enterprise workflows | realistic ServiceNow tasks | overlaps current AgentRewardBench corpus | no released complete span tree in current operations |
| AgiBotWorld2026 | task, subtask intervals, primitive skill intervals, objects, success | real long-horizon embodied trajectories | strongest typed multi-level temporal gold | large multimodal adapter and domain shift |
| HABIT | task, per-step human/robot subtask indices, workflow graph | real human-robot demonstrations | high-quality recorded boundaries | shallower hierarchy |

### Metrics

- Use labeled and unlabeled constituent span precision/recall/F1 when the gold
  and prediction are ordered nested intervals.
- Use normalized ordered tree-edit distance only as a secondary whole-tree
  measure because edit costs introduce a convention.
- Boundary F1 diagnoses segmentation and B-cubed diagnoses one flat partition;
  neither validates all hierarchy levels.

## Baseline Handoff

The competing scientific positions are:

1. **Runtime-field hierarchy is sufficient.** Represent with the current fixed
   session/phase/action or equivalent field stack.
2. **Flat semantic subtask segmentation is sufficient.** Represent with a
   GUIDE-style full-trajectory partition or dataset-native phase hierarchy.
3. **Typed task responsibility paths add value.** Represent with concrete task,
   nested subtask when evidence supports it, strategy/phase, semantic action,
   object, and result, while retaining system fields only as attributes.

Do not add multiple weak field-order variants. A matched flat semantic
segmentation is the strongest immediately runnable mechanism baseline; the
runtime-field view is a lower-bound/current-practice control.

## Experiment Implication

The next experiment should avoid another per-operation free-label policy. The
method should first segment a complete real trajectory into coherent subtasks
with global context, then deterministically attach typed lower frames from
visible action/object/result evidence. Its depth is variable because subtask
nesting and optional lower evidence vary, not because every operation can invent
an unconstrained frame.

The first valid experiment must state exactly which hierarchy levels have
independent gold. If only task/subtask boundaries are available, it tests that
level and does not claim full-stack accuracy. A future stronger run can use the
AgiBotWorld2026 typed hierarchy if the metadata-only real preflight shows the
adapter is feasible without leaking annotation fields into the method.

## Search-Strategy Update

Stop searching for more local CodeTrace cutoffs. Search only when it can settle
one of two remaining questions: the strongest runnable public hierarchy asset,
or the strongest matched task-segmentation baseline. GUIDE, CRAB, WorkArena++,
and AgiBotWorld2026 are the active branches.

## Remaining Uncertainty

The public AI-software-agent assets inspected here do not provide a single clean
six-level gold tree. The experiment should proceed with the strongest runnable
independent level rather than pause for human input or fabricate a bespoke gold
set.

## Next Node

`research-experiment-design`: paper-value admission, one hierarchy-fidelity
hypothesis under unchanged RQ3, a concise plan, and real preflight of the
selected public asset. Resource conservation is a correctness check; an RQ1
decision consequence requires a separate later experiment.
