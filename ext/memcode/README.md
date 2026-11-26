# MemCode external correlation sample

This sample implements the external-correlation shape proposed in
[issue 219](https://github.com/eunomia-bpf/agentsight/issues/219). That reply was
labelled AI-generated; maintainer review is still pending.
It adds no capture hook, extension command, controller routing, or exporter to
`agent-session`.

## Event contract

The MemCode client application can explicitly emit a line like this after a
save or recall operation, independently of its request content:

```json
{"operation":"recall","duration_ms":12,"status":"ok","request_id":"0123456789abcdef0123456789abcdef","pid":42,"starttime_ticks":7}
```

Generate the opaque request ID randomly (16 random bytes, hex encoded), never
from prompts, user IDs, keys, content, or payload hashes. Obtain PID and process
start ticks from the same process instance AgentSight is observing. A PID alone
is insufficient because the OS can reuse it. The integration app owns emitting
these events; this PR does not claim the MemCode SDK already emits them.

`MemoryEvent::parse` accepts only the declared fields, fixed operation/status
enums, a 32-character hex ID, valid PID/start ticks, a duration below one hour,
and a line below 4 KiB. Unknown fields are rejected rather than ingested.
Do not feed arbitrary MemCode request/response objects into this recipe.

## Correlation

An external adapter calls `discover_and_correlate` with an existing
`SessionCache`, `SessionProcessMatcher`, the live process-tree candidates,
FD/observed-path evidence, and a timestamp from the AgentSight capture context.
The function calls `SessionCache::discover_cached(25, Duration::from_secs(2))`,
maps the discovered sessions to matcher inputs, and uses the native matcher and
PID-to-session lookup. Events without a current process-instance match are
dropped. Child processes can be correlated through the captured tree.

Paths and transcript previews can be used locally by the existing session
layer, but this sample never projects them to memory telemetry. The sink row
contains only operation, duration, status, request ID, root PID, and an opaque
SHA-256 session key. The session key supports correlation without exposing the
original transcript session name. Request IDs should not be metric labels.

## Sinks and limits

`write_sqlite` demonstrates a separate `memcode_operations` table on an existing
SQLite connection, with request-ID deduplication. `otel_attributes` produces the
same allowlisted fields for an application's existing OTEL sink. It does not
start an exporter or wire into `ext/analysis` automatically. This keeps the
capture and session boundaries unchanged; the external adapter owns the join
and sink plumbing. Content-free guarantees rely on the emitter following the
ID contract, and on sending only `CorrelatedEvent` projections to sinks.

## Offline verification

```bash
cargo test --manifest-path ext/memcode/Cargo.toml
```

The fixture includes a private prompt, project path, session name, cross-process
events and reused PIDs. Tests exercise the actual session matcher and an actual
in-memory SQLite sink, inspect the OTEL attribute projection, reject payload
and identity fields, and prove those private values never reach either sample
sink. No live transcript discovery, server, collector or MemCode call is needed.
