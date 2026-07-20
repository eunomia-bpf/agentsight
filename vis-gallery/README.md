# AgentSight single-view visualizations

Repository Nebula 的普通用户入口已经内嵌在 Rust CLI：

```bash
agentsight vis [PATH] [-o repository-nebula.html] [--global]
```

只改输出扩展名即可生成 `.html`、`.svg`、`.png`、`.gif` 或 `.mp4`。HTML
不需要浏览器依赖；其他格式需要 Chromium，GIF/MP4 还需要 FFmpeg。该路径直接调用
`agent-session` library，不经过 Python、Node 子进程或中间 JSON。

本文后面的命令是保留全部 31 张实验图的开发入口，不是 Nebula 的安装后用法。

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

Use `--since repo` to search native Agent sessions over the repository's whole
lifetime:

```bash
npm run render -- \
  --repo /path/to/repository --since repo \
  --view workspace-constellation \
  --output repository-nebula.html
```

By default, sessions must identify the repository through cwd, a sibling Git
worktree, project hash, or Git remote. Add `--global` to scan every local
Claude, Codex, and Gemini history and include only real Tool operations whose
command/path targets the repository. Prompt text and ordinary mentions are not
included:

```bash
npm run render -- \
  --repo /path/to/repository --since repo --global \
  --view workspace-constellation \
  --output repository-nebula-global.html
```

Dynamic figures advance only on recorded Agent-event timestamps. They do not
invent activity for intervals without a native session. Git commits never move
or resize the animated files; a commit inside the observed Agent interval only
flashes the artifact's outer border. Read/write attention remains visible for
24 file-event steps and fades with a six-step half-life.

Repository Nebula draws stars only for files involved in real Agent file
actions. Directories are never stars: they provide inherited color and
invisible path attraction. Files emerge beside path-near observed files and
continually rebalance under attraction, repulsion, collision, damping, and
recent attention. Untouched endpoint files, processes, network activity, and
LLM responses do not enter the graph.

Change only the output extension to select a format:

```bash
npm run render -- --repo .. --since 30d --view line-age-pixels --output lines.svg
npm run render -- --repo .. --since 30d --view hotspot-treemap --output hotspot.png
npm run render -- --repo .. --since 30d --view session-storylines --output story.gif
npm run render -- --repo .. --since 30d --view session-storylines --output story.mp4
```

All 31 views support every output format. Prefer PNG or SVG for static
endpoint/history views; their GIF/MP4 compatibility output contains one frame.
The 22 time-aware GIF/MP4 views sample their observed evidence range, avoiding
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
the repository, frozen Git revision, and whether the session scope is repository
identity or global Tool operations.

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
