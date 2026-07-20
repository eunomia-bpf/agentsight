# Experiment Plan: RQ3 Global Task-Semantic Segmentation

## Research Question

- RQ exactly as written in the paper: **How Accurate Are the Tags?**
- Specific uncertainty tested here: can one source-only, whole-trajectory model
  pass recover a coherent variable-depth task/subtask path and the contiguous
  human workflow-stage partition better than the current label-free recurrence
  constructor?
- Why the answer matters: the paper's main profile must explain how an agent
  decomposes and advances a concrete task. A profile whose main frames are
  agent, session, tool, command, path, or status is only a grouped runtime log.

## Paper-Value Admission

- Planned role: decisive RQ3 mechanism experiment.
- Largest credible paper story this experiment could unlock: AgentProf can turn
  a completed source-native agent trajectory into the intended profile
  structure

  ```text
  concrete task -> nested subtask -> phase/strategy
                -> semantic action -> operation object -> result
  ```

  while retaining agent/model/session/tool/command/path/status only as metadata,
  filters, colors, measures, or drill-down evidence.
- Strongest reviewer reject argument addressed: the current automatic
  constructors recover flat stage-like partitions but do not demonstrate that
  the visible stack is task semantic.
- Independent evidence beyond existing runs: Step0050--Step0052 and
  Step0054--Step0056 make local causal transition decisions. This experiment
  instead observes the complete completed trajectory once and emits a globally
  coherent interval decomposition. It has no online transition policy,
  threshold, feature score, depth cap, or post-hoc leaf deletion.
- Why the result is not already settled: existing recurrence is label-free and
  existing Qwen runs are causal. Neither tests whether completed-trajectory
  context lets a small model infer persistent task instances and their outcomes.
- Paper decision if positive: adopt the global semantic constructor, update
  only the implementation/evaluation description and one representative
  task-semantic figure, and preserve the exact thesis, title, four RQs, and
  story.
- Paper decision if contradictory, mixed, or inconclusive: reject only this
  constructor. Keep the result in experiment history; do not narrow the thesis,
  RQs, contribution, hypothesis, or positive paper story.
- Best alternative: another local push/pop/stay prompt. Step0056 closed that
  family, so it has less decision value than testing global context.

## Expected And Alternative Outcomes

- Current expected answer: a global task-semantic interval decomposition will
  exceed current recurrence on ordinary unweighted B-cubed F1 and yield a
  visibly task-centered representative profile.
- Strongest competing explanation: Qwen2.5-3B can summarize a completed
  trajectory but still chooses partitions whose semantic coherence does not
  correspond to independently annotated workflow stages.
- Contradictory result: candidate-minus-current-recurrence B-cubed F1 has a
  task-cluster bootstrap interval whose upper bound is at most zero, or the
  generated records violate the fixed semantic-frame contract.

## External Precedent And Real Assets

- Closest external protocols: the April 2026 GUIDE arXiv preprint decomposes a
  completed GUI-agent trajectory into coherent subtasks for diagnosis; Activity Mining by Global
  Trace Segmentation constructs activity trees from complete event logs; Grosz
  and Sidner formalize nested intention stacks. These establish global
  completed-trajectory decomposition and task stacks as precedents, not the
  AgentProf contribution.
- Official assets: the preselected 405 reconstructable failed trajectories
  from CodeTraceBench's 1,000-row public manifest: 20,866 operations, 17,148
  source-native turns, 2,948 independent human stage spans, 251 task clusters,
  and all four official frameworks.
- Model: the fixed local `Qwen2.5-3B-Instruct-Q4_K_M`, temperature zero and
  seed `20260720`, served by a dedicated single-slot llama.cpp process with the
  model's native effective 32,768-token context. The existing four-slot server on port 18182
  exposes only 16,384 tokens per slot and is not used.
- What is reused: exact Step0056 source-native reconstruction, current
  multi-resolution recurrence assignments, verified human-stage manifest,
  standard scorer definitions, and task-cluster bootstrap.
- Necessary custom glue: one thin adapter serializes each complete trajectory,
  requests semantic intervals, validates exact turn coverage and proper path
  syntax, expands intervals to operations, and renders one profile. It does not
  invent a benchmark or metric. Every turn is retained with fixed visible-text
  caps of 256 intent characters, 128 progress characters, 128 action
  characters, and 256 result characters so the complete selected workload fits the
  model's native context.

## Proposed Method

