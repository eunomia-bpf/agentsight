# Step 0094 Experiment 001: ToolSandbox Official-Milestone Identity

## Decision context

- **Fixed paper RQ:** RQ3 — “How Accurate Are the Tags?”
- **Paper thesis preserved:** “Agent observability needs profiling, not only debugging.”
- **Uncertainty:** Within repeated executions of one official ToolSandbox
  scenario, do current AgentProf canonical, root-stripped semantic leaf IDs
  identify the same exact one-to-one action-linked achieved milestone across
  fresh runs better than a predeclared value/result-aware source-native action
  signature?
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

**Hypothesis.** Within repeated executions of each official ToolSandbox
scenario, current canonical root-stripped semantic leaf IDs align with exact
one-to-one action-linked achieved official milestone-node identities better
than the source-native value/result-aware signature defined below.

The balanced screen is a futility gate, not confirmatory evidence. Paper
admission requires the **untouched 3,107-trajectory confirmatory remainder** and
all of:

1. exact offline replay succeeds without a heuristic subgoal parser on every
   predeclared eligible exact action-linked milestone occurrence;
2. candidate scenario-macro ordinary B-cubed F1 exceeds the frozen
   value/result-aware source-native baseline and the conservative envelope of
   every registered source-native baseline;
3. the 95% complete-scenario bootstrap intervals for both paired differences
   are wholly positive on the untouched remainder;
4. candidate B-cubed precision and recall are both non-degenerate and neither
   root-only nor prompt-only identity matches the candidate;
5. model/persona-condition and trial-index sensitivities preserve the direction,
   and any registered pre-inference cue-masked sensitivity does not reverse it;
6. a new independent reviewer reconstructs the oracle population, primary
   scores, and bootstrap without invoking the authoritative scorer.

The all-3,551 score is descriptive/secondary because the screen was observed
before the remainder was authorized. If the screen interval is not wholly
positive, stop with a valid negative result. If the untouched remainder fails
either confirmatory interval, the result is not admitted to the paper.

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

The stages run as separate processes with auditable argv, working directory, and
opened-file manifests:

1. the packet/oracle builder may open raw trajectories and official scenarios;
2. the annotator may open only opaque packets and the response schema;
3. the canonicalizer may open only source operations and frozen marks;
4. the scorer may open only frozen predictions and gold rows.

The builder writes packets and oracle rows in separate directories. No
`scenario_id`, source path, condition, trial, model, persona, outcome, official
object, or gold-derived value may appear in an annotator-visible ID, filename,
working directory, prompt, environment variable, or run-record field. The
scorer opens gold only after every selected response is frozen and hashed.

Here “model” means the source trajectory's model/condition. The annotator
necessarily receives and records the fixed annotation backend
`gpt-5.6-sol`; that backend identifier is not source metadata.

Gold labels are opaque `(scenario_id, official_milestone_node_index)` pairs.
Before inference, enumerate these exact literal strings in every model-visible
field; their occurrence count must be zero. Separately inventory official
constraint functions, namespaces, columns, tool names, argument keys/values,
and target strings as **gold-definition features**, not target-label strings.
Post-hoc removal of rows whose action contains such a feature is not a leakage
test. Any optional feature sensitivity must instead build and hash a second
packet population before inference, mask the same cue from both candidate and
baselines, and pay for independent annotations of that population.

## Official offline replay

Implement one adapter, `toolsandbox_milestone_identity.py`, without changing the
official ToolSandbox checkout.

For each raw trajectory:

1. flatten the raw messages in exact source order;
2. pair every call and result by exact call ID, never list position; abort an
   ambiguous or duplicate pairing, including a reordered parallel-call case
   that cannot be resolved exactly;
3. reconstruct initial databases from the first recorded full state;
4. replay user, assistant, call, result, and database-update records into a
   ToolSandbox `ExecutionContext` with exact snapshot indices;
5. reconstruct a successful `tool_trace` only when the raw result is reversibly
   typed by the official representation (JSON or exact Python-literal
   round-trip) and the reserialized value equals the source; otherwise classify
   it as non-reversible and exclude trace-dependent action linkage;
6. require exact equality for every primitive actually present in raw: flattened
   role/content order, call ID/name/arguments, result, and database update;
7. round-trip project the reconstructed `ExecutionContext` back to that frozen
   raw primitive sequence and require exact equality; hash reconstructed native
   SANDBOX rows and namespace snapshots as explicitly derived artifacts, never
   claim that those native hashes independently existed in raw;
8. instantiate the official scenario and invoke its unchanged
   `MilestoneMatcher`; verify the official DAG and optimized mapping.

