# Experiment Plan: RQ3 Source-Native Task-Progress Boundaries

## Research Question

- **RQ exactly as written in the paper:** **RQ3: How accurate are the tags?**
- **Specific uncertainty tested here:** whether a fixed local model can recover
  the independently annotated CodeTraceBench workflow-stage partition by
  comparing adjacent *completed* operations through task-semantic evidence:
  the concrete task, the agent's own intent or progress state, the action, and
  the action result. The experiment tests one flat subtask-boundary operator;
  it does not claim to validate the entire recursive operation stack.
- **Why the answer matters:** the intended primary profile is organized by
  `concrete task -> subtask -> phase/strategy -> semantic action -> object ->
  result`. The current recurrence constructor instead derives continuity from
  action fields. A task-semantic flamegraph is credible only if task-progress
  evidence recovers human responsibility intervals better than that incumbent.

## Paper-Value Admission

- **Planned role:** decisive mechanism evidence for the stage/group component
  of RQ3.
- **Largest credible paper story this experiment could unlock:** completed
  agent trajectories contain sufficient source-native task-progress evidence
  to reconstruct profiling responsibility around what the agent was trying to
  accomplish, rather than around which tool, command, path, model, or status
  happened to appear.
- **Strongest reviewer reject argument or load-bearing uncertainty addressed:**
  the current “semantic” flamegraph may only be a system-field classification
  tree and may not represent task decomposition, progress, retry, failure, or
  result-producing work.
- **Independent evidence added beyond existing runs:** Steps 0050--0052 used
  root-task text, action fields, and the preceding observation, while omitting
  the agent's source-native per-step intent/progress and the current action
  result. This experiment changes that observable, not the transition grammar,
  recurrence cutoff, metric, or benchmark.
- **Why the result is not tautological, already settled, or dominated:** human
  stages remain unavailable until predictions are complete. Source-native
  thoughts, plans, progress markers, actions, and results are execution data,
  not stage labels. Existing recurrence is the strongest complete matched
  target-blind comparator on the same population.
- **Paper decision if positive:** adopt source-native task-progress boundaries
  for the task-semantic stage layer, then construct the primary flamegraph with
  task/subtask/result frames and retain agent/model/session/tool/status only as
  visual metadata, filters, measures, or source-linked evidence.
- **Paper decision if contradictory, mixed, or inconclusive:** do not call the
  generated grouping task-semantic or use it as a positive paper figure. Keep
  the fixed thesis, four RQs, and desired task-semantic hierarchy; return the
  tested source/model boundary to the orchestrator without another local prompt
  or grammar variant.
- **Best alternative experiment and why this one has higher decision value:**
  another stack-state, plan-inventory, recurrence-score, cutoff, or contraction
  variant reuses the same impoverished observable and has already produced
  failure or diminishing returns. Testing the missing source-native task signal
  directly is both simpler and more consequential.

## Expected And Alternative Outcomes

- **Current expected answer:** source-native intent/progress plus the completed
  action result will reduce spurious tool/file/command boundaries and recover
  human workflow stages more accurately than action-field recurrence.
- **Strongest competing explanation:** agent self-reports are absent, stale,
  overly local, or stylistically inconsistent across frameworks, and a 3B
  model cannot turn them into stable responsibility boundaries.
- **Result that would contradict the expectation:** the candidate's ordinary
  B-cubed F1 is reliably no higher than the current multi-resolution recurrence
  on the complete population.

## Published Precedent And Real Assets

- **Closest published protocol:** GUIDE partitions completed agent trajectories
  into coherent subtasks before subtask diagnosis; CodeTracer/CodeTraceBench
  releases author-verified contiguous workflow stages for completed coding-agent
  trajectories. The candidate follows that completed-trajectory, subtask-first
  information contract rather than imposing an online-causal restriction.
- **Official system/model/data/benchmark/tool and version:** all 405 public
  CodeTraceBench source-valid failed trajectories, 20,866 official operations,
  2,948 author-verified stages, and the existing llama.cpp build 9870 serving
  fixed Qwen2.5-3B-Instruct Q4_K_M.
