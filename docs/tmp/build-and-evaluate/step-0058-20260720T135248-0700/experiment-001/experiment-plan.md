# Experiment Plan — Stronger-Model Sufficiency for the Task-Responsibility Stack

## Research Question

- Paper question, unchanged: **RQ3 — How Accurate Are the Tags?**
- Tested uncertainty: can the same complete-trajectory task-semantic interface,
  when run by the already-used local Qwen3.6-27B model rather than
  Qwen2.5-3B, recover human workflow-stage occurrences while emitting the
  required task-responsibility stack?
- Why it matters: Step 0057 established that one fixed 3B call collapses all
  405 trajectories to one interval. It did not establish whether the same
  global interface is sufficient with the already-held Qwen3.6-27B checkpoint.

## One Hypothesis And Paper Value

**Hypothesis.** With the Step 0057 prompt, visible source fields, grammar,
complete selected workload, and standard scorer unchanged, Qwen3.6-27B will
produce persistent task-path occurrences whose ordinary operation-level
B-cubed F1 exceeds the current multi-resolution recurrence constructor, with a
positive paired task-cluster confidence interval.

This is one stronger-model sufficiency test, not another prompt, threshold,
score, cutoff, depth, or benchmark variant. Because the checkpoints also differ
in model generation, training data, architecture, and tokenizer, the result
cannot isolate parameter capacity. It can establish whether the fixed global
interface works with this Qwen3.6-27B checkpoint; a negative result establishes
only that the interface is insufficient with both tested checkpoints.

- Positive consequence: adopt the global task-path constructor for the
  task/subtask prefix, keep the lower semantic suffix, and then synchronize
  only evidence authorized by result review.
- Contradictory or inconclusive consequence: reject this fixed candidate, keep
  the thesis, four RQs, positive hypotheses, and intended hierarchy unchanged,
  and return to a source-grounded task-interface candidate.
- Direct thesis challenge: none. The exact thesis remains **“Agent
  observability needs profiling, not only debugging.”**

## Representation Contract

The main stack is exactly:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, prompt, tool, command, path, and status are metadata,
filters, colors, measures, details, or source-linked evidence. They never
become task-responsibility frames.

The model emits contiguous fine-grained semantic segments. A persistent task
occurrence is the maximal contiguous run with the same ordered
`concrete task -> nested subtask*` path. Changes only to phase, semantic action,
object, or result do not create a new task occurrence. This is the profiler
analogy: a task call stack can stay active while its lower operations change.
The flamegraph retains the full six-part stack; the flat CodeTrace comparison
scores only the active task occurrence.

## External Precedent And Real Assets

- GUIDE, an April 2026 arXiv preprint, is the direct conceptual baseline for
  whole-trajectory LLM subtask segmentation. Its usability validation is not
  human temporal-boundary or nested-tree gold.
- CodeTraceBench supplies the complete fixed real workload: 405 preselected
  reconstructable failed trajectories, 17,148 source-native turns, 20,866
  operations, 2,948 human stage occurrences, and 251 task clusters across four
  agent frameworks.
- The already-held Qwen3.6-27B Q4_K_M GGUF is the same local 27B model family
  previously used in AgentProf experiments. The model file is external and
  unchanged.
- DevAI supplies 55 real AI-development tasks and 365 manually authored
  hierarchical requirements. Its public repository contains only one complete
  OpenHands trajectory, fixed before candidate scoring as
  `benchmark/trajectories/OpenHands/39_Drug_Response_Prediction_SVM_GDSC_ML.json`.
  That trajectory may audit task-name realism but cannot enter the quantitative
  CodeTrace decision or be presented as a full temporal benchmark.

## Fixed Comparison

- Candidate: one Qwen3.6-27B call per complete trajectory, using the exact Step
  0057 system prompt, source reconstruction, output grammar, temperature zero,
  seed, 32,768-token context, and source-visible fields.
- Main baseline: current multi-resolution recurrence assignments on the same
  operations.
