# AgentSight single-view visualizations

Generate one portable software-evolution graph per file. There is no dashboard,
server, project file, or user-visible intermediate dataset.

```text
repository + native agent sessions -> selected view -> HTML / SVG / PNG / GIF / MP4
```

The 31 views cover activity timelines, SeeSoft-style line-age pixels, evolution
matrices, repository maps, particle playback, strata/survival, forensic
networks, storylines, and longitudinal rhythms. Every view uses ECharts so its
interactive HTML, vector SVG, raster PNG, and animation frames share the same
rendering logic.

## Setup

```bash
cd vis-gallery
npm ci
npx playwright install chromium
npm run build
```

Python 3 and the Rust toolchain are needed when reading a repository directly.
FFmpeg is needed only for GIF and MP4 output.

## Generate one graph

```bash
npm run render -- \
  --repo .. --since 30d \
  --view repository-treemap \
  --output repository-treemap.html
```

The HTML is self-contained and opens directly from disk. It contains exactly
one graph plus its title, evidence legend, and—when the view has time
semantics—one playable progress bar. No network request or local server is
required. Session/Git data is piped between the internal parser and projector;
no intermediate JSON file is written or exposed to the user.

Change only the output extension to select a format:

```bash
npm run render -- --repo .. --since 30d --view line-age-pixels --output lines.svg
npm run render -- --repo .. --since 30d --view hotspot-treemap --output hotspot.png
npm run render -- --repo .. --since 30d --view session-storylines --output story.gif
npm run render -- --repo .. --since 30d --view session-storylines --output story.mp4
```

All 31 views support every output format. Prefer PNG or SVG for static
endpoint/history views; their GIF/MP4 compatibility output contains one frame.
The 23 time-aware GIF/MP4 views sample their observed evidence range, avoiding
mostly empty frames in sparse sessions. Interactive HTML keeps the complete
selected interval.

List all view IDs:

```bash
npm run render -- --list-views
```

Generate every view from one repository/session scan:

```bash
npm run render:all -- \
  --repo .. --since 30d \
  --output-dir artifacts/30d \
  --formats html,gif
```

## Share and embed

- Attach PNG, SVG, GIF, or MP4 directly to social posts and reports.
- Embed the self-contained HTML with an `<iframe>` in any report system that
  accepts local/generated assets.
- Copy an SVG inline when the host report wants selectable vector labels.
- Regenerate several sizes with `--width` and `--height`; graph semantics do not
  change.

Each SVG includes compact provenance metadata. The visible footer also names
the repository, frozen Git revision, and association mode.

## Evidence boundaries

The renderer keeps three facts separate:

1. recorded process: path/tool events from native Claude, Codex, and Gemini
   histories;
2. durable Git: commits, file changes, renames, lifetimes, and Git authors;
3. frozen endpoint: current tree, bytes, and Git-blame line origins.

A Git author is never relabeled as an agent author. Read-before-write edges are
temporal order, not causality. Candidate event-to-Git associations remain
uncertain visual evidence, not authorship or provenance claims.

The ownership view includes Git author display names because they are the
durable-history identity being visualized; email addresses are excluded. Treat
reports from private repositories as private unless those names are safe to
share.

## Verify

```bash
npm run lint
npm run build
npm test
npm run test:project
npm run test:e2e
```

The browser test generates and opens all 31 HTML files one by one, checks that
each contains one rendered SVG graph, exercises every dynamic cursor, rejects
console/page errors and overflow, and captures ignored local screenshots for
visual review.