The immutable root is the concrete user task. One model call sees the complete
ordered source-native trajectory, including each turn's native intent,
progress, planned action, and visible result. It returns contiguous intervals:

```json
{
  "through": 18,
  "subtask_path": "verify the profiling claim > inspect evaluation evidence",
  "phase": "collect evidence",
  "action": "check reported measurements",
  "object": "results summary",
  "result": "evidence remains insufficient"
}
```

Each non-final interval reports only its inclusive `through` turn. Its start is
the previous interval's end plus one, and the final interval always ends at the
last trajectory turn. Coverage is therefore structural rather than a pair of
redundant model-generated bounds. Intervals cover every turn exactly once in
order. `subtask_path` is a single parent-to-child string separated by `>` and
may have any natural number of frames, including zero; there is no configured
frame-count limit. The full visible stack is the fixed task root followed by
the parsed subtask path, `phase`, `action`,
`object`, and `result`. Longest-common-prefix differences between consecutive
paths define the corresponding stack pops and pushes; there is no learned
transition controller. Raw commands, file paths, tools, statuses, agent,
model, and session never become leading responsibility frames. They remain
lineage and drill-down attributes.

The model may place a meaningful file or system component in the operation
object frame, because that frame answers what the semantic action concerns. It
may not replace task/subtask/phase/action with a tool or field name.

## Comparison

- Proposed method: global task-semantic interval decomposition.
- Main baseline: current multi-resolution recurrence, B-cubed F1 `0.662740` on
  the same 405 trajectories. It is the strongest adopted label-free constructor
  and represents recurrence-derived continuity without model interpretation.
- Control: Step0056 exact-leaf causal Qwen stack, B-cubed F1 `0.649878`, which
  represents the strongest completed local transition policy using the same
  source-native turns and model.
- No matched baseline rerun is needed: both fixed operation assignments already
  cover the identical population and will be read directly.
- Human stages and solved/quality labels remain unavailable during inference.
  They are opened only after all candidate assignments have been materialized.

## Workloads And Metrics

- Workload: all 405 preselected reconstructable failed CodeTraceBench
  trajectories; no sampled smoke run substitutes for this complete selected
  workload. This is not described as all 1,000 manifest rows.
- Primary metric: ordinary unweighted operation-level B-cubed precision,
  recall, and F1, as defined by Bagga and Baldwin for hard partitions.
- Secondary diagnostics: exact adjacent-boundary precision/recall/F1 and exact
  unlabeled span precision/recall/F1. They do not override the primary metric.
- Semantic contract checks: every turn and operation is covered exactly once;
  intervals are ordered and nonoverlapping; labels are nonempty; generated
  task/subtask/phase/action/object/result frames exclude the forbidden
  system-field hierarchy; one representative complete profile is inspected
  against raw lineage.
- Hierarchy boundary: CodeTraceBench provides one flat workflow-stage level, so
  B-cubed evaluates the candidate's contiguous interval instances, not full
  nested-tree correctness. The generated hierarchy is reported as qualitative
  representation evidence until an official nested-tree gold set is available.
- Uncertainty: 10,000 paired resamples over the 251 underlying task clusters,
  retaining all trajectories for a sampled task.
- Cost: 405 model calls, rather than one call per turn or operation. Existing
  context measurements put all complete projected trajectories plus at least a
  4,096-token completion budget and margin within the model's native
  32,768-token context.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | executable-path check | one complete trajectory from each framework | global semantic interval decomposition | 1 deterministic pass | proceed only if real extraction, model inference, expansion, and scoring run end to end |
| main | proposed | all 405 trajectories | global semantic interval decomposition | 1 deterministic pass | primary candidate evidence |
| baseline | fixed comparison | same 405 trajectories | current multi-resolution recurrence | reuse complete assignments | strongest comparison |
| control | mechanism comparison | same 405 trajectories | Step0056 causal exact-leaf stack | reuse complete assignments | isolates whole-trajectory context from local transitions |

## Execution

- Adapter: `script/rq3_global_task_semantic_segmentation_eval.py`.
- Server command:

  ```bash
  /home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
    -m /home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf \
    -ngl 99 -c 32768 -np 1 --host 127.0.0.1 --port 18183 \
    --seed 20260720 --temp 0 --metrics \
    --log-file .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/llama-server.log
  ```

