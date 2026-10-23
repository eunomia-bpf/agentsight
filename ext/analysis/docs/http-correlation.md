# HTTP exchange correlation

This is the second stage of the TLS identity work in #208 and #210. It consumes
the additive capture metadata from #210; it does not change the BPF probes,
ring-buffer allocation, provider adapters, or agent-native session parsing.

## Identity and processing order

For captures with a nonzero `transport_handle`, a nonzero `process_start_ns`,
and a known `tls_library`, the parser resolves
`(pid, process_start_ns, tls_library, transport_handle)` to an opaque,
capture-local `connection_id`. TID remains execution provenance, not a
connection key. A supported `CLOSE`, ten-minute idle expiration, or state
eviction retires the identity. A later observation receives a new ID. Raw TLS
addresses are not embedded in these IDs or added to the SQLite/OTel call model.

The HTTP analyzer chain is:

```text
TLS events -> legacy SSE pass-through for known transport identities
           -> HTTPParser -> HTTPDecompressor -> SSEProcessor -> materialized view
```

Standalone raw SSE processing remains available. Events with incomplete or
unknown transport identity (rustls-based captures such as Codex and Grok, and
traces recorded before #210) use the same HTTP/1 reassembly, keyed per
`(pid, tid)` as before; their evidence is labeled `inferred` and must not be
interpreted as exact connection evidence. Because there is no close event for
them, a response without Content-Length or chunked framing is emitted with the
bytes buffered so far.

* HTTP/1.1 buffers are separate for each connection and direction. A message
  is a request or a response according to its start line, not the TLS
  direction, so a captured server (requests read, responses written) pairs the
  same way. Complete requests receive successive exchange IDs; final responses
  use the pending request FIFO. Invalid or conflicting Content-Length values and
  malformed chunking are protocol errors (see below). Informational responses do not consume that FIFO. HEAD, 204,
  and 304 responses do not require a body. Content-Length, chunked encoding
  (including trailers), and close-delimited responses are supported.
* HTTP/2 frame remainders, directional HPACK decoders, pending CONTINUATION
  blocks, and streams belong to one connection. The exchange key includes the
  stream ID. Actual TIDs are retained, not replaced with synthetic stream TIDs.
  Responses finish at END_STREAM; RST_STREAM and GOAWAY produce terminal
  correlation records for affected streams.
* The existing SSE processor preserves the HTTP exchange evidence when it
  converts a complete HTTP body into an SSE aggregate. This stage does **not**
  emit incremental response-body chunks. Streaming SSE framing, early emission,
  and bounded incremental aggregation belong to the third stage.

## Derived event fields

| Field | Meaning |
| --- | --- |
| `connection_id` | Opaque identity within this parser/capture instance |
| `connection_generation` | Diagnostic generation for recently retired handles; bounded history, not a globally persistent counter |
| `stream_id` | HTTP/2 stream ID; null for HTTP/1.1 |
| `http_exchange_id` | Shared request/response key, distinct from provider IDs |
| `correlation_method` | `h1_connection_fifo`, `h2_stream`, or explicitly labeled legacy evidence |
| `correlation_status` | `exact` for protocol matching with known identity, `inferred` for legacy evidence, `unlinked` for unmatched/terminated calls |
| `correlation_version` | 2 for known transport identity, 1 for legacy behavior |
| `confidence` | Ranking of the matching evidence, not a calibrated probability or a promise of loss-free capture |
| `completion_reason` | Normal completion, TLS close, capture end, timeout, eviction, capture loss, reset, GOAWAY, truncation, or protocol error |
| `end_stream` | Whether this HTTP message is complete; false for informational responses |

Capture provenance retains #210's summary contract. Each contributing TLS call
is counted once per derived HTTP message, including fragments containing only
a partial header/frame. A single TLS call can contribute to multiple messages;
therefore their capture length totals are not additive traffic accounting.
Binary bodies are preserved in `body_hex` before decompression.

`source="http_correlation"` denotes terminal/partial evidence, not an HTTP
response. `completion_reason="partial"` may additionally carry
`termination_reason`, `buffered_bytes`, and optional raw bytes. Pending call
rows retain `status="pending"` for compatibility but gain
`correlation_status="unlinked"` and the terminal reason.

## Loss and incomplete captures

A record that arrives with `truncated: true` lost its tail inside the capture.
For HTTP/1.1 the message it belongs to is **not dropped**: it is emitted for the
prefix that was seen (start line, parsed headers, body prefix) with
`body_truncated: true`, `body_truncation_reason` (`capture_truncated`, or
`body_limit` when a message passes the 1 MiB cap) and `body_captured_bytes`;
`content_length` is still the size the peer declared and `completion_reason` is
`truncated`. Requests still enter the exchange FIFO, so their responses pair
normally. When the message has a declared Content-Length and the record reports
how many bytes it lost (`bytes_lost`), the parser discards exactly the rest of
that body and the connection stays usable for later requests. Otherwise (chunked
or close-delimited framing, an unreported or too-large loss, a loss that left no
visible message start) the framing cannot be realigned: the connection's
pending exchanges are terminated as `truncated` and matching stops until the
connection is retired. Non-HTTP/1 protocols (HTTP/2 frames, WebSocket
compression state) stop matching on any truncated record.

The ring-buffer failure counter is tracer-wide. A changed counter, including
the final `CAPTURE_LOSS` record, invalidates all currently active connections'
pending parser state. A truncated TLS payload invalidates its connection.
Those connection lifetimes stop protocol matching until retirement; raw input
is retained. This intentionally sacrifices coverage instead of guessing an
HTTP/1 FIFO position or continuing with an unreliable HPACK dictionary.

An explicit exchange ID that has no pending request never falls back to a
different PID/TID request. Only legacy events without explicit HTTP identity
use the existing request-ID/unique-thread-candidate fallback.

End of input terminates remaining known exchanges with `capture_end`. It is
not treated as a TLS close, so an unfinished close-delimited body is not
silently declared complete. This finalization requires the event stream to be
drained; abrupt cancellation cannot guarantee it.

## Persistence and compatibility

SQLite `llm_calls` and exported call rows add nullable protocol, connection,
stream, exchange, provider request/response ID, and correlation evidence
columns. Writable databases use additive column migration. Read-only legacy
databases synthesize nulls for absent columns. OTel includes the corresponding
evidence attributes when present. Existing request/response payloads remain
unchanged; no historical rows are retrospectively re-correlated.

## Limits

This is passive reconstruction, not a full HTTP endpoint. Capture starting
mid-connection, a missed lifecycle event followed by address reuse, unreported
loss, or plaintext delivered out of protocol order cannot be proven correct
from TLS handles alone. A new opaque ID is not proof of a new TCP connection.

State is bounded: 1,024 active connections, 1,024 HTTP/2 streams/pending header
blocks per connection, 64 KiB header blocks, 1 MiB HTTP/2 bodies, and a 1 MiB
HTTP/1 message prefix per direction (beyond it the message is emitted with
`body_truncated`; a chunked or close-delimited message over the cap cannot be
realigned and stops matching the connection). Buffered fragment provenance is capped at 4,096 entries per
direction, and HTTP/1 pending request queues at 1,024. Materialization retains
at most 16,384 pending exchanges with a
five-minute expiry. Exceeding limits produces terminal evidence rather than a
successful association. Large/long-running SSE responses can therefore remain
unlinked in this stage; incremental aggregation is deliberately deferred.
