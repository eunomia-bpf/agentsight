# Experiment Plan: RQ3 Stateful Task-Stack Fidelity

## Research Question

- RQ exactly as written in the paper: **RQ3 — How accurate are the tags?**
- Specific uncertainty tested here: whether a persistent variable-depth task
  stack, updated from each source-native agent turn under a strict task-frame
  rule, recovers human workflow stages more accurately than the current
  label-free recurrence constructor.
- Why the answer matters: the paper's semantic flamegraph needs a principled
  `concrete task -> nested subtask` prefix. System fields and one-frame-per-call
  labels cannot supply that structure.

## Paper-Value Admission

- Planned role: decisive mechanism experiment for the task/subtask prefix.
- Largest credible paper story this experiment could unlock: AgentProf can use
  a persistent task-semantic backend, then attach phase/action/object/result
  evidence below it, rather than merely grouping calls by runtime fields. Flat
  CodeTrace stages test the active task-leaf partition, not the full topology.
- Strongest reviewer reject argument or load-bearing uncertainty addressed:
  the proposed semantic stack may be only an unstable LLM relabeling of each
  tool call, not a persistent task decomposition.
- Independent evidence added beyond existing runs and published results: a
  fixed online stack policy on all 405 public CodeTraceBench failed
  trajectories, using native intent/progress unavailable to Step 0049 and
  preserving exact variable-depth state unavailable to Step 0053.
- Why the result is not tautological, already settled, or dominated: Step 0049
  tested an operation-level policy without an immutable source-task root or
  native intent/progress and collapsed to near singletons; Step 0053 tested a
  memoryless adjacent classifier and over-merged. Neither tests this stateful
  mechanism.
- Paper decision if positive: adopt the task-stack constructor for the semantic
  hierarchy prefix and synchronize the RQ3 mechanism/evidence slots without
  changing the fixed thesis, story, or RQs.
- Paper decision if contradictory, mixed, or inconclusive: reject only this
  fixed transition policy, retain the source evidence and target hierarchy, and
  return the mechanism choice to the outer loop. Do not narrow the thesis or
  replace the four RQs.
- Best alternative experiment and why this one has higher decision value: a
  GUIDE-style whole-trajectory segmenter has global context and is the strongest
  alternative, but it does not test the user's simpler persistent online stack
  and cannot directly represent push, return, and variable-depth nesting.

## Expected And Alternative Outcomes

- Current expected answer: a strict task-frame rule plus persistent native-turn
  context will avoid both prior degeneracies and exceed multi-resolution
  recurrence on ordinary B-cubed F1.
- Strongest competing explanation: Qwen2.5-3B cannot reliably distinguish a
  multi-operation task from the current atomic action, so it will still create
  near-singleton frames or over-merge at the root.
- Result that would contradict the expectation: the candidate does not exceed
  the current multi-resolution recurrence B-cubed F1 under the registered
  paired task-cluster uncertainty test.

## Published Precedent And Real Assets

- Closest published protocol: Grosz and Sidner's focus/intention stack supplies
  the push/subordination and pop/return semantics; GUIDE supplies the closest
  recent precedent for reconstructing coherent agent subtasks from action
  trajectories; CodeTraceBench supplies public agent traces and human workflow
  stages.
- Official system/model/data/benchmark/tool and version: the existing complete
  CodeTraceBench population (405 source-valid trajectories, 20,866 operations,
  2,948 verified stages), fixed Qwen2.5-3B-Instruct Q4_K_M on llama.cpp, and the
  existing standard ordinary B-cubed scorer.
- What is reused: raw source archives, exact source adapters, verified stage
  manifest, Step 0053 native intent/progress/action/result reconstruction,
  current multi-resolution recurrence assignments, model binary, seed, and
  standard scoring code.
- Necessary deviations or custom glue: exact native turns are reconstructed
  from message, response, trajectory-element, or model-response identity; the
  model returns one legal stack transition per turn. No new benchmark, custom
  oracle, nonstandard primary metric, score cutoff, or post-hoc contraction is
  introduced.

## Comparison

- Proposed system or method: an immutable concrete-task root plus zero or more
  persistent subtask frames. Let `d` be the mutable subtask depth; the root is
  outside this index and can never be removed. For each new source-native turn,
  the fixed model sees the complete current stack, the turn's native
  intent/progress and planned action, and only the preceding turn's result. It
  returns exactly one of these JSON objects:
  `{"transition":"stay"}` leaves the stack unchanged;
  `{"transition":"push","label":"..."}` appends one fresh subtask instance;
  `{"transition":"pop","target_depth":k}` retains the first `k` mutable
  frames, where `0 <= k < d`; or
  `{"transition":"replace","target_depth":k,"label":"..."}` retains the
  first `k` frames and appends one fresh instance, where `0 <= k < d`.
  Every label is a concise task-goal phrase. Each push/replace creates a unique
  instance even if the label appeared earlier. All operations in the turn
  inherit the resulting active leaf, or the immutable root at depth zero.
  Depth has no fixed cap and each turn can add at most one frame.
- Task-frame rule: a persistent node must be a concrete goal or responsibility
  with a completion condition that can span multiple turns. Phase/strategy,
  semantic action, operation object, current result, tool, command, file, path,
  status, inspect, edit, test, retry, and any one atomic operation are transient
  evidence only. A change in any of them cannot by itself cause `push` or
  `replace`. The current turn's result is attached below the task path after the
  transition and is visible only as `preceding result` on the next turn; it does
  not participate in the current transition or B-cubed group identity.
