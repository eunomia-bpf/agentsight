# Experiment Plan — Result-Grounded Task Stack

## Research Question

- Paper question, unchanged: **RQ3 — How Accurate Are the Tags?**
- Tested uncertainty: can the same small local model maintain a useful
  variable-depth task stack when opening a task and closing a task are grounded
  in the two different observations that justify them?
- Why it matters: the desired profile must represent the agent's persistent
  task decomposition, not a stack of commands, files, phases, or status fields.

## One Hypothesis And Paper Value

**Hypothesis.** Across the complete public collection of ToolSandbox execution
conditions with published per-turn subgoal progress, replacing the single mixed
`stay / push / pop` decision with an intent-grounded OPEN followed by a
result-grounded CLOSE will align task-closing events with externally evaluated
subgoal-completion turns more accurately than both the Step 0059 controller and
the current recurrence constructor, with wholly positive paired scenario-level
intervals. Complete CodeTraceBench B-cubed results are retained as a partition
compatibility/regression result, not as the adoption oracle for task/subtask
semantics.

The mechanism remains a literal stack. Each non-root frame stores only:

```text
(task label, observable completion condition)
```

The completion condition is controller memory, not a displayed stack level.
It makes the semantic claim behind a push explicit and gives a later pop a
specific fact to check.

- Positive consequence: retain this constructor for integration with the
  event-local suffix, while preserving the stated limits on topology and label
  validation.
- Contradictory or inconclusive consequence: retain the recurrence constructor
  and reject this fixed policy; do not narrow RQ3, the hierarchy, or the paper
  story.
- Direct thesis challenge: none. The thesis remains exactly **“Agent
  observability needs profiling, not only debugging.”**

## Why This Is A Non-Equivalent Mechanism Test

Step 0059 made one transition decision before each source-native turn. The
same prompt exposed the next turn's semantic intent, progress statement,
planned command/action, and the preceding visible result. That controller
opened 5,343 effective frames but closed only 128. Inspection shows the small
model frequently copied `cd`, file paths, implementation actions, tests, and
phase-like text into persistent frames. Although its stack was mechanically
well nested, its decision did not distinguish evidence that a task starts from
evidence that a task finishes.

This experiment changes that causal interface:

1. **OPEN:** before assigning a source-native turn, inspect its high-level
   visible intent/progress. Return `continue` or `start(label, done_when)`;
   `start` pushes exactly one child.
2. Assign that turn's operations to the resulting path.
3. **CLOSE:** after the turn's visible result exists, compare it against the
   active leaf's stored completion condition. Return `keep` or `complete`;
   `complete` records a task-completion event; a completed subtask pops one
   frame, whereas a completed immutable root remains active under the latch
   rule.

On CodeTrace the persistent controller never receives the raw planned
command/action, tool, file, path, model, agent identity, status, human stage,
score, or oracle. On ToolSandbox, which lacks source-native intent text, OPEN
may read the prefix-visible requested tool call as evidence but may not copy it
as a persistent frame. Result/state evidence is exposed only to CLOSE. Model
identity, published subgoals, progress scores, later turns, and all evaluation
oracles remain hidden. The excluded system fields remain event-local evidence
or metadata for the eventual lower suffix and visualization.

This is not a prompt/model sweep, depth rule, threshold, feature score, label
cleanup, contraction, or post-hoc segmentation. It tests one missing semantic
primitive: an explicit, observable completion contract attached to each task
frame.

## Fixed Representation Contract

The intended profile remains exactly:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

This experiment evaluates only `concrete task -> nested subtask*`. The root is
immutable, depth is variable and uncapped, and the displayed identity is the
ordered task-label path. Phase/strategy, semantic action, object, and result
are event-local suffix frames; agent, model, session, prompt, tool, command,
path, and status are metadata, filters, visual encodings, measures, details, or
source evidence.

One task occurrence is one maximal contiguous run of the exact visible task
path. Controller frame IDs and `done_when` text are not scored identities.

## Fixed State Machine

For source-native turn `t`:

```text
OPEN(current high-level intent)
if start(label, done_when): push exactly one leaf

assign turn t to the resulting exact task path

CLOSE(current visible outcome, active done_when)
if complete:
    record completion
    if the active leaf is a subtask: pop exactly one leaf for turn t + 1
    if the active leaf is the root: keep the immutable root
```

The root's completion condition is the user's concrete task being satisfied
and truthfully reported. Root completion is latched so unchanged later turns
do not emit duplicate events; opening new child work clears that latch. At most
one push and one pop occur per turn. A one-turn subtask may therefore
open, own the turn's operations, and close after its result. A sibling can
begin only on the following turn from the returned parent. The model cannot
jump to an arbitrary ancestor. Exact duplicate active labels are
identity-preserving continues. No maximum depth, normalization, fuzzy match,
embedding, threshold, contraction, phase filter, or after-the-fact pruning is
used. Model-proposed non-task labels are retained in raw predictions and
counted as semantic limitations. This test can authorize the completion-timing
mechanism, not generated-label validity.

