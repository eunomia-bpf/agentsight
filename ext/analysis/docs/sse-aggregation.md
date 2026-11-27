# Incremental SSE aggregation by HTTP exchange

Stage 3 builds on [HTTP exchange correlation](http-correlation.md). It changes
the analysis path, not BPF capture, ring-buffer allocation or TLS identity.

## Processing and completion

```text
TLS fragments -> connection-aware HTTPParser -> HTTPDecompressor
              -> exchange-aware SSEProcessor -> materialized view
```

For known transport identities (`correlation_version=2`), uncompressed
`text/event-stream` responses are emitted as `source="http_parser"`,
`message_type="response_chunk"`. HTTP/1.1 uses the pending request's exchange
ID until the response ends. HTTP/2 uses the connection and stream's exchange
ID. One TLS read can produce several body chunks; a body chunk can also require
several TLS reads. Neither a TLS read nor a body chunk is an SSE record boundary.
An empty initial chunk binds the exchange as soon as response headers finish,
including HTTP/2 HEADERS followed by CONTINUATION. HTTP/1 message type follows
the start line, so server-side TLS writes also stream responses correctly.

The SSE processor groups these chunks by `http_exchange_id`, retains bytes
across input boundaries, then parses complete records. Split UTF-8, LF, CRLF,
CR, comments, and multiline data are handled without parsing half a record.
Unknown event types are retained in `sse_events`. This is passive observation,
not a browser EventSource client: `retry` does not trigger reconnects.

A provider's `finish_reason`, `message_stop`, usage record or `[DONE]` does not
close an exchange early. The processor waits for HTTP Content-Length exhaustion,
the final chunk/trailers, HTTP/2 END_STREAM (including trailer HEADERS), or a
terminal correlation event. This preserves later usage and other choices.
Ordinary complete HTTP response events, including successfully decompressed
SSE bodies, are accepted as a single completed input.
Their existing truncation/termination reason is retained; consuming a complete
input event does not prove that its HTTP body was captured completely.

Close, reset, GOAWAY, capture loss, timeout, eviction and capture end preserve
available SSE records as an incomplete aggregate before forwarding the terminal
correlation event. Even a close-delimited response is conservatively marked
partial on close: passive observation does not prove provider completion.
Unterminated records remain exact bytes in `unparsed_sse_hex`; they are not
silently promoted to valid events. Graceful EOF finalization requires draining
the analyzer stream; abrupt cancellation cannot guarantee an aggregate.

## Output and provenance

The aggregate retains `source="sse_processor"` and the stage-2 correlation
fields. Additional fields are:

| Field | Meaning |
| --- | --- |
| `received_bytes` | Body bytes observed by this aggregator, excluding HTTP transfer framing; can exceed the retention limit |
| `incomplete` | True for interruption, retention limits, leftover record bytes or conflicting provider IDs |
| `unparsed_sse_hex` | Retained bytes not consumed as complete SSE records, when nonempty |
| `response_id` | Provider response ID, used for reporting/consistency checks, never the grouping key |
| `completion_reason` | HTTP completion (`done`), provider `error`, or terminal/limit reason |
| `duration_ns` | Difference between the first chunk and completion timestamps, converted from milliseconds to nanoseconds |

For incremental HTTP events, `capture_metadata_scope="http_message"` means the
capture summary is **cumulative for that HTTP response**, not an additive
per-chunk delta. SSE replaces the previous summary with each newer snapshot.
Thus several chunks from the same TLS call do not inflate fragment counts or
length totals. Capture lengths include the entire contributing TLS calls and
can overlap between distinct HTTP messages; they are not traffic accounting.
Aggregation limits do not rewrite `capture_truncated`: that field describes
TLS capture quality, while `incomplete` describes the resulting SSE aggregate.

OpenAI-compatible choices/refusals and tool calls retain their choice/index
identity. Anthropic blocks retain text, thinking, signatures and partial tool
JSON; parsed tool input is exposed only after its block stops. Usage fields are
merged as provider snapshots, not added once per record. Existing Responses API
handling remains available. Conflicting provider IDs within one exchange mark
`correlation_status="ambiguous"`; they do not split/reassign the response.
Raw SSE records remain available alongside these convenience summaries.

The materialized view marks an incomplete matched or orphan aggregate
`status="partial"`; a normally terminated provider error is `status="error"`
even when the HTTP status is 200. Request/response identity still comes from
the HTTP exchange, not from matching provider IDs.

## Bounds and compatibility

- At most 1,024 active exact SSE aggregates; the oldest is flushed as partial
  on capacity pressure. Each retains at most 4 MiB of input body bytes and
  100,000 parsed records. Active aggregates also share a 64 MiB retained-input
  budget, released when an aggregate is emitted. This conservatively counts
  all retained input, including bytes already parsed into records. Serialized
  JSON and parser objects add memory overhead; these are input-retention bounds,
  not total allocation/RSS bounds.
- After a per-response or shared limit, later body bytes are counted but not retained;
  the aggregate is emitted at termination/end/timeout with reason `truncated`.
- The default idle timeout is 30 seconds, evaluated against timestamps when
  another input event arrives. It is not a wall-clock background timer.
  A bounded, timeout-limited retired-ID cache suppresses late chunks; it is not
  an unlimited deduplication history.
- HTTP/1 transfer chunks still need valid complete framing within the existing
  1 MiB per-direction buffer. The total SSE body can exceed that HTTP buffer
  as completed transfer chunks are drained. HTTP/2 DATA is drained per frame.
- Compressed SSE keeps the existing bounded whole-HTTP-body/decompression path;
  incremental gzip/brotli/zstd decompression is not introduced here.
- Events without complete transport identity keep the existing raw/legacy SSE
  routing and heuristic lifetime rules. The new completion/bounds contract is
  for protocol-bound responses, not a promise of exact legacy reconstruction.
- Stage-2 pending-request expiry and capture-loss quarantine remain in effect.
  Very long calls, missed bytes and captures starting mid-connection can still
  yield partial or unlinked results. This work does not eliminate ring-buffer
  reservation failures or reconstruct bytes that were never captured.

## Deterministic regression coverage

`http_stream_tests.rs` exercises the full HTTP -> decompression -> SSE -> view
path for interleaved connections, pipelined responses, HTTP/2 streams/trailers
and reset, split UTF-8, cumulative provenance, a body exceeding the old HTTP/1
whole-message bound, compressed compatibility, provider errors, and interrupted
captures. It includes same-PID/TID raw TLS interleaved with chunked SSE on
another handle, header-time binding, server-written responses, and truncated
stream prefixes. `sse_stream_tests.rs` covers bytewise SSE framing, provider variants,
response-ID conflicts, timeout/eviction, per-response byte/event limits, and
shared retention-budget release. Existing raw SSE,
HTTP parsing and persistence tests remain enabled. These fixtures do not replace
a fresh live Kimi swarm coverage/performance measurement.