The unchanged matcher remains the **achievement oracle**, but its optimized
snapshot is not silently reinterpreted as a causal first-achievement mapping.
A separate frozen action-link eligibility predicate is applied to that selected
snapshot:

- every constraint composition for the node is on the predeclared exact
  allowlist below, and matcher-selected node similarity is exactly 1;
- for a constrained state namespace, similarity at the immediately preceding
  source snapshot is 0, the selected index contains a delta in that namespace,
  and exactly one call-ID-linked raw tool-result action records the complete
  database update producing that delta;
- for an accepted tool-trace constraint, the selected snapshot contains exactly
  one exact call-ID-linked tool action and a reversible typed trace;
- the selected physical action carries exactly one eligible official milestone
  node.

For a constraint that references a predecessor or another milestone, compute
both selected- and prior-snapshot similarity using the unchanged matcher's
already frozen selected mapping for every referenced node. Never recompute or
remap a reference to make the `0→1` test pass.

Eligibility is explicitly two-stage. First classify each node provisionally
from its frozen composition, exact score transition, and unique action link.
Then group provisional nodes by physical action and retain an occurrence only
when that action has exactly one provisional node. This second stage removes
zero-node and multi-node actions without circularly defining node eligibility.

Exclude initial-state matches, persistent-state matches without a delta at the
matcher-selected snapshot, response/user-selected snapshots, ambiguous
parallel calls, non-reversible results, zero-node actions, and actions carrying
multiple nodes. Do not remap a non-causal official snapshot to an earlier
action. The retained items are named **exact one-to-one action-linked official
milestone occurrences**. Unmatched actions and excluded milestones contribute
only to eligibility/coverage accounting.

Before any annotation, enumerate every official node's complete composition:
snapshot constraint function, namespace, target columns, effective default or
overridden column comparators, reference node, and guardrail. The allowlist is:

- direct binary state comparisons whose every constrained column uses
  `column_exact_match_similarity`;
- direct tool-trace comparisons using
  `column_tool_trace_exact_match_similarity`;
- `addition_similarity`, `removal_similarity`, or `update_similarity` only when
  all constrained target columns use exact comparators and every reference
  snapshot is already exactly action-linked;
- `tool_trace_dependant_similarity` only when both the reference trace and
  derived target trace are reversible and the final comparison is exact;
- binary `guardrail_similarity` only as a consistency condition, never as a
  standalone occurrence.

Exclude a node if any effective constraint uses ROUGE, substring/contains,
continuous/tolerance, semantic/textual, or otherwise non-binary comparison,
including SANDBOX `content`, MESSAGING/REMINDER `content`, and CONTACT
`relationship` under their default comparators. `similarity == 1` does not
override this exclusion. Freeze and hash the node inventory and report node and
occurrence counts for every exclusion reason before annotations exist.

Replay is invalid if it needs description parsing, task-prompt parsing, manual
labels, fuzzy tool-name rules, hand-written per-scenario cases, a changed
official constraint, or AgentReward `progress_rates`/`subgoal_validations`.
Invalid replay stops the experiment before inference.

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

The source packet preserves the current Step 0087 granularity: marks may start
only at a packet user turn's `first_operation_id`. ToolSandbox user turns often
contain several atomic actions, so all actions in such a turn receive the same
active path. The builder must not atomize those actions into synthetic turns.
This known construct mismatch is retained in primary identity scoring and
reported as a limitation; the experiment makes no atomic boundary-accuracy
claim.

### Main baseline

The frozen value/result-aware source-native identity is:

`normalized tool name + canonical complete argument JSON + success/error class
+ changed database namespace/column set + action kind`

Canonical JSON preserves typed argument values, recursively sorts object keys,
preserves list order, and uses no gold, scenario, outcome, or model output.
Success is assigned only by an exact reversible result round-trip; otherwise the
source exception class or explicit non-reversible class is used. Database-delta
features contain namespace and changed-column names, not gold target values.
Missing tools use the explicit response/action kind and empty argument/result/
delta sentinels, never generated response text. The normalization source and
hash are frozen before outputs.

For a conservative paper gate, each bootstrap replicate also forms a
**source-native envelope** equal to the maximum scenario-macro F1 among all
registered source-native baselines below. Candidate-minus-envelope must have a
wholly positive confirmatory interval; no post-hoc baseline choice is allowed.

### Controls and ablations

- tool name only;
- action kind only;
- tool name + sorted argument-key set + action kind;
- tool name + canonical complete arguments + action kind;
- success/error class + changed namespace/column set;
- ordered source-native signatures for the containing user turn;
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
- reconcile every flattened message, call-ID pairing, typed result, database
  update, SANDBOX row, and namespace snapshot;
