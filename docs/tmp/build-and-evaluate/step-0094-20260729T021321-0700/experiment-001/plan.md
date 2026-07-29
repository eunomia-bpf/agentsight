# Step 0094 Experiment 001: ToolSandbox Official-Milestone Identity

## Decision context

- **Fixed paper RQ:** RQ3 — “How Accurate Are the Tags?”
- **Paper thesis preserved:** “Agent observability needs profiling, not only debugging.”
- **Uncertainty:** Do current AgentProf canonical, root-stripped semantic leaf IDs
  identify the same independently defined ToolSandbox milestone across fresh
  runs better than the strongest source-native action signature?
- **Role:** external, programmatic cross-run identity test. This is not another
  CodeTrace retrieval analysis and does not reuse Step 0060's retired
  completion-boundary predictions.

The immediate no-inference alternatives are closed:

- ASE's 2,737 eight-class labels were already exhausted by Step 0032 and do not
  define nested or object-sensitive operation identity.
- retained WorkArena++ trajectories contain final reward but no offline
  per-subtask completion mapping, while official validation requires unavailable
  BrowserGym/ServiceNow state;
- Step 0060 ToolSandbox predictions contain completion-boundary indices only,
  not current hierarchy names or IDs.

Fresh current-backend inference is therefore necessary, but it is forbidden
until an offline official-oracle replay passes.

## Hypothesis and paper-value gate

**Hypothesis.** Across repeated executions of the same official ToolSandbox
scenario, current canonical root-stripped semantic leaf IDs align with achieved
official milestone-node identities better than the source-native
`tool name + argument-key signature + action kind` baseline.

Paper admission requires the **complete 3,551-trajectory population** and all of:

1. exact offline replay succeeds without a heuristic subgoal parser on every
   predeclared eligible milestone occurrence;
2. candidate ordinary B-cubed F1 exceeds the strongest source-native baseline;
3. the 95% complete-scenario bootstrap interval for the paired F1 difference is
   wholly positive;
4. candidate B-cubed precision and recall are both non-degenerate and neither
   root-only nor prompt-only identity matches the candidate;
5. exact-visible-string exclusion, model/persona-condition, and trial-index
   sensitivities preserve the direction;
6. a new independent reviewer reconstructs the oracle population, primary
   scores, and bootstrap without invoking the authoritative scorer.

The balanced 444-trajectory screen described below can only authorize the full
run. It cannot enter the paper. If its candidate-minus-baseline interval is not
wholly positive, stop with a valid negative result and do not spend on the full
population.

## Frozen sources

- visible inference source:
  `.agentsight/experiments/rq3-result-grounded-task-stack-v1/source/visible-trajectories.jsonl`
- raw-file manifest:
  `.agentsight/experiments/rq3-result-grounded-task-stack-v1/source/source-audit.json`
- raw AgentReward files:
  `.agentsight/external/agent-quality-inspect-complete/toolsandbox/<model>/<persona>/trial_<n>_results.json`
- official ToolSandbox source:
  `.agentsight/external/ToolSandbox` at
  `165848b9a78cead7ca7fe7c89c688b58e6501219`
- official oracle code:
  `tool_sandbox/common/evaluation.py`,
  `tool_sandbox/common/scenario.py`, and `tool_sandbox/scenarios/*.py`
- current annotation protocol:
  `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/direct_annotation/annotate.py`
- current source-only canonicalizer:
  `script/canonicalize_operation_marks.py`

The source inventory is 3,551 trajectories, 37 scenarios, 12 model/persona
conditions, 9,485 user turns, 20,571 visible actions, and 11,082 tool actions.
All 37 scenario IDs resolve in the official source. One pass over the 37
official templates defines 99 milestone nodes; 34 scenarios have multiple
milestones.

Every input and selected population file receives a SHA-256 digest. The official
checkout must remain clean and read-only.

## Information separation

Inference may read only:

- an opaque sequence ID that does not contain scenario, condition, trial, model,
  persona, outcome, or gold information;
- the concrete user task;
- ordered visible user utterances, assistant requests/responses, tool names,
  argument values, tool results, and visible state updates.

Inference must not read:

- `scenario_id` or source path;
- official scenario/milestone objects, node indices, edges, constraints, or
  reference snapshots;
- `metrics.progress_rates`, `metrics.subgoal_validations`, success/reward, or
  any AgentReward judge explanation;
- Step 0060 gold or prediction fields;
- replay results or scorer rows.

The adapter writes inference packets and oracle rows in separate directories.
The model-facing process receives only the packet directory. The scorer opens
gold only after every selected response is frozen and hashed.

Gold labels are opaque `(scenario_id, official_milestone_node_index)` pairs, not
literal taxonomy strings. Before inference, nevertheless enumerate exact
official constraint-function, database-namespace, column, tool, and action
strings and their occurrences in every model-visible field. Record a sensitivity
that excludes milestone occurrences with an exact scorer-signature string in
the active visible action.

## Official offline replay

Implement one adapter, `toolsandbox_milestone_identity.py`, without changing the
official ToolSandbox checkout.

For each raw trajectory:

1. reconstruct the initial databases from the first recorded state;
2. replay ordered user, assistant, tool-call, tool-result, and database-update
   records into a ToolSandbox `ExecutionContext` with exact source order and
   snapshot indices;
