# Single-artifact software evolution views

## Purpose

The longitudinal views complement AgentSight's run timeline and agentpprof.
They expose repository structure, development rhythm, durable Git outcomes, and
long-lived code shape across agent sessions.

The delivery unit is deliberately small: one command produces one graph in one
self-contained file. There is no shared dashboard or server.

```text
repository + native sessions
        |
        v
in-memory EvolutionData (sessions + Git + associations)
        |
        v
one selected view model -> HTML / SVG / PNG / GIF / MP4
```

The shared data is computed once for batch generation, projected through a
stdout/stdin pipe, and discarded when the command exits. No canonical JSON is
written for users to create, store, understand, or pass between commands.

## Evidence contract

- Native path/tool activity is recorded process evidence.
- Commits, changes, renames, lifetimes, and Git authors are durable Git
  evidence.
- Current blobs and blame origins are frozen-endpoint evidence.
- A Git author is never renamed as an agent author.
- Read-before-write is temporal order, not causality.
- Candidate event-to-Git matches retain zero/one/many uncertainty and never
  become authorship claims.
- Same-path deletion and recreation create separate file lifetimes.

## Rendering contract

All 31 view specs use one tree-shaken ECharts SVG runtime. Each spec declares
its input keys and one time mode: `static`, `cursor-marker`, `cumulative`,
`trailing-6h`, `endpoint-overlay`, or `mixed-day`.

- Each HTML mounts exactly one graph.
- Time-aware HTML adds one playable range control.
- Static HTML disables the time control and rejects GIF/MP4 export.
- SVG is extracted from the same HTML renderer and receives compact provenance
  metadata.
- PNG is a screenshot of the complete artifact; GIF and MP4 are sequences of
  the same cursor-driven render function.
- Output is self-contained and makes no network requests.

Every playable view uses recorded Agent operation timestamps as its only state
clock. Repository geometry may stay stable while reads, writes, and other
recorded effects change salience and decay. A Git commit may flash the outer
artifact frame, but it must not create, move, resize, recolor, or delete marks
inside an Agent playback. Static Git/lifetime views remain explicit snapshots;
they do not pretend to be Agent-time animations.

## Verification

Registry tests require exactly 31 unique views and render every spec at both
ends of the interval through ECharts SVG SSR. Browser tests then generate and
open all 31 HTML files individually, require one visible SVG graph, exercise
dynamic cursors, reject console/page errors and overflow, and capture ignored
screenshots for visual inspection.