- **What is reused:** the official archives and verified manifest; the existing
  target-operation sequence and source adapters; the current and
  multi-resolution recurrence assignments; the established target-hidden
  scorer; and standard partition/boundary metrics.
- **Necessary deviations or custom glue:** one thin source adapter exposes
  fields already present in each official archive: MiniSWE `THOUGHT` and
  returned output; OpenHands action thoughts, task-tracker progress, and tool
  results; Terminus2 `analysis`, `plan`, commands, and available result context;
  SWE-agent `thought`, action, and observation. Missing fields are represented
  as absent, never synthesized. One evaluator asks the fixed local model for
  an adjacent `continue` or `boundary` decision.

The adapter fixes operation-to-evidence alignment before inference, using the
official operation's existing `source_ref` and source action as invariants:

- MiniSWE message trajectories use the referenced assistant-message index;
  the intent is the prose outside that message's executable fence and the
  result is the return record in the following user message.
- SWE-agent trajectories use the referenced trajectory element; its `thought`
  or response, action, and observation remain one record.
- OpenHands native event streams use the referenced chronological agent event;
  an observation joins only through its `cause` event id.
- OpenHands maximal tool histories use the referenced message and tool-call
  index; results join only through the exact tool-call id, while the latest
  source-native task-tracker state is carried forward in message order.
- Terminus2 official command records align in order to the same normalized
  command in the response stream; every command inherits only that response
  episode's `analysis` and `plan`. Multiple commands from one response may
  share an episode intent, but no episode may be selected by operation count or
  human stage. A result is absent unless the archive uniquely attributes it to
  that command; a later episode's batch terminal context is not relabeled as a
  per-command result.

Any missing reference, action mismatch, duplicate join, or incomplete mapping
invalidates that run rather than falling back to positional zipping.

## Comparison

- **Proposed system or method:** for each of the 20,461 adjacent operation
  pairs, present the concrete task plus the two completed source-native
  operation records. The records contain only available intent/progress,
  source action, and result evidence. A fixed binary grammar returns
  `continue` or `boundary`; the first operation starts a segment and predicted
  boundaries form the candidate partition. No active-label inventory, numeric
  plan index, stack-depth limit, recurrence score, target label, or resource
  weight is visible.
- **Main baseline:** the current multi-resolution recurrence constructor,
  ordinary B-cubed F1 `0.662740`. It represents the strongest complete
  target-blind action-field answer on this exact population and therefore needs
  a matched numerical comparison.
- **Controls, not main baselines:** the already-complete coarse recurrence
  (`0.649173` B-cubed F1), phase-only (`0.654445`), raw-action (`0.541070`),
  per-session, and per-operation partitions remain interpretation controls and
  are reused without rerunning.
- **Conclusion if the main baseline matches or wins:** the tested source-native
  boundary operator is not adopted, regardless of whether its labels appear
  plausible in selected examples.
- **Information, tuning, and compute fairness:** the candidate receives more
  semantically relevant *source-native* information by design but no target
  stage, target-derived plan, resource measure, alternative-label inventory,
  or future human annotation. The fixed model, seed, temperature, grammar, and
  source projection are constant across every pair. Existing baseline outputs
  are reused exactly.
- **Split or leakage rule:** source adaptation and inference complete for all
  sessions before the verified manifest is opened. The scorer alone reads the
  human stages. No prompt, projection, failure repair, or model call may depend
  on a stage boundary or metric.

## Workloads And Metrics

- **Real workloads or tasks:** all 405 source-valid CodeTraceBench failed
  trajectories from OpenHands, mini-SWE-agent, SWE-agent, and Terminus2; 251
  benchmark tasks, 20,866 operations, and 20,461 adjacent decisions.
- **Primary metric:** ordinary unweighted operation-level B-cubed precision,
  recall, and F1 against the human stage partition, as defined by Bagga and
  Baldwin and analyzed by Amigó et al.
- **Secondary metrics:** pooled unlabeled exact-span precision/recall/F1 and
  exact adjacent-boundary precision/recall/F1. These diagnose over-merge and
  over-split behavior but cannot override the primary decision.
