# ARO Bridge Integration — Branch Status

Branch: `aro-bridge-v1` (pushed to `github.com/gauransh/agentsight`).
Base: `f7d961f8` = tag `v1.0.20`.

| Commit | Content | Tests |
|---|---|---|
| 70806c16 | Bridge protocol v1 (feature `bridge`), mutation emitter + revisioning + metadata projection, UDS server (`--bridge-socket`), cgroup-filter CLI plumbing, golden vectors, canary suite | protocol+bridge 15; capture 189; collector bin 106 |
| 72fac5c2 | Privacy fix: `executable_basename` never echoes a shell env assignment | capture 190 |
| 76abf9a7 | `BridgeProcessNodeRow.start_ticks` (pid-reuse-safe identity), vectors regenerated | protocol 15; capture 190 |
| (pending) | Reverse-annotation rows + `AnnotationStore` + vectors (capability `aro_annotations`) | in flight |

Known limits (stated, not hidden):

- The eBPF `process` events do not yet report starttime, so live projections carry
  `start_ticks: None`; consumers must treat process identity as incomplete until the
  capture side adds it.
- `collector/tests/export_snapshot_test.rs` has 2 pre-existing failures on hosts with
  live local agent sessions (they scan the real `~/.claude`); unrelated to this branch.
- wasm builds of `agentsight-protocol` are unaffected (the `bridge` feature is never
  enabled for wasm) but not exercised on the development host.
- SO_PEERCRED peer refusal is unit-covered on the accept path; the refusal path needs a
  second uid (CI-tier).

Upstream PR: prepared from this branch once the consumer-side end-to-end evidence is
recorded; the PR body should carry the protocol summary, privacy guarantees, and the
golden-vector compatibility mechanism from [aro-integration.md](aro-integration.md).
