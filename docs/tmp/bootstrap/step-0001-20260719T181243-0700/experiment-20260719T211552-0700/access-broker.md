# Matched-Access Broker Contract

Status: frozen proposal for independent review; no supervisor inference has run.

## Purpose

Every tool-mediated condition uses one read-only broker and one model-turn
packer. Matched access is enforced before inference, not inferred from logs. The
supervisor receives no shell, direct filesystem access, `rg`, `jq`, database
client, notebook, or unmetered side channel.

## Pinned Accounting Model And Tokenizer

Feasibility accounting is fixed to:

- model/tokenizer repository: `Qwen/Qwen3-32B`;
- immutable revision: `9216db5781bf21249d130ec9da846c4624c16137`;
- tokenizer class published at that revision: `Qwen2Tokenizer`;
- `transformers==5.14.1`;
- `tokenizers==0.23.1`;
- `trust_remote_code=False`;
- the repository chat template at the pinned revision;
- `add_generation_prompt=True`; and
- one frozen thinking-mode value for all conditions.

Before use, the exact repository tokenizer files, chat template, package wheels,
and dependency lock are cached and SHA-256 recorded. The test loads the cached
revision with `local_files_only=True` and rejects any hash mismatch. A hosted
provider is admissible only if it consumes the identical rendered token stream;
otherwise inference must use the pinned open-weight model locally. Opaque
provider-added prompts or an approximate token estimator are disallowed.

Changing model, revision, tokenizer packages, template, thinking mode, or tool
serialization invalidates parity and requires a newly reviewed broker audit.

## Request

Every broker request contains:

```json
{
  "condition": "raw_full|raw_target|state_diff|ocpm|htir|trajectory_full|trajectory_target",
  "operation": "condition-specific allowlisted operation",
  "arguments": {},
  "cursor": null
}
```

The broker validates condition/operation and resolves it only against one frozen
workspace supervision manifest. `*_full` binds to $H_0\rightarrow W_T$;
`*_target` binds to the target-goal window and its two atomic boundary snapshots.
All conditions receive budgets computed from the full interval, so Target-Only
does not win or lose through a smaller budget. Requests cannot escape the bound
raw stores, session IDs, goals, time range, workspace roots, snapshots, or
baseline artifacts.

Final State, Native Report, and Counts are fixed one-shot inputs and use the same
turn packer even when they need no retrieval call. Session Local uses isolated
per-session broker instances whose aggregate counters share the condition total.

## Response

```json
{
  "items": [],
  "next_cursor": null,
  "response_utf8_bytes": 0,
  "response_payload_tokens": 0,
  "cumulative_queries": 0,
  "cumulative_utf8_bytes": 0,
  "cumulative_model_input_tokens": 0,
  "budget_remaining": {},
  "source_ids": []
}
```

The canonical compact JSON serializer, key order, UTF-8 encoding, escaping, and
newline policy are frozen. All delivered envelope fields, item text, cursors,
source IDs, and error payloads count. A constant field is either counted for
every condition or omitted for every condition.

`response_payload_tokens` is diagnostic only. The binding token budget is
`cumulative_model_input_tokens`, defined below.

## What The Token Budget Counts

For every attempted model inference, the turn packer constructs the **entire
request the model would see**:

- common system prompt;
- condition name and condition-specific instructions;
- all tool names, descriptions, JSON schemas, defaults, and examples;
- user/task query;
- prior assistant messages, reasoning fields if retained, and tool calls;
- every prior tool response/envelope/cursor;
- the candidate current tool response; and
- the generation prompt inserted by the pinned chat template.

It calls the pinned tokenizer's
`apply_chat_template(messages, tools=..., tokenize=True,
add_generation_prompt=True, <frozen thinking mode>)`. The token charge for a
model call is the length of that complete rendered request. The cumulative input
charge is the sum of complete request lengths over all model calls, matching the
fact that repeated API calls resend prior context. Repeated prompts and schemas
in Session Local are therefore charged repeatedly.

Condition-specific prompt/schema material is never treated as free setup.
Output tokens have one identical cap and are measured separately for compute
reporting; they cannot be exchanged for more input access.

## Label-Independent Feasibility Budget

Let $S$ be the number of genuine top-level sessions in the frozen interval.
Before any condition output is constructed, every condition for that interval
receives the same totals:

- successful retrieval queries: $Q=\max(8,2S)$;
- UTF-8 response bytes: $B=\max(131072,8192S)$; and
- cumulative complete model-input tokens: $T=\max(32768,2048S)$.

These caps exist only to test enforcement and Session Local partitioning; they
are not an effect-study budget. A future diagnosis experiment must freeze its
budget rule from source-size distributions, context limits, and a development-
only pilot before viewing test condition outputs.

## Pre-Response Enforcement

For a retrieval response:

