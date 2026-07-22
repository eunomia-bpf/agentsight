# RQ1 Queryable Workspace-Trajectory Preflight Plan

Created: 2026-07-20T02:13:17-07:00
Status: approved by independent Review Round 3 for the declared two-episode mechanics preflight only
Gate: BOOTSTRAP / EXPERIMENT_GATE
Owner RQ: RQ1 diagnostic utility

## Decision Question

Can an automatic supervisor diagnose long-horizon process pathologies more
reliably when exact persistent-workspace relations are directly queryable than
when it receives an equally budgeted, full-fidelity Raw trace-navigation
interface over the same evidence?

This is scientifically distinct from the terminally blocked static experiment.
No condition concatenates the full history into a prompt. The preflight tests
whether the source, broker, blinding, gold, scoring, and two-domain execution
path are valid; its two development episodes cannot support an effect claim.

## Hypothesis And Falsification

For work crossing at least two explicit goals and two independent top-level
sessions, Workspace Trajectory Retrieval will improve pathology diagnosis and
canonical evidence localization over AggAgent-style Raw Retrieval at the same
model, source membership, prompt, rendered-token/byte budget, and tool-call
budget.

- A later held-out accuracy/evidence gain supports incremental epistemic value.
- An accuracy tie with materially lower retrieval cost supports compression or
  interface efficiency only.
- A Raw win, or a gain explained by State Diff/Counts, rejects the proposed
  representation claim.
- This preflight can only admit or block a later effect pilot; it cannot support
  any of those outcomes.

## Research Algorithm

The method is the deterministic source-linked projection in `docs/design.md`:

1. `agent-session` parses every native Agent action and source-native call/result
   interval;
2. successful system file effects attach only under the executable ownership
   rule below;
3. artifact identities are versioned across observed create/read/write/rename/
   delete effects and exact quiescent boundary states;
4. the store emits only order, action/session/goal ownership, action/effect,
   artifact-version, path-hierarchy, and source-evidence relations; and
5. unresolved evidence remains `unknown`.

Construction is one pass over time-ordered actions/effects, expected
$O(|A|+|E|)$ time. It contains no pathology classifier, anomaly score, learned
ranker, visual force, recency decay, operation weight, hotspot threshold,
semantic label, recurrence threshold, or validation judgment.

### Executable system-effect ownership rule

For Claude and Codex, the authoritative tool interval is the RFC3339 timestamp
on the source-native tool-call record through the timestamp on its result record,
paired by the native call ID. `agent-session::ToolEvent::{ts_ms,end_ts_ms,
call_id}` exposes these fields; controller stdout-arrival sidecars are never
used. A direct native file tool may emit an observed effect only when its
structured path/operation and matching successful result are present.

For shell/tool subprocesses, capture retains `clone`/`fork`/`vfork`, `execve`,
`exit`, and file syscalls. A process subtree belongs to a tool call only when:

1. its root `execve` occurs inside exactly one completed native tool interval;
2. the executed argv and CWD exactly match the structured command/CWD carried
   by that native call after deterministic parsing;
3. every descendant is reachable through retained process-creation records;
4. the subtree does not overlap a second candidate native call; and
5. the syscall timestamp lies after that subtree's creation and before its exit
   and the native result.

File effects from the long-lived Agent/controller process itself are not
assigned to a shell call by temporal proximity. Multiple matching calls,
missing start/result/process records, detached children, clock inversion, or
concurrent ambiguity yield `unknown`.

At syscall time, absolute paths stand alone; `AT_FDCWD` uses the retained
process CWD; a numeric directory FD uses its decoded `strace -yy` target;
undecoded numeric FDs are `unknown`. Old/new `renameat*` and `linkat` operands
resolve independently. Only a paired terminal syscall result `>= 0` establishes
success; failed, unfinished, resumed-without-entry, or entry-only records do not
create an effect. `no_effect` is allowed only for a successfully completed
direct tool or a completely captured owned process subtree with no successful
workspace effect. All other cases remain `unknown`.

## One Source Store

Each episode has one immutable store with neutral IDs. It retains:

