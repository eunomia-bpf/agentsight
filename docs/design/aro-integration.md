# ARO Bridge Integration

This branch adds a generic, transport-bounded **bridge** through which an external
resource-observatory (the first consumer is [ARO](https://github.com/gauransh/agent-resource-observatory))
subscribes to AgentSight's materialized evidence as a revisioned mutation stream,
with privacy projection applied **inside AgentSight before anything leaves the process**.

## Pieces

| Layer | Where | What |
|---|---|---|
| Wire contract | `agentsight-protocol` feature `bridge` | `BRIDGE_PROTOCOL_VERSION = 1` (separate from the Node API `PROTOCOL_VERSION`); u32-LE length + CBOR frames; hello/agreement + capability negotiation; opaque scope registration (the consumer's tenancy identifiers never cross the wire); revisioned row mutations with per-(node,boot) sequences; ack/resume/declared-gap/snapshot-reconstruction semantics; golden vectors under `tests/fixtures/bridge-v1/` are the cross-implementation compatibility contract |
| Mutation emission | `agentsight-capture/src/bridge/` | `MutationSink` beside the existing `ViewSink` (unchanged); content-hash revisioning (identical re-emits never bump); metadata projection `as-redact/v1`: path/cwd classes, executable basenames (env-assignment safe), argv shapes, command fingerprints, eTLD+1 destination classes, digests for raw targets; disclosure modes MetadataOnly / ResearchFull / IncidentScoped; sessions now flow as mutations |
| Server | `collector` `--bridge-socket` | tokio UDS listener: symlink-refusing 0700/0600 socket prep, Linux `SO_PEERCRED` same-uid policy, bounded outbound queue with counted drops surfacing as declared gaps, heartbeat, resume buffer, snapshot resync |
| Cgroup scoping | `collector` `--cgroup-filter[,--cgroup-filter-children]` | finally forwards the flags the eBPF `process` binary already implemented |
| Process identity | `BridgeProcessNodeRow.start_ticks` | kernel start ticks for pid-reuse-safe identity; `None` until the eBPF process events carry starttime (deliberate: never invented from timestamps) |
| Reverse annotations (foundation) | protocol rows + capture `AnnotationStore` | read-only ARO→AgentSight overlays (resource domain, enforcement, policy decisions, correlations), capability-gated (`aro_annotations`), idempotent by (kind,row_id,revision); display-only — AgentSight never executes them |

## Guarantees

- **Privacy**: MetadataOnly serialized bytes carry no prompts/responses/commands/argv
  values/raw paths/URLs/queries/headers/secrets — enforced by projection and proven by
  the 13-class canary suite (`agentsight-capture/tests/bridge_metadata_canary.rs`).
- **Boundedness**: every queue is bounded; overflow is counted and declared, never silent.
- **No authority**: the bridge is observation-only. Nothing in it can actuate cgroups,
  policies, or processes.
- **Compatibility**: the consumer re-implements the wire types independently and both
  sides round-trip the same pinned vectors byte-for-byte.

## Base and status

Base: `v1.0.20` (f7d961f8). See [aro-integration-status.md](aro-integration-status.md).