- Fixed control: Step 0056 causal Qwen2.5-3B task paths.
- Step 0057 small-model result remains the same-interface small-model control; its
  all-session collapse produces the same one-task occurrence whether identity
  is represented by the full segment or the task path.
- Inference cannot read human stages, stage counts, benchmark quality labels,
  baseline assignments, scores, or framework/model/session/status fields.

## Workload And Standard Metrics

- Real preflight: the same four projected-token-longest complete trajectories,
  one per framework.
- Full run: all 405 selected trajectories; every source-native turn and all
  20,866 operations must complete.
- Primary standard metric: ordinary operation-level B-cubed precision, recall,
  and F1 against session-local human workflow-stage occurrences.
- Primary uncertainty: 10,000 paired bootstrap resamples over the fixed 251
  task clusters for candidate minus recurrence B-cubed F1.
- Standard secondary metrics: adjacent-boundary precision/recall/F1 and exact
  span precision/recall/F1.
- Descriptive checks: segment count, task-occurrence count, task depth,
  repeated-frame count, command-primitive-shaped action count, complete
  coverage, additive operation conservation, and model usage. They do not
  replace the standard metrics or create extra gates.

Flat CodeTrace stages can validate only the active task-occurrence partition.
They do not validate ancestor topology, open-vocabulary task names,
cross-run semantic equivalence, or the lower suffix. The fixed DevAI sample and
the existing independent result reviewer perform one qualitative contract
check: system fields must not enter the responsibility stack; task/subtask
frames must describe concrete work; and phase/action/object/result must neither
occupy the wrong slot nor degenerate into command primitives or repeated empty
labels. This is a claim-boundary check, not a custom score, extra checker,
reviewer, or gate.

## Planned Execution

1. Generalize the Step 0057 evaluator only enough to record the server's fixed
   model identity and to group contiguous equal task paths. Do not change the
   prompt, grammar, source clipping, workload, scorer definitions, or baselines.
2. Run the four-trajectory real preflight through inference, expansion,
   task-occurrence construction, scoring, and rendering. Repair wiring or
   model-identity defects only; do not tune semantic behavior from preflight.
3. Complete all 405 trajectories even if preflight suggests a negative result.
4. Open the verified stages only after all candidate assignments are durable,
   compute the registered standard scores, and render one representative
   task-semantic profile from the fixed predictions.
5. Obtain one independent raw-result review before disposition.

The complete candidate uses one model, one prompt, one full run, and one
scorer. No model sweep, prompt revision, threshold, contraction, score
calibration, hand-authored experiment, or paper edit is admitted.

## Execution Paths And Completion

- Reused evaluator:
  `script/rq3_global_task_semantic_segmentation_eval.py`
- Candidate artifacts:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-qwen27b-v1/`
- Model:
  `/home/yunwei37/.cache/huggingface/hub/models--DevQuasar--Qwen.Qwen3.6-27B-GGUF/snapshots/b19fa7e8538a1a5f66452eb3b3167e026177be1d/Qwen.Qwen3.6-27B.f16.gguf.Q4_K_M.gguf`
- Server: one 32,768-token slot on a new local port; old 3B servers may be
  stopped because their complete outputs are already durable.
- Resume: per-session caches are ordinary compute recovery and are accepted
  only when the candidate model/prompt/grammar/request identity matches.

Full completion requires 405/405 sessions, 17,148/17,148 turns,
20,866/20,866 uniquely assigned operations, all registered standard metrics,
the paired interval, a rendered full-stack example, and independent result
review. Smoke cases cannot substitute for the complete workload.

## Decision

- Supported: candidate-minus-recurrence B-cubed F1 has a 95% interval wholly
  above zero and the output respects the fixed task-responsibility contract.
- Contradicted: the interval upper bound is at most zero, or the output
  degenerates to whole-session collapse or near-turn singleton task paths.
- Inconclusive: the interval crosses zero or the quantitative task partition
  improves while open-vocabulary frames cannot support the representation
  contract.

Any outcome changes only the tested constructor decision. It cannot narrow or
replace the thesis, story, contribution, RQ, or positive hypothesis. Negative
development evidence remains internal and does not enter the paper.
