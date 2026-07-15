# Implementation Status

## Current state

- Worktree: `/home/yunwei37/workspace/agentsight-evolution-gallery`
- Branch: `codex/vis-gallery`, based on `origin/master` at `a007540cc`.
- Existing `agent-session` library parses Claude, Codex, and Gemini native
  histories into prompts, tool events, model responses, tokens, paths, cwd, and
  timestamps.
- AgentSight's existing frontend already owns single-run timeline, process tree,
  log, and resource views; the longitudinal gallery remains separate.

## Planned artifact boundary

- Extend `ToolEvent` without breaking existing consumers: preserve exact
  repository-relative path references and bounded edit/read payload metrics
  where a native schema exposes them; keep `path_groups` as the privacy-safe
  summary.
- Add an `agent-session` export CLI with explicit repository, time-range,
  source, and output arguments. Its canonical longitudinal artifact will carry
  raw normalized events, Git changes and file lifetimes, endpoint state,
  candidate associations, confidence, and preaggregated projections.
- Export equivalent normalized JSON/JSONL, Perfetto Trace Event JSON, and
  Gource custom logs. Formats that cannot carry the whole evidence model are
  labeled lossy baselines.
- Add a root-level experimental `vis-gallery/` TypeScript application with
  package-locked ECharts, D3, Cytoscape.js, and uPlot dependencies and no
  runtime CDN requirement.
- Preserve `frontend/` and README Quick Start.
- Generate private real-data output under ignored artifact paths; commit only
  sanitized fixtures and screenshots that have been checked for sensitive
  content.

## Planned pipeline

1. Discover and parse Claude, Codex, and Gemini session files with the existing
   vendor-neutral parser.
2. Canonicalize repository-relative path evidence while retaining pathless and
   external events.
3. Collect Git commits, diffs, renames, authors, file birth/death intervals,
   current paths, and line lineage through stable non-interactive plumbing.
4. Produce zero/one/many candidate associations for each eligible event. Keep
   event-side and Git-side unmatched records and never infer authorship from
   time alone.
5. Build multi-resolution time buckets, stable path coordinates, view
   projections, and baseline exports from the same canonical artifact.
6. Serve the artifact locally and coordinate all renderers through one typed
   time/path/session/evidence selection state.

File-lifetime IDs are structural: an add begins a lifetime, detected renames
preserve it, deletion ends it, and same-path recreation creates a new ID. The
primary join emits candidates in the preregistered event-relative time window
without forcing a bijection; merge changes are retained in a separate stratum.

## Privacy and reproducibility

The default artifact excludes prompt bodies, command secrets, absolute home
paths, and edit contents. It retains hashes, bounded previews only when
explicitly requested, categorical actions, normalized paths, and aggregate
sizes. Every experiment records the source time range, repository revision,
exporter version, join settings, confidence thresholds, and dependency lock.

## Validation entrypoints

Pending implementation. Rust unit fixtures will cover every supported native
schema, path normalization, candidate ambiguity, rename chains, file lifetimes,
and endpoint state. Integration fixtures will compare exporter aggregates with
Git commands and Hercules where reproducible. Browser tests will load a
sanitized fixture, exercise every view, scrub/play/filter linked state, and
capture screenshots. Final validation includes Cargo tests, gallery typecheck/
build/tests, a real multi-day export, privacy scan, and measured browser render.