An OPEN label must be a concrete multi-step goal such as `write the paper` or
`write the abstract`, not `run grep`, `edit main.tex`, `test`, `phase 3`, or a
file/path/status/result description. `done_when` must state an observable
outcome, such as `the abstract expresses the problem, insight, method, and key
result`, rather than another action.

## Fixed Model, Public Workload, Existing Regression Workload, And Isolation

- Model: the same local Qwen2.5-3B-Instruct Q4_K_M artifact used by Step 0059,
  SHA-256 `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`.
- Decoding: temperature zero, seed `20260720`, grammar-constrained JSON.
- Primary public workload: every released ToolSandbox trial JSON in
  `SAP/agent-quality-inspect`: six agent models, expert and nonexpert user
  personas, all eight trials, and all available runs of the 37 official
  ToolSandbox scenario names. The release contains 96 trial files, 12 complete
  model/persona conditions, 3,551 available trajectories, and 9,485 observed
  turns. One expected trajectory is absent from the public release and is
  reported as unavailable rather than synthesized. The files contain the full
  user/assistant/tool trace, fixed natural-language subgoals used by the
  published TED evaluation, and a published monotone `progress_rates` curve.
  This is the complete released ToolSandbox trial population, not a selected
  model, persona, scenario, or success subset.
- Existing regression workload: all 405 reconstructable failed
  CodeTraceBench trajectories, 17,148 source-native turns, and 20,866
  operations across four frameworks and five source layouts.
- Human stages, stage count, recurrence assignments, prior predictions,
  framework/model/session labels, and success/failure remain invisible during
  inference.
- The source archives and operation populations are reused. Only model outputs
  for byte-identical CLOSE or OPEN requests may be reused; Step 0059 responses
  are not compatible.

For CodeTrace OPEN, the controller reads only the concrete task, active task
frames, and current source-native intent/progress. CLOSE reads the same task
memory plus the current intent/progress and visible result. Raw planned
commands/actions are withheld from persistent frame decisions.

For ToolSandbox, which does not expose private chain-of-thought intent, OPEN
reads the current user utterance and, when present, the prefix-visible tool-call
request (name and arguments) before its result. An assistant-only natural-
language response is an outcome and is withheld from OPEN. CLOSE
then reads the tool result, visible state delta, and/or agent response from
that same turn. Tool name/arguments are evidence; they are forbidden in the
persistent label unless rewritten as a user-facing task goal. Agent/model
identity, published subgoals, `progress_rates`, and all later turns are hidden.

## Primary Completion Comparison And Standard Metrics

- Candidate: this fixed combined result-grounded OPEN/CLOSE controller.
- Mechanism baseline: the Step 0059 `stay / push-one / pop-one` controller,
  applied to the same ToolSandbox turn representation with the same fixed
  model. Its applied `pop` events are predicted completion boundaries.
- Incumbent baseline: the existing multi-resolution recurrence constructor,
  applied to the same ordered visible operation signatures across all released
  runs of each scenario. A change of recurrence occurrence is a predicted
  boundary.
- Trivial control: predict a completion boundary after the first observed turn
  of every trajectory and nowhere else. On the complete released population
  this fixed control has pooled micro `P=0.667699`, `R=0.613137`, and
  `F1=0.639256`; it is registered before candidate inference.
- Published completion reference: for each released trajectory, a gold
  completion boundary is a turn whose published TED `progress_rates` value is
  strictly greater than the preceding value (zero before the first turn).
  TED computes this curve by judging the fixed natural-language ToolSandbox
  subgoals against each trajectory prefix. The stored curves are monotone.
  Some files pad the curve to `max_turns`; only indices backed by an observed
  trajectory turn are eligible. The five positive changes found only in the
  padded suffix are excluded because no corresponding trace boundary exists.
  Multiple subgoals completed in one turn therefore form one boundary;
  subgoals never completed create no boundary.
- Completion is success-only for both candidate and Step 0059 comparison in
  this public test. Failed or abandoned terminal boundaries are outside the TED
  positive-progress target and are not claimed here.
- Time alignment: candidate CLOSE after turn `t` maps to boundary `t`.
  A Step 0059 pop proposed before turn `t+1` from turn `t`'s result maps back to
  boundary `t`. A recurrence operation boundary maps to the turn containing
  the operation on its left; multiple predicted boundaries in one turn are
  deduplicated. No method receives an implicit completion merely because a
  trajectory or recurrence occurrence terminates. Candidate CLOSE on the final
  observed turn is explicit and therefore eligible; a Step 0059 stack still
  active at termination predicts no final boundary.
