# REVIEW Node 2: External Search And Source Verification

- synthesis persisted: 2026-07-20T01:46:33-07:00
- parent: REVIEW Node 1
- objective: test the novelty, task-hierarchy, baseline, and evaluation threats
  raised by the blind read
- method: primary papers, official proceedings, official product documentation,
  and official dataset pages; secondary summaries were leads only
- completion: complete for routing; benchmark executability remains an
  EXPERIMENT-gate question

## Search Branches

1. cross-layer request/resource profiling;
2. query-time grouping and profile tags;
3. cross-run agent behavior and process analysis;
4. task/subtask hierarchy induction;
5. real datasets with explicit task/subtask/action/object/result structure;
6. standard tree and boundary comparison metrics.

## Decisive Closest Work

- Magpie is the most important missing systems ancestor: it correlates
  heterogeneous low-level events into per-request control-flow/resource models
  and canonicalizes executions.
- Pivot Tracing, pprof tags, OpenTelemetry Profiles, NeMo, LangSmith, and Datadog
  establish selective grouping, profile/trace linkage, nested workflow reports,
  and hierarchical population rollups.
- Hodoscope, Graphectory, TraceProbe, TraceGraph, and CodeTracer establish
  semantic cross-run analysis, process profiles, hierarchical traces, and
  intervention-oriented evaluation.
- GUIDE is the closest newly verified task-semantic mechanism. It partitions a
  completed GUI-agent trace into coherent subtasks, diagnoses each subtask, and
  aggregates a task result. Its reported evaluation covers 932 industrial
  e-commerce traces, 1,302 AgentRewardBench traces, and 480 AndroidBench traces.
  GUIDE is single-trajectory evaluation, not conserved cross-run profiling, but
  it directly invalidates any novelty claim based merely on task-to-subtask
  segmentation and result labels.

## Task-Hierarchy Assets

- TaskBench provides task steps and a ground-truth tool-dependency graph for
  realistic multi-tool requests, but its target is a DAG and not a full nested
  execution stack.
- CRAB represents each task as a graph of decomposed subtasks with executable
  reward functions; it is a strong source for subtask completion and dependency
  structure, again as a DAG.
- WorkArena++ composes realistic enterprise workflows from simpler tasks and is
  already represented inside AgentRewardBench, but public trajectories do not
  directly provide a complete nested span tree.
- AgiBotWorld2026 exposes an explicit multi-level temporal hierarchy:
  episode/task, subtask intervals, primitive skill/instruction intervals,
  objects, and success results. It is a real embodied-agent dataset and a strong
  hierarchy-fidelity asset, though adapting its sensor/action stream to the
  current text/tool operation schema is non-trivial.
- HABIT provides human-recorded subtask boundaries and task workflow graphs, but
  only a shallower task/subtask structure for the current purpose.

## Standard Metrics

For a predicted ordered nested span tree, PARSEVAL-style labeled and unlabeled
constituent precision/recall/F1 are the closest standard structural metrics.
Zhang--Shasha tree-edit distance is a standard secondary whole-tree distance.
Exact boundary precision/recall/F1 remains useful but cannot by itself validate
hierarchy. Ordinary B-cubed remains appropriate for one flat partition only and
must not be presented as full task-stack fidelity.

## Novelty And Experiment Impact

The search does not justify a smaller story. It sharpens the positive claim that
must be proven: task-semantic cross-run profiles attach conserved resources and
effects to task responsibility paths and expose repeated/failed work across
runs, beyond both runtime-field profiles and single-trajectory task diagnosis.

## Search-Tree Update

The search frontier changes from “find a better boundary constructor” to “test
task responsibility structure and its profiling consequence.” Further cutoff,
depth, or field-purity searches on CodeTraceBench are closed unless new external
evidence requires them.

## Remaining Uncertainty

No single public AI-software-agent dataset verified in this node provides all
six desired typed levels as independent gold over complete raw trajectories.
The next plan must therefore either use the strongest partial public gold and
state its tested level, or use a real multi-level embodied-agent dataset. It may
not claim full hierarchy from flat stage labels.

## Next Node

Full-paper reread with the closest-work and task-hierarchy findings fixed.