- run the unchanged official matcher, then apply the separate frozen
  one-to-one action-link eligibility predicate without remapping snapshots;
- inventory the full comparator composition for all six nodes and exclude the
  textual/fuzzy node(s) before annotation;
- map only exact one-to-one action-linked achieved nodes to source actions;
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
trajectories, independent of outcomes and annotations. Before any call, freeze
and hash both the 444 screen manifest and its disjoint 3,107-trajectory
remainder manifest.

Run all 444 through the current backend. Score the complete screen and bootstrap
whole eligible scenario IDs 10,000 times with seed `20260729`. Stop as a valid
negative unless both candidate-minus-main-baseline and
candidate-minus-source-native-envelope scenario-macro B-cubed F1 intervals are
wholly positive and the root/prompt controls do not match the candidate.

### Phase C: untouched confirmatory remainder

Only a passed screen authorizes annotation of the already frozen disjoint 3,107
remainder. Paper admission uses only this untouched remainder and its
independent review. It must pass the same two wholly positive scenario-bootstrap
intervals and all registered controls. After this decision, combine the frozen
screen and remainder only for a descriptive all-3,551 estimate; the combined
score cannot rescue a failed confirmation.

## Metrics

Primary:

- within each eligible scenario, ordinary B-cubed precision, recall, and F1 over
  exact one-to-one action-linked occurrences, using official node index as the
  task-relative gold cluster;
- unweighted macro means of the per-scenario B-cubed precision, recall, and F1;
- candidate-minus-frozen-main-baseline and candidate-minus-source-native-
  envelope scenario-macro B-cubed F1;
- 10,000 paired percentile-bootstrap replicates over complete eligible scenario
  IDs, seed `20260729`.

Primary inclusion requires a gold node cluster to occur in at least two
distinct trajectories and at least two model/persona conditions, and an
eligible scenario to contain at least two such node identities. Freeze this
oracle-only inclusion before predictions. The estimand is identity conditional
on exact one-to-one action-linked achievement; it is not milestone achievement
or detection recall.

Secondary:

- homogeneity, completeness, and V-measure;
- within-scenario cross-session same-ID pair precision, recall, and F1, where
  different nodes in the same scenario are negatives and cross-scenario pairs
  are never treated as known non-equivalences;
- population-global B-cubed over `(scenario_id, node_index)` as a clearly
  misalignment-prone diagnostic only;
- coarse turn-boundary diagnostics, explicitly not atomic boundary accuracy;
- eligible milestone/action coverage;
- per-scenario, condition, model/persona, and trial-index results;
- all registered controls and sensitivities.

No pairwise, occurrence, operation, or within-scenario trajectory bootstrap is
permitted. A duplicated scenario in a bootstrap draw contributes a duplicated
precomputed scenario statistic; gold clusters are never merged across draws.
The 37-scenario conditional interval does not imply a general population of
arbitrary agent tasks or cross-scenario semantic equivalence.

## Cost and validity controls

The Step 0087 complete run used 415 calls, 12.05M input tokens, 231,886 output
tokens, and 2,215.9 seconds active backend wall for 405 trajectories. Phase B is
similar in call count. The untouched Phase C remainder is expected to be about
7.7 times that run; screen plus remainder is about 8.8 times that run. Phase C
is not authorized unless Phase B passes.

One ordinary format retry per trajectory is permitted. A third attempt requires
a concrete plan amendment before it runs. Concurrency is at most four. Partial
valid outputs are resumable by source hash; failed or interrupted output
directories are not cleaned destructively.

## Artifacts and review

Research artifacts remain under this experiment directory:

- plan and independent plan review;
- input/source, selected-screen, and untouched-remainder manifests;
- per-process argv, working-directory, environment-key, and opened-file access
  manifests;
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
Phase B inference. After the screen score, a reviewer must verify that the
stopping decision and disjoint remainder were frozen without leakage. After any
confirmatory score, another reviewer independently recomputes the oracle
population, primary scores, baseline envelope, and bootstrap. Only an accepted
untouched-remainder result may be summarized as positive evidence; all negative
or invalid outcomes remain experiment records and are summarized only in
`docs/evaluation.md`.

The maximum admissible positive claim is: within repeated official ToolSandbox
scenarios, and conditional on exact one-to-one action-linked milestone
achievement, root-stripped AgentProf leaf IDs align with recurring task-relative
milestone nodes better than the predeclared source-native signatures. The
experiment does not establish global semantic equivalence, arbitrary-task
generalization, causal first achievement, milestone detection recall, or atomic
boundary accuracy.