- Validity rule: the grammar permits only legal transitions for the current
  depth. An illegal/malformed response, a target depth outside the frozen range,
  an empty/invalid label, missing source evidence, or inability to fit the
  complete untruncated stack plus the fixed minimum turn evidence in the model
  context makes the run invalid. Evidence fields may use fixed pre-registered
  clipping, but the active stack is never clipped and the prompt is not changed
  after preflight.
- Main baselines and the competing position each represents:
  multi-resolution recurrence represents the strongest current label-free
  constructor on the same complete population.
- Why each main baseline needs a matched run instead of citation alone: the
  existing assignments can be rescored on exactly the same operations and gold
  stages; no baseline rerun is needed.
- Controls or ablations, labeled separately: one-span, per-native-turn, and the
  already completed Step 0049 operation-stack policy diagnose over-merging,
  over-segmentation, and whether the new semantic contract changes behavior.
- Conclusion if each main baseline matches or wins: this fixed task-stack
  transition policy is not adopted; no paper-level thesis or RQ is changed.
- Information, tuning, and compute fairness: the candidate cannot read human
  stages, recurrence assignments, framework/model/session/status fields, or
  scorer outputs. The prompt, grammar, model, temperature, and seed are fixed
  before the official stages are opened.
- Split or leakage rule when relevant: inference reads public task and
  source-native trajectory only. The verified stage manifest is score-only.

## Workloads And Metrics

- Real workloads or tasks: all 405 source-valid failed CodeTraceBench
  trajectories from MiniSWE, SWE-agent, OpenHands, and Terminus2.
- Primary metrics: ordinary B-cubed precision, recall, and F1 against verified
  human workflow stages, with paired task-cluster bootstrap uncertainty.
- Correctness check or ground truth: 2,948 verified human stages; boundary F1
  and exact-span F1 are standard secondary diagnostics. Stack legality,
  operation coverage, depth distribution, transition counts, and per-framework
  results diagnose failure modes but do not replace B-cubed.
- Repetitions, seeds, and uncertainty: deterministic inference with the fixed
  seed; 10,000 paired bootstrap resamples over 251 task clusters.
- Cost estimate when material: 17,148 or fewer model calls, one per native turn,
  reusing the local fixed model and current artifacts.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| real preflight | wiring | one real trajectory from each of five source layouts | fixed task-stack policy | 1 | verify source joins, legal transitions, coverage, and scorer execution; do not tune on gold |
| full candidate | proposed | all 405 trajectories | fixed task-stack policy | 1 | primary RQ3 mechanism decision |
| matched score | baseline/control | same 405 trajectories | multi-resolution recurrence, one-span, native-turn, prior Step 0049 | existing fixed assignments | identify improvement or degeneracy |
| uncertainty | analysis | 251 task clusters | paired bootstrap | 10,000 | quantify candidate-minus-incumbent B-cubed F1 |

## Execution

- Authoritative command or workflow: one evaluator exposes separate `infer`
  and `score` commands. `infer` reconstructs native turns, performs legal stack
  transitions, and writes complete per-turn/per-operation artifacts; `score`
  opens the verified stages and matched assignments afterward.
- Real preflight case: the smallest complete trajectory for each of the five
  fixed source layouts, including a real multi-command Terminus2 response.
- Full completion rule: all selected source-native turns receive exactly one
  legal transition; all 20,866 operations appear exactly once under a valid
  root-to-leaf task path; every selected trajectory and framework is scored.
- Raw-result path:
  `.agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/`.
- Checkpoint or recovery approach: atomic per-session caches allow safe resume;
  cached entries are accepted only when their fixed prompt/model/config and
  expected session coverage match.

## Interpretation

- Positive result: adopt the constructor's active-leaf backend if
  candidate-minus-multi-resolution B-cubed F1 is positive with a paired 95%
  interval above zero. Per-framework deltas are reported as heterogeneity, not
  added as an unregistered veto.
- Negative or contradictory result: reject this fixed policy and preserve the
  intended task-semantic hierarchy as an open mechanism problem; do not convert
  system fields into task frames or weaken the paper story.
- Mixed or inconclusive result: report the exact supported framework/mechanism
  boundary to the outer loop without paper-story changes.
- Target paper figure or table: if adopted, a standard RQ3 comparison table and
  one source-linked task-semantic flamegraph example. The experiment does not
  claim that flat stage gold validates ancestor topology, variable depth,
  nested label meaning, or the lower `phase/action/object/result` suffix. A
  positive result authorizes the active-leaf/task-stack backend only, not the
  statement that the full actual task hierarchy has been recovered.

## Reproducibility Notes

- Software and data versions: existing repository revision at Step 0054 entry,
  CodeTraceBench artifacts and verified manifest already used by RQ3, fixed
  Qwen2.5-3B-Instruct Q4_K_M, and llama.cpp server build already recorded by the
  preceding run.
- Config and seed notes: deterministic temperature zero, seed 20260720,
  variable depth without a cap, one transition per source-native turn.
- Known deviations: 167/2,543 verified boundaries (6.57%), all in Terminus2,
  lie inside a native response turn and cannot be split by the persistent task
  leaf. The lower action/object/result evidence remains available and this
  limitation is kept explicit.