1. resolve and deterministically order complete candidate items;
2. serialize the candidate response with the canonical encoder;
3. remove trailing whole items until the cumulative byte cap fits;
4. place that exact candidate response into the next full model request;
5. render/tokenize the entire request with the pinned chat template;
6. remove more trailing items until cumulative complete-input tokens fit;
7. atomically reserve query, byte, and token counters; and
8. only then release the response and invoke the model.

If no complete item plus required envelope fits, return a fixed minimal
`budget_exhausted` response only if the next model request still fits. Otherwise
the host terminates the condition without another inference. Denied payload
bytes never reach the model. Every attempt is appended to an audit transcript.

Exact-fit, byte-overrun, token-overrun, and query-overrun paths are tested
independently with synthetic records, so exhaustion of one cap cannot hide a
broken second cap.

## Determinism And Atomicity

- Items use a total order fixed by source time, session ID, source-call ID, then
  deterministic subitem ID.
- Pagination occurs only at source-record or typed-item boundaries. Native byte
  chunks are the sole exception and expose explicit start/end offsets.
- Cursors are authenticated hashes of episode, condition, operation, normalized
  arguments, last item/offset, and broker schema revision. They contain no hidden
  result text.
- A transaction reserves all three counters. Concurrent requests serialize on
  one condition ledger; failed reservations expose no payload.
- Accepted, denied, malformed, cursor-tampered, source-escape, and internal-error
  requests are retained in an append-only transcript with pre/post counters.

## Shared Raw Evidence

The immutable raw store contains every bottom-level fact any structured view may
use:

- complete native Agent request/response/tool/session records;
- system-effect records with monotonic timestamps and process/workspace identity;
- every atomic boundary-snapshot manifest plus allowed raw file bytes/chunks;
- evaluator, test, metric, and outcome records;
- task and goal specifications; and
- frozen skill, prompt, tool-schema, harness, and orchestration artifacts.

Each object has a typed canonical ID, content hash, and origin manifest. Native
actions retain `<session_id>#<source_call_id>`; the other families use
`system:`, `snapshot:`, `evaluator:`, or `spec:` prefixes. Every structured item
must cite a nonempty set of these IDs. The parity audit follows every cited ID
through Raw and byte-compares the returned bottom-level record.

Full-History Raw can list/filter/search every permitted raw family in
$H_0\rightarrow W_T$ and fetch a record or byte range by ID. Target-Only Raw has
the identical schema but is restricted to target-window actions/effects, target
start/end snapshots, target evaluator records, and the same frozen static
specifications. Full/Target Trajectory use those respective scopes exactly.

Generic Raw primitives include chronological range, record-family, session/goal,
source ID, tool/category, process, artifact path, exact text, manifest path, and
raw byte range. Snapshot-file access is byte/chunk access, not a precomputed
diff. Raw receives no derived lifecycle, flow, recurrence, conformance,
pathology, intent, cause, or generated summary. Structured indexes may differ
only because that difference is the tested representation. Index build time,
bytes, latency, and returned evidence volume are reported.

## Session-Local Partition And Aggregation

Sort genuine top-level session IDs lexicographically. Partition $Q$, $B$, and
$T$ by integer division; the first `total mod S` sorted sessions receive one unit
of the remainder. Each isolated supervisor call receives only raw
native/system/evaluator records in its session, the static specifications, and
the exact goal-boundary snapshots that enclose it. It receives no other
session's actions or outputs. Child/subagent records remain with the parent
session that owned them.

The fixed aggregator receives only schema-valid per-session outputs, never raw
evidence. It:

- unions positive pathology labels;
- takes the maximum **uncalibrated** model-reported confidence per label, used
  only as deterministic baseline output and never described as calibrated;
- unions cited canonical evidence IDs;
- chooses the earliest cited intervention by global source timestamp with
  source-ID tie-break; and
- resolves conflicting intervention actions by the frozen priority
  `stop > repair_harness > clarify > redirect > continue`.

The priority is a deterministic baseline rule, not a claim that it is optimal.
Every system prompt, schema, model call, and aggregator input is charged to the
single Session Local condition total. If any session's initial request cannot fit
its frozen partition, Session Local is infeasible for that case; the baseline
obligation fails rather than silently reallocating budget after inspection.

## Verification Matrix

Automated tests must cover:

- exact byte fit and one-byte overrun;
- exact full-turn token fit and one-token overrun;
- query exact fit and one-query overrun;
- oversized single record and native byte chunking;
- deterministic pagination and restart;
- cursor tampering, source escape, and condition/operation mismatch;
- simultaneous requests and failed atomic reservation;
- identical typed raw-ID/byte retrieval from the matching Raw scope for every
  structured item, covering native, system, snapshot, evaluator, and spec data;
- full rendering of system, condition instructions, tools, queries, envelopes,
  responses, assistant history, and generation prompt;
- tokenizer/template/hash mismatch rejection;
- repeated-context charging over two or more model calls; and
- deterministic Session Local quotient/remainder allocation.

A parity table reports configured totals, actual maxima, denied payload hashes,
and complete-input token counts for every condition. Post-hoc provider usage logs
or output truncation alone do not constitute enforcement.