- complete source-native session JSONL for all participating Agent vendors;
- complete system trace records, including records outside the workspace;
- exact quiescent boundary archives and manifests;
- explicit goal and top-level/child-session ownership records;
- evaluator/test/experiment outcomes;
- task, skill, harness, and specification bytes visible to the worker; and
- hidden perturbation/intervention provenance in a physically separate gold
  store that is never available to either supervisor condition.

Raw records receive canonical IDs before either condition is materialized. The
store hash, ordered Raw-ID set, neutral scope IDs, and action-ID namespace must
be byte-identical across paired conditions. Runtime paths, source payloads, tool
responses, prompts, and envelopes are scanned for mechanism names, pair labels,
`perturbed`, `repaired`, and condition names before inference.

## Conditions

### Main baseline: Full Raw Retrieval

This condition follows AggAgent's full-fidelity navigation precedent. It gets:

- `list_scopes()` — neutral goal/session/source intervals and exact boundaries;
- `search(query, scope, source_types, k)` — source-record retrieval ranked by
  the frozen AggAgent ROUGE-L rule, with Raw-ID tie breaking;
- `read_record(raw_id)` — exact native/system/evaluator/specification record or
  exact snapshot byte range; and
- `read_range(scope, start_raw_id, end_raw_id)` — a contiguous ordered range
  without summarization.

No source row is removed because it appears irrelevant. The supervisor can
navigate the complete history without loading it all at once.

### Proposed: Workspace Trajectory Retrieval

This condition receives all Raw operations and additionally:

- `artifact_history(path)` — ordered observed/unknown effects, versions,
  renames, deletion, and supporting Raw IDs;
- `goal_diff(from_goal, to_goal)` — exact continued/added/removed artifact and
  action relations between two explicit scopes; and
- `effects(action_id)` — observed effects plus explicit unknown candidates.

These three tools perform no ranking, classification, summarization, generic
chronology shortcut, or semantic inference. All returned facts are
reconstructible from the Raw store.

### Reduced controls

State Diff and Counts are constructed for later mechanism diagnosis but do not
gate this two-condition preflight and are not equal-status baselines. A later
effect pilot must include them. AgentTether is the closest structured diagnostic
competitor on predeclared compatible failed-run cases; OCPM is the established
lifecycle/process alternative; Full HTIR remains specific to compatible
harness-failure cases. They are not required to prove this broker's mechanics.

## Fairness And Budget Contract

Both conditions use Qwen3.6-27B Q4_K_M at Hugging Face snapshot
`b19fa7e8538a1a5f66452eb3b3167e026177be1d`, blob SHA-256
`f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`,
through llama.cpp revision `2d973636e292ee6f75fadcf08d29cb33511f509f`.
The server uses a 65,536-token context, Qwen's pinned Jinja chat template,
function calling, `enable_thinking=false`, temperature `0`, top-p `1`, seed
`20260720`, and at most 2,048 output tokens. Each condition starts a fresh
conversation and has a 30-minute wall timeout.

Every rendered request, including system/user/assistant messages, tool schemas,
queries, tool responses, and the output reservation, must fit the exact model
tokenizer. In addition, each condition receives at most 31,744 tool-response
tokens and 126,976 UTF-8 bytes: exactly half of the 63,488-token input ceiling,
with the byte cap fixed at four bytes per token. One response is capped at
4,096 tokens and 16,384 bytes. The lower remaining cap wins. Oversize results
return the largest prefix ending at a complete UTF-8 boundary plus a continuation
cursor; they never fail only because one Raw record is large.

AggAgent official commit `9638f7d88aee01eb636c02841e13a05bb2e3c449`
is adapted as follows: `rouge-score`'s `rougeL` recall with
`use_stemmer=false`; one Raw JSONL record is one searchable step; only its
lossless payload field is scored; scores sort descending then by Raw ID; `k`
defaults to 5 and is capped at 10; result snippets contain the first 150
whitespace-delimited words. `read_range` returns at most five contiguous Raw
records, matching `get_segment`; a record exceeding the response cap is exposed
through the same byte-offset continuation used by `read_record(raw_id,
offset_bytes)`. Snapshot binaries are searchable by exact path/manifest metadata
and readable as base64 byte pages; no generated description enters the index.

