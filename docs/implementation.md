# Implementation Status

## Current state

- Worktree: `/home/yunwei37/workspace/agentsight-evolution-gallery`
- Branch: `codex/vis-gallery`, based on `origin/master` at `a007540cc`.
- Existing `agent-session` library parses Claude, Codex, and Gemini native
  histories into prompts, tool events, model responses, tokens, paths, cwd, and
  timestamps.
- AgentSight's existing frontend already owns single-run timeline, process tree,
  log, and resource views; the longitudinal gallery remains separate.

## Implemented artifact boundary

- Extend `ToolEvent` without breaking existing consumers: preserve exact
  repository-relative path references and bounded edit/read payload metrics
  where a native schema exposes them; keep `path_groups` as the privacy-safe
  summary.
- The `agent-session-export` CLI has explicit repository, frozen revision, time-range,
  source, and output arguments. Its canonical longitudinal artifact will carry
  raw normalized events, Git changes and file lifetimes, endpoint state,
  candidate associations, confidence, and preaggregated projections.
- It exports canonical longitudinal JSON, normalized event JSONL, Perfetto
  Trace Event JSON, and Gource custom logs. The compatibility formats are
  labeled lossy baselines.
- The root-level experimental `vis-gallery/` TypeScript application uses
  package-locked ECharts, Cytoscape.js, and uPlot dependencies and no
  runtime CDN requirement.
- Preserve `frontend/` and README Quick Start.
- Private real-data output remains under ignored artifact paths; only
  sanitized fixtures and screenshots that have been checked for sensitive
  content.

## Implemented pipeline

1. Discover and parse Claude, Codex, and Gemini session files with the existing
   vendor-neutral parser.
2. Canonicalize repository-relative path evidence while retaining pathless and
   external events. Shell operands are modeled conservatively: copy sources
   are reads, destinations and output redirections are writes, sed expressions
   and glob/command fragments are not files, and cwd-relative `..` candidates
   survive only when exporter normalization keeps them inside the repository.
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

Event-level exact-hunk fingerprints are emitted only for single-file,
single-hunk native edits. Multi-file and multi-hunk patches remain visible as
path observations but are ineligible for exact-hunk evidence.

## Privacy and reproducibility

The default artifact excludes prompt bodies, command bodies, edit/read bodies,
secrets, and absolute home paths. It retains hashes, bounded previews only when
explicitly requested, categorical actions, repository-relative normalized
paths, and aggregate sizes. Every experiment records the source time range, repository revision,
exporter version, join settings, confidence thresholds, and dependency lock.

## Validation entrypoints

- `cargo test --manifest-path agent-session/Cargo.toml`
- `cd vis-gallery && npm run build && npm test && npm run test:e2e`
- `python3 vis-gallery/analysis/build_gallery_data.py ...` creates the checked
  public projection from private native-history exports and rejects prompt,
  command, edit-body, content, and absolute-home-path keys.

Rust fixtures cover all three native schemas, path normalization, exact edit
fingerprints, pathless events, rename/recreation lifetimes, and deleted-path
gaps. Browser tests exercise all nine navigation families, the shared cursor,
filters, and representative screenshots. The public real-data atlas contains
56 deduplicated sessions, 6,040 path-event rows, 918 file lifetimes, 177
commits, 1,852 Git changes, and 12,000 Git-blame line pixels across three
observation days spanning June 2 through July 14. July 14 is explicitly
right-censored and process-only for quantitative association purposes.
