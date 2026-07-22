# Evidence And Matched-Access Contract

Status: proposed, frozen for independent plan review.

## Typed Raw Store

One immutable run manifest binds five raw families:

1. `native:<session>#<call>` — complete Agent/model/tool request-response records;
2. `system:<id>` — source-backed process/file/state effects and monotonic time;
3. `snapshot:<boundary>:<path-or-object>` — quiescent manifests and allowed raw
   file bytes/chunks;
4. `evaluator:<id>` — tests, metrics, outcomes, and evaluator records; and
5. `spec:<id>` — task/goal/skill/prompt/tool-schema/harness/orchestrator artifacts.

Every record carries type, canonical ID, content hash, origin, time/boundary, and
scope. Every structured item cites a nonempty sorted set of these IDs. A parity
audit fetches each ID through matching Raw and byte-compares it with the bytes
used to construct the item. Unlinked or mismatched items fail.

## Full And Target Scopes

- **Full Raw/Trajectory:** all permitted raw families from $H_0$ through target
  end, including prior goals.
- **Target Raw/Trajectory:** target-window native/system/evaluator records,
  target start/end states, every specification version in force at target start
  or changed during the target, but no earlier spec versions, prior actions,
  effects, reports, or recurrence.

The two members of each pair share exact membership. Both pairs get budgets
computed from full-history session count. Every condition predicts the same
target-goal outcome; scope is fixed before any output.

Raw generic operations are list/filter/search by record family, time, goal,
session, source ID, tool/category, process, artifact path, exact text, manifest
path, and byte range. Snapshot access returns raw manifest/file bytes rather than
a precomputed diff. Raw never returns derived lifecycle, flow, recurrence,
conformance, pathology, intent, cause, or generated summary.

## Structured Views

- State Diff compares quiescent $H_0/W_T$ bytes and orderlessly emits create,
  delete, content/mode/type changes; rename requires source/system identity.
- Session Local partitions full raw evidence by owning top-level session,
  retains child records with parent, includes enclosing goal states and spec
  versions in force for that session,
  and provides no cross-session scratchpad.
- OCPM, HTIR, and Trajectory expose only fields frozen in `baseline-contract.md`
  and the parent plan.
- Full Trajectory may emit deterministic cross-goal recurrence candidates;
  Target Trajectory cannot.

No structured view emits a human label, generated diagnosis, intent, root cause,
or recommendation.

## One Delivery Path For All Eleven Conditions

The model begins with the common system/task prompt and **no condition evidence**.
Every evidence byte for all eleven conditions is delivered through the same
broker and turn packer. The condition namespace is:

```text
final_state | native_report | counts | state_diff | session_local |
raw_full | ocpm | htir | trajectory_full | raw_target | trajectory_target
```

Final State, Native Report, Counts, State Diff, OCPM, HTIR, and both Trajectory
conditions expose deterministic ordered item collections. Raw exposes the
generic operations above. Session Local exposes one deterministic collection per
top-level-session partition and no cross-session collection. There is no free
initial context: a mandatory `open` request returns the first envelope/page for
every condition, consumes one successful query, charges the UTF-8 bytes of the
complete canonical response, and is inserted into the next complete model
request before that inference is admitted. Further pages or queries are charged
identically.

Static views are not exempt from budgets. They paginate only at whole-item
boundaries, except declared raw-file/native-record chunks. If the mandatory
opening envelope plus one indivisible item cannot fit $B$ or the next complete
request cannot fit $T$, the condition is `infeasible` before the model sees any
condition evidence. It may not receive a truncated out-of-contract substitute.
Infeasibility of any of the eleven required conditions fails this experiment;
another condition, pooled domain, later budget, or omitted baseline cannot
rescue it.

## Broker Request And Response

```json
{
  "condition": "final_state|native_report|counts|state_diff|session_local|raw_full|ocpm|htir|trajectory_full|raw_target|trajectory_target",
  "operation": "allowlisted_operation",
  "arguments": {},
  "cursor": null
}
```

Responses use canonical compact JSON with deterministic key/item order and
include items, cursor, exact bytes, exact payload tokens, cumulative query/byte/
complete-input-token counters, remaining budget, and typed raw IDs. Cursors are
authenticated hashes of manifest, scope, operation, arguments, and last item;
they contain no hidden text.

## Exact Complete-Input Token Accounting

Pin:

- `Qwen/Qwen3-32B@9216db5781bf21249d130ec9da846c4624c16137`;
- published `Qwen2Tokenizer` and chat template at that revision;
- `transformers==5.14.1`, `tokenizers==0.23.1`;
- `trust_remote_code=False`, local hashed tokenizer files/wheels/lock;
- `add_generation_prompt=True`; and
- one identical thinking mode/output cap across conditions.

Before every inference, construct the entire model request: common system prompt,
condition instructions, complete tool descriptions/schemas, task/query,
assistant/tool history, calls, envelopes/cursors/responses, and generation prompt.
Use `apply_chat_template(..., tokenize=True)` and sum the complete request length
for every model call, including repeated history. Condition setup and schemas are
not free. A model/provider with opaque wrapping is inadmissible.

For full-history top-level session count $S$, every condition receives:

- $Q=\max(8,2S)$ successful retrieval calls;
- $B=\max(131072,8192S)$ returned UTF-8 bytes; and
- $T=\max(32768,2048S)$ cumulative complete model-input tokens.

These are dependency-test caps, not later effect-study budgets.

## Pre-Response Enforcement

For each candidate response, including every mandatory opening/static payload,
deterministically order/serialize whole items,
trim whole items to byte budget, insert the exact response into the next complete
model request, tokenize, trim again to token budget, then atomically reserve
query/byte/token counters before releasing bytes. If no item/envelope fits,
return a fixed budget error only if the next request fits; otherwise stop without
another inference. Denied payload never reaches the model.

Pagination is at item/record boundaries except explicit native/snapshot byte
chunks. Concurrent requests serialize on one condition ledger. Every accepted,
denied, malformed, tampered, escape, and internal-error attempt is append-only.

## Session-Local Determinism

Sort top-level session IDs; quotient/remainder partition $Q,B,T$, assigning the
first `total mod S` sessions one extra unit. Each isolated call sees only its raw
partition. Every per-session mandatory `open`, page, and inference passes through
the same packer and its assigned ledger; no session summary is preloaded for
free. The deterministic aggregator receives only the model outputs already
charged within those partitions and performs no retrieval or model call. It:

- unions positive labels/evidence;
- reports maximum **uncalibrated** model confidence (never a calibrated claim);
- selects earliest cited target action; and
- resolves action conflict by fixed priority
  `stop > repair_harness > clarify > redirect > continue`.

Repeated prompts/schemas/calls count in the single condition total. A session
whose initial request cannot fit its frozen partition makes the baseline
infeasible; no post-inspection reallocation.

## Verification

For **each of the eleven condition delivery modes**, tests cover mandatory-open
exact-fit and one-unit byte/token/query overruns, oversized first payloads and
records,
byte chunks, pagination/restart, cursor tampering, source/scope escape,
condition-operation mismatch, concurrency/atomic reservation, tokenizer/hash
mismatch, repeated-request charging, Session Local remainder allocation, and
byte-identical retrieval for every raw family from every structured view.

The parity table reports configured/observed maxima, complete request tokens,
denied payload hashes, Full/Target scope hashes, and raw-link coverage. Provider
usage logs or post-hoc truncation alone do not pass.
