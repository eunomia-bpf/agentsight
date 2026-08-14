# PR body: External-consumer bridge (revisioned mutation stream over UDS)

*This file is the prepared body for the upstream PR from
`gauransh/agentsight:aro-bridge-v1` to `eunomia-bpf/agentsight:main`.
Open with: `gh pr create --repo eunomia-bpf/agentsight --head gauransh:aro-bridge-v1
--title "feat: external-consumer bridge — revisioned mutation stream over UDS"
--body-file docs/design/aro-integration-pr.md` (when upstream engagement is wanted).*

---

## What this adds

A **bridge** through which an external observatory subscribes to AgentSight's
materialized evidence as a bounded, revisioned mutation stream — with privacy
projection applied inside AgentSight before anything leaves the process. The first
consumer is [ARO](https://github.com/gauransh/agent-resource-observatory), which
correlates AgentSight's semantic/process evidence with its own cgroup-authoritative
resource accounting. Nothing in the bridge can actuate anything: it is observation
out, display-only annotations in.

## Design (full docs in `docs/design/aro-integration.md`)

- **`agentsight-protocol`**, feature `bridge` (off by default; wasm untouched):
  `BRIDGE_PROTOCOL_VERSION = 1`, separate from the Node API version. u32-LE length +
  CBOR frames. Hello/agreement with capability negotiation; opaque scope registration
  (consumer tenancy never crosses the wire); per-(node,boot) sequences with
  ack/resume/declared-gap/snapshot-reconstruction semantics; revisioned rows
  (identical re-emits never bump). Golden vectors under `tests/fixtures/bridge-v1/`
  (37 entries, 5 files) pin the wire bytes; ARO's independent implementation
  round-trips them byte-for-byte as its compatibility gate.
- **`agentsight-capture`**: `MutationSink` beside the existing `ViewSink`
  (unchanged); metadata projection (`as-redact/v1`) — path/cwd classes, env-safe
  executable basenames, argv shapes, command fingerprints, eTLD+1 destination
  classes, digests for raw targets; disclosure modes MetadataOnly / ResearchFull /
  IncidentScoped; sessions now stream as mutations; 13-class canary suite proves
  MetadataOnly bytes carry no prompts/commands/paths/secrets.
- **`collector`**: `--bridge-socket` UDS server (0700/0600, symlink-refusing,
  Linux `SO_PEERCRED` same-uid, bounded queues with counted drops surfacing as
  declared gaps, heartbeat, resume buffer, snapshot resync). `--cgroup-filter` /
  `--cgroup-filter-children` finally forwarded to the eBPF `process` binary.
- **Process identity**: `start_ticks` on process rows, read from procfs at event
  arrival (never derived from timestamps; `None` when unknowable).
- **Reverse annotations** (capability `aro_annotations`): display-only ARO overlays
  (resource domain, enforcement, policy decisions, correlations), scope-bound,
  revision-idempotent, bounded store; served in snapshots; never executed.

## Compatibility

- Base: `v1.0.20` (`f7d961f8`). All existing tests pass unchanged; the two
  `export_snapshot_test` cases that scan a live host `~/.claude` remain
  environment-dependent as on main.
- The Node API (`PROTOCOL_VERSION`, paths, WASM bindings) is untouched.
- New capability names are additive; a build without an arm simply does not
  advertise it.

## Tests

`agentsight-protocol --features bridge`: 23 · `agentsight-capture`: 207 (+1 ignored)
· `collector` bin: 113 — plus adversarial protocol tests (oversize/truncated/garbage
frames, unknown tags), revision semantics, canary privacy suite, server
integration (hello, scopes, ack/resume/gap/saturation, peer-cred accept path).
Consumer-side end-to-end evidence (live collector → bridge → mapped, signed,
verified evidence store) is recorded in ARO's repository
(`docs/integrations/agentsight-report.md`).

## Commits

`70806c16` bridge protocol v1 + emitter + projection + server + cgroup flags ·
`72fac5c2` env-assignment basename privacy fix · `76abf9a7` start_ticks on process
rows · `a9421a9b` reverse-annotation rows + store + vectors · `d8001dad`/`aeadb157`
collector e2e enablement fixes · `91e2722f` annotation server arm + serving +
start_ticks at arrival.