- Primary standard metric: exact turn-boundary precision, recall, and F1 on all
  released trajectories. Point estimates pool TP/FP/FN over all trajectories
  (micro aggregation); no temporal tolerance window is used.
- Primary uncertainty: 10,000 paired bootstrap resamples over the 37 scenario
  IDs, keeping every model, persona, and available trial of a sampled scenario
  together. Each draw recomputes pooled TP/FP/FN and micro F1, for candidate
  minus each of the two mechanism baselines and the first-turn control.
- Positive: candidate point F1 exceeds all three comparisons and all three
  paired 95% intervals are wholly positive. Contradictory: any interval is
  wholly negative. Otherwise: inconclusive and not adopted. Merely exceeding
  Step 0059 or recurrence while failing to exceed first-turn-only is not
  evidence of useful completion timing.

The public reference is an externally released LLM-judge progress evaluation,
not manual temporal gold and not ToolSandbox's hidden official
`milestone_mapping`. The experiment will report that source plainly. The 37
scenario definitions are also checked against the official ToolSandbox repo;
all names must resolve. This primary test validates completion-event timing,
not full nested topology or open-vocabulary label equivalence.

## CodeTrace Partition Compatibility

- Main baseline: current multi-resolution recurrence assignments.
- Mechanism baseline: corrected Step 0059 contiguous task occurrences.
- Standard metric: ordinary operation-level B-cubed precision, recall, and F1
  against session-local human workflow-stage occurrences.
- Uncertainty: 10,000 paired bootstrap resamples over the fixed 251 task
  clusters for candidate minus each baseline B-cubed F1.
- Standard secondary metrics: adjacent-boundary precision/recall/F1 and exact
  span precision/recall/F1.
- Descriptive diagnostics: CLOSE/OPEN counts, task depth, frame closure rate,
  duplicate-label continues, command/path-like labels, phase-like labels,
  coverage, latency, and model tokens. They explain behavior but are not extra
  acceptance gates.

CodeTrace's flat stages validate only partition compatibility. They belong to
the phase/strategy level and therefore cannot authorize or reject a
task/subtask constructor by themselves. They do not validate ancestor
names/topology, cross-run semantic equality, or the lower suffix.

## Source Acquisition, Cost, And Completion

- Source metadata and file list come from the public Hugging Face repository
  `SAP/agent-quality-inspect` at revision
  `593e686f4d0c2e9fcae5ae664c16a7687907cf97`. Download
  every `toolsandbox/**/trial_*_results.json` file.
- Validate 96 files, 12 model/persona conditions, eight trial IDs per
  condition, 3,551 unique `(model, persona, trial_id, sample_id)` trajectories,
  37 unique official scenario names, 9,485 observed turns, 3,867 eligible
  positive progress boundaries, monotonic observed progress, and all scenario
  names present in the official Apple ToolSandbox scenario sources. Record the
  one source-missing trajectory and never fabricate it.
- Maximum ToolSandbox controller work is 28,455 small-model
  requests: one candidate OPEN and at most one candidate CLOSE plus one Step
  0059 baseline request per turn. Expected CodeTrace controller work is at
  most 34,296 OPEN/CLOSE requests; on the observed local endpoint this is
  expected to complete within roughly one GPU-hour.
- Complete means every admitted trajectory has durable candidate/baseline
  predictions and every registered metric/paired interval has been computed.
  A weak preflight does not stop either full run.
- Private raw and cache root:
  `.agentsight/experiments/rq3-result-grounded-task-stack-v1/`.

## Planned Execution

1. Implement one thin evaluator by reusing the verified source reconstruction,
   model client, exact-path scorer, standard metrics, and bootstrap code.
2. Run one complete CodeTrace trajectory from each source layout and one
   complete ToolSandbox trajectory through OPEN/CLOSE. Repair only malformed
   I/O or state wiring; do not tune semantic behavior.
3. Run all 3,551 available public ToolSandbox trajectories across all 96
   released trial files and 12 model/persona conditions, plus all 405
   CodeTrace trajectories, to completion even if preflight behavior is weak.
4. Materialize all candidate and baseline predictions before opening published
   progress curves or CodeTrace human stages, then compute the registered
   metrics and intervals.
5. Obtain an independent raw-result review and outer audit before disposition.

One fixed controller, one model, two complementary complete public/existing
workloads, and one scorer per workload are admitted. No prompt variants,
completion thresholds, depth variants, model sweep, score calibration, or
paper edit are admitted. The intervention is correctly described as the
combined result-grounded OPEN/CLOSE controller; without an ablation, no result
is attributed solely to `done_when`.