The 100-call maximum is retained only as AggAgent's rollout-level safety ceiling,
not claimed as a uniquely fair diagnosis budget. The binding parity constraints
are the exact rendered context and cumulative token/byte caps above. Invalid,
failed, and continuation calls consume one call and all returned envelope bytes.
Trajectory's additional tool schemas consume its own context budget. Search
queries and stopping are selected by the supervisor, never by a pathology-aware
selector.

## Development Workloads

The preflight uses exactly two excluded development episodes:

1. one real SWE-bench Verified coding workspace; and
2. one real OR-Space multi-artifact auto-research workspace.

Each episode crosses a prior goal, a neutral environment transition, and a
target goal in separate top-level Agent sessions. Each has one hidden controlled
perturbation with a counterfactual repaired sibling retained only for the
post-gold manipulation auditor.
The episode IDs and runtime directory names are sampled before the mechanism is
assigned and reveal neither domain condition nor treatment. These episodes are
permanently excluded from later estimates and threshold selection.

The retained B13 coding episode may be used only to test source parsing because
its runtime path leaks treatment identity. It cannot be shown to a supervisor.
Fresh neutral-ID episodes are required for end-to-end preflight.

## Independent Gold And Outputs

Before supervisor inference, two independent human experts inspect complete
ordinary Raw evidence, exact boundaries, explicit goals, evaluator results, and
worker-visible harness/specification bytes. They are blinded to perturbation
assignment, pair identity, repaired sibling, and hidden intervention provenance.
A third expert adjudicates while under the same blind. They produce and freeze
one target-goal record per episode:

- four independent boolean labels: stagnation, goal drift, validation gap, and
  harness waste;
- one or more alternate accepted minimal sets of canonical action IDs and
  affected artifact paths;
- a retrospective intervention in `continue`, `stop`, `redirect`, `clarify`, or
  `repair_harness`;
- the earliest target action supporting that intervention; and
- four pathology confidences and insufficient-evidence.

Only after that gold is immutable does a separate manipulation auditor see the
hidden assignment, repaired sibling, and intervention provenance. This auditor
records whether the manipulation occurred and whether the repaired outcome
changed as intended; it cannot edit labels, evidence sets, paths, earliest
actions, or interventions. Failed manipulation blocks the episode rather than
rewriting its gold.

The scorer must exist, print usage, validate schemas, and pass synthetic exact,
partial, alternate-set, rename, earliest-action, intervention, confidence, and
abstain tests before any supervisor call. It freezes these rules:

- pathology macro-F1 always includes all four labels; absent positives do not
  remove a label from descriptive output;
- evidence score is the maximum set-F1 against any accepted minimal action-ID
  set, so extra citations are penalized and equivalent minimal explanations are
  accepted;
- paths are canonicalized to frozen artifact lineage IDs, and score is the
  maximum set-F1 over accepted path/rename-alias sets;
- earliest support reports exact action accuracy and a separately named
  same-goal ±1-action tolerance, never the better of the two post hoc;
- intervention uses exact five-class accuracy and macro-F1;
- pathology confidence uses per-label Brier score; and
- `insufficient_evidence=true` is correct only when gold says evidence is
  insufficient. Otherwise it is an abstention with all four labels,
  intervention, evidence, path, and earliest-support items scored incorrect.

Supervisor outputs use the same schema. Condition identity is stored outside
model-visible files.

## Preflight Sequence

1. freeze neutral IDs, source-store schema, Raw-ID namespace, tool schemas,
   prompts, model revision, tokenizer/template, seed, and budget ledger;
2. capture the two fresh episodes and their repaired siblings with exact
   quiescent boundaries, then build the complete neutral source stores;
3. create and freeze blinded gold plus the fully tested scorer;
4. independently verify source/action closure for every frozen gold evidence
   action, task-relevant successful effect, evaluator action, and used
   cross-goal lineage;
5. reveal hidden provenance only to the separate manipulation auditor; block
   failed manipulations without changing gold;
6. reconstruct both interfaces and verify fact/source parity;
7. run one Raw and one Trajectory supervisor per domain in randomized order;
8. independently review raw broker transcripts, budget ledgers, outputs,
   scores, leakage scan, and provenance; and
9. stop. Do not launch a larger matrix without a new result review and power
   plan.