- Real preflight: verify port 18183 reports `total_slots=1` and
  `n_ctx=32768`; select the projected-token-longest complete trajectory in
  each of the four frameworks; verify each exact prompt plus the retained
  completion budget and 512-token margin fits; then run real model inference, interval validation,
  operation expansion, and the standard scorer path.
- Preflight command:

  ```bash
  python3 script/rq3_global_task_semantic_segmentation_eval.py infer preflight \
    --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
    --source-cache-dir .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/full/sessions \
    --turn-assignments .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/predictions.jsonl \
    --llama-url http://127.0.0.1:18183 --workers 1 --timeout-seconds 1200 \
    --out .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/preflight

  python3 script/rq3_global_task_semantic_segmentation_eval.py score \
    --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
    --predictions .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/preflight/predictions.jsonl \
    --inference-summary .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/preflight/inference-summary.json \
    --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
    --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
    --causal-score-rows .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/score/operation-score-rows.jsonl \
    --out .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/preflight/score
  ```
- Full commands use the same arguments, replace `preflight` by `full`, and
  require the same single-slot server:

  ```bash
  python3 script/rq3_global_task_semantic_segmentation_eval.py infer full \
    --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
    --source-cache-dir .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/full/sessions \
    --turn-assignments .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/predictions.jsonl \
    --llama-url http://127.0.0.1:18183 --workers 1 --timeout-seconds 1200 \
    --out .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/full

  python3 script/rq3_global_task_semantic_segmentation_eval.py score \
    --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
    --predictions .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/full/predictions.jsonl \
    --inference-summary .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/full/inference-summary.json \
    --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
    --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
    --causal-score-rows .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/score/operation-score-rows.jsonl \
    --out .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/score
  ```
- Full inference root:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-v1/full/`.
- Full score root:
  `.agentsight/experiments/rq3-global-task-semantic-segmentation-v1/score/`.
- Completion: 405/405 trajectories, 17,148/17,148 turns, and
  20,866/20,866 operations have valid candidate assignments; all planned
  primary/secondary metrics and 10,000 paired task-cluster resamples exist; one
  representative complete flamegraph is rendered.
- Cache one source-hashed response per trajectory so an interrupted complete run
  resumes without changing completed outputs.

## Interpretation

- Positive: candidate-minus-current-recurrence B-cubed F1 has a paired 95%
  interval strictly above zero, population B-cubed F1 is higher, all semantic
  contract checks pass, and the independent result review finds the
  task-semantic figure faithful to its raw trajectory.
- Contradictory: the interval is wholly nonpositive or semantic contract checks
  fail. Reject the constructor only.
- Mixed/inconclusive: point estimate improves but the interval crosses zero, or
  quantitative partitions improve while the required semantic representation
  is not faithful. Do not adopt until the same completed result is interpreted;
  do not choose another benchmark or metric to rescue it.
- Target output: one standard-metric comparison table and one representative
  task-semantic flamegraph with operation count as width and
  agent/model/tool/status only as metadata. CodeTraceBench does not provide
  comparable per-operation time or token mass, so those widths are not invented.

## Reproducibility Notes

- Data, model, seed, server, source reconstruction, baselines, and scorer are
  the already completed Step0056 environment.
- The run is deterministic at temperature zero. Raw requests, responses,
  assignments, summary, score rows, and the rendered profile are retained.
- A real server startup showed that llama.cpp caps this model at its native
  32,768-token training context. With the fixed per-field projection above, the
  longest measured complete input is 27,552 tokens. Each request receives the
  available completion budget between 4,096 and 8,192 tokens, so input, output
  budget, and margin fit without rope
  scaling or trajectory truncation.
- The adapter reuses the completed source-only Step0049 operation projections
  and Step0056 native-turn assignments rather than reopening every compressed
  benchmark archive. It reconstructs all 20,866 source operations and 17,148
  turns exactly before any model call; this changes execution cost, not visible
  evidence or the scientific method.
- One complete-run response exposed an output-schema failure: the model treated
  the unbounded `subtasks[]` array as a sequential plan and repeated steps until
  the completion limit, while the other first 331 responses collapsed to one
  whole-trajectory segment. The one final interface revision encodes the active
  nested path as a single `parent > child` string and explicitly rejects both a
  whole-trajectory summary and per-turn fragmentation in the prompt. This keeps
  the same global-context hypothesis, model, evidence, standard metrics, and
  semantic stack. No further prompt/schema variant is admitted after this run.
- This is an offline completed-trajectory profiler. It does not claim online
  task-stack recovery.
