# Windows Native Capture: Phase 1 Design

Status: backend stack 1 of 2; latest-head elevated runtime smoke remains pending.
Date: 2026-11-15.
Source baseline: commit `c1574366122a90c451bca6a84713e28813ab95e2` (`1.0.35`).
Target platform for initial validation: Windows 11 x86-64.
Related roadmap: [issue #17](https://github.com/eunomia-bpf/agentsight/issues/17).

This note defines the review contract for adding a native Windows process
capture backend. It is narrower than a general "Windows parity" plan: this PR
adds the process-lifecycle transport, decoder, tracker, and a target-gated
smoke. A stacked follow-up wires the backend into `top --pid` and the shared
process projection without changing the Linux capture path.
File, network, TLS, helper IPC, and command launch are intentionally deferred.

When this design conflicts with current source behavior, the source and focused
user-facing docs remain authoritative. Live validation evidence for the tested
machine is recorded below; portability to other Windows builds, privilege
boundaries, and workloads remains to be established.

## Problem

Windows currently supports agent-native session discovery, process snapshots,
reports, visualization, and binding. The eBPF runner path is Linux-only, so
Windows lacks independent evidence for short-lived child processes and their
lifecycle. `sysinfo` snapshots can show a process that survives a sampling
interval, but they cannot reliably observe a process that starts and exits
between samples or reconstruct its creation and exit ordering.

The backend should use Event Tracing for Windows (ETW) to supply process
lifecycle evidence to the existing `Runner` and `EventStream` boundary. The
goal is incremental, observable evidence, not a promise of complete equivalence
with Linux eBPF capture.

## Phase 1 goals

1. Capture process creation and exit for one explicitly selected running root
   process and its descendants.
2. Feed normalized events through the existing `Event` model and analyzer
   pipeline without changing the public `Runner` trait.
3. Preserve target safety: attach only, never launch or terminate the target.
4. Make failures and known loss explicit rather than silently falling back to
   snapshots or emitting a misleading empty stream.
5. Keep all Windows API use behind `cfg(windows)` so Linux and other supported
   targets remain unaffected.
6. Establish a small, reviewable implementation seam for later file, network,
   privilege separation, and recording work.
7. Bind captured descendants to the selected `top --pid` root even after a
   short-lived child exits before the next process snapshot.

## Phase 1 non-goals

- No file, network, TLS, stdio payload, or resource-event capture.
- No command launch, suspended-process management, or launch-ready handshake.
- No privileged helper or cross-user IPC.
- No `top` behavior beyond the explicit `--pid` capture path. No changes to
  `record`, `monitor`, `bind`, or the Web/Node privilege boundary.
- No kernel driver, certificate installation, global DLL injection, proxy, or
  mandatory background service.
- No claim of complete Windows/Linux feature parity.
- No attempt to observe WSL2 or Linux-container internals through host ETW.
- No change to the Linux eBPF loaders or `BinaryExtractor` behavior.

## Terminology

| Term | Meaning in this design |
| --- | --- |
| ETW | Event Tracing for Windows, the operating system event tracing infrastructure used for this backend. |
| Provider | An event source identified by a provider GUID and selected by flags, keywords, levels, or event descriptors. |
| Controller | The component that creates, configures, queries, and stops an ETW session. |
| Consumer | The component that opens a real-time trace and receives `EVENT_RECORD` callbacks through `ProcessTrace`. |
| ETW session | A kernel-backed tracing session. It is unrelated to an AgentSight agent session. |
| SystemTraceProvider | The classic system provider used for the first process-only implementation. |
| `EVENT_TRACE_FLAG_PROCESS` | The classic system-provider process-event enable flag. |
| System logger | A kernel-backed logger that can collect SystemTraceProvider events under a caller-owned session name and control GUID. |
| Rundown / DCStart | Events emitted for processes that already existed when tracing started. They are observations of pre-existing state, not new process creation. |
| PID / PPID / TID | Process, parent-process, and thread identifiers. All can be reused and cannot alone identify a process instance. |
| Process instance | One execution of a program from creation to exit, identified by node identity plus PID and creation identity when available. |
| FILETIME | Windows time represented as 100-nanosecond intervals since 1601-01-01 UTC. |
| Event time | The timestamp attached to the observed ETW event. |
| Receive time | The local time at which the consumer processes the record; it is diagnostic ordering, not event time. |
| `EventStream` | The repository's asynchronous `Stream<Item = Event>` boundary between capture and analysis. |
| `Runner` | The trait implemented by process, SSL, system, and future native capture sources. |
| Provenance | Metadata describing that an event was observed by ETW, including provider, schema, capture mode, and limitations. |
| Bounded queue | A fixed-capacity channel between the ETW callback and async processing. Saturation increments a loss counter instead of blocking the callback. |
| Attach mode | Capture of a target that was started independently by the user. Stopping capture does not stop the target. |
| NT Kernel Logger | The reserved classic ETW session name required when a session is controlled by `SystemTraceControlGuid`. It is not an AgentSight-owned arbitrary name. |

## Architecture

```text
Selected root PID
  -> ETW controller: owned real-time process session
  -> ETW consumer thread: ProcessTrace + EVENT_RECORD callback
     -> shallow-copy required header/payload fields inside callback
     -> bounded nonblocking queue
  -> async decoder/process tracker
     -> descendant attribution and PID-reuse checks
     -> Windows adapter: Event with Unix epoch milliseconds
  -> existing Runner / EventStream / analyzers
```

### Module boundaries

The first implementation should keep the public surface small:

```text
agentsight-capture/src/runners/windows_etw/
  mod.rs      Runner adapter, async stream, attribution, and diagnostic replay.
  runtime.rs  ETW controller, real-time consumer, callback, and stop semantics.
  payload.rs  Process schemas, phase mapping, and FILETIME conversion.
  tracker.rs  Process instances, parentage, PID reuse, and bounded retention.

collector/src/cmd_perf_live.rs
  Elevated `top --pid` capture startup and non-elevated snapshot fallback.

collector/src/view/live_top.rs
  Root-bound process-event attribution and backend-specific evidence labels.

ext/analysis/src/runners/mod.rs
  Portable analyzer and view integration.
```

The native runner must not use `BinaryExecutor`: that type executes the
external Linux eBPF loader path and is not a general process abstraction.
Likewise, the Windows `top` branch must not instantiate `BinaryExtractor`,
because `BinaryExtractor::new` currently rejects non-Linux capture
environments.

### Command surface

Complete command lines are omitted by default because they commonly contain
tokens or credentials. The product `top --pid` path always omits command lines;
only the target-gated smoke fixture can opt in for transport validation.

The stacked product entry will be:

```text
agentsight top --pid <pid>
```

When that command runs in an elevated terminal, it will start the same
process-only ETW backend and attribute short-lived descendants to the selected
root. In a normal terminal it will keep the existing snapshot and agent-native
session view and report that ETW is inactive. The command will never request
elevation.

This behavior is compile-time Windows-only. Non-Windows builds retain the
existing eBPF and portable process paths.

## ETW provider and event mapping

The first implementation uses the classic SystemTraceProvider with
`EVENT_TRACE_FLAG_PROCESS` in a real-time system logger. It does not occupy the
reserved `NT Kernel Logger` session: a fixed AgentSight control GUID plus
`EVENT_TRACE_SYSTEM_LOGGER_MODE` gives the session an independent name that can
coexist with the Windows kernel logger. This avoids terminating another
controller or failing merely because a reserved logger is already active. The
implementation must record the provider identity, descriptor/version, pointer
width, schema, OS build, and privilege context used during validation.

Process events map to the existing event vocabulary as follows:

| ETW observation | `Event.source` | `data.event` | Required semantics |
| --- | --- | --- | --- |
| Process `Start` | `process` | `EXEC` | New process creation. Include Windows phase metadata so it is not interpreted as an exact Linux `execve`. |
| Process `DCStart` | `process` | `PROCESS_PRESENT` | Pre-existing process observed during startup rundown. It seeds process identity without incrementing a new-process count. |
| Process `End` | `process` | `EXIT` | Observed exit. Exit status is included only when the selected schema supplies it. |
| Process `DCEnd` | `process` | `PROCESS_PRESENT_AT_STOP` | Rundown confirms that the process still existed when tracing stopped. It must not be reported as an exit or used to mutate live-exit state. |
| Process `Terminate` (opcode `0x0B`) | `process` | `EXIT` | Legacy terminate signal whose four-byte payload is the terminated PID. Treat it as provisional: publish it only if no authoritative `End` arrives before capture stops; a later `End` replaces it and supplies exit status. Do not substitute the event-header process context for the payload PID. |
| Unknown or malformed record | `diagnostic` | `ETW_*` | Never reinterpret an unknown schema as a known process event. Include a parse/decode failure reason. |

The adapter should preserve the original Windows fields needed for review,
such as PID, PPID, image or command-line data when available, user identity
when available, and the ETW phase. Fields that are absent remain absent; the
adapter must not invent an exit code, parent, path, or completion outcome.

Payload decoding must be schema-driven. A known Event ID alone is insufficient
when the provider, descriptor, version, or architecture differs. Unknown
layouts must produce diagnostics and must not be unchecked-cast to an older
structure.

The first implementation supports process payload versions 0 through 4. Version
4 adds the process flags field before the SID and app-container strings after
the command line; Windows 11 x86-64 emits version 4 in the recorded smoke run.
Version 5 and the defunct opcode are outside this PR and must produce an
unsupported-schema diagnostic rather than being decoded with the version 4
layout.

A null user SID is encoded as one 32-bit zero after the fixed header. A non-null
SID retains the `TOKEN_USER` shape and variable-length SID. The decoder must
distinguish these encodings before reading the process image. For versions 1
through 4, the image filename and the version 2+ command line are required
NUL-terminated fields; missing terminators are decode failures. The version 4
package and application strings may be absent at the end of the record. Versions
1 through 4 carry an exit status on `End`, which is emitted as the portable
`exit_code` attribute.

## Process tracking and identity

The selected PID identifies the root only at attach time. Once the runner has
bound the root to a process instance, later reuse of the same PID must not
authorize the new process as part of the capture tree.
On Windows the root snapshot identity is the 100-nanosecond creation `FILETIME`
from `GetProcessTimes`, not sysinfo's second-granular start time. The weak
second-granular value is only a display fallback. The collector re-reads the
strong identity before and after starting ETW and withholds captured evidence
if the PID changed process instance.

The tracker should maintain:

- root PID and the strongest available root creation identity;
- live child membership by parent instance, not by PID alone;
- creation-time or provider-supplied process keys when available;
- a capture-local instance identifier when strong creation identity cannot be
  verified, marked as weaker identity;
- PPID reconciliation for records whose parent exits before the child record is
  processed;
- bounded state with explicit eviction counters.

The process provider's `UniqueProcessKey` is the address of the current kernel
process object. It is useful for correlating records while that object is
alive, but it is not the public Windows `ProcessStartKey` and is not a
permanent identifier. Once an instance is observed exiting, a later `Start`
with the same key must create a new capture-local instance rather than reviving
the retained exited record. The emitted `process_instance_id` is tracker-owned,
stable only within one capture, and may not be joined across captures.

`DCStart` records seed the tree with already-running descendants. Overlapping
live `Start` and rundown observations must be idempotent: the same process
instance cannot be counted twice.

Parent resolution must be incremental. The tracker should index unresolved
children by PPID and linked children by parent instance, then visit only the
subtree affected by a new parent or membership change. A full scan or clone of
every tracked instance on each system-wide process start is not acceptable.
Periodic compaction may scan retained instances, but its cost must be amortized
and any cache eviction must remain observable.

ETW can deliver a child `Start` after its parent's `End`. A bounded recent-exit
map may retain the most recently exited member instance for that PPID so the
late child can still be attributed. A new `Start` with the same PID clears the
old mapping before any child can attach. Nonmember/unresolved instances and
ambiguous parent PIDs also have explicit caps. A global instance cap covers
members whose `End` was lost, and eviction of a member without an observed exit
has its own counter. Lost events therefore degrade attribution instead of
growing tracker memory without bound.

Ambiguity entries carry a monotonic token so an old FIFO entry cannot clear a
new collision for the same PID. Competing-generation ambiguity clears once at
most one live instance remains for that PID. If the instance cap must evict an
active member that has linked children, the PID remains fail-closed because the
missing `End` makes later PID ownership unknowable; those children are not
returned to a bare-PPID adoption bucket. This poisoned state is bounded by the
same ambiguity cap and its eviction is counted.

Each generation records three distinct time boundaries. `generation_started_at`
is set only by the first live `Start` observation and is the strongest
generation boundary available to the tracker.
`first_start_observed_at` preserves that first live `Start` observation even if
later bookkeeping changes, while `first_rundown_observed_at` preserves the
first `DCStart` observation. A `DCStart` timestamp is the time ETW emitted the
startup rundown record; it is not the actual creation time of the pre-existing
process and must not be presented as one.

When the same process key is first observed through `DCStart` and later through
a live `Start`, the live `Start` may resolve to the existing instance and be
reported as a duplicate. Even then, the tracker backfills the instance's
`first_start_observed_at` and `generation_started_at` boundaries before
returning the duplicate result. This prevents an earlier observation-only
rundown timestamp from masquerading as the generation's live creation boundary.
For keyless schema versions 0 and 1, where a provider-supplied process key is
unavailable, replaying the same `Start` at the same ETW timestamp resolves to
the existing instance rather than creating a second generation.
The first live `Start` for the same PID after such a keyless instance has only
been observed through `DCStart` is also rundown/live overlap, not immediate PID
reuse: the instance still lacks `first_start_observed_at`, so the tracker
backfills `generation_started_at` and returns a duplicate while retaining one
instance and one live PID count. Only a later `Start` with a different
timestamp may enter the PID generation-reuse path.

`Terminate` and `End` are two observations of at most one logical exit for a
process instance. The first `Terminate` updates tracker identity and membership
state immediately but remains unpublished. A later `End` is published once
with any available exit status; if capture stops without that `End`, the held
`Terminate` is flushed once as the fallback exit evidence. Repeated
`Terminate`/`End` combinations must not produce a second EXIT audit or a second
exit-only process node. Provisional exits have their own bounded cache. Tracker
eviction clears any provisional entry for that instance. Capacity drops and
tracker-requested provisional cleanup are counted separately from event
decoding and native ETW loss.

`DCEnd` is not an exit. At trace stop, process rundown reports instances that
still exist, so the adapter names it `PROCESS_PRESENT_AT_STOP`. It must not
decrement the live-generation count, populate the recent-exit map, suppress a
later `End`, or increment `top` exit counters.

A keyless exit that overlaps multiple generations is resolved only when PPID,
session, image, and event-time boundaries identify one unique instance. If the
evidence still matches more than one retained generation, the event remains
deferred and fail-closed; another generation's keyed exit is not treated as
proof that the keyless record belongs to the survivor. The first unresolved
keyless event snapshots the original candidate-instance witness set for that
PID. Matching uses that witness set rather than whichever instances happen to
remain after cache compaction. Ordinary exit compaction preserves witness
instances. If a global capacity eviction removes a witness, the witness set is
marked incomplete and all further keyless attribution for that PID fails
closed instead of silently accepting the sole remaining live generation.

Both live-parent and recent-exited-parent attribution pass through the same
generation guard. A child whose live `Start` timestamp predates the current
parent generation's `generation_started_at` is not attributed to that parent.
When a new parent generation has a reliable `generation_started_at` but the
child lacks a reliable time, attribution also fails closed rather than guessing
ownership from PPID alone. This covers a late or replayed child from an evicted
generation whose PID has already been reused. Per-PID live-generation counters
make ambiguity reconciliation constant time; cleanup does not scan the full
65,536-instance table.

The phase 1 defaults are 1,024 recent exited members, 4,096 retained
nonmembers, 1,024 ambiguous parent PIDs, and 65,536 total tracked instances.
These are implementation limits, not claims about workload capacity; hitting
one is reported in capture metadata.

If the root exits, descendant tracking continues until the descendant set exits
or capture stops. Root exit does not implicitly terminate descendants and does
not terminate capture.

The live product retains the selected root's latest image name and exit
observation before projection. `PROCESS_PRESENT` remains a state observation
rather than a synthetic new-process count, but this retained metadata lets
`top` keep a capture-only root row after the PID disappears from the process
snapshot. A different creation identity for the same PID withholds that
captured evidence instead of merging the new process into the old row.

## Timestamps

The output `Event.timestamp` is Unix epoch milliseconds. The consumer should
not set `PROCESS_TRACE_MODE_RAW_TIMESTAMP`; `ProcessTrace` then supplies
converted system timestamps. The adapter converts FILETIME with checked
arithmetic:

```text
unix_ms = (filetime_100ns - 116444736000000000) / 10000
```

The ETW runner must bypass `TimestampNormalizer`. That analyzer converts Linux
boot-relative nanoseconds and must not receive a second, differently defined
timestamp domain.

For diagnostics, the event data may preserve a local receive sequence. A
receive timestamp may be used for health ordering, but it must not replace the
event timestamp. Invalid or out-of-range times produce a diagnostic; they do
not silently become the current time.

## FFI and lifecycle requirements

ETW has several sharp edges that are part of the design contract:

- `ProcessTrace` blocks and must run on a dedicated thread. Dropping or aborting
  an async task does not stop the native session.
- The `EVENT_RECORD` callback is a Win32 callback boundary. Rust panics must
  not unwind across it; catch and convert failures to bounded diagnostics.
- An `EVENT_RECORD` copy is shallow. The callback must copy every header and
  payload field required after return; it must not retain pointers into the
  record.
- Callback context must outlive `ProcessTrace` and be released only after the
  consumer thread joins.
- The callback must not block on database writes, network calls, path queries,
  or expensive decoding. It should attempt a bounded enqueue and return.
- Queue insertion must use nonblocking `try_send` semantics. Saturation
  increments a dropped-record counter and emits a final or periodic diagnostic.
- Stop must be idempotent: signal the stream, stop the owned ETW session so
  `ProcessTrace` can return, keep the consumer handle across a bounded wait,
  call `CloseTrace` as the fallback that unblocks a consumer when session stop
  did not, and drain records already accepted by the bounded application queue
  before freeing callback state. A join timeout is an explicit cleanup error;
  it is not permission to report a clean stop or abandon ownership silently.
- The runner stops only sessions it created. It must never stop an unrelated
  session with a similar name and must never terminate the attached target.
- The AgentSight system logger uses `EVENT_TRACE_SYSTEM_LOGGER_MODE`, a stable
  session name, and a control GUID distinct from `SystemTraceControlGuid`.
  A same-name conflict is an error; it is not permission to terminate another
  controller's session. The error must distinguish an occupied AgentSight
  session from insufficient capture privilege.

## Privileges and safety

Classic system-process tracing is expected to require an elevated capture
process. Phase 1 therefore uses a deliberately constrained workflow:

1. The target is started normally by the user.
2. The operator runs `agentsight top --pid <pid>` from an elevated terminal.
3. The elevated process performs ETW controller/consumer operations and the
   existing read-only `top` UI/query path.
4. It does not execute the selected target, resume an agent session, start the
   Web server, accept IPC clients, or write to caller-selected privileged paths.
5. Stopping the command does not kill the target.

This intentionally preserves the existing Windows Bind rule that agent
execution and session messaging remain in the non-elevated transcript user's
context. A later helper design must add authenticated, least-privilege IPC; it
is out of scope here.

The command must report permission and provider failures as Windows errors. It
must not silently fall back to snapshots or produce an apparently successful
empty capture.

## Health and loss

Phase 1 must distinguish:

- ETW lost-event and buffer counters;
- application queue drops;
- provisional-exit capacity drops and tracker-requested provisional cleanup;
- oversized or malformed records;
- decode failures;
- unknown process identity or parentage;
- bounded-cache evictions;
- stop/cleanup failures.

These categories can overlap and must not be summed into one "loss" number. A
zero counter means zero observed losses for that counter; it must not be used
to claim complete system coverage. Diagnostics must remain observable even when
the business-event queue is full.

Decode diagnostics use the existing `runner_parse_error` product shape while
retaining the `ETW_DECODE_ERROR` event name and ETW metadata. A consumer exit
emits a separate `runner_consumer_stopped` diagnostic containing the status,
reason, records drained, and still-pending replay count. The live view changes
from `active` to `stopped`; it must not leave an enabled capture note after
`ProcessTrace` has exited. Plain and interactive TUI rendering both read the
current capture status rather than the immutable startup note.

The real-time implementation queries the owned session's `EventsLost`,
`LogBuffersLost`, and `RealTimeBuffersLost` counters at most once per second
and again after a successful stop. Application queue drops remain a separate
counter. Query failures are reported separately from ETW loss.

## Testing and acceptance

### Pure tests

The following logic should be testable without starting ETW:

- FILETIME to Unix millisecond conversion, including the epoch boundary,
  out-of-range values, and invalid timestamps;
- process payload parsing for every supported schema version, including the
  version 4 fields observed on Windows 11;
- null-SID and full-SID process records, payload-PID terminate events, exit
  status, and required image/command-line terminators;
- unknown or truncated payload rejection;
- `Start` versus `DCStart` and `End` versus `DCEnd` mapping, including that
  `DCEnd` means present at tracing stop rather than exited;
- `Terminate` followed by `End` publishes one logical exit with the
  authoritative status, while a terminate-only sequence flushes one fallback
  exit at capture stop;
- descendant membership and root binding;
- PID and PPID reuse;
- reuse of an exited ETW process-object key without reviving the old instance;
- idempotent rundown/live overlap;
- bounded queue loss accounting;
- bounded provisional-exit retention, capacity loss, and tracker-eviction
  cleanup;
- stop-state transitions and repeated stop;
- graceful queue drain after a stop request;
- plain and TUI status replacement after a consumer stop, so an exited capture
  cannot continue to render as enabled;
- root exit with retained capture-only descendant evidence;
- successful child exits remain visible in `top` evidence;
- process projection keeps overlapping instances with the same PID separate by
  `process_instance_id`;
- parent exit before a reordered child event, with bounded recent-exit state;
- sustained unresolved/member churn and resolver-cache eviction;
- generation-token reuse after ambiguity clears, missing-`End` collision
  eviction, timestamp rejection of late/replayed children from an older PID
  generation, and isolation of children whose active parent was evicted;
- `DCStart` followed by a same-key live `Start`: duplicate announcement without
  a second process count, while `first_start_observed_at` and
  `generation_started_at` are backfilled;
- keyless version 0/1 replay of the same `Start` timestamp, which must remain
  idempotent;
- keyless version 0/1 `DCStart` followed by the first same-PID live `Start`,
  which must backfill the generation boundary, return a duplicate, and preserve
  one instance/live count rather than entering PID reuse;
- fail-closed attribution for recent-exited and live parents when the new
  parent generation has a reliable start time but the child does not;
- preservation of `first_rundown_observed_at` as an observation time without
  treating it as the process's actual creation time;
- non-Windows command error or absence.

These tests should compile and run in the existing Windows CI job, and the
relevant crates should remain buildable on Linux.

### Native smoke test

Before calling the implementation validated, run on the declared Windows 11
x86-64 build with the declared privilege context:

1. Start a synthetic target as a normal user.
2. Attach with `agentsight top --pid <pid>` and set a nonzero capture interval.
3. Have the target start and exit at least one short-lived child.
4. Verify root and child lifecycle events, timestamps, and provenance.
5. Stop capture and verify the target remains alive.
6. Stop the target independently and verify its exit event is captured when
   capture remains active.
7. Verify no owned ETW session remains after repeated stop and process exit.
8. Exercise non-admin, invalid-PID, session-conflict, and saturated-queue
   failures and verify explicit errors/diagnostics.
9. Verify a later reuse of the root PID does not attach old capture counters to
   the new process instance.
10. Deliver a descendant event before its parent event and verify it is replayed
    once after the parent becomes attributable.

A fixture or pure test is not evidence that live ETW capture works. Conversely,
one successful smoke test does not establish support for other Windows builds,
ARM64, alternate providers, or all process schemas.

### Smoke evidence

On 2026-11-14, Windows 11 x86-64, an elevated run of
`cargo run --manifest-path agentsight-capture/Cargo.toml --example windows_etw_smoke`
captured and returned:

- root version 4 `DCStart`, mapped to `PROCESS_PRESENT`, with the expected
  PID and image name;
- child version 4 `Start`, mapped to `EXEC`, with the parent PID equal to the
  root PID;
- child version 4 `End`, mapped to `EXIT`, with the same process-instance
  identity;
- root version 4 `End`, mapped to `EXIT`, with the root process-instance
  identity.

The captured events reported `queue_dropped_records=0`, `callback_errors=0`, and
`stop_errors=0`. Dropping the stream stopped the consumer and removed the
`AgentSight Windows Process Capture` session. This machine had two active
`NT Kernel Logger` sessions throughout the run, demonstrating coexistence with
the reserved logger. A separate non-admin `agentsight top --pid` run verified
snapshot fallback and an explicit privilege note without opening UAC. The
synthetic target inherited the elevated token, so an elevated `top --pid`
end-to-end run against a normal-user target still requires a separate smoke.

The same run also exposed legacy process `Terminate` records (opcode `0x0B`)
that the first candidate diagnosed as unsupported. Null-SID decoding,
payload-PID terminate handling, exit status, graceful draining, and bounded
tracker retention were added afterward and covered by pure tests. The native
smoke therefore predates the exact draft-PR head and must be repeated before
the draft is marked ready for review.

### CI policy

The existing Windows workflow should continue to run portable and compile/test
coverage. Live ETW testing should be a capability-probed manual or separate
privileged job; it must not assume that a hosted `windows-latest` image
guarantees a particular OS build or administrator behavior. Cross-privilege
helper testing requires a later dedicated environment.

## Review checklist

- [ ] Windows API code and dependencies are target-gated.
- [ ] The public `Runner` contract is unchanged.
- [ ] ETW timestamps are epoch milliseconds and bypass the Linux normalizer.
- [ ] `DCStart`/rundown cannot be counted as new process creation.
- [ ] Missing payload fields remain unknown.
- [ ] PID reuse cannot merge distinct process instances.
- [ ] Descendants are tracked through root exit.
- [ ] Callback work is bounded, nonblocking, and does not unwind across FFI.
- [ ] Required `EVENT_RECORD` data is copied before crossing the queue.
- [ ] Queue saturation increments explicit loss counters.
- [ ] Stop is idempotent, drains, joins, and cleans only owned state.
- [ ] Attach does not launch or terminate the target.
- [ ] Failure paths return explicit platform errors without silent fallback.
- [ ] Linux/macOS builds and existing portable tests remain green.
- [ ] PR validation lists actual OS, schema, privilege, test, and smoke evidence.

## Roadmap after phase 1

| Stage | Scope | Exit condition |
| --- | --- | --- |
| Privilege separation | Constrained elevated helper and authenticated local IPC | Normal-user product surface can request capture without elevating agent or Node execution. |
| File activity | File, path, request, and outcome correlation | Success, failure, and unknown outcomes render correctly; reads are not labeled as mutations. |
| Network activity | Connection and ownership correlation | Local synthetic workload and reports agree; no invented TLS, HTTP, or LLM semantics. |
| Safe recording | Attach/launch readiness and persistence round trip | No elevated agent, suspended-process leaks, or missing readiness gaps. |
| TLS boundary | Runtime-specific opt-in instrumentation | Version-validated plaintext, redaction, protocol, and deduplication tests pass. |
| Optional Windows evidence | PowerShell, registry, or UI Automation | Each source remains opt-in with explicit causality limits. |

Each stage should remain a separate reviewable PR. Do not merge privilege
broker, file/network semantics, launch behavior, or TLS into the first process
backend.