## Vetoes

The preflight fails before inference if any of the following occurs:

- a gold evidence action, task-relevant successful effect, evaluator action, or
  used cross-goal lineage lacks exact ownership and Raw bytes;
- an unresolved event is silently converted to `no_effect`;
- the two conditions differ in source-store hash, Raw-ID set, initial prompt,
  output schema, model, seed, or enforceable budget;
- any model-visible byte reveals condition, treatment, mechanism, pair, or
  runtime-name cues;
- any Trajectory response lacks retrievable supporting Raw IDs;
- any Raw fact needed to reconstruct a returned Trajectory relation is
  inaccessible through Raw tools;
- the broker's accounting differs from the fully rendered model transcript;
- the scorer/gold is absent or changed after inference; or
- coding or auto-research cannot complete the identical end-to-end path.

The preflight fails after inference if output parsing, tool execution, or score
reproduction fails. Diagnostic accuracy is reported descriptively but cannot
admit the later study because $n=2$.

## Preflight Deliverables

- immutable source-store manifests and hashes;
- exact command/version/environment provenance;
- neutral prompts and tool schemas;
- Raw and Trajectory broker transcripts plus complete budget ledgers;
- independent gold and tested scorer outputs;
- leakage and source-parity reports;
- one result report and one fresh independent result review.

No animation, HTML, PNG, GIF, layout metric, or human usability result is part
of this gate.

## Decision After Preflight

- **PASS mechanics:** both domains satisfy every veto and all outputs/scores
  reproduce. Admit only a separately planned development effect pilot with
  grouped sampling and power analysis.
- **BLOCK source/interface:** repair only within the reviewed limit or close the
  candidate after the review threshold; do not reinterpret partial output.
- **No scientific conclusion:** regardless of descriptive model answers, this
  two-episode preflight cannot support RQ1.

## Frozen Reproducibility Commands

The implementation must preserve these interfaces or return to plan review:

```bash
cargo run --release --manifest-path agentvis/Cargo.toml -- research-store \
  --source <neutral-capture-dir> --output <episode-store-dir> --verify

/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  --model /home/yunwei37/.cache/huggingface/hub/models--DevQuasar--Qwen.Qwen3.6-27B-GGUF/snapshots/b19fa7e8538a1a5f66452eb3b3167e026177be1d/Qwen.Qwen3.6-27B.f16.gguf.Q4_K_M.gguf \
  --ctx-size 65536 --n-gpu-layers 99 --host 127.0.0.1 --port 8013 --jinja

cargo run --release --manifest-path agentvis/Cargo.toml -- research-supervisor \
  --store <episode-store-dir> --condition <raw|trajectory> \
  --base-url http://127.0.0.1:8013/v1 \
  --model /home/yunwei37/.cache/huggingface/hub/models--DevQuasar--Qwen.Qwen3.6-27B-GGUF/snapshots/b19fa7e8538a1a5f66452eb3b3167e026177be1d/Qwen.Qwen3.6-27B.f16.gguf.Q4_K_M.gguf \
  --seed 20260720 --context-tokens 65536 --reserve-output-tokens 2048 \
  --evidence-tokens 31744 --evidence-bytes 126976 \
  --response-tokens 4096 --response-bytes 16384 \
  --max-tool-calls 100 --timeout-seconds 1800 --output <broker-run-dir>

cargo run --release --manifest-path agentvis/Cargo.toml -- research-score \
  --gold <frozen-blinded-gold.jsonl> \
  --predictions <broker-run-dirs> --output <score-dir>
```

The broker sends `temperature=0`, `top_p=1`, `seed=20260720`,
`max_tokens=2048`, `chat_template_kwargs.enable_thinking=false`, strict tool
schemas, and the frozen output schema on every relevant OpenAI-compatible
request. Its Rust ROUGE-L port must match `rouge-score==0.1.2` with
`use_stemmer=false` on retained conformance fixtures before a real run.

`research-store --help`, `research-supervisor --help`, `research-score --help`,
all focused fixtures, the full `agent-session` tests, and the full `agentvis`
tests must pass before fresh capture. Hashes and ledgers remain ordinary
correctness outputs of these commands, not a separate research framework.