- **Correctness check or ground truth:** the official verified CodeTraceBench
  stage intervals; every operation must appear exactly once in one predicted
  contiguous segment.
- **Repetitions, seeds, and uncertainty:** deterministic model inference at
  temperature zero and seed 20260720; 10,000 paired task-cluster bootstrap
  resamples for candidate minus current multi-resolution recurrence.
- **Cost estimate:** approximately 20,461 fixed local-model calls and 20--35
  minutes on the existing RTX 5090 llama.cpp server, plus source adaptation and
  scoring.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | real path | one complete trajectory from each of five source-adapter layouts | source-native adjacent boundary classifier | 1 deterministic run | establish source coverage, exact evidence alignment, and executable inference only |
| main | proposed | all 405 trajectories / 20,866 operations | source-native adjacent boundary classifier | 1 deterministic run | candidate partition and task-cluster uncertainty |
| reused | main baseline | identical complete population | current multi-resolution recurrence | existing complete result | adoption comparison |
| reused | controls | identical complete population | coarse, phase, raw, session, singleton | existing complete results | diagnose scale and error direction |

## Execution

- **Authoritative workflow:** a new thin evaluator under `script/` will reuse
  CodeTraceBench archive readers and the existing standard scorer. It will have
  separate `infer` and `score` commands so inference cannot open the verified
  manifest.
- **Real preflight case:** the smallest complete trajectory from each
  of the five layouts—MiniSWE messages, SWE-agent trajectory elements,
  Terminus2 responses/commands, OpenHands native events, and OpenHands maximal
  tool history—using the exact source-reference alignment,
  intent/progress/result extraction, Qwen3B request, grammar, prediction
  persistence, and subsequent scorer path.
- **Full completion rule:** all 405 trajectories, 20,866 operations, and 20,461
  adjacent decisions reach terminal status; every operation belongs to one
  contiguous predicted segment; source-evidence coverage is reported by
  framework and adapter layout; all source references, source actions, event
  causes, tool-call ids, and command-to-episode joins satisfy the fixed rules;
  the scorer completes all standard metrics and 10,000 paired task resamples.
- **Raw-result path:** `.agentsight/experiments/rq3-source-native-task-progress-boundary-v1/`.
- **Checkpoint or recovery approach:** one atomic per-session prediction cache;
  reruns reuse only byte-identical source evidence and model configuration.

## Interpretation

- **Positive result:** candidate B-cubed F1 is higher than current recurrence
  and the paired 95% interval is wholly above zero, with valid coverage and no
  framework whose source adapter silently replaces missing intent with target
  or system-field labels. Adopt the boundary operator for the task-semantic
  stage layer; separately label and render a source-linked example without
  treating label wording as a scored result.
- **Negative or contradictory result:** candidate-minus-current interval is
  wholly at or below zero. Record the source/model boundary and do not render a
  positive task-semantic flamegraph from these predictions.
- **Mixed or inconclusive result:** point estimate improves but the interval
  crosses zero, or gains are confined to frameworks with explicit progress
  state while pooled performance does not improve. Do not adopt; report the
  framework evidence-availability boundary.
- **Target paper figure or table:** if and only if supported, one task-rooted
  flamegraph whose main path is concrete task, predicted subtask/stage,
  semantic action, operation object, and result; agent/model/session/tool/status
  appear only as metadata, filters, color, width, or source detail. The scored
  table reports standard B-cubed and boundary/span metrics.

## Reproducibility Notes

- **Software and data versions:** llama.cpp build 9870, revision `2d973636e`;
  Qwen2.5-3B-Instruct Q4_K_M SHA-256
  `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`;
  existing CodeTraceBench archive hashes and target-operation sequence.
- **Config and seed notes:** temperature zero, seed 20260720, four workers,
  fixed binary output grammar, no target-time prompt or threshold tuning.
- **Known deviations:** public archives expose different native intent/progress
  fields across frameworks. Coverage and missingness are part of the result,
  not repaired with project-invented pseudo-intent. This experiment validates
  one flat task-stage boundary component, not literal subtask-name accuracy,
  arbitrary nested depth, diagnosis quality, or the whole task-semantic stack.
