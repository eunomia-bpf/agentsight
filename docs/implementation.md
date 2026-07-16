# Implementation status

## Current shape

- `agent-session` parses Claude, Codex, and Gemini native histories and joins
  repository-relative path events to a frozen Git revision.
- `agent-session-export` retains privacy-safe sessions, normalized events, Git
  changes, file lifetimes, and uncertain event-to-Git candidates. Its Perfetto
  and Gource formats remain lossy compatibility exports.
- `vis-gallery/` is a command-line single-artifact generator, not a dashboard.
  Each invocation selects one of 31 views and writes one self-contained HTML,
  SVG, PNG, GIF, or MP4 file.
- AgentSight's existing `frontend/` remains the owner of live single-run
  timeline, process tree, log, and resource views.

## User path

```text
repository + native session histories
        |
        v
in-memory EvolutionData (sessions + Git + associations)
        |
        v
shared compact projection over stdout/stdin (no file)
        |
        v
selected per-view ViewModel in renderer memory
        |
        v
one requested output file
```

Users provide only repository, time range, view ID, and output path. The Rust
`agent-session` layer builds the shared evolution data once; its compact
projection is piped directly into the renderer and is never written as an
intermediate file.
Batch generation reuses that in-memory result for every selected output.

The renderer has one runtime dependency, ECharts. A tree-shaken SVG runtime is
inlined into HTML, SVG is extracted from that renderer, PNG captures the full
artifact, and GIF/MP4 replay the same cursor function through Playwright and
FFmpeg. Static views reject animation output rather than repeating identical
frames.

## Evidence and privacy

- Native path/tool events are recorded-process evidence.
- Commits, changes, file lifetimes, and Git authors are durable-Git evidence.
- Current blobs and blame origins are frozen-endpoint evidence.
- Git authors are not agent authors, read-before-write is not causality, and
  candidate event-to-Git links are not provenance claims.
- Prompt, command, edit/read body, secret, native session path, absolute home
  path, and Git author email fields are excluded from the projection.
- Fresh writes whose forward association window has not matured remain
  descriptive and carry no candidate evidence.

File-lifetime IDs are structural: add begins a lifetime, rename preserves it,
deletion ends it, and same-path recreation creates a new lifetime.

## Validation entrypoints

```bash
cargo test --manifest-path agent-session/Cargo.toml
cd vis-gallery
npm ci
npm run lint
npm run build
npm test
npm run test:project
npm run test:e2e
```

Registry tests require 31 unique view IDs and SVG-render every view at both
interval endpoints. Browser tests generate and open all 31 HTML files one by
one, require a single rendered SVG graph, exercise every dynamic cursor, reject
console/page errors and overflow, and capture ignored screenshots for visual
inspection.