3. instantiate the official scenario and invoke its unchanged
   `MilestoneMatcher`;
4. verify the official DAG and mapping;
5. retain only achieved milestone nodes whose score is mechanically exact and
   whose matching snapshot maps to recorded source actions;
6. exclude response-only nodes that require ROUGE or another textual similarity
   oracle;
7. map every retained milestone occurrence to exactly one visible atomic action.

Multiple milestone nodes may match one action; each remains a distinct gold
occurrence and receives the same active predicted leaf. Unmatched actions are
retained for boundary/coverage accounting but are not invented as labeled
milestones.

Replay is invalid if it needs description parsing, task-prompt parsing, manual
labels, fuzzy tool-name rules, hand-written per-scenario cases, or a changed
official constraint. Invalid replay stops the experiment before inference.

## Candidate and baselines

### Candidate

Use the Step 0087 direct multi-level protocol unchanged:

- one isolated complete-trajectory call;
- `gpt-5.6-sol`;
- sparse variable-depth action-first marks;
- the same allowed verbs and response contract;
- the current source-only action/object canonicalizer.

The scored candidate is the active canonical **root-stripped leaf ID** at the
source action mapped to each official milestone occurrence. The root is never a
candidate identity.

### Main baseline

The main source-native identity is:

`normalized tool name + sorted normalized argument-key set + action kind`

It uses only fields visible to the candidate at that atomic action. Missing
tools use the explicit response/action kind, never generated text content.

### Controls and ablations

- tool name only;
- action kind only;
- operation leaf before canonicalization;
- canonical root only;
- opaque prompt hash/root-only task identity;
- canonical complete root-stripped path;
- generic-frame-removed root-stripped leaf/path.

Step 0060 completion boundaries are a historical diagnostic only, not an
identity baseline.

## Population sequence and stopping

### Phase A: real oracle preflight

Use exactly:

`gpt_4_1/expert/trial-0/find_current_city_low_battery_mode`

The official scenario must expose six milestone nodes and edges
`[(0,1),(0,2),(1,4),(2,3),(3,4),(4,5)]`. The preflight must:

- rebuild the real `ExecutionContext`;
- map only mechanically exact achieved nodes to source actions;
- reconcile source/tool/action counts;
- create one opaque current-backend packet;
- complete one real annotation call;
- canonicalize source-only;
- resolve every retained milestone occurrence to exactly one active
  root-stripped leaf.

If any check fails, stop and report the concrete replay limitation.

### Phase B: balanced screen

For every one of 37 scenarios and each of 12 model/persona conditions, choose
the lowest trial index containing that scenario. This yields exactly 444
trajectories, independent of outcomes and annotations. Freeze the selected
sequence list before model calls.

Run all 444 through the current backend. Score the complete screen and bootstrap
whole scenario IDs 10,000 times with seed `20260729`. Stop as a valid negative
unless the candidate-minus-main-baseline B-cubed F1 interval is wholly positive
and the root/prompt controls do not match the candidate.

### Phase C: complete population

Only a passed balanced screen authorizes the remaining trajectories. Reuse the
444 valid responses and annotate every other source trajectory, for 3,551 total.
Paper admission uses only the full population and its independent review.

## Metrics

Primary:

- ordinary B-cubed precision, recall, and F1 over all retained official
  milestone occurrences, with gold clusters
  `(scenario_id, milestone_node_index)`;
- candidate-minus-main-baseline B-cubed F1;
- 10,000 paired percentile-bootstrap replicates over complete scenario IDs.

Secondary:

- homogeneity, completeness, and V-measure;
- cross-session same-ID pair precision, recall, and F1, excluding within-run
  pairs;
- exact milestone-boundary precision, recall, and F1 over atomic actions;
- eligible milestone/action coverage;
- per-scenario, condition, model/persona, and trial-index results;
- all registered controls and sensitivities.

No pairwise or operation bootstrap is permitted. The 37-scenario conditional
interval does not imply a general population of arbitrary agent tasks.

## Cost and validity controls

The Step 0087 complete run used 415 calls, 12.05M input tokens, 231,886 output
tokens, and 2,215.9 seconds active backend wall for 405 trajectories. Phase B is
similar in call count. Phase C is expected to be about 8.8 times that run.

One ordinary format retry per trajectory is permitted. A third attempt requires
a concrete plan amendment before it runs. Concurrency is at most four. Partial
valid outputs are resumable by source hash; failed or interrupted output
directories are not cleaned destructively.

## Artifacts and review

Research artifacts remain under this experiment directory:

- plan and independent plan review;
- input/source manifest and selected-screen manifest;
- replay audit, oracle rows, and model-visible packets;
- raw annotations and run records;
- source-only canonical marks/predictions;
- score rows, bootstrap summaries, result report, and cost record;
- independent implementation/result review.

No product output other than the standard pprof artifact is introduced. This
experiment does not edit the paper, `docs/user-instruction.md`,
`docs/idea-story.md`, or the read-only paper submodule.

The plan must receive independent `APPROVE` before adapter implementation.
After Phase A, an independent reviewer must audit replay faithfulness before
Phase B inference. After any full score, another reviewer independently
recomputes the oracle population, primary scores, and bootstrap. Only an
accepted full result may be summarized as positive evidence; all negative or
invalid outcomes remain experiment records and are summarized only in
`docs/evaluation.md`.