## Commands

```bash
hf download SAP/agent-quality-inspect --repo-type dataset \
  --revision 593e686f4d0c2e9fcae5ae664c16a7687907cf97 \
  --include 'toolsandbox/**/trial_*_results.json' \
  --local-dir .agentsight/external/agent-quality-inspect-complete

python3 script/rq3_result_grounded_task_stack_eval.py inspect-toolsandbox \
  --source .agentsight/external/agent-quality-inspect-complete/toolsandbox \
  --official-source .agentsight/external/ToolSandbox/tool_sandbox/scenarios \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/source

python3 script/rq3_result_grounded_task_stack_eval.py infer-toolsandbox preflight \
  --visible-trajectories .agentsight/experiments/rq3-result-grounded-task-stack-v1/source/visible-trajectories.jsonl \
  --llama-url http://127.0.0.1:18181 \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-preflight

python3 script/rq3_result_grounded_task_stack_eval.py infer-toolsandbox full \
  --visible-trajectories .agentsight/experiments/rq3-result-grounded-task-stack-v1/source/visible-trajectories.jsonl \
  --llama-url http://127.0.0.1:18181 --workers 8 \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-full

python3 script/rq3_result_grounded_task_stack_eval.py score-toolsandbox \
  --visible-trajectories .agentsight/experiments/rq3-result-grounded-task-stack-v1/source/visible-trajectories.jsonl \
  --completion-key .agentsight/experiments/rq3-result-grounded-task-stack-v1/source/completion-key.jsonl \
  --predictions .agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-full/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-full/inference-summary.json \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-full/score

python3 script/rq3_result_grounded_task_stack_eval.py infer-codetrace preflight \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18181 \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/codetrace-preflight

python3 script/rq3_result_grounded_task_stack_eval.py infer-codetrace full \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18181 --workers 8 \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/codetrace-full

python3 script/rq3_result_grounded_task_stack_eval.py score-codetrace \
  --predictions .agentsight/experiments/rq3-result-grounded-task-stack-v1/codetrace-full/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-result-grounded-task-stack-v1/codetrace-full/inference-summary.json \
  --step0059-score-rows .agentsight/experiments/rq3-well-nested-task-stack-v1/full/score/operation-score-rows.jsonl \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/codetrace-full/score
```

## Metric And Dataset Sources

- ToolSandbox benchmark and Milestone-DAG design: Lu et al., 2024/NAACL 2025,
  <https://arxiv.org/abs/2408.04682> and
  <https://github.com/apple/ToolSandbox>.
- Published traces, subgoals, and per-turn TED progress curves: Chong et al.,
  ICLR 2026, <https://openreview.net/forum?id=fHsVNklKOc> and
  <https://huggingface.co/datasets/SAP/agent-quality-inspect>.
- Exact boundary precision/recall/F1 follows the standard segmentation
  boundary TP/FP/FN definition described by Çöltekin, 2017,
  <https://doi.org/10.1111/cogs.12454>, with zero tolerance.
- B-cubed follows Bagga and Baldwin, 1998,
  <https://aclanthology.org/P98-1012/>.

## Expected Paths

- evaluator: `script/rq3_result_grounded_task_stack_eval.py`
- private full artifacts:
  `.agentsight/experiments/rq3-result-grounded-task-stack-v1/`
- public step record:
  `docs/tmp/build-and-evaluate/step-0060-20260720T162207-0700/`

## Post-Execution Authority Addendum

Independent raw-result review found that the first r6 candidate CLOSE prompt
serialized an internal sequence-bearing frame instance. The scientific plan,
workloads, metrics, and state machine above remain unchanged, but the original
`toolsandbox-full` candidate and partial `codetrace-full` candidate are invalid
historical artifacts. The authoritative repair projects the active leaf to
`{label, done_when}` and uses separate r7 output paths:

```bash
python3 script/rq3_result_grounded_task_stack_eval.py infer-toolsandbox full \
  --visible-trajectories .agentsight/experiments/rq3-result-grounded-task-stack-v1/source/visible-trajectories.jsonl \
  --baseline-cache-dir .agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-full/sequences/step0059 \
  --llama-url http://127.0.0.1:18181 --workers 8 \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-full-r7

python3 script/rq3_result_grounded_task_stack_eval.py infer-codetrace full \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18181 --workers 8 \
  --out .agentsight/experiments/rq3-result-grounded-task-stack-v1/codetrace-full-r7
```

All authoritative score and report paths are under these `*-full-r7`
directories. The r6 Step 0059 baseline caches are valid and were replay-
validated before read-only reuse; no r6 candidate result is authoritative.
